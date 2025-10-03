import uuid
from datetime import datetime
from typing import Dict, List, Any

# 2.1. Custom Exception Classes
class EcommerceError(Exception):
    """Base exception for all errors in this module."""
    pass

class UserNotFoundError(EcommerceError):
    """Raised when an operation is attempted on a non-existent user."""
    pass

class ProductNotFoundError(EcommerceError):
    """Raised when an operation is attempted on a non-existent product."""
    pass

class InsufficientFundsError(EcommerceError):
    """Raised during checkout if the user's balance is too low."""
    pass

class EmptyCartError(EcommerceError):
    """Raised during checkout if the user's cart is empty."""
    pass


# 2.2. Main Class: Ecommerce
class Ecommerce:
    """
    Core class for the simple e-commerce system. It manages all data and
    exposes methods to interact with the platform.
    """

    def __init__(self) -> None:
        """
        Initializes a new instance of the Ecommerce system. It sets up the empty
        in-memory data stores for products, users, carts, and orders.
        """
        self._products: Dict[str, Dict[str, Any]] = {}
        self._users: Dict[str, Dict[str, Any]] = {}
        self._carts: Dict[str, Dict[str, int]] = {}
        self._orders: Dict[str, List[Dict[str, Any]]] = {}

    # Setup Methods
    def add_product(self, product_id: str, name: str, price: float) -> None:
        """
        Adds a new product to the system's catalog.

        Args:
            product_id: The unique identifier for the product.
            name: The name of the product.
            price: The price of the product.

        Raises:
            ValueError: If the price is negative.
        """
        if price < 0:
            raise ValueError("Price cannot be negative.")
        self._products[product_id] = {'name': name, 'price': price}

    def add_user(self, user_id: str, name: str, initial_balance: float) -> None:
        """
        Adds a new user to the system.

        Args:
            user_id: The unique identifier for the user.
            name: The name of the user.
            initial_balance: The user's starting funds.

        Raises:
            ValueError: If the initial balance is negative.
        """
        if initial_balance < 0:
            raise ValueError("Initial balance cannot be negative.")
        self._users[user_id] = {'name': name, 'balance': initial_balance}

    # Cart Management Methods
    def add_to_cart(self, user_id: str, product_id: str, quantity: int = 1) -> None:
        """
        Adds a specified quantity of a product to a user's shopping cart.

        Args:
            user_id: The ID of the user.
            product_id: The ID of the product to add.
            quantity: The number of items to add. Defaults to 1.

        Raises:
            UserNotFoundError: If the user_id does not exist.
            ProductNotFoundError: If the product_id does not exist.
            ValueError: If the quantity is not a positive integer.
        """
        if user_id not in self._users:
            raise UserNotFoundError(f"User '{user_id}' not found.")
        if product_id not in self._products:
            raise ProductNotFoundError(f"Product '{product_id}' not found.")
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

        if user_id not in self._carts:
            self._carts[user_id] = {}

        current_quantity = self._carts[user_id].get(product_id, 0)
        self._carts[user_id][product_id] = current_quantity + quantity

    def remove_from_cart(self, user_id: str, product_id: str, quantity: int = 1) -> None:
        """
        Removes a specified quantity of a product from a user's cart.
        If the resulting quantity is zero or less, the item is removed entirely.

        Args:
            user_id: The ID of the user.
            product_id: The ID of the product to remove.
            quantity: The number of items to remove. Defaults to 1.

        Raises:
            UserNotFoundError: If the user_id does not exist.
            ValueError: If the quantity is not a positive integer.
        """
        if user_id not in self._users:
            raise UserNotFoundError(f"User '{user_id}' not found.")
        if not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("Quantity must be a positive integer.")

        user_cart = self._carts.get(user_id)
        if not user_cart or product_id not in user_cart:
            return  # Silently do nothing as per design

        current_quantity = user_cart.get(product_id, 0)
        new_quantity = current_quantity - quantity

        if new_quantity <= 0:
            del self._carts[user_id][product_id]
        else:
            self._carts[user_id][product_id] = new_quantity
            
        if not self._carts[user_id]: # Clean up empty cart dict
             del self._carts[user_id]


    def view_cart(self, user_id: str) -> Dict[str, Any]:
        """
        Returns a detailed view of a user's shopping cart.

        Args:
            user_id: The ID of the user whose cart to view.

        Returns:
            A dictionary containing a list of items and the total value.

        Raises:
            UserNotFoundError: If the user_id does not exist.
        """
        if user_id not in self._users:
            raise UserNotFoundError(f"User '{user_id}' not found.")

        user_cart = self._carts.get(user_id, {})
        if not user_cart:
            return {"items": [], "total_value": 0.0}

        cart_details = {"items": [], "total_value": 0.0}
        total_value = 0.0

        for product_id, quantity in user_cart.items():
            product_info = self._products.get(product_id)
            if product_info:
                subtotal = product_info['price'] * quantity
                cart_details["items"].append({
                    "product_id": product_id,
                    "name": product_info['name'],
                    "price": product_info['price'],
                    "quantity": quantity,
                    "subtotal": subtotal
                })
                total_value += subtotal

        cart_details["total_value"] = total_value
        return cart_details

    # Checkout and Order Methods
    def checkout(self, user_id: str) -> str:
        """
        Processes the user's cart for checkout.

        Args:
            user_id: The ID of the user checking out.

        Returns:
            The unique ID of the generated order.

        Raises:
            UserNotFoundError: If the user_id does not exist.
            EmptyCartError: If the user's cart is empty.
            InsufficientFundsError: If the user's balance is less than the cart total.
        """
        if user_id not in self._users:
            raise UserNotFoundError(f"User '{user_id}' not found.")

        user_cart_data = self.view_cart(user_id)
        cart_total = user_cart_data["total_value"]

        if not user_cart_data["items"]:
            raise EmptyCartError(f"Cart for user '{user_id}' is empty.")

        user_balance = self._users[user_id]['balance']

        if cart_total > user_balance:
            raise InsufficientFundsError(
                f"Insufficient funds for user '{user_id}'. "
                f"Balance: {user_balance}, Required: {cart_total}"
            )

        # Process the order
        self._users[user_id]['balance'] -= cart_total

        order_id = str(uuid.uuid4())
        
        # We need a copy of the items, not just the product IDs
        order_items = self._carts.get(user_id, {}).copy()

        order_record = {
            "order_id": order_id,
            "items": order_items,
            "total_value": cart_total,
            "timestamp": datetime.utcnow().isoformat()
        }

        if user_id not in self._orders:
            self._orders[user_id] = []
        self._orders[user_id].append(order_record)

        # Clear the cart
        if user_id in self._carts:
            del self._carts[user_id]

        return order_id

    def get_order_history(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves the complete order history for a given user.

        Args:
            user_id: The ID of the user.

        Returns:
            A list of order dictionaries for the user. Returns an empty list
            if the user has no orders.

        Raises:
            UserNotFoundError: If the user_id does not exist.
        """
        if user_id not in self._users:
            raise UserNotFoundError(f"User '{user_id}' not found.")

        return self._orders.get(user_id, [])