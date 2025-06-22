import sqlite3
import os

# Determine the path for the database file.
# Place it in the instance folder if using Flask, or project root for simplicity here.
DATABASE_FILE = os.path.join(os.path.dirname(__file__), '..', 'chores_app.db')
# This places chores_app.db in the project root directory.

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row # Access columns by name
    return conn

def init_db(conn = None):
    """
    Initializes the database by creating tables if they don't already exist.
    If a connection is passed, it uses it; otherwise, it creates a new one.
    """
    should_close_conn = False
    if conn is None:
        conn = get_db_connection()
        should_close_conn = True

    cursor = conn.cursor()

    # Create tasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        description TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'pending',
        notes TEXT,
        due_date TEXT, -- Store dates as ISO8601 strings (YYYY-MM-DD)
        materials_needed TEXT -- Can store comma-separated list, JSON, or newline-separated text
    );
    """)

    # Create sub_tasks table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sub_tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        description TEXT NOT NULL,
        completed INTEGER NOT NULL DEFAULT 0, -- 0 for False, 1 for True
        order_index INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (task_id) REFERENCES tasks (id) ON DELETE CASCADE
    );
    """)
    # ON DELETE CASCADE ensures sub_tasks are deleted if their parent task is deleted.

    conn.commit()

    if should_close_conn:
        conn.close()

def clear_db_for_testing(conn = None):
    """
    Clears all data from tasks and sub_tasks tables. Used for testing.
    If a connection is passed, it uses it; otherwise, it creates a new one.
    """
    should_close_conn = False
    if conn is None:
        conn = get_db_connection()
        should_close_conn = True

    cursor = conn.cursor()
    # Drop tables to ensure schema is recreated by init_db if it changed
    cursor.execute("DROP TABLE IF EXISTS sub_tasks;")
    cursor.execute("DROP TABLE IF EXISTS tasks;")
    conn.commit() # Commit drops before recreating

    # Re-initialize the schema
    init_db(conn=conn) # Pass the existing connection

    # clear_db_for_testing used to also reset sequences, but init_db will create fresh tables
    # so sequences are implicitly reset. If init_db didn't drop/create but only
    # CREATE IF NOT EXISTS, then sequence reset might be needed here.
    # Given init_db is now called after drop, this is fine.

    if should_close_conn:
        conn.close()


if __name__ == '__main__':
    # For manual initialization if needed
    print(f"Initializing database at {DATABASE_FILE}...")
    init_db()
    print("Database initialized.")
    # Example of clearing for manual testing:
    # print("Clearing database for testing...")
    # clear_db_for_testing()
    # print("Database cleared.")
