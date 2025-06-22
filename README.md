# Chores Manager

A simple application to manage household chores.

## Features (Planned)

*   Task creation and tracking
*   Chore planning and scheduling
*   Material ordering suggestions (future)
*   Photo analysis for repair suggestions (future)

## Setup

1.  **Clone the repository (if applicable).**
2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Database:** The application uses an SQLite database (`chores_app.db`) which will be automatically created in the project root directory when the web application is first run (or when `chores/database.py` is run directly).

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
    *   **Manage Sub-tasks:** From the chore detail page, you can add new sub-tasks, mark them as complete/pending, delete them, or reorder them using 'Up'/'Down' buttons.
    *   **AI Sub-task & Material Suggestions:** On the chore detail page, click "Suggest with AI". This feature attempts to use the Google AI Gemini API (gemini-pro model) to generate:
        *   New, distinct, high-level sub-task suggestions (aware of existing sub-tasks).
        *   A list of common materials needed for the overall chore.
        *   **API Key Required:** For live AI suggestions, set the `GOOGLE_API_KEY` environment variable (get a key from [Google AI Studio](https://aistudio.google.com/)). Fallbacks/errors are handled if the key is missing.
        *   **De-duplication:** Suggested sub-tasks and materials are de-duplicated against existing items.
    *   **Materials List & Shopping Links:** Chores can have a list of needed materials (manually editable and AI-suggested). The chore detail page displays these materials with convenient search links to Amazon and Home Depot.
*   **Update Status:** Quickly change a chore's overall status (Pending, In Progress, Completed) from the main list.
*   **Delete Chore:** Remove a chore and all its associated details.

### CLI Features:
*   Basic functionality for adding, viewing, updating status, and deleting chores.
*   Basic planning note association (less extensive than web interface).

(More detailed instructions for specific CLI commands or web interactions can be added as needed.)
