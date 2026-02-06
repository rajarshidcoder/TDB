import pytest
import uuid
from app.models import Order
from sqlalchemy.exc import IntegrityError


class TestOrderModel:
    """Test Order database model"""
    
    def test_create_order(self, db_session):
        """Test creating a new order"""
        order = Order(
            order_id=uuid.uuid4(),
            pg_order_id="HDFC123456789",
            amount=10000,
            currency="INR",
            status="PENDING",
            raw_payload={"test": "data"}
        )
        
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        assert order.id is not None
        assert order.amount == 10000
        assert order.currency == "INR"
        assert order.status == "PENDING"
        assert order.created_at is not None
        assert order.updated_at is not None
    
    def test_order_unique_constraint(self, db_session):
        """Test unique constraint on order_id"""
        order_id = uuid.uuid4()
        
        # Create first order
        order1 = Order(
            order_id=order_id,
            amount=10000,
            currency="INR",
            status="PENDING"
        )
        db_session.add(order1)
        db_session.commit()
        
        # Try to create duplicate order
        order2 = Order(
            order_id=order_id,
            amount=20000,
            currency="INR",
            status="PENDING"
        )
        db_session.add(order2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_order_to_dict(self, db_session):
        """Test order to_dict method"""
        order = Order(
            order_id=uuid.uuid4(),
            pg_order_id="HDFC123456789",
            amount=10000,
            currency="INR",
            status="SUCCESS"
        )
        
        db_session.add(order)
        db_session.commit()
        db_session.refresh(order)
        
        order_dict = order.to_dict()
        
        assert "id" in order_dict
        assert "order_id" in order_dict
        assert "amount" in order_dict
        assert order_dict["amount"] == 10000
        assert order_dict["status"] == "SUCCESS"
    
    def test_order_repr(self, db_session):
        """Test order __repr__ method"""
        order = Order(
            order_id=uuid.uuid4(),
            amount=10000,
            currency="INR",
            status="PENDING"
        )
        
        db_session.add(order)
        db_session.commit()
        
        repr_str = repr(order)
        assert "Order" in repr_str
        assert "10000" in repr_str
        assert "PENDING" in repr_str
