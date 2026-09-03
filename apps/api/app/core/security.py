from datetime import datetime, timedelta, timezone
from enum import Enum
import re
from typing import Any, Dict, Optional
from jose import jwt, JWTError
import hashlib
import os
from apps.api.app.core.config import settings

class UserRole(str, Enum):
    CUSTOMER = "customer"
    SUPPORT_AGENT = "support_agent"
    ADMIN = "admin"

def get_password_hash(password: str) -> str:
    salt = "enterprise_salt_v1"
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt.encode('utf-8'), 100000)
    return key.hex()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return get_password_hash(plain_password) == hashed_password

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None

# Secret and PII Redaction Engine
REDACTION_PATTERNS = [
    (re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'), "[REDACTED_CREDIT_CARD]"),
    (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'), "[REDACTED_EMAIL]"),
    (re.compile(r'(?i)(password|secret|key|token)\s*[:=]\s*["\']?([^"\'\s]+)["\']?'), r'\1: "[REDACTED]"'),
    (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), "[REDACTED_SSN]"),
]

def redact_sensitive_data(val: Any) -> Any:
    """Recursively redacts secrets, PII, and credentials from strings, dicts, and lists."""
    if isinstance(val, str):
        result = val
        for pattern, replacement in REDACTION_PATTERNS:
            result = pattern.sub(replacement, result)
        return result
    elif isinstance(val, dict):
        return {k: redact_sensitive_data(v) for k, v in val.items()}
    elif isinstance(val, list):
        return [redact_sensitive_data(item) for item in val]
    return val
