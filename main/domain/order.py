"""
Domain model for Order aggregate.
"""
from __future__ import annotations

from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4


class OrderStatus(str, Enum):
    """Order status enumeration."""
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    PAID = "PAID"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class OrderItem:
    """Order line item value object."""
    
    def __init__(self, product_id: UUID, quantity: int, price: Decimal):
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        if price < 0:
            raise ValueError("Price must be non-negative")
        
        self.product_id = product_id
        self.quantity = quantity
        self.price = price
    
    @property
    def subtotal(self) -> Decimal:
        """Calculate item subtotal."""
        return self.price * self.quantity


class Order:
    """Order aggregate root."""
    
    def __init__(
        self,
        id: UUID | None = None,
        customer_id: UUID | None = None,
        items: list[OrderItem] | None = None,
        status: OrderStatus = OrderStatus.DRAFT,
    ):
        self.id = id or uuid4()
        self.customer_id = customer_id
        self._items = items or []
        self._status = status
    
    @property
    def items(self) -> list[OrderItem]:
        """Get order items (immutable)."""
        return list(self._items)
    
    @property
    def status(self) -> OrderStatus:
        """Get order status."""
        return self._status
    
    @property
    def total_amount(self) -> Decimal:
        """Calculate total order amount."""
        return sum(item.subtotal for item in self._items)
    
    def add_item(self, product_id: UUID, quantity: int, price: Decimal) -> None:
        """Add item to order."""
        if self._status != OrderStatus.DRAFT:
            raise ValueError("Can only add items to draft orders")
        
        item = OrderItem(product_id, quantity, price)
        self._items.append(item)
    
    def confirm(self) -> None:
        """Confirm order (move from DRAFT to PENDING)."""
        if self._status != OrderStatus.DRAFT:
            raise ValueError("Can only confirm draft orders")
        if not self._items:
            raise ValueError("Cannot confirm empty order")
        
        self._status = OrderStatus.PENDING
    
    def mark_paid(self) -> None:
        """Mark order as paid."""
        if self._status != OrderStatus.PENDING:
            raise ValueError("Can only mark pending orders as paid")
        
        self._status = OrderStatus.PAID
    
    def mark_refunded(self) -> None:
        """Mark order as refunded."""
        if self._status != OrderStatus.PAID:
            raise ValueError("Can only refund paid orders")
        
        self._status = OrderStatus.REFUNDED
    
    def cancel(self) -> None:
        """Cancel order."""
        if self._status in (OrderStatus.PAID, OrderStatus.REFUNDED):
            raise ValueError("Cannot cancel paid or refunded orders")
        
        self._status = OrderStatus.CANCELLED

