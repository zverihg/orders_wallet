from __future__ import annotations

from pathlib import Path

from ariadne import ObjectType, load_schema_from_path, make_executable_schema

from .resolvers import order_mutation, order_query, wallet_mutation, wallet_query
from .scalars import datetime_scalar, decimal_scalar, uuid_scalar

SCHEMAS_DIR = Path(__file__).resolve().parents[1] / "schemas"
type_defs = "\n".join(
    [
        load_schema_from_path(SCHEMAS_DIR / "common"),
        load_schema_from_path(SCHEMAS_DIR / "query"),
        load_schema_from_path(SCHEMAS_DIR / "mutation"),
    ]
)

order = ObjectType("Order")
order_item = ObjectType("OrderItem")
orders_by_customer_result = ObjectType("OrdersByCustomerResult")

schema = make_executable_schema(
    type_defs,
    order_query,
    wallet_query,
    order_mutation,
    wallet_mutation,
    order,
    order_item,
    orders_by_customer_result,
    datetime_scalar,
    decimal_scalar,
    uuid_scalar,
)
