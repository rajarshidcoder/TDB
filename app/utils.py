import uuid
from typing import Optional


def generate_order_id() -> str:
    """
    Generate a unique order ID using UUID4.
    
    Returns:
        str: A unique order ID in UUID format
    """
    return str(uuid.uuid4())


def validate_order_status(status: str) -> bool:
    """
    Validate if the order status is valid.
    
    Args:
        status: The status to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    valid_statuses = {"PENDING", "SUCCESS", "FAILED", "CANCELLED", "PROCESSING"}
    return status.upper() in valid_statuses


def format_amount(amount: int, currency: str = "INR") -> str:
    """
    Format amount for display.
    
    Args:
        amount: Amount in smallest currency unit (paise for INR)
        currency: Currency code
        
    Returns:
        str: Formatted amount string
    """
    if currency == "INR":
        rupees = amount / 100
        return f"₹{rupees:,.2f}"
    return f"{amount / 100:,.2f} {currency}"


def validate_currency(currency: str) -> bool:
    """
    Validate if the currency code is supported.
    
    Args:
        currency: Currency code to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    supported_currencies = {"INR", "USD", "EUR", "GBP"}
    return currency.upper() in supported_currencies
