import time
import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .schemas import (
    CheckoutRequest,
    CheckoutResponse,
    PaymentReturnResponse
)
from .db import get_db
from .models import Order
from .hdfc import create_order, fetch_order_status
from .config import RETURN_URL

router = APIRouter()

def generate_order_id():
    return f"ORD{int(time.time())}{random.randint(100,999)}"


@router.post("/checkout", response_model=CheckoutResponse)
def checkout(payload: CheckoutRequest, db: Session = Depends(get_db)):
    amount = payload.amount
    if not amount:
        raise HTTPException(400, "Amount missing")

    order_id = generate_order_id()

    hdfc_resp = create_order(
        order_id=order_id,
        amount=amount,
        return_url=RETURN_URL
    )

    order = Order(
        order_id=order_id,
        pg_order_id=hdfc_resp["id"],
        amount=amount,
        status="PENDING",
        raw_payload=payload
    )

    db.add(order)
    db.commit()

    return {
        "order_id": order_id,
        "payment_url": hdfc_resp["payment_links"]["web"]
    }


@router.get("/payment/return")
def payment_return(order_id: str, db: Session = Depends(get_db)):
    order = db.query(Order).filter_by(order_id=order_id).first()

    if not order:
        raise HTTPException(404, "Order not found")

    status_resp = fetch_order_status(order.pg_order_id)

    if (
        status_resp["status"] == "CHARGED"
        and status_resp["amount"] == order.amount
    ):
        order.status = "SUCCESS"
    else:
        order.status = "FAILED"

    db.commit()

    return {
        "order_id": order.order_id,
        "status": order.status,
        "amount": order.amount
    }
