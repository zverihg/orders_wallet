from django.db import models
from uuid import uuid4

from main.infra.models.service_models.models.base_timestamp_model import TimeStampedModel


class Customer(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=("id",)),
        ]

