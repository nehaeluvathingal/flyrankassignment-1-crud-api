from fastapi import FastAPI, HTTPException, status, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import sqlite3
from contextlib import asynccontextmanager

DATABASE_FILE = "tasks.db"

def init_db():
    """
    Stage 0: Establish SQLite database, tables, and insert seed data if empty.
    """
    # Open/create the tasks.db database file automatically
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    
    # Create the tasks table automatically if it does not exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL CHECK (done IN (0, 1))
        )
    """)
    conn.commit()
    
    # Check if the tasks table is empty to avoid duplicating seed tasks
    cursor.execute("SELECT COUNT(*) FROM tasks")
    count = cursor.fetchone()[0]
    
    if count == 0:
        # Insert exactly three example tasks using parameterized SQL
        example_tasks = [
            (1, "Buy groceries", 0),
            (2, "Clean the house", 1),
            (3, "Read a book", 0)
        ]
        cursor.executemany("INSERT INTO tasks (id, title, done) VALUES (?, ?, ?)", example_tasks)
        conn.commit()
        
    conn.close()

# The lifespan context manager handles application startup events in FastAPI.
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run the database initialization and seeding on startup
    init_db()
    yield

# Initialize FastAPI application with lifespan event handler
app = FastAPI(
    title="Task API",
    description="A simple CRUD API for managing tasks with SQLite.",
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
# Stage 1: GET Tasks (All and Single) Endpoints from SQLite
# ---------------------------------------------------------

@app.get("/tasks", status_code=status.HTTP_200_OK)
async def get_tasks():
    """
    GET /tasks
    Returns the full list of tasks stored in SQLite database.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, done FROM tasks")
    rows = cursor.fetchall()
    conn.close()
    
    tasks = []
    for row in rows:
        tasks.append({
            "id": row[0],
            "title": row[1],
            "done": bool(row[2])
        })
    return tasks

@app.get("/tasks/{id}", status_code=status.HTTP_200_OK)
async def get_task(id: int):
    """
    GET /tasks/{id}
    Retrieves a single task by its unique integer ID from SQLite.
    If the task does not exist, returns HTTP 404 and a JSON error message.
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    # Query using parameterized query with ? placeholder
    cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    
    if row is not None:
        return {
            "id": row[0],
            "title": row[1],
            "done": bool(row[2])
        }
    
    # Task not found, return 404 Response
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": f"Task {id} not found"}
    )

# ---------------------------------------------------------
# Temporarily Commented Out CRUD Endpoints for Stage 1
# ---------------------------------------------------------
# These will be fully migrated to SQLite in Stage 2 and Stage 3.

# @app.post("/tasks", status_code=status.HTTP_201_CREATED)
# async def create_task(task_in: TaskCreate):
#     """
#     POST /tasks
#     """
#     pass

# @app.put("/tasks/{id}", status_code=status.HTTP_200_OK)
# async def update_task(id: int, task_in: TaskUpdate):
#     """
#     PUT /tasks/{id}
#     """
#     pass

# @app.delete("/tasks/{id}", response_class=Response)
# async def delete_task(id: int):
#     """
#     DELETE /tasks/{id}
#     """
#     pass
