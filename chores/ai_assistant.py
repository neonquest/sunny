# This module will eventually house the logic for interacting with an AI service
# to get suggestions, such as breaking down chores into sub-tasks.

from typing import List
import time
import random

def get_subtask_suggestions(chore_description: str) -> List[str]:
    """
    Placeholder/mock function to simulate getting sub-task suggestions from an AI.
    In a real implementation, this would call an external AI API.
    """
    print(f"[AI Assistant Mock] Received request for chore: {chore_description}")

    # Simulate network delay and processing time
    time.sleep(random.uniform(0.5, 1.5))

    suggestions = []
    description_lower = chore_description.lower()

    if "kitchen" in description_lower:
        suggestions.extend([
            "Clear countertops",
            "Wash dishes",
            "Wipe down surfaces",
            "Clean sink",
            "Sweep or mop floor"
        ])
    elif "bathroom" in description_lower:
        suggestions.extend([
            "Clean toilet",
            "Clean sink and countertop",
            "Clean shower/tub",
            "Clean mirror",
            "Mop floor"
        ])
    elif "garden" in description_lower or "yard" in description_lower:
        suggestions.extend([
            "Mow the lawn",
            "Weed flower beds",
            "Water plants",
            "Trim hedges (if applicable)",
            "Rake leaves (if applicable)"
        ])
    elif "fix" in description_lower or "repair" in description_lower:
        suggestions.extend([
            "Identify the exact problem",
            "Gather necessary tools",
            "Research repair steps (e.g., online videos, manuals)",
            "Purchase any required parts",
            "Perform the repair carefully",
            "Test the repair"
        ])
    else:
        # Generic suggestions if no keywords match
        suggestions.extend([
            "Assess the scope of the chore",
            "Break down into smaller, manageable parts",
            "Gather all necessary tools and materials",
            "Execute each part systematically",
            "Clean up after completion"
        ])
        # Add a random number of generic items to make it seem more dynamic
        for i in range(random.randint(0,2)):
            suggestions.append(f"Generic suggested step {i+1}")

    # Simulate a small chance of AI "failing" or returning no suggestions
    if random.random() < 0.05: # 5% chance of empty suggestions
        print("[AI Assistant Mock] Simulating AI failure - returning no suggestions.")
        return []

    print(f"[AI Assistant Mock] Returning suggestions: {suggestions}")
    return suggestions[:random.randint(2,5)] # Return a random number of suggestions (2-5)
