from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager

from app.config import settings
from app.routes import router
from app.middleware import RequestLoggingMiddleware
from app.logging_config import setup_logging, get_logger
from app.exceptions import PaymentGatewayException
from app.hdfc import hdfc_client

# Setup logging
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info(
        f"Starting {settings.app_name}",
        extra={
            "environment": settings.environment,
            "debug": settings.debug
        }
    )
    
    yield
    
    # Shutdown
    logger.info(f"Shutting down {settings.app_name}")
    hdfc_client.close()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Production-ready HDFC SmartGateway Payment Integration API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    debug=settings.debug
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)


# Exception handlers
@app.exception_handler(PaymentGatewayException)
async def payment_gateway_exception_handler(request: Request, exc: PaymentGatewayException):
    """Handle custom payment gateway exceptions"""
    logger.error(
        f"Payment gateway exception: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "path": request.url.path
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "details": exc.details
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    logger.warning(
        f"Validation error: {str(exc)}",
        extra={
            "path": request.url.path,
            "errors": exc.errors()
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors()
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions"""
    logger.error(
        f"Unexpected exception: {str(exc)}",
        extra={"path": request.url.path},
        exc_info=True
    )
    
    # Don't expose internal errors in production
    if settings.is_production:
        message = "An internal error occurred"
    else:
        message = str(exc)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "InternalServerError",
            "message": message,
            "details": {}
        }
    )


# Include routers
app.include_router(router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return {
        "name": settings.app_name,
        "version": "1.0.0",
        "environment": settings.environment,
        "docs": "/docs",
        "health": "/health"
    }
