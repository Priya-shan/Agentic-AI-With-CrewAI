### **Design Doc: `todo.py` Task Management Module**

### 1. Overview

This document outlines the design for a single-module, single-class task management system. The module, `todo.py`, will contain a class named `Todo` that encapsulates all functionality for managing tasks. The system will be entirely in-memory and self-contained, requiring no external databases or dependencies beyond the Python standard library. The design prioritizes clarity, testability, and ease of use.

### 2. Module Structure (`todo.py`)

The module will consist of the following components, all within the `todo.py` file:

1.  **Imports**: Necessary imports from the standard library (`datetime`, `typing`, `dataclasses`, `enum`).
2.  **`Priority` Enum**: An `IntEnum` to represent task priorities in a clear and type-safe manner. This makes sorting and comparisons more robust than using strings.
3.  **`Task` Dataclass**: A dataclass to represent the structure and attributes of a single task. This provides a clean, immutable-by-default way to handle task data.
4.  **`Todo` Class**: The main class that will contain the logic for managing the collection of tasks.

### 3. Data Models

#### 3.1. `Priority` Enum

To handle priorities consistently, we will define an `IntEnum`. This allows us to treat priorities as integers for easy sorting (lower number = higher priority).

```python
from enum import IntEnum

class Priority(IntEnum):
    """Represents the priority of a task."""
    HIGH = 1
    MEDIUM = 2
    LOW = 3
```

#### 3.2. `Task` Dataclass

This dataclass will serve as the blueprint for every task object managed by the system.

```python
import datetime
from dataclasses import dataclass, field
from typing import Optional

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
```

**Fields:**
*   `id` (`int`): A unique identifier for the task.
*   `description` (`str`): The text describing the task.
*   `priority` (`Priority`): The task's priority (HIGH, MEDIUM, LOW). Defaults to `MEDIUM`.
*   `deadline` (`Optional[datetime.date]`): An optional deadline for the task.
*   `is_completed` (`bool`): The status of the task. Defaults to `False`.
*   `creation_date` (`datetime.date`): The date the task was created. Defaults to the current day.
*   `completion_date` (`Optional[datetime.date]`): The date the task was marked as completed. `None` if pending.

---

### 4. `Todo` Class Design

This is the primary class for interacting with the task management system. It will manage a collection of `Task` objects.

#### 4.1. Properties

The `Todo` class will have the following internal properties:

*   `_tasks` (`Dict[int, Task]`): A private dictionary to store task objects, keyed by their unique `id`. This provides efficient O(1) lookups, updates, and deletions.
*   `_next_id` (`int`): A private integer to track the next available ID for a new task.

#### 4.2. Method Signatures

Here are the detailed signatures and descriptions for all public methods of the `Todo` class.

##### `__init__(self)`
*   **Description:** Initializes a new, empty `Todo` list manager.
*   **Parameters:** None.
*   **Returns:** `None`.

##### `add_task(self, description: str, priority: Priority = Priority.MEDIUM, deadline: Optional[datetime.date] = None) -> int`
*   **Description:** Adds a new task to the system. It generates a unique ID, creates a `Task` object, and stores it.
*   **Parameters:**
    *   `description` (`str`): A clear description of the task.
    *   `priority` (`Priority`): The priority of the task. Defaults to `MEDIUM`.
    *   `deadline` (`Optional[datetime.date]`): An optional deadline for the task.
*   **Returns:** (`int`): The unique ID of the newly created task.

##### `delete_task(self, task_id: int) -> bool`
*   **Description:** Deletes a task from the system using its ID.
*   **Parameters:**
    *   `task_id` (`int`): The ID of the task to delete.
*   **Returns:** (`bool`): `True` if the deletion was successful, `False` if no task with the given ID was found.

##### `complete_task(self, task_id: int) -> Optional[Task]`
*   **Description:** Marks a task as completed. Sets `is_completed` to `True` and records the `completion_date`.
*   **Parameters:**
    *   `task_id` (`int`): The ID of the task to complete.
*   **Returns:** (`Optional[Task]`): The updated `Task` object if found, otherwise `None`.

##### `get_task(self, task_id: int) -> Optional[Task]`
*   **Description:** Retrieves a single task by its ID.
*   **Parameters:**
    *   `task_id` (`int`): The ID of the task to retrieve.
*   **Returns:** (`Optional[Task]`): The `Task` object if found, otherwise `None`.

##### `get_pending_tasks(self) -> List[Task]`
*   **Description:** Returns a list of all tasks that are not yet completed. The list is sorted by priority (high to low) and then by deadline (earliest first).
*   **Parameters:** None.
*   **Returns:** (`List[Task]`): A sorted list of pending `Task` objects.

##### `get_completed_tasks(self) -> List[Task]`
*   **Description:** Returns a list of all tasks that have been marked as completed. The list is sorted by completion date (most recent first).
*   **Parameters:** None.
*   **Returns:** (`List[Task]`): A sorted list of completed `Task` objects.

##### `get_overdue_tasks(self) -> List[Task]`
*   **Description:** Returns a list of all pending tasks whose deadline has passed. The check is performed against the current date. The list is sorted by deadline (oldest first).
*   **Parameters:** None.
*   **Returns:** (`List[Task]`): A sorted list of overdue `Task` objects.

##### `get_completion_percentage(self) -> float`
*   **Description:** Calculates the percentage of tasks that have been completed.
*   **Parameters:** None.
*   **Returns:** (`float`): The completion percentage (from 0.0 to 100.0). Returns `0.0` if there are no tasks.

##### `get_daily_summary(self, summary_date: Optional[datetime.date] = None) -> Dict[str, Any]`
*   **Description:** Provides a summary of task activity for a specific day. If no date is provided, it defaults to the current day. The summary includes tasks created, tasks completed, and a snapshot of overdue tasks on that day.
*   **Parameters:**
    *   `summary_date` (`Optional[datetime.date]`): The date for which to generate the summary. Defaults to `datetime.date.today()`.
*   **Returns:** (`Dict[str, Any]`): A dictionary containing the summary, with keys: `date`, `tasks_created`, `tasks_completed`, and `overdue_tasks_snapshot`.

---

### 5. Full Module Code Structure (`todo.py`)

This is how the final `todo.py` file will be structured.

```python
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
        """Adds a new task to the system."""
        # Implementation...
        pass

    def delete_task(self, task_id: int) -> bool:
        """Deletes a task from the system using its ID."""
        # Implementation...
        pass

    def complete_task(self, task_id: int) -> Optional[Task]:
        """Marks a task as completed."""
        # Implementation...
        pass

    def get_task(self, task_id: int) -> Optional[Task]:
        """Retrieves a single task by its ID."""
        # Implementation...
        pass

    def get_pending_tasks(self) -> List[Task]:
        """Returns a list of all tasks that are not yet completed."""
        # Implementation...
        pass

    def get_completed_tasks(self) -> List[Task]:
        """Returns a list of all tasks that have been marked as completed."""
        # Implementation...
        pass

    def get_overdue_tasks(self) -> List[Task]:
        """Returns a list of all pending tasks whose deadline has passed."""
        # Implementation...
        pass

    def get_completion_percentage(self) -> float:
        """Calculates the percentage of tasks that have been completed."""
        # Implementation...
        pass

    def get_daily_summary(
        self,
        summary_date: Optional[datetime.date] = None
    ) -> Dict[str, Any]:
        """Provides a summary of task activity for a specific day."""
        # Implementation...
        pass

```