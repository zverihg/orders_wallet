from django.db import models
from uuid import uuid4

from main.infra.models.service_models.models.base_timestamp_model import TimeStampedModel

from main.infra.models.customer_models.models import Customer


class Order(TimeStampedModel):

    STATUS_CHOICES = (
        ("DRAFT", "Черновик"),
        ("PENDING", "В обработке"),
        ("PAID", 'Оплачен'),
        ("REFUNDED", 'Возврат'),
        ("CANCELLED", 'Отменён'),
    )

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.PROTECT,
        related_name="orders",
    )
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(choices=STATUS_CHOICES)

    class Meta:
        indexes = [
            models.Index(fields=("customer", "status")),
            models.Index(fields=("customer",)),
        ]