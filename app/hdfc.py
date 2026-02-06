import requests
from requests.auth import HTTPBasicAuth
from requests.exceptions import RequestException, Timeout, ConnectionError
from typing import Dict, Any, Optional
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)
import logging

from app.config import settings
from app.exceptions import HDFCAPIException
from app.logging_config import get_logger

logger = get_logger(__name__)


class HDFCClient:
    """Client for HDFC SmartGateway API with retry logic and error handling"""
    
    def __init__(self):
        self.base_url = settings.hdfc_base_url
        self.merchant_id = settings.hdfc_merchant_id
        self.api_key = settings.hdfc_api_key
        self.timeout = settings.hdfc_timeout
        self.max_retries = settings.hdfc_max_retries
        
        # Create session for connection pooling
        self.session = requests.Session()
        self.session.auth = HTTPBasicAuth(self.merchant_id, self.api_key)
        
        logger.info(f"HDFC Client initialized with base_url={self.base_url}")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((ConnectionError, Timeout)),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    def _make_request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make HTTP request to HDFC API with retry logic.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json_data: JSON payload for POST requests
            params: Query parameters
            
        Returns:
            Dict containing the API response
            
        Raises:
            HDFCAPIException: If the API request fails
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.info(
                f"Making {method} request to HDFC API",
                extra={
                    "method": method,
                    "url": url,
                    "has_payload": json_data is not None
                }
            )
            
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                timeout=self.timeout
            )
            
            # Log response
            logger.info(
                f"HDFC API response received",
                extra={
                    "status_code": response.status_code,
                    "url": url
                }
            )
            
            # Check for HTTP errors
            response.raise_for_status()
            
            # Parse JSON response
            response_data = response.json()
            
            return response_data
            
        except Timeout as e:
            logger.error(f"HDFC API request timeout: {url}", exc_info=True)
            raise HDFCAPIException(
                message=f"Request timeout after {self.timeout}s",
                hdfc_error_code="TIMEOUT"
            )
        
        except ConnectionError as e:
            logger.error(f"HDFC API connection error: {url}", exc_info=True)
            raise HDFCAPIException(
                message="Failed to connect to HDFC API",
                hdfc_error_code="CONNECTION_ERROR"
            )
        
        except requests.HTTPError as e:
            logger.error(
                f"HDFC API HTTP error: {e.response.status_code}",
                extra={"response_body": e.response.text},
                exc_info=True
            )
            
            # Try to parse error response
            try:
                error_data = e.response.json()
                error_message = error_data.get("message", str(e))
                error_code = error_data.get("error_code", "HTTP_ERROR")
            except:
                error_message = str(e)
                error_code = "HTTP_ERROR"
                error_data = None
            
            raise HDFCAPIException(
                message=error_message,
                status_code=e.response.status_code,
                hdfc_error_code=error_code,
                hdfc_response=error_data
            )
        
        except ValueError as e:
            logger.error("Failed to parse HDFC API response as JSON", exc_info=True)
            raise HDFCAPIException(
                message="Invalid JSON response from HDFC API",
                hdfc_error_code="INVALID_RESPONSE"
            )
        
        except Exception as e:
            logger.error(f"Unexpected error calling HDFC API: {str(e)}", exc_info=True)
            raise HDFCAPIException(
                message=f"Unexpected error: {str(e)}",
                hdfc_error_code="UNKNOWN_ERROR"
            )
    
    def create_order(
        self,
        order_id: str,
        amount: int,
        currency: str = "INR",
        return_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new order in HDFC SmartGateway.
        
        Args:
            order_id: Unique order identifier
            amount: Amount in smallest currency unit
            currency: Currency code (default: INR)
            return_url: URL to redirect after payment
            
        Returns:
            Dict containing order details from HDFC
            
        Raises:
            HDFCAPIException: If order creation fails
        """
        payload = {
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "return_url": return_url or settings.return_url
        }
        
        logger.info(
            f"Creating HDFC order",
            extra={
                "order_id": order_id,
                "amount": amount,
                "currency": currency
            }
        )
        
        response = self._make_request(
            method="POST",
            endpoint="/orders",
            json_data=payload
        )
        
        # Validate response structure
        if "id" not in response or "payment_links" not in response:
            logger.error(
                "Invalid response structure from HDFC create_order",
                extra={"response": response}
            )
            raise HDFCAPIException(
                message="Invalid response structure from HDFC API",
                hdfc_error_code="INVALID_RESPONSE_STRUCTURE",
                hdfc_response=response
            )
        
        logger.info(
            f"HDFC order created successfully",
            extra={
                "order_id": order_id,
                "pg_order_id": response.get("id")
            }
        )
        
        return response
    
    def fetch_order_status(self, pg_order_id: str) -> Dict[str, Any]:
        """
        Fetch order status from HDFC SmartGateway.
        
        Args:
            pg_order_id: Payment gateway order ID
            
        Returns:
            Dict containing order status details
            
        Raises:
            HDFCAPIException: If status fetch fails
        """
        logger.info(
            f"Fetching HDFC order status",
            extra={"pg_order_id": pg_order_id}
        )
        
        response = self._make_request(
            method="GET",
            endpoint=f"/orders/{pg_order_id}"
        )
        
        # Validate response structure
        if "status" not in response or "amount" not in response:
            logger.error(
                "Invalid response structure from HDFC fetch_order_status",
                extra={"response": response}
            )
            raise HDFCAPIException(
                message="Invalid response structure from HDFC API",
                hdfc_error_code="INVALID_RESPONSE_STRUCTURE",
                hdfc_response=response
            )
        
        logger.info(
            f"HDFC order status fetched",
            extra={
                "pg_order_id": pg_order_id,
                "status": response.get("status")
            }
        )
        
        return response
    
    def close(self):
        """Close the HTTP session"""
        self.session.close()
        logger.info("HDFC Client session closed")


# Global HDFC client instance
hdfc_client = HDFCClient()


# Convenience functions for backward compatibility
def create_order(order_id: str, amount: int, return_url: str, currency: str = "INR") -> Dict[str, Any]:
    """Create order using global client"""
    return hdfc_client.create_order(order_id, amount, currency, return_url)


def fetch_order_status(pg_order_id: str) -> Dict[str, Any]:
    """Fetch order status using global client"""
    return hdfc_client.fetch_order_status(pg_order_id)
