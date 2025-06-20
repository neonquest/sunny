# This module houses the logic for interacting with an AI service (Google Gemini)
# to get suggestions, such as breaking down chores into sub-tasks.

import os
from typing import List
import google.generativeai as genai
import re

# Attempt to configure API key from environment variable at module load time (optional)
# Or configure it within the function call to ensure it's checked each time.
# For this iteration, we'll check and configure within the function.

def get_subtask_suggestions(chore_description: str) -> List[str]:
    """
    Gets sub-task suggestions from Google Gemini API based on the chore description.
    Falls back to returning an empty list if API key is not set or an error occurs.
    """
    api_key = os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        print("[AI Assistant] GOOGLE_API_KEY not found in environment variables. Skipping AI suggestions.")
        # To simulate the previous mock behavior somewhat if no key is found:
        # return _get_mock_suggestions(chore_description)
        return ["AI features disabled: GOOGLE_API_KEY not set."]


    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash') # Or other suitable model

        prompt = f"""
        Break down the following household chore into a short, numbered list of actionable sub-tasks.
        Each sub-task should be a concise action. Do not include a preamble or a conclusion, just the numbered list.
        Limit the number of sub-tasks to a maximum of 5.

        Chore: "{chore_description}"

        Sub-tasks:
        """

        print(f"[AI Assistant] Sending prompt to Gemini for chore: {chore_description}")
        response = model.generate_content(prompt)

        if not response.text:
            print("[AI Assistant] Received empty response from Gemini.")
            return []

        print(f"[AI Assistant] Raw response from Gemini: {response.text}")

        # Parse the response to extract sub-tasks
        # Assuming AI returns a numbered list like:
        # 1. First sub-task
        # 2. Second sub-task
        # ...
        sub_tasks = []
        # Regex to find lines starting with a number, a dot, and then the task description.
        # It captures the text after "number. ".
        # Handles potential variations in spacing.
        for line in response.text.splitlines():
            match = re.match(r"^\s*\d+\.?\s+(.*)", line)
            if match:
                sub_task_description = match.group(1).strip()
                if sub_task_description: # Ensure it's not an empty string
                    sub_tasks.append(sub_task_description)

        if not sub_tasks:
             print(f"[AI Assistant] Could not parse any sub-tasks from Gemini response: {response.text}")
             # Fallback: maybe the whole response is a single task or a list without numbers
             # This is a very basic fallback, more sophisticated parsing might be needed for varied AI outputs.
             if len(response.text.splitlines()) <= 5 and len(response.text.splitlines()) > 0 : # if it's a short list of lines
                 return [line.strip() for line in response.text.splitlines() if line.strip()]


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
