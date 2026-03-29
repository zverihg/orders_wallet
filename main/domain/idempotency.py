from __future__ import annotations

import hashlib
import json
from uuid import UUID

from main.domain.errors import DomainError
from main.infra.models.service_models.models import IdempotencyKey


def _request_hash(payload: dict) -> str:
    canonical_payload = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()


def run_idempotent(
    *,
    operation: str,
    key: str | None,
    user_id: UUID | None,
    payload: dict,
    handler,
):
    if not key:
        return handler()

    request_hash = _request_hash(payload)
    existing = IdempotencyKey.objects.select_for_update().filter(
        key=key,
        user_id=user_id,
        operation=operation,
    ).first()

    if existing:
        if existing.request_hash != request_hash:
            raise DomainError(
                code="IDEMPOTENCY_KEY_REUSED",
                message="Idempotency key was already used with a different payload",
            )
        return existing.response_payload

    response_payload = handler()
    IdempotencyKey.objects.create(
        key=key,
        user_id=user_id,
        operation=operation,
        request_hash=request_hash,
        response_payload=response_payload,
    )
    return response_payload

