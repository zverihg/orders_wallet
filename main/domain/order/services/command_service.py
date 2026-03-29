from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from django.db import transaction

from main.domain.errors import DomainError
from main.infra.models.order_models.models import Order, OrderItem, OrderStatus

from .base import BaseOrderService


class OrderCommandService(BaseOrderService):
    @transaction.atomic
    def create_order(self, customer_id: UUID, items_list: list[dict]) -> dict:
        customer = self._get_customer(customer_id=customer_id)
        if not items_list:
            raise DomainError(code="ORDER_EMPTY", message="Order must contain at least one item")

        total_amount = Decimal("0.00")
        order_items = []
        for item in items_list:
            quantity = int(item["quantity"])
            price = Decimal(str(item["price"]))
            total_amount += price * quantity
            order_items.append(
                OrderItem(
                    product_id=item["productId"],
                    quantity=quantity,
                    price=price,
                )
            )

        order = Order.objects.create(
            customer=customer,
            total_amount=total_amount,
            status=OrderStatus.DRAFT.value,
        )

        for item in order_items:
            item.order = order
        OrderItem.objects.bulk_create(order_items)

        return {"orderId": order.id, "status": order.status}
