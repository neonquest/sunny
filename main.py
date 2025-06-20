# Main application file for the Chores Manager
from chores import tasks, planning # Assuming tasks and planning are exposed via chores/__init__.py

def print_menu():
    """Prints the main menu options."""
    print("\nChores Manager Menu:")
    print("1. Add new chore")
    print("2. View all chores")
    print("3. Update chore status")
    print("4. Delete chore")
    print("5. Add/Update plan for chore")
    print("6. View plan for chore")
    print("7. Exit")

def handle_add_chore():
    """Handles adding a new chore."""
    description = input("Enter chore description: ")
    task = tasks.add_task(description)
    print(f"Chore added: {task}")

def handle_view_chores():
    """Handles viewing all chores."""
    all_tasks = tasks.get_all_tasks()
    if not all_tasks:
        print("No chores yet!")
        return
    print("\n--- All Chores ---")
    for task in all_tasks:
        print(task)
    print("------------------")

def handle_update_chore_status():
    """Handles updating a chore's status."""
    try:
        task_id_str = input("Enter chore ID to update: ")
        task_id = int(task_id_str)
        new_status = input(f"Enter new status for chore {task_id} (e.g., pending, in progress, completed): ")
        updated_task = tasks.update_task_status(task_id, new_status)
        if updated_task:
            print(f"Chore status updated: {updated_task}")
        else:
            print(f"Chore with ID {task_id} not found.")
    except ValueError:
        print("Invalid input. Chore ID must be a number.")

def handle_delete_chore():
    """Handles deleting a chore."""
    try:
        task_id_str = input("Enter chore ID to delete: ")
        task_id = int(task_id_str)
        if tasks.delete_task(task_id):
            print(f"Chore with ID {task_id} deleted.")
            planning.remove_plan(task_id) # Also remove any associated plan
        else:
            print(f"Chore with ID {task_id} not found.")
    except ValueError:
        print("Invalid input. Chore ID must be a number.")

def handle_add_plan():
    """Handles adding or updating a plan for a chore."""
    try:
        task_id_str = input("Enter chore ID to plan for: ")
        task_id = int(task_id_str)
        task = tasks.get_task_by_id(task_id)
        if not task:
            print(f"Chore with ID {task_id} not found. Cannot add plan.")
            return

        print(f"Adding/Updating plan for: {task}")
        notes = input("Enter planning notes (optional): ")
        due_date = input("Enter due date (e.g., YYYY-MM-DD, optional): ")

        plan_details = {}
        if notes:
            plan_details["notes"] = notes
        if due_date:
            plan_details["due_date"] = due_date

        if not plan_details:
            print("No planning details provided. Plan not added/updated.")
            return

        if planning.add_plan_details(task_id, plan_details):
            print(f"Plan details added/updated for chore ID {task_id}.")
        else:
            # This case should ideally not be hit if task_id validation is done prior
            print(f"Failed to add/update plan for chore ID {task_id}.")

    except ValueError:
        print("Invalid input. Chore ID must be a number.")


def handle_view_plan():
    """Handles viewing the plan for a chore."""
    try:
        task_id_str = input("Enter chore ID to view plan: ")
        task_id = int(task_id_str)
        task = tasks.get_task_by_id(task_id)
        if not task:
            print(f"Chore with ID {task_id} not found.")
            return

        plan_details = planning.get_plan_details(task_id)
        print(f"\n--- Plan for Chore: {task.description} (ID: {task.id}) ---")
        if plan_details:
            for key, value in plan_details.items():
                print(f"  {key.replace('_', ' ').capitalize()}: {value}")
        else:
            print("  No plan details found for this chore.")
        print("--------------------------------------")

    except ValueError:
        print("Invalid input. Chore ID must be a number.")


def main():
    """Main function to run the Chores Manager CLI."""
    print("Welcome to the Chores Manager!")

    while True:
        print_menu()
        choice = input("Enter your choice (1-7): ")

        if choice == '1':
            handle_add_chore()
        elif choice == '2':
            handle_view_chores()
        elif choice == '3':
            handle_update_chore_status()
        elif choice == '4':
            handle_delete_chore()
        elif choice == '5':
            handle_add_plan()
        elif choice == '6':
            handle_view_plan()
        elif choice == '7':
            print("Exiting Chores Manager. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 7.")

if __name__ == "__main__":
    main()
