"""
Projector for updating read models from events.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID

from django.db import transaction
from django.utils import timezone

from main.domain.events import (
    OrderCreated,
    OrderConfirmed,
    OrderPaid,
    OrderRefunded,
    OrderCancelled,
    WalletCreated,
    WalletDebited,
    WalletCredited,
)
from main.infra.outbox import OutboxRepository
from main.infra.read_models import OrderSummary, WalletView
from main.infra.models import CustomerORM, OrderORM


class Projector:
    """Projector for updating read models from domain events."""

    def __init__(self, outbox_repo: OutboxRepository | None = None):
        self.outbox_repo = outbox_repo or OutboxRepository()

    @transaction.atomic
    def process_outbox_events(self, limit: int = 100) -> int:
        """Process unprocessed outbox events."""
        events = self.outbox_repo.get_unprocessed_events(limit=limit)
        processed_count = 0

        for event_orm in events:
            try:
                self._process_event(event_orm)
                self.outbox_repo.mark_processed(event_orm.id)
                processed_count += 1
            except Exception as e:
                # Increment retry count
                self.outbox_repo.increment_retry(event_orm.id)
                # Log error but continue processing
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    "projector_error",
                    extra={
                        "event_id": str(event_orm.id),
                        "error": str(e),
                    },
                    exc_info=True,
                )

        return processed_count

    def _process_event(self, event_orm) -> None:
        """Process single event."""
        event_data = event_orm.event_data
        event_type = event_orm.event_type

        if event_type == "OrderCreated":
            self._handle_order_created(event_orm.aggregate_id, event_data)
        elif event_type == "OrderConfirmed":
            self._handle_order_confirmed(event_orm.aggregate_id, event_data)
        elif event_type == "OrderPaid":
            self._handle_order_paid(event_orm.aggregate_id, event_data)
        elif event_type == "OrderRefunded":
            self._handle_order_refunded(event_orm.aggregate_id, event_data)
        elif event_type == "OrderCancelled":
            self._handle_order_cancelled(event_orm.aggregate_id, event_data)
        elif event_type == "WalletCreated":
            self._handle_wallet_created(event_orm.aggregate_id, event_data)
        elif event_type == "WalletDebited":
            self._handle_wallet_debited(event_orm.aggregate_id, event_data)
        elif event_type == "WalletCredited":
            self._handle_wallet_credited(event_orm.aggregate_id, event_data)

    def _handle_order_created(self, order_id: UUID, event_data: dict) -> None:
        """Handle OrderCreated event."""
        customer_id = UUID(event_data["customer_id"])
        try:
            customer = CustomerORM.objects.get(id=customer_id)
            customer_name = customer.name
        except CustomerORM.DoesNotExist:
            # Fallback if customer doesn't exist
            customer_name = "Unknown Customer"
        
        OrderSummary.objects.update_or_create(
            id=order_id,
            defaults={
                "customer_id": customer_id,
                "customer_name": customer_name,
                "status": "DRAFT",
                "total_amount": Decimal(str(event_data["total_amount"])),
                "items_count": event_data.get("items_count", 0),
                "created_at_read": timezone.now(),
            }
        )

    def _handle_order_confirmed(self, order_id: UUID, event_data: dict) -> None:
        """Handle OrderConfirmed event."""
        OrderSummary.objects.filter(id=order_id).update(status="PENDING")

    def _handle_order_paid(self, order_id: UUID, event_data: dict) -> None:
        """Handle OrderPaid event."""
        OrderSummary.objects.filter(id=order_id).update(status="PAID")

    def _handle_order_refunded(self, order_id: UUID, event_data: dict) -> None:
        """Handle OrderRefunded event."""
        OrderSummary.objects.filter(id=order_id).update(status="REFUNDED")

    def _handle_order_cancelled(self, order_id: UUID, event_data: dict) -> None:
        """Handle OrderCancelled event."""
        OrderSummary.objects.filter(id=order_id).update(status="CANCELLED")

    def _handle_wallet_created(self, wallet_id: UUID, event_data: dict) -> None:
        """Handle WalletCreated event."""
        customer_id = UUID(event_data["customer_id"])
        WalletView.objects.update_or_create(
            id=wallet_id,
            defaults={
                "customer_id": customer_id,
                "balance": Decimal("0.00"),
                "transactions_count": 0,
            }
        )

    def _handle_wallet_debited(self, wallet_id: UUID, event_data: dict) -> None:
        """Handle WalletDebited event."""
        # Get wallet view or create if doesn't exist
        # Note: customer_id should be set from WalletCreated event, but handle missing case
        try:
            wallet_view = WalletView.objects.get(id=wallet_id)
        except WalletView.DoesNotExist:
            # If wallet view doesn't exist, we need customer_id from wallet
            from main.infra.models import WalletORM
            try:
                wallet_orm = WalletORM.objects.select_related("customer").get(id=wallet_id)
                customer_id = wallet_orm.customer_id
            except WalletORM.DoesNotExist:
                # This should not happen - wallet should exist before debiting
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    "wallet_not_found_for_debit",
                    extra={"wallet_id": str(wallet_id)}
                )
                return  # Skip processing if wallet doesn't exist
            wallet_view = WalletView.objects.create(
                id=wallet_id,
                customer_id=customer_id,
                balance=Decimal("0.00"),
                transactions_count=0,
            )
        
        wallet_view.balance = Decimal(str(event_data["new_balance"]))
        wallet_view.transactions_count += 1
        wallet_view.last_transaction_at = timezone.now()
        wallet_view.save()

    def _handle_wallet_credited(self, wallet_id: UUID, event_data: dict) -> None:
        """Handle WalletCredited event."""
        # Get wallet view or create if doesn't exist
        try:
            wallet_view = WalletView.objects.get(id=wallet_id)
        except WalletView.DoesNotExist:
            # If wallet view doesn't exist, we need customer_id from wallet
            from main.infra.models import WalletORM
            try:
                wallet_orm = WalletORM.objects.select_related("customer").get(id=wallet_id)
                customer_id = wallet_orm.customer_id
            except WalletORM.DoesNotExist:
                # This should not happen - wallet should exist before crediting
                import logging
                logger = logging.getLogger(__name__)
                logger.error(
                    "wallet_not_found_for_credit",
                    extra={"wallet_id": str(wallet_id)}
                )
                return  # Skip processing if wallet doesn't exist
            wallet_view = WalletView.objects.create(
                id=wallet_id,
                customer_id=customer_id,
                balance=Decimal("0.00"),
                transactions_count=0,
            )
        
        wallet_view.balance = Decimal(str(event_data["new_balance"]))
        wallet_view.transactions_count += 1
        wallet_view.last_transaction_at = timezone.now()
        wallet_view.save()

