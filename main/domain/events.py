"""
Domain events for Event Sourcing (lightweight).
"""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from uuid import UUID


class EventVersion(str, Enum):
    """Event version for upcasting."""
    V1 = "1.0"


@dataclass
class DomainEvent:
    """Base domain event."""
    event_id: UUID
    aggregate_id: UUID
    event_type: str
    # version and occurred_at are set in subclasses to avoid dataclass field ordering issues


# Order events
@dataclass
class OrderCreated(DomainEvent):
    """Order created event."""
    customer_id: UUID
    total_amount: Decimal
    items_count: int
    version: EventVersion = EventVersion.V1
    occurred_at: str = ""


@dataclass
class OrderConfirmed(DomainEvent):
    """Order confirmed event."""
    version: EventVersion = EventVersion.V1
    occurred_at: str = ""


@dataclass
class OrderPaid(DomainEvent):
    """Order paid event."""
    amount: Decimal
    version: EventVersion = EventVersion.V1
    occurred_at: str = ""


@dataclass
class OrderRefunded(DomainEvent):
    """Order refunded event."""
    amount: Decimal
    version: EventVersion = EventVersion.V1
    occurred_at: str = ""


@dataclass
class OrderCancelled(DomainEvent):
    """Order cancelled event."""
    version: EventVersion = EventVersion.V1
    occurred_at: str = ""


# Wallet events
@dataclass
class WalletCreated(DomainEvent):
    """Wallet created event."""
    customer_id: UUID
    version: EventVersion = EventVersion.V1
    occurred_at: str = ""


@dataclass
class WalletDebited(DomainEvent):
    """Wallet debited event."""
    amount: Decimal
    new_balance: Decimal
    order_id: UUID | None = None
    description: str = ""
    version: EventVersion = EventVersion.V1
    occurred_at: str = ""


@dataclass
class WalletCredited(DomainEvent):
    """Wallet credited event."""
    amount: Decimal
    new_balance: Decimal
    order_id: UUID | None = None
    description: str = ""
    version: EventVersion = EventVersion.V1
    occurred_at: str = ""

