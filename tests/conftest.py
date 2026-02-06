import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.db import Base, get_db
from app.models import Order

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def sample_order_data():
    """Sample order data for testing"""
    return {
        "amount": 10000,
        "currency": "INR",
        "customer_email": "test@example.com",
        "customer_phone": "+919876543210"
    }


@pytest.fixture
def mock_hdfc_create_response():
    """Mock HDFC create order response"""
    return {
        "id": "HDFC123456789",
        "order_id": "test-order-id",
        "amount": 10000,
        "currency": "INR",
        "status": "PENDING",
        "payment_links": {
            "web": "https://smartgatewayuat.hdfcbank.com/pay/test123"
        }
    }


@pytest.fixture
def mock_hdfc_status_response():
    """Mock HDFC order status response"""
    return {
        "id": "HDFC123456789",
        "status": "CHARGED",
        "amount": 10000,
        "currency": "INR"
    }
