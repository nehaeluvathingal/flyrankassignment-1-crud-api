from fastapi import FastAPI, HTTPException, status, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List

# Initialize FastAPI application
# This is Stage 0 setup. FastAPI naturally enables the interactive documentation
# (Swagger UI) at '/docs' automatically.
app = FastAPI(
    title="Task API",
    description="A simple CRUD API for managing tasks.",
    version="1.0"
)

# ---------------------------------------------------------
# Pydantic Models for Request Validation
# ---------------------------------------------------------

# The Task schema representing the structure of our task objects
class Task(BaseModel):
    id: int
    title: str
    done: bool

# Schema used when creating a task (Stage 3)
# It only requires "title". The ID is auto-assigned, and done defaults to false.
class TaskCreate(BaseModel):
    title: str = Field(..., description="The title of the task")

    # Custom validator to ensure that the title is not empty or just whitespace.
    # If it is empty, raises a ValueError which gets caught by our validation handler.
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Title is required and cannot be empty")
        return v

# Schema used when updating a task (Stage 4)
# Allows updating either "title", "done", or both.
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, description="The updated title of the task")
    done: Optional[bool] = Field(None, description="The updated completion status of the task")

    # Custom validator to ensure that if a title is provided, it cannot be empty.
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Title cannot be empty")
        return v

# ---------------------------------------------------------
# Custom Validation Exception Handler
# ---------------------------------------------------------
# By default, FastAPI returns HTTP 422 Unprocessable Entity when validation
# fails. The assignment requirements specify returning HTTP 400 along with a
# JSON error message for invalid request bodies, missing, or empty titles.
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    # Generate a descriptive error message listing the validation issues
    error_messages = []
    for error in errors:
        loc = " -> ".join(str(l) for l in error.get("loc", []))
        msg = error.get("msg", "validation error")
        error_messages.append(f"Field '{loc}': {msg}")
    
    combined_message = "; ".join(error_messages)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"error": f"Invalid request body. Details: {combined_message}"}
    )

# ---------------------------------------------------------
# In-Memory Database (List of Tasks)
# ---------------------------------------------------------
# Pre-seeded database with 3 sample tasks as required in Stage 2.
tasks_db: List[dict] = [
    {"id": 1, "title": "Buy groceries", "done": False},
    {"id": 2, "title": "Clean the house", "done": True},
    {"id": 3, "title": "Read a book", "done": False},
]

# Variable to keep track of the next ID to be assigned.
# Starts at 4, as IDs 1, 2, and 3 are already taken by the sample tasks.
next_id = 4

# ---------------------------------------------------------
# Stage 1: Basic Metadata & Health Check Endpoints
# ---------------------------------------------------------

@app.get("/", status_code=status.HTTP_200_OK)
async def get_metadata():
    """
    GET /
    Returns application metadata: name, version, and available endpoints.
    """
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """
    GET /health
    Returns a simple health check status indicating that the API is up and running.
    """
    return {
        "status": "ok"
    }

# ---------------------------------------------------------
# Stage 2: GET Tasks (All and Single) Endpoints
# ---------------------------------------------------------

@app.get("/tasks", status_code=status.HTTP_200_OK)
async def get_tasks():
    """
    GET /tasks
    Returns the full list of tasks stored in-memory.
    """
    return tasks_db

@app.get("/tasks/{id}", status_code=status.HTTP_200_OK)
async def get_task(id: int):
    """
    GET /tasks/{id}
    Retrieves a single task by its unique integer ID.
    If the task does not exist, returns HTTP 404 and a JSON error message.
    """
    for task in tasks_db:
        if task["id"] == id:
            return task
    
    # Task not found, return 404 Response
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {id} not found"}
    )

# ---------------------------------------------------------
# Stage 3: POST Task (Create) Endpoint
# ---------------------------------------------------------

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(task_in: TaskCreate):
    """
    POST /tasks
    Creates a new task.
    - Expects a JSON input containing a 'title' string.
    - Automatically assigns the next available sequential ID.
    - Defaults 'done' to false.
    - Returns the created task with HTTP 201 Created status.
    """
    global next_id
    new_task = {
        "id": next_id,
        "title": task_in.title,
        "done": False
    }
    tasks_db.append(new_task)
    next_id += 1
    return new_task

# ---------------------------------------------------------
# Stage 4: PUT (Update) and DELETE (Remove) Endpoints
# ---------------------------------------------------------

@app.put("/tasks/{id}", status_code=status.HTTP_200_OK)
async def update_task(id: int, task_in: TaskUpdate):
    """
    PUT /tasks/{id}
    Updates an existing task's title and/or completion status.
    - If the ID does not exist, returns HTTP 404.
    - If the request body contains invalid values, returns HTTP 400.
    """
    # Search for the task by ID
    task_idx = None
    for idx, t in enumerate(tasks_db):
        if t["id"] == id:
            task_idx = idx
            break
            
    if task_idx is None:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"error": f"Task {id} not found"}
        )
    
    # If the user passes an empty object or invalid fields, return HTTP 400.
    if task_in.title is None and task_in.done is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid request body. You must update 'title' and/or 'done'."}
        )

    # Perform the updates
    if task_in.title is not None:
        tasks_db[task_idx]["title"] = task_in.title
    if task_in.done is not None:
        tasks_db[task_idx]["done"] = task_in.done
        
    return tasks_db[task_idx]

@app.delete("/tasks/{id}", response_class=Response)
async def delete_task(id: int):
    """
    DELETE /tasks/{id}
    Removes a task by its unique ID.
    - If the task exists, deletes it and returns HTTP 204 with no response body.
    - If the ID is unknown, returns HTTP 404 with a JSON error message.
    """
    global tasks_db
    for idx, task in enumerate(tasks_db):
        if task["id"] == id:
            tasks_db.pop(idx)
            # Return an empty response with HTTP 204 status code (no content)
            return Response(status_code=status.HTTP_204_NO_CONTENT)
            
    # Task not found, return HTTP 404
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {id} not found"}
    )
