"""Main FastAPI application."""
import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.v1.router import api_router
from app.config import settings
from app.database import get_db
from app.exceptions import (
    AppException,
    app_exception_handler,
    database_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize Sentry with comprehensive error tracking
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.SENTRY_ENVIRONMENT,
        traces_sample_rate=0.1 if settings.SENTRY_ENVIRONMENT == "production" else 1.0,
        profiles_sample_rate=0.1,  # Profile 10% of sampled transactions
        enable_tracing=True,
        integrations=[
            # FastAPI is auto-detected by Sentry SDK
        ],
        # Set context tags
        release=settings.APP_VERSION,
        # Track performance
        _experiments={
            "profiles_sample_rate": 0.1,
        },
    )
    logger.info(f"Sentry initialized for environment: {settings.SENTRY_ENVIRONMENT}")

# Initialize OpenTelemetry for distributed tracing
if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
    resource = Resource.create({
        "service.name": settings.OTEL_SERVICE_NAME,
        "service.version": settings.APP_VERSION,
        "deployment.environment": settings.SENTRY_ENVIRONMENT,
    })
    trace.set_tracer_provider(TracerProvider(resource=resource))
    otlp_exporter = OTLPSpanExporter(endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT)
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(otlp_exporter))
    logger.info(f"OpenTelemetry initialized with endpoint: {settings.OTEL_EXPORTER_OTLP_ENDPOINT}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager."""
    logger.info("Starting Prompter API...")
    yield
    logger.info("Shutting down Prompter API...")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Visibility Platform API",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Store debug state
app.state.debug = settings.DEBUG

# Add middleware (order matters - first added = outermost layer = runs first)
# 1. Security headers (outermost)
from app.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# 2. Request ID propagation
from app.middleware.request_id import RequestIDMiddleware
app.add_middleware(RequestIDMiddleware)

# 3. Rate limiting
from app.middleware.rate_limit import RateLimitMiddleware
if settings.RATE_LIMIT_ENABLED:
    app.add_middleware(RateLimitMiddleware)

# 4. CORS middleware with explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,  # Configured in settings (production origins)
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID", "Idempotency-Key"],
    expose_headers=["X-Process-Time", "X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    max_age=86400,  # Cache preflight requests for 24 hours
)

# 5. Trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"],  # Configure for production: ["api.prompter.site", "*.prompter.site"]
)


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Register exception handlers (order matters - specific to general)
app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(SQLAlchemyError, database_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)


# Health check endpoints
@app.get("/healthz")
async def healthz():
    """Liveness probe - checks if the application is running."""
    return {"ok": True, "status": "alive", "version": settings.APP_VERSION}


@app.get("/readyz")
async def readyz(db: Session = Depends(get_db)):
    """Readiness probe - checks if the application can serve traffic (includes DB check)."""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "ok": True,
            "status": "ready",
            "version": settings.APP_VERSION,
            "checks": {"database": "connected"},
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "ok": False,
                "status": "not_ready",
                "version": settings.APP_VERSION,
                "checks": {"database": "disconnected"},
                "error": str(e),
            },
        )


@app.get("/health")
async def health_check():
    """Legacy health check endpoint (deprecated, use /healthz instead)."""
    return {"status": "healthy", "version": settings.APP_VERSION}


# Include API router
app.include_router(api_router, prefix="/v1")

# Instrument with OpenTelemetry
if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
    FastAPIInstrumentor.instrument_app(app)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

