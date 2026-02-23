"""
Доменная модель агрегата Заказ (Order).
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from main.infra.repo import order_repo, customer_repo, wallet_repo
from main.infra.repo.value_objects import CustomerObject, OrderObject, OrderItemObject

def process_items(items_list):

    items = []
    total = Decimal("0.00")

    for item in items_list:

        items.append(
            OrderItemObject(
                product_id=item["productId"],
                quantity=item["quantity"],
                price=item["price"],
            )
        )

        total += item["price"] * item["quantity"]

    return items, total

def create_order(customer_id: UUID, items_list):

    customer_dict = customer_repo.get_customer_by_id(customer_id=customer_id)
    customer = CustomerObject(id = customer_dict["pk"], name = customer_dict["name"])

    items, total_amount = process_items(items_list)

    order = OrderObject(
        total_amount=total_amount,
        status="DRAFT",
        items=items,
        customer=customer,
    )

    order_id, order_status = order_repo.create(order)

    return order_id, order_status

def get_order_by_id(order_id: UUID):

    order = order_repo.get_order_by_id(order_id=order_id)
    return order

def get_orders_by_customer(customer_id):

    orders = order_repo.get_orders_by_customer(customer_id=customer_id)
    return orders

def capture_payment(order_id):

    order = order_repo.get_order_by_id(order_id=order_id)

    customer = order.customer

    balance = wallet_repo.get_wallet_balance(customer_id=customer.pk)

    if balance < order.total_amount:
        raise ValueError("Insufficient balance for payment")

    status = wallet_repo.capture_payment(order_id=order_id)

    return {
        "orderId": order_id,
        "status": status,
        "amountDebited": order.total_amount
    }

def refund_order(order_id:str):

    order = order_repo.get_order_by_id(order_id=order_id)

    if order.status != "PAID":
        raise ValueError("Order is not paid")

    status = wallet_repo.refund_order(order_id=order_id)

    return {"orderId": order_id, "status": status}