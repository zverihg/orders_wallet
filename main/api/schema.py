"""
GraphQL schema definition using Ariadne.
"""
from ariadne import (
    QueryType,
    MutationType,
    ObjectType,
    make_executable_schema,
    ScalarType,
)
from decimal import Decimal
from uuid import UUID
from datetime import datetime
from pathlib import Path

# Import services - services.py is a module, not a package
# Import directly from the file to avoid conflict with services/ directory
import importlib.util
import sys
import logging
import json
import time

logger = logging.getLogger(__name__)

# Get the services.py file path
services_file = Path(__file__).parent.parent / "services.py"
spec = importlib.util.spec_from_file_location("main_services_module", services_file)
services_module = importlib.util.module_from_spec(spec)
sys.modules["main_services_module"] = services_module
spec.loader.exec_module(services_module)

OrderService = services_module.OrderService
WalletService = services_module.WalletService

# Import RefundService from services/compensation.py
compensation_file = Path(__file__).parent.parent / "services" / "compensation.py"
compensation_spec = importlib.util.spec_from_file_location("main_services_compensation", compensation_file)
compensation_module = importlib.util.module_from_spec(compensation_spec)
compensation_spec.loader.exec_module(compensation_module)
RefundService = compensation_module.RefundService

# Load schema from file
type_defs = """
    scalar DateTime
    scalar Decimal
    scalar UUID

    type Query {
        order(id: UUID!): Order
        ordersByCustomer(customerId: UUID!, limit: Int = 50, offset: Int = 0): OrdersPage!
        walletBalance(customerId: String!): WalletBalance!
    }

    type OrdersPage {
        orders: [Order!]!
        totalCount: Int!
        hasMore: Boolean!
    }

    type Mutation {
        createOrder(input: CreateOrderInput!): CreateOrderPayload!
        capturePayment(orderId: UUID!): CapturePaymentPayload!
        refundOrder(orderId: UUID!): RefundOrderPayload!
    }

    input CreateOrderInput {
        customerId: String!
        items: [OrderItemInput!]!
    }

    input OrderItemInput {
        productId: String!
        quantity: Int!
        price: Decimal!
    }

    type CreateOrderPayload {
        orderId: String!
        status: String!
    }

    type CapturePaymentPayload {
        orderId: UUID!
        status: String!
        amountDebited: Decimal!
        bonusCredited: Decimal!
    }

    type RefundOrderPayload {
        orderId: UUID!
        status: String!
        amountRefunded: Decimal!
    }

    type Order {
        id: UUID!
        customerId: UUID!
        status: String!
        totalAmount: Decimal!
        items: [OrderItem!]!
        createdAt: DateTime!
    }

    type OrderItem {
        productId: UUID!
        quantity: Int!
        price: Decimal!
        subtotal: Decimal!
    }

    type WalletBalance {
        customerId: String!
        balance: Decimal!
    }
"""

query = QueryType()
mutation = MutationType()
order = ObjectType("Order")
order_item = ObjectType("OrderItem")


@query.field("order")
def resolve_order(_, info, id: str):
    """Resolve order query."""
    order_service = OrderService()
    order_domain = order_service.get_order(UUID(id))
    if not order_domain:
        return None
    return _order_to_dict(order_domain)


@query.field("ordersByCustomer")
def resolve_orders_by_customer(_, info, customerId: str, limit: int = 50, offset: int = 0):
    """Resolve orders by customer query with pagination."""
    # Validate pagination limits
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 1
    if offset < 0:
        offset = 0

    order_service = OrderService()
    orders = order_service.get_orders_by_customer(UUID(customerId), limit=limit + 1, offset=offset)
    
    has_more = len(orders) > limit
    if has_more:
        orders = orders[:limit]

    # Get total count (optimized query)
    from main.infra.models import OrderORM
    total_count = OrderORM.objects.filter(customer_id=UUID(customerId)).count()

    return {
        "orders": [_order_to_dict(order) for order in orders],
        "totalCount": total_count,
        "hasMore": has_more,
    }


@query.field("walletBalance")
def resolve_wallet_balance(_, info, customerId: str):
    """Resolve wallet balance query."""
    # #region agent log
    try:
        log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H3", "location": "schema.py:162", "message": "resolve_wallet_balance_entry", "data": {"customer_id": customerId}, "timestamp": int(time.time() * 1000)}
        with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except: pass
    # #endregion
    wallet_service = WalletService()
    try:
        result = wallet_service.get_balance(customerId)
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H3", "location": "schema.py:169", "message": "resolve_wallet_balance_success", "data": {"balance": str(result.get("balance", "N/A"))}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        return result
    except Exception as e:
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H3", "location": "schema.py:175", "message": "resolve_wallet_balance_exception", "data": {"exception_type": type(e).__name__, "exception_msg": str(e)}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        raise


@mutation.field("createOrder")
def resolve_create_order(_, info, input: dict):
    """Resolve create order mutation."""
    # #region agent log
    try:
        log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H1", "location": "schema.py:169", "message": "resolve_create_order_entry", "data": {"customer_id": input.get("customerId"), "items_count": len(input.get("items", []))}, "timestamp": int(time.time() * 1000)}
        with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except: pass
    # #endregion
    order_service = OrderService()
    logger.warning(f"Order mutation: {input}")
    try:
        order_id = order_service.create_order(
            customer_id=input["customerId"],
            items=input["items"],
        )
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H1", "location": "schema.py:177", "message": "resolve_create_order_success", "data": {"order_id": str(order_id)}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        return {
            "orderId": str(order_id),
            "status": "DRAFT",
        }
    except Exception as e:
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H1", "location": "schema.py:186", "message": "resolve_create_order_exception", "data": {"exception_type": type(e).__name__, "exception_msg": str(e)}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        raise


@mutation.field("capturePayment")
def resolve_capture_payment(_, info, orderId: str):
    """Resolve capture payment mutation."""
    # #region agent log
    try:
        log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "schema.py:183", "message": "resolve_capture_payment_entry", "data": {"order_id": orderId}, "timestamp": int(time.time() * 1000)}
        with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except: pass
    # #endregion
    order_service = OrderService()
    try:
        result = order_service.capture_payment(UUID(orderId))
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "schema.py:190", "message": "resolve_capture_payment_success", "data": {"status": result.get("status", "N/A")}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        # Convert UUID to string to avoid serialization issues
        # The UUID scalar parser will convert it back to UUID if needed
        order_id = result["order_id"]
        order_id_str = str(order_id) if isinstance(order_id, UUID) else order_id
        
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "schema.py:254", "message": "returning_capture_payment_result", "data": {"order_id_type": type(order_id).__name__, "order_id_str_type": type(order_id_str).__name__, "order_id_str": order_id_str}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        
        return {
            "orderId": order_id_str,  # String - UUID scalar will handle parsing
            "status": result["status"],
            "amountDebited": str(result["amount_debited"]),
            "bonusCredited": str(result["bonus_credited"]),
        }
    except Exception as e:
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "schema.py:201", "message": "resolve_capture_payment_exception", "data": {"exception_type": type(e).__name__, "exception_msg": str(e)}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        raise


@mutation.field("refundOrder")
def resolve_refund_order(_, info, orderId: str):
    """Resolve refund order mutation."""
    refund_service = RefundService()
    result = refund_service.refund_order(UUID(orderId))
    # Convert UUID to string to avoid serialization issues
    order_id = result["order_id"]
    order_id_str = str(order_id) if isinstance(order_id, UUID) else order_id
    
    return {
        "orderId": order_id_str,  # String - UUID scalar will handle parsing
        "status": result["status"],
        "amountRefunded": str(result["amount_refunded"]),
    }


@order.field("items")
def resolve_order_items(order_dict, info):
    """Resolve order items."""
    return order_dict.get("items", [])


def _order_to_dict(order_domain) -> dict:
    """Convert domain order to dict for GraphQL."""
    return {
        "id": str(order_domain.id),
        "customerId": str(order_domain.customer_id),
        "status": order_domain.status.value,
        "totalAmount": str(order_domain.total_amount),
        "items": [
            {
                "productId": str(item.product_id),
                "quantity": item.quantity,
                "price": str(item.price),
                "subtotal": str(item.subtotal),
            }
            for item in order_domain.items
        ],
        "createdAt": None,  # Will be added from ORM if needed
    }


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
    # #region agent log
    try:
        log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "schema.py:327", "message": "serialize_uuid_called", "data": {"value_type": type(value).__name__, "value": str(value) if hasattr(value, '__str__') else repr(value)}, "timestamp": int(time.time() * 1000)}
        with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except: pass
    # #endregion
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
    # #region agent log
    try:
        log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "schema.py:381", "message": "serialize_datetime_called", "data": {"value_type": type(value).__name__, "is_uuid": isinstance(value, UUID), "is_datetime": isinstance(value, datetime)}, "timestamp": int(time.time() * 1000)}
        with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except: pass
    # #endregion
    # Don't try to serialize UUID objects as datetime
    if isinstance(value, UUID):
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "schema.py:391", "message": "datetime_serializer_received_uuid", "data": {"value": str(value)}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        raise ValueError(f"Expected datetime, got UUID: {value}")
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


@datetime_scalar.value_parser
def parse_datetime_value(value):
    """Parse DateTime from string."""
    # #region agent log
    try:
        log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "schema.py:365", "message": "parse_datetime_value_called", "data": {"value_type": type(value).__name__, "is_uuid": isinstance(value, UUID)}, "timestamp": int(time.time() * 1000)}
        with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except: pass
    # #endregion
    # Don't try to parse UUID objects as datetime
    if isinstance(value, UUID):
        # #region agent log
        try:
            log_entry = {"sessionId": "debug-session", "runId": "run1", "hypothesisId": "H4", "location": "schema.py:375", "message": "datetime_parser_received_uuid", "data": {"value": str(value)}, "timestamp": int(time.time() * 1000)}
            with open("/home/zverihg/Documents/orders_wallet/.cursor/debug.log", "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except: pass
        # #endregion
        raise ValueError(f"Expected datetime string, got UUID: {value}")
    if isinstance(value, str):
        return datetime.fromisoformat(value.replace('Z', '+00:00'))
    return value


orders_page = ObjectType("OrdersPage")

@orders_page.field("orders")
def resolve_orders_page_orders(page_dict, info):
    """Resolve orders from page."""
    return page_dict.get("orders", [])

# Create executable schema
schema = make_executable_schema(
    type_defs,
    query,
    mutation,
    order,
    order_item,
    orders_page,
    datetime_scalar,
    decimal_scalar,
    uuid_scalar,
)

