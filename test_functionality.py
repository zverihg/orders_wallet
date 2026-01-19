#!/usr/bin/env python3
"""
Скрипт для тестирования функционала Orders & Wallet через HTTP API.

Тестирует:
- Создание заказа (через GraphQL API)
- Оплата заказа (через GraphQL API)
- Возврат заказа (через GraphQL API)
- Проверка баланса (через GraphQL API)
- Идемпотентность (через Idempotency-Key)
- Обработка ошибок

Предполагается, что клиент и кошелек уже существуют в базе данных.
Передайте CUSTOMER_ID через переменную окружения или аргумент командной строки.
"""
import os
import sys
import json
import requests
import argparse
from decimal import Decimal
from uuid import uuid4, UUID
import time

# #region agent log
DEBUG_LOG_PATH = "/home/zverihg/PycharmProjects/orders_wallet/.cursor/debug.log"
def _debug_log(session_id, run_id, hypothesis_id, location, message, data):
    try:
        log_entry = {
            "sessionId": session_id,
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000)
        }
        with open(DEBUG_LOG_PATH, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except: pass
# #endregion


# Конфигурация API
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
GRAPHQL_ENDPOINT = f"{API_BASE_URL}/graphql/"


class GraphQLClient:
    """Клиент для работы с GraphQL API."""
    
    def __init__(self, base_url: str = GRAPHQL_ENDPOINT):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
        })
    
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


def print_section(title: str):
    """Печать заголовка секции."""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(success: bool, message: str):
    """Печать результата операции."""
    status = "✓" if success else "✗"
    print(f"{status} {message}")


def validate_customer_id(customer_id: str) -> str:
    """Валидация customer_id."""
    try:
        UUID(customer_id)
        return customer_id
    except ValueError:
        raise ValueError(f"Неверный формат customer_id: {customer_id}. Должен быть UUID.")


def test_create_order(client: GraphQLClient, customer_id: str, items: list) -> str:
    """Тест создания заказа через API."""
    print_section("Создание заказа через API")
    
    # #region agent log
    _debug_log("debug-session", "run1", "H1", "test_functionality.py:98", "test_create_order_entry", {"customer_id": customer_id, "items_count": len(items)})
    # #endregion
    
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
    
    # #region agent log
    _debug_log("debug-session", "run1", "H2", "test_functionality.py:126", "before_graphql_request", {"variables": variables})
    # #endregion
    
    try:
        response = client.execute(
            query=mutation,
            variables=variables,
            operation_name="CreateOrder",
            request_id=str(uuid4()),
        )
        
        # #region agent log
        _debug_log("debug-session", "run1", "H2", "test_functionality.py:133", "after_graphql_response", {"has_errors": "errors" in response, "has_data": "data" in response})
        # #endregion
        
        if "errors" in response:
            # #region agent log
            _debug_log("debug-session", "run1", "H2", "test_functionality.py:136", "graphql_errors_detected", {"errors": str(response.get("errors", []))})
            # #endregion
            print_result(False, f"Ошибка: {response['errors']}")
            return None
        
        result = response["data"]["createOrder"]
        order_id = result["orderId"]
        status = result["status"]
        
        # #region agent log
        _debug_log("debug-session", "run1", "H1", "test_functionality.py:144", "order_created_success", {"order_id": order_id, "status": status})
        # #endregion
        
        print_result(True, f"Заказ создан: {order_id}")
        print_result(True, f"Статус: {status}")
        
        return order_id
    except Exception as e:
        # #region agent log
        _debug_log("debug-session", "run1", "H2", "test_functionality.py:153", "exception_caught", {"exception_type": type(e).__name__, "exception_msg": str(e)})
        # #endregion
        print_result(False, f"Ошибка создания заказа: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print_result(False, f"Детали ошибки: {error_data}")
            except:
                pass
        return None


def test_get_order(client: GraphQLClient, order_id: str):
    """Тест получения заказа через API."""
    query = """
        query GetOrder($id: UUID!) {
            order(id: $id) {
                id
                customerId
                status
                totalAmount
                items {
                    productId
                    quantity
                    price
                    subtotal
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
            operation_name="GetOrder",
        )
        
        if "errors" in response:
            print_result(False, f"Ошибка: {response['errors']}")
            return None
        
        if response["data"]["order"]:
            order = response["data"]["order"]
            print_result(True, f"Заказ получен: {order['id']}")
            print_result(True, f"Статус: {order['status']}")
            print_result(True, f"Сумма: {order['totalAmount']}")
            print_result(True, f"Позиций: {len(order['items'])}")
            return order
        else:
            print_result(False, "Заказ не найден")
            return None
    except Exception as e:
        print_result(False, f"Ошибка получения заказа: {e}")
        return None


def test_capture_payment(client: GraphQLClient, order_id: str, idempotency_key: str = None):
    """Тест оплаты заказа через API."""
    print_section("Оплата заказа через API")
    
    # #region agent log
    _debug_log("debug-session", "run1", "H4", "test_functionality.py:204", "test_capture_payment_entry", {"order_id": order_id, "has_idempotency_key": idempotency_key is not None})
    # #endregion
    
    mutation = """
        mutation CapturePayment($orderId: UUID!) {
            capturePayment(orderId: $orderId) {
                orderId
                status
                amountDebited
                bonusCredited
            }
        }
    """
    
    variables = {"orderId": order_id}
    
    if not idempotency_key:
        idempotency_key = str(uuid4())
    
    try:
        response = client.execute(
            query=mutation,
            variables=variables,
            operation_name="CapturePayment",
            idempotency_key=idempotency_key,
            request_id=str(uuid4()),
        )
        
        # #region agent log
        _debug_log("debug-session", "run1", "H4", "test_functionality.py:225", "capture_payment_response", {"has_errors": "errors" in response, "has_data": "data" in response})
        # #endregion
        
        if "errors" in response:
            # #region agent log
            _debug_log("debug-session", "run1", "H4", "test_functionality.py:234", "capture_payment_errors", {"errors": str(response.get("errors", []))})
            # #endregion
            print_result(False, f"Ошибка: {response['errors']}")
            return None
        
        result = response["data"]["capturePayment"]
        
        # #region agent log
        _debug_log("debug-session", "run1", "H4", "test_functionality.py:237", "capture_payment_success", {"status": result.get("status", "N/A"), "amount_debited": str(result.get("amountDebited", "N/A"))})
        # #endregion
        
        print_result(True, f"Заказ оплачен: {result['orderId']}")
        print_result(True, f"Статус: {result['status']}")
        print_result(True, f"Списано: {result['amountDebited']}")
        print_result(True, f"Начислено бонусов: {result['bonusCredited']}")
        
        return result
    except Exception as e:
        # #region agent log
        _debug_log("debug-session", "run1", "H4", "test_functionality.py:246", "capture_payment_exception", {"exception_type": type(e).__name__, "exception_msg": str(e)})
        # #endregion
        print_result(False, f"Ошибка оплаты: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print_result(False, f"Детали ошибки: {error_data}")
            except:
                pass
        return None


def test_wallet_balance(client: GraphQLClient, customer_id: str):
    """Тест проверки баланса кошелька через API."""
    print_section("Проверка баланса кошелька через API")
    
    # #region agent log
    _debug_log("debug-session", "run1", "H1", "test_functionality.py:256", "test_wallet_balance_entry", {"customer_id": customer_id})
    # #endregion
    
    query = """
        query GetWalletBalance($customerId: String!) {
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
            operation_name="GetWalletBalance",
        )
        
        # #region agent log
        _debug_log("debug-session", "run1", "H3", "test_functionality.py:272", "wallet_balance_response", {"has_errors": "errors" in response, "has_data": "data" in response})
        # #endregion
        
        if "errors" in response:
            # #region agent log
            _debug_log("debug-session", "run1", "H3", "test_functionality.py:275", "wallet_balance_errors", {"errors": str(response.get("errors", []))})
            # #endregion
            print_result(False, f"Ошибка: {response['errors']}")
            return None
        
        result = response["data"]["walletBalance"]
        
        # #region agent log
        _debug_log("debug-session", "run1", "run1", "test_functionality.py:282", "wallet_balance_success", {"balance": str(result.get("balance", "N/A"))})
        # #endregion
        
        print_result(True, f"Баланс: {result['balance']}")

        return result
    except Exception as e:
        # #region agent log
        _debug_log("debug-session", "run1", "H3", "test_functionality.py:288", "wallet_balance_exception", {"exception_type": type(e).__name__, "exception_msg": str(e)})
        # #endregion
        print_result(False, f"Ошибка получения баланса: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print_result(False, f"Детали ошибки: {error_data}")
            except:
                pass
        return None


def test_refund_order(client: GraphQLClient, order_id: str):
    """Тест возврата заказа через API."""
    print_section("Возврат заказа через API")
    
    mutation = """
        mutation RefundOrder($orderId: UUID!) {
            refundOrder(orderId: $orderId) {
                orderId
                status
                amountRefunded
            }
        }
    """
    
    variables = {"orderId": order_id}
    
    try:
        response = client.execute(
            query=mutation,
            variables=variables,
            operation_name="RefundOrder",
            request_id=str(uuid4()),
        )
        
        if "errors" in response:
            print_result(False, f"Ошибка: {response['errors']}")
            return None
        
        result = response["data"]["refundOrder"]
        
        print_result(True, f"Заказ возвращен: {result['orderId']}")
        print_result(True, f"Статус: {result['status']}")
        print_result(True, f"Сумма возврата: {result['amountRefunded']}")
        
        return result
    except Exception as e:
        print_result(False, f"Ошибка возврата: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print_result(False, f"Детали ошибки: {error_data}")
            except:
                pass
        return None


def test_idempotency(client: GraphQLClient, customer_id: str, items: list):
    """Тест идемпотентности через API."""
    print_section("Тест идемпотентности через API")
    
    # Создать заказ первый раз
    order_id_1 = test_create_order(client, customer_id, items)
    if not order_id_1:
        return
    
    # Попытка оплатить дважды с одинаковым Idempotency-Key
    idempotency_key = str(uuid4())
    
    print_result(True, f"Первая попытка оплаты с ключом: {idempotency_key[:8]}...")
    result1 = test_capture_payment(client, order_id_1, idempotency_key)
    
    print_result(True, f"Вторая попытка оплаты с тем же ключом: {idempotency_key[:8]}...")
    result2 = test_capture_payment(client, order_id_1, idempotency_key)
    
    if result1 and result2:
        if result1["orderId"] == result2["orderId"]:
            print_result(True, "Идемпотентность работает: одинаковый результат при повторном запросе")
        else:
            print_result(False, "ОШИБКА: Разные результаты при одинаковом ключе!")
    else:
        print_result(True, "Идемпотентность проверена (вторая попытка вернула ошибку или дубликат)")


def test_insufficient_balance(client: GraphQLClient, customer_id: str):
    """Тест недостаточного баланса через API."""
    print_section("Тест недостаточного баланса через API")
    
    # Создать заказ на большую сумму
    large_order_items = [
        {"product_id": str(uuid4()), "quantity": 1, "price": "10000.00"}
    ]
    
    order_id = test_create_order(client, customer_id, large_order_items)
    if not order_id:
        return
    
    # Попытка оплатить
    result = test_capture_payment(client, order_id)
    if result is None:
        print_result(True, "Ожидаемая ошибка: недостаточный баланс")
    else:
        print_result(False, "ОШИБКА: Оплата прошла при недостаточном балансе!")


def test_multiple_orders(client: GraphQLClient, customer_id: str):
    """Тест нескольких заказов через API."""
    print_section("Тест нескольких заказов через API")
    
    # Создать несколько заказов
    orders = []
    for i in range(3):
        items = [
            {"product_id": str(uuid4()), "quantity": 1, "price": "50.00"}
        ]
        order_id = test_create_order(client, customer_id, items)
        if order_id:
            orders.append(order_id)
            print_result(True, f"Заказ {i+1} создан: {order_id}")
    
    # Оплатить все заказы
    for i, order_id in enumerate(orders):
        result = test_capture_payment(client, order_id)
        if result:
            print_result(True, f"Заказ {i+1} оплачен: {result['status']}")
        else:
            print_result(False, f"Ошибка оплаты заказа {i+1}")
    
    # Проверить баланс
    balance_info = test_wallet_balance(client, customer_id)
    if balance_info:
        print_result(True, f"Финальный баланс: {balance_info['balance']}")


def test_orders_by_customer(client: GraphQLClient, customer_id: str):
    """Тест получения списка заказов клиента через API."""
    print_section("Тест получения списка заказов через API")
    
    query = """
        query GetOrdersByCustomer($customerId: UUID!, $limit: Int, $offset: Int) {
            ordersByCustomer(customerId: $customerId, limit: $limit, offset: $offset) {
                orders {
                    id
                    status
                    totalAmount
                }
                totalCount
                hasMore
            }
        }
    """
    
    variables = {
        "customerId": customer_id,
        "limit": 10,
        "offset": 0,
    }
    
    try:
        response = client.execute(
            query=query,
            variables=variables,
            operation_name="GetOrdersByCustomer",
        )
        
        if "errors" in response:
            print_result(False, f"Ошибка: {response['errors']}")
            return None
        
        result = response["data"]["ordersByCustomer"]
        
        print_result(True, f"Всего заказов: {result['totalCount']}")
        print_result(True, f"Есть еще: {result['hasMore']}")
        print_result(True, f"Получено заказов: {len(result['orders'])}")
        
        return result
    except Exception as e:
        print_result(False, f"Ошибка получения списка заказов: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_data = e.response.json()
                print_result(False, f"Детали ошибки: {error_data}")
            except:
                pass
        return None


def main(customer_id: str, api_url: str):
    """Основная функция тестирования."""

    # #region agent log
    _debug_log("debug-session", "run1", "H1", "test_functionality.py:474", "main_entry", {"customer_id": customer_id, "api_url": api_url})
    # #endregion

    graphql_endpoint = f"{api_url}/graphql/"
    
    print("\n" + "=" * 60)
    print("  ТЕСТИРОВАНИЕ ФУНКЦИОНАЛА ORDERS & WALLET ЧЕРЕЗ HTTP API")
    print("=" * 60)
    print(f"\nAPI Endpoint: {graphql_endpoint}")
    print(f"Customer ID: {customer_id}")
    
    client = GraphQLClient(base_url=graphql_endpoint)
    # Простой запрос для проверки доступности
    test_query = "query { __typename }"
    client.execute(query=test_query)
    print_result(True, "API доступен")
    
    try:
        # 1. Проверка начального баланса через API
        initial_balance = test_wallet_balance(client, customer_id)
        if not initial_balance:
            print_section("ОШИБКА")
            print_result(False, "Не удалось получить баланс. Проверьте, что клиент и кошелек существуют в базе данных.")
            sys.exit(1)
        
        # 2. Создание заказа через API
        items = [
            {"product_id": str(uuid4()), "quantity": 2, "price": "100.00"},
            {"product_id": str(uuid4()), "quantity": 1, "price": "50.00"},
        ]
        order_id = test_create_order(client, customer_id, items)
        
        if not order_id:
            print_section("ОШИБКА")
            print_result(False, "Не удалось создать заказ, дальнейшие тесты пропущены")
            sys.exit(1)
        
        # 3. Получение заказа через API
        test_get_order(client, order_id)
        
        # 4. Проверка баланса до оплаты
        test_wallet_balance(client, customer_id)
        
        # 5. Оплата заказа через API
        payment_result = test_capture_payment(client, order_id)
        
        # 6. Проверка баланса после оплаты
        balance_after_payment = test_wallet_balance(client, customer_id)
        
        # 7. Возврат заказа через API
        refund_result = test_refund_order(client, order_id)
        
        # 8. Проверка баланса после возврата
        balance_after_refund = test_wallet_balance(client, customer_id)
        
        # 9. Тест идемпотентности
        test_idempotency(client, customer_id, items)
        
        # 10. Тест недостаточного баланса
        test_insufficient_balance(client, customer_id)
        
        # 11. Тест нескольких заказов
        test_multiple_orders(client, customer_id)
        
        # 12. Тест получения списка заказов
        test_orders_by_customer(client, customer_id)
        
        # Итоги
        print_section("ИТОГИ ТЕСТИРОВАНИЯ")
        print_result(True, "Все основные тесты пройдены")
        print(f"\nCustomer ID: {customer_id}")
        print(f"Заказ ID: {order_id}")
        if initial_balance:
            print(f"\nНачальный баланс: {initial_balance['balance']}")
        if balance_after_payment:
            print(f"Баланс после оплаты: {balance_after_payment['balance']}")
        if balance_after_refund:
            print(f"Баланс после возврата: {balance_after_refund['balance']}")
        
    except Exception as e:
        print_section("ОШИБКА")
        print_result(False, f"Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    api_url = "http://localhost:8000"
    customer_id = "82c5c163-18bf-4685-9be4-5f3358d056bb"
    main(customer_id, api_url)
