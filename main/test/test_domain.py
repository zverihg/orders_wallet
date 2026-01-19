"""
Unit tests for domain models.
"""
from decimal import Decimal
from uuid import UUID, uuid4

from django.test import TestCase

from main.domain.order import Order, OrderItem, OrderStatus
from main.domain.wallet import Wallet, WalletTransaction, TransactionType


class OrderItemTest(TestCase):
    """Tests for OrderItem value object."""

    def test_create_order_item(self):
        """Test creating order item with valid data."""
        item = OrderItem(
            product_id=uuid4(),
            quantity=2,
            price=Decimal("100.00"),
        )
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, Decimal("100.00"))
        self.assertEqual(item.subtotal, Decimal("200.00"))

    def test_order_item_negative_quantity_fails(self):
        """Test that negative quantity raises error."""
        with self.assertRaises(ValueError):
            OrderItem(
                product_id=uuid4(),
                quantity=-1,
                price=Decimal("100.00"),
            )

    def test_order_item_negative_price_fails(self):
        """Test that negative price raises error."""
        with self.assertRaises(ValueError):
            OrderItem(
                product_id=uuid4(),
                quantity=1,
                price=Decimal("-100.00"),
            )


class OrderTest(TestCase):
    """Tests for Order aggregate."""

    def test_create_draft_order(self):
        """Test creating draft order."""
        customer_id = uuid4()
        order = Order(customer_id=customer_id)
        self.assertEqual(order.status, OrderStatus.DRAFT)
        self.assertEqual(order.customer_id, customer_id)
        self.assertEqual(order.total_amount, Decimal("0.00"))

    def test_add_item_to_draft_order(self):
        """Test adding item to draft order."""
        order = Order(customer_id=uuid4())
        product_id = uuid4()
        order.add_item(product_id, quantity=2, price=Decimal("50.00"))
        self.assertEqual(len(order.items), 1)
        self.assertEqual(order.total_amount, Decimal("100.00"))

    def test_cannot_add_item_to_non_draft_order(self):
        """Test that items can only be added to draft orders."""
        order = Order(customer_id=uuid4())
        order.add_item(uuid4(), quantity=1, price=Decimal("50.00"))
        order.confirm()
        with self.assertRaises(ValueError):
            order.add_item(uuid4(), quantity=1, price=Decimal("50.00"))

    def test_confirm_order(self):
        """Test confirming order."""
        order = Order(customer_id=uuid4())
        order.add_item(uuid4(), quantity=1, price=Decimal("50.00"))
        order.confirm()
        self.assertEqual(order.status, OrderStatus.PENDING)

    def test_cannot_confirm_empty_order(self):
        """Test that empty order cannot be confirmed."""
        order = Order(customer_id=uuid4())
        with self.assertRaises(ValueError):
            order.confirm()

    def test_mark_order_as_paid(self):
        """Test marking order as paid."""
        order = Order(customer_id=uuid4())
        order.add_item(uuid4(), quantity=1, price=Decimal("50.00"))
        order.confirm()
        order.mark_paid()
        self.assertEqual(order.status, OrderStatus.PAID)

    def test_cannot_mark_non_pending_order_as_paid(self):
        """Test that only pending orders can be marked as paid."""
        order = Order(customer_id=uuid4())
        with self.assertRaises(ValueError):
            order.mark_paid()

    def test_cancel_order(self):
        """Test canceling order."""
        order = Order(customer_id=uuid4())
        order.cancel()
        self.assertEqual(order.status, OrderStatus.CANCELLED)

    def test_cannot_cancel_paid_order(self):
        """Test that paid orders cannot be canceled."""
        order = Order(customer_id=uuid4())
        order.add_item(uuid4(), quantity=1, price=Decimal("50.00"))
        order.confirm()
        order.mark_paid()
        with self.assertRaises(ValueError):
            order.cancel()


class WalletTest(TestCase):
    """Tests for Wallet aggregate."""

    def test_create_wallet(self):
        """Test creating wallet."""
        customer_id = uuid4()
        wallet = Wallet(customer_id=customer_id)
        self.assertEqual(wallet.balance, Decimal("0.00"))
        self.assertEqual(wallet.customer_id, customer_id)

    def test_credit_to_wallet(self):
        """Test crediting to wallet."""
        wallet = Wallet(customer_id=uuid4())
        transaction = wallet.credit(Decimal("100.00"))
        self.assertEqual(wallet.balance, Decimal("100.00"))
        self.assertEqual(transaction.transaction_type, TransactionType.CREDIT)
        self.assertEqual(transaction.amount, Decimal("100.00"))

    def test_debit_from_wallet(self):
        """Test debiting from wallet."""
        wallet = Wallet(customer_id=uuid4())
        wallet.credit(Decimal("100.00"))
        transaction = wallet.debit(Decimal("50.00"))
        self.assertEqual(wallet.balance, Decimal("50.00"))
        self.assertEqual(transaction.transaction_type, TransactionType.DEBIT)

    def test_debit_insufficient_balance_fails(self):
        """Test that debit with insufficient balance fails."""
        wallet = Wallet(customer_id=uuid4())
        wallet.credit(Decimal("50.00"))
        with self.assertRaises(ValueError) as context:
            wallet.debit(Decimal("100.00"))
        self.assertIn("Insufficient balance", str(context.exception))

    def test_negative_credit_fails(self):
        """Test that negative credit amount fails."""
        wallet = Wallet(customer_id=uuid4())
        with self.assertRaises(ValueError):
            wallet.credit(Decimal("-10.00"))

    def test_negative_debit_fails(self):
        """Test that negative debit amount fails."""
        wallet = Wallet(customer_id=uuid4())
        with self.assertRaises(ValueError):
            wallet.debit(Decimal("-10.00"))

    def test_calculate_balance_from_transactions(self):
        """Test calculating balance from transactions."""
        wallet = Wallet(customer_id=uuid4())
        wallet.credit(Decimal("100.00"))
        wallet.debit(Decimal("30.00"))
        wallet.credit(Decimal("20.00"))
        calculated = wallet.calculate_balance_from_transactions()
        self.assertEqual(calculated, Decimal("90.00"))
        self.assertEqual(calculated, wallet.balance)

