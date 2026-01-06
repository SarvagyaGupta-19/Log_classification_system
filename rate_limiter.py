"""
Rate limiting middleware for production API protection

Implements token bucket algorithm with in-memory storage.
For distributed systems, consider Redis-backed implementation.

Configuration:
- RATE_LIMIT_ENABLED: Enable/disable rate limiting
- RATE_LIMIT_REQUESTS: Max requests per window
- RATE_LIMIT_WINDOW: Time window in seconds

Features:
- Per-IP rate limiting
- Automatic cleanup of expired entries
- Informative error messages with retry-after header
"""
import time
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from logger_config import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Token bucket rate limiter with automatic cleanup"""
    
    def __init__(self, requests_per_window: int, window_seconds: int):
        """
        Initialize rate limiter
        
        Args:
            requests_per_window: Maximum requests allowed in time window
            window_seconds: Time window in seconds
        """
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        # Format: {ip: [(timestamp1, timestamp2, ...)]}
        self.request_history: Dict[str, list] = defaultdict(list)
        self.last_cleanup = time.time()
        self.cleanup_interval = 300  # Clean up every 5 minutes
        
        logger.info("Rate limiter initialized", extra={
            "requests_per_window": requests_per_window,
            "window_seconds": window_seconds
        })
    
    def _cleanup_old_entries(self):
        """Remove expired entries to prevent memory bloat"""
        current_time = time.time()
        
        # Only cleanup every cleanup_interval seconds
        if current_time - self.last_cleanup < self.cleanup_interval:
            return
        
        cutoff_time = current_time - self.window_seconds
        for ip in list(self.request_history.keys()):
            # Remove old timestamps
            self.request_history[ip] = [
                ts for ts in self.request_history[ip] if ts > cutoff_time
            ]
            # Remove IP if no recent requests
            if not self.request_history[ip]:
                del self.request_history[ip]
        
        self.last_cleanup = current_time
        logger.debug("Rate limiter cleanup completed", extra={
            "active_ips": len(self.request_history)
        })
    
    def is_allowed(self, client_ip: str) -> Tuple[bool, int]:
        """
        Check if request is allowed under rate limit
        
        Args:
            client_ip: Client IP address
            
        Returns:
            Tuple of (allowed: bool, retry_after: int seconds)
        """
        current_time = time.time()
        cutoff_time = current_time - self.window_seconds
        
        # Periodic cleanup
        self._cleanup_old_entries()
        
        # Get recent requests from this IP
        recent_requests = [
            ts for ts in self.request_history[client_ip] if ts > cutoff_time
        ]
        
        # Check if limit exceeded
        if len(recent_requests) >= self.requests_per_window:
            # Calculate retry-after: time until oldest request expires
            oldest_request = min(recent_requests)
            retry_after = int(self.window_seconds - (current_time - oldest_request)) + 1
            
            logger.warning("Rate limit exceeded", extra={
                "client_ip": client_ip,
                "requests_count": len(recent_requests),
                "retry_after": retry_after
            })
            
            return False, retry_after
        
        # Allow request and record timestamp
        self.request_history[client_ip].append(current_time)
        return True, 0


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for rate limiting"""
    
    def __init__(self, app, rate_limiter: RateLimiter):
        super().__init__(app)
        self.rate_limiter = rate_limiter
        # Exempt paths that shouldn't be rate limited
        self.exempt_paths = ["/health", "/docs", "/redoc", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Get client IP (consider X-Forwarded-For if behind proxy)
        client_ip = request.headers.get("X-Forwarded-For")
        if not client_ip and request.client:
            client_ip = request.client.host
        elif not client_ip:
            client_ip = "unknown"
        
        if "," in client_ip:
            client_ip = client_ip.split(",")[0].strip()
        
        # Check rate limit
        allowed, retry_after = self.rate_limiter.is_allowed(client_ip)
        
        if not allowed:
            logger.warning("Rate limit blocked request", extra={
                "client_ip": client_ip,
                "path": request.url.path,
                "retry_after": retry_after
            })
            
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.rate_limiter.requests_per_window)
        response.headers["X-RateLimit-Window"] = str(self.rate_limiter.window_seconds)
        
        return response


def create_rate_limiter(requests_per_window: int, window_seconds: int) -> RateLimiter:
    """Factory function to create rate limiter instance"""
    return RateLimiter(requests_per_window, window_seconds)
