"""Test script for stock history API."""

import requests
import json
from datetime import date, timedelta

BASE_URL = "http://localhost:8000"


def test_cn_stock_query():
    """Test querying CN stock history."""
    print("\n=== Test 1: Query CN Stock (600000) ===")

    url = f"{BASE_URL}/api/market/stock/history"
    payload = {
        "market": "cn",
        "symbol": "600000",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "action": "query",
        "adjust": "qfq"
    }

    response = requests.post(url, json=payload, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Count: {data.get('count')}")
        print(f"Message: {data.get('message')}")

        if data.get('data'):
            print(f"First 3 records:")
            for i, record in enumerate(data['data'][:3], 1):
                print(f"  {i}. {record}")
    else:
        print(f"Error: {response.text}")


def test_us_stock_query():
    """Test querying US stock history."""
    print("\n=== Test 2: Query US Stock (AAPL) ===")

    url = f"{BASE_URL}/api/market/stock/history"
    payload = {
        "market": "us",
        "symbol": "AAPL",
        "start_date": "2024-01-01",
        "end_date": "2024-01-31",
        "action": "query"
    }

    response = requests.post(url, json=payload, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Count: {data.get('count')}")
        print(f"Message: {data.get('message')}")

        if data.get('data'):
            print(f"First 3 records:")
            for i, record in enumerate(data['data'][:3], 1):
                print(f"  {i}. {record}")
    else:
        print(f"Error: {response.text}")


def test_save_to_database():
    """Test saving stock data to database."""
    print("\n=== Test 3: Save CN Stock to Database ===")

    url = f"{BASE_URL}/api/market/stock/history"
    payload = {
        "market": "cn",
        "symbol": "600000",
        "start_date": "2024-01-01",
        "end_date": "2024-01-10",
        "action": "save"
    }

    response = requests.post(url, json=payload, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Count: {data.get('count')}")
        print(f"Message: {data.get('message')}")
    else:
        print(f"Error: {response.text}")


def test_get_endpoint():
    """Test simplified GET endpoint."""
    print("\n=== Test 4: Simplified GET Endpoint ===")

    url = f"{BASE_URL}/api/market/stock/history/cn/600000"
    params = {
        "start_date": "2024-01-01",
        "end_date": "2024-01-05"
    }

    response = requests.get(url, params=params, timeout=30)
    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Count: {data.get('count')}")
        print(f"Message: {data.get('message')}")
    else:
        print(f"Error: {response.text}")


def test_validation_errors():
    """Test parameter validation."""
    print("\n=== Test 5: Parameter Validation ===")

    test_cases = [
        {
            "name": "Invalid CN symbol (not 6 digits)",
            "payload": {
                "market": "cn",
                "symbol": "12345",
                "start_date": "2024-01-01",
                "end_date": "2024-01-31"
            }
        },
        {
            "name": "Invalid date format",
            "payload": {
                "market": "cn",
                "symbol": "600000",
                "start_date": "2024/01/01",
                "end_date": "2024-01-31"
            }
        },
        {
            "name": "Start date after end date",
            "payload": {
                "market": "cn",
                "symbol": "600000",
                "start_date": "2024-02-01",
                "end_date": "2024-01-01"
            }
        }
    ]

    url = f"{BASE_URL}/api/market/stock/history"

    for test in test_cases:
        print(f"\n  Testing: {test['name']}")
        response = requests.post(url, json=test['payload'], timeout=10)
        print(f"  Status: {response.status_code}")
        if response.status_code != 200:
            print(f"  Expected error: {response.json().get('detail', 'Unknown')}")


if __name__ == "__main__":
    print("=" * 60)
    print("Stock History API Tests")
    print("=" * 60)

    try:
        # Check if server is running
        response = requests.get(f"{BASE_URL}/api/system/health", timeout=5)
        if response.status_code != 200:
            print("ERROR: Server is not running!")
            exit(1)

        print("Server is running, starting tests...\n")

        test_cn_stock_query()
        test_us_stock_query()
        test_save_to_database()
        test_get_endpoint()
        test_validation_errors()

        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot connect to {BASE_URL}")
        print("Please make sure the server is running:")
        print("  uvicorn app.main:app --reload --port 8000")
    except Exception as e:
        print(f"ERROR: {e}")
