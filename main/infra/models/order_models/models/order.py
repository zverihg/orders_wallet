from django.db import models
from uuid import uuid4

from main.infra.models.service_models.models.base_timestamp_model import TimeStampedModel

from main.infra.models.customer_models.models import Customer
from enum import Enum


class OrderStatus(Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    PAID = "PAID"
    REFUNDED = "REFUNDED"
    CANCELLED = "CANCELLED"


class Order(TimeStampedModel):

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)

    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(choices=OrderStatus)

    class Meta:
        indexes = [
            models.Index(fields=("customer", "status")),
            models.Index(fields=("customer",)),
        ]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_amount__gte=0),
                name="order_total_amount_gte_0",
            ),
        ]