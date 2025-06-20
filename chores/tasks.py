# This file will contain the logic for managing tasks.

from datetime import date
from typing import List, Dict, Any, Optional

_SENTINEL = object() # Sentinel for default arguments to distinguish from None

class Task:
    def __init__(self, description: str, status: str = "pending",
                 notes: str = "", due_date: Optional[date] = None,
                 sub_tasks: Optional[List[Dict[str, Any]]] = None):
        self.id: Optional[int] = None  # Will be assigned when added to the list
        self.description: str = description
        self.status: str = status  # e.g., "pending", "in progress", "completed"
        self.notes: str = notes
        self.due_date: Optional[date] = due_date
        self.sub_tasks: List[Dict[str, Any]] = sub_tasks if sub_tasks is not None else []
        # Each sub_task could be: {'description': str, 'completed': bool, 'id': int}

    def __str__(self) -> str:
        due_date_str = f", Due: {self.due_date.isoformat()}" if self.due_date else ""
        notes_str = f", Notes: Yes" if self.notes else ""
        sub_tasks_count = len(self.sub_tasks)
        sub_tasks_str = f", Sub-tasks: {sub_tasks_count}" if sub_tasks_count > 0 else ""
        return (f"[ID: {self.id}] Task: {self.description} (Status: {self.status}{due_date_str}{notes_str}{sub_tasks_str})")

# In-memory storage for tasks
_tasks_db: List[Task] = []
_next_task_id: int = 1
_next_sub_task_id: int = 1 # For uniquely identifying sub_tasks if needed for direct manipulation

def add_task(description: str, notes: str = "", due_date: Optional[date] = None) -> Task:
    """Adds a new task to the list."""
    global _next_task_id
    new_task = Task(description=description, notes=notes, due_date=due_date)
    new_task.id = _next_task_id
    _tasks_db.append(new_task)
    _next_task_id += 1
    return new_task

def get_all_tasks() -> List[Task]:
    """Returns all tasks."""
    return _tasks_db

def get_task_by_id(task_id: int) -> Task | None:
    """Finds a task by its ID."""
    for task in _tasks_db:
        if task.id == task_id:
            return task
    return None

def update_task_status(task_id: int, new_status: str) -> Task | None:
    """Updates the status of a specific task."""
    task = get_task_by_id(task_id)
    if task:
        task.status = new_status
        return task
    return None

def delete_task(task_id: int) -> bool:
    """Deletes a task by its ID."""
    task = get_task_by_id(task_id)
    if task:
        _tasks_db.remove(task)
        return True
    return False

def clear_all_tasks():
    """Clears all tasks from the database. Useful for testing."""
    global _tasks_db, _next_task_id, _next_sub_task_id
    _tasks_db = []
    _next_task_id = 1
    _next_sub_task_id = 1

def update_task_details(task_id: int,
                        description: Any = _SENTINEL,
                        notes: Any = _SENTINEL,
                        due_date: Any = _SENTINEL) -> Optional[Task]:
    """
    Updates the core details of a specific task.
    Uses a sentinel to differentiate between passing None and not passing an argument.
    """
    task = get_task_by_id(task_id)
    if task:
        if description is not _SENTINEL:
            task.description = description if description is not None else "" # Ensure description is not None
        if notes is not _SENTINEL:
            task.notes = notes if notes is not None else "" # Ensure notes is not None
        if due_date is not _SENTINEL:
            task.due_date = due_date # This can be a date object or None
        return task
    return None

# --- Sub-task Management ---

def add_sub_task(task_id: int, sub_task_description: str) -> Dict[str, Any] | None:
    """Adds a new sub-task to a given parent task."""
    global _next_sub_task_id
    task = get_task_by_id(task_id)
    if task:
        new_sub_task = {
            'id': _next_sub_task_id,
            'description': sub_task_description,
            'completed': False
        }
        task.sub_tasks.append(new_sub_task)
        _next_sub_task_id += 1
        return new_sub_task
    return None

def get_sub_task_by_id(task: Task, sub_task_id: int) -> Dict[str, Any] | None:
    """Finds a sub-task by its ID within a parent task."""
    for sub_task in task.sub_tasks:
        if sub_task['id'] == sub_task_id:
            return sub_task
    return None

def update_sub_task(task_id: int, sub_task_id: int,
                    description: Optional[str] = None, completed: Optional[bool] = None) -> Dict[str, Any] | None:
    """Updates a sub-task's description or completed status."""
    task = get_task_by_id(task_id)
    if task:
        sub_task = get_sub_task_by_id(task, sub_task_id)
        if sub_task:
            if description is not None:
                sub_task['description'] = description
            if completed is not None:
                sub_task['completed'] = completed
            return sub_task
    return None

def delete_sub_task(task_id: int, sub_task_id: int) -> bool:
    """Deletes a sub-task from a parent task."""
    task = get_task_by_id(task_id)
    if task:
        sub_task = get_sub_task_by_id(task, sub_task_id)
        if sub_task:
            task.sub_tasks.remove(sub_task)
            return True
    return False

def move_sub_task(task_id: int, sub_task_id: int, direction: str) -> bool:
    """Moves a sub-task up or down in the sub_tasks list of a parent task."""
    task = get_task_by_id(task_id)
    if not task:
        return False

    sub_task_to_move = None
    current_index = -1
    for i, st in enumerate(task.sub_tasks):
        if st['id'] == sub_task_id:
            sub_task_to_move = st
            current_index = i
            break

    if sub_task_to_move is None:
        return False # Sub-task not found

    if direction == 'up':
        if current_index == 0:
            return False # Already at the top
        new_index = current_index - 1
    elif direction == 'down':
        if current_index == len(task.sub_tasks) - 1:
            return False # Already at the bottom
        new_index = current_index + 1
    else:
        return False # Invalid direction

    # Perform the move
    task.sub_tasks.pop(current_index)
    task.sub_tasks.insert(new_index, sub_task_to_move)
    return True
