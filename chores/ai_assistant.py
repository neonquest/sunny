# This module houses the logic for interacting with an AI service (Google Gemini)
# to get suggestions, such as breaking down chores into sub-tasks.

import os
from typing import List, Dict # Added Dict
import google.generativeai as genai
import re

# Attempt to configure API key from environment variable at module load time (optional)
# Or configure it within the function call to ensure it's checked each time.
# For this iteration, we'll check and configure within the function.

def get_subtask_and_material_suggestions(chore_description: str, existing_subtask_descriptions: List[str] = None) -> Dict[str, List[str]]:
    """
    Gets NEW sub-task suggestions AND material suggestions from Google Gemini API.
    Returns a dictionary: {'sub_tasks': [...], 'materials': [...]}.
    Falls back to returning empty lists or error messages if API key is not set or an error occurs.
    """
    if existing_subtask_descriptions is None:
        existing_subtask_descriptions = []

    default_response = {'sub_tasks': [], 'materials': []}
    api_key = os.environ.get("GOOGLE_API_KEY")

    if not api_key:
        print("[AI Assistant] GOOGLE_API_KEY not found. Skipping AI suggestions.")
        # Return a specific structure indicating the error for the caller to handle.
        default_response['sub_tasks'] = ["AI features disabled: GOOGLE_API_KEY not set."]
        return default_response

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')

        existing_tasks_prompt_part = "There are no existing sub-tasks yet."
        if existing_subtask_descriptions:
            existing_tasks_list_str = "\n".join([f"- {desc}" for desc in existing_subtask_descriptions])
            existing_tasks_prompt_part = f"The following sub-tasks already exist for this chore:\n{existing_tasks_list_str}"

        prompt = f"""
        You are a helpful assistant for breaking down household chores and identifying needed materials.
        The main chore is: "{chore_description}"

        {existing_tasks_prompt_part}

        1.  Based on the main chore and EXCLUDING the existing sub-tasks listed above, suggest up to 3-5 NEW, ADDITIONAL, and DISTINCT sub-tasks to help complete the main chore.
            Each new sub-task should represent a significant, high-level step. Avoid overly granular details.
            Ensure your new suggestions are not redundant with the existing ones.
            Format your new suggestions as a numbered list under a heading "New Sub-tasks:".
            If no further distinct high-level sub-tasks are needed, write "No new sub-tasks needed." under this heading.

        2.  Based on the main chore (and considering both existing and any new sub-tasks you might suggest), list common materials that might be needed to complete the overall chore.
            Format these materials as a simple comma-separated list under a heading "Suggested Materials:".
            If no specific materials come to mind or are typically needed, write "None" or "General cleaning supplies" under this heading.

        Example of expected output structure:
        New Sub-tasks:
        1. First new sub-task
        2. Second new sub-task

        Suggested Materials:
        Material A, Material B, Screwdriver
        """

        print(f"[AI Assistant] Sending prompt to Gemini for chore: '{chore_description}' (requesting sub-tasks and materials).")
        response = model.generate_content(prompt)

        if not response.text:
            print("[AI Assistant] Received empty response from Gemini.")
            return default_response

        print(f"[AI Assistant] Raw response from Gemini:\n{response.text}")

        suggested_sub_tasks = []
        suggested_materials = []

        # Parse response text
        lines = response.text.splitlines()
        parsing_subtasks = False
        parsing_materials = False

        for line in lines:
            line_lower = line.lower().strip()
            if "new sub-tasks:" in line_lower:
                parsing_subtasks = True
                parsing_materials = False
                continue
            if "suggested materials:" in line_lower:
                parsing_materials = True
                parsing_subtasks = False
                continue

            if parsing_subtasks:
                if "no new sub-tasks needed" in line_lower:
                    # Stop parsing subtasks if this phrase is found
                    parsing_subtasks = False
                    continue
                match = re.match(r"^\s*\d+\.?\s+(.*)", line)
                if match:
                    desc = match.group(1).strip()
                    if desc: suggested_sub_tasks.append(desc)

            elif parsing_materials:
                # Materials are expected as a comma-separated list on one or more lines after the heading.
                # We'll collect all lines under this heading and then process.
                # For simplicity, let's assume materials are on the line immediately following the heading,
                # or that they are the only content if the heading is the last part.
                # A more robust parser would handle multi-line material lists.
                if line_lower not in ["none", "general cleaning supplies", ""]: # ignore common non-material responses
                    # Split by comma, strip whitespace from each material
                    materials_from_line = [m.strip() for m in line.split(',') if m.strip()]
                    suggested_materials.extend(materials_from_line)
                parsing_materials = False # Assume materials are listed on one primary line after heading for now.

        # Further clean up materials: remove duplicates and ensure they are not empty
        if suggested_materials:
            unique_materials = []
            seen_materials = set()
            for mat in suggested_materials:
                if mat.lower() not in seen_materials and mat.lower() not in ["none", "general cleaning supplies"]:
                    unique_materials.append(mat)
                    seen_materials.add(mat.lower())
            suggested_materials = unique_materials


        print(f"[AI Assistant] Parsed suggestions - Sub-tasks: {suggested_sub_tasks}, Materials: {suggested_materials}")
        return {'sub_tasks': suggested_sub_tasks, 'materials': suggested_materials}

    except Exception as e:
        print(f"[AI Assistant] Error interacting with Google Gemini API: {e}")
        default_response['sub_tasks'] = [f"Error getting AI suggestions: {type(e).__name__}"]
        return default_response


# Helper mock function (can be removed if not needed for fallback)
def _get_mock_suggestions(chore_description: str) -> List[str]: # This mock is now outdated
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
