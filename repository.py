import os
import psycopg
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any

# Load environment variables from .env file
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db_connection():
    """
    Helper to establish a connection to the PostgreSQL database.
    """
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL is not set in the environment variables.")
    return psycopg.connect(DATABASE_URL)

def init_db():
    """
    Establish PostgreSQL connection, create the tasks table, and insert seed data if empty.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            # Create the tasks table automatically if it does not exist
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    done BOOLEAN NOT NULL DEFAULT FALSE
                )
            """)
            conn.commit()
            
            # Check if the tasks table is empty to avoid duplicating seed tasks
            cursor.execute("SELECT COUNT(*) FROM tasks")
            count = cursor.fetchone()[0]
            
            if count == 0:
                # Insert exactly three example tasks using parameterized SQL (%s)
                example_tasks = [
                    (1, "Buy groceries", False),
                    (2, "Clean the house", True),
                    (3, "Read a book", False)
                ]
                cursor.executemany("INSERT INTO tasks (id, title, done) VALUES (%s, %s, %s)", example_tasks)
                
                # Reset PostgreSQL serial sequence tracker so subsequent auto-increment IDs start at 4
                cursor.execute("SELECT setval(pg_get_serial_sequence('tasks', 'id'), COALESCE(MAX(id), 1)) FROM tasks")
                conn.commit()

def get_tasks() -> List[Dict[str, Any]]:
    """
    Retrieve all tasks from PostgreSQL database.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, title, done FROM tasks ORDER BY id")
            rows = cursor.fetchall()
            
    return [{"id": row[0], "title": row[1], "done": bool(row[2])} for row in rows]

def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    """
    Retrieve a single task by ID from PostgreSQL database.
    """
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, title, done FROM tasks WHERE id = %s", (task_id,))
            row = cursor.fetchone()
            
    if row:
        return {"id": row[0], "title": row[1], "done": bool(row[2])}
    return None
