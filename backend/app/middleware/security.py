from fastapi import Request, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import redis
from typing import Dict, Optional
from ..utils.security import SecurityManager

security_manager = SecurityManager("your-secret-key-change-in-production")
security = HTTPBearer()
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
    
    async def dispatch(self, request: Request, call_next):
        # Get client IP
        client_ip = request.client.host
        
        # Check rate limit
        key = f"rate_limit:{client_ip}"
        current = redis_client.get(key)
        
        if current is None:
            redis_client.setex(key, self.period, 1)
        elif int(current) >= self.calls:
            raise HTTPException(status_code=429, detail="Rate limit exceeded")
        else:
            redis_client.incr(key)
        
        response = await call_next(request)
        return response

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        
        return response

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify JWT token and return current user"""
    token = credentials.credentials
    payload = security_manager.verify_token(token, "access")
    
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return payload

class AuditLogger:
    @staticmethod
    def log_operation(user_id: str, operation: str, resource: str, details: Dict = None):
        """Log security-relevant operations"""
        log_entry = {
            "timestamp": time.time(),
            "user_id": user_id,
            "operation": operation,
            "resource": resource,
            "details": details or {}
        }
        
        # Store in Redis for immediate access
        redis_client.lpush("audit_logs", str(log_entry))
        
        # Keep only last 10000 entries
        redis_client.ltrim("audit_logs", 0, 9999)