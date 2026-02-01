from django.db import models
from uuid import uuid4

from main.infra.models.service_models.models.base_timestamp_model import TimeStampedModel

from .wallet import Wallet


class WalletTransaction(TimeStampedModel):
    TRANSACTION_TYPE_CHOICES = (
        ("DEBIT", "Списание"),
        ("CREDIT", "Начисление"),
    )

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    transaction_type = models.CharField(choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    order_id = models.UUIDField(null=True, blank=True)
    description = models.TextField(default="")

    class Meta:
        indexes = [
            models.Index(fields=("wallet",)),
            models.Index(fields=("wallet", "created_at")),
        ]
