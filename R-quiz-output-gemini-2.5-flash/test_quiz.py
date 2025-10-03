import unittest
import uuid
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import random

# Assume quiz.py content is available in the same directory or imported
# For testing, we will just include the classes here to make the test file self-contained
# In a real scenario, you'd do:
# from quiz import Question, QuizAttempt, Quiz

class Question:
    def __init__(self, question_text: str, options: list[str], correct_option_index: int):
        if not (0 <= correct_option_index < len(options)):
            raise ValueError("correct_option_index is out of bounds for the provided options.")

        self.id = str(uuid.uuid4())
        self.question_text = question_text
        self.options = list(options) # Ensure a copy is stored
        self.correct_option_index = correct_option_index

    def is_correct(self, chosen_index: int) -> bool:
        return chosen_index == self.correct_option_index

    def to_dict(self) -> dict[str, any]:
        return {
            'id': self.id,
            'question_text': self.question_text,
            'options': self.options,
            'correct_option_index': self.correct_option_index
        }

    def to_player_dict(self) -> dict[str, any]:
        return {
            'id': self.id,
            'question_text': self.question_text,
            'options': self.options
        }

class QuizAttempt:
    def __init__(self, player_name: str, questions: list[Question]):
        if not questions:
            raise ValueError("A quiz attempt must have at least one question.")

        self.attempt_id = str(uuid.uuid4())
        self.player_name = player_name
        self._questions_for_attempt = list(questions) # Store a copy
        self.answers_given: list[int | None] = [None] * len(questions)
        self.correct_answers_count = 0
        self.current_question_idx = 0
        self.is_completed = False
        self.start_time = datetime.now()
        self.end_time: datetime | None = None
        self.question_results: list[dict[str, any]] = []

    def get_current_question_for_player(self) -> dict[str, any] | None:
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

    def get_summary(self) -> dict[str, any]:
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

    def get_score_history_entry(self) -> dict[str, any]:
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
        self._questions: dict[str, Question] = {}
        self._active_quizzes: dict[str, QuizAttempt] = {}
        self._player_scores_history: dict[str, list[QuizAttempt]] = {}

    # Admin Functions

    def add_question(self, question_text: str, options: list[str], correct_option_index: int) -> str:
        new_question = Question(question_text, options, correct_option_index)
        self._questions[new_question.id] = new_question
        return new_question.id

    def get_all_questions(self) -> list[dict[str, any]]:
        return [q.to_dict() for q in self._questions.values()]

    def delete_question(self, question_id: str) -> bool:
        if question_id in self._questions:
            del self._questions[question_id]
            return True
        return False

    # Player Functions

    def start_quiz(self, player_name: str, num_questions: int | None = None) -> dict[str, any] | None:
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


    def get_current_quiz_state(self, player_name: str) -> dict[str, any] | None:
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

    def get_next_question_for_player(self, player_name: str) -> dict[str, any] | None:
        active_attempt = self._active_quizzes.get(player_name)
        if not active_attempt:
            return None # No active quiz or quiz ended

        next_q_data = active_attempt.get_current_question_for_player()
        if next_q_data:
            next_q_data['attempt_id'] = active_attempt.attempt_id
        return next_q_data

    def end_quiz(self, player_name: str) -> dict[str, any] | None:
        active_attempt = self._active_quizzes.get(player_name)
        if not active_attempt:
            return None

        # The get_summary method of QuizAttempt handles marking it as completed and setting end_time
        summary = active_attempt.get_summary()

        self._player_scores_history.setdefault(player_name, []).append(active_attempt)
        del self._active_quizzes[player_name]
        return summary

    def get_player_score_history(self, player_name: str) -> list[dict[str, any]]:
        history = self._player_scores_history.get(player_name, [])
        # Call get_score_history_entry on each attempt to ensure consistent data and handling of completion status
        return [attempt.get_score_history_entry() for attempt in history]

    def get_player_last_attempt_details(self, player_name: str, attempt_id: str) -> dict[str, any] | None:
        history = self._player_scores_history.get(player_name, [])
        for attempt in history:
            if attempt.attempt_id == attempt_id:
                # Call get_summary on the specific attempt to ensure consistent data and handling of completion status
                return attempt.get_summary()
        return None



class TestQuestion(unittest.TestCase):
    @patch('uuid.uuid4', return_value=uuid.UUID('12345678-1234-5678-1234-567812345678'))
    def test_question_initialization(self, mock_uuid):
        q = Question("What is 2+2?", ["3", "4", "5"], 1)
        self.assertEqual(q.question_text, "What is 2+2?")
        self.assertEqual(q.options, ["3", "4", "5"])
        self.assertEqual(q.correct_option_index, 1)
        self.assertEqual(q.id, '12345678-1234-5678-1234-567812345678')
        mock_uuid.assert_called_once()

        # Test options list is copied
        original_options = ["A", "B"]
        q2 = Question("Which one?", original_options, 0)
        original_options.append("C")
        self.assertEqual(q2.options, ["A", "B"])

    def test_question_invalid_correct_option_index(self):
        with self.assertRaisesRegex(ValueError, "correct_option_index is out of bounds"):
            Question("What is 2+2?", ["3", "4", "5"], 3)
        with self.assertRaisesRegex(ValueError, "correct_option_index is out of bounds"):
            Question("What is 2+2?", ["3", "4", "5"], -1)
        with self.assertRaisesRegex(ValueError, "correct_option_index is out of bounds"):
            Question("What is 2+2?", [], 0) # Empty options

    def test_is_correct(self):
        q = Question("What is the capital of France?", ["Berlin", "Madrid", "Paris"], 2)
        self.assertFalse(q.is_correct(0))
        self.assertFalse(q.is_correct(1))
        self.assertTrue(q.is_correct(2))
        self.assertFalse(q.is_correct(99)) # Out of bounds, but still just incorrect

    @patch('uuid.uuid4', return_value=uuid.UUID('test-id-1'))
    def test_to_dict(self, mock_uuid):
        q = Question("Who painted the Mona Lisa?", ["Van Gogh", "Da Vinci"], 1)
        expected_dict = {
            'id': 'test-id-1',
            'question_text': "Who painted the Mona Lisa?",
            'options': ["Van Gogh", "Da Vinci"],
            'correct_option_index': 1
        }
        self.assertEqual(q.to_dict(), expected_dict)

    @patch('uuid.uuid4', return_value=uuid.UUID('test-id-2'))
    def test_to_player_dict(self, mock_uuid):
        q = Question("What is the largest ocean?", ["Atlantic", "Pacific", "Indian"], 1)
        expected_dict = {
            'id': 'test-id-2',
            'question_text': "What is the largest ocean?",
            'options': ["Atlantic", "Pacific", "Indian"]
        }
        self.assertEqual(q.to_player_dict(), expected_dict)


class TestQuizAttempt(unittest.TestCase):
    def setUp(self):
        self.q1 = Question("Q1 text", ["O1a", "O1b"], 0)
        self.q2 = Question("Q2 text", ["O2a", "O2b"], 1)
        self.q3 = Question("Q3 text", ["O3a", "O3b"], 0)
        self.questions = [self.q1, self.q2, self.q3]
        self.player_name = "TestPlayer"
        self.mock_start_time = datetime(2023, 1, 1, 10, 0, 0)
        self.mock_end_time = datetime(2023, 1, 1, 10, 5, 0)

    def test_quiz_attempt_initialization_success(self):
        with patch('uuid.uuid4', return_value=uuid.UUID('attempt-1-id')), \
             patch('datetime.now', return_value=self.mock_start_time):
            attempt = QuizAttempt(self.player_name, self.questions)

            self.assertEqual(attempt.attempt_id, 'attempt-1-id')
            self.assertEqual(attempt.player_name, self.player_name)
            self.assertEqual(attempt._questions_for_attempt, self.questions)
            self.assertEqual(attempt.answers_given, [None, None, None])
            self.assertEqual(attempt.correct_answers_count, 0)
            self.assertEqual(attempt.current_question_idx, 0)
            self.assertFalse(attempt.is_completed)
            self.assertEqual(attempt.start_time, self.mock_start_time)
            self.assertIsNone(attempt.end_time)
            self.assertEqual(attempt.question_results, [])

            # Ensure questions list is copied
            original_questions_list = [self.q1]
            attempt2 = QuizAttempt("Player2", original_questions_list)
            original_questions_list.append(self.q2)
            self.assertEqual(attempt2._questions_for_attempt, [self.q1])

    def test_quiz_attempt_initialization_no_questions(self):
        with self.assertRaisesRegex(ValueError, "A quiz attempt must have at least one question."):
            QuizAttempt(self.player_name, [])

    def test_get_current_question_for_player(self):
        with patch('uuid.uuid4', return_value=uuid.UUID('attempt-1-id')), \
             patch('datetime.now', return_value=self.mock_start_time):
            attempt = QuizAttempt(self.player_name, self.questions)

            # First question
            current_q = attempt.get_current_question_for_player()
            self.assertIsNotNone(current_q)
            self.assertEqual(current_q['id'], self.q1.id)
            self.assertEqual(current_q['question_text'], self.q1.question_text)
            self.assertEqual(current_q['options'], self.q1.options)
            self.assertEqual(current_q['attempt_id'], 'attempt-1-id')
            self.assertNotIn('correct_option_index', current_q)

            # After submitting an answer, next question should be Q2
            attempt.current_question_idx = 1
            current_q = attempt.get_current_question_for_player()
            self.assertIsNotNone(current_q)
            self.assertEqual(current_q['id'], self.q2.id)

            # After all questions
            attempt.current_question_idx = len(self.questions)
            self.assertIsNone(attempt.get_current_question_for_player())

            # When quiz is completed
            attempt.is_completed = True
            attempt.current_question_idx = 0 # Reset index, but completed flag should prevent
            self.assertIsNone(attempt.get_current_question_for_player())


    @patch('datetime.now', side_effect=[datetime(2023, 1, 1, 10, 0, 0), datetime(2023, 1, 1, 10, 1, 0),
                                        datetime(2023, 1, 1, 10, 2, 0), datetime(2023, 1, 1, 10, 3, 0)])
    def test_submit_answer(self, mock_datetime_now):
        attempt = QuizAttempt(self.player_name, self.questions) # mock_datetime_now used for start_time

        # Submit correct answer for Q1
        is_correct = attempt.submit_answer(self.q1.id, 0)
        self.assertTrue(is_correct)
        self.assertEqual(attempt.answers_given[0], 0)
        self.assertEqual(attempt.correct_answers_count, 1)
        self.assertEqual(attempt.current_question_idx, 1)
        self.assertFalse(attempt.is_completed)
        self.assertEqual(len(attempt.question_results), 1)
        self.assertTrue(attempt.question_results[0]['is_correct'])

        # Submit incorrect answer for Q2
        is_correct = attempt.submit_answer(self.q2.id, 0) # Q2 correct is 1
        self.assertFalse(is_correct)
        self.assertEqual(attempt.answers_given[1], 0)
        self.assertEqual(attempt.correct_answers_count, 1) # Still 1
        self.assertEqual(attempt.current_question_idx, 2)
        self.assertFalse(attempt.is_completed)
        self.assertEqual(len(attempt.question_results), 2)
        self.assertFalse(attempt.question_results[1]['is_correct'])

        # Submit correct answer for Q3 (last question)
        is_correct = attempt.submit_answer(self.q3.id, 0)
        self.assertTrue(is_correct)
        self.assertEqual(attempt.answers_given[2], 0)
        self.assertEqual(attempt.correct_answers_count, 2)
        self.assertEqual(attempt.current_question_idx, 3)
        self.assertTrue(attempt.is_completed)
        self.assertEqual(attempt.end_time, datetime(2023, 1, 1, 10, 3, 0)) # End time set
        self.assertEqual(len(attempt.question_results), 3)
        self.assertTrue(attempt.question_results[2]['is_correct'])

    def test_submit_answer_errors(self):
        attempt = QuizAttempt(self.player_name, [self.q1])

        # Test question ID mismatch
        with self.assertRaisesRegex(ValueError, f"Question ID mismatch. Expected {self.q1.id}, got .*"):
            attempt.submit_answer(self.q2.id, 0)

        # Test chosen option index out of bounds
        with self.assertRaisesRegex(ValueError, "Chosen option index .* is out of bounds"):
            attempt.submit_answer(self.q1.id, 5)
        with self.assertRaisesRegex(ValueError, "Chosen option index .* is out of bounds"):
            attempt.submit_answer(self.q1.id, -1)

        # Test quiz already completed
        attempt.submit_answer(self.q1.id, 0) # Complete the quiz
        self.assertTrue(attempt.is_completed)
        with self.assertRaisesRegex(ValueError, "Quiz is already completed."):
            attempt.submit_answer(self.q1.id, 0)

        # Test no more questions
        attempt_no_more = QuizAttempt(self.player_name, [self.q1])
        attempt_no_more.current_question_idx = 1 # Manually advance past last question
        with self.assertRaisesRegex(ValueError, "No more questions in this quiz."):
            attempt_no_more.submit_answer(self.q1.id, 0) # ID mismatch would happen first if it was not q1.id

    @patch('datetime.now', side_effect=[datetime(2023, 1, 1, 10, 0, 0), datetime(2023, 1, 1, 10, 5, 0)])
    def test_get_summary_completed(self, mock_datetime_now):
        attempt = QuizAttempt(self.player_name, [self.q1])
        attempt.submit_answer(self.q1.id, 0) # Complete the quiz, sets end_time and is_completed

        summary = attempt.get_summary()
        self.assertEqual(summary['attempt_id'], attempt.attempt_id)
        self.assertEqual(summary['player_name'], self.player_name)
        self.assertEqual(summary['score'], 1)
        self.assertEqual(summary['total_questions'], 1)
        self.assertEqual(summary['start_time'], self.mock_start_time.isoformat())
        self.assertEqual(summary['end_time'], self.mock_end_time.isoformat())
        self.assertTrue(summary['is_completed'])
        self.assertIsInstance(summary['details'], list)
        self.assertEqual(len(summary['details']), 1)
        self.assertTrue(summary['details'][0]['is_correct'])

    @patch('datetime.now', side_effect=[datetime(2023, 1, 1, 10, 0, 0), datetime(2023, 1, 1, 10, 6, 0)])
    def test_get_summary_not_completed_prematurely(self, mock_datetime_now):
        attempt = QuizAttempt(self.player_name, self.questions) # Only start_time set by mock
        attempt.submit_answer(self.q1.id, 0) # Answer one question, not completed

        summary = attempt.get_summary() # Call summary before completion
        self.assertTrue(attempt.is_completed) # Should be marked completed by get_summary
        self.assertEqual(attempt.end_time, datetime(2023, 1, 1, 10, 6, 0)) # end_time should be set

        self.assertEqual(summary['score'], 1)
        self.assertEqual(summary['total_questions'], 3)
        self.assertEqual(summary['end_time'], datetime(2023, 1, 1, 10, 6, 0).isoformat())
        self.assertTrue(summary['is_completed'])
        self.assertEqual(len(summary['details']), 1)

    @patch('datetime.now', side_effect=[datetime(2023, 1, 1, 10, 0, 0), datetime(2023, 1, 1, 10, 7, 0)])
    def test_get_score_history_entry(self, mock_datetime_now):
        attempt = QuizAttempt(self.player_name, [self.q1, self.q2])
        attempt.submit_answer(self.q1.id, 0) # Correct
        attempt.submit_answer(self.q2.id, 0) # Incorrect, completes quiz

        history_entry = attempt.get_score_history_entry()
        self.assertTrue(attempt.is_completed)
        self.assertEqual(attempt.end_time, datetime(2023, 1, 1, 10, 7, 0))

        self.assertEqual(history_entry['attempt_id'], attempt.attempt_id)
        self.assertEqual(history_entry['score'], 1)
        self.assertEqual(history_entry['total_questions'], 2)
        self.assertEqual(history_entry['start_time'], self.mock_start_time.isoformat())
        self.assertEqual(history_entry['end_time'], datetime(2023, 1, 1, 10, 7, 0).isoformat())
        self.assertTrue(history_entry['is_completed'])
        self.assertNotIn('details', history_entry)

    @patch('datetime.now', side_effect=[datetime(2023, 1, 1, 10, 0, 0), datetime(2023, 1, 1, 10, 8, 0)])
    def test_get_score_history_entry_not_completed_prematurely(self, mock_datetime_now):
        attempt = QuizAttempt(self.player_name, self.questions) # Only start_time set by mock
        attempt.submit_answer(self.q1.id, 0) # Answer one question, not completed

        history_entry = attempt.get_score_history_entry()
        self.assertTrue(attempt.is_completed) # Should be marked completed by get_score_history_entry
        self.assertEqual(attempt.end_time, datetime(2023, 1, 1, 10, 8, 0)) # end_time should be set

        self.assertEqual(history_entry['score'], 1)
        self.assertEqual(history_entry['total_questions'], 3)
        self.assertEqual(history_entry['end_time'], datetime(2023, 1, 1, 10, 8, 0).isoformat())
        self.assertTrue(history_entry['is_completed'])


class TestQuiz(unittest.TestCase):
    def setUp(self):
        self.quiz = Quiz()
        self.player1 = "Alice"
        self.player2 = "Bob"
        self.mock_uuid_counter = 0

    def mock_uuid_side_effect(self):
        self.mock_uuid_counter += 1
        return uuid.UUID(int=self.mock_uuid_counter)

    # Admin Functions Tests
    @patch('uuid.uuid4', side_effect=lambda: uuid.UUID(int=random.randint(0, 10000)))
    def test_add_question(self, mock_uuid):
        q_id1 = self.quiz.add_question("Q1", ["A", "B"], 0)
        self.assertIsNotNone(q_id1)
        self.assertIn(q_id1, self.quiz._questions)
        self.assertEqual(self.quiz._questions[q_id1].question_text, "Q1")

        q_id2 = self.quiz.add_question("Q2", ["C", "D"], 1)
        self.assertIsNotNone(q_id2)
        self.assertIn(q_id2, self.quiz._questions)
        self.assertEqual(self.quiz._questions[q_id2].question_text, "Q2")
        self.assertNotEqual(q_id1, q_id2)

    @patch('uuid.uuid4', side_effect=lambda: uuid.UUID(int=random.randint(0, 10000)))
    def test_get_all_questions(self, mock_uuid):
        self.assertEqual(self.quiz.get_all_questions(), [])

        q_id1 = self.quiz.add_question("Q1", ["A", "B"], 0)
        q_id2 = self.quiz.add_question("Q2", ["C", "D"], 1)

        all_questions = self.quiz.get_all_questions()
        self.assertEqual(len(all_questions), 2)
        q_texts = {q['question_text'] for q in all_questions}
        self.assertIn("Q1", q_texts)
        self.assertIn("Q2", q_texts)

        # Check structure
        q1_dict = next(q for q in all_questions if q['id'] == q_id1)
        self.assertEqual(q1_dict['options'], ["A", "B"])
        self.assertEqual(q1_dict['correct_option_index'], 0)
        self.assertIn('id', q1_dict)

    @patch('uuid.uuid4', side_effect=lambda: uuid.UUID(int=random.randint(0, 10000)))
    def test_delete_question(self, mock_uuid):
        q_id1 = self.quiz.add_question("Q1", ["A", "B"], 0)
        q_id2 = self.quiz.add_question("Q2", ["C", "D"], 1)

        self.assertTrue(self.quiz.delete_question(q_id1))
        self.assertNotIn(q_id1, self.quiz._questions)
        self.assertEqual(len(self.quiz._questions), 1)

        self.assertFalse(self.quiz.delete_question("non-existent-id"))
        self.assertFalse(self.quiz.delete_question(q_id1)) # Already deleted

        self.assertTrue(self.quiz.delete_question(q_id2))
        self.assertEqual(len(self.quiz._questions), 0)


    # Player Functions Tests
    @patch('random.shuffle')
    @patch('datetime.now', return_value=datetime(2023, 1, 1, 10, 0, 0))
    @patch('uuid.uuid4', side_effect=MagicMock(side_effect=lambda: uuid.UUID(int=random.randint(0, 1000000))))
    def test_start_quiz(self, mock_uuid, mock_datetime_now, mock_shuffle):
        # No questions available
        self.assertIsNone(self.quiz.start_quiz(self.player1))

        q_id1 = self.quiz.add_question("Q1", ["A", "B"], 0)
        q_id2 = self.quiz.add_question("Q2", ["C", "D"], 1)
        q_id3 = self.quiz.add_question("Q3", ["E", "F"], 0)

        # Ensure shuffle is called
        mock_shuffle.reset_mock() # Reset after add_question might call it internally for other reasons (not here)
        first_q_data = self.quiz.start_quiz(self.player1)

        self.assertIsNotNone(first_q_data)
        self.assertIn(self.player1, self.quiz._active_quizzes)
        self.assertIn('id', first_q_data)
        self.assertIn('question_text', first_q_data)
        self.assertIn('options', first_q_data)
        self.assertIn('attempt_id', first_q_data)
        self.assertNotIn('correct_option_index', first_q_data)
        mock_shuffle.assert_called_once()
        self.assertEqual(len(self.quiz._active_quizzes[self.player1]._questions_for_attempt), 3)

        # Test num_questions
        self.quiz._active_quizzes.clear() # Clear active quiz for next test run
        mock_shuffle.reset_mock()
        first_q_data_limited = self.quiz.start_quiz(self.player2, num_questions=2)
        self.assertIsNotNone(first_q_data_limited)
        self.assertIn(self.player2, self.quiz._active_quizzes)
        self.assertEqual(len(self.quiz._active_quizzes[self.player2]._questions_for_attempt), 2)
        mock_shuffle.assert_called_once() # Still called, but takes slice

        # Test starting a new quiz for an existing player (should end the old one)
        self.quiz._player_scores_history.clear()
        _ = self.quiz.start_quiz(self.player1, num_questions=1) # First quiz for Alice
        old_attempt_id = self.quiz._active_quizzes[self.player1].attempt_id
        self.assertEqual(len(self.quiz._player_scores_history.get(self.player1, [])), 0)

        # Start a second quiz for Alice
        second_q_data = self.quiz.start_quiz(self.player1, num_questions=1)
        new_attempt_id = self.quiz._active_quizzes[self.player1].attempt_id
        self.assertNotEqual(old_attempt_id, new_attempt_id)
        self.assertEqual(len(self.quiz._player_scores_history[self.player1]), 1)
        self.assertEqual(self.quiz._player_scores_history[self.player1][0].attempt_id, old_attempt_id)
        self.assertTrue(self.quiz._player_scores_history[self.player1][0].is_completed)


    @patch('random.shuffle')
    @patch('datetime.now', return_value=datetime(2023, 1, 1, 10, 0, 0))
    @patch('uuid.uuid4', side_effect=MagicMock(side_effect=lambda: uuid.UUID(int=random.randint(0, 1000000))))
    def test_get_current_quiz_state(self, mock_uuid, mock_datetime_now, mock_shuffle):
        self.assertIsNone(self.quiz.get_current_quiz_state(self.player1))

        q_id1 = self.quiz.add_question("Q1", ["A", "B"], 0)
        _ = self.quiz.start_quiz(self.player1)
        active_attempt = self.quiz._active_quizzes[self.player1]

        state = self.quiz.get_current_quiz_state(self.player1)
        self.assertIsNotNone(state)
        self.assertEqual(state['id'], active_attempt._questions_for_attempt[0].id)
        self.assertEqual(state['attempt_id'], active_attempt.attempt_id)

        # After quiz completion
        self.quiz.submit_answer(self.player1, active_attempt._questions_for_attempt[0].id, 0)
        self.assertIsNone(self.quiz.get_current_quiz_state(self.player1))


    @patch('random.shuffle')
    @patch('datetime.now', return_value=datetime(2023, 1, 1, 10, 0, 0))
    @patch('uuid.uuid4', side_effect=MagicMock(side_effect=lambda: uuid.UUID(int=random.randint(0, 1000000))))
    def test_submit_answer_quiz_flow(self, mock_uuid, mock_datetime_now, mock_shuffle):
        q_id1 = self.quiz.add_question("Q1", ["A", "B"], 0)
        q_id2 = self.quiz.add_question("Q2", ["C", "D"], 1)
        q_id3 = self.quiz.add_question("Q3", ["E", "F"], 0)

        # Mock shuffle to return questions in a known order for testing
        mock_shuffle.side_effect = lambda x: None # Don't shuffle for this test

        first_q_data = self.quiz.start_quiz(self.player1)
        active_attempt = self.quiz._active_quizzes[self.player1]

        # Ensure selected questions are as expected for deterministic testing
        self.assertEqual(active_attempt._questions_for_attempt[0].id, q_id1)
        self.assertEqual(active_attempt._questions_for_attempt[1].id, q_id2)
        self.assertEqual(active_attempt._questions_for_attempt[2].id, q_id3)

        # Submit answer for Q1 (correct)
        is_correct = self.quiz.submit_answer(self.player1, q_id1, 0)
        self.assertTrue(is_correct)
        self.assertEqual(active_attempt.correct_answers_count, 1)
        self.assertEqual(active_attempt.current_question_idx, 1)
        self.assertFalse(active_attempt.is_completed)
        self.assertIn(self.player1, self.quiz._active_quizzes)
        self.assertEqual(len(self.quiz._player_scores_history.get(self.player1, [])), 0)

        # Submit answer for Q2 (incorrect)
        is_correct = self.quiz.submit_answer(self.player1, q_id2, 0)
        self.assertFalse(is_correct)
        self.assertEqual(active_attempt.correct_answers_count, 1)
        self.assertEqual(active_attempt.current_question_idx, 2)
        self.assertFalse(active_attempt.is_completed)

        # Submit answer for Q3 (correct, last question)
        is_correct = self.quiz.submit_answer(self.player1, q_id3, 0)
        self.assertTrue(is_correct)
        self.assertEqual(active_attempt.correct_answers_count, 2)
        self.assertEqual(active_attempt.current_question_idx, 3)
        self.assertTrue(active_attempt.is_completed)
        self.assertNotIn(self.player1, self.quiz._active_quizzes) # Quiz moved to history
        self.assertEqual(len(self.quiz._player_scores_history[self.player1]), 1)
        self.assertEqual(self.quiz._player_scores_history[self.player1][0].attempt_id, active_attempt.attempt_id)
        self.assertEqual(self.quiz._player_scores_history[self.player1][0].correct_answers_count, 2)

    def test_submit_answer_no_active_quiz(self):
        self.quiz.add_question("Q1", ["A", "B"], 0)
        with self.assertRaisesRegex(ValueError, "No active quiz for player 'Alice'."):
            self.quiz.submit_answer(self.player1, "some_id", 0)

    @patch('random.shuffle')
    @patch('datetime.now', return_value=datetime(2023, 1, 1, 10, 0, 0))
    @patch('uuid.uuid4', side_effect=MagicMock(side_effect=lambda: uuid.UUID(int=random.randint(0, 1000000))))
    def test_get_next_question_for_player(self, mock_uuid, mock_datetime_now, mock_shuffle):
        self.assertIsNone(self.quiz.get_next_question_for_player(self.player1))

        q_id1 = self.quiz.add_question("Q1", ["A", "B"], 0)
        q_id2 = self.quiz.add_question("Q2", ["C", "D"], 1)

        mock_shuffle.side_effect = lambda x: x.sort(key=lambda q: q.question_text) # For deterministic order
        _ = self.quiz.start_quiz(self.player1)
        active_attempt = self.quiz._active_quizzes[self.player1]

        self.assertEqual(active_attempt._questions_for_attempt[0].id, q_id1) # Q1
        self.assertEqual(active_attempt._questions_for_attempt[1].id, q_id2) # Q2

        # First call should give current (first) question for a fresh start, not next
        # The logic is that get_current_quiz_state gives current, get_next_question_for_player advances and then gets current
        # Let's manually advance to simulate a flow, as get_next_question_for_player simply calls get_current_question_for_player
        # The internal current_question_idx is advanced by submit_answer
        current_q_data = self.quiz.get_current_quiz_state(self.player1)
        self.assertEqual(current_q_data['id'], q_id1)

        # Submit Q1 to move to Q2
        self.quiz.submit_answer(self.player1, q_id1, 0)
        next_q_data = self.quiz.get_next_question_for_player(self.player1)
        self.assertIsNotNone(next_q_data)
        self.assertEqual(next_q_data['id'], q_id2)
        self.assertEqual(next_q_data['attempt_id'], active_attempt.attempt_id)

        # Submit Q2 (last question)
        self.quiz.submit_answer(self.player1, q_id2, 1)
        self.assertIsNone(self.quiz.get_next_question_for_player(self.player1)) # No more questions, quiz ended


    @patch('random.shuffle')
    @patch('datetime.now', side_effect=[datetime(2023, 1, 1, 10, 0, 0), datetime(2023, 1, 1, 10, 10, 0)])
    @patch('uuid.uuid4', side_effect=MagicMock(side_effect=lambda: uuid.UUID(int=random.randint(0, 1000000))))
    def test_end_quiz(self, mock_uuid, mock_datetime_now, mock_shuffle):
        self.assertIsNone(self.quiz.end_quiz(self.player1)) # No active quiz

        q_id1 = self.quiz.add_question("Q1", ["A", "B"], 0)
        self.quiz.add_question("Q2", ["C", "D"], 1)

        mock_shuffle.side_effect = lambda x: x # No shuffling for predictability
        _ = self.quiz.start_quiz(self.player1)
        active_attempt_id = self.quiz._active_quizzes[self.player1].attempt_id
        self.quiz.submit_answer(self.player1, q_id1, 0) # Answer one question

        summary = self.quiz.end_quiz(self.player1)
        self.assertIsNotNone(summary)
        self.assertNotIn(self.player1, self.quiz._active_quizzes) # Should be moved
        self.assertIn(self.player1, self.quiz._player_scores_history)
        self.assertEqual(len(self.quiz._player_scores_history[self.player1]), 1)
        self.assertEqual(self.quiz._player_scores_history[self.player1][0].attempt_id, active_attempt_id)
        self.assertTrue(self.quiz._player_scores_history[self.player1][0].is_completed)
        self.assertEqual(summary['score'], 1)
        self.assertEqual(summary['total_questions'], 2)
        self.assertEqual(summary['end_time'], datetime(2023, 1, 1, 10, 10, 0).isoformat()) # End time set by end_quiz


    @patch('random.shuffle')
    @patch('datetime.now', side_effect=[datetime(2023, 1, 1, 10, 0, 0), datetime(2023, 1, 1, 10, 1, 0),
                                        datetime(2023, 1, 1, 10, 5, 0), datetime(2023, 1, 1, 10, 6, 0)])
    @patch('uuid.uuid4', side_effect=MagicMock(side_effect=[
        uuid.UUID('q1-id'), uuid.UUID('q2-id'), uuid.UUID('att1-id'), uuid.UUID('att2-id')
    ]))
    def test_get_player_score_history(self, mock_uuid, mock_datetime_now, mock_shuffle):
        self.assertEqual(self.quiz.get_player_score_history(self.player1), [])

        q1 = Question("Q1", ["A", "B"], 0)
        q2 = Question("Q2", ["C", "D"], 1)
        self.quiz._questions = {q1.id: q1, q2.id: q2}
        mock_shuffle.side_effect = lambda x: x.sort(key=lambda q: q.question_text) # for deterministic order

        # First attempt (completed manually)
        att1_start_time = datetime(2023, 1, 1, 10, 0, 0)
        att1_end_time = datetime(2023, 1, 1, 10, 1, 0)
        mock_datetime_now.side_effect = [att1_start_time, att1_end_time]
        first_q_data = self.quiz.start_quiz(self.player1)
        att1_id = first_q_data['attempt_id']
        self.quiz.submit_answer(self.player1, q1.id, 0) # Correct
        self.quiz.submit_answer(self.player1, q2.id, 0) # Incorrect, completes quiz

        history = self.quiz.get_player_score_history(self.player1)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['attempt_id'], att1_id)
        self.assertEqual(history[0]['score'], 1)
        self.assertEqual(history[0]['total_questions'], 2)
        self.assertTrue(history[0]['is_completed'])
        self.assertEqual(history[0]['start_time'], att1_start_time.isoformat())
        self.assertEqual(history[0]['end_time'], att1_end_time.isoformat())
        self.assertNotIn('details', history[0])

        # Second attempt (ended prematurely)
        att2_start_time = datetime(2023, 1, 1, 10, 5, 0)
        att2_end_time = datetime(2023, 1, 1, 10, 6, 0)
        mock_datetime_now.side_effect = [att2_start_time, att2_end_time] # start for QuizAttempt, then end for get_summary/end_quiz
        _ = self.quiz.start_quiz(self.player1) # Starts a new quiz, first quiz is now history
        att2_id = self.quiz._active_quizzes[self.player1].attempt_id
        self.quiz.submit_answer(self.player1, q1.id, 0) # Answer one question
        self.quiz.end_quiz(self.player1) # End prematurely

        history = self.quiz.get_player_score_history(self.player1)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]['attempt_id'], att2_id)
        self.assertEqual(history[1]['score'], 1)
        self.assertEqual(history[1]['total_questions'], 2)
        self.assertTrue(history[1]['is_completed'])
        self.assertEqual(history[1]['start_time'], att2_start_time.isoformat())
        self.assertEqual(history[1]['end_time'], att2_end_time.isoformat())

    @patch('random.shuffle')
    @patch('datetime.now', side_effect=[datetime(2023, 1, 1, 10, 0, 0), datetime(2023, 1, 1, 10, 1, 0),
                                        datetime(2023, 1, 1, 10, 5, 0), datetime(2023, 1, 1, 10, 6, 0)])
    @patch('uuid.uuid4', side_effect=MagicMock(side_effect=[
        uuid.UUID('q1-id'), uuid.UUID('q2-id'), uuid.UUID('att1-id'), uuid.UUID('att2-id')
    ]))
    def test_get_player_last_attempt_details(self, mock_uuid, mock_datetime_now, mock_shuffle):
        self.assertIsNone(self.quiz.get_player_last_attempt_details(self.player1, "non-existent-id"))

        q1 = Question("Q1", ["A", "B"], 0)
        q2 = Question("Q2", ["C", "D"], 1)
        self.quiz._questions = {q1.id: q1, q2.id: q2}
        mock_shuffle.side_effect = lambda x: x.sort(key=lambda q: q.question_text) # for deterministic order

        # First attempt
        att1_start_time = datetime(2023, 1, 1, 10, 0, 0)
        att1_end_time = datetime(2023, 1, 1, 10, 1, 0)
        mock_datetime_now.side_effect = [att1_start_time, att1_end_time]
        first_q_data = self.quiz.start_quiz(self.player1)
        att1_id = first_q_data['attempt_id']
        self.quiz.submit_answer(self.player1, q1.id, 0) # Correct
        self.quiz.submit_answer(self.player1, q2.id, 0) # Incorrect, completes quiz

        # Second attempt
        att2_start_time = datetime(2023, 1, 1, 10, 5, 0)
        att2_end_time = datetime(2023, 1, 1, 10, 6, 0)
        mock_datetime_now.side_effect = [att2_start_time, att2_end_time]
        _ = self.quiz.start_quiz(self.player1)
        att2_id = self.quiz._active_quizzes[self.player1].attempt_id
        self.quiz.submit_answer(self.player1, q1.id, 0) # Correct
        self.quiz.end_quiz(self.player1)

        # Get details for first attempt
        details1 = self.quiz.get_player_last_attempt_details(self.player1, att1_id)
        self.assertIsNotNone(details1)
        self.assertEqual(details1['attempt_id'], att1_id)
        self.assertEqual(details1['score'], 1)
        self.assertEqual(details1['total_questions'], 2)
        self.assertTrue(details1['is_completed'])
        self.assertEqual(len(details1['details']), 2)
        self.assertTrue(details1['details'][0]['is_correct'])
        self.assertFalse(details1['details'][1]['is_correct'])

        # Get details for second attempt
        details2 = self.quiz.get_player_last_attempt_details(self.player1, att2_id)
        self.assertIsNotNone(details2)
        self.assertEqual(details2['attempt_id'], att2_id)
        self.assertEqual(details2['score'], 1)
        self.assertEqual(details2['total_questions'], 2)
        self.assertTrue(details2['is_completed'])
        self.assertEqual(len(details2['details']), 1) # Only 1 question was answered before ending
        self.assertTrue(details2['details'][0]['is_correct'])

        self.assertIsNone(self.quiz.get_player_last_attempt_details(self.player1, str(uuid.uuid4()))) # Non-existent ID


if __name__ == '__main__':
    unittest.main()