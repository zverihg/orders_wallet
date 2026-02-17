"""
GraphQL schema definition using Ariadne.
"""
from ariadne import (
    QueryType,
    MutationType,
    ObjectType,
    make_executable_schema,
    ScalarType,
    load_schema_from_path,
)
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from pathlib import Path

from main.domain.order import (
    create_order,
    get_order_by_id,
    get_orders_by_customer,
    capture_payment,
    refund_order
)

from main.domain.wallet import (
    get_wallet_balance,
    wallet_debit,
    wallet_credit,
)

# Load schema from .graphql files
SCHEMAS_DIR = Path(__file__).parent / "schemas"
type_defs = "\n".join([
    load_schema_from_path(SCHEMAS_DIR / "common"),
    load_schema_from_path(SCHEMAS_DIR / "query"),
    load_schema_from_path(SCHEMAS_DIR / "mutation"),
])

query = QueryType()
mutation = MutationType()
order = ObjectType("Order")
order_item = ObjectType("OrderItem")
orders_by_customer_result = ObjectType("OrdersByCustomerResult")


@query.field("getOrder")
def resolve_getOrder(_, info, id):
    """Resolve order query."""

    order = get_order_by_id(id)

    return order


@query.field("OrdersByCustomer")
def resolve_orders_by_customer(_, info, customerId):
    """Resolve orders by customer query with pagination."""

    data = get_orders_by_customer(customerId)
    return data


@mutation.field("createOrder")
def resolve_create_order(_, info, input: dict):
    """Resolve create order mutation."""

    customer_id = UUID(input["customerId"])
    items_input = input["items"]
    items_list = [
        {
            "productId":UUID(item["productId"]),
            "quantity":item["quantity"],
            "price":Decimal(str(item["price"]))
        }
        for item in items_input
    ]
    order_id, order_status = create_order(customer_id, items_list)

    return {"orderId": str(order_id), "status": order_status}

@query.field("walletBalance")
def resolve_wallet_balance(_, info, customerId: str):
    """Resolve wallet balance query."""

    balance = get_wallet_balance(customerId)

    return {"customerId": customerId, "balance": balance}


@mutation.field("capturePayment")
def resolve_capture_payment(_, info, orderId: str):
    """Resolve capture payment mutation."""

    result = capture_payment(orderId)

    return result

@mutation.field("refundOrder")
def resolve_refund_order(_, info, orderId):
    """Resolve refund order mutation."""

    result = refund_order(orderId)

    return result


@mutation.field("walletDebit")
def resolve_wallet_debit(_, info, input: dict):

    result = wallet_debit(input["customerId"], input["amount"])

    return result

@mutation.field("walletCredit")
def resolve_wallet_credit(_, info, input: dict):

    result = wallet_credit(input["customerId"], input["amount"])

    return result


# TODO delete
@order.field("items")
def resolve_order_items(order_dict, info):
    """Resolve order items."""
    return []


# Define custom scalars
decimal_scalar = ScalarType("Decimal")
uuid_scalar = ScalarType("UUID")
datetime_scalar = ScalarType("DateTime")


@decimal_scalar.serializer
def serialize_decimal(value):
    """Serialize Decimal to string."""
    return str(value)


@decimal_scalar.value_parser
def parse_decimal_value(value):
    """Parse Decimal from string."""
    return Decimal(str(value))


@uuid_scalar.serializer
def serialize_uuid(value):
    """Serialize UUID to string."""
    # Handle both UUID objects and strings
    if isinstance(value, UUID):
        return str(value)
    elif isinstance(value, str):
        # Already a string, validate it's a valid UUID format
        try:
            UUID(value)  # Validate format
            return value
        except (ValueError, TypeError):
            return str(value)
    else:
        return str(value)


@uuid_scalar.value_parser
def parse_uuid_value(value):
    """Parse UUID from string."""
    if isinstance(value, UUID):
        return value
    return UUID(str(value))

@uuid_scalar.literal_parser
def parse_uuid_literal(ast):
    """Parse UUID from GraphQL literal."""
    value = str(ast.value)
    return UUID(value)


@datetime_scalar.serializer
def serialize_datetime(value):
    """Serialize DateTime to ISO format string."""
    if value is None:
        return None
    if isinstance(value, UUID):
        raise ValueError(f"Expected datetime, got UUID: {value}")
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


@datetime_scalar.value_parser
def parse_datetime_value(value):
    """Parse DateTime from string."""

    if value is None:
        return None
    if isinstance(value, UUID):
        raise ValueError(f"Expected datetime string, got UUID: {value}")
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    return value



# Create executable schema
schema = make_executable_schema(
    type_defs,
    query,
    mutation,
    order,
    order_item,
    orders_by_customer_result,
    datetime_scalar,
    decimal_scalar,
    uuid_scalar,
)

