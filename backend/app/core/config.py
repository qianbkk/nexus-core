"""
Nexus Core - Enterprise Knowledge & Workflow Orchestration Platform
Iteration 1: Core Architecture & Security Foundation
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional
import secrets


class Settings(BaseSettings):
    """Application settings with security-first design"""
    
    # Application
    APP_NAME: str = "Nexus Core"
    APP_VERSION: str = "1.0.0-iter1"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(64)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MFA_ISSUER: str = "Nexus Core"
    
    # Password Policy
    PASSWORD_MIN_LENGTH: int = 12
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    
    # Account Security
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    SESSION_TIMEOUT_MINUTES: int = 60
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://nexus:nexus_pass@postgres:5432/nexus_core"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 200
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://nexus.example.com"]
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # Feature Flags
    ENABLE_MFA: bool = True
    ENABLE_AUDIT_LOG: bool = True
    ENABLE_WORKFLOW_ENGINE: bool = True
    ENABLE_KNOWLEDGE_GRAPH: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
