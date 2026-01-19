"""
Transactional Outbox pattern implementation.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from django.db import models, transaction
from django.db.models import F

from main.domain.events import DomainEvent
from main.infra.models import TimeStampedModel
import logging


logger = logging.getLogger(__name__)


class OutboxEvent(TimeStampedModel):
    """Outbox event for transactional outbox pattern."""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    aggregate_id = models.UUIDField()
    aggregate_type = models.CharField(max_length=50)
    event_type = models.CharField(max_length=100)
    event_data = models.JSONField()
    processed = models.BooleanField(default=False)
    processed_at = models.DateTimeField(null=True, blank=True)
    retry_count = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=("processed", "created_at")),
            models.Index(fields=("aggregate_id", "aggregate_type")),
        ]


class OutboxRepository:
    """Repository for outbox events."""

    @transaction.atomic
    def add_event(self, event: DomainEvent, aggregate_type: str) -> UUID:
        """Add event to outbox (within transaction)."""
        event_data = self._serialize_event(event)

        logger.warning(f"--------------------------------------------{event_data}")
        outbox_event = OutboxEvent.objects.create(
            aggregate_id=event.aggregate_id,
            aggregate_type=aggregate_type,
            event_type=event.event_type,
            event_data=event_data,
        )
        return outbox_event.id

    def get_unprocessed_events(self, limit: int = 100) -> list[OutboxEvent]:
        """Get unprocessed events."""
        return list(
            OutboxEvent.objects
            .filter(processed=False)
            .order_by("created_at")[:limit]
        )

    def mark_processed(self, event_id: UUID) -> None:
        """Mark event as processed."""
        from django.utils import timezone
        OutboxEvent.objects.filter(id=event_id).update(
            processed=True,
            processed_at=timezone.now(),
        )

    def increment_retry(self, event_id: UUID) -> None:
        """Increment retry count."""
        OutboxEvent.objects.filter(id=event_id).update(
            retry_count=F("retry_count") + 1,
        )

    def _serialize_event(self, event: DomainEvent) -> dict:
        """Serialize event to dict."""
        data = {
            "event_id": str(event.event_id),
            "aggregate_id": str(event.aggregate_id),
            "event_type": event.event_type,
            "version": event.version.value,
        }
        for key, value in event.__dict__.items():
            if key not in ("event_id", "aggregate_id", "event_type", "version", "occurred_at"):
                if isinstance(value, UUID):
                    data[key] = str(value)
                elif isinstance(value, Decimal):
                    data[key] = str(value)
                else:
                    data[key] = value
        return data

