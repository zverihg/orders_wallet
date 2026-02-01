from django.db import models
from uuid import uuid4

from main.infra.models.service_models.models.base_timestamp_model import TimeStampedModel

from .order import Order


class OrderItem(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name="items",
    )
    product_id = models.UUIDField()
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=("order",)),
        ]

