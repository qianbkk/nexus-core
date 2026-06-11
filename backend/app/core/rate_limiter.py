"""
Rate Limiter - Iteration 5: Advanced Rate Limiting with SlowAPI
Production-grade request throttling with Redis backend
"""
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address, get_ipaddr
from fastapi import Request, HTTPException
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import logging
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class NexusRateLimiter:
    """Advanced rate limiter with multiple strategies"""
    
    def __init__(self):
        self.limiter = Limiter(
            key_func=get_remote_address,
            key_prefix="nexus",
            default_limits=[
                f"{settings.RATE_LIMIT_PER_MINUTE}/minute",
                f"{settings.RATE_LIMIT_BURST}/burst"
            ],
            storage_uri=settings.REDIS_URL if settings.ENABLE_RATE_LIMITING else "memory://",
            strategy="fixed-window",  # Options: fixed-window, sliding-window, moving-window
        )
        self._initialized = False
    
    def initialize(self, app) -> None:
        """Initialize rate limiter with FastAPI app"""
        if self._initialized:
            return
        
        app.state.limiter = self.limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
        
        self._initialized = True
        logger.info("Rate limiter initialized")
    
    @staticmethod
    def get_user_identifier(request: Request) -> str:
        """Get unique identifier for rate limiting (user ID or IP)"""
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fallback to IP address
        return f"ip:{get_ipaddr(request)}"
    
    @staticmethod
    def get_endpoint_identifier(request: Request) -> str:
        """Get endpoint identifier for granular rate limiting"""
        return f"endpoint:{request.method}:{request.url.path}"


# Custom rate limit decorators
def rate_limit_auth_requests():
    """Strict rate limit for authentication endpoints"""
    from slowapi import Limiter
    limiter = Limiter(key_func=get_ipaddr)
    return limiter.limit(f"{settings.MAX_LOGIN_ATTEMPTS * 2}/hour")


def rate_limit_api_requests(limit: Optional[str] = None):
    """Standard rate limit for API requests"""
    from slowapi import Limiter
    limiter = Limiter(key_func=NexusRateLimiter.get_user_identifier)
    
    if limit is None:
        limit = f"{settings.RATE_LIMIT_PER_MINUTE}/minute"
    
    return limiter.limit(limit)


def rate_limit_heavy_operations():
    """Strict rate limit for resource-intensive operations"""
    from slowapi import Limiter
    limiter = Limiter(key_func=NexusRateLimiter.get_user_identifier)
    return limiter.limit("10/minute")


def rate_limit_public_endpoints():
    """Very strict rate limit for public/unauthenticated endpoints"""
    from slowapi import Limiter
    limiter = Limiter(key_func=get_ipaddr)
    return limiter.limit("30/minute")


# Custom rate limit exceeded handler
async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded) -> HTTPException:
    """Custom handler for rate limit exceeded errors"""
    logger.warning(
        f"Rate limit exceeded for {NexusRateLimiter.get_user_identifier(request)} "
        f"on {NexusRateLimiter.get_endpoint_identifier(request)}"
    )
    
    return HTTPException(
        status_code=HTTP_429_TOO_MANY_REQUESTS,
        detail={
            "error": "rate_limit_exceeded",
            "message": "Too many requests. Please try again later.",
            "retry_after": str(exc.detail.split(":")[-1].strip() if ":" in exc.detail else "60"),
        },
        headers={"Retry-After": "60"}
    )


# Global rate limiter instance
rate_limiter = NexusRateLimiter()
