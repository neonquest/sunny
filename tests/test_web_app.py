import unittest
from web_app import app # Import the Flask app instance
from chores import tasks, planning

class WebAppTests(unittest.TestCase):

    def setUp(self):
        """Set up a test client for the Flask application."""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False # Disable CSRF for testing forms if applicable
        app.secret_key = 'test_secret_key' # Consistent secret key for tests
        self.client = app.test_client()

        # Clear any existing tasks and plans before each test
        tasks.clear_all_tasks()
        planning.clear_all_plans()

    def tearDown(self):
        """Clean up after each test."""
        tasks.clear_all_tasks()
        planning.clear_all_plans()

    def test_home_page_loads(self):
        """Test if the home page loads correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Welcome to the Chores Manager", response.data)

    def test_view_chores_page_loads(self):
        """Test if the view chores page loads correctly."""
        response = self.client.get('/chores')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"All Chores", response.data)

    def test_add_chore_page_loads_get(self):
        """Test if the add chore page loads correctly with a GET request."""
        response = self.client.get('/add_chore')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Add a New Chore", response.data)

    def test_add_new_chore_post(self):
        """Test adding a new chore via POST request."""
        initial_task_count = len(tasks.get_all_tasks())
        self.assertEqual(initial_task_count, 0)

        response = self.client.post('/add_chore', data={'description': 'Test Web Chore'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # After redirect to /chores
        self.assertIn(b"Test Web Chore", response.data) # Check if the new chore is displayed
        self.assertIn(b"Chore &#39;Test Web Chore&#39; added successfully!", response.data) # Check flash message (HTML escaped)

        self.assertEqual(len(tasks.get_all_tasks()), initial_task_count + 1)
        self.assertEqual(tasks.get_all_tasks()[0].description, "Test Web Chore")

    def test_add_empty_chore_post(self):
        """Test adding a chore with an empty description via POST request."""
        response = self.client.post('/add_chore', data={'description': ''}, follow_redirects=True)
        self.assertEqual(response.status_code, 400) # Should be a bad request or render template with error
        self.assertIn(b"Chore description cannot be empty", response.data)
        self.assertEqual(len(tasks.get_all_tasks()), 0) # No task should be added

    def test_update_chore_status(self):
        """Test updating a chore's status."""
        task = tasks.add_task("Chore to Update")
        self.assertEqual(task.status, "pending")

        response = self.client.post(f'/update_chore_status/{task.id}', data={'status': 'in progress'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Status for chore &#39;Chore to Update&#39; updated to &#39;in progress&#39;.", response.data) # HTML escaped

        updated_task = tasks.get_task_by_id(task.id)
        self.assertEqual(updated_task.status, "in progress")

    def test_update_chore_status_invalid_status(self):
        """Test updating a chore's status with an invalid status value."""
        task = tasks.add_task("Chore Invalid Update")
        response = self.client.post(f'/update_chore_status/{task.id}', data={'status': 'invalid_state'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Still redirects
        self.assertIn(b"Invalid status &#39;invalid_state&#39;.", response.data) # Check flash message (HTML escaped)

        updated_task = tasks.get_task_by_id(task.id)
        self.assertEqual(updated_task.status, "pending") # Status should not have changed

    def test_update_non_existent_chore_status(self):
        """Test updating status of a non-existent chore."""
        response = self.client.post('/update_chore_status/999', data={'status': 'completed'}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Chore with ID 999 not found", response.data)

    def test_delete_chore(self):
        """Test deleting a chore."""
        task = tasks.add_task("Chore to Delete")
        task_id_to_delete = task.id
        self.assertIsNotNone(tasks.get_task_by_id(task_id_to_delete))

        response = self.client.post(f'/delete_chore/{task_id_to_delete}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Chore &#39;Chore to Delete&#39; and any associated plans deleted successfully.", response.data) # HTML escaped
        self.assertIsNone(tasks.get_task_by_id(task_id_to_delete))

    def test_delete_non_existent_chore(self):
        """Test deleting a non-existent chore."""
        response = self.client.post('/delete_chore/999', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Chore with ID 999 not found", response.data)

if __name__ == '__main__':
    unittest.main()
