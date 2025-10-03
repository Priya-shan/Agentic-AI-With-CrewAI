import gradio as gr
from ecommerce import Ecommerce, EcommerceError

# --- Backend Setup ---
# This part initializes the backend system.
# In a real application, this data would come from a database.

ecommerce_system = Ecommerce()

# Create a single user for this demo
USER_ID = "user_01"
ecommerce_system.add_user(USER_ID, "Demo User", 150.00)

# Add some products to the store catalog
ecommerce_system.add_product("p_001", "Laptop", 50.0)
ecommerce_system.add_product("p_002", "Mouse", 5.0)
ecommerce_system.add_product("p_003", "Keyboard", 10.0)
ecommerce_system.add_product("p_004", "Monitor", 75.0)

# Create a list of choices for the Gradio dropdown component
PRODUCT_CHOICES = [
    ("Laptop ($50.00)", "p_001"),
    ("Mouse ($5.00)", "p_002"),
    ("Keyboard ($10.00)", "p_003"),
    ("Monitor ($75.00)", "p_004")
]

# --- UI Helper Functions ---
# These functions format the data from the backend for display in the UI.

def format_balance():
    """Returns a formatted string for the user's current balance."""
    balance = ecommerce_system._users[USER_ID]['balance']
    return f"**User:** {ecommerce_system._users[USER_ID]['name']} | **Current Balance:** ${balance:.2f}"

def format_cart():
    """Returns a formatted string of the cart's contents."""
    cart_data = ecommerce_system.view_cart(USER_ID)
    if not cart_data["items"]:
        return "Your cart is empty."
    
    display_text = []
    for item in cart_data["items"]:
        display_text.append(
            f"- {item['name']} (ID: {item['product_id']})\n"
            f"  Quantity: {item['quantity']} @ ${item['price']:.2f} each\n"
            f"  Subtotal: ${item['subtotal']:.2f}"
        )
    display_text.append("--------------------")
    display_text.append(f"TOTAL: ${cart_data['total_value']:.2f}")
    return "\n".join(display_text)

def format_order_history():
    """Returns a formatted string of the user's order history."""
    history = ecommerce_system.get_order_history(USER_ID)
    if not history:
        return "No past orders found."

    display_text = []
    for order in reversed(history): # Show most recent first
        display_text.append(f"Order ID: {order['order_id']}")
        display_text.append(f"Date: {order['timestamp']}")
        display_text.append("Items:")
        for product_id, quantity in order['items'].items():
             product_name = ecommerce_system._products.get(product_id, {}).get('name', 'Unknown Product')
             display_text.append(f"  - {quantity} x {product_name} ({product_id})")
        display_text.append(f"Total: ${order['total_value']:.2f}")
        display_text.append("--------------------")
    return "\n".join(display_text)

# --- Gradio Action Handlers ---
# These functions are called when the user interacts with the UI components.

def add_item_action(product_id, quantity):
    """Handles the 'Add to Cart' button click."""
    if not product_id:
        return format_balance(), format_cart(), format_order_history(), "Error: Please select a product."
    try:
        quantity = int(quantity)
        ecommerce_system.add_to_cart(USER_ID, product_id, quantity)
        product_name = ecommerce_system._products[product_id]['name']
        status = f"Success: Added {quantity} x {product_name} to your cart."
    except (EcommerceError, ValueError) as e:
        status = f"Error: {e}"
    
    return format_balance(), format_cart(), format_order_history(), status

def remove_item_action(product_id, quantity):
    """Handles the 'Remove from Cart' button click."""
    if not product_id:
        return format_balance(), format_cart(), format_order_history(), "Error: Please select a product."
    try:
        quantity = int(quantity)
        ecommerce_system.remove_from_cart(USER_ID, product_id, quantity)
        product_name = ecommerce_system._products[product_id]['name']
        status = f"Success: Removed {quantity} x {product_name} from your cart."
    except (EcommerceError, ValueError) as e:
        status = f"Error: {e}"
    
    return format_balance(), format_cart(), format_order_history(), status

def checkout_action():
    """Handles the 'Checkout' button click."""
    try:
        order_id = ecommerce_system.checkout(USER_ID)
        status = f"Success! Checkout complete. Your Order ID is: {order_id}"
    except EcommerceError as e:
        status = f"Checkout Failed: {e}"
        
    return format_balance(), format_cart(), format_order_history(), status


# --- Gradio UI Definition ---
# This block defines the layout and components of the web interface.

with gr.Blocks(theme=gr.themes.Soft(), title="E-commerce Demo") as demo:
    gr.Markdown("# Simple E-commerce System Demo")
    
    balance_display = gr.Markdown(value=format_balance)

    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## Manage Your Cart")
            product_dropdown = gr.Dropdown(
                choices=PRODUCT_CHOICES, 
                label="Select a Product"
            )
            quantity_input = gr.Number(
                value=1, 
                label="Quantity", 
                minimum=1, 
                step=1
            )
            with gr.Row():
                add_button = gr.Button("Add to Cart")
                remove_button = gr.Button("Remove from Cart")
            
            gr.Markdown("---")
            gr.Markdown("## Finalize Purchase")
            checkout_button = gr.Button("Checkout", variant="primary")
            
            status_display = gr.Textbox(
                label="Status Message",
                value="Welcome! Add items to your cart.",
                interactive=False
            )

        with gr.Column(scale=2):
            cart_display = gr.Textbox(
                value=format_cart,
                label="🛒 Your Cart",
                lines=10,
                interactive=False,
                autoscroll=True
            )
            history_display = gr.Textbox(
                value=format_order_history,
                label="📜 Order History",
                lines=10,
                interactive=False,
                autoscroll=True
            )

    # --- Component Wiring ---
    # Connect the buttons to their respective action functions.
    # The outputs update the display components on the right.
    outputs_to_update = [balance_display, cart_display, history_display, status_display]

    add_button.click(
        fn=add_item_action,
        inputs=[product_dropdown, quantity_input],
        outputs=outputs_to_update
    )
    
    remove_button.click(
        fn=remove_item_action,
        inputs=[product_dropdown, quantity_input],
        outputs=outputs_to_update
    )
    
    checkout_button.click(
        fn=checkout_action,
        inputs=[],
        outputs=outputs_to_update
    )

if __name__ == "__main__":
    demo.launch()