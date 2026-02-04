import requests
from requests.auth import HTTPBasicAuth
from .config import HDFC_BASE_URL, MERCHANT_ID, API_KEY

def create_order(order_id: str, amount: int, return_url: str):
    payload = {
        "order_id": order_id,
        "amount": amount,
        "currency": "INR",
        "return_url": return_url
    }

    response = requests.post(
        f"{HDFC_BASE_URL}/orders",
        json=payload,
        auth=HTTPBasicAuth(MERCHANT_ID, API_KEY),
        timeout=10
    )

    response.raise_for_status()
    return response.json()


def fetch_order_status(pg_order_id: str):
    response = requests.get(
        f"{HDFC_BASE_URL}/orders/{pg_order_id}",
        auth=HTTPBasicAuth(MERCHANT_ID, API_KEY),
        timeout=10
    )

    response.raise_for_status()
    return response.json()
