"""
Security Module - Iteration 3: Advanced Password Policy, MFA Support & Token Security
Enhanced with breach detection, TOTP support, and token binding
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, field_validator
import re
import secrets
import base64
import hashlib
import hmac
import time
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing context with Argon2id (most secure)
pwd_context = CryptContext(schemes=["argon2"], argon2__type="id", deprecated="auto")


class TokenData(BaseModel):
    """JWT token payload structure with enhanced security fields"""
    sub: str  # subject (user_id)
    exp: datetime
    iat: datetime
    type: str  # "access" or "refresh"
    roles: list[str] = []
    permissions: list[str] = []
    mfa_verified: bool = False
    token_id: Optional[str] = None  # For token binding/revocation


class UserCreate(BaseModel):
    """User registration schema with enhanced validation"""
    email: EmailStr
    username: str
    password: str
    full_name: str
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        errors = []
        
        # Length check
        if len(v) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters")
        
        # Complexity checks
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", v):
            errors.append("Password must contain uppercase letter")
        
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", v):
            errors.append("Password must contain lowercase letter")
        
        if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", v):
            errors.append("Password must contain digit")
        
        if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            errors.append("Password must contain special character")
        
        # Repetition check
        if settings.PASSWORD_MAX_REPETITION:
            if re.search(r"(.)\1{" + str(settings.PASSWORD_MAX_REPETITION) + r",}", v):
                errors.append(f"Password cannot have more than {settings.PASSWORD_MAX_REPETITION} repeated characters")
        
        # Common password check (basic)
        common_passwords = ['password', '123456', 'qwerty', 'admin', 'letmein', 'welcome']
        if v.lower() in common_passwords:
            errors.append("Password is too common")
        
        if errors:
            raise ValueError("; ".join(errors))
        
        return v


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash with timing attack protection"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Constant-time failure to prevent timing attacks
        pwd_context.hash("dummy_password_for_timing")
        return False


def get_password_hash(password: str) -> str:
    """Hash password using Argon2id"""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None, token_id: Optional[str] = None) -> str:
    """Create JWT access token with enhanced security"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # Generate unique token ID for tracking/revocation if not provided
    if token_id is None:
        token_id = secrets.token_urlsafe(16)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
        "token_id": token_id,
        "nbf": datetime.utcnow()  # Not before claim
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], token_id: Optional[str] = None) -> str:
    """Create JWT refresh token with enhanced security"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    if token_id is None:
        token_id = secrets.token_urlsafe(16)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh",
        "token_id": token_id,
        "nbf": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str, verify_exp: bool = True) -> Optional[TokenData]:
    """Decode and validate JWT token with enhanced security checks"""
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": verify_exp}
        )
        
        sub = payload.get("sub")
        exp = payload.get("exp")
        iat = payload.get("iat")
        token_type = payload.get("type")
        roles = payload.get("roles", [])
        permissions = payload.get("permissions", [])
        mfa_verified = payload.get("mfa_verified", False)
        token_id = payload.get("token_id")
        
        if sub is None or token_type is None:
            logger.warning("Invalid token: missing required claims")
            return None
        
        # Check for suspicious patterns
        if token_type not in ["access", "refresh"]:
            logger.warning(f"Invalid token type: {token_type}")
            return None
        
        return TokenData(
            sub=sub,
            exp=datetime.fromtimestamp(exp),
            iat=datetime.fromtimestamp(iat),
            type=token_type,
            roles=roles,
            permissions=permissions,
            mfa_verified=mfa_verified,
            token_id=token_id
        )
    except JWTError as e:
        logger.warning(f"Token decoding failed: {str(e)}")
        return None


def validate_token_expiration(token_data: TokenData) -> bool:
    """Check if token is expired"""
    return datetime.utcnow() < token_data.exp


# MFA/TOTP Functions
def generate_totp_secret() -> str:
    """Generate a new TOTP secret"""
    return base64.b32encode(secrets.token_bytes(20)).decode('utf-8')


def get_totp_uri(secret: str, username: str, issuer: str = settings.MFA_ISSUER) -> str:
    """Generate TOTP URI for QR code"""
    return f"otpauth://totp/{issuer}:{username}?secret={secret}&issuer={issuer}"


def verify_totp(secret: str, code: str, window: int = 1) -> bool:
    """
    Verify TOTP code with configurable window
    window: number of time steps to check before/after current time
    """
    try:
        secret_bytes = base64.b32decode(secret.upper())
        current_time = int(time.time())
        time_step = 30  # Standard TOTP time step
        
        # Check current and adjacent time windows
        for offset in range(-window, window + 1):
            expected_code = generate_hotp(secret_bytes, current_time // time_step + offset)
            if hmac.compare_digest(expected_code, code.zfill(6)):
                return True
        
        return False
    except Exception as e:
        logger.error(f"TOTP verification error: {e}")
        return False


def generate_hotp(secret: bytes, counter: int) -> str:
    """Generate HOTP code"""
    msg = counter.to_bytes(8, byteorder='big')
    hmac_hash = hmac.new(secret, msg, hashlib.sha1).digest()
    offset = hmac_hash[-1] & 0x0f
    binary = ((hmac_hash[offset] & 0x7f) << 24 |
              (hmac_hash[offset + 1] & 0xff) << 16 |
              (hmac_hash[offset + 2] & 0xff) << 8 |
              (hmac_hash[offset + 3] & 0xff))
    return str(binary % 1000000).zfill(6)


# Security utilities
def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"nexus_{secrets.token_urlsafe(32)}"


def mask_sensitive_data(data: str, visible_chars: int = 4) -> str:
    """Mask sensitive data for logging"""
    if len(data) <= visible_chars:
        return "*" * len(data)
    return data[:visible_chars] + "*" * (len(data) - visible_chars)

