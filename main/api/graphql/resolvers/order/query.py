from __future__ import annotations

from ariadne import QueryType

from main.domain.order import get_order_by_id, get_orders_by_customer

from ..errors import run_with_hybrid_errors

query = QueryType()


@query.field("getOrder")
def resolve_get_order(_, info, id):
    return run_with_hybrid_errors(lambda: get_order_by_id(id))


@query.field("OrdersByCustomer")
def resolve_orders_by_customer(_, info, customerId, limit=50, offset=0):
    return run_with_hybrid_errors(
        lambda: get_orders_by_customer(customerId, limit=limit, offset=offset)
    )
