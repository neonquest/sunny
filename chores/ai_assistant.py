# This module houses the logic for interacting with an AI service (Google Gemini)
# to get suggestions, such as breaking down chores into sub-tasks.

import os
from typing import List
import google.generativeai as genai
import re

# Attempt to configure API key from environment variable at module load time (optional)
# Or configure it within the function call to ensure it's checked each time.
# For this iteration, we'll check and configure within the function.

def get_subtask_suggestions(chore_description: str, existing_subtask_descriptions: List[str] = None) -> List[str]:
    """
    Gets NEW sub-task suggestions from Google Gemini API, considering existing sub-tasks.
    Falls back to returning an empty list or error message if API key is not set or an error occurs.
    """
    if existing_subtask_descriptions is None:
        existing_subtask_descriptions = []

    api_key = os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        print("[AI Assistant] GOOGLE_API_KEY not found in environment variables. Skipping AI suggestions.")
        return ["AI features disabled: GOOGLE_API_KEY not set."]

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-pro')

        existing_tasks_prompt_part = "There are no existing sub-tasks yet."
        if existing_subtask_descriptions:
            existing_tasks_list_str = "\n".join([f"- {desc}" for desc in existing_subtask_descriptions])
            existing_tasks_prompt_part = f"The following sub-tasks already exist for this chore:\n{existing_tasks_list_str}"

        prompt = f"""
        You are a helpful assistant for breaking down household chores into actionable steps.
        The main chore is: "{chore_description}"
        The existing sub-tasks list is: "{existing_tasks_prompt_part}"

        {existing_tasks_prompt_part}

        Based on the main chore and EXCLUDING the existing sub-tasks, suggest if any NEW, ADDITIONAL, and DISTINCT actionable sub-tasks to help complete the main chore.
        Ensure your new suggestions are not redundant with the existing ones. It is not necessary to include new sub tasks. 
        For example, if the main chore is 'Clean the kitchen', a good high-level sub-task is 'Wash dishes', not 'Turn on tap' or 'Scrub each plate individually'.
        Ensure your new suggestions are not redundant with the existing ones.
        Format your new suggestions as a numbered list.
        If no further distinct high-level sub-tasks are needed or you cannot think of any, respond with the exact phrase "No new suggestions needed." or provide an empty list.
        Do not include any preamble or concluding remarks, only the list of new sub-tasks or the specific phrase if none are needed.

        New additional sub-tasks:
        """

        print(f"[AI Assistant] Sending prompt to Gemini for chore: '{chore_description}' with {len(existing_subtask_descriptions)} existing sub-tasks (requesting high-level).")
        # print(f"Full prompt:\n{prompt}") # For debugging prompt structure
        response = model.generate_content(prompt)

        if not response.text:
            print("[AI Assistant] Received empty response from Gemini.")
            return []

        print(f"[AI Assistant] Raw response from Gemini: {response.text}")

        # Handle the "No new suggestions needed." case
        if "no new suggestions needed" in response.text.lower():
            print("[AI Assistant] Gemini indicated no new suggestions are needed.")
            return []

        # Parse the response to extract sub-tasks
        sub_tasks = []
        # Regex to find lines starting with a number, a dot, and then the task description.
        for line in response.text.splitlines():
            match = re.match(r"^\s*\d+\.?\s+(.*)", line)
            if match:
                sub_task_description = match.group(1).strip()
                if sub_task_description: # Ensure it's not an empty string
                    sub_tasks.append(sub_task_description)

        if not sub_tasks and response.text.strip(): # If no numbered list found, but there is text
             print(f"[AI Assistant] Could not parse numbered sub-tasks from Gemini response. Using lines as fallback: {response.text}")
             # Fallback: use non-empty lines as suggestions if no numbered list is found.
             # This is a basic fallback.
             potential_fallback_tasks = [line.strip() for line in response.text.splitlines() if line.strip()]
             # Filter out common non-task phrases if necessary, or just return them.
             if len(potential_fallback_tasks) <= 5: # Arbitrary limit for fallback
                 return potential_fallback_tasks

        print(f"[AI Assistant] Parsed suggestions: {sub_tasks}")
        return sub_tasks

    except Exception as e:
        print(f"[AI Assistant] Error interacting with Google Gemini API: {e}")
        # Potentially provide more specific error messages based on exception type
        return [f"Error getting AI suggestions: {type(e).__name__}"]


# Helper mock function (can be removed if not needed for fallback)
def _get_mock_suggestions(chore_description: str) -> List[str]:
    """Provides basic mock suggestions if API key is not available."""
    # This is a simplified version of the previous mock
    suggestions = []
    description_lower = chore_description.lower()
    if "kitchen" in description_lower:
        suggestions.extend(["Clear countertops", "Wash dishes", "Wipe surfaces"])
    elif "fix" in description_lower:
        suggestions.extend(["Identify problem", "Gather tools", "Attempt repair"])
    else:
        suggestions.extend(["Assess task", "Break into steps", "Execute steps"])
    return suggestions[:3] # Return up to 3 mock suggestions
