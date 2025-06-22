import unittest
from unittest import mock # Import mock
from web_app import app # Import the Flask app instance
from chores import tasks, planning

from chores import database # Import database module

class WebAppTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Initialize the database once for all tests in this class."""
        # Ensure Flask app is configured for testing before DB init if DB relies on app context
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.secret_key = 'test_secret_key'
        # It's important that init_db() is called after app context might be needed,
        # or if it creates the db file path based on app.instance_path, etc.
        # For our simple setup, direct call is okay.
        database.init_db()

    def setUp(self):
        """Set up a test client and clear DB before each test."""
        # App config is set in setUpClass or here if preferred per test
        self.client = app.test_client()
        database.clear_db_for_testing() # Clear data from tables

    def tearDown(self):
        """Clear DB after each test."""
        database.clear_db_for_testing() # Clear data from tables

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
        self.assertIn(b"N/A", response.data) # Due date should be N/A
        self.assertIn(b"0", response.data) # Sub-tasks count

        self.assertEqual(len(tasks.get_all_tasks()), initial_task_count + 1)
        created_task = tasks.get_all_tasks()[0]
        self.assertEqual(created_task.description, "Test Web Chore")
        self.assertEqual(created_task.notes, "")
        self.assertIsNone(created_task.due_date)

    def test_add_new_chore_with_details_post(self):
        """Test adding a new chore with notes and due date."""
        from datetime import date
        today_str = date.today().isoformat()
        response = self.client.post('/add_chore', data={
            'description': 'Detailed Chore',
            'notes': 'Some important notes.',
            'due_date': today_str,
            'materials_needed': 'Hammer\nNails\nWood Glue' # New form field
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Redirects to /chores
        self.assertIn(b"Detailed Chore", response.data)
        self.assertIn(b"Chore &#39;Detailed Chore&#39; added successfully!", response.data)
        self.assertIn(bytes(today_str, 'utf-8'), response.data)

        created_task = tasks.get_task_by_id(1)
        self.assertIsNotNone(created_task)
        self.assertEqual(created_task.description, "Detailed Chore")
        self.assertEqual(created_task.notes, "Some important notes.")
        self.assertEqual(created_task.due_date, date.fromisoformat(today_str))
        self.assertEqual(created_task.materials_needed, ["Hammer", "Nails", "Wood Glue"])

        # Also check if materials are displayed on the chore detail page if we were to navigate there
        # For now, this test focuses on the add functionality and data integrity.
        # Display on chores list page is not detailed enough for materials.


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
        self.assertIn(b"Chore &#39;Chore to Delete&#39; and its details deleted successfully.", response.data) # HTML escaped
        self.assertIsNone(tasks.get_task_by_id(task_id_to_delete))

    def test_delete_non_existent_chore(self):
        """Test deleting a non-existent chore."""
        response = self.client.post('/delete_chore/999', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Chore with ID 999 not found", response.data)

    def test_chore_detail_page_loads(self):
        """Test if the chore detail page loads and shows details."""
        from datetime import date
        today = date.today()
        # task = tasks.add_task("Detail Test Chore", notes="Detail notes.", due_date=today) # Removed duplicate
        # tasks.add_sub_task(task.id, "Sub-task 1 for detail page") # And its sub_task

        task = tasks.add_task("Detail Test Chore", notes="Detail notes.", due_date=today, materials_needed_text="Paint\nBrush")
        # Add sub_task to this specific task object if needed for other assertions, or ensure task.id is correct
        # The original test only added one task, then tried to add another with same description but more details.
        # Let's assume we only want one task for this test.
        sub_task_info = tasks.add_sub_task(task.id, "Sub-task 1 for detail page") # ensure sub-task is added to the correct task

        response = self.client.get(f'/chore/{task.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Detail Test Chore", response.data)
        self.assertIn(b"Detail notes.", response.data)
        self.assertIn(bytes(today.isoformat(), 'utf-8'), response.data)
        self.assertIn(b"Sub-task 1 for detail page", response.data)
        self.assertIn(b"Edit Main Chore Details", response.data)
        self.assertIn(b"Materials Needed:", response.data)
        self.assertIn(b"Paint", response.data)
        self.assertIn(b"Brush", response.data)
        self.assertIn(b"amazon.com/s?k=Paint", response.data) # Check for Amazon link
        self.assertIn(b"homedepot.com/s/Brush", response.data) # Check for Home Depot link


    def test_chore_detail_page_not_found(self):
        """Test chore detail page for a non-existent chore."""
        response = self.client.get('/chore/999', follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Follows redirect to chores list
        self.assertIn(b"Chore with ID 999 not found", response.data) # Flash message on chores list

    def test_edit_chore_details_page_loads_get(self):
        """Test if the edit chore page loads correctly with a GET request."""
        task = tasks.add_task("Chore To Edit Get")
        response = self.client.get(f'/chore/{task.id}/edit')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Edit Chore: Chore To Edit Get", response.data)
        self.assertIn(b"Chore To Edit Get", response.data) # Original description in form

    def test_edit_chore_details_post(self):
        """Test editing chore details via POST request."""
        from datetime import date
        task = tasks.add_task("Original Desc", notes="Original Notes", due_date=date(2023, 1, 1))

        new_desc = "Updated Description"
        new_notes = "Updated Notes"
        new_due_date_str = "2024-12-25"
        new_due_date_obj = date(2024, 12, 25)

        response = self.client.post(f'/chore/{task.id}/edit', data={
            'description': new_desc,
            'notes': new_notes,
            'due_date': new_due_date_str,
            'materials_needed': 'Saw\nScrewdriver\nMeasuring Tape' # New form field
        }, follow_redirects=True)

        self.assertEqual(response.status_code, 200) # Redirects to chore_detail
        self.assertIn(bytes(f"Chore &#39;{new_desc}&#39; updated successfully!", 'utf-8'), response.data)

        updated_task = tasks.get_task_by_id(task.id)
        self.assertEqual(updated_task.description, new_desc)
        self.assertEqual(updated_task.notes, new_notes)
        self.assertEqual(updated_task.due_date, new_due_date_obj)
        self.assertEqual(updated_task.materials_needed, ["Saw", "Screwdriver", "Measuring Tape"])

        # Check if details are updated on the detail page
        self.assertIn(bytes(new_desc, 'utf-8'), response.data) # Description on detail page
        self.assertIn(bytes(new_notes, 'utf-8'), response.data) # Notes on detail page
        self.assertIn(bytes(new_due_date_str, 'utf-8'), response.data) # Due date on detail page
        self.assertIn(b"Saw", response.data) # Materials on detail page
        self.assertIn(b"Screwdriver", response.data)
        self.assertIn(b"Measuring Tape", response.data)
        self.assertIn(b"amazon.com/s?k=Saw", response.data) # Check for one of the links

    def test_edit_chore_details_empty_description_post(self):
        """Test editing chore with empty description."""
        task = tasks.add_task("Valid Description")
        response = self.client.post(f'/chore/{task.id}/edit', data={
            'description': '', 'notes': 'Some notes', 'due_date': ''
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Renders edit_chore.html again, not 400 directly due to follow_redirects on error path
        self.assertIn(b"Description cannot be empty.", response.data)
        original_task = tasks.get_task_by_id(task.id)
        self.assertEqual(original_task.description, "Valid Description") # Should not change

    def test_edit_chore_details_invalid_date_post(self):
        """Test editing chore with invalid date format."""
        task = tasks.add_task("Date Test Chore")
        response = self.client.post(f'/chore/{task.id}/edit', data={
            'description': 'Date Test Chore', 'notes': '', 'due_date': 'not-a-date'
        }, follow_redirects=True) # Renders edit_chore.html again
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Invalid due date format.", response.data)
        original_task = tasks.get_task_by_id(task.id)
        self.assertIsNone(original_task.due_date) # Should not change or be set

# --- Tests for Sub-task Management ---

    def test_add_sub_task(self):
        """Test adding a sub-task to a chore."""
        task = tasks.add_task("Parent Chore for Sub-task")
        response = self.client.post(f'/chore/{task.id}/add_sub_task', data={
            'sub_task_description': 'My First Sub-task'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200) # Redirects to chore_detail
        self.assertIn(b"Sub-task added successfully.", response.data)
        self.assertIn(b"My First Sub-task", response.data) # Sub-task shown on detail page

        updated_parent_task = tasks.get_task_by_id(task.id)
        self.assertEqual(len(updated_parent_task.sub_tasks), 1)
        self.assertEqual(updated_parent_task.sub_tasks[0]['description'], "My First Sub-task")
        self.assertFalse(updated_parent_task.sub_tasks[0]['completed'])

    def test_add_empty_sub_task(self):
        """Test adding an empty sub-task."""
        task = tasks.add_task("Parent for Empty Sub")
        response = self.client.post(f'/chore/{task.id}/add_sub_task', data={
            'sub_task_description': ''
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sub-task description cannot be empty.", response.data)
        updated_parent_task = tasks.get_task_by_id(task.id)
        self.assertEqual(len(updated_parent_task.sub_tasks), 0)

    def test_toggle_sub_task_status(self):
        """Test toggling a sub-task's completion status."""
        task = tasks.add_task("Parent for Toggle Sub-task")
        sub_task = tasks.add_sub_task(task.id, "Sub-task to toggle")
        self.assertFalse(sub_task['completed'])

        # Toggle to complete
        response = self.client.post(f'/chore/{task.id}/sub_task/{sub_task["id"]}/toggle', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(f"Sub-task &#39;{sub_task['description']}&#39; marked as completed.", 'utf-8'), response.data)
        updated_sub_task_obj = tasks.get_sub_task_by_id_from_db(sub_task['id']) # Corrected call
        self.assertTrue(updated_sub_task_obj['completed'])
        self.assertIn(b"Mark Pending", response.data) # Button text should change

        # Toggle back to pending
        response = self.client.post(f'/chore/{task.id}/sub_task/{sub_task["id"]}/toggle', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(f"Sub-task &#39;{sub_task['description']}&#39; marked as pending.", 'utf-8'), response.data)
        updated_sub_task_obj = tasks.get_sub_task_by_id_from_db(sub_task['id']) # Corrected call
        self.assertFalse(updated_sub_task_obj['completed'])
        self.assertIn(b"Mark Complete", response.data) # Button text should change back

    def test_delete_sub_task(self):
        """Test deleting a sub-task."""
        task = tasks.add_task("Parent for Delete Sub-task")
        sub_task_to_delete = tasks.add_sub_task(task.id, "Sub-task to be deleted")
        sub_task_to_keep = tasks.add_sub_task(task.id, "Sub-task to keep")

        self.assertEqual(len(tasks.get_task_by_id(task.id).sub_tasks), 2)

        response = self.client.post(f'/chore/{task.id}/sub_task/{sub_task_to_delete["id"]}/delete', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(bytes(f"Sub-task &#39;{sub_task_to_delete['description']}&#39; deleted successfully.", 'utf-8'), response.data)

        updated_parent_task = tasks.get_task_by_id(task.id)
        self.assertEqual(len(updated_parent_task.sub_tasks), 1)
        self.assertEqual(updated_parent_task.sub_tasks[0]['id'], sub_task_to_keep['id'])

        # Check that the deleted sub-task's specific list item structure is not present
        # This is more targeted than checking the entire response.data for the description string
        # which might appear in a flash message.
        deleted_sub_task_html_part = f"<span>\n                                    {sub_task_to_delete['description']}\n                                    <em>(ID: {sub_task_to_delete['id']})</em>"
        self.assertNotIn(bytes(deleted_sub_task_html_part, 'utf-8'), response.data)

        # Check that the kept sub-task's list item structure IS present
        kept_sub_task_html_part = f"<span>\n                                    {sub_task_to_keep['description']}\n                                    <em>(ID: {sub_task_to_keep['id']})</em>"
        self.assertIn(bytes(kept_sub_task_html_part, 'utf-8'), response.data)

    def test_move_sub_task_web(self):
        """Test moving sub-tasks up and down via web interface."""
        task = tasks.add_task("Parent for Web Sub-task Reorder")
        st1 = tasks.add_sub_task(task.id, "SubTask Web One")
        st2 = tasks.add_sub_task(task.id, "SubTask Web Two")
        st3 = tasks.add_sub_task(task.id, "SubTask Web Three")

        # Initial order on page: st1, st2, st3
        response = self.client.get(f'/chore/{task.id}')
        self.assertEqual(response.status_code, 200)

        # Ensure order before move using regex to find list items and their content.
        # This is more robust than checking fixed string positions if minor HTML changes.
        import re
        page_content = response.data.decode('utf-8')

        # Find all sub-task descriptions in order of appearance
        sub_task_descriptions_in_html = re.findall(r'<li class="[^"]*".*?>\s*<span>\s*([^<]+?)\s*<em>\(ID: \d+\)</em>', page_content, re.DOTALL)

        self.assertEqual(sub_task_descriptions_in_html, ["SubTask Web One", "SubTask Web Two", "SubTask Web Three"])

        # Move st2 up (st1, st2, st3 -> st2, st1, st3)
        response = self.client.post(f'/chore/{task.id}/sub_task/{st2["id"]}/move/up', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sub-task &#39;SubTask Web Two&#39; moved up.", response.data)

        page_content_after_move_up = response.data.decode('utf-8')
        sub_task_descriptions_after_move_up = re.findall(r'<li class="[^"]*".*?>\s*<span>\s*([^<]+?)\s*<em>\(ID: \d+\)</em>', page_content_after_move_up, re.DOTALL)
        self.assertEqual(sub_task_descriptions_after_move_up, ["SubTask Web Two", "SubTask Web One", "SubTask Web Three"])

        # Move st3 (now at original st3 position, which is index 2) down.
        # After st2 moved up, list is st2, st1, st3. We want to move st3 (last) down. This should fail.
        # Let's move st1 (now at index 1) down. (st2, st1, st3 -> st2, st3, st1)
        response = self.client.post(f'/chore/{task.id}/sub_task/{st1["id"]}/move/down', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Sub-task &#39;SubTask Web One&#39; moved down.", response.data)

        page_content_after_move_down = response.data.decode('utf-8')
        sub_task_descriptions_after_move_down = re.findall(r'<li class="[^"]*".*?>\s*<span>\s*([^<]+?)\s*<em>\(ID: \d+\)</em>', page_content_after_move_down, re.DOTALL)
        self.assertEqual(sub_task_descriptions_after_move_down, ["SubTask Web Two", "SubTask Web Three", "SubTask Web One"])

        # Try to move st2 (now first) up - should be disabled/fail gracefully
        response = self.client.post(f'/chore/{task.id}/sub_task/{st2["id"]}/move/up', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Could not move sub-task &#39;SubTask Web Two&#39;. It might be at the limit or an error occurred.", response.data)

        # Try to move st1 (now last) down - should be disabled/fail gracefully
        response = self.client.post(f'/chore/{task.id}/sub_task/{st1["id"]}/move/down', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Could not move sub-task &#39;SubTask Web One&#39;. It might be at the limit or an error occurred.", response.data)

# --- Tests for AI Sub-task Suggestions ---
    def test_suggest_ai_subtasks(self):
        """Test AI sub-task suggestion feature (sub-tasks and materials)."""
        task = tasks.add_task("Clean the entire house")

        with mock.patch('chores.ai_assistant.get_subtask_and_material_suggestions') as mock_get_ai_response:
            mock_get_ai_response.return_value = {
                'sub_tasks': [
                    "Clean kitchen",
                    "Clean bathrooms",
                    "Vacuum all floors"
                ],
                'materials': ["Cleaning spray", "Paper towels", "Vacuum bags"]
            }

            response = self.client.post(f'/chore/{task.id}/suggest_subtasks_ai', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            mock_get_ai_response.assert_called_once_with("Clean the entire house", existing_subtask_descriptions=[])
            self.assertIn(b"3 new sub-task(s) added.", response.data) # Message part for sub-tasks
            self.assertIn(b"3 new material(s) added.", response.data) # Message part for materials

            updated_task = tasks.get_task_by_id(task.id)
            self.assertEqual(len(updated_task.sub_tasks), 3)
            self.assertEqual(updated_task.sub_tasks[0]['description'], "Clean kitchen")
            self.assertEqual(updated_task.sub_tasks[1]['description'], "Clean bathrooms")
            self.assertEqual(updated_task.sub_tasks[2]['description'], "Vacuum all floors")

            # Check if they appear on the page
            self.assertIn(b"Clean kitchen", response.data)
            self.assertIn(b"Clean bathrooms", response.data)
            self.assertIn(b"Vacuum all floors", response.data)

    def test_suggest_ai_subtasks_no_suggestions(self):
        """Test AI sub-task suggestion when AI returns no suggestions."""
        task = tasks.add_task("Organize esoteric book collection")

        with mock.patch('chores.ai_assistant.get_subtask_and_material_suggestions') as mock_get_ai_response:
            mock_get_ai_response.return_value = {'sub_tasks': [], 'materials': []} # AI returns nothing

            response = self.client.post(f'/chore/{task.id}/suggest_subtasks_ai', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            mock_get_ai_response.assert_called_once_with("Organize esoteric book collection", existing_subtask_descriptions=[])
            self.assertIn(b"AI processing complete. No new sub-tasks or materials were added.", response.data)

            updated_task = tasks.get_task_by_id(task.id)
            self.assertEqual(len(updated_task.sub_tasks), 0) # No sub-tasks should be added

    def test_suggest_ai_subtasks_api_error(self):
        """Test AI sub-task suggestion when the AI call raises an exception."""
        task = tasks.add_task("Plan interstellar voyage")

        with mock.patch('chores.ai_assistant.get_subtask_and_material_suggestions') as mock_get_ai_response:
            mock_get_ai_response.side_effect = Exception("Simulated API Error")

            response = self.client.post(f'/chore/{task.id}/suggest_subtasks_ai', follow_redirects=True)
            mock_get_ai_response.assert_called_once_with("Plan interstellar voyage", existing_subtask_descriptions=[])
            self.assertEqual(response.status_code, 200)
            self.assertIn(b"An error occurred while trying to get AI suggestions.", response.data)

            updated_task = tasks.get_task_by_id(task.id)
            self.assertEqual(len(updated_task.sub_tasks), 0)

    def test_suggest_ai_subtasks_api_key_missing(self):
        """Test AI sub-task suggestion when GOOGLE_API_KEY is not set."""
        task = tasks.add_task("Chore with missing API key")

        # We want to test the behavior of get_subtask_suggestions when os.environ.get returns None
        # So, we patch os.environ.get directly.
        with mock.patch('os.environ.get') as mock_env_get:
            mock_env_get.return_value = None # Simulate GOOGLE_API_KEY not being set

            # We also need to ensure that 'chores.ai_assistant' is reloaded or its
            # get_subtask_suggestions reflects this change if api_key is checked at module load.
            # However, my current ai_assistant.py checks os.environ.get() inside the function,
            # so mocking os.environ.get should be sufficient.

            response = self.client.post(f'/chore/{task.id}/suggest_subtasks_ai', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            # The flash message comes from web_app.py after checking the specific return from ai_assistant.py
            self.assertIn(b"AI features disabled: GOOGLE_API_KEY not set. Please set the environment variable.", response.data)

            updated_task = tasks.get_task_by_id(task.id)
            self.assertEqual(len(updated_task.sub_tasks), 0) # No sub-tasks should be added

    def test_suggest_ai_subtasks_with_duplicates(self):
        """Test AI suggestion with some duplicates and case variations."""
        task = tasks.add_task("Maintain the garden")
        # Add an existing sub-task
        st_existing1 = tasks.add_sub_task(task.id, "Water the plants")
        st_existing2 = tasks.add_sub_task(task.id, "Weed the flower beds")
        existing_st_descs = [st_existing1['description'], st_existing2['description']]

        with mock.patch('chores.ai_assistant.get_subtask_and_material_suggestions') as mock_get_ai_response:
            mock_get_ai_response.return_value = {
                'sub_tasks': [
                    "Mow the lawn",           # New
                    "Water the plants",       # Duplicate of existing sub-task
                    "  mow the lawn  "        # Duplicate from this AI batch
                ],
                'materials': ["Gloves", "Shears", "Gloves"] # "Gloves" is duplicated by AI here
            }

            response = self.client.post(f'/chore/{task.id}/suggest_subtasks_ai', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            mock_get_ai_response.assert_called_once_with("Maintain the garden", existing_subtask_descriptions=existing_st_descs)

            # Sub-tasks: "Mow the lawn" (new). "Water the plants" (skipped, existing). "  mow the lawn  " (skipped, dup in batch)
            # Materials: "Gloves" (new), "Shears" (new). Second "Gloves" (skipped, dup in batch)
            self.assertIn(b"1 new sub-task(s) added.", response.data)
            self.assertIn(b"2 sub-task suggestion(s) were duplicates/empty and skipped.", response.data)
            self.assertIn(b"2 new material(s) added.", response.data)
            self.assertIn(b"1 material suggestion(s) were duplicates/empty and skipped.", response.data)


            updated_task = tasks.get_task_by_id(task.id)
            self.assertEqual(len(updated_task.sub_tasks), 3) # 2 existing + 1 new ("Mow the lawn")

            descriptions = {st['description'] for st in updated_task.sub_tasks}
            self.assertIn("Water the plants", descriptions) # Existing
            self.assertIn("Weed the flower beds", descriptions) # Original casing
            self.assertIn("Mow the lawn", descriptions)     # Added with original AI casing
            # self.assertIn("Trim hedges", descriptions)      # "Trim Hedges" was not in this test's mock AI response

            # Ensure "  weed the flower beds  " (from AI) was not added as a new item if "Weed the flower beds" existed.
            # Ensure "  mow the lawn  " (from AI) was not added if "Mow the lawn" was already added from this batch.
            # The current logic adds the first occurrence (e.g. "Mow the lawn") and skips subsequent normalized duplicates ("  mow the lawn  ").

    def test_suggest_ai_subtasks_all_duplicates(self):
        """Test AI suggestion when all suggestions are duplicates."""
        task = tasks.add_task("Clean Room")
        st1 = tasks.add_sub_task(task.id, "Make bed")
        st2 = tasks.add_sub_task(task.id, "Dust surfaces")
        existing_st_descs = [st1['description'], st2['description']]

        with mock.patch('chores.ai_assistant.get_subtask_and_material_suggestions') as mock_get_ai_response: # Corrected mock target
            mock_get_ai_response.return_value = {
                'sub_tasks': [
                    "make bed", # Duplicate of existing
                    "  DUST SURFACES  "  # Duplicate of existing (case/space)
                ],
                'materials': ["Polish"] # One new material
            }
            response = self.client.post(f'/chore/{task.id}/suggest_subtasks_ai', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            mock_get_ai_response.assert_called_once_with("Clean Room", existing_subtask_descriptions=existing_st_descs)

            self.assertIn(b"2 sub-task suggestion(s) were duplicates/empty and skipped.", response.data)
            self.assertNotIn(b"new sub-task(s) added.", response.data) # No new sub-tasks
            self.assertIn(b"1 new material(s) added.", response.data) # New material added

            updated_task = tasks.get_task_by_id(task.id)
            self.assertEqual(len(updated_task.sub_tasks), 2) # Should remain 2


if __name__ == '__main__':
    unittest.main()
