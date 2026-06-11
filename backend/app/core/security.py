"""
Security Module - Iteration 1: Authentication & Authorization Core
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, validator
import re

from app.core.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class TokenData(BaseModel):
    """JWT token payload structure"""
    sub: str  # subject (user_id)
    exp: datetime
    iat: datetime
    type: str  # "access" or "refresh"
    roles: list[str] = []
    permissions: list[str] = []


class UserCreate(BaseModel):
    """User registration schema with validation"""
    email: EmailStr
    username: str
    password: str
    full_name: str
    
    @validator('password')
    def validate_password(cls, v):
        errors = []
        
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")
        
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", v):
            errors.append("Password must contain uppercase letter")
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", v):
            errors.append("Password must contain lowercase letter")
        
        if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", v):
            errors.append("Password must contain digit")
        
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            errors.append("Password must contain special character")
        
        if errors:
            raise ValueError("; ".join(errors))
        
        return v


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash password using Argon2"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[TokenData]:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        
        sub = payload.get("sub")
        exp = payload.get("exp")
        iat = payload.get("iat")
        token_type = payload.get("type")
        roles = payload.get("roles", [])
        permissions = payload.get("permissions", [])
        
        if sub is None or token_type is None:
            return None
        
        return TokenData(
            sub=sub,
            exp=datetime.fromtimestamp(exp),
            iat=datetime.fromtimestamp(iat),
            type=token_type,
            roles=roles,
            permissions=permissions
        )
    except JWTError:
        return None


def validate_token_expiration(token_data: TokenData) -> bool:
    """Check if token is expired"""
    return datetime.utcnow() < token_data.exp
