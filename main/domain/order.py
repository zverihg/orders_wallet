"""
Domain model for Order aggregate.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from django.db import transaction

from main.infra.models.wallet_models.models import WalletTransaction
from main.infra.models.customer_models.models import Customer
from main.infra.models.order_models.models import Order
from main.infra.models.order_models.models import OrderItem

from main.domain.wallet import TransactionType

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

    return order.id, order.status

def get_order_by_id(order_id: UUID):
    order = Order.objects.filter(id=order_id).select_related("customer").prefetch_related("items").first()

    items = order.items.all()

    items_dict = [
        {
        "productId":item.product_id,
        "quantity":item.quantity,
        "price":item.price
        }
        for item in items]

    data = {
        "id": order.id,
        "customerId": order.customer_id,
        "status": order.status,
        "totalAmount": order.total_amount,
        "items": items_dict,
        "createdAt": order.created_at,
    }

    return data


def get_orders_by_customer(customerId):

    orders = Order.objects.filter(customer_id=customerId)

    orders_dict = [
        {
        "id":order.id,
        "customerId":order.customer_id,
        "status":order.status,
        "totalAmount":order.total_amount,
        "createdAt":order.created_at,
        }
        for order in orders]

    data = {
        "orders": orders_dict,
        "totalCount": len(orders)
    }

    return data


def capture_payment(orderId):

    order = Order.objects.get(id=orderId)

    wallet = order.customer.wallet

    balance = Decimal(0)
    for wallet_transaction in wallet.transactions.all():
        if wallet_transaction.transaction_type == TransactionType.CREDIT:
            balance += wallet_transaction.amount
        elif wallet_transaction.transaction_type == TransactionType.DEBIT:
            balance -= wallet_transaction.amount
        else:
            pass

    if balance < order.total_amount:
        raise ValueError("Insufficient balance for payment")

    with transaction.atomic():

        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=TransactionType.DEBIT,
            amount=order.total_amount,
            description=f"Payment for order {order.id}",
        )

        order.status = "PAID"
        order.save()

    return {
        "orderId": str(orderId),
        "status": order.status,
        "amountDebited": str(order.total_amount)
    }


def refund_order(orderId:str):

    order = Order.objects.get(id=orderId)
    wallet = order.customer.wallet

    if order.status != "PAID":
        raise ValueError("Order is not paid")

    with transaction.atomic():

        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=TransactionType.CREDIT,
            amount=order.total_amount,
            description=f"Payment for order {order.id}",
        )

        order.status = "REFUNDED"
        order.save()

    return {"orderId": str(orderId), "status": order.status}