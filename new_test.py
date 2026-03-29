import os
import requests
from uuid import uuid4

# Конфигурация API
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
GRAPHQL_ENDPOINT = f"{API_BASE_URL}/graphql/"


class GraphQLClient:
    """Клиент для работы с GraphQL API."""

    def __init__(self, base_url: str = GRAPHQL_ENDPOINT):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Content-Type": "application/json",
            }
        )

    def execute(
        self,
        query: str,
        variables: dict = None,
        operation_name: str = None,
        idempotency_key: str = None,
        request_id: str = None,
        user_id: str = None,
    ) -> dict:
        """Выполнить GraphQL запрос."""
        payload = {
            "query": query,
        }
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name

        headers = {}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        if request_id:
            headers["X-Request-ID"] = request_id
        if user_id:
            headers["X-User-ID"] = user_id

        response = self.session.post(
            self.base_url,
            json=payload,
            headers=headers,
        )

        response.raise_for_status()
        return response.json()


def create_order(client: GraphQLClient, customer_id: str, items: list) -> str:
    """Тест создания заказа через API."""
    print("Создание заказа через API")

    mutation = """
        mutation CreateOrder($input: CreateOrderInput!) {
            createOrder(input: $input) {
                orderId
                status
            }
        }
    """

    variables = {
        "input": {
            "customerId": customer_id,
            "items": [
                {
                    "productId": item["product_id"],
                    "quantity": item["quantity"],
                    "price": str(item["price"]),
                }
                for item in items
            ],
        }
    }

    try:
        response = client.execute(
            query=mutation,
            variables=variables,
            operation_name="CreateOrder",
            request_id=str(uuid4()),
        )

        if "errors" in response:
            print(False, f"Ошибка: {response['errors']}")
            return None

        result = response["data"]["createOrder"]
        order_id = result["orderId"]
        status = result["status"]

        print(True, f"Заказ создан: {order_id}")
        print(True, f"Статус: {status}")

        return order_id
    except Exception as e:
        print(False, f"Ошибка создания заказа: {e}")
        if hasattr(e, "response") and e.response is not None:
            try:
                error_data = e.response.json()
                print(False, f"Детали ошибки: {error_data}")
            except Exception:
                pass
        return None


def get_order(client: GraphQLClient, order_id: str):
    """Тест получения заказа через API."""
    query = """
        query getOrder($id: UUID!) {
            getOrder(id: $id) {
                id
                customerId
                status
                totalAmount
                items {
                    productId
                    quantity
                    price
                }
                createdAt
            }
        }
    """

    variables = {"id": order_id}

    try:
        response = client.execute(
            query=query,
            variables=variables,
            operation_name="getOrder",
        )

        print(response["data"]["getOrder"])

    except Exception as e:
        print(False, f"Ошибка получения заказа: {e}")
        return None


def get_orders_by_customer(client: GraphQLClient, customer_id: str):
    query = """
        query OrdersByCustomer($customerId: UUID!) {
            OrdersByCustomer(customerId: $customerId) {
                totalCount
                orders {
                    id
                    status
                    totalAmount
                }
            }
        }
    """

    variables = {"customerId": customer_id}

    try:
        response = client.execute(
            query=query,
            variables=variables,
            operation_name="OrdersByCustomer",
        )

        print(response["data"]["OrdersByCustomer"])

    except Exception as e:
        print(False, f"Ошибка получения заказа: {e}")
        return None


def get_balance(client: GraphQLClient, customer_id: str):
    query = """
        query walletBalance($customerId: UUID!) {
            walletBalance(customerId: $customerId) {
                customerId
                balance
            }
        }
    """

    variables = {"customerId": customer_id}

    try:
        response = client.execute(
            query=query,
            variables=variables,
            operation_name="walletBalance",
        )

        print(response["data"]["walletBalance"])

    except Exception as e:
        print(False, f"Ошибка получения заказа: {e}")
        return None


def capture_payment(orderId: str):
    query = """
        mutation capturePayment($orderId: UUID!) {
            capturePayment(orderId: $orderId) {
                orderId
                status
                amountDebited
            }
        }
    """
    variables = {"orderId": orderId}

    try:
        response = client.execute(
            query=query,
            variables=variables,
            operation_name="capturePayment",
        )

        print(response["data"]["capturePayment"])

    except Exception as e:
        print(False, f"Ошибка получения заказа: {e}")
        return None


def refund_order(orderId: str):
    query = """
        mutation refundOrder($orderId: UUID!) {
            refundOrder(orderId: $orderId) {
                orderId
                status
            }
        }
    """
    variables = {"orderId": orderId}

    try:
        response = client.execute(
            query=query,
            variables=variables,
            operation_name="refundOrder",
        )

        print(response["data"]["refundOrder"])

    except Exception as e:
        print(False, f"Ошибка получения заказа: {e}")
        return None


def wallet_debit(client: GraphQLClient, customerId: str, amount: int):
    query = """
        mutation walletDebit($input: walletOperationsInput!) {
            walletDebit(input: $input) {
                status
            }
        }
    """
    variables = {"input": {"customerId": customerId, "amount": amount}}

    try:
        response = client.execute(
            query=query,
            variables=variables,
            operation_name="walletDebit",
        )

        print(response["data"]["walletDebit"])

    except Exception as e:
        print(False, f"Ошибка получения заказа: {e}")
        return None


def wallet_credit(client: GraphQLClient, customerId: str, amount: int):
    query = """
        mutation walletCredit($input: walletOperationsInput!) {
            walletCredit(input: $input) {
                status
            }
        }
    """
    variables = {"input": {"customerId": customerId, "amount": amount}}

    try:
        response = client.execute(
            query=query,
            variables=variables,
            operation_name="walletCredit",
        )

        print(response["data"]["walletCredit"])

    except Exception as e:
        print(False, f"Ошибка получения заказа: {e}")
        return None


if __name__ == "__main__":
    api_url = "http://localhost:8000"
    customer_id = "82c5c163-18bf-4685-9be4-5f3358d056bb"

    items = [
        {"product_id": str(uuid4()), "quantity": 2, "price": "1000.00"},
        {"product_id": str(uuid4()), "quantity": 1, "price": "50.00"},
    ]
    client = GraphQLClient()
    # create_order(client, customer_id, items)

    order_id = "b6a43ac3-bbd7-40ca-bba7-86378a903482"

    # get_order(client, order_id)

    # get_orders_by_customer(client, customer_id)
    get_balance(client, customer_id)
    # capture_payment(order_id)
    # refund_order(order_id)

    wallet_credit(client, customer_id, 5000)

    get_balance(client, customer_id)
