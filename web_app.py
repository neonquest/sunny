from flask import Flask, render_template, url_for, request, redirect, flash
from chores import tasks, planning # Import the tasks and planning modules

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
        if description:
            new_task = tasks.add_task(description)
            flash(f"Chore '{new_task.description}' added successfully!", 'success')
            return redirect(url_for('view_chores_route'))
        else:
            flash('Chore description cannot be empty.', 'error')
            return render_template('add_chore.html', title="Add New Chore"), 400 # Bad request

    # For GET request, just show the form
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
        # Attempt to delete the task
        if tasks.delete_task(task_id):
            planning.remove_plan(task_id) # Also remove any associated plan
            flash(f"Chore '{task.description}' and any associated plans deleted successfully.", 'success')
        else:
            # This case should ideally not be hit if task was found by get_task_by_id
            flash(f"Failed to delete chore '{task.description}'.", 'error')
    else:
        flash(f"Chore with ID {task_id} not found.", 'error')

    return redirect(url_for('view_chores_route'))


if __name__ == '__main__':
    app.run(debug=True)
