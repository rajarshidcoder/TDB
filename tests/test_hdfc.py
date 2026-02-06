import pytest
from unittest.mock import patch, MagicMock
from app.hdfc import HDFCClient
from app.exceptions import HDFCAPIException
from requests.exceptions import Timeout, ConnectionError


class TestHDFCClient:
    """Test HDFC API client"""
    
    @pytest.fixture
    def hdfc_client(self):
        """Create HDFC client instance"""
        return HDFCClient()
    
    @patch('app.hdfc.requests.Session.request')
    def test_create_order_success(self, mock_request, hdfc_client):
        """Test successful order creation"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "HDFC123456789",
            "order_id": "test-order-123",
            "amount": 10000,
            "currency": "INR",
            "payment_links": {
                "web": "https://smartgatewayuat.hdfcbank.com/pay/test123"
            }
        }
        mock_request.return_value = mock_response
        
        # Call create_order
        result = hdfc_client.create_order(
            order_id="test-order-123",
            amount=10000,
            currency="INR"
        )
        
        # Assertions
        assert result["id"] == "HDFC123456789"
        assert result["payment_links"]["web"] is not None
        mock_request.assert_called_once()
    
    @patch('app.hdfc.requests.Session.request')
    def test_create_order_timeout(self, mock_request, hdfc_client):
        """Test order creation with timeout"""
        # Mock timeout
        mock_request.side_effect = Timeout()
        
        # Should raise HDFCAPIException
        with pytest.raises(HDFCAPIException) as exc_info:
            hdfc_client.create_order(
                order_id="test-order-123",
                amount=10000
            )
        
        assert "timeout" in str(exc_info.value.message).lower()
    
    @patch('app.hdfc.requests.Session.request')
    def test_create_order_connection_error(self, mock_request, hdfc_client):
        """Test order creation with connection error"""
        # Mock connection error
        mock_request.side_effect = ConnectionError()
        
        # Should raise HDFCAPIException
        with pytest.raises(HDFCAPIException) as exc_info:
            hdfc_client.create_order(
                order_id="test-order-123",
                amount=10000
            )
        
        assert "connect" in str(exc_info.value.message).lower()
    
    @patch('app.hdfc.requests.Session.request')
    def test_create_order_invalid_response(self, mock_request, hdfc_client):
        """Test order creation with invalid response structure"""
        # Mock response without required fields
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "order_id": "test-order-123"
            # Missing 'id' and 'payment_links'
        }
        mock_request.return_value = mock_response
        
        # Should raise HDFCAPIException
        with pytest.raises(HDFCAPIException) as exc_info:
            hdfc_client.create_order(
                order_id="test-order-123",
                amount=10000
            )
        
        assert "invalid response structure" in str(exc_info.value.message).lower()
    
    @patch('app.hdfc.requests.Session.request')
    def test_fetch_order_status_success(self, mock_request, hdfc_client):
        """Test successful order status fetch"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "HDFC123456789",
            "status": "CHARGED",
            "amount": 10000,
            "currency": "INR"
        }
        mock_request.return_value = mock_response
        
        # Call fetch_order_status
        result = hdfc_client.fetch_order_status("HDFC123456789")
        
        # Assertions
        assert result["status"] == "CHARGED"
        assert result["amount"] == 10000
        mock_request.assert_called_once()
    
    @patch('app.hdfc.requests.Session.request')
    def test_fetch_order_status_invalid_response(self, mock_request, hdfc_client):
        """Test order status fetch with invalid response"""
        # Mock response without required fields
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "HDFC123456789"
            # Missing 'status' and 'amount'
        }
        mock_request.return_value = mock_response
        
        # Should raise HDFCAPIException
        with pytest.raises(HDFCAPIException) as exc_info:
            hdfc_client.fetch_order_status("HDFC123456789")
        
        assert "invalid response structure" in str(exc_info.value.message).lower()
