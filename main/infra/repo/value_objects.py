from decimal import Decimal
from uuid import UUID

from dataclasses import dataclass


@dataclass(frozen=True)
class CustomerObject:
    id: UUID
    name: str | None

@dataclass(frozen=True)
class OrderItemObject:
    product_id: UUID
    quantity: int
    price: Decimal

@dataclass(frozen=True)
class OrderObject:

    total_amount: Decimal
    status: str
    items: list[OrderItemObject] | None
    customer: CustomerObject

@dataclass(frozen=True)
class OrderObjectPreView:
    total_amount: Decimal
    status: str
