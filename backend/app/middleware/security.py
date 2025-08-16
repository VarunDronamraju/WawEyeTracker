import time
import redis
from fastapi import Request, HTTPException, status
from fastapi.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Dict

from ..utils.config import settings

# Redis client for rate limiting
try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
except:
    redis_client = None

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        return response

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware"""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.memory_store: Dict[str, Dict] = {}
    
    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path in ["/health", "/metrics"]:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        
        if redis_client:
            # Use Redis for distributed rate limiting
            current = await self._check_redis_limit(client_ip)
        else:
            # Use memory for single instance
            current = self._check_memory_limit(client_ip)
        
        if current > self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(self.calls)
        response.headers["X-RateLimit-Remaining"] = str(max(0, self.calls - current))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host
    
    async def _check_redis_limit(self, client_ip: str) -> int:
        """Check rate limit using Redis"""
        key = f"rate_limit:{client_ip}"
        try:
            current = redis_client.get(key)
            if current is None:
                redis_client.setex(key, self.period, 1)
                return 1
            else:
                return redis_client.incr(key)
        except:
            return 0  # Fail open if Redis is down
    
    def _check_memory_limit(self, client_ip: str) -> int:
        """Check rate limit using memory store"""
        now = time.time()
        
        # Clean old entries
        to_delete = []
        for ip, data in self.memory_store.items():
            if now - data["timestamp"] > self.period:
                to_delete.append(ip)
        
        for ip in to_delete:
            del self.memory_store[ip]
        
        # Check current IP
        if client_ip not in self.memory_store:
            self.memory_store[client_ip] = {"count": 1, "timestamp": now}
            return 1
        else:
            data = self.memory_store[client_ip]
            if now - data["timestamp"] > self.period:
                self.memory_store[client_ip] = {"count": 1, "timestamp": now}
                return 1
            else:
                data["count"] += 1
                return data["count"]