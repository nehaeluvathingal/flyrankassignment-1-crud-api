# Task API - Containerized CRUD Application with PostgreSQL

A CRUD API built using Python 3.11, FastAPI, PostgreSQL, and Docker Compose. This project demonstrates migrating database-backed persistence from SQLite to a dockerized PostgreSQL container, isolating database logic in a repository layer, custom input validation using Pydantic, and containerized deployment with volumes for persistent storage.

---

## Why PostgreSQL?
For this project, **PostgreSQL** was selected as the database engine instead of SQLite because:
- **Scalability & Concurrency**: PostgreSQL is a robust, client-server relational database that supports multiple concurrent connections and complex transactions, making it suitable for production environments.
- **Enterprise-Grade Features**: Offers rich support for advanced data types, indexing strategies, and database extensions.
- **Production Alignment**: Containerizing PostgreSQL aligns the development environment database system with actual production environments.

---

## Architecture
The application architecture is cleanly separated to isolate database storage operations from network handling:

```
Client ──> FastAPI routes (main.py) ──> repository.py ──> PostgreSQL (Docker)
```

- **Separation of Concerns**: The API contract, routes, request/response formats, and externally visible behavior remained unchanged, while the storage implementation was migrated behind `repository.py`.
- **Single Source of Truth**: PostgreSQL serves as the only source of truth for task storage. SQLite and in-memory caching are not used.

---

## Environment Configuration
The database connection string is managed via environment variables:
- **`.env`**: Contains the local database connection URL:
  `DATABASE_URL=postgres://<user>:<password>@<host>:5432/<database>`
- **Git Ignore**: The `.env` file contains sensitive credentials and is listed in `.gitignore` so it is never committed to source control.
- **`.env.example`**: A committed template file documenting the required environment variables:
  `DATABASE_URL=postgres://username:password@localhost:5432/database_name`

---

## Running the Containerized Stack

### Prerequisites
Make sure you have **Docker** and **Docker Desktop** installed and running on your system.

### Starting the Services
To build and run the entire application stack (API server and database) together, navigate to the project root directory and run:
```bash
docker compose up
```
To run the containers in the background (detached mode), use:
```bash
docker compose up -d
```
The FastAPI application will be accessible at: **http://localhost:8000**

### Compose Services Explained
Docker Compose orchestrates two key services defined in `docker-compose.yml`:
1. **`db`**: Runs a `postgres:16` database instance. It includes a healthcheck using `pg_isready -U postgres -d tasks` to ensure it is healthy and ready to accept connections.
2. **`app`**: Builds the custom FastAPI application container from the project's local `Dockerfile`. It uses `depends_on` with `condition: service_healthy` to wait for the database container to be healthy before starting.

---

## Data Persistence & Volume Management
Database records are stored in a persistent Docker named volume named **`pgdata`**, mounted to `/var/lib/postgresql/data` inside the `db` container.
- **Volume Survivability**: PostgreSQL records survive container restarts and stops. Running:
  ```bash
  docker compose down
  ```
  followed by:
  ```bash
  docker compose up
  ```
  will retain all custom task items.
- **Persistence Caveat**: Do **NOT** use `docker compose down -v` when stopping the stack, as the `-v` flag will destroy the `pgdata` volume and delete all stored database data.

---

## API Endpoints

| Method | Endpoint | Description | Success Status | Error Status |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/` | Retrieve API metadata | `200 OK` | - |
| **GET** | `/health` | Verify server health status | `200 OK` | - |
| **GET** | `/tasks` | List all tasks | `200 OK` | - |
| **GET** | `/tasks/{id}` | Retrieve a single task by ID | `200 OK` | `404 Not Found` |
| **POST** | `/tasks` | Create a new task (auto-generates ID) | `201 Created` | `400 Bad Request` |
| **PUT** | `/tasks/{id}` | Update title and/or status of a task | `200 OK` | `400 Bad Request`, `404 Not Found` |
| **DELETE**| `/tasks/{id}` | Remove a task by ID (returns empty response) | `204 No Content` | `404 Not Found` |

### Endpoint Status & Response Behaviors:
- **POST** requests return `201 Created` on successful creation.
- **PUT** requests return `200 OK` with the merged updated fields.
- **DELETE** requests return `204 No Content` with a completely empty body.
- Requests with an **unknown ID** return `404 Not Found` with payload: `{"error": "Task {id} not found"}`.
- Malformed payloads (e.g. empty or missing titles) return `400 Bad Request` with validation error details.

---

## Database Exploration & Verification

### Example SQL Query
To inspect all stored tasks directly inside the PostgreSQL database container, run:
```bash
docker exec compose_db psql -U postgres -d tasks -c "SELECT * FROM tasks;"
```
* **Explanation**: This query selects and displays all columns (`id`, `title`, `done`) and all rows currently saved inside the `tasks` table.

---

## Persistence Verification Steps
To verify that database writes survive container shutdowns:
1. **Create a task** using an HTTP client:
   ```bash
   curl -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d '{"title": "Persistent container task"}'
   ```
2. **Stop the stack**:
   ```bash
   docker compose down
   ```
3. **Start the stack again**:
   ```bash
   docker compose up -d
   ```
4. **Fetch all tasks**:
   ```bash
   curl -X GET http://localhost:8000/tasks
   ```
   The response contains `"Persistent container task"`, demonstrating that the data successfully survived the compose shutdown via the `pgdata` volume.

---

## Project Structure

```text
Assignment 1/
├── Dockerfile          # Installs dependencies and runs the FastAPI server
├── docker-compose.yml  # Configures app and db services and pgdata named volume
├── main.py             # FastAPI App with clean abstraction calling repository
├── repository.py       # PostgreSQL database connection and CRUD statements
├── requirements.txt    # Python dependencies (psycopg[binary] and python-dotenv)
├── .env.example        # Reference environment template with placeholder values
└── .gitignore          # Ignores transient database and credentials files
```

