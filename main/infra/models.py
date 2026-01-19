from __future__ import annotations

from uuid import uuid4

from django.db import models


PAYMENT_TYPE = (
    ("CAPTURE_ORDER", "Оплата заказа"),
    ("REFUND_ORDER", "Возврат оплаты"),
)

OPERATION_TYPE = (
    ("CREATE_ORDER", "Создание заказа"),
    ("CAPTURE_PAYMENT", "Подтверждение оплаты"),
    ("REFUND_ORDER", "Возврат заказа"),
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class CustomerORM(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=("id",)),
        ]


class WalletORM(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    customer = models.OneToOneField(
        CustomerORM,
        on_delete=models.PROTECT,
        related_name="wallet",
    )
    # Balance is calculated from events, not stored

    class Meta:
        indexes = [
            models.Index(fields=("customer",)),
        ]


class WalletTransactionORM(TimeStampedModel):
    TRANSACTION_TYPE_CHOICES = (
        ("DEBIT", "Списание"),
        ("CREDIT", "Начисление"),
    )

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    wallet = models.ForeignKey(
        WalletORM,
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


class OrderORM(TimeStampedModel):

    STATUS_CHOICES = (
        ("DRAFT", "Черновик"),
        ("PENDING", "В обработке"),
        ("PAID", 'Оплачен'),
        ("REFUNDED", 'Возврат'),
        ("CANCELLED", 'Отменён'),
    )

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    customer = models.ForeignKey(
        CustomerORM,
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


class OrderItemORM(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    order = models.ForeignKey(
        OrderORM,
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


class PaymentORM(TimeStampedModel):


    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    order = models.ForeignKey(
        OrderORM,
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


class IdempotencyKey(TimeStampedModel):
    key = models.CharField(max_length=255)
    user_id = models.UUIDField(null=True, blank=True)  # Temporarily nullable for migration
    operation = models.CharField(choices=OPERATION_TYPE)
    request_hash = models.CharField(max_length=255)
    response_payload = models.JSONField()

    class Meta:
        unique_together = [("key", "user_id", "operation")]
        indexes = [
            models.Index(fields=("request_hash",)),
            models.Index(fields=("key", "user_id", "operation")),
        ]