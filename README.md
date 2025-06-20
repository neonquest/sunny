# Chores Manager

A simple application to manage household chores.

## Features (Planned)

*   Task creation and tracking
*   Chore planning and scheduling
*   Material ordering suggestions (future)
*   Photo analysis for repair suggestions (future)

## Setup

(Instructions to be added)

## Running the Web Application

1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Run the Flask development server:**
    ```bash
    python web_app.py
    ```
3.  Open your web browser and go to `http://127.0.0.1:5000/`.

## Running the Command-Line Interface (CLI)

1.  **Run the main CLI script:**
    ```bash
    python main.py
    ```

## Usage

The application supports managing chores through a Command-Line Interface (CLI) or a web interface.

### Web Interface Features:
*   **View Chores:** Lists all chores, their status, due date, and sub-task count.
*   **Chore Details:** Click on a chore to see its full details including notes and a list of sub-tasks.
*   **Add Chore:** Create new chores, optionally specifying initial notes and a due date.
*   **Edit Chore Details:** Modify a chore's description, notes, and due date.
*   **Manage Sub-tasks:** From the chore detail page, you can add new sub-tasks, mark them as complete/pending, or delete them.
*   **Update Status:** Quickly change a chore's overall status (Pending, In Progress, Completed) from the main list.
*   **Delete Chore:** Remove a chore and all its associated details.

### CLI Features:
*   Basic functionality for adding, viewing, updating status, and deleting chores.
*   Basic planning note association (less extensive than web interface).

(More detailed instructions for specific CLI commands or web interactions can be added as needed.)
