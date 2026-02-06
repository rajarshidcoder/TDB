from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class CheckoutRequest(BaseModel):
    """Request schema for checkout endpoint"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 10000,
                "currency": "INR",
                "customer_email": "customer@example.com",
                "customer_phone": "+919876543210"
            }
        }
    )
    
    amount: int = Field(
        ...,
        gt=0,
        description="Amount in smallest currency unit (e.g., paise for INR)",
        examples=[10000]
    )
    
    currency: str = Field(
        default="INR",
        description="Currency code (ISO 4217)",
        examples=["INR", "USD"]
    )
    
    customer_email: Optional[str] = Field(
        default=None,
        description="Customer email address",
        examples=["customer@example.com"]
    )
    
    customer_phone: Optional[str] = Field(
        default=None,
        description="Customer phone number",
        examples=["+919876543210"]
    )
    
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional metadata for the order"
    )
    
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v: int) -> int:
        """Validate amount is positive"""
        if v <= 0:
            raise ValueError("Amount must be greater than 0")
        if v > 100000000:  # 10 lakh rupees max
            raise ValueError("Amount exceeds maximum limit")
        return v
    
    @field_validator("currency")
    @classmethod
    def validate_currency(cls, v: str) -> str:
        """Validate currency code"""
        allowed = ["INR", "USD", "EUR", "GBP"]
        if v.upper() not in allowed:
            raise ValueError(f"Currency must be one of {allowed}")
        return v.upper()


class CheckoutResponse(BaseModel):
    """Response schema for checkout endpoint"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "order_id": "550e8400-e29b-41d4-a716-446655440000",
                "payment_url": "https://smartgatewayuat.hdfcbank.com/pay/abc123",
                "amount": 10000,
                "currency": "INR",
                "status": "PENDING"
            }
        }
    )
    
    order_id: str = Field(..., description="Unique order identifier (UUID)")
    payment_url: str = Field(..., description="URL to redirect user for payment")
    amount: int = Field(..., description="Order amount")
    currency: str = Field(..., description="Currency code")
    status: str = Field(..., description="Order status")


class PaymentReturnResponse(BaseModel):
    """Response schema for payment return endpoint"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "order_id": "550e8400-e29b-41d4-a716-446655440000",
                "status": "SUCCESS",
                "amount": 10000,
                "currency": "INR",
                "pg_order_id": "HDFC123456789"
            }
        }
    )
    
    order_id: str = Field(..., description="Order identifier")
    status: str = Field(..., description="Payment status")
    amount: int = Field(..., description="Order amount")
    currency: str = Field(..., description="Currency code")
    pg_order_id: Optional[str] = Field(None, description="Payment gateway order ID")


class OrderDetailResponse(BaseModel):
    """Response schema for order details"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": 1,
                "order_id": "550e8400-e29b-41d4-a716-446655440000",
                "pg_order_id": "HDFC123456789",
                "amount": 10000,
                "currency": "INR",
                "status": "SUCCESS",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:35:00Z"
            }
        }
    )
    
    id: int
    order_id: str
    pg_order_id: Optional[str]
    amount: int
    currency: str
    status: str
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    """Response schema for health check endpoint"""
    
    status: str = Field(..., description="Service status")
    database: str = Field(..., description="Database connectivity status")
    version: str = Field(default="1.0.0", description="API version")


class ErrorResponse(BaseModel):
    """Response schema for error responses"""
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "Order not found",
                "message": "Order not found: 550e8400-e29b-41d4-a716-446655440000",
                "details": {"order_id": "550e8400-e29b-41d4-a716-446655440000"}
            }
        }
    )
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
