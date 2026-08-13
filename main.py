from fastapi import FastAPI, HTTPException, status, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import repository
from contextlib import asynccontextmanager

# The lifespan context manager handles application startup events in FastAPI.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Stage 1: Initialize the PostgreSQL database on startup.
    # SQLite has been completely removed from the storage architecture.
    repository.init_db()
    yield

# Initialize FastAPI application with lifespan event handler
app = FastAPI(
    title="Task API",
    description="A simple CRUD API for managing tasks with PostgreSQL in Docker.",
    version="1.0",
    lifespan=lifespan
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
class TaskCreate(BaseModel):
    title: str = Field(..., description="The title of the task")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Title is required and cannot be empty")
        return v

# Schema used when updating a task (Stage 4)
class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, description="The updated title of the task")
    done: Optional[bool] = Field(None, description="The updated completion status of the task")

    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or not v.strip()):
            raise ValueError("Title cannot be empty")
        return v

# ---------------------------------------------------------
# Custom Validation Exception Handler
# ---------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
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
# Stage 1: Task CRUD Endpoints calling Repository
# ---------------------------------------------------------

@app.get("/tasks", status_code=status.HTTP_200_OK)
async def get_tasks():
    """
    GET /tasks
    Returns the full list of tasks from PostgreSQL.
    """
    return repository.get_tasks()

@app.get("/tasks/{id}", status_code=status.HTTP_200_OK)
async def get_task(id: int):
    """
    GET /tasks/{id}
    Retrieves a single task by its unique integer ID.
    If the task does not exist, returns HTTP 404 and a JSON error message.
    """
    task = repository.get_task(id)
    if task is not None:
        return task
    
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {id} not found"}
    )

@app.post("/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(task_in: TaskCreate):
    """
    POST /tasks
    Creates a new task in PostgreSQL.
    - Expects a JSON input containing a 'title' string.
    - Returns the created task with HTTP 201 Created status.
    """
    return repository.create_task(task_in.title)

@app.put("/tasks/{id}", status_code=status.HTTP_200_OK)
async def update_task(id: int, task_in: TaskUpdate):
    """
    PUT /tasks/{id}
    Updates an existing task's title and/or completion status in PostgreSQL.
    - If the ID does not exist, returns HTTP 404.
    - If the request body contains invalid values, returns HTTP 400.
    """
    if task_in.title is None and task_in.done is None:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"error": "Invalid request body. You must update 'title' and/or 'done'."}
        )
    
    task = repository.update_task(id, task_in.title, task_in.done)
    if task is not None:
        return task
        
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {id} not found"}
    )

@app.delete("/tasks/{id}", response_class=Response)
async def delete_task(id: int):
    """
    DELETE /tasks/{id}
    Removes a task by its unique ID in PostgreSQL.
    - If the task exists, deletes it and returns HTTP 204 with no response body.
    - If the ID is unknown, returns HTTP 404 with a JSON error message.
    """
    success = repository.delete_task(id)
    if success:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
            
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {id} not found"}
    )
