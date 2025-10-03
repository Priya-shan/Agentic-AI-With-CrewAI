import unittest
import uuid
from ecommerce import (
    Ecommerce,
    UserNotFoundError,
    ProductNotFoundError,
    InsufficientFundsError,
    EmptyCartError,
    EcommerceError,
)

class TestEcommerce(unittest.TestCase):

    def setUp(self):
        """Set up a new Ecommerce instance and some initial data for each test."""
        self.ecommerce = Ecommerce()
        self.ecommerce.add_user("user1", "Alice", 100.0)
        self.ecommerce.add_user("user2", "Bob", 10.0)
        self.ecommerce.add_product("prod1", "Laptop", 80.0)
        self.ecommerce.add_product("prod2", "Mouse", 15.0)

    # Test Setup Methods
    def test_add_product_success(self):
        """Test adding a product with valid data."""
        self.ecommerce.add_product("prod3", "Keyboard", 25.0)
        self.assertIn("prod3", self.ecommerce._products)
        self.assertEqual(self.ecommerce._products["prod3"]["name"], "Keyboard")
        self.assertEqual(self.ecommerce._products["prod3"]["price"], 25.0)

    def test_add_product_negative_price(self):
        """Test that adding a product with a negative price raises ValueError."""
        with self.assertRaises(ValueError):
            self.ecommerce.add_product("prod_invalid", "Faulty Item", -10.0)

    def test_add_user_success(self):
        """Test adding a user with valid data."""
        self.ecommerce.add_user("user3", "Charlie", 500.0)
        self.assertIn("user3", self.ecommerce._users)
        self.assertEqual(self.ecommerce._users["user3"]["name"], "Charlie")
        self.assertEqual(self.ecommerce._users["user3"]["balance"], 500.0)

    def test_add_user_negative_balance(self):
        """Test that adding a user with a negative initial balance raises ValueError."""
        with self.assertRaises(ValueError):
            self.ecommerce.add_user("user_invalid", "David", -50.0)

    # Test Cart Management Methods
    def test_add_to_cart_new_item(self):
        """Test adding a new item to a user's cart."""
        self.ecommerce.add_to_cart("user1", "prod1")
        self.assertIn("user1", self.ecommerce._carts)
        self.assertIn("prod1", self.ecommerce._carts["user1"])
        self.assertEqual(self.ecommerce._carts["user1"]["prod1"], 1)

    def test_add_to_cart_increase_quantity(self):
        """Test adding an item that's already in the cart increases its quantity."""
        self.ecommerce.add_to_cart("user1", "prod1", 2)
        self.ecommerce.add_to_cart("user1", "prod1", 3)
        self.assertEqual(self.ecommerce._carts["user1"]["prod1"], 5)

    def test_add_to_cart_invalid_user(self):
        """Test adding to cart for a non-existent user raises UserNotFoundError."""
        with self.assertRaises(UserNotFoundError):
            self.ecommerce.add_to_cart("non_existent_user", "prod1")

    def test_add_to_cart_invalid_product(self):
        """Test adding a non-existent product to cart raises ProductNotFoundError."""
        with self.assertRaises(ProductNotFoundError):
            self.ecommerce.add_to_cart("user1", "non_existent_product")

    def test_add_to_cart_invalid_quantity(self):
        """Test adding an item with zero, negative, or non-integer quantity raises ValueError."""
        with self.assertRaises(ValueError):
            self.ecommerce.add_to_cart("user1", "prod1", 0)
        with self.assertRaises(ValueError):
            self.ecommerce.add_to_cart("user1", "prod1", -1)
        with self.assertRaises(ValueError):
            self.ecommerce.add_to_cart("user1", "prod1", 1.5)

    # Test remove_from_cart
    def test_remove_from_cart_partial_quantity(self):
        """Test removing a quantity that is less than the total in the cart."""
        self.ecommerce.add_to_cart("user1", "prod1", 5)
        self.ecommerce.remove_from_cart("user1", "prod1", 2)
        self.assertEqual(self.ecommerce._carts["user1"]["prod1"], 3)

    def test_remove_from_cart_exact_quantity(self):
        """Test removing the exact quantity of an item, removing it from the cart."""
        self.ecommerce.add_to_cart("user1", "prod1", 2)
        self.ecommerce.add_to_cart("user1", "prod2", 1)
        self.ecommerce.remove_from_cart("user1", "prod1", 2)
        self.assertNotIn("prod1", self.ecommerce._carts["user1"])
        self.assertIn("prod2", self.ecommerce._carts["user1"]) # Other items remain

    def test_remove_from_cart_more_than_quantity(self):
        """Test removing more than the quantity of an item, removing it from the cart."""
        self.ecommerce.add_to_cart("user1", "prod1", 2)
        self.ecommerce.remove_from_cart("user1", "prod1", 5)
        self.assertNotIn("prod1", self.ecommerce._carts["user1"])

    def test_remove_from_cart_item_not_in_cart(self):
        """Test that removing an item not in the cart does nothing and does not raise an error."""
        self.ecommerce.add_to_cart("user1", "prod1")
        # Attempt to remove a different product
        self.ecommerce.remove_from_cart("user1", "prod2")
        self.assertEqual(self.ecommerce._carts["user1"]["prod1"], 1)

    def test_remove_from_cart_cleanup_empty_cart(self):
        """Test that the user's cart is removed entirely when the last item is removed."""
        self.ecommerce.add_to_cart("user1", "prod1")
        self.ecommerce.remove_from_cart("user1", "prod1")
        self.assertNotIn("user1", self.ecommerce._carts)

    def test_remove_from_cart_invalid_user(self):
        """Test removing from cart for a non-existent user raises UserNotFoundError."""
        with self.assertRaises(UserNotFoundError):
            self.ecommerce.remove_from_cart("non_existent_user", "prod1")

    def test_remove_from_cart_invalid_quantity(self):
        """Test removing an item with zero, negative, or non-integer quantity raises ValueError."""
        self.ecommerce.add_to_cart("user1", "prod1")
        with self.assertRaises(ValueError):
            self.ecommerce.remove_from_cart("user1", "prod1", 0)
        with self.assertRaises(ValueError):
            self.ecommerce.remove_from_cart("user1", "prod1", -1)
        with self.assertRaises(ValueError):
            self.ecommerce.remove_from_cart("user1", "prod1", 1.5)

    # Test view_cart
    def test_view_cart_empty(self):
        """Test viewing an empty cart."""
        cart = self.ecommerce.view_cart("user1")
        self.assertEqual(cart, {"items": [], "total_value": 0.0})

    def test_view_cart_with_items(self):
        """Test viewing a cart with items and correct total value calculation."""
        self.ecommerce.add_to_cart("user1", "prod1", 1)  # 80.0
        self.ecommerce.add_to_cart("user1", "prod2", 2)  # 15.0 * 2 = 30.0
        cart = self.ecommerce.view_cart("user1")
        self.assertEqual(len(cart["items"]), 2)
        self.assertAlmostEqual(cart["total_value"], 110.0)
        # Check details of one item
        laptop_item = next(item for item in cart["items"] if item["product_id"] == "prod1")
        self.assertEqual(laptop_item["name"], "Laptop")
        self.assertEqual(laptop_item["quantity"], 1)
        self.assertAlmostEqual(laptop_item["subtotal"], 80.0)

    def test_view_cart_invalid_user(self):
        """Test viewing cart for a non-existent user raises UserNotFoundError."""
        with self.assertRaises(UserNotFoundError):
            self.ecommerce.view_cart("non_existent_user")

    # Test Checkout and Order Methods
    def test_checkout_success(self):
        """Test a successful checkout process."""
        self.ecommerce.add_to_cart("user1", "prod1", 1) # 80.0
        self.ecommerce.add_to_cart("user1", "prod2", 1) # 15.0
        # Total: 95.0, Balance: 100.0
        
        initial_balance = self.ecommerce._users["user1"]["balance"]
        cart_total = self.ecommerce.view_cart("user1")["total_value"]
        
        order_id = self.ecommerce.checkout("user1")

        # Check order ID format
        self.assertIsInstance(order_id, str)
        try:
            uuid.UUID(order_id)
        except ValueError:
            self.fail("Checkout did not return a valid UUID string.")

        # Check balance deduction
        self.assertAlmostEqual(self.ecommerce._users["user1"]["balance"], initial_balance - cart_total)
        
        # Check cart is cleared
        self.assertNotIn("user1", self.ecommerce._carts)
        
        # Check order history
        orders = self.ecommerce.get_order_history("user1")
        self.assertEqual(len(orders), 1)
        self.assertEqual(orders[0]["order_id"], order_id)
        self.assertAlmostEqual(orders[0]["total_value"], 95.0)
        self.assertEqual(orders[0]["items"], {"prod1": 1, "prod2": 1})

    def test_checkout_empty_cart(self):
        """Test checkout with an empty cart raises EmptyCartError."""
        with self.assertRaises(EmptyCartError):
            self.ecommerce.checkout("user1")

    def test_checkout_insufficient_funds(self):
        """Test checkout with insufficient funds raises InsufficientFundsError."""
        self.ecommerce.add_to_cart("user2", "prod1", 1)  # Price 80.0, balance 10.0
        with self.assertRaises(InsufficientFundsError):
            self.ecommerce.checkout("user2")

    def test_checkout_invalid_user(self):
        """Test checkout for a non-existent user raises UserNotFoundError."""
        with self.assertRaises(UserNotFoundError):
            self.ecommerce.checkout("non_existent_user")

    # Test get_order_history
    def test_get_order_history_no_orders(self):
        """Test getting order history for a user with no orders."""
        history = self.ecommerce.get_order_history("user1")
        self.assertEqual(history, [])

    def test_get_order_history_with_orders(self):
        """Test getting order history for a user with multiple orders."""
        # First order
        self.ecommerce.add_to_cart("user1", "prod2", 1)
        order_id1 = self.ecommerce.checkout("user1")
        
        # Second order
        self.ecommerce.add_to_cart("user1", "prod2", 2)
        order_id2 = self.ecommerce.checkout("user1")
        
        history = self.ecommerce.get_order_history("user1")
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["order_id"], order_id1)
        self.assertEqual(history[1]["order_id"], order_id2)

    def test_get_order_history_invalid_user(self):
        """Test getting order history for a non-existent user raises UserNotFoundError."""
        with self.assertRaises(UserNotFoundError):
            self.ecommerce.get_order_history("non_existent_user")
            
    # Test Custom Exception Inheritance
    def test_exception_inheritance(self):
        """Test that custom exceptions inherit from the base EcommerceError."""
        self.assertTrue(issubclass(UserNotFoundError, EcommerceError))
        self.assertTrue(issubclass(ProductNotFoundError, EcommerceError))
        self.assertTrue(issubclass(InsufficientFundsError, EcommerceError))
        self.assertTrue(issubclass(EmptyCartError, EcommerceError))


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)