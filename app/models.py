from sqlalchemy import Column, String, Integer, JSON, TIMESTAMP, CheckConstraint, Index
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.db import Base


class Order(Base):
    """Order model for payment transactions"""
    
    __tablename__ = "orders"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Order identifiers
    order_id = Column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        index=True,
        default=uuid.uuid4,
        comment="Unique order identifier (UUID)"
    )
    
    pg_order_id = Column(
        String(64),
        nullable=True,
        index=True,
        comment="Payment gateway order ID from HDFC"
    )
    
    # Transaction details
    amount = Column(
        Integer,
        nullable=False,
        comment="Amount in smallest currency unit (paise for INR)"
    )
    
    currency = Column(
        String(8),
        nullable=False,
        default="INR",
        comment="Currency code (ISO 4217)"
    )
    
    status = Column(
        String(20),
        nullable=False,
        default="PENDING",
        index=True,
        comment="Order status: PENDING, SUCCESS, FAILED, CANCELLED, PROCESSING"
    )
    
    # Metadata
    raw_payload = Column(
        JSON,
        nullable=True,
        comment="Original request payload for debugging"
    )
    
    # Timestamps
    created_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Order creation timestamp"
    )
    
    updated_at = Column(
        TIMESTAMP(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Last update timestamp"
    )
    
    # Constraints
    __table_args__ = (
        CheckConstraint('amount > 0', name='check_amount_positive'),
        CheckConstraint(
            "status IN ('PENDING', 'SUCCESS', 'FAILED', 'CANCELLED', 'PROCESSING')",
            name='check_status_valid'
        ),
        CheckConstraint(
            "currency IN ('INR', 'USD', 'EUR', 'GBP')",
            name='check_currency_valid'
        ),
        Index('idx_order_status_created', 'status', 'created_at'),
        Index('idx_pg_order_id', 'pg_order_id'),
    )
    
    def __repr__(self) -> str:
        """String representation of Order"""
        return (
            f"<Order(id={self.id}, order_id={self.order_id}, "
            f"amount={self.amount}, status={self.status})>"
        )
    
    def to_dict(self) -> dict:
        """Convert order to dictionary"""
        return {
            "id": self.id,
            "order_id": str(self.order_id),
            "pg_order_id": self.pg_order_id,
            "amount": self.amount,
            "currency": self.currency,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
