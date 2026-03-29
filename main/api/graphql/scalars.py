from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from ariadne import ScalarType

decimal_scalar = ScalarType("Decimal")
uuid_scalar = ScalarType("UUID")
datetime_scalar = ScalarType("DateTime")


@decimal_scalar.serializer
def serialize_decimal(value):
    return str(value)


@decimal_scalar.value_parser
def parse_decimal_value(value):
    return Decimal(str(value))


@uuid_scalar.serializer
def serialize_uuid(value):
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, str):
        try:
            UUID(value)
            return value
        except (ValueError, TypeError):
            return str(value)
    return str(value)


@uuid_scalar.value_parser
def parse_uuid_value(value):
    if isinstance(value, UUID):
        return value
    return UUID(str(value))


@uuid_scalar.literal_parser
def parse_uuid_literal(ast):
    return UUID(str(ast.value))


@datetime_scalar.serializer
def serialize_datetime(value):
    if value is None:
        return None
    if isinstance(value, UUID):
        raise ValueError(f"Expected datetime, got UUID: {value}")
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


@datetime_scalar.value_parser
def parse_datetime_value(value):
    if value is None:
        return None
    if isinstance(value, UUID):
        raise ValueError(f"Expected datetime string, got UUID: {value}")
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    return value
