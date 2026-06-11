"""
Nexus Core - Main Application Entry Point
Iteration 7: Production-Ready with Rate Limiting, Health Checks & Full Middleware Stack
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import json
import time
import uuid

from app.core.config import settings
from app.core.rate_limiter import rate_limiter
from app.db.session import init_db, close_db
from app.api.v1.endpoints import auth


# Configure structured JSON logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s", "module": "%(module)s"}',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager with initialization and cleanup"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"MFA Enabled: {settings.ENABLE_MFA}")
    logger.info(f"Audit Log Enabled: {settings.ENABLE_AUDIT_LOG}")
    logger.info(f"Rate Limiting Enabled: {settings.ENABLE_RATE_LIMITING}")
    
    # Initialize database
    await init_db()
    
    # Initialize rate limiter
    if settings.ENABLE_RATE_LIMITING:
        rate_limiter.initialize(app)
        logger.info("Rate limiter initialized")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    await close_db()
    logger.info("Application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Knowledge & Workflow Orchestration Platform",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS Middleware with strict configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add unique request ID to all requests for tracing"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response


@app.middleware("http")
async def timing_middleware(request: Request, call_next):
    """Track request processing time"""
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(json.dumps({
        "event": "request_timing",
        "method": request.method,
        "path": request.url.path,
        "process_time_ms": round(process_time * 1000, 2),
        "request_id": getattr(request.state, "request_id", None),
    }))
    
    return response


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for audit and debugging"""
    request_id = getattr(request.state, "request_id", id(request))
    
    logger.info(json.dumps({
        "event": "request",
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else None,
        "request_id": request_id,
        "user_agent": request.headers.get("user-agent"),
    }))
    
    response = await call_next(request)
    
    logger.info(json.dumps({
        "event": "response",
        "status_code": response.status_code,
        "request_id": request_id,
    }))
    
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for security and error tracking"""
    logger.error(json.dumps({
        "event": "exception",
        "error_type": type(exc).__name__,
        "error_message": str(exc),
        "request_id": getattr(request.state, "request_id", None),
        "path": request.url.path,
    }), exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error",
            "request_id": getattr(request.state, "request_id", None),
        } if not settings.DEBUG else {
            "detail": str(exc),
            "type": type(exc).__name__,
            "request_id": getattr(request.state, "request_id", None),
        }
    )


# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - Health check"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "features": {
            "mfa": settings.ENABLE_MFA,
            "audit_log": settings.ENABLE_AUDIT_LOG,
            "workflow_engine": settings.ENABLE_WORKFLOW_ENGINE,
            "knowledge_graph": settings.ENABLE_KNOWLEDGE_GRAPH,
            "rate_limiting": settings.ENABLE_RATE_LIMITING
        },
        "security": {
            "password_min_length": settings.PASSWORD_MIN_LENGTH,
            "max_login_attempts": settings.MAX_LOGIN_ATTEMPTS,
            "session_timeout_minutes": settings.SESSION_TIMEOUT_MINUTES,
        }
    }


@app.get("/ready", tags=["Health"])
async def readiness_check():
    """Readiness probe for Kubernetes/load balancers"""
    # Add database connectivity check here when models are ready
    return {"status": "ready"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )
