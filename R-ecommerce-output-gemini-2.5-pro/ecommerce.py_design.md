# Design Document: Simple E-Commerce System

**To:** Backend Engineer
**From:** Engineering Lead
**Date:** 2023-10-27
**Re:** Detailed Design for `ecommerce.py` Module

Here is the detailed design for the simple e-commerce system. The goal is a single, self-contained Python module that can be easily tested or integrated with a simple UI. Please follow this design closely.

## 1. Module Overview

The entire system will be encapsulated within a single Python file: `ecommerce.py`. This module will contain one primary class, `Ecommerce`, which will manage the state and business logic of the system. It will also include several custom exception classes for robust error handling.

## 2. Module: `ecommerce.py`

This module will contain all the necessary classes and logic. We will not use external databases; all data (users, products, carts, orders) will be stored in memory in instance variables of the `Ecommerce` class.

### 2.1. Custom Exception Classes

To handle specific error scenarios gracefully, we will define the following custom exceptions. They should all inherit from a base `EcommerceError`.

```python
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
```

### 2.2. Main Class: `Ecommerce`

This class is the core of our system. It will manage all data and expose methods to interact with the e-commerce platform.

**Class Signature:**
`class Ecommerce:`

**Instance Variables:**

*   `self._products`: A dictionary to store product information.
    *   **Structure:** `{ product_id (str): {'name': str, 'price': float} }`
*   `self._users`: A dictionary to store user data.
    *   **Structure:** `{ user_id (str): {'name': str, 'balance': float} }`
*   `self._carts`: A dictionary to store the contents of each user's shopping cart.
    *   **Structure:** `{ user_id (str): {product_id (str): quantity (int)} }`
*   `self._orders`: A dictionary to store the order history for each user.
    *   **Structure:** `{ user_id (str): [order_details (dict), ...] }`

---

### `Ecommerce` Methods

#### `__init__(self)`

*   **Signature:** `def __init__(self) -> None:`
*   **Description:** Initializes a new instance of the `Ecommerce` system. It sets up the empty in-memory data stores for products, users, carts, and orders.
*   **Logic:**
    1.  Initialize `self._products` to an empty dictionary.
    2.  Initialize `self._users` to an empty dictionary.
    3.  Initialize `self._carts` to an empty dictionary.
    4.  Initialize `self._orders` to an empty dictionary.

---

#### Setup Methods

These methods are for populating the demo system with data.

*   **`add_product(self, product_id: str, name: str, price: float) -> None:`**
    *   **Description:** Adds a new product to the system's catalog.
    *   **Logic:**
        1.  Validate that `price` is a non-negative number.
        2.  Add a new entry to the `self._products` dictionary.

*   **`add_user(self, user_id: str, name: str, initial_balance: float) -> None:`**
    *   **Description:** Adds a new user to the system.
    *   **Logic:**
        1.  Validate that `initial_balance` is a non-negative number.
        2.  Add a new entry to the `self._users` dictionary.

---

#### Cart Management Methods

*   **`add_to_cart(self, user_id: str, product_id: str, quantity: int = 1) -> None:`**
    *   **Description:** Adds a specified quantity of a product to a user's shopping cart.
    *   **Logic:**
        1.  Check if `user_id` exists in `self._users`. If not, raise `UserNotFoundError`.
        2.  Check if `product_id` exists in `self._products`. If not, raise `ProductNotFoundError`.
        3.  Validate that `quantity` is a positive integer.
        4.  If the user does not have a cart yet (`user_id` not in `self._carts`), create an empty dictionary for them.
        5.  Add the `quantity` to the existing quantity for the `product_id` in the user's cart. If the product is not yet in the cart, add it.
    *   **Raises:** `UserNotFoundError`, `ProductNotFoundError`, `ValueError` (for invalid quantity).

*   **`remove_from_cart(self, user_id: str, product_id: str, quantity: int = 1) -> None:`**
    *   **Description:** Removes a specified quantity of a product from a user's cart. If the resulting quantity is zero or less, the item is removed from the cart entirely.
    *   **Logic:**
        1.  Check if `user_id` exists. If not, raise `UserNotFoundError`.
        2.  Check if the user's cart or the `product_id` within it exists. If not, the method can silently do nothing or raise an error (let's have it do nothing to be safe).
        3.  Validate that `quantity` is a positive integer.
        4.  Subtract `quantity` from the product's count in the cart.
        5.  If the new quantity is <= 0, remove the `product_id` key from the user's cart dictionary.
    *   **Raises:** `UserNotFoundError`, `ValueError` (for invalid quantity).

*   **`view_cart(self, user_id: str) -> dict:`**
    *   **Description:** Returns a detailed view of a user's shopping cart, including product names, prices, quantities, and a subtotal for each item.
    *   **Logic:**
        1.  Check if `user_id` exists. If not, raise `UserNotFoundError`.
        2.  If the user has no cart, return an empty dictionary.
        3.  Iterate through the `product_id` and `quantity` in the user's cart.
        4.  For each item, look up the product details (`name`, `price`) from `self._products`.
        5.  Construct and return a dictionary containing the detailed list of items and the total cart value.
    *   **Return Format Example:**
        ```json
        {
          "items": [
            {
              "product_id": "p1",
              "name": "Laptop",
              "price": 1200.00,
              "quantity": 1,
              "subtotal": 1200.00
            },
            {
              "product_id": "p2",
              "name": "Mouse",
              "price": 25.00,
              "quantity": 2,
              "subtotal": 50.00
            }
          ],
          "total_value": 1250.00
        }
        ```
    *   **Raises:** `UserNotFoundError`.

---

#### Checkout and Order Methods

*   **`checkout(self, user_id: str) -> str:`**
    *   **Description:** Processes the user's cart for checkout. If successful, it deducts funds, creates an order record, and clears the cart.
    *   **Logic:**
        1.  Check if `user_id` exists. If not, raise `UserNotFoundError`.
        2.  Get the user's cart. If the cart is empty or does not exist, raise `EmptyCartError`.
        3.  Calculate the total value of the cart by iterating through items, fetching their prices, and summing the `price * quantity`.
        4.  Retrieve the user's current balance from `self._users`.
        5.  If `cart_total > user_balance`, raise `InsufficientFundsError`.
        6.  If sufficient funds exist:
            a. Deduct the `cart_total` from the user's balance.
            b. Generate a unique order ID (e.g., using `uuid.uuid4()` or a simple counter).
            c. Create an order record dictionary containing `order_id`, `items` (a copy of the cart), `total_value`, and a `timestamp`.
            d. If `user_id` is not in `self._orders`, create an empty list for them.
            e. Append the new order record to the user's order history in `self._orders`.
            f. Clear the user's cart by deleting their entry from `self._carts`.
            g. Return the generated `order_id`.
    *   **Raises:** `UserNotFoundError`, `EmptyCartError`, `InsufficientFundsError`.

*   **`get_order_history(self, user_id: str) -> list[dict]:`**
    *   **Description:** Retrieves the complete order history for a given user.
    *   **Logic:**
        1.  Check if `user_id` exists. If not, raise `UserNotFoundError`.
        2.  Return the list of order dictionaries for the user from `self._orders`. If the user has no orders, return an empty list.
    *   **Raises:** `UserNotFoundError`.

---
### 3. Example Usage Flow

A developer using this module would perform the following steps:

1.  Instantiate the system: `system = Ecommerce()`
2.  Set up products and users: `system.add_product(...)`, `system.add_user(...)`
3.  Simulate a user adding items: `system.add_to_cart(user_id='u1', product_id='p1', quantity=2)`
4.  View the cart: `cart_details = system.view_cart(user_id='u1')`
5.  Proceed to checkout: `order_id = system.checkout(user_id='u1')`
6.  View past orders: `history = system.get_order_history(user_id='u1')`