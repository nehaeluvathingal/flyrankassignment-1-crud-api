# Task API - FastAPI CRUD Application

A beginner-friendly, in-memory CRUD API built using Python 3.10+ and FastAPI. This project serves as an introduction to constructing RESTful web services, validating request bodies with Pydantic, and managing API endpoints.

---

## Features
- **Full CRUD Support**: Create, read, update, and delete tasks dynamically.
- **In-Memory Data Store**: Works out-of-the-box without requiring database installation or setup.
- **Seeded Data**: Pre-populated with 3 example tasks for quick testing.
- **Input Validation**: Uses Pydantic models to validate input data type constraints and enforce required fields.
- **Custom Error Handling**: Returns HTTP 400 instead of the default 422 for malformed/empty payloads.
- **Interactive Documentation**: Auto-generated Swagger UI for browser-based testing.

---

## Requirements
- Python 3.10 or higher
- Pip package manager

---

## Installation

1. **Clone or Download the Repository**:
   Clone or download this project folder into your workspace.

2. **Open Terminal**:
   Navigate to the project root directory.

3. **Install Dependencies**:
   Install the required Python packages using pip:
   ```bash
   pip install -r requirements.txt
   ```

---

## Running the Server

Start the development server using Uvicorn:
```bash
uvicorn main:app --reload
```

- `--reload` enables auto-reload, meaning the server will restart automatically when files are modified.
- The server will run at: **http://localhost:8000**

---

## Interactive API Documentation (Swagger UI)

FastAPI provides an out-of-the-box UI to visualize and test your API endpoints. 

Access the documentation at:
👉 **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

## API Endpoints

| Method | Endpoint | Description | Success Status | Error Status |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/` | Retrieve API metadata | `200 OK` | - |
| **GET** | `/health` | Verify server health status | `200 OK` | - |
| **GET** | `/tasks` | List all tasks | `200 OK` | - |
| **GET** | `/tasks/{id}` | Retrieve a single task by ID | `200 OK` | `404 Not Found` |
| **POST** | `/tasks` | Create a new task (auto-assign ID) | `201 Created` | `400 Bad Request` |
| **PUT** | `/tasks/{id}` | Update title and/or status of a task | `200 OK` | `400 Bad Request`, `404 Not Found` |
| **DELETE**| `/tasks/{id}` | Remove a task by ID (returns empty response) | `204 No Content` | `404 Not Found` |

---

## Example Usage and Responses

### 1. Retrieve Metadata
**Request**:
```bash
curl -X GET http://localhost:8000/
```
**Response (`200 OK`)**:
```json
{
  "name": "Task API",
  "version": "1.0",
  "endpoints": ["/tasks"]
}
```

### 2. Create a Task (Valid)
**Request**:
```bash
curl -X POST http://localhost:8000/tasks \
     -H "Content-Type: application/json" \
     -d '{"title": "Buy milk"}'
```
**Response (`201 Created`)**:
```json
{
  "id": 4,
  "title": "Buy milk",
  "done": false
}
```

### 3. Create a Task (Invalid - Empty Title)
**Request**:
```bash
curl -X POST http://localhost:8000/tasks \
     -H "Content-Type: application/json" \
     -d '{"title": ""}'
```
**Response (`400 Bad Request`)**:
```json
{
  "error": "Invalid request body. Details: Field 'body -> title': Value error, Title is required and cannot be empty"
}
```

### 4. Update a Task
**Request**:
```bash
curl -X PUT http://localhost:8000/tasks/1 \
     -H "Content-Type: application/json" \
     -d '{"title": "Buy groceries and snacks", "done": true}'
```
**Response (`200 OK`)**:
```json
{
  "id": 1,
  "title": "Buy groceries and snacks",
  "done": true
}
```

### 5. Delete a Task
**Request**:
```bash
curl -X DELETE http://localhost:8000/tasks/1
```
**Response (`204 No Content`)**:
*(No response body returned)*

---

## Project Structure

```text
Assignment 1/
├── main.py             # Single-file FastAPI CRUD implementation
├── requirements.txt    # Python dependencies (FastAPI, Uvicorn, Pydantic)
└── README.md           # Getting started guide and API documentation
```

---

## Future Improvements
- **Persistent Data Store**: Add SQL Database integration (such as SQLite or PostgreSQL) using SQLAlchemy or SQLModel.
- **User Authentication**: Implement user registration and token-based authentication (OAuth2 / JWT tokens) to secure individual tasks.
- **Unit & Integration Tests**: Implement test automation using `pytest` and FastAPI's `TestClient` to prevent regressions.
- **Task Attributes**: Add extra attributes like priority levels, due dates, and categories.
