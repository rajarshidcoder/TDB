from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class PaymentGatewayException(Exception):
    """Base exception for payment gateway errors"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class OrderNotFoundException(PaymentGatewayException):
    """Raised when an order is not found"""
    
    def __init__(self, order_id: str):
        super().__init__(
            message=f"Order not found: {order_id}",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"order_id": order_id}
        )


class InvalidOrderStateException(PaymentGatewayException):
    """Raised when order state transition is invalid"""
    
    def __init__(self, order_id: str, current_state: str, attempted_state: str):
        super().__init__(
            message=f"Invalid state transition for order {order_id}: {current_state} -> {attempted_state}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={
                "order_id": order_id,
                "current_state": current_state,
                "attempted_state": attempted_state
            }
        )


class HDFCAPIException(PaymentGatewayException):
    """Raised when HDFC API call fails"""
    
    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_502_BAD_GATEWAY,
        hdfc_error_code: Optional[str] = None,
        hdfc_response: Optional[Dict[str, Any]] = None
    ):
        details = {"hdfc_error_code": hdfc_error_code}
        if hdfc_response:
            details["hdfc_response"] = hdfc_response
        
        super().__init__(
            message=f"HDFC API Error: {message}",
            status_code=status_code,
            details=details
        )


class ValidationException(PaymentGatewayException):
    """Raised when input validation fails"""
    
    def __init__(self, message: str, field: Optional[str] = None):
        details = {}
        if field:
            details["field"] = field
        
        super().__init__(
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=details
        )


class DuplicateOrderException(PaymentGatewayException):
    """Raised when attempting to create a duplicate order"""
    
    def __init__(self, order_id: str):
        super().__init__(
            message=f"Order already exists: {order_id}",
            status_code=status.HTTP_409_CONFLICT,
            details={"order_id": order_id}
        )


class DatabaseException(PaymentGatewayException):
    """Raised when database operation fails"""
    
    def __init__(self, message: str, operation: Optional[str] = None):
        details = {}
        if operation:
            details["operation"] = operation
        
        super().__init__(
            message=f"Database error: {message}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )
