# This file will contain tests for the task management functionality.

import unittest
from chores import tasks # Import the tasks module

class TestTaskManagement(unittest.TestCase):

    def setUp(self):
        """Clear all tasks before each test."""
        tasks.clear_all_tasks()

    def tearDown(self):
        """Clear all tasks after each test to ensure isolation."""
        tasks.clear_all_tasks()

    def test_create_task_object(self):
        """Test basic Task object creation."""
        task_obj = tasks.Task("Test Description", "test_status")
        self.assertEqual(task_obj.description, "Test Description")
        self.assertEqual(task_obj.status, "test_status")
        # ID will be None until added by add_task
        self.assertIsNone(task_obj.id)


    def test_add_task(self):
        """Test adding a single task."""
        task = tasks.add_task("Fix the shower door")
        self.assertIsNotNone(task.id, "Task ID should be set after adding.")
        self.assertEqual(task.description, "Fix the shower door")
        self.assertEqual(task.status, "pending")
        self.assertEqual(len(tasks.get_all_tasks()), 1)
        self.assertEqual(tasks.get_all_tasks()[0], task)

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
        tasks.update_task_status(task.id, "in progress")
        # The ID is assigned when the task is added.
        expected_str = f"[ID: {task.id}] Task: Clean the garage (Status: in progress)"
        self.assertEqual(str(task), expected_str)

    def test_clear_all_tasks(self):
        """Test clearing all tasks."""
        tasks.add_task("Task 1")
        tasks.add_task("Task 2")
        self.assertEqual(len(tasks.get_all_tasks()), 2)
        tasks.clear_all_tasks()
        self.assertEqual(len(tasks.get_all_tasks()), 0)
        # Check if _next_task_id is reset
        task_after_clear = tasks.add_task("New Task")
        self.assertEqual(task_after_clear.id, 1, "Next task ID should be reset to 1 after clear.")


if __name__ == '__main__':
    unittest.main()
