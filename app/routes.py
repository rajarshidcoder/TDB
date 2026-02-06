from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from typing import Optional
import uuid

from app.schemas import (
    CheckoutRequest,
    CheckoutResponse,
    PaymentReturnResponse,
    OrderDetailResponse,
    HealthResponse,
    ErrorResponse
)
from app.db import get_db, check_db_health
from app.models import Order
from app.hdfc import hdfc_client
from app.config import settings
from app.exceptions import (
    OrderNotFoundException,
    HDFCAPIException,
    DuplicateOrderException,
    DatabaseException
)
from app.logging_config import get_logger
from app.utils import generate_order_id

logger = get_logger(__name__)

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify service and database connectivity.
    """
    db_status = "healthy" if check_db_health() else "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "database": db_status,
        "version": "1.0.0"
    }


@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Payments"],
    responses={
        201: {"description": "Order created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        409: {"model": ErrorResponse, "description": "Duplicate order"},
        502: {"model": ErrorResponse, "description": "Payment gateway error"}
    }
)
def checkout(payload: CheckoutRequest, db: Session = Depends(get_db)):
    """
    Create a new payment order and get payment URL.
    
    This endpoint creates an order in the database and initiates a payment
    session with HDFC SmartGateway. Returns a payment URL to redirect the user.
    """
    try:
        # Generate unique order ID
        order_id = generate_order_id()
        
        logger.info(
            f"Processing checkout request",
            extra={
                "order_id": order_id,
                "amount": payload.amount,
                "currency": payload.currency
            }
        )
        
        # Create order in HDFC
        try:
            hdfc_resp = hdfc_client.create_order(
                order_id=str(order_id),
                amount=payload.amount,
                currency=payload.currency,
                return_url=settings.return_url
            )
        except HDFCAPIException as e:
            logger.error(
                f"HDFC order creation failed for order {order_id}",
                extra={"error": str(e)},
                exc_info=True
            )
            raise
        
        # Create order in database
        try:
            order = Order(
                order_id=uuid.UUID(order_id) if isinstance(order_id, str) else order_id,
                pg_order_id=hdfc_resp["id"],
                amount=payload.amount,
                currency=payload.currency,
                status="PENDING",
                raw_payload={
                    "amount": payload.amount,
                    "currency": payload.currency,
                    "customer_email": payload.customer_email,
                    "customer_phone": payload.customer_phone,
                    "metadata": payload.metadata
                }
            )
            
            db.add(order)
            db.commit()
            db.refresh(order)
            
            logger.info(
                f"Order created successfully",
                extra={
                    "order_id": str(order.order_id),
                    "pg_order_id": order.pg_order_id,
                    "status": order.status
                }
            )
            
        except IntegrityError as e:
            db.rollback()
            logger.error(
                f"Database integrity error creating order",
                extra={"order_id": order_id},
                exc_info=True
            )
            raise DuplicateOrderException(order_id=str(order_id))
        
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                f"Database error creating order",
                extra={"order_id": order_id},
                exc_info=True
            )
            raise DatabaseException(
                message=str(e),
                operation="create_order"
            )
        
        # Extract payment URL
        payment_url = hdfc_resp.get("payment_links", {}).get("web")
        if not payment_url:
            logger.error(
                f"No payment URL in HDFC response",
                extra={"hdfc_response": hdfc_resp}
            )
            raise HDFCAPIException(
                message="Payment URL not found in HDFC response",
                hdfc_error_code="MISSING_PAYMENT_URL",
                hdfc_response=hdfc_resp
            )
        
        return CheckoutResponse(
            order_id=str(order.order_id),
            payment_url=payment_url,
            amount=order.amount,
            currency=order.currency,
            status=order.status
        )
        
    except (HDFCAPIException, DuplicateOrderException, DatabaseException):
        # Re-raise known exceptions
        raise
    
    except Exception as e:
        logger.error(
            f"Unexpected error in checkout",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/payment/return",
    response_model=PaymentReturnResponse,
    tags=["Payments"],
    responses={
        200: {"description": "Payment status retrieved"},
        404: {"model": ErrorResponse, "description": "Order not found"},
        502: {"model": ErrorResponse, "description": "Payment gateway error"}
    }
)
def payment_return(
    order_id: str = Query(..., description="Order ID to check status"),
    db: Session = Depends(get_db)
):
    """
    Handle payment return callback and update order status.
    
    This endpoint is called when the user returns from the payment gateway.
    It fetches the payment status from HDFC and updates the order accordingly.
    """
    try:
        logger.info(
            f"Processing payment return",
            extra={"order_id": order_id}
        )
        
        # Convert string to UUID
        try:
            order_uuid = uuid.UUID(order_id)
        except ValueError:
            logger.warning(f"Invalid UUID format for order_id: {order_id}")
            raise OrderNotFoundException(order_id=order_id)
        
        # Fetch order from database
        order = db.query(Order).filter(Order.order_id == order_uuid).first()
        
        if not order:
            logger.warning(f"Order not found: {order_id}")
            raise OrderNotFoundException(order_id=order_id)
        
        # Skip if already processed
        if order.status in ["SUCCESS", "FAILED"]:
            logger.info(
                f"Order already processed",
                extra={
                    "order_id": order_id,
                    "status": order.status
                }
            )
            return PaymentReturnResponse(
                order_id=str(order.order_id),
                status=order.status,
                amount=order.amount,
                currency=order.currency,
                pg_order_id=order.pg_order_id
            )
        
        # Fetch status from HDFC
        try:
            status_resp = hdfc_client.fetch_order_status(order.pg_order_id)
        except HDFCAPIException as e:
            logger.error(
                f"Failed to fetch order status from HDFC",
                extra={
                    "order_id": order_id,
                    "pg_order_id": order.pg_order_id
                },
                exc_info=True
            )
            raise
        
        # Update order status based on HDFC response
        hdfc_status = status_resp.get("status")
        hdfc_amount = status_resp.get("amount")
        
        logger.info(
            f"HDFC status received",
            extra={
                "order_id": order_id,
                "hdfc_status": hdfc_status,
                "hdfc_amount": hdfc_amount,
                "expected_amount": order.amount
            }
        )
        
        # Verify amount matches
        if hdfc_status == "CHARGED" and hdfc_amount == order.amount:
            order.status = "SUCCESS"
            logger.info(f"Order marked as SUCCESS: {order_id}")
        else:
            order.status = "FAILED"
            logger.warning(
                f"Order marked as FAILED: {order_id}",
                extra={
                    "hdfc_status": hdfc_status,
                    "amount_match": hdfc_amount == order.amount
                }
            )
        
        # Commit status update
        try:
            db.commit()
            db.refresh(order)
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(
                f"Failed to update order status",
                extra={"order_id": order_id},
                exc_info=True
            )
            raise DatabaseException(
                message=str(e),
                operation="update_order_status"
            )
        
        return PaymentReturnResponse(
            order_id=str(order.order_id),
            status=order.status,
            amount=order.amount,
            currency=order.currency,
            pg_order_id=order.pg_order_id
        )
        
    except (OrderNotFoundException, HDFCAPIException, DatabaseException):
        # Re-raise known exceptions
        raise
    
    except Exception as e:
        logger.error(
            f"Unexpected error in payment return",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )


@router.get(
    "/orders/{order_id}",
    response_model=OrderDetailResponse,
    tags=["Orders"],
    responses={
        200: {"description": "Order details retrieved"},
        404: {"model": ErrorResponse, "description": "Order not found"}
    }
)
def get_order(order_id: str, db: Session = Depends(get_db)):
    """
    Get order details by order ID.
    
    Returns complete order information including status and timestamps.
    """
    try:
        logger.info(f"Fetching order details", extra={"order_id": order_id})
        
        # Convert string to UUID
        try:
            order_uuid = uuid.UUID(order_id)
        except ValueError:
            logger.warning(f"Invalid UUID format for order_id: {order_id}")
            raise OrderNotFoundException(order_id=order_id)
        
        # Fetch order
        order = db.query(Order).filter(Order.order_id == order_uuid).first()
        
        if not order:
            logger.warning(f"Order not found: {order_id}")
            raise OrderNotFoundException(order_id=order_id)
        
        return OrderDetailResponse(
            id=order.id,
            order_id=str(order.order_id),
            pg_order_id=order.pg_order_id,
            amount=order.amount,
            currency=order.currency,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at
        )
        
    except OrderNotFoundException:
        raise
    
    except Exception as e:
        logger.error(
            f"Unexpected error fetching order",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
