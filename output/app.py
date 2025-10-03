import gradio as gr
import datetime
from typing import List

# Import the backend class and models from the todo.py module
from todo import Todo, Task, Priority

# --- 1. Backend Instance ---
# Create a single, global instance of the Todo manager to act as our state for this simple demo.
# In a real multi-user application, this would be handled differently, likely with session state
# or a proper database backend.
todo_manager = Todo()

# --- 2. Helper Functions ---
# These functions bridge the gap between the raw data from the backend class
# and the format required by the Gradio UI components.

def format_tasks_for_display(tasks: List[Task]) -> List[List]:
    """Converts a list of Task objects into a list of lists for a Gradio DataFrame."""
    if not tasks:
        # Return a list with a placeholder if there are no tasks, to avoid an empty DataFrame display issue.
        # However, Gradio handles empty lists well now, so an empty list is fine.
        return []
    
    display_list = []
    for task in tasks:
        display_list.append([
            task.id,
            task.description,
            task.priority.name,
            task.deadline.isoformat() if task.deadline else "N/A",
            "✔️" if task.is_completed else "❌",
            task.creation_date.isoformat(),
            task.completion_date.isoformat() if task.completion_date else "N/A"
        ])
    return display_list

def get_all_updates():
    """
    A single function to fetch all data from the backend and format it for the UI.
    This is efficient as it updates all relevant components in one go.
    """
    pending_tasks = todo_manager.get_pending_tasks()
    completed_tasks = todo_manager.get_completed_tasks()
    overdue_tasks = todo_manager.get_overdue_tasks()
    
    pending_df_data = format_tasks_for_display(pending_tasks)
    completed_df_data = format_tasks_for_display(completed_tasks)
    overdue_df_data = format_tasks_for_display(overdue_tasks)
    
    percentage = todo_manager.get_completion_percentage()
    percentage_str = f"Completion: {percentage:.2f}%"
    
    # The order of returned values must match the order of `outputs` in the click/load events.
    return pending_df_data, completed_df_data, overdue_df_data, percentage_str

# --- 3. UI Interaction Handlers ---
# These functions are called when users interact with buttons in the UI.

def add_task_handler(description, priority_str, deadline_str):
    """Handles the 'Add Task' button click."""
    if not description:
        gr.Warning("Task description cannot be empty.")
        # Return the current state without making changes
        return get_all_updates() + (description, deadline_str) 

    # Convert priority string from UI to Priority enum for the backend
    priority_map = {"HIGH": Priority.HIGH, "MEDIUM": Priority.MEDIUM, "LOW": Priority.LOW}
    priority = priority_map.get(priority_str, Priority.MEDIUM)
    
    # Convert deadline string to a date object, handling empty or invalid input
    deadline = None
    if deadline_str:
        try:
            deadline = datetime.date.fromisoformat(deadline_str)
        except ValueError:
            gr.Warning("Invalid date format. Please use YYYY-MM-DD.")
            return get_all_updates() + (description, deadline_str)
    
    # Call the backend method
    todo_manager.add_task(description=description, priority=priority, deadline=deadline)
    gr.Info(f"Task '{description}' added.")
    
    # After adding, clear the input fields and refresh all data displays
    return get_all_updates() + ("", "") # Return empty strings to clear description and deadline

def complete_task_handler(task_id):
    """Handles the 'Mark as Complete' button click."""
    if task_id is None or task_id <= 0:
        gr.Warning("Please enter a valid Task ID.")
        return get_all_updates()
        
    task_id = int(task_id)
    task = todo_manager.complete_task(task_id)
    if task:
        gr.Info(f"Task {task_id} marked as complete.")
    else:
        gr.Error(f"Task with ID {task_id} not found or already complete.")
        
    # Refresh all data displays
    return get_all_updates()

def delete_task_handler(task_id):
    """Handles the 'Delete Task' button click."""
    if task_id is None or task_id <= 0:
        gr.Warning("Please enter a valid Task ID.")
        return get_all_updates()

    task_id = int(task_id)
    if todo_manager.delete_task(task_id):
        gr.Info(f"Task {task_id} deleted.")
    else:
        gr.Error(f"Task with ID {task_id} not found.")

    # Refresh all data displays
    return get_all_updates()

def get_summary_handler(date_str):
    """Handles the 'Get Summary' button click."""
    summary_date = datetime.date.today()
    if date_str:
        try:
            summary_date = datetime.date.fromisoformat(date_str)
        except (ValueError, TypeError):
            return "Invalid date format. Please use YYYY-MM-DD."

    summary = todo_manager.get_daily_summary(summary_date)
    
    # Format the summary dictionary into a readable Markdown string
    md = f"## Daily Summary for {summary['date'].isoformat()}\n\n"
    
    md += "### Tasks Created\n"
    if summary['tasks_created']:
        for task in summary['tasks_created']:
            md += f"- (ID: {task.id}) {task.description}\n"
    else:
        md += "- None\n"
        
    md += "\n### Tasks Completed\n"
    if summary['tasks_completed']:
        for task in summary['tasks_completed']:
            md += f"- (ID: {task.id}) {task.description}\n"
    else:
        md += "- None\n"
        
    md += "\n### Overdue Tasks (Snapshot for this day)\n"
    if summary['overdue_tasks_snapshot']:
        for task in summary['overdue_tasks_snapshot']:
            md += f"- (ID: {task.id}) {task.description} (Deadline: {task.deadline})\n"
    else:
        md += "- None\n"
        
    return md

# --- 4. Gradio UI Layout ---

with gr.Blocks(theme=gr.themes.Soft(), title="Todo List Manager") as demo:
    gr.Markdown("# ✅ Simple Todo List Manager")
    
    # A central display for the completion percentage
    completion_progress = gr.Textbox(
        label="Overall Progress", 
        value="Completion: 0.00%", 
        interactive=False
    )
    
    with gr.Tabs():
        with gr.TabItem("📋 Manage & View Tasks"):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### Add New Task")
                    task_desc_input = gr.Textbox(label="Description", placeholder="e.g., Buy milk")
                    task_prio_input = gr.Radio(
                        ["HIGH", "MEDIUM", "LOW"], 
                        label="Priority", 
                        value="MEDIUM"
                    )
                    task_deadline_input = gr.Textbox(
                        label="Deadline (Optional)", 
                        placeholder="YYYY-MM-DD"
                    )
                    add_button = gr.Button("Add Task", variant="primary")
                    
                    gr.Markdown("---")
                    gr.Markdown("### Actions on Existing Task")
                    task_id_input = gr.Number(label="Task ID", precision=0, minimum=1)
                    with gr.Row():
                        complete_button = gr.Button("Mark as Complete")
                        delete_button = gr.Button("Delete Task", variant="stop")

                with gr.Column(scale=2):
                    gr.Markdown("### Task Lists")
                    df_headers = ["ID", "Description", "Priority", "Deadline", "Completed", "Created", "Completed On"]
                    df_datatypes = ["number", "str", "str", "str", "str", "str", "str"]
                    with gr.Accordion("Pending Tasks", open=True):
                        pending_tasks_df = gr.DataFrame(
                            headers=df_headers, datatype=df_datatypes, row_count=(5, "dynamic")
                        )
                    with gr.Accordion("Completed Tasks", open=False):
                        completed_tasks_df = gr.DataFrame(
                            headers=df_headers, datatype=df_datatypes, row_count=(5, "dynamic")
                        )
                    with gr.Accordion("Overdue Tasks", open=False):
                        overdue_tasks_df = gr.DataFrame(
                            headers=df_headers, datatype=df_datatypes, row_count=(5, "dynamic")
                        )

        with gr.TabItem("🗓️ Daily Summary"):
            gr.Markdown("Get a summary of tasks created, completed, and overdue for a specific day.")
            with gr.Row():
                summary_date_input = gr.Textbox(
                    label="Date", 
                    placeholder="YYYY-MM-DD (defaults to today)"
                )
                summary_button = gr.Button("Get Summary")
            summary_output = gr.Markdown()
    
    # --- 5. Event Listeners ---
    # Connect the UI components to the handler functions.
    
    # Define the list of outputs that are updated by most actions.
    outputs_to_update = [pending_tasks_df, completed_tasks_df, overdue_tasks_df, completion_progress]

    add_button.click(
        fn=add_task_handler,
        inputs=[task_desc_input, task_prio_input, task_deadline_input],
        outputs=outputs_to_update + [task_desc_input, task_deadline_input] # Also clears inputs
    )
    
    complete_button.click(
        fn=complete_task_handler,
        inputs=[task_id_input],
        outputs=outputs_to_update
    )
    
    delete_button.click(
        fn=delete_task_handler,
        inputs=[task_id_input],
        outputs=outputs_to_update
    )
    
    summary_button.click(
        fn=get_summary_handler,
        inputs=[summary_date_input],
        outputs=[summary_output]
    )
    
    # Use the 'load' event to populate the UI with initial data when the app starts.
    demo.load(
        fn=get_all_updates,
        inputs=None,
        outputs=outputs_to_update
    )

# --- 6. Launch the App ---
if __name__ == "__main__":
    # Add some sample data for a better first-time experience
    todo_manager.add_task("Review Gradio documentation", Priority.HIGH, datetime.date.today() + datetime.timedelta(days=1))
    todo_manager.add_task("Submit project proposal", Priority.HIGH, datetime.date(2023, 1, 1)) # Overdue example
    todo_manager.add_task("Water the plants", Priority.LOW)
    completed_task_id = todo_manager.add_task("Buy groceries", Priority.MEDIUM)
    todo_manager.complete_task(completed_task_id)
    
    # Launch the Gradio interface
    demo.launch()