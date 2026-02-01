"""
Integration tests for GraphQL API.
"""
import json
from decimal import Decimal

from django.test import TestCase

from main.infra.models.models import WalletORM, WalletTransactionORM
from main.infra.repositories import CustomerRepository

from infra.models.event_store_models.models.event_store import EventStoreRepository

from main.domain.wallet import TransactionType
from main.domain.events import WalletCredited
from uuid import uuid4
from django.utils import timezone


class GraphQLAPITest(TestCase):
    """Integration tests for GraphQL API."""

    def setUp(self):
        """Set up test data."""
        self.customer_repo = CustomerRepository()
        self.customer_id = self.customer_repo.create(
            name="Test Customer",
        )
        # Create wallet for customer (balance will be calculated from events)
        wallet_orm = WalletORM.objects.create(
            customer_id=self.customer_id,
        )
        # Create initial credit transaction to set balance to 1000.00

        WalletTransactionORM.objects.create(
            wallet=wallet_orm,
            transaction_type=TransactionType.CREDIT.value,
            amount=Decimal("1000.00"),
            description="Initial balance",
        )
        # Create corresponding event

        event_store = EventStoreRepository()
        event = WalletCredited(
            event_id=uuid4(),
            aggregate_id=wallet_orm.id,
            event_type="WalletCredited",
            amount=Decimal("1000.00"),
            order_id=None,
            description="Initial balance",
            new_balance=Decimal("1000.00"),
        )
        event.occurred_at = timezone.now().isoformat()
        event_store.save_event(event, "Wallet")

    def test_create_order_mutation(self):
        """Test createOrder mutation."""
        query = """
            mutation {
                createOrder(input: {
                    customerId: "%s"
                    items: [
                        {
                            productId: "%s"
                            quantity: 2
                            price: "100.00"
                        }
                    ]
                }) {
                    orderId
                    status
                }
            }
        """ % (str(self.customer_id), str(uuid4()))

        response = self.client.post(
            "/graphql/",
            data={"query": query},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("data", data)
        self.assertIn("createOrder", data["data"])
        self.assertEqual(data["data"]["createOrder"]["status"], "DRAFT")

    def test_query_order(self):
        """Test order query."""
        # First create an order
        product_id = uuid4()
        create_query = """
            mutation {
                createOrder(input: {
                    customerId: "%s"
                    items: [
                        {
                            productId: "%s"
                            quantity: 1
                            price: "50.00"
                        }
                    ]
                }) {
                    orderId
                }
            }
        """ % (str(self.customer_id), str(product_id))

        create_response = self.client.post(
            "/graphql/",
            data={"query": create_query},
            content_type="application/json",
        )
        create_data = json.loads(create_response.content)
        order_id = create_data["data"]["createOrder"]["orderId"]

        # Then query it
        query = """
            query {
                order(id: "%s") {
                    id
                    customerId
                    status
                    totalAmount
                    items {
                        productId
                        quantity
                        price
                    }
                }
            }
        """ % order_id

        response = self.client.post(
            "/graphql/",
            data={"query": query},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("data", data)
        self.assertIn("order", data["data"])
        self.assertEqual(data["data"]["order"]["status"], "DRAFT")
        self.assertEqual(data["data"]["order"]["totalAmount"], "50.00")

    def test_wallet_balance_query(self):
        """Test walletBalance query."""
        query = """
            query {
                walletBalance(customerId: "%s") {
                    customerId
                    balance
                }
            }
        """ % str(self.customer_id)

        response = self.client.post(
            "/graphql/",
            data={"query": query},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("data", data)
        self.assertIn("walletBalance", data["data"])
        self.assertEqual(data["data"]["walletBalance"]["balance"], "1000.00")

    def test_capture_payment_mutation(self):
        """Test capturePayment mutation."""
        # First create an order
        product_id = uuid4()
        create_query = """
            mutation {
                createOrder(input: {
                    customerId: "%s"
                    items: [
                        {
                            productId: "%s"
                            quantity: 1
                            price: "100.00"
                        }
                    ]
                }) {
                    orderId
                }
            }
        """ % (str(self.customer_id), str(product_id))

        create_response = self.client.post(
            "/graphql/",
            data={"query": create_query},
            content_type="application/json",
        )
        create_data = json.loads(create_response.content)
        order_id = create_data["data"]["createOrder"]["orderId"]

        # Then capture payment
        capture_query = """
            mutation {
                capturePayment(orderId: "%s") {
                    orderId
                    status
                    amountDebited
                    bonusCredited
                }
            }
        """ % order_id

        response = self.client.post(
            "/graphql/",
            data={"query": capture_query},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("data", data)
        if data.get("data") is None and "errors" in data:
            self.fail(f"GraphQL errors: {data['errors']}")
        self.assertIsNotNone(data["data"], f"Response data is None. Full response: {data}")
        self.assertIn("capturePayment", data["data"])
        self.assertEqual(data["data"]["capturePayment"]["status"], "PAID")
        self.assertEqual(data["data"]["capturePayment"]["amountDebited"], "100.00")

