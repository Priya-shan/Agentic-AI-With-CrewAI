import uuid
from datetime import datetime
import random
from typing import List, Dict, Any, Optional

# Internal Helper Classes

class Question:
    def __init__(self, question_text: str, options: List[str], correct_option_index: int):
        if not (0 <= correct_option_index < len(options)):
            raise ValueError("correct_option_index is out of bounds for the provided options.")

        self.id = str(uuid.uuid4())
        self.question_text = question_text
        self.options = list(options) # Ensure a copy is stored
        self.correct_option_index = correct_option_index

    def is_correct(self, chosen_index: int) -> bool:
        return chosen_index == self.correct_option_index

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'question_text': self.question_text,
            'options': self.options,
            'correct_option_index': self.correct_option_index
        }

    def to_player_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'question_text': self.question_text,
            'options': self.options
        }

class QuizAttempt:
    def __init__(self, player_name: str, questions: List[Question]):
        if not questions:
            raise ValueError("A quiz attempt must have at least one question.")

        self.attempt_id = str(uuid.uuid4())
        self.player_name = player_name
        self._questions_for_attempt = list(questions) # Store a copy
        self.answers_given: List[Optional[int]] = [None] * len(questions)
        self.correct_answers_count = 0
        self.current_question_idx = 0
        self.is_completed = False
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
        self.question_results: List[Dict[str, Any]] = []

    def get_current_question_for_player(self) -> Optional[Dict[str, Any]]:
        if self.is_completed or self.current_question_idx >= len(self._questions_for_attempt):
            return None
        current_q = self._questions_for_attempt[self.current_question_idx]
        player_dict = current_q.to_player_dict()
        player_dict['attempt_id'] = self.attempt_id # Add attempt_id to player view
        return player_dict

    def submit_answer(self, question_id: str, chosen_option_index: int) -> bool:
        if self.is_completed:
            raise ValueError("Quiz is already completed.")
        if self.current_question_idx >= len(self._questions_for_attempt):
            raise ValueError("No more questions in this quiz.")

        current_question = self._questions_for_attempt[self.current_question_idx]
        if question_id != current_question.id:
            raise ValueError(f"Question ID mismatch. Expected {current_question.id}, got {question_id}.")

        if not (0 <= chosen_option_index < len(current_question.options)):
            raise ValueError(f"Chosen option index {chosen_option_index} is out of bounds for question '{current_question.question_text}'.")

        self.answers_given[self.current_question_idx] = chosen_option_index
        is_correct = current_question.is_correct(chosen_option_index)

        if is_correct:
            self.correct_answers_count += 1

        self.question_results.append({
            'question_id': current_question.id,
            'question_text': current_question.question_text,
            'options': current_question.options,
            'chosen_answer_index': chosen_option_index,
            'correct_answer_index': current_question.correct_option_index,
            'is_correct': is_correct
        })

        self.current_question_idx += 1
        if self.current_question_idx >= len(self._questions_for_attempt):
            self.is_completed = True
            self.end_time = datetime.now()

        return is_correct

    def get_summary(self) -> Dict[str, Any]:
        # If quiz is not completed but summary is requested (e.g., via end_quiz),
        # mark it as completed and set end_time if not already set.
        if not self.is_completed: # Don't overwrite if already completed from submit_answer
            self.is_completed = True
        if self.end_time is None: # Only set end_time if not already set
            self.end_time = datetime.now()

        return {
            'attempt_id': self.attempt_id,
            'player_name': self.player_name,
            'score': self.correct_answers_count,
            'total_questions': len(self._questions_for_attempt),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_completed': self.is_completed,
            'details': self.question_results
        }

    def get_score_history_entry(self) -> Dict[str, Any]:
        # Ensure that the attempt is marked as completed and end_time is set for history display
        # This state manipulation should ideally be done consistently on quiz completion
        # For history display, we ensure the data reflects a completed state
        if not self.is_completed:
            # If for some reason this is called on an active quiz, it will behave as if ended
            self.is_completed = True
        if self.end_time is None:
            self.end_time = datetime.now()

        return {
            'attempt_id': self.attempt_id,
            'score': self.correct_answers_count,
            'total_questions': len(self._questions_for_attempt),
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'is_completed': self.is_completed
        }

# Main Class: Quiz

class Quiz:
    def __init__(self):
        self._questions: Dict[str, Question] = {}
        self._active_quizzes: Dict[str, QuizAttempt] = {}
        self._player_scores_history: Dict[str, List[QuizAttempt]] = {}

    # Admin Functions

    def add_question(self, question_text: str, options: List[str], correct_option_index: int) -> str:
        new_question = Question(question_text, options, correct_option_index)
        self._questions[new_question.id] = new_question
        return new_question.id

    def get_all_questions(self) -> List[Dict[str, Any]]:
        return [q.to_dict() for q in self._questions.values()]

    def delete_question(self, question_id: str) -> bool:
        if question_id in self._questions:
            del self._questions[question_id]
            return True
        return False

    # Player Functions

    def start_quiz(self, player_name: str, num_questions: Optional[int] = None) -> Optional[Dict[str, Any]]:
        available_questions = list(self._questions.values())
        if not available_questions:
            return None

        random.shuffle(available_questions)

        if num_questions is None or num_questions > len(available_questions):
            selected_questions = available_questions
        else:
            selected_questions = available_questions[:num_questions]

        if not selected_questions: # Should not happen if available_questions is not empty after filtering
            return None

        # If a quiz is already active, end it and move to history
        if player_name in self._active_quizzes:
            self.end_quiz(player_name) # This will store the old quiz in history

        new_attempt = QuizAttempt(player_name, selected_questions)
        self._active_quizzes[player_name] = new_attempt

        # Return the first question
        first_question = new_attempt.get_current_question_for_player()
        if first_question:
            # Ensure attempt_id is included as per design for the return value
            first_question['attempt_id'] = new_attempt.attempt_id
        return first_question


    def get_current_quiz_state(self, player_name: str) -> Optional[Dict[str, Any]]:
        active_attempt = self._active_quizzes.get(player_name)
        if not active_attempt:
            return None
        current_q_data = active_attempt.get_current_question_for_player()
        if current_q_data:
            current_q_data['attempt_id'] = active_attempt.attempt_id # Ensure attempt_id is present
        return current_q_data

    def submit_answer(self, player_name: str, question_id: str, chosen_option_index: int) -> bool:
        active_attempt = self._active_quizzes.get(player_name)
        if not active_attempt:
            raise ValueError(f"No active quiz for player '{player_name}'.")

        is_correct = active_attempt.submit_answer(question_id, chosen_option_index)

        # If quiz is completed after submitting this answer, move it to history
        if active_attempt.is_completed:
            self._player_scores_history.setdefault(player_name, []).append(active_attempt)
            del self._active_quizzes[player_name]

        return is_correct

    def get_next_question_for_player(self, player_name: str) -> Optional[Dict[str, Any]]:
        active_attempt = self._active_quizzes.get(player_name)
        if not active_attempt:
            return None # No active quiz or quiz ended

        next_q_data = active_attempt.get_current_question_for_player()
        if next_q_data:
            next_q_data['attempt_id'] = active_attempt.attempt_id
        return next_q_data

    def end_quiz(self, player_name: str) -> Optional[Dict[str, Any]]:
        active_attempt = self._active_quizzes.get(player_name)
        if not active_attempt:
            return None

        # The get_summary method of QuizAttempt handles marking it as completed and setting end_time
        summary = active_attempt.get_summary()

        self._player_scores_history.setdefault(player_name, []).append(active_attempt)
        del self._active_quizzes[player_name]
        return summary

    def get_player_score_history(self, player_name: str) -> List[Dict[str, Any]]:
        history = self._player_scores_history.get(player_name, [])
        # Call get_score_history_entry on each attempt to ensure consistent data and handling of completion status
        return [attempt.get_score_history_entry() for attempt in history]

    def get_player_last_attempt_details(self, player_name: str, attempt_id: str) -> Optional[Dict[str, Any]]:
        history = self._player_scores_history.get(player_name, [])
        for attempt in history:
            if attempt.attempt_id == attempt_id:
                # Call get_summary on the specific attempt to ensure consistent data and handling of completion status
                return attempt.get_summary()
        return None