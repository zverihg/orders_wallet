"""
Read models (projections) for CQRS.
"""
from __future__ import annotations

from decimal import Decimal
from uuid import UUID, uuid4

from django.db import models

from main.infra.models import TimeStampedModel


class OrderSummary(TimeStampedModel):
    """Read model for order summary (denormalized for fast reads)."""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    customer_id = models.UUIDField()
    customer_name = models.CharField(max_length=255)
    status = models.CharField(max_length=50)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    items_count = models.IntegerField(default=0)
    created_at_read = models.DateTimeField()  # Denormalized from write model

    class Meta:
        indexes = [
            models.Index(fields=("customer_id", "status")),
            models.Index(fields=("customer_id", "-created_at_read")),
            models.Index(fields=("status",)),
        ]


class WalletView(TimeStampedModel):
    """Read model for wallet view (denormalized for fast reads)."""
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    customer_id = models.UUIDField(unique=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2)
    transactions_count = models.IntegerField(default=0)
    last_transaction_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=("customer_id",)),
        ]

