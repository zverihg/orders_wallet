from django.db import models
from uuid import uuid4

from main.infra.models.service_models.models.base_timestamp_model import TimeStampedModel

from main.infra.models.customer_models.models import Customer

class Wallet(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    customer = models.OneToOneField(
        Customer,
        on_delete=models.PROTECT,
        related_name="wallet",
    )
    # Balance is calculated from events, not stored

    class Meta:
        indexes = [
            models.Index(fields=("customer",)),
        ]
