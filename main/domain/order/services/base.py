from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from django.core.exceptions import ObjectDoesNotExist

from main.domain.errors import DomainError
from main.infra.models.customer_models.models import Customer
from main.infra.models.order_models.models import Order
from main.infra.models.wallet_models.models import TransactionType, Wallet


class BaseOrderService:
    def _get_customer(self, customer_id: UUID) -> Customer:
        try:
            return Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist as exc:
            raise DomainError(code="CUSTOMER_NOT_FOUND", message="Customer not found") from exc

    def _get_order(self, order_id: UUID) -> Order:
        try:
            return Order.objects.select_related("customer").prefetch_related("items").get(id=order_id)
        except Order.DoesNotExist as exc:
            raise DomainError(code="ORDER_NOT_FOUND", message="Order not found") from exc

    def _get_wallet(self, customer: Customer) -> Wallet:
        try:
            return customer.wallet
        except ObjectDoesNotExist as exc:
            raise DomainError(code="WALLET_NOT_FOUND", message="Wallet not found") from exc

    def _wallet_balance(self, wallet: Wallet) -> Decimal:
        balance = Decimal("0.00")
        for transaction in wallet.transactions.all():
            transaction_type = transaction.transaction_type
            if transaction_type in (TransactionType.CREDIT, TransactionType.CREDIT.value):
                balance += transaction.amount
            elif transaction_type in (TransactionType.DEBIT, TransactionType.DEBIT.value):
                balance -= transaction.amount
        return balance

    def _serialize_item(self, item) -> dict:
        subtotal = item.price * item.quantity
        return {
            "productId": item.product_id,
            "quantity": item.quantity,
            "price": item.price,
            "subtotal": subtotal,
        }

    def _serialize_order(self, order: Order) -> dict:
        return {
            "id": order.id,
            "customerId": order.customer_id,
            "status": order.status,
            "totalAmount": order.total_amount,
            "items": [self._serialize_item(item) for item in order.items.all()],
            "createdAt": order.created_at,
        }
