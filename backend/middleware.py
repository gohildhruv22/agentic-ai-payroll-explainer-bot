"""
HTTP middleware: per-IP rate limiting and API request logging.

Rate limit counts requests per client IP in a 60s sliding window. Logging skips non-/api paths.
"""
import time
import logging
from collections import defaultdict
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from config import RATE_LIMIT_PER_MINUTE

logger = logging.getLogger("payroll_bot")

request_counts = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window = 60

        request_counts[client_ip] = [
            t for t in request_counts[client_ip] if now - t < window
        ]

        if len(request_counts[client_ip]) >= RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Please try again later."}
            )

        request_counts[client_ip].append(now)

        try:
            response = await call_next(request)
            return response
        except Exception as e:
            logger.error(f"Unhandled error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={"detail": "Internal server error. Please try again later."}
            )


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        duration = time.time() - start_time

        if not request.url.path.startswith("/api/"):
            return response

        logger.info(
            f"{request.method} {request.url.path} "
            f"- Status: {response.status_code} "
            f"- Duration: {duration:.3f}s"
        )
        return response
