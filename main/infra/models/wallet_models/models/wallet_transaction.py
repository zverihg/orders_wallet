from django.db import models
from uuid import uuid4
from enum import Enum
from main.infra.models.service_models.models.base_timestamp_model import TimeStampedModel
from .wallet import Wallet


class TransactionType(Enum):
    """Тип транзакции кошелька."""
    DEBIT = "DEBIT"  # Списание
    CREDIT = "CREDIT"  # Начисление


class WalletTransaction(TimeStampedModel):

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.PROTECT,
        related_name="transactions",
    )
    transaction_type = models.CharField(choices=TransactionType)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.TextField(default="")

    class Meta:
        indexes = [
            models.Index(fields=("wallet",)),
            models.Index(fields=("wallet", "created_at")),
        ]
