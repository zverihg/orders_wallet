"""
Event store for Event Sourcing (lightweight).
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from django.db import models

from main.domain.events import DomainEvent, EventVersion
from main.domain.wallet import TransactionType
from main.infra.models import TimeStampedModel, WalletORM
import logging


logger = logging.getLogger(__name__)


class EventStore(TimeStampedModel):
    """Event store for domain events."""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    aggregate_id = models.UUIDField()
    aggregate_type = models.CharField(max_length=50)  # "Order" or "Wallet"
    event_type = models.CharField(max_length=100)
    event_version = models.CharField(max_length=10, default=EventVersion.V1.value)
    event_data = models.JSONField()
    sequence_number = models.BigIntegerField()  # For ordering events

    class Meta:
        indexes = [
            models.Index(fields=("aggregate_id", "aggregate_type")),
            models.Index(fields=("aggregate_id", "aggregate_type", "sequence_number")),
        ]
        ordering = ["sequence_number"]


class EventStoreRepository:
    """Repository for event store."""

    def save_event(self, event: DomainEvent, aggregate_type: str) -> None:
        """Save domain event to store."""
        # Get next sequence number

        last_event = (
            EventStore.objects
            .filter(aggregate_id=event.aggregate_id, aggregate_type=aggregate_type)
            .order_by("-sequence_number")
            .first()
        )
        sequence_number = (last_event.sequence_number + 1) if last_event else 1

        # Serialize event
        event_data = self._serialize_event(event)


        EventStore.objects.create(
            aggregate_id=event.aggregate_id,
            aggregate_type=aggregate_type,
            event_type=event.event_type,
            event_version=event.version.value,
            event_data=event_data,
            sequence_number=sequence_number,
        )

    def get_events(self, aggregate_id: UUID, aggregate_type: str) -> list[dict]:
        """Get all events for aggregate."""
        events = (
            EventStore.objects
            .filter(aggregate_id=aggregate_id, aggregate_type=aggregate_type)
            .order_by("sequence_number")
        )
        return [self._deserialize_event(e) for e in events]

    def calculate_wallet_balance(self, wallet: WalletORM) -> Decimal:
        """Calculate wallet balance from events."""
        balance = Decimal("0.00")

        events = wallet.transactions.all()

        for event in events:
            
            if event.transaction_type == TransactionType.DEBIT:
                balance -= event.amount
            elif event.transaction_type == TransactionType.CREDIT:
                balance += event.amount
        
        return balance

    def _serialize_event(self, event: DomainEvent) -> dict:
        """Serialize event to dict."""
        data = {
            "event_id": str(event.event_id),
            "aggregate_id": str(event.aggregate_id),
            "event_type": event.event_type,
            "version": event.version.value,
        }
        # Add event-specific fields
        for key, value in event.__dict__.items():
            if key not in ("event_id", "aggregate_id", "event_type", "version", "occurred_at"):
                if isinstance(value, UUID):
                    data[key] = str(value)
                elif hasattr(value, "__dict__"):
                    data[key] = str(value)
                elif isinstance(value, Decimal):
                    data[key] = str(value)
                else:
                    data[key] = value

        return data

    def _deserialize_event(self, event_orm: EventStore) -> dict:
        """Deserialize event from store."""
        return {
            "id": str(event_orm.id),
            "aggregate_id": str(event_orm.aggregate_id),
            "event_type": event_orm.event_type,
            "version": event_orm.event_version,
            "data": event_orm.event_data,
            "sequence_number": event_orm.sequence_number,
            "occurred_at": event_orm.created_at.isoformat(),
        }

