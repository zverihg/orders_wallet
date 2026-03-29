from __future__ import annotations

from uuid import UUID

from django.db import transaction

from main.domain.errors import DomainError
from main.domain.idempotency import run_idempotent
from main.infra.models.order_models.models import Order, OrderStatus
from main.infra.models.wallet_models.models import (
    TransactionType,
    Wallet,
    WalletTransaction,
)

from .base import BaseOrderService


class OrderPaymentService(BaseOrderService):
    @transaction.atomic
    def capture_payment(
        self, order_id: UUID, idempotency_key: str | None = None
    ) -> dict:
        def _capture():
            order = (
                Order.objects.select_for_update()
                .select_related("customer")
                .prefetch_related("items")
                .filter(id=order_id)
                .first()
            )
            if not order:
                raise DomainError(code="ORDER_NOT_FOUND", message="Order not found")

            if order.status not in (OrderStatus.DRAFT.value, OrderStatus.PENDING.value):
                raise DomainError(
                    code="ORDER_NOT_PAYABLE", message="Order is not payable"
                )

            wallet = (
                Wallet.objects.select_for_update()
                .filter(customer=order.customer)
                .first()
            )
            if not wallet:
                raise DomainError(code="WALLET_NOT_FOUND", message="Wallet not found")

            balance = self._wallet_balance(wallet)
            if balance < order.total_amount:
                raise DomainError(
                    code="INSUFFICIENT_BALANCE",
                    message="Insufficient balance for payment",
                )

            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type=TransactionType.DEBIT.value,
                amount=order.total_amount,
                description=f"Payment for order {order.id}",
            )

            order.status = OrderStatus.PAID.value
            order.save(update_fields=["status", "updated_at"])

            return {
                "orderId": order.id,
                "status": order.status,
                "amountDebited": order.total_amount,
            }

        return run_idempotent(
            operation="CAPTURE_PAYMENT",
            key=idempotency_key,
            user_id=None,
            payload={"orderId": str(order_id)},
            handler=_capture,
        )

    @transaction.atomic
    def refund_order(self, order_id: UUID) -> dict:
        order = self._get_order(order_id=order_id)
        if order.status != OrderStatus.PAID.value:
            raise DomainError(code="ORDER_NOT_PAID", message="Order is not paid")

        wallet = self._get_wallet(order.customer)
        WalletTransaction.objects.create(
            wallet=wallet,
            transaction_type=TransactionType.CREDIT.value,
            amount=order.total_amount,
            description=f"Refund for order {order.id}",
        )

        order.status = OrderStatus.REFUNDED.value
        order.save(update_fields=["status", "updated_at"])

        return {
            "orderId": order.id,
            "status": order.status,
            "amountRefunded": order.total_amount,
        }
