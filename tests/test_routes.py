import pytest
from unittest.mock import patch, MagicMock
import uuid


class TestHealthEndpoint:
    """Test health check endpoint"""
    
    def test_health_check_success(self, client):
        """Test health check returns healthy status"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "version" in data


class TestCheckoutEndpoint:
    """Test checkout endpoint"""
    
    @patch('app.routes.hdfc_client.create_order')
    def test_checkout_success(self, mock_create_order, client, sample_order_data, mock_hdfc_create_response):
        """Test successful checkout"""
        mock_create_order.return_value = mock_hdfc_create_response
        
        response = client.post("/checkout", json=sample_order_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "order_id" in data
        assert "payment_url" in data
        assert data["amount"] == 10000
        assert data["status"] == "PENDING"
    
    def test_checkout_invalid_amount(self, client):
        """Test checkout with invalid amount"""
        invalid_data = {
            "amount": -100,  # Negative amount
            "currency": "INR"
        }
        
        response = client.post("/checkout", json=invalid_data)
        
        assert response.status_code == 422
        data = response.json()
        assert "error" in data
    
    def test_checkout_zero_amount(self, client):
        """Test checkout with zero amount"""
        invalid_data = {
            "amount": 0,
            "currency": "INR"
        }
        
        response = client.post("/checkout", json=invalid_data)
        
        assert response.status_code == 422
    
    def test_checkout_invalid_currency(self, client):
        """Test checkout with invalid currency"""
        invalid_data = {
            "amount": 10000,
            "currency": "XYZ"  # Invalid currency
        }
        
        response = client.post("/checkout", json=invalid_data)
        
        assert response.status_code == 422
    
    @patch('app.routes.hdfc_client.create_order')
    def test_checkout_hdfc_error(self, mock_create_order, client, sample_order_data):
        """Test checkout when HDFC API fails"""
        from app.exceptions import HDFCAPIException
        
        mock_create_order.side_effect = HDFCAPIException(
            message="HDFC API error",
            hdfc_error_code="API_ERROR"
        )
        
        response = client.post("/checkout", json=sample_order_data)
        
        assert response.status_code == 502
        data = response.json()
        assert "error" in data


class TestPaymentReturnEndpoint:
    """Test payment return endpoint"""
    
    @patch('app.routes.hdfc_client.fetch_order_status')
    def test_payment_return_success(self, mock_fetch_status, client, db_session, mock_hdfc_status_response):
        """Test successful payment return"""
        from app.models import Order
        
        # Create order in database
        order_id = uuid.uuid4()
        order = Order(
            order_id=order_id,
            pg_order_id="HDFC123456789",
            amount=10000,
            currency="INR",
            status="PENDING"
        )
        db_session.add(order)
        db_session.commit()
        
        # Mock HDFC response
        mock_fetch_status.return_value = mock_hdfc_status_response
        
        # Call payment return
        response = client.get(f"/payment/return?order_id={str(order_id)}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "SUCCESS"
        assert data["amount"] == 10000
    
    @patch('app.routes.hdfc_client.fetch_order_status')
    def test_payment_return_failed(self, mock_fetch_status, client, db_session):
        """Test payment return with failed payment"""
        from app.models import Order
        
        # Create order in database
        order_id = uuid.uuid4()
        order = Order(
            order_id=order_id,
            pg_order_id="HDFC123456789",
            amount=10000,
            currency="INR",
            status="PENDING"
        )
        db_session.add(order)
        db_session.commit()
        
        # Mock HDFC response with failed status
        mock_fetch_status.return_value = {
            "id": "HDFC123456789",
            "status": "FAILED",
            "amount": 10000
        }
        
        # Call payment return
        response = client.get(f"/payment/return?order_id={str(order_id)}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "FAILED"
    
    def test_payment_return_order_not_found(self, client):
        """Test payment return with non-existent order"""
        fake_order_id = str(uuid.uuid4())
        
        response = client.get(f"/payment/return?order_id={fake_order_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
    
    def test_payment_return_invalid_uuid(self, client):
        """Test payment return with invalid UUID"""
        response = client.get("/payment/return?order_id=invalid-uuid")
        
        assert response.status_code == 404


class TestGetOrderEndpoint:
    """Test get order endpoint"""
    
    def test_get_order_success(self, client, db_session):
        """Test successful order retrieval"""
        from app.models import Order
        
        # Create order
        order_id = uuid.uuid4()
        order = Order(
            order_id=order_id,
            pg_order_id="HDFC123456789",
            amount=10000,
            currency="INR",
            status="SUCCESS"
        )
        db_session.add(order)
        db_session.commit()
        
        # Get order
        response = client.get(f"/orders/{str(order_id)}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["order_id"] == str(order_id)
        assert data["amount"] == 10000
        assert data["status"] == "SUCCESS"
    
    def test_get_order_not_found(self, client):
        """Test get order with non-existent ID"""
        fake_order_id = str(uuid.uuid4())
        
        response = client.get(f"/orders/{fake_order_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
