from sqlalchemy import Column, Integer, String, JSON, TIMESTAMP
from sqlalchemy.sql import func
from .db import Base

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True)
    order_id = Column(String(32), unique=True, index=True)
    pg_order_id = Column(String(64), index=True)
    amount = Column(Integer)
    currency = Column(String(8), default="INR")
    status = Column(String(20))
    raw_payload = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, onupdate=func.now())
