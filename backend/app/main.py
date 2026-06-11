"""
Nexus Core - Main Application Entry Point
Iteration 3: Complete FastAPI Application with Security & CORS
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import json

from app.core.config import settings
from app.api.v1.endpoints import auth


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"MFA Enabled: {settings.ENABLE_MFA}")
    logger.info(f"Audit Log Enabled: {settings.ENABLE_AUDIT_LOG}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Enterprise Knowledge & Workflow Orchestration Platform",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for audit and debugging"""
    request_id = id(request)
    
    logger.info(json.dumps({
        "event": "request",
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host if request.client else None,
        "request_id": request_id,
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
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "type": "internal_error"
        } if not settings.DEBUG else {
            "detail": str(exc),
            "type": type(exc).__name__
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
            "knowledge_graph": settings.ENABLE_KNOWLEDGE_GRAPH
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
