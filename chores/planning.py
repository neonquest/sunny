# This file will contain the logic for planning chores.
from typing import Any, Dict

# In-memory storage for plans. Key is task_id.
_task_plans: Dict[int, Dict[str, Any]] = {}

def add_plan_details(task_id: int, details: Dict[str, Any]) -> bool:
    """
    Adds or updates planning details for a given task_id.
    Details could include notes, due_date, materials, etc.
    Returns True if successful, False if task_id is invalid (though we don't check that here yet).
    """
    _task_plans[task_id] = details
    return True

def get_plan_details(task_id: int) -> Dict[str, Any] | None:
    """
    Retrieves the planning details for a given task_id.
    Returns the details dictionary or None if no plan exists for the task.
    """
    return _task_plans.get(task_id)

def remove_plan(task_id: int) -> bool:
    """
    Removes the plan associated with a task_id.
    Returns True if a plan was removed, False otherwise.
    """
    if task_id in _task_plans:
        del _task_plans[task_id]
        return True
    return False

def clear_all_plans():
    """Clears all plans. Useful for testing."""
    global _task_plans
    _task_plans = {}
