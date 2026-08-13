import os
import psycopg
from dotenv import load_dotenv

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
