# todo.py
# A self-contained module for a simple task management system.

import datetime
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Any, Dict, List, Optional

# --- 3. Data Models ---

class Priority(IntEnum):
    """Represents the priority of a task."""
    HIGH = 1
    MEDIUM = 2
    LOW = 3

@dataclass
class Task:
    """Represents a single task in the to-do list."""
    id: int
    description: str
    priority: Priority = Priority.MEDIUM
    deadline: Optional[datetime.date] = None
    is_completed: bool = False
    creation_date: datetime.date = field(default_factory=datetime.date.today)
    completion_date: Optional[datetime.date] = None

# --- 4. Todo Class Design ---

class Todo:
    """
    A class to manage a collection of tasks.
    """
    def __init__(self):
        """Initializes a new, empty Todo list manager."""
        self._tasks: Dict[int, Task] = {}
        self._next_id: int = 1

    def add_task(
        self,
        description: str,
        priority: Priority = Priority.MEDIUM,
        deadline: Optional[datetime.date] = None
    ) -> int:
        """
        Adds a new task to the system. It generates a unique ID, creates a
        Task object, and stores it.
        """
        task_id = self._next_id
        new_task = Task(
            id=task_id,
            description=description,
            priority=priority,
            deadline=deadline
        )
        self._tasks[task_id] = new_task
        self._next_id += 1
        return task_id

    def delete_task(self, task_id: int) -> bool:
        """
        Deletes a task from the system using its ID.
        Returns True if successful, False if the task ID was not found.
        """
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def complete_task(self, task_id: int) -> Optional[Task]:
        """
        Marks a task as completed. Sets is_completed to True and records the
        completion_date. Returns the updated Task object if found, otherwise None.
        """
        task = self.get_task(task_id)
        if task:
            task.is_completed = True
            task.completion_date = datetime.date.today()
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        """
        Retrieves a single task by its ID.
        Returns the Task object if found, otherwise None.
        """
        return self._tasks.get(task_id)

    def get_pending_tasks(self) -> List[Task]:
        """
        Returns a list of all tasks that are not yet completed, sorted by
        priority (high to low) and then by deadline (earliest first).
        """
        pending = [task for task in self._tasks.values() if not task.is_completed]
        # Sort by priority (ascending, since smaller number is higher priority),
        # then by deadline. None deadlines are considered last.
        pending.sort(key=lambda t: (t.priority, t.deadline or datetime.date.max))
        return pending

    def get_completed_tasks(self) -> List[Task]:
        """
        Returns a list of all tasks that have been marked as completed,
        sorted by completion date (most recent first).
        """
        completed = [task for task in self._tasks.values() if task.is_completed]
        # Sort by completion date, most recent first.
        # Completion date cannot be None for a completed task.
        completed.sort(key=lambda t: t.completion_date, reverse=True)
        return completed

    def get_overdue_tasks(self) -> List[Task]:
        """
        Returns a list of all pending tasks whose deadline has passed.
        The list is sorted by deadline (oldest first).
        """
        today = datetime.date.today()
        overdue = [
            task for task in self._tasks.values()
            if not task.is_completed and task.deadline and task.deadline < today
        ]
        # Sort by deadline, oldest first.
        overdue.sort(key=lambda t: t.deadline)
        return overdue

    def get_completion_percentage(self) -> float:
        """
        Calculates the percentage of tasks that have been completed.
        Returns 0.0 if there are no tasks.
        """
        total_tasks = len(self._tasks)
        if total_tasks == 0:
            return 0.0

        completed_tasks = len(self.get_completed_tasks())
        return (completed_tasks / total_tasks) * 100.0

    def get_daily_summary(
        self,
        summary_date: Optional[datetime.date] = None
    ) -> Dict[str, Any]:
        """
        Provides a summary of task activity for a specific day.
        Defaults to the current day if no date is provided.
        """
        if summary_date is None:
            summary_date = datetime.date.today()

        tasks_created = [
            task for task in self._tasks.values()
            if task.creation_date == summary_date
        ]

        tasks_completed = [
            task for task in self._tasks.values()
            if task.completion_date == summary_date
        ]
        
        # A snapshot of tasks that were overdue on that day.
        # This means they were not completed and their deadline was before that day.
        overdue_tasks_snapshot = [
            task for task in self._tasks.values()
            if (not task.is_completed or (task.completion_date and task.completion_date > summary_date))
               and task.deadline and task.deadline < summary_date
        ]

        return {
            "date": summary_date,
            "tasks_created": tasks_created,
            "tasks_completed": tasks_completed,
            "overdue_tasks_snapshot": overdue_tasks_snapshot
        }