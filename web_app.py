from flask import Flask, render_template, url_for, request, redirect, flash
from chores import tasks, planning, ai_assistant, database # Import modules
import urllib.parse # For URL encoding

app = Flask(__name__)
app.secret_key = 'your secret key' # Needed for flashing messages

# Initialize the database (create tables if they don't exist)
# This should ideally be run once. For simple apps, doing it here is okay.
# For more complex apps, consider Flask CLI commands or app factory pattern.
with app.app_context(): # Ensures DB operations have app context if needed by extensions (not strictly for sqlite3)
    database.init_db()

@app.context_processor
def utility_processor():
    def generate_amazon_search_url(material_name):
        encoded_material = urllib.parse.quote_plus(material_name)
        return f"https://www.amazon.com/s?k={encoded_material}"

    def generate_home_depot_search_url(material_name):
        encoded_material = urllib.parse.quote_plus(material_name)
        return f"https://www.homedepot.com/s/{encoded_material}"

    return dict(
        amazon_search_url=generate_amazon_search_url,
        home_depot_search_url=generate_home_depot_search_url
    )

# Sample data for initial testing if tasks module is not fully populated
# tasks.clear_all_tasks() # Clear previous tasks if any from prior runs
# tasks.add_task("Clean the kitchen")
# tasks.add_task("Take out the trash")
# tasks.update_task_status(tasks.get_all_tasks()[0].id, "in progress")


@app.route('/')
def home():
    """Serves the homepage."""
    return render_template('index.html', title='Welcome')

@app.route('/chores')
def view_chores_route():
    """Serves the page that displays all chores."""
    all_chores = tasks.get_all_tasks()
    return render_template('chores.html', chores=all_chores, title="View All Chores")

@app.route('/add_chore', methods=['GET', 'POST'])
def add_chore_route():
    """Handles adding a new chore. Shows form on GET, processes form on POST."""
    if request.method == 'POST':
        description = request.form.get('description')
        notes = request.form.get('notes', '')
        due_date_str = request.form.get('due_date')
        materials_needed_text = request.form.get('materials_needed', '') # Get materials

        if not description:
            flash('Chore description cannot be empty.', 'error')
            return render_template('add_chore.html', title="Add New Chore",
                                   description=description, notes=notes, due_date=due_date_str,
                                   form_materials_text=materials_needed_text), 400 # Use consistent var name

        due_date_obj = None
        if due_date_str:
            try:
                from datetime import datetime
                due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash("Invalid due date format. Please use YYYY-MM-DD.", 'error')
                return render_template('add_chore.html', title="Add New Chore",
                                       description=description, notes=notes, due_date=due_date_str,
                                       form_materials_text=materials_needed_text), 400 # Use consistent var name

        new_task = tasks.add_task(
            description=description,
            notes=notes,
            due_date=due_date_obj,
            materials_needed_text=materials_needed_text # Pass to tasks.add_task
        )
        flash(f"Chore '{new_task.description}' added successfully!", 'success')
        return redirect(url_for('view_chores_route'))

    # For GET request, just show the form
    return render_template('add_chore.html', title="Add New Chore",
                           description="", notes="", due_date="", materials_needed="") # Pass empty for GET

@app.route('/update_chore_status/<int:task_id>', methods=['POST'])
def update_chore_status_route(task_id):
    """Handles updating the status of a chore."""
    new_status = request.form.get('status')
    task = tasks.get_task_by_id(task_id)

    if not task:
        flash(f"Chore with ID {task_id} not found.", 'error')
    elif new_status not in ['pending', 'in progress', 'completed']:
        flash(f"Invalid status '{new_status}'.", 'error')
    else:
        updated_task = tasks.update_task_status(task_id, new_status)
        if updated_task:
            flash(f"Status for chore '{updated_task.description}' updated to '{new_status}'.", 'success')
        else:
            # This case should ideally not be hit if task was found initially
            flash(f"Failed to update status for chore ID {task_id}.", 'error')

    return redirect(url_for('view_chores_route'))

@app.route('/delete_chore/<int:task_id>', methods=['POST'])
def delete_chore_route(task_id):
    """Handles deleting a chore."""
    task = tasks.get_task_by_id(task_id)
    if task:
        task_description = task.description # Save before deletion
        # Attempt to delete the task
        if tasks.delete_task(task_id):
            # planning.remove_plan(task_id) # This is no longer needed as details are part of the task
            flash(f"Chore '{task_description}' and its details deleted successfully.", 'success')
        else:
            # This case should ideally not be hit if task was found by get_task_by_id
            flash(f"Failed to delete chore '{task.description}'.", 'error')
    else:
        flash(f"Chore with ID {task_id} not found.", 'error')

    return redirect(url_for('view_chores_route'))

@app.route('/chore/<int:task_id>')
def chore_detail_route(task_id):
    """Serves the page displaying details for a specific chore."""
    chore = tasks.get_task_by_id(task_id)
    if not chore:
        flash(f"Chore with ID {task_id} not found.", 'error')
        return redirect(url_for('view_chores_route'))
    return render_template('chore_detail.html', chore=chore, title=chore.description)

@app.route('/chore/<int:task_id>/edit', methods=['GET', 'POST'])
def edit_chore_details_route(task_id):
    """Handles editing the main details of a chore."""
    chore = tasks.get_task_by_id(task_id)
    if not chore:
        flash(f"Chore with ID {task_id} not found.", 'error')
        return redirect(url_for('view_chores_route'))

    if request.method == 'POST':
        description = request.form.get('description')
        notes = request.form.get('notes', '')
        due_date_str = request.form.get('due_date')
        materials_text = request.form.get('materials_needed', '') # Raw text from textarea

        if not description:
            flash("Description cannot be empty.", 'error')
            return render_template('edit_chore.html', chore=chore, title=f"Edit {chore.description}",
                                   description=description, notes=notes, due_date=due_date_str,
                                   form_materials_text=materials_text) # Use consistent var name

        due_date_obj = None
        if due_date_str:
            try:
                from datetime import datetime
                due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash("Invalid due date format. Please use YYYY-MM-DD.", 'error')
                return render_template('edit_chore.html', chore=chore, title=f"Edit {chore.description}",
                                       description=description, notes=notes, due_date=due_date_str,
                                       form_materials_text=materials_text) # Use consistent var name

        updated_chore = tasks.update_task_details(
            task_id,
            description=description,
            notes=notes,
            due_date=due_date_obj,
            materials_needed_text=materials_text # Pass as raw text
        )
        if updated_chore:
            flash(f"Chore '{updated_chore.description}' updated successfully!", 'success')
            return redirect(url_for('chore_detail_route', task_id=task_id))
        else:
            flash("Failed to update chore.", 'error') # Should not happen if chore was found initially

    return render_template('edit_chore.html', chore=chore, title=f"Edit {chore.description}")


@app.route('/chore/<int:task_id>/add_sub_task', methods=['POST'])
def add_sub_task_route(task_id):
    chore = tasks.get_task_by_id(task_id)
    if not chore:
        flash(f"Chore with ID {task_id} not found.", 'error')
        return redirect(url_for('view_chores_route'))

    sub_task_description = request.form.get('sub_task_description')
    if not sub_task_description:
        flash("Sub-task description cannot be empty.", 'error')
    else:
        if tasks.add_sub_task(task_id, sub_task_description):
            flash("Sub-task added successfully.", 'success')
        else:
            flash("Failed to add sub-task.", 'error') # Should not happen if chore exists
    return redirect(url_for('chore_detail_route', task_id=task_id))

@app.route('/chore/<int:task_id>/sub_task/<int:sub_task_id>/toggle', methods=['POST'])
def toggle_sub_task_route(task_id, sub_task_id):
    chore = tasks.get_task_by_id(task_id)
    if not chore:
        flash(f"Chore with ID {task_id} not found.", 'error')
        return redirect(url_for('view_chores_route')) # Parent chore must exist

    # With DB, sub_task_id is globally unique, so we don't need parent chore object to find it.
    sub_task = tasks.get_sub_task_by_id_from_db(sub_task_id)
    if not sub_task or sub_task['task_id'] != task_id: # Also ensure it belongs to the correct task
        flash(f"Sub-task with ID {sub_task_id} not found for chore {task_id}.", 'error')
    else:
        # tasks.update_sub_task now takes only sub_task_id and new values
        updated_sub_task = tasks.update_sub_task(sub_task_id, completed=not sub_task['completed'])
        if updated_sub_task:
            status_text = "completed" if updated_sub_task['completed'] else "pending"
            flash(f"Sub-task '{updated_sub_task['description']}' marked as {status_text}.", 'success')
        else:
            flash("Failed to update sub-task status.", 'error')
    return redirect(url_for('chore_detail_route', task_id=task_id))

@app.route('/chore/<int:task_id>/sub_task/<int:sub_task_id>/delete', methods=['POST'])
def delete_sub_task_route(task_id, sub_task_id):
    chore = tasks.get_task_by_id(task_id)
    if not chore:
        flash(f"Chore with ID {task_id} not found.", 'error')
        return redirect(url_for('view_chores_route'))

    # Need to get sub-task description for flash message before deleting
    sub_task = tasks.get_sub_task_by_id_from_db(sub_task_id)
    if not sub_task or sub_task['task_id'] != task_id: # Ensure it belongs to the correct task
         flash(f"Sub-task with ID {sub_task_id} not found for chore {task_id}.", 'error')
    # tasks.delete_sub_task now only takes sub_task_id
    elif tasks.delete_sub_task(sub_task_id):
        flash(f"Sub-task '{sub_task['description']}' deleted successfully.", 'success')
    else:
        # This case should be rare if sub_task was found, implies DB error during delete
        flash(f"Failed to delete sub-task '{sub_task['description']}'.", 'error')
    return redirect(url_for('chore_detail_route', task_id=task_id))

@app.route('/chore/<int:task_id>/sub_task/<int:sub_task_id>/move/<direction>', methods=['POST'])
def move_sub_task_route(task_id, sub_task_id, direction):
    """Handles moving a sub-task up or down."""
    if direction not in ['up', 'down']:
        flash("Invalid move direction specified.", 'error')
        return redirect(url_for('chore_detail_route', task_id=task_id))

    chore = tasks.get_task_by_id(task_id)
    if not chore:
        flash(f"Chore with ID {task_id} not found.", 'error')
        return redirect(url_for('view_chores_route'))

    # Fetch sub-task by its own ID to ensure it exists before attempting to move.
    # The tasks.move_sub_task function will also verify it belongs to task_id.
    sub_task = tasks.get_sub_task_by_id_from_db(sub_task_id)
    if not sub_task or sub_task['task_id'] != task_id: # Ensure it belongs to the correct task
        flash(f"Sub-task with ID {sub_task_id} not found for chore {task_id}.", 'error')
        return redirect(url_for('chore_detail_route', task_id=task_id))

    if tasks.move_sub_task(task_id, sub_task_id, direction): # move_sub_task itself checks parent task_id implicitly
        flash(f"Sub-task '{sub_task['description']}' moved {direction}.", 'success')
    else:
        flash(f"Could not move sub-task '{sub_task['description']}'. It might be at the limit or an error occurred.", 'warning')

    return redirect(url_for('chore_detail_route', task_id=task_id))

@app.route('/chore/<int:task_id>/suggest_subtasks_ai', methods=['POST'])
def suggest_ai_subtasks_route(task_id):
    """Handles AI suggestion for sub-tasks."""
    chore = tasks.get_task_by_id(task_id)
    if not chore:
        flash(f"Chore with ID {task_id} not found.", 'error')
        return redirect(url_for('view_chores_route'))

    try:
        existing_sub_tasks_objects = tasks.get_sub_tasks_for_task(task_id) # List of dicts
        existing_sub_task_descriptions = [st['description'] for st in existing_sub_tasks_objects]

        ai_response = ai_assistant.get_subtask_and_material_suggestions( # Renamed function
            chore.description,
            existing_subtask_descriptions=existing_sub_task_descriptions
        )

        suggested_sub_task_descs = ai_response.get('sub_tasks', [])
        suggested_material_names = ai_response.get('materials', [])

        # Check for specific API key error message or other errors from the assistant (now in sub_tasks list)
        api_key_error_msg = "AI features disabled: GOOGLE_API_KEY not set."
        error_getting_suggestions_prefix = "Error getting AI suggestions:"

        flash_messages_parts = []
        overall_status_is_error = False

        if suggested_sub_task_descs and suggested_sub_task_descs[0] == api_key_error_msg:
            flash(api_key_error_msg + " Please set the environment variable.", 'error')
            overall_status_is_error = True
        elif suggested_sub_task_descs and suggested_sub_task_descs[0].startswith(error_getting_suggestions_prefix):
            flash(suggested_sub_task_descs[0], 'error') # Show the specific error from AI module
            overall_status_is_error = True

        if not overall_status_is_error:
            added_st_count = 0
            skipped_st_count = 0
            added_st_count = 0
            skipped_st_count = 0
            added_mat_count = 0
            skipped_mat_count = 0

            # Process Sub-tasks
            if suggested_sub_task_descs:
                current_sub_tasks_for_dedup = tasks.get_sub_tasks_for_task(task_id)
                existing_desc_normalized_set = {
                    st['description'].strip().lower() for st in current_sub_tasks_for_dedup
                }
                for desc_ai in suggested_sub_task_descs:
                    normalized_desc_ai = desc_ai.strip().lower()
                    if normalized_desc_ai and normalized_desc_ai not in existing_desc_normalized_set:
                        if tasks.add_sub_task(task_id, desc_ai.strip()):
                            added_st_count += 1
                            existing_desc_normalized_set.add(normalized_desc_ai)
                    elif normalized_desc_ai:
                        skipped_st_count +=1

                if added_st_count > 0:
                    flash_messages_parts.append(f"{added_st_count} new sub-task(s) added.")
                if skipped_st_count > 0:
                    flash_messages_parts.append(f"{skipped_st_count} sub-task suggestion(s) were duplicates/empty and skipped.")
                if not suggested_sub_task_descs and not added_st_count and not skipped_st_count: # AI returned empty list explicitly
                     flash_messages_parts.append("AI provided no new sub-task suggestions.")


            # Process Materials
            if suggested_material_names:
                # Fetch existing materials for the chore (task.materials_needed is a list of strings)
                # The chore object was fetched at the beginning of the route.
                # Its materials_needed field should be up-to-date if we only add,
                # but if we want to merge/replace, fetching from DB is safer.
                # For simplicity, let's assume chore.materials_needed is what we work with.
                # In tasks.py, materials_needed is stored as a newline-separated string.

                current_materials_text = chore.materials_needed # This is a list of strings from _row_to_task
                existing_materials_normalized_set = {m.strip().lower() for m in current_materials_text}

                added_mat_count = 0
                skipped_mat_count = 0
                new_materials_to_add_to_task_object = []

                for mat_ai in suggested_material_names:
                    normalized_mat_ai = mat_ai.strip().lower()
                    if normalized_mat_ai and normalized_mat_ai not in existing_materials_normalized_set:
                        new_materials_to_add_to_task_object.append(mat_ai.strip())
                        existing_materials_normalized_set.add(normalized_mat_ai) # for de-dup within AI batch
                        added_mat_count += 1
                    elif normalized_mat_ai:
                        skipped_mat_count += 1

                if new_materials_to_add_to_task_object:
                    # Append new materials to the existing ones
                    final_materials_list = current_materials_text + new_materials_to_add_to_task_object
                    # Convert list to newline-separated string for DB update
                    final_materials_text = "\n".join(final_materials_list)
                    tasks.update_task_details(task_id, materials_needed_text=final_materials_text)
                    flash_messages_parts.append(f"{added_mat_count} new material(s) added.")

                if skipped_mat_count > 0:
                     flash_messages_parts.append(f"{skipped_mat_count} material suggestion(s) were duplicates/empty and skipped.")

            if not flash_messages_parts: # If no specific messages were generated (e.g. AI returned empty for both)
                 flash("AI processing complete. No new sub-tasks or materials were added.", 'info')
            else:
                 flash(" ".join(flash_messages_parts), 'success' if (added_st_count > 0 or added_mat_count > 0) else 'info')

    except Exception as e:
        # In a real scenario, log the error `e`
        print(f"Error during AI sub-task suggestion: {e}") # For debugging
        flash("An error occurred while trying to get AI suggestions. Please try again later.", 'error')

    return redirect(url_for('chore_detail_route', task_id=task_id))


if __name__ == '__main__':
    app.run(debug=True)
