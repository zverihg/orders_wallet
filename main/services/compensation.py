"""
Compensation (Saga) patterns for order refunds.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from django.db import transaction
from django.utils import timezone

from main.domain.order import OrderStatus
from main.domain.events import OrderRefunded
from main.infra.repositories import OrderRepository, WalletRepository
from main.infra.outbox import OutboxRepository
from infra.models.event_store_models.models.event_store import EventStoreRepository
from main.infra.locks import wallet_lock


class RefundService:
    """Service for handling order refunds (compensation)."""

    def __init__(
        self,
        order_repo: OrderRepository | None = None,
        wallet_repo: WalletRepository | None = None,
        outbox_repo: OutboxRepository | None = None,
        event_store_repo: EventStoreRepository | None = None,
    ):
        self.order_repo = order_repo or OrderRepository()
        self.wallet_repo = wallet_repo or WalletRepository()
        self.outbox_repo = outbox_repo or OutboxRepository()
        self.event_store_repo = event_store_repo or EventStoreRepository()

    @transaction.atomic
    def refund_order(self, order_id: UUID) -> dict:
        """Refund order (compensate payment)."""
        # Get order
        order = self.order_repo.get_by_id(order_id)
        if not order:
            raise ValueError(f"Order {order_id} not found")

        if order.status != OrderStatus.PAID:
            raise ValueError(f"Order {order_id} is not in PAID status")

        # Get wallet
        wallet = self.wallet_repo.get_by_customer_id(order.customer_id)
        if not wallet:
            raise ValueError(f"Wallet not found for customer {order.customer_id}")

        # Use distributed lock
        with wallet_lock(wallet.id):
            # Reload wallet within lock
            wallet = self.wallet_repo.get_by_id(wallet.id)

            # Refund payment (credit back)
            wallet.credit(
                amount=order.total_amount,
                order_id=order.id,
                description=f"Refund for order {order.id}",
            )

            # Deduct bonus (compensate bonus)
            bonus_amount = order.total_amount * Decimal("0.05")
            if wallet.balance >= bonus_amount:
                wallet.debit(
                    amount=bonus_amount,
                    order_id=order.id,
                    description=f"Bonus compensation for refunded order {order.id}",
                )

            # Mark order as refunded
            order.mark_refunded()

            # Save wallet and order
            self.wallet_repo.save(wallet)
            self.order_repo.save(order)

            # Emit OrderRefunded event
            event = OrderRefunded(
                event_id=uuid4(),
                aggregate_id=order_id,
                event_type="OrderRefunded",
                amount=order.total_amount,
            )
            event.occurred_at = timezone.now().isoformat()
            self.event_store_repo.save_event(event, "Order")
            self.outbox_repo.add_event(event, "Order")

        return {
            "order_id": order.id,
            "status": order.status.value,
            "amount_refunded": order.total_amount,
        }

