from flask import Flask, render_template, url_for, request, redirect, flash
from chores import tasks, planning, ai_assistant # Import the tasks, planning, and ai_assistant modules

app = Flask(__name__)
app.secret_key = 'your secret key' # Needed for flashing messages

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

        if not description:
            flash('Chore description cannot be empty.', 'error')
            # Re-render form with previously entered values if any
            return render_template('add_chore.html', title="Add New Chore",
                                   description=description, notes=notes, due_date=due_date_str), 400

        due_date_obj = None
        if due_date_str:
            try:
                from datetime import datetime
                due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash("Invalid due date format. Please use YYYY-MM-DD.", 'error')
                return render_template('add_chore.html', title="Add New Chore",
                                       description=description, notes=notes, due_date=due_date_str), 400

        new_task = tasks.add_task(description=description, notes=notes, due_date=due_date_obj)
        flash(f"Chore '{new_task.description}' added successfully!", 'success')
        return redirect(url_for('view_chores_route')) # Or redirect to the new chore's detail page: redirect(url_for('chore_detail_route', task_id=new_task.id))

    # For GET request, just show the form, passing empty values
    return render_template('add_chore.html', title="Add New Chore")

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
        notes = request.form.get('notes', '') # Default to empty string if not provided
        due_date_str = request.form.get('due_date')

        if not description:
            flash("Description cannot be empty.", 'error')
            return render_template('edit_chore.html', chore=chore, title=f"Edit {chore.description}")

        due_date_obj = None
        if due_date_str:
            try:
                from datetime import datetime
                due_date_obj = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            except ValueError:
                flash("Invalid due date format. Please use YYYY-MM-DD.", 'error')
                return render_template('edit_chore.html', chore=chore, title=f"Edit {chore.description}")

        updated_chore = tasks.update_task_details(task_id, description=description, notes=notes, due_date=due_date_obj)
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
        return redirect(url_for('view_chores_route'))

    sub_task = tasks.get_sub_task_by_id(chore, sub_task_id)
    if not sub_task:
        flash(f"Sub-task with ID {sub_task_id} not found for chore {task_id}.", 'error')
    else:
        updated_sub_task = tasks.update_sub_task(task_id, sub_task_id, completed=not sub_task['completed'])
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
    sub_task = tasks.get_sub_task_by_id(chore, sub_task_id)
    if not sub_task:
         flash(f"Sub-task with ID {sub_task_id} not found.", 'error')
    elif tasks.delete_sub_task(task_id, sub_task_id):
        flash(f"Sub-task '{sub_task['description']}' deleted successfully.", 'success')
    else:
        flash("Failed to delete sub-task.", 'error') # Should not happen if sub_task was found
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
        return redirect(url_for('view_chores_route')) # Or back to chore_detail if appropriate

    sub_task = tasks.get_sub_task_by_id(chore, sub_task_id)
    if not sub_task:
        flash(f"Sub-task with ID {sub_task_id} not found.", 'error')
        return redirect(url_for('chore_detail_route', task_id=task_id))

    if tasks.move_sub_task(task_id, sub_task_id, direction):
        flash(f"Sub-task '{sub_task['description']}' moved {direction}.", 'success')
    else:
        # This might happen if trying to move first item up, or last item down,
        # or if sub-task/task not found (though checked above).
        flash(f"Could not move sub-task '{sub_task['description']}'. It might be at the limit.", 'warning')

    return redirect(url_for('chore_detail_route', task_id=task_id))

@app.route('/chore/<int:task_id>/suggest_subtasks_ai', methods=['POST'])
def suggest_ai_subtasks_route(task_id):
    """Handles AI suggestion for sub-tasks."""
    chore = tasks.get_task_by_id(task_id)
    if not chore:
        flash(f"Chore with ID {task_id} not found.", 'error')
        return redirect(url_for('view_chores_route'))

    try:
        # This will call our mock AI for now
        # Corrected: Call ai_assistant module directly
        suggested_descriptions = ai_assistant.get_subtask_suggestions(chore.description)

        # Check for specific API key error message from the assistant
        api_key_error_msg = "AI features disabled: GOOGLE_API_KEY not set."
        error_getting_suggestions_prefix = "Error getting AI suggestions:"

        if suggested_descriptions and suggested_descriptions[0] == api_key_error_msg:
            flash(api_key_error_msg + " Please set the environment variable.", 'error')
        elif suggested_descriptions and suggested_descriptions[0].startswith(error_getting_suggestions_prefix):
            flash(suggested_descriptions[0], 'error') # Show the specific error from AI module
        elif not suggested_descriptions:
            flash("The AI assistant couldn't come up with any new suggestions for this chore.", 'info')
        else:
            count = 0
            for desc in suggested_descriptions:
                if tasks.add_sub_task(task_id, desc): # add_sub_task should ideally not fail if desc is valid
                    count += 1
            if count > 0:
                flash(f"{count} sub-task(s) suggested by AI and added.", 'success')
            else:
                # This might happen if suggestions were empty or invalid, though unlikely with current parsing.
                flash("AI provided suggestions, but none could be added as new sub-tasks.", 'warning')

    except Exception as e:
        # In a real scenario, log the error `e`
        print(f"Error during AI sub-task suggestion: {e}") # For debugging
        flash("An error occurred while trying to get AI suggestions. Please try again later.", 'error')

    return redirect(url_for('chore_detail_route', task_id=task_id))


if __name__ == '__main__':
    app.run(debug=True)
