import time
import logging
from typing import dict, tuple
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

class SimpleRateLimiter(BaseHTTPMiddleware):
    """Simple in-memory sliding window rate limiter to protect Gemini quota."""
    
    def __init__(self, app, max_requests: int = 15, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        # Store structured as client_ip: (request_timestamps_list)
        self.requests: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next):
        # We only rate limit API routes that interact with Gemini (ingest, chat)
        if not (request.url.path.startswith("/api/chat") or request.url.path.startswith("/api/ingest")):
            return await call_next(request)
            
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        
        # Initialize or clean old requests
        if client_ip not in self.requests:
            self.requests[client_ip] = []
            
        # Filter timestamps within window
        self.requests[client_ip] = [
            t for t in self.requests[client_ip] if now - t < self.window_seconds
        ]
        
        if len(self.requests[client_ip]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for IP: {client_ip} on path {request.url.path}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please wait a minute to protect API limits."
            )
            
        # Log request
        self.requests[client_ip].append(now)
        return await call_next(request)
