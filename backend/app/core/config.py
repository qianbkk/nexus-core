"""
Nexus Core - Enterprise Knowledge & Workflow Orchestration Platform
Iteration 2: Enhanced Security Validation & Rate Limiting Integration
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field
from functools import lru_cache
from typing import List, Optional
import secrets
import re


class Settings(BaseSettings):
    """Application settings with security-first design and strict validation"""
    
    # Application
    APP_NAME: str = "Nexus Core"
    APP_VERSION: str = "2.0.0-iter2-secure"
    DEBUG: bool = False
    ENVIRONMENT: str = Field(default="production", pattern="^(development|staging|production)$")
    
    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(64), min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    MFA_ISSUER: str = "Nexus Core"
    
    # Password Policy - Enhanced
    PASSWORD_MIN_LENGTH: int = 14
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True
    PASSWORD_REQUIRE_SPECIAL: bool = True
    PASSWORD_MAX_REPETITION: int = 3
    
    # Account Security - Enhanced
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 30
    SESSION_TIMEOUT_MINUTES: int = 60
    MFA_REQUIRED_FOR_ADMIN: bool = True
    
    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://nexus:nexus_pass@postgres:5432/nexus_core", pattern="^postgresql\\+asyncpg://")
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_ECHO: bool = False
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    REDIS_SSL: bool = False
    
    # Rate Limiting - Enhanced with SlowAPI support
    RATE_LIMIT_PER_SECOND: int = 10
    RATE_LIMIT_PER_MINUTE: int = 100
    RATE_LIMIT_BURST: int = 200
    RATE_LIMIT_ENABLED: bool = True
    
    # CORS - Strict
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://nexus.example.com"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["GET", "POST", "PUT", "DELETE", "PATCH"]
    CORS_ALLOW_HEADERS: List[str] = ["Authorization", "Content-Type", "X-Requested-With"]
    
    # Logging - Enhanced
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    LOG_AUDIT_ENABLED: bool = True
    
    # Feature Flags
    ENABLE_MFA: bool = True
    ENABLE_AUDIT_LOG: bool = True
    ENABLE_WORKFLOW_ENGINE: bool = True
    ENABLE_KNOWLEDGE_GRAPH: bool = True
    ENABLE_RATE_LIMITING: bool = True
    
    @field_validator('SECRET_KEY')
    @classmethod
    def validate_secret_key(cls, v):
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters")
        if v == "change_this_in_production" or "secret" in v.lower():
            raise ValueError("SECRET_KEY must be a strong random value")
        return v
    
    @field_validator('ALLOWED_ORIGINS')
    @classmethod
    def validate_cors_origins(cls, v):
        if "*" in v and len(v) > 1:
            raise ValueError("Cannot use wildcard with specific origins")
        for origin in v:
            if origin != "*" and not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid CORS origin: {origin}")
        return v
    
    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v):
        if "localhost" in v and "production" in os.getenv('ENVIRONMENT', ''):
            raise ValueError("Cannot use localhost in production environment")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = 'forbid'  # Reject unknown fields


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance"""
    return Settings()


settings = get_settings()
