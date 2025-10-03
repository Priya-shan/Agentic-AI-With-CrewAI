#!/usr/bin/env python
import sys
import warnings
import os
from datetime import datetime

from presidio.crew import PresidioTeam

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Create output directory if it doesn't exist
os.makedirs('output', exist_ok=True)

# Ecommerce

requirements = """
A simple task management system.
The system should allow users to add tasks, mark tasks as completed, and delete tasks.
The system should support assigning deadlines and priorities.
The system should provide a list of pending tasks, completed tasks, and overdue tasks.
The system should calculate completion percentage and provide a daily summary of tasks.
"""

module_name = "todo.py"
class_name = "Todo"


def run():
    """
    Run the research crew.
    """
    inputs = {
        'requirements': requirements,
        'module_name': module_name,
        'class_name': class_name
    }

    # Create and run the crew
    result = PresidioTeam().crew().kickoff(inputs=inputs)
    print(result)


if __name__ == "__main__":
    run()