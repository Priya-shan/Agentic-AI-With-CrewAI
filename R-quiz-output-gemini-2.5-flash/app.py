import gradio as gr
from quiz import Quiz # Assuming quiz.py is in the same directory

# Initialize the Quiz backend
quiz_engine = Quiz()
# For demonstration purposes, let's pre-populate some questions
# We'll use a single "player" for this simple UI: "Player1"
PLAYER_NAME = "Player1"

# --- Backend Helper Functions for Gradio UI ---

def admin_add_question(question_text, option1, option2, option3, option4, correct_option_index_str):
    try:
        options = [option1, option2, option3, option4]
        # Filter out empty options to allow fewer than 4 if needed, but ensure at least 2 for a valid quiz
        valid_options = [opt for opt in options if opt.strip()]
        if len(valid_options) < 2:
            return "Error: A question must have at least two non-empty options.", None

        correct_option_index = int(correct_option_index_str) - 1 # Convert 1-based index to 0-based
        if not (0 <= correct_option_index < len(valid_options)):
            return "Error: Correct option index is out of bounds for the provided options.", None

        # Re-map the correct index if we filtered options
        original_options_map = {}
        idx = 0
        for i, opt in enumerate(options):
            if opt.strip():
                original_options_map[idx] = i # original index from input
                idx += 1
        
        # Find the correct option index within the `valid_options` list
        # This is a bit tricky if options are sparse; simpler to just use the original list for indexing
        # and rely on the backend validation. Let's assume 4 options for simplicity of UI.
        # If we truly want dynamic number of options, the UI would need to be more complex.
        # For a simple demo, assuming 4 input fields are always used.
        
        # Let's stick to the original assumption that `options` list for `Question` is exactly what the user inputs.
        # This means if option4 is empty, it's still part of the list, and validation for `correct_option_index`
        # should happen based on the length of `options` as provided.
        # However, the backend `Question` class expects options to be valid.
        
        # To simplify, let's assume all 4 options are always provided for this UI.
        # If any are empty, the backend Question constructor would still take them.
        # Let's ensure non-empty options for a better user experience.
        final_options = [opt for opt in options if opt.strip()]
        if len(final_options) != 4:
             return "Please provide text for all four options.", None

        # Recheck correct_option_index after filtering to valid options
        # A more robust way would be to align the UI's 1-based index with the filtered list
        # For simplicity, let's just make sure the selected index matches an actual non-empty option
        if not (0 <= correct_option_index < len(final_options)):
             return "Error: Correct option index must be between 1 and 4.", None
             
        question_id = quiz_engine.add_question(question_text, final_options, correct_option_index)
        all_questions = quiz_engine.get_all_questions()
        questions_str = "\n".join([f"ID: {q['id']}, Q: {q['question_text']}, Options: {q['options']}, Correct: {q['correct_option_index']+1}" for q in all_questions])
        return f"Question added! ID: {question_id}\n\nCurrent Questions:\n{questions_str}", None
    except ValueError as e:
        return f"Error: {e}", None
    except Exception as e:
        return f"An unexpected error occurred: {e}", None

def admin_delete_question(question_id):
    success = quiz_engine.delete_question(question_id)
    if success:
        all_questions = quiz_engine.get_all_questions()
        questions_str = "\n".join([f"ID: {q['id']}, Q: {q['question_text']}, Options: {q['options']}, Correct: {q['correct_option_index']+1}" for q in all_questions])
        return f"Question ID {question_id} deleted.\n\nCurrent Questions:\n{questions_str}", None
    else:
        return f"Question ID {question_id} not found.", None

def get_all_questions_for_display():
    questions = quiz_engine.get_all_questions()
    if not questions:
        return "No questions created yet.", ""
    
    questions_str = "\n".join([f"ID: {q['id']}, Q: {q['question_text']}, Options: {q['options']}, Correct: {q['correct_option_index']+1}" for q in questions])
    return "All Questions (for Admin):\n" + questions_str, ""

def start_player_quiz(num_questions_str):
    try:
        num_questions = int(num_questions_str) if num_questions_str.strip() else None
    except ValueError:
        return "Please enter a valid number for questions, or leave blank for all.", None, None, None

    first_question = quiz_engine.start_quiz(PLAYER_NAME, num_questions)
    if first_question:
        gr.State(first_question['id']) # Store current question ID in state
        options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(first_question['options'])])
        return (f"Quiz Started for {PLAYER_NAME}!\n\nQuestion:\n{first_question['question_text']}\n\nOptions:\n{options_text}",
                first_question['id'], # For hidden question ID
                gr.update(choices=[str(i+1) for i in range(len(first_question['options']))], value=None, visible=True),
                gr.update(visible=True), # Show submit button
                gr.update(visible=True)) # Show end quiz button
    else:
        return "Could not start quiz. No questions available or other error.", None, None, None, None

def submit_player_answer(question_id_state, chosen_option_index_str):
    if not question_id_state:
        return "No active question to answer. Please start a quiz.", None, None, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

    try:
        chosen_option_index = int(chosen_option_index_str) - 1 # Convert 1-based index to 0-based
        is_correct = quiz_engine.submit_answer(PLAYER_NAME, question_id_state, chosen_option_index)

        feedback = "Correct!" if is_correct else "Incorrect."

        next_question_data = quiz_engine.get_next_question_for_player(PLAYER_NAME)

        if next_question_data:
            options_text = "\n".join([f"{i+1}. {opt}" for i, opt in enumerate(next_question_data['options'])])
            return (f"{feedback}\n\nNext Question:\n{next_question_data['question_text']}\n\nOptions:\n{options_text}",
                    next_question_data['id'],
                    gr.update(choices=[str(i+1) for i in range(len(next_question_data['options']))], value=None, visible=True),
                    gr.update(visible=True), gr.update(visible=True))
        else:
            # Quiz completed
            summary = quiz_engine.end_quiz(PLAYER_NAME)
            score_history = quiz_engine.get_player_score_history(PLAYER_NAME)
            history_str = "\n".join([f"Attempt {i+1}: Score {s['score']}/{s['total_questions']} on {s['end_time']}" for i, s in enumerate(score_history)])
            
            return (f"{feedback}\n\nQuiz Completed! Final Score: {summary['score']}/{summary['total_questions']}\n\n"
                    f"Player {PLAYER_NAME} Score History:\n{history_str}",
                    None,
                    gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))

    except ValueError as e:
        return f"Error: {e}", question_id_state, gr.update(value=None), gr.update(visible=True), gr.update(visible=True)
    except Exception as e:
        return f"An unexpected error occurred: {e}", question_id_state, gr.update(value=None), gr.update(visible=True), gr.update(visible=True)


def end_player_quiz():
    summary = quiz_engine.end_quiz(PLAYER_NAME)
    if summary:
        score_history = quiz_engine.get_player_score_history(PLAYER_NAME)
        history_str = "\n".join([f"Attempt {i+1}: Score {s['score']}/{s['total_questions']} on {s['end_time']}" for i, s in enumerate(score_history)])
        
        return (f"Quiz ended by player. Final Score: {summary['score']}/{summary['total_questions']}\n\n"
                f"Player {PLAYER_NAME} Score History:\n{history_str}",
                None,
                gr.update(visible=False), gr.update(visible=False), gr.update(visible=False))
    else:
        return "No active quiz to end.", None, gr.update(visible=False), gr.update(visible=False), gr.update(visible=False)

def get_player_history():
    history = quiz_engine.get_player_score_history(PLAYER_NAME)
    if not history:
        return f"No score history for {PLAYER_NAME} yet.", None
    
    history_str = "\n".join([
        f"Attempt ID: {s['attempt_id']}, Score: {s['score']}/{s['total_questions']}, Start: {s['start_time']}, End: {s['end_time']}, Completed: {s['is_completed']}"
        for s in history
    ])
    return f"Score History for {PLAYER_NAME}:\n{history_str}", None

def view_attempt_details(attempt_id):
    details = quiz_engine.get_player_last_attempt_details(PLAYER_NAME, attempt_id)
    if not details:
        return "Attempt details not found or invalid Attempt ID."
    
    summary_str = (f"Attempt ID: {details['attempt_id']}\nPlayer: {details['player_name']}\n"
                   f"Score: {details['score']}/{details['total_questions']}\n"
                   f"Start Time: {details['start_time']}\nEnd Time: {details['end_time']}\n"
                   f"Completed: {details['is_completed']}\n\nDetails:\n")
    
    details_list = []
    for q_detail in details['details']:
        result = "Correct" if q_detail['is_correct'] else "Incorrect"
        chosen_option_text = q_detail['options'][q_detail['chosen_answer_index']] if q_detail['chosen_answer_index'] is not None else "Not answered"
        correct_option_text = q_detail['options'][q_detail['correct_answer_index']]
        details_list.append(
            f"  Q: {q_detail['question_text']}\n"
            f"  Your Answer: {chosen_option_text} ({q_detail['chosen_answer_index']+1})\n"
            f"  Correct Answer: {correct_option_text} ({q_detail['correct_answer_index']+1})\n"
            f"  Result: {result}\n"
        )
    
    return summary_str + "\n".join(details_list)


# --- Gradio UI Layout ---

with gr.Blocks(title="Simple Quiz Game") as demo:
    gr.Markdown("# Simple Quiz Game Engine")
    
    # State variable to hold the current question ID for the player session
    current_question_id_state = gr.State(value=None) 

    with gr.Tab("Admin Panel"):
        gr.Markdown("## Admin: Manage Questions")
        with gr.Row():
            question_text_input = gr.Textbox(label="Question Text", placeholder="Enter question...")
        with gr.Row():
            option1_input = gr.Textbox(label="Option 1")
            option2_input = gr.Textbox(label="Option 2")
            option3_input = gr.Textbox(label="Option 3")
            option4_input = gr.Textbox(label="Option 4")
        with gr.Row():
            correct_option_index_input = gr.Radio(label="Correct Option (1-4)", choices=["1", "2", "3", "4"], value="1")
            add_question_btn = gr.Button("Add Question")
        
        admin_output = gr.Textbox(label="Admin Message", lines=5, interactive=False)
        
        gr.Markdown("### All Questions")
        view_questions_btn = gr.Button("Refresh All Questions")
        all_questions_output = gr.Textbox(label="Existing Questions", lines=10, interactive=False)

        gr.Markdown("### Delete Question")
        with gr.Row():
            delete_question_id_input = gr.Textbox(label="Question ID to Delete", placeholder="Enter UUID of question to delete...")
            delete_question_btn = gr.Button("Delete Question")

        add_question_btn.click(
            admin_add_question,
            [question_text_input, option1_input, option2_input, option3_input, option4_input, correct_option_index_input],
            [admin_output]
        ).then(
            get_all_questions_for_display,
            None,
            [all_questions_output, admin_output] # Refresh display and ensure admin_output is cleared/updated appropriately
        )

        delete_question_btn.click(
            admin_delete_question,
            [delete_question_id_input],
            [admin_output]
        ).then(
            get_all_questions_for_display,
            None,
            [all_questions_output, admin_output]
        )
        
        view_questions_btn.click(
            get_all_questions_for_display,
            None,
            [all_questions_output, admin_output] # The admin_output is cleared here.
        )
        # Initial load of questions
        demo.load(get_all_questions_for_display, None, [all_questions_output, admin_output])


    with gr.Tab("Player: Take Quiz"):
        gr.Markdown("## Player: Take a Quiz")
        gr.Markdown(f"Playing as: **{PLAYER_NAME}**")
        
        with gr.Row():
            num_questions_input = gr.Textbox(label="Number of Questions (Optional, leave blank for all)", placeholder="e.g., 3")
            start_quiz_btn = gr.Button("Start New Quiz")
            
        player_quiz_display = gr.Textbox(label="Quiz Progress", lines=10, interactive=False)
        player_answer_options = gr.Radio(label="Choose an option:", choices=[], visible=False)
        
        with gr.Row():
            submit_answer_btn = gr.Button("Submit Answer", visible=False)
            end_quiz_player_btn = gr.Button("End Quiz Early", visible=False)

        start_quiz_btn.click(
            start_player_quiz,
            [num_questions_input],
            [player_quiz_display, current_question_id_state, player_answer_options, submit_answer_btn, end_quiz_player_btn]
        )

        submit_answer_btn.click(
            submit_player_answer,
            [current_question_id_state, player_answer_options],
            [player_quiz_display, current_question_id_state, player_answer_options, submit_answer_btn, end_quiz_player_btn]
        )
        
        end_quiz_player_btn.click(
            end_player_quiz,
            None,
            [player_quiz_display, current_question_id_state, player_answer_options, submit_answer_btn, end_quiz_player_btn]
        )

    with gr.Tab("Player: Score History"):
        gr.Markdown("## Player: Score History")
        gr.Markdown(f"History for: **{PLAYER_NAME}**")
        
        refresh_history_btn = gr.Button("Refresh Score History")
        player_history_output = gr.Textbox(label="Your Quiz Score History", lines=10, interactive=False)

        gr.Markdown("### View Specific Attempt Details")
        with gr.Row():
            attempt_id_input = gr.Textbox(label="Attempt ID", placeholder="Enter an Attempt ID from history")
            view_attempt_details_btn = gr.Button("View Details")
        attempt_details_output = gr.Textbox(label="Attempt Details", lines=15, interactive=False)
        
        refresh_history_btn.click(
            get_player_history,
            None,
            [player_history_output, attempt_details_output] # Clear details when refreshing history
        )
        
        view_attempt_details_btn.click(
            view_attempt_details,
            [attempt_id_input],
            [attempt_details_output]
        )
        # Initial load of player history
        demo.load(get_player_history, None, [player_history_output, attempt_details_output])


if __name__ == "__main__":
    # Pre-populate some questions for testing
    quiz_engine.add_question("What is the capital of France?", ["Berlin", "Madrid", "Paris", "Rome"], 2) # Paris
    quiz_engine.add_question("Which planet is known as the Red Planet?", ["Earth", "Mars", "Jupiter", "Venus"], 1) # Mars
    quiz_engine.add_question("What is 2 + 2?", ["3", "4", "5", "6"], 1) # 4
    quiz_engine.add_question("What is the largest ocean on Earth?", ["Atlantic", "Indian", "Arctic", "Pacific"], 3) # Pacific

    demo.launch()