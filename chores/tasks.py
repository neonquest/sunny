# This file will contain the logic for managing tasks.

from datetime import date
from typing import List, Dict, Any, Optional

_SENTINEL = object() # Sentinel for default arguments to distinguish from None

class Task:
    def __init__(self, description: str, status: str = "pending",
                 notes: str = "", due_date: Optional[date] = None,
                 sub_tasks: Optional[List[Dict[str, Any]]] = None,
                 materials_needed: Optional[List[str]] = None): # New attribute
        self.id: Optional[int] = None
        self.description: str = description
        self.status: str = status
        self.notes: str = notes
        self.due_date: Optional[date] = due_date
        self.sub_tasks: List[Dict[str, Any]] = sub_tasks if sub_tasks is not None else []
        self.materials_needed: List[str] = materials_needed if materials_needed is not None else [] # New attribute

    def __str__(self) -> str:
        due_date_str = f", Due: {self.due_date.isoformat()}" if self.due_date else ""
        notes_str = f", Notes: Yes" if self.notes else ""
        sub_tasks_count = len(self.sub_tasks)
        sub_tasks_str = f", Sub-tasks: {sub_tasks_count}" if sub_tasks_count > 0 else ""
        materials_str = f", Materials: {len(self.materials_needed)}" if self.materials_needed else ""
        return (f"[ID: {self.id}] Task: {self.description} (Status: {self.status}{due_date_str}{notes_str}{sub_tasks_str}{materials_str})")

# No more in-memory storage, _next_id counters. DB handles this.
from . import database # Import the database module

def _row_to_task(row: database.sqlite3.Row) -> Optional[Task]:
    """Converts a database row to a Task object."""
    if not row:
        return None

    due_date_obj = None
    if row['due_date']:
        try:
            due_date_obj = date.fromisoformat(row['due_date'])
        except ValueError:
            print(f"Warning: Could not parse due_date '{row['due_date']}' for task ID {row['id']}")
            due_date_obj = None

    materials_list = []
    if row['materials_needed']:
        # Assuming newline-separated strings in the DB TEXT field
        materials_list = [m.strip() for m in row['materials_needed'].splitlines() if m.strip()]

    task = Task(
        description=row['description'],
        status=row['status'],
        notes=row['notes'] if row['notes'] is not None else "",
        due_date=due_date_obj,
        materials_needed=materials_list
        # sub_tasks are populated by get_sub_tasks_for_task and added in higher-level functions
    )
    task.id = row['id']
    return task

def add_task(description: str, notes: str = "", due_date: Optional[date] = None, materials_needed_text: str = "") -> Task:
    """Adds a new task to the database."""
    due_date_str = due_date.isoformat() if due_date else None
    # materials_needed_text is assumed to be a newline-separated string from a textarea or similar
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO tasks (description, notes, due_date, status, materials_needed) VALUES (?, ?, ?, ?, ?)",
        (description, notes, due_date_str, "pending", materials_needed_text)
    )
    conn.commit()
    new_task_id = cursor.lastrowid
    conn.close()

    materials_list = [m.strip() for m in materials_needed_text.splitlines() if m.strip()]
    created_task = Task(description=description, notes=notes, due_date=due_date, status="pending", materials_needed=materials_list)
    created_task.id = new_task_id
    return created_task


def get_all_tasks() -> List[Task]:
    """Returns all tasks from the database. Sub-tasks are NOT populated yet."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, description, status, notes, due_date, materials_needed FROM tasks ORDER BY id")
    rows = cursor.fetchall()
    conn.close()

    tasks_list = []
    for row in rows:
        task = _row_to_task(row)
        if task:
            # Populate sub_tasks for each task
            task.sub_tasks = get_sub_tasks_for_task(task.id)
            tasks_list.append(task)
    return tasks_list

def get_task_by_id(task_id: int) -> Optional[Task]:
    """Finds a task by its ID from the database. Sub-tasks are NOT populated yet."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, description, status, notes, due_date, materials_needed FROM tasks WHERE id = ?", (task_id,))
    row = cursor.fetchone()
    conn.close()

    task = _row_to_task(row)
    if task:
        # Populate sub_tasks for this specific task
        task.sub_tasks = get_sub_tasks_for_task(task.id)
    return task


def update_task_status(task_id: int, new_status: str) -> Optional[Task]:
    """Updates the status of a specific task in the database."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET status = ? WHERE id = ?", (new_status, task_id))
    conn.commit()

    updated_rows = cursor.rowcount
    conn.close()

    if updated_rows > 0:
        return get_task_by_id(task_id) # Fetch the updated task
    return None


def delete_task(task_id: int) -> bool:
    """Deletes a task by its ID from the database. Sub-tasks are deleted by CASCADE."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    deleted_rows = cursor.rowcount
    conn.close()
    return deleted_rows > 0

def clear_all_tasks():
    """Clears all tasks and sub-tasks from the database. Useful for testing."""
    # This function now directly calls the database clearing function.
    database.clear_db_for_testing()


def update_task_details(task_id: int,
                        description: Any = _SENTINEL,
                        notes: Any = _SENTINEL,
                        due_date: Any = _SENTINEL,
                        materials_needed_text: Any = _SENTINEL) -> Optional[Task]:
    """
    Updates the core details of a specific task, including materials.
    Uses a sentinel to differentiate between passing None and not passing an argument.
    materials_needed_text is expected as a raw string (e.g., from a textarea).
    """
    task_exists = get_task_by_id(task_id)
    if not task_exists:
        return None

    fields_to_update = {}
    if description is not _SENTINEL:
        fields_to_update['description'] = description if description is not None else ""
    if notes is not _SENTINEL:
        fields_to_update['notes'] = notes if notes is not None else ""
    if due_date is not _SENTINEL:
        fields_to_update['due_date'] = due_date.isoformat() if isinstance(due_date, date) else None
    if materials_needed_text is not _SENTINEL:
        # Store as text; conversion to list happens in _row_to_task or Task constructor
        fields_to_update['materials_needed'] = materials_needed_text if materials_needed_text is not None else ""


    if not fields_to_update:
        return task_exists

    set_clause = ", ".join([f"{field} = ?" for field in fields_to_update.keys()])
    values = list(fields_to_update.values())
    values.append(task_id)

    conn = database.get_db_connection()
    cursor = conn.cursor()
    updated_rows = 0
    try:
        cursor.execute(f"UPDATE tasks SET {set_clause} WHERE id = ?", tuple(values))
        conn.commit()
        updated_rows = cursor.rowcount
    except database.sqlite3.Error as e:
        print(f"Database error during task update for task ID {task_id}: {e}")
        conn.rollback() # Rollback on error
    finally:
        conn.close()

    if updated_rows > 0:
        return get_task_by_id(task_id) # Fetch and return the updated task
    else:
        # If no rows updated, but we know the task exists, it might mean an error or no actual change needed
        # We return the task as it was before the attempted update if an error occurred during DB op,
        # or if the values provided happened to be the same as already in DB.
        # get_task_by_id will give the current state from DB.
        return get_task_by_id(task_id)


# --- Sub-task Management ---

# Helper to convert a sub_task DB row to a dictionary
def _row_to_sub_task_dict(row: database.sqlite3.Row) -> Optional[Dict[str, Any]]:
    if not row:
        return None
    return {
        'id': row['id'],
        'task_id': row['task_id'],
        'description': row['description'],
        'completed': bool(row['completed']), # Convert 0/1 to False/True
        'order_index': row['order_index']
    }

def add_sub_task(task_id: int, sub_task_description: str) -> Optional[Dict[str, Any]]:
    """Adds a new sub-task to a given parent task in the database."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    try:
        # Check if parent task exists
        cursor.execute("SELECT id FROM tasks WHERE id = ?", (task_id,))
        parent_task_row = cursor.fetchone()
        if not parent_task_row:
            print(f"Parent task with ID {task_id} not found. Cannot add sub-task.")
            conn.close()
            return None

        # Determine the next order_index
        cursor.execute("SELECT COUNT(*) FROM sub_tasks WHERE task_id = ?", (task_id,))
        count = cursor.fetchone()[0]
        order_index = count # 0-based index for new item

        cursor.execute(
            "INSERT INTO sub_tasks (task_id, description, completed, order_index) VALUES (?, ?, ?, ?)",
            (task_id, sub_task_description, 0, order_index) # completed defaults to 0 (False)
        )
        conn.commit()
        new_sub_task_id = cursor.lastrowid

        # Return the newly created sub-task as a dictionary
        return {
            'id': new_sub_task_id,
            'task_id': task_id,
            'description': sub_task_description,
            'completed': False,
            'order_index': order_index
        }
    except database.sqlite3.Error as e:
        print(f"Database error adding sub_task for task_id {task_id}: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def get_sub_tasks_for_task(task_id: int) -> List[Dict[str, Any]]:
    """Retrieves all sub-tasks for a given parent task_id, ordered by order_index."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, task_id, description, completed, order_index FROM sub_tasks WHERE task_id = ? ORDER BY order_index ASC",
        (task_id,)
    )
    rows = cursor.fetchall()
    conn.close()

    sub_tasks_list = []
    for row in rows:
        st_dict = _row_to_sub_task_dict(row)
        if st_dict:
            sub_tasks_list.append(st_dict)
    return sub_tasks_list

# get_sub_task_by_id is less used now that sub_tasks are part of Task object,
# but can be useful for direct manipulation or if needed.
def get_sub_task_by_id_from_db(sub_task_id: int) -> Optional[Dict[str, Any]]:
    """Finds a specific sub-task by its ID from the database."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, task_id, description, completed, order_index FROM sub_tasks WHERE id = ?",
        (sub_task_id,)
    )
    row = cursor.fetchone()
    conn.close()
    return _row_to_sub_task_dict(row)


def update_sub_task(sub_task_id: int,
                    description: Any = _SENTINEL,
                    completed: Any = _SENTINEL) -> Optional[Dict[str, Any]]:
    """Updates a sub-task's description or completed status in the database."""
    current_sub_task = get_sub_task_by_id_from_db(sub_task_id)
    if not current_sub_task:
        return None

    fields_to_update = {}
    if description is not _SENTINEL:
        fields_to_update['description'] = description if description is not None else ""
    if completed is not _SENTINEL:
        fields_to_update['completed'] = 1 if completed else 0 # Convert boolean to int

    if not fields_to_update:
        return current_sub_task # No actual update values passed

    set_clause = ", ".join([f"{field} = ?" for field in fields_to_update.keys()])
    values = list(fields_to_update.values())
    values.append(sub_task_id)

    conn = database.get_db_connection()
    cursor = conn.cursor()
    updated_rows = 0
    try:
        cursor.execute(f"UPDATE sub_tasks SET {set_clause} WHERE id = ?", tuple(values))
        conn.commit()
        updated_rows = cursor.rowcount
    except database.sqlite3.Error as e:
        print(f"Database error updating sub_task ID {sub_task_id}: {e}")
        conn.rollback()
    finally:
        conn.close()

    if updated_rows > 0:
        return get_sub_task_by_id_from_db(sub_task_id)
    return current_sub_task # Return current state if update failed or made no changes


def delete_sub_task(sub_task_id: int) -> bool:
    """Deletes a sub-task by its ID from the database."""
    conn = database.get_db_connection()
    cursor = conn.cursor()
    deleted_rows = 0
    try:
        cursor.execute("DELETE FROM sub_tasks WHERE id = ?", (sub_task_id,))
        conn.commit()
        deleted_rows = cursor.rowcount
    except database.sqlite3.Error as e:
        print(f"Database error deleting sub_task ID {sub_task_id}: {e}")
        conn.rollback()
    finally:
        conn.close()
    return deleted_rows > 0

def move_sub_task(task_id: int, sub_task_id: int, direction: str) -> bool:
    """Moves a sub-task up or down, updating order_index in the database."""
    conn = database.get_db_connection()
    cursor = conn.cursor()

    try:
        # Get all sub-tasks for the parent task, ordered
        cursor.execute("SELECT id, order_index FROM sub_tasks WHERE task_id = ? ORDER BY order_index ASC", (task_id,))
        sub_tasks_ordered = cursor.fetchall()

        if not sub_tasks_ordered:
            return False # No sub-tasks for this parent

        current_index = -1
        for i, st_row in enumerate(sub_tasks_ordered):
            if st_row['id'] == sub_task_id:
                current_index = i
                break

        if current_index == -1:
            return False # Sub-task not found in this parent's list

        num_sub_tasks = len(sub_tasks_ordered)

        if direction == 'up':
            if current_index == 0: return False # Already at top
            target_index = current_index - 1
            # Swap order_index with the item currently at target_index
            st_to_move_id = sub_tasks_ordered[current_index]['id']
            st_other_id = sub_tasks_ordered[target_index]['id']

            # Start transaction
            cursor.execute("BEGIN TRANSACTION;")
            # Temporarily give st_to_move_id a placeholder index to avoid unique constraint violation if swapping directly
            # A common way is to update both:
            # Item moving up gets the lower index, item moving down gets the higher index.
            cursor.execute("UPDATE sub_tasks SET order_index = ? WHERE id = ?", (target_index, st_to_move_id))
            cursor.execute("UPDATE sub_tasks SET order_index = ? WHERE id = ?", (current_index, st_other_id))
            conn.commit()
            return True

        elif direction == 'down':
            if current_index == num_sub_tasks - 1: return False # Already at bottom
            target_index = current_index + 1
            # Swap order_index
            st_to_move_id = sub_tasks_ordered[current_index]['id']
            st_other_id = sub_tasks_ordered[target_index]['id']

            cursor.execute("BEGIN TRANSACTION;")
            cursor.execute("UPDATE sub_tasks SET order_index = ? WHERE id = ?", (target_index, st_to_move_id))
            cursor.execute("UPDATE sub_tasks SET order_index = ? WHERE id = ?", (current_index, st_other_id))
            conn.commit()
            return True
        else:
            return False # Invalid direction

    except database.sqlite3.Error as e:
        print(f"Database error moving sub_task ID {sub_task_id} for task ID {task_id}: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
