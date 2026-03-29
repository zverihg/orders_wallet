from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import threading

import pytest
from django.conf import settings

from main.api.graphql.resolvers.errors import domain_error_payload
from main.domain.errors import DomainError
from main.domain.order.services import OrderPaymentService, OrderQueryService
from main.domain.wallet.services import WalletCommandService
from main.infra.models.customer_models.models import Customer
from main.infra.models.order_models.models import Order, OrderStatus
from main.infra.models.service_models.models import IdempotencyKey
from main.infra.models.wallet_models.models import TransactionType, Wallet, WalletTransaction


def _create_customer_with_wallet(*, balance: Decimal) -> tuple[Customer, Wallet]:
    customer = Customer.objects.create(name="test-user")
    wallet = Wallet.objects.create(customer=customer)
    WalletTransaction.objects.create(
        wallet=wallet,
        transaction_type=TransactionType.CREDIT.value,
        amount=balance,
        description="Seed balance",
    )
    return customer, wallet


@pytest.mark.django_db
def test_domain_error_payload_uses_code_and_message():
    payload = domain_error_payload(
        status="ERROR",
        error=DomainError(code="WALLET_NOT_FOUND", message="Wallet not found"),
        orderId=None,
    )

    assert payload["status"] == "ERROR"
    assert payload["errorCode"] == "WALLET_NOT_FOUND"
    assert payload["errorMessage"] == "Wallet not found"


@pytest.mark.django_db
def test_capture_payment_is_idempotent_by_key():
    customer, wallet = _create_customer_with_wallet(balance=Decimal("300.00"))
    order = Order.objects.create(
        customer=customer,
        total_amount=Decimal("100.00"),
        status=OrderStatus.DRAFT.value,
    )

    service = OrderPaymentService()
    result_1 = service.capture_payment(order.id, idempotency_key="capture-key-1")
    result_2 = service.capture_payment(order.id, idempotency_key="capture-key-1")

    assert result_1 == result_2
    assert Order.objects.get(id=order.id).status == OrderStatus.PAID.value
    assert WalletTransaction.objects.filter(
        wallet=wallet,
        transaction_type=TransactionType.DEBIT.value,
    ).count() == 1
    assert IdempotencyKey.objects.filter(
        key="capture-key-1",
        operation="CAPTURE_PAYMENT",
    ).count() == 1


@pytest.mark.django_db
def test_wallet_debit_rejects_same_key_with_different_payload():
    customer, _ = _create_customer_with_wallet(balance=Decimal("500.00"))
    service = WalletCommandService()

    service.wallet_debit(customer.id, Decimal("100.00"), idempotency_key="wallet-key-1")

    with pytest.raises(DomainError) as exc_info:
        service.wallet_debit(customer.id, Decimal("200.00"), idempotency_key="wallet-key-1")

    assert exc_info.value.code == "IDEMPOTENCY_KEY_REUSED"


@pytest.mark.django_db
def test_orders_by_customer_limit_offset_pagination():
    customer, _ = _create_customer_with_wallet(balance=Decimal("1000.00"))

    for amount in ("10.00", "20.00", "30.00"):
        Order.objects.create(
            customer=customer,
            total_amount=Decimal(amount),
            status=OrderStatus.DRAFT.value,
        )

    service = OrderQueryService()
    first_page = service.get_orders_by_customer(customer.id, limit=2, offset=0)
    second_page = service.get_orders_by_customer(customer.id, limit=2, offset=2)

    assert first_page["totalCount"] == 3
    assert first_page["limit"] == 2
    assert first_page["offset"] == 0
    assert first_page["hasNextPage"] is True
    assert len(first_page["orders"]) == 2

    assert second_page["totalCount"] == 3
    assert second_page["offset"] == 2
    assert second_page["hasNextPage"] is False
    assert len(second_page["orders"]) == 1


@pytest.mark.django_db(transaction=True)
def test_capture_payment_concurrent_requests_only_one_succeeds():
    if "sqlite" in settings.DATABASES["default"]["ENGINE"]:
        pytest.skip("select_for_update is not reliable on sqlite")

    customer, _ = _create_customer_with_wallet(balance=Decimal("300.00"))
    order = Order.objects.create(
        customer=customer,
        total_amount=Decimal("100.00"),
        status=OrderStatus.DRAFT.value,
    )
    barrier = threading.Barrier(2)

    def run_capture(idempotency_key: str):
        barrier.wait()
        service = OrderPaymentService()
        try:
            service.capture_payment(order.id, idempotency_key=idempotency_key)
            return "ok"
        except DomainError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(
            executor.map(
                run_capture,
                ["capture-concurrent-1", "capture-concurrent-2"],
            )
        )

    assert results.count("ok") == 1
    assert results.count("ORDER_NOT_PAYABLE") == 1
