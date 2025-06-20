# This file previously contained logic for planning chores.
# Basic planning details like notes, due date, and sub-tasks are now
# managed directly within the Task object in `chores.tasks`.

# Advanced planning features, if added in the future (e.g., material estimation,
# time blocking, complex dependency tracking), might utilize this module again
# or a new dedicated planning system.

# (Previous functions like add_plan_details, get_plan_details, remove_plan, clear_all_plans are now obsolete
# in their old form as these details are part of the Task object itself.)

def clear_all_plans():
    """
    Placeholder. If any module-level plan storage were to be reintroduced
    independent of tasks, this would clear it. Currently does nothing
    as planning details are tied to tasks.
    """
    pass
