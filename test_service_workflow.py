#!/usr/bin/env python3
"""
Test script to verify service functionality.
"""
import json
import requests
import sys
from uuid import uuid4

BASE_URL = "http://localhost:8000/graphql/"

def test_graphql_query(query, variables=None, headers=None):
    """Execute GraphQL query."""
    payload = {"query": query}
    if variables:
        payload["variables"] = variables
    
    response = requests.post(
        BASE_URL,
        json=payload,
        headers=headers or {},
    )
    
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.json()

def main():
    """Test service workflow."""
    print("=" * 60)
    print("Testing Orders Wallet Service")
    print("=" * 60)
    
    # Test 1: Simple introspection query
    print("\n[Test 1] GraphQL introspection")
    test_graphql_query("{ __typename }")
    
    # Test 2: Create customer (if there's a mutation for it)
    # Note: Customers need to be created via admin or directly in DB
    # For now, we'll test with a random UUID and see what happens
    
    customer_id = str(uuid4())
    print(f"\n[Test 2] Testing with  ID: {customer_id}")
    
    # Test 3: Try to create order (will fail if customer doesn't exist)
    print("\n[Test 3] Create order (may fail if customer doesn't exist)")
    create_order_query = """
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
                    "productId": str(uuid4()),
                    "quantity": 2,
                    "price": "100.00"
                }
            ]
        }
    }
    result = test_graphql_query(create_order_query, variables)
    
    # Test 4: Query wallet balance
    print("\n[Test 4] Query wallet balance")
    wallet_query = """
        query GetWalletBalance($customerId: String!) {
            walletBalance(customerId: $customerId) {
                customerId
                balance
            }
        }
    """
    test_graphql_query(wallet_query, {"customerId": customer_id})
    
    print("\n" + "=" * 60)
    print("Test completed")
    print("=" * 60)

if __name__ == "__main__":
    main()

