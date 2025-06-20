# This file will contain the logic for managing tasks.

class Task:
    def __init__(self, description, status="pending"):
        self.id = None # Will be assigned when added to the list
        self.description = description
        self.status = status # e.g., "pending", "in progress", "completed"

    def __str__(self):
        return f"[ID: {self.id}] Task: {self.description} (Status: {self.status})"

# In-memory storage for tasks
_tasks_db = []
_next_task_id = 1

def add_task(description: str) -> Task:
    """Adds a new task to the list."""
    global _next_task_id
    new_task = Task(description=description)
    new_task.id = _next_task_id
    _tasks_db.append(new_task)
    _next_task_id += 1
    return new_task

def get_all_tasks() -> list[Task]:
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
    global _tasks_db, _next_task_id
    _tasks_db = []
    _next_task_id = 1
