"""
Domain model for Order aggregate.
"""
from __future__ import annotations

from decimal import Decimal
from enum import Enum
from uuid import UUID, uuid4

from django.db import transaction

from main.infra.models.customer_models.models import Customer
from main.infra.models.order_models.models import Order
from main.infra.models.order_models.models import OrderItem



def get_total_amount(items_list) -> Decimal:

    total = Decimal("0.00")

    for item in items_list:
        total += item["price"] * item["quantity"]

    return total


def create_order(customer_id: UUID, items_list):

    with transaction.atomic():
        customer, _ = Customer.objects.get_or_create(
            id=customer_id,
            defaults={"name": str(customer_id)},
        )

        order = Order.objects.create(
            customer=customer,
            total_amount=get_total_amount(items_list),
            status="DRAFT",
        )

        for item in items_list:

            OrderItem.objects.create(
                order=order,
                product_id=item["productId"],
                quantity=item["quantity"],
                price=item["price"],
            )



def get_order_by_id(order_id: UUID):
    return Order.objects.get(id=order_id)