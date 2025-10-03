```markdown
# Module: quiz.py

This module provides a simple quiz game engine, allowing administrators to create questions and players to take quizzes, track scores, and view history. It is designed to be completely self-contained within a single Python file.

## Internal Helper Classes

These classes are internal to the `Quiz` engine and encapsulate specific data structures and logic.

### Class: `Question`

Represents a single quiz question with its options and the correct answer.

**Attributes:**

*   `id` (str): A unique identifier for the question (UUID).
*   `question_text` (str): The text of the question.
*   `options` (List[str]): A list of strings, where each string is a possible answer option.
*   `correct_option_index` (int): The 0-based index of the correct answer within the `options` list.

**Methods:**

*   `__init__(self, question_text: str, options: List[str], correct_option_index: int)`
    *   **Description:** Initializes a new `Question` object.
    *   **Parameters:**
        *   `question_text`: The text of the question.
        *   `options`: A list of strings for the answer options.
        *   `correct_option_index`: The index of the correct answer in `options`.
    *   **Raises:** `ValueError` if `correct_option_index` is out of bounds.

*   `is_correct(self, chosen_index: int) -> bool`
    *   **Description:** Checks if a given chosen option index is the correct answer.
    *   **Parameters:**
        *   `chosen_index`: The 0-based index of the player's chosen answer.
    *   **Returns:** `True` if correct, `False` otherwise.

*   `to_dict(self) -> Dict[str, Any]`
    *   **Description:** Returns a dictionary representation of the question, including the correct answer index (for admin use).
    *   **Returns:** `Dict` with keys 'id', 'question_text', 'options', 'correct_option_index'.

*   `to_player_dict(self) -> Dict[str, Any]`
    *   **Description:** Returns a dictionary representation suitable for players, excluding the correct answer index.
    *   **Returns:** `Dict` with keys 'id', 'question_text', 'options'.

### Class: `QuizAttempt`

Manages the state and progress of a single quiz session for a specific player.

**Attributes:**

*   `attempt_id` (str): A unique identifier for this quiz attempt (UUID).
*   `player_name` (str): The name of the player taking the quiz.
*   `_questions_for_attempt` (List[Question]): The specific list of `Question` objects for this attempt, in the order they are presented.
*   `answers_given` (List[Optional[int]]): A list to store the player's chosen option index for each question, `None` if unanswered.
*   `correct_answers_count` (int): The number of questions answered correctly so far.
*   `current_question_idx` (int): The 0-based index of the *next* question to be presented to the player.
*   `is_completed` (bool): `True` if all questions have been answered or the quiz has been explicitly ended.
*   `start_time` (datetime): The timestamp when the quiz attempt started.
*   `end_time` (Optional[datetime]): The timestamp when the quiz attempt was completed or ended.
*   `question_results` (List[Dict[str, Any]]): A list storing detailed results for each question, including chosen and correct answers.

**Methods:**

*   `__init__(self, player_name: str, questions: List[Question])`
    *   **Description:** Initializes a new quiz attempt for a player with a specified set of questions.
    *   **Parameters:**
        *   `player_name`: The name of the player.
        *   `questions`: A list of `Question` objects to be used in this attempt.

*   `get_current_question_for_player(self) -> Optional[Dict[str, Any]]`
    *   **Description:** Returns the current question (the one at `current_question_idx`) for the player in a player-friendly dictionary format.
    *   **Returns:** `Dict` (id, question_text, options) or `None` if no more questions.

*   `submit_answer(self, question_id: str, chosen_option_index: int) -> bool`
    *   **Description:** Records a player's answer for the current question, updates score, and advances to the next question.
    *   **Parameters:**
        *   `question_id`: The ID of the question currently being answered (for validation).
        *   `chosen_option_index`: The 0-based index of the player's chosen answer.
    *   **Returns:** `True` if the answer was correct, `False` otherwise.
    *   **Raises:** `ValueError` if the quiz is completed, no more questions, `question_id` mismatch, or `chosen_option_index` is invalid.

*   `get_summary(self) -> Dict[str, Any]`
    *   **Description:** Generates a comprehensive summary of the quiz attempt, including total score, question-by-question results, and timestamps.
    *   **Returns:** `Dict` containing 'attempt_id', 'player_name', 'score', 'total_questions', 'start_time', 'end_time', 'is_completed', 'details'.

*   `get_score_history_entry(self) -> Dict[str, Any]`
    *   **Description:** Returns a simplified dictionary suitable for displaying in a player's score history.
    *   **Returns:** `Dict` containing 'attempt_id', 'score', 'total_questions', 'start_time', 'end_time', 'is_completed'.

## Main Class: `Quiz`

The central class for the quiz game engine, managing questions, active quizzes, and player score history.

**Attributes:**

*   `_questions` (Dict[str, Question]): A dictionary storing all available `Question` objects, keyed by their `id`.
*   `_active_quizzes` (Dict[str, QuizAttempt]): A dictionary storing ongoing `QuizAttempt` objects, keyed by `player_name`.
*   `_player_scores_history` (Dict[str, List[QuizAttempt]]): A dictionary storing lists of completed `QuizAttempt` objects for each player, keyed by `player_name`.

**Methods:**

### Initialization

*   `__init__(self)`
    *   **Description:** Initializes a new `Quiz` engine instance, setting up empty storage for questions, active quizzes, and player history.

### Admin Functions

These methods are intended for administrative tasks like managing questions.

*   `add_question(self, question_text: str, options: List[str], correct_option_index: int) -> str`
    *   **Description:** Adds a new question to the quiz engine's pool of available questions.
    *   **Parameters:**
        *   `question_text`: The text of the question.
        *   `options`: A list of strings representing the possible answer choices.
        *   `correct_option_index`: The 0-based index of the correct answer within the `options` list.
    *   **Returns:** `str`: The unique ID of the newly created question.
    *   **Raises:** `ValueError`: If `correct_option_index` is out of bounds for the provided `options`.

*   `get_all_questions(self) -> List[Dict[str, Any]]`
    *   **Description:** Retrieves a list of all questions currently stored in the system, including their correct answers. This is primarily for admin review or editing.
    *   **Returns:** `List[Dict[str, Any]]`: A list where each dictionary represents a question, including 'id', 'question_text', 'options', and 'correct_option_index'.

*   `delete_question(self, question_id: str) -> bool`
    *   **Description:** Removes a question from the system based on its ID.
    *   **Parameters:**
        *   `question_id`: The unique ID of the question to be deleted.
    *   **Returns:** `bool`: `True` if the question was found and deleted, `False` otherwise.

### Player Functions

These methods are for players to interact with the quiz engine.

*   `start_quiz(self, player_name: str, num_questions: Optional[int] = None) -> Optional[Dict[str, Any]]`
    *   **Description:** Initializes and starts a new quiz for the specified player. If a quiz is already active for this player, it will be replaced. Questions are randomly selected from the available pool and shuffled.
    *   **Parameters:**
        *   `player_name`: The unique identifier or name of the player.
        *   `num_questions`: (Optional) The desired number of questions for this quiz. If `None` or greater than available questions, all available questions will be used.
    *   **Returns:** `Optional[Dict[str, Any]]`: A dictionary representing the first question (including 'attempt_id', 'question_id', 'question_text', 'options'), or `None` if no questions are available to form a quiz.

*   `get_current_quiz_state(self, player_name: str) -> Optional[Dict[str, Any]]`
    *   **Description:** Retrieves the current question the player needs to answer for their active quiz.
    *   **Parameters:**
        *   `player_name`: The name of the player.
    *   **Returns:** `Optional[Dict[str, Any]]`: A dictionary with the current question details (including 'attempt_id', 'question_id', 'question_text', 'options'), or `None` if there is no active quiz for the player or the quiz is completed.

*   `submit_answer(self, player_name: str, question_id: str, chosen_option_index: int) -> bool`
    *   **Description:** Submits an answer for the current question in an active quiz. This method validates the answer against the correct one and updates the player's score and quiz progress.
    *   **Parameters:**
        *   `player_name`: The name of the player.
        *   `question_id`: The ID of the question for which the answer is being submitted. This must match the current question being presented.
        *   `chosen_option_index`: The 0-based index of the player's chosen answer option.
    *   **Returns:** `bool`: `True` if the submitted answer was correct, `False` otherwise.
    *   **Raises:** `ValueError`: If no active quiz exists for the player, the quiz is already completed, the `question_id` does not match the current question, or `chosen_option_index` is invalid.

*   `get_next_question_for_player(self, player_name: str) -> Optional[Dict[str, Any]]`
    *   **Description:** Retrieves the subsequent question for a player's active quiz after an answer has been submitted.
    *   **Parameters:**
        *   `player_name`: The name of the player.
    *   **Returns:** `Optional[Dict[str, Any]]`: A dictionary with the next question details (including 'attempt_id', 'question_id', 'question_text', 'options'), or `None` if the quiz is completed or no active quiz for the player.

*   `end_quiz(self, player_name: str) -> Optional[Dict[str, Any]]`
    *   **Description:** Explicitly ends the active quiz for a player, calculates the final score, and stores the attempt in the player's score history.
    *   **Parameters:**
        *   `player_name`: The name of the player.
    *   **Returns:** `Optional[Dict[str, Any]]`: A detailed summary of the completed quiz attempt (including 'attempt_id', 'player_name', 'score', 'total_questions', 'start_time', 'end_time', 'is_completed', 'details'), or `None` if there was no active quiz for the player.

*   `get_player_score_history(self, player_name: str) -> List[Dict[str, Any]]`
    *   **Description:** Retrieves a list of all past completed quiz attempts for a given player.
    *   **Parameters:**
        *   `player_name`: The name of the player.
    *   **Returns:** `List[Dict[str, Any]]`: A list of dictionaries, where each dictionary provides a summary of a past quiz attempt (including 'attempt_id', 'score', 'total_questions', 'start_time', 'end_time', 'is_completed').

*   `get_player_last_attempt_details(self, player_name: str, attempt_id: str) -> Optional[Dict[str, Any]]`
    *   **Description:** Retrieves the full, detailed summary of a specific completed quiz attempt for a player.
    *   **Parameters:**
        *   `player_name`: The name of the player.
        *   `attempt_id`: The unique ID of the specific quiz attempt to retrieve.
    *   **Returns:** `Optional[Dict[str, Any]]`: The full summary dictionary for the specified attempt (same format as `end_quiz` return), or `None` if the attempt is not found for the player.
```