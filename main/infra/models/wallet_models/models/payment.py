from __future__ import annotations
from uuid import uuid4
from django.db import models

from main.infra.models.service_models.models.base_timestamp_model import TimeStampedModel

from main.infra.models.order_models.models import Order


PAYMENT_TYPE = (
    ("CAPTURE_ORDER", "Оплата заказа"),
    ("REFUND_ORDER", "Возврат оплаты"),
)

class Payment(TimeStampedModel):


    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    order = models.ForeignKey(
        Order,
        on_delete=models.PROTECT,
        related_name="payments",
    )

    pay_type = models.CharField(
        choices=PAYMENT_TYPE,
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        indexes = [
            models.Index(fields=("order",)),
        ]
