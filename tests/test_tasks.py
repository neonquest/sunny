# This file will contain tests for the task management functionality.

import unittest
from chores import tasks # Import the tasks module

from datetime import date

class TestTaskManagement(unittest.TestCase):

    def setUp(self):
        """Clear all tasks before each test."""
        tasks.clear_all_tasks()

    def tearDown(self):
        """Clear all tasks after each test to ensure isolation."""
        tasks.clear_all_tasks()

    def test_create_task_object_defaults(self):
        """Test basic Task object creation with defaults."""
        task_obj = tasks.Task("Test Description")
        self.assertEqual(task_obj.description, "Test Description")
        self.assertEqual(task_obj.status, "pending")
        self.assertEqual(task_obj.notes, "")
        self.assertIsNone(task_obj.due_date)
        self.assertEqual(task_obj.sub_tasks, [])
        self.assertIsNone(task_obj.id) # ID will be None until added by add_task

    def test_create_task_object_with_all_fields(self):
        """Test Task object creation with all fields specified."""
        test_date = date(2024, 1, 15)
        sub_tasks_list = [{'id': 1, 'description': 'sub1', 'completed': False}]
        task_obj = tasks.Task(
            description="Full Task",
            status="in progress",
            notes="Important notes here.",
            due_date=test_date,
            sub_tasks=sub_tasks_list
        )
        self.assertEqual(task_obj.description, "Full Task")
        self.assertEqual(task_obj.status, "in progress")
        self.assertEqual(task_obj.notes, "Important notes here.")
        self.assertEqual(task_obj.due_date, test_date)
        self.assertEqual(task_obj.sub_tasks, sub_tasks_list)


    def test_add_task_basic(self):
        """Test adding a single task with only description."""
        task = tasks.add_task("Fix the shower door")
        self.assertIsNotNone(task.id, "Task ID should be set after adding.")
        self.assertEqual(task.description, "Fix the shower door")
        self.assertEqual(task.status, "pending") # Default status
        self.assertEqual(task.notes, "")       # Default notes
        self.assertIsNone(task.due_date)       # Default due_date
        self.assertEqual(task.sub_tasks, [])   # Default sub_tasks
        self.assertEqual(len(tasks.get_all_tasks()), 1)
        self.assertEqual(tasks.get_all_tasks()[0], task)

    def test_add_task_with_details(self):
        """Test adding a task with notes and due date."""
        test_date = date(2024, 5, 20)
        task = tasks.add_task("Plan vacation", notes="Research destinations", due_date=test_date)
        self.assertEqual(task.description, "Plan vacation")
        self.assertEqual(task.notes, "Research destinations")
        self.assertEqual(task.due_date, test_date)
        self.assertEqual(len(tasks.get_all_tasks()), 1)


    def test_add_multiple_tasks(self):
        """Test adding multiple tasks and check IDs are unique and sequential."""
        task1 = tasks.add_task("Task 1")
        task2 = tasks.add_task("Task 2")
        self.assertNotEqual(task1.id, task2.id, "Task IDs should be unique.")
        self.assertEqual(task1.id, 1)
        self.assertEqual(task2.id, 2)
        self.assertEqual(len(tasks.get_all_tasks()), 2)

    def test_get_all_tasks(self):
        """Test retrieving all tasks."""
        self.assertEqual(len(tasks.get_all_tasks()), 0) # Initially empty
        tasks.add_task("Task A")
        tasks.add_task("Task B")
        all_tasks_list = tasks.get_all_tasks()
        self.assertEqual(len(all_tasks_list), 2)
        self.assertEqual(all_tasks_list[0].description, "Task A")
        self.assertEqual(all_tasks_list[1].description, "Task B")

    def test_get_task_by_id(self):
        """Test retrieving a task by its ID."""
        task1 = tasks.add_task("Find this task")
        tasks.add_task("Another task")

        found_task = tasks.get_task_by_id(task1.id)
        self.assertIsNotNone(found_task)
        self.assertEqual(found_task, task1)

        non_existent_task = tasks.get_task_by_id(999) # Assuming 999 is not a valid ID
        self.assertIsNone(non_existent_task, "Should return None for non-existent ID.")

    def test_update_task_status(self):
        """Test updating the status of a task."""
        task = tasks.add_task("Original task")
        updated_task = tasks.update_task_status(task.id, "in progress")
        self.assertIsNotNone(updated_task)
        self.assertEqual(updated_task.status, "in progress")

        # Verify the task in the list is updated
        retrieved_task = tasks.get_task_by_id(task.id)
        self.assertEqual(retrieved_task.status, "in progress")

        # Test updating non-existent task
        non_updated_task = tasks.update_task_status(999, "completed")
        self.assertIsNone(non_updated_task, "Should return None for non-existent ID.")

    def test_delete_task(self):
        """Test deleting a task."""
        task1 = tasks.add_task("To be deleted")
        task2 = tasks.add_task("To be kept")

        self.assertEqual(len(tasks.get_all_tasks()), 2)

        delete_result = tasks.delete_task(task1.id)
        self.assertTrue(delete_result, "delete_task should return True on success.")
        self.assertEqual(len(tasks.get_all_tasks()), 1)

        remaining_task = tasks.get_all_tasks()[0]
        self.assertEqual(remaining_task, task2)

        # Test deleting non-existent task
        delete_non_existent_result = tasks.delete_task(999)
        self.assertFalse(delete_non_existent_result, "delete_task should return False for non-existent ID.")
        self.assertEqual(len(tasks.get_all_tasks()), 1) # Count should remain unchanged

    def test_task_str_representation(self):
        """Test the string representation of a Task object after it's added."""
        task = tasks.add_task("Clean the garage")
        task.notes = "Broom and dustpan"
        task.due_date = date(2024,12,31)
        tasks.add_sub_task(task.id, "Sweep floor")
        tasks.update_task_status(task.id, "in progress")

        expected_str = f"[ID: {task.id}] Task: Clean the garage (Status: in progress, Due: 2024-12-31, Notes: Yes, Sub-tasks: 1)"
        self.assertEqual(str(task), expected_str)

    def test_clear_all_tasks(self):
        """Test clearing all tasks, including sub-task ID counter."""
        tasks.add_task("Task 1")
        tasks.add_task("Task 2")
        self.assertEqual(len(tasks.get_all_tasks()), 2)
        tasks.clear_all_tasks()
        self.assertEqual(len(tasks.get_all_tasks()), 0)
        # Check if _next_task_id is reset
        task_after_clear = tasks.add_task("New Task")
        self.assertEqual(task_after_clear.id, 1, "Next task ID should be reset to 1 after clear.")
        # Check if _next_sub_task_id is reset
        sub_task_after_clear = tasks.add_sub_task(task_after_clear.id, "New Sub-task")
        self.assertEqual(sub_task_after_clear['id'], 1, "Next sub-task ID should be reset to 1 after clear.")

    def test_update_task_details(self):
        """Test updating various details of a task."""
        task = tasks.add_task("Initial Description", notes="Initial notes", due_date=date(2023,1,1))

        # Update all details
        updated_desc = "Updated Description"
        updated_notes = "Updated notes."
        updated_due_date = date(2024,2,2)
        tasks.update_task_details(task.id, description=updated_desc, notes=updated_notes, due_date=updated_due_date)

        retrieved_task = tasks.get_task_by_id(task.id)
        self.assertEqual(retrieved_task.description, updated_desc)
        self.assertEqual(retrieved_task.notes, updated_notes)
        self.assertEqual(retrieved_task.due_date, updated_due_date)

        # Update only notes
        tasks.update_task_details(task.id, notes="Only notes updated")
        retrieved_task = tasks.get_task_by_id(task.id)
        self.assertEqual(retrieved_task.description, updated_desc) # Should remain unchanged
        self.assertEqual(retrieved_task.notes, "Only notes updated")
        self.assertEqual(retrieved_task.due_date, updated_due_date) # Should remain unchanged

        # Remove due date
        tasks.update_task_details(task.id, due_date=None)
        retrieved_task = tasks.get_task_by_id(task.id)
        self.assertIsNone(retrieved_task.due_date)

        # Test updating non-existent task
        non_updated_task = tasks.update_task_details(999, description="no such task")
        self.assertIsNone(non_updated_task)

# --- Sub-task specific tests ---
    def test_add_sub_task(self):
        """Test adding a sub-task to a parent task."""
        parent_task = tasks.add_task("Parent Task")
        sub_task_1 = tasks.add_sub_task(parent_task.id, "Sub-task 1")

        self.assertIsNotNone(sub_task_1)
        self.assertEqual(sub_task_1['description'], "Sub-task 1")
        self.assertFalse(sub_task_1['completed'])
        self.assertIsNotNone(sub_task_1['id'])

        self.assertEqual(len(parent_task.sub_tasks), 1)
        self.assertEqual(parent_task.sub_tasks[0], sub_task_1)

        sub_task_2 = tasks.add_sub_task(parent_task.id, "Sub-task 2")
        self.assertEqual(len(parent_task.sub_tasks), 2)
        self.assertNotEqual(sub_task_1['id'], sub_task_2['id'], "Sub-task IDs should be unique.")

        # Test adding to non-existent parent task
        non_existent_sub_task = tasks.add_sub_task(999, "Sub for non-existent task")
        self.assertIsNone(non_existent_sub_task)

    def test_get_sub_task_by_id(self):
        """Test retrieving a sub-task by its ID from a parent."""
        parent_task = tasks.add_task("Parent")
        st1 = tasks.add_sub_task(parent_task.id, "ST1")
        st2 = tasks.add_sub_task(parent_task.id, "ST2")

        found_st1 = tasks.get_sub_task_by_id(parent_task, st1['id'])
        self.assertEqual(found_st1, st1)

        found_st_non_existent = tasks.get_sub_task_by_id(parent_task, 9999)
        self.assertIsNone(found_st_non_existent)

    def test_update_sub_task(self):
        """Test updating a sub-task's description and completion status."""
        parent_task = tasks.add_task("Parent for sub-task update")
        sub_task = tasks.add_sub_task(parent_task.id, "Original sub-task desc")

        # Update description
        updated_sub_task_desc = tasks.update_sub_task(parent_task.id, sub_task['id'], description="New sub-task desc")
        self.assertEqual(updated_sub_task_desc['description'], "New sub-task desc")
        self.assertFalse(updated_sub_task_desc['completed']) # Should remain unchanged

        # Update completion status
        updated_sub_task_completed = tasks.update_sub_task(parent_task.id, sub_task['id'], completed=True)
        self.assertEqual(updated_sub_task_completed['description'], "New sub-task desc") # Should remain unchanged
        self.assertTrue(updated_sub_task_completed['completed'])

        # Update both
        updated_sub_task_both = tasks.update_sub_task(parent_task.id, sub_task['id'], description="Final Desc", completed=False)
        self.assertEqual(updated_sub_task_both['description'], "Final Desc")
        self.assertFalse(updated_sub_task_both['completed'])

        # Test updating non-existent sub-task
        non_updated_sub = tasks.update_sub_task(parent_task.id, 999, description="no such sub")
        self.assertIsNone(non_updated_sub)

        # Test updating sub-task of non-existent parent task
        non_updated_sub_parent = tasks.update_sub_task(999, 1, description="no such parent")
        self.assertIsNone(non_updated_sub_parent)


    def test_delete_sub_task(self):
        """Test deleting a sub-task from a parent task."""
        parent_task = tasks.add_task("Parent for sub-task deletion")
        sub_task_to_delete = tasks.add_sub_task(parent_task.id, "Delete Me")
        sub_task_to_keep = tasks.add_sub_task(parent_task.id, "Keep Me")

        self.assertEqual(len(parent_task.sub_tasks), 2)

        delete_result = tasks.delete_sub_task(parent_task.id, sub_task_to_delete['id'])
        self.assertTrue(delete_result)
        self.assertEqual(len(parent_task.sub_tasks), 1)
        self.assertEqual(parent_task.sub_tasks[0], sub_task_to_keep)

        # Test deleting non-existent sub-task
        delete_non_existent_result = tasks.delete_sub_task(parent_task.id, 999)
        self.assertFalse(delete_non_existent_result)
        self.assertEqual(len(parent_task.sub_tasks), 1) # Count should remain unchanged

        # Test deleting from non-existent parent task
        delete_from_non_existent_parent = tasks.delete_sub_task(999, sub_task_to_keep['id'])
        self.assertFalse(delete_from_non_existent_parent)


if __name__ == '__main__':
    unittest.main()
