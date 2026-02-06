# HDFC Payment Gateway Backend

Production-ready FastAPI backend for HDFC SmartGateway payment integration with comprehensive error handling, database migrations, testing, and DevOps support.

## Features

✅ **Production-Ready**
- Comprehensive error handling and retry logic
- Structured JSON logging with correlation IDs
- Health check endpoints for monitoring
- Database migrations with Alembic
- Connection pooling and proper resource management

✅ **Security**
- No hardcoded credentials (environment-based configuration)
- Input validation with Pydantic
- Non-root Docker user
- CORS configuration
- Proper exception handling without information leakage

✅ **Developer Experience**
- Type-safe configuration with Pydantic Settings
- Comprehensive test suite (unit + integration)
- Auto-generated API documentation (Swagger/ReDoc)
- Docker Compose for local development
- Hot reload in development mode

✅ **Observability**
- Request/response logging with timing
- Correlation IDs for request tracing
- Database health checks
- Detailed error tracking

## Tech Stack

- **Framework**: FastAPI 0.109.0
- **Database**: PostgreSQL 15 with SQLAlchemy 2.0
- **Migrations**: Alembic 1.13.1
- **Testing**: Pytest with coverage
- **Containerization**: Docker & Docker Compose
- **HTTP Client**: Requests with Tenacity retry logic

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Pydantic settings configuration
│   ├── db.py                # Database connection and session management
│   ├── models.py            # SQLAlchemy ORM models
│   ├── schemas.py           # Pydantic request/response schemas
│   ├── routes.py            # API route handlers
│   ├── hdfc.py              # HDFC API client with retry logic
│   ├── exceptions.py        # Custom exception classes
│   ├── middleware.py        # Request logging middleware
│   ├── logging_config.py    # Logging configuration
│   └── utils.py             # Utility functions
├── alembic/
│   ├── versions/            # Database migration scripts
│   ├── env.py               # Alembic environment configuration
│   └── script.py.mako       # Migration template
├── tests/
│   ├── conftest.py          # Pytest fixtures
│   ├── test_routes.py       # API endpoint tests
│   ├── test_hdfc.py         # HDFC client tests
│   └── test_models.py       # Database model tests
├── alembic.ini              # Alembic configuration
├── docker-compose.yml       # Docker Compose configuration
├── Dockerfile               # Multi-stage Docker build
├── requirements.txt         # Python dependencies
├── .env.example             # Environment variables template
└── README.md                # This file
```

## Quick Start

### Prerequisites

- Docker & Docker Compose (recommended)
- OR Python 3.11+ and PostgreSQL 15+

### Option 1: Docker (Recommended)

1. **Clone and navigate to the project**
   ```bash
   cd backend
   ```

2. **Create environment file**
   ```bash
   cp .env.example .env
   ```

3. **Edit `.env` file with your credentials**
   ```bash
   # Required: Update these values
   POSTGRES_PASSWORD=your_secure_password
   PGADMIN_PASSWORD=your_admin_password
   HDFC_MERCHANT_ID=your_merchant_id
   HDFC_API_KEY=your_api_key
   ```

4. **Start all services**
   ```bash
   docker-compose up --build
   ```

5. **Access the application**
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - pgAdmin: http://localhost:5050

### Option 2: Local Development

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up PostgreSQL database**
   ```bash
   createdb payments
   ```

4. **Create and configure `.env`**
   ```bash
   cp .env.example .env
   # Edit .env with your local database URL
   DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/payments
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the application**
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `HDFC_BASE_URL` | HDFC SmartGateway API URL | - | ✅ |
| `HDFC_MERCHANT_ID` | HDFC Merchant ID | - | ✅ |
| `HDFC_API_KEY` | HDFC API Key | - | ✅ |
| `DATABASE_URL` | PostgreSQL connection string | - | ✅ |
| `RETURN_URL` | Payment return callback URL | - | ✅ |
| `ENVIRONMENT` | Environment (development/staging/production) | development | ❌ |
| `LOG_LEVEL` | Logging level | INFO | ❌ |
| `LOG_FORMAT` | Log format (json/console) | console | ❌ |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | localhost:3000,localhost:8000 | ❌ |
| `POSTGRES_PASSWORD` | PostgreSQL password (Docker only) | - | ✅ (Docker) |
| `PGADMIN_PASSWORD` | pgAdmin password (Docker only) | - | ✅ (Docker) |

See `.env.example` for complete list.

## API Endpoints

### Health Check
```http
GET /health
```
Returns service health status and database connectivity.

### Create Payment Order
```http
POST /checkout
Content-Type: application/json

{
  "amount": 10000,
  "currency": "INR",
  "customer_email": "customer@example.com",
  "customer_phone": "+919876543210"
}
```

### Payment Return Callback
```http
GET /payment/return?order_id=<uuid>
```

### Get Order Details
```http
GET /orders/<order_id>
```

## Database Migrations

### Create a new migration
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Apply migrations
```bash
alembic upgrade head
```

### Rollback migration
```bash
alembic downgrade -1
```

### View migration history
```bash
alembic history
```

## Testing

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

### Run specific test file
```bash
pytest tests/test_routes.py -v
```

### Run specific test
```bash
pytest tests/test_routes.py::TestCheckoutEndpoint::test_checkout_success -v
```

## Development

### Code formatting
```bash
black app/ tests/
```

### Linting
```bash
flake8 app/ tests/
```

### Type checking
```bash
mypy app/
```

## Deployment

### Production Checklist

- [ ] Set `ENVIRONMENT=production` in `.env`
- [ ] Use strong passwords for database and pgAdmin
- [ ] Configure proper `CORS_ORIGINS`
- [ ] Set `LOG_FORMAT=json` for structured logging
- [ ] Set `DEBUG=false`
- [ ] Use HTTPS for `RETURN_URL`
- [ ] Set up proper monitoring and alerting
- [ ] Configure database backups
- [ ] Review and adjust connection pool settings
- [ ] Set up log aggregation (e.g., ELK stack)

### Docker Production Build

```bash
docker build -t hdfc-payment-backend:latest .
docker run -p 8000:8000 --env-file .env hdfc-payment-backend:latest
```

## Troubleshooting

### Database connection issues
```bash
# Check if PostgreSQL is running
docker-compose ps

# View database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

### Migration issues
```bash
# Check current migration version
alembic current

# View pending migrations
alembic heads

# Reset database (⚠️ destroys data)
alembic downgrade base
alembic upgrade head
```

### Application logs
```bash
# View application logs
docker-compose logs backend

# Follow logs in real-time
docker-compose logs -f backend
```

## Architecture

### Request Flow
1. Client sends request to FastAPI endpoint
2. Request logging middleware adds correlation ID
3. Pydantic validates request payload
4. Route handler processes business logic
5. HDFC client makes external API call (with retry)
6. Database transaction commits/rolls back
7. Response returned with proper status code
8. Request completion logged with timing

### Error Handling
- Custom exceptions for different error scenarios
- Automatic retry for transient failures (network, timeout)
- Proper HTTP status codes
- Detailed logging without exposing sensitive data
- Database transaction rollback on errors

## Contributing

1. Create a feature branch
2. Make changes with tests
3. Run tests and linting
4. Submit pull request

## License

Proprietary - All rights reserved

## Support

For issues and questions, contact the development team.
