from django.db import models

from .base_timestamp_model import TimeStampedModel


OPERATION_TYPE = (
    ("CREATE_ORDER", "Создание заказа"),
    ("CAPTURE_PAYMENT", "Подтверждение оплаты"),
    ("REFUND_ORDER", "Возврат заказа"),
)


class IdempotencyKey(TimeStampedModel):
    key = models.CharField(max_length=255)
    user_id = models.UUIDField(null=True, blank=True)
    operation = models.CharField(choices=OPERATION_TYPE)
    request_hash = models.CharField(max_length=255)
    response_payload = models.JSONField()

    class Meta:
        unique_together = [("key", "user_id", "operation")]
        indexes = [
            models.Index(fields=("request_hash",)),
            models.Index(fields=("key", "user_id", "operation")),
        ]