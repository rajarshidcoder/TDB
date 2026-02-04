from pydantic import BaseModel
from typing import Any, Dict

class CheckoutRequest(BaseModel):
    amount: int
    raw_payload: Dict[str, Any] | None = None


class CheckoutResponse(BaseModel):
    order_id: str
    payment_url: str


class PaymentReturnResponse(BaseModel):
    order_id: str
    status: str
    amount: int
