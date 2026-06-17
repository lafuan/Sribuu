"""
Request/response logging middleware for Sribuu.
"""

import time
from typing import Callable, cast

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .logging import get_logger

logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware that logs every HTTP request and response with structured data."""

    def __init__(self, app: ASGIApp, skip_paths: list[str] | None = None) -> None:
        super().__init__(app)
        self.skip_paths = skip_paths or ["/health", "/static", "/favicon.ico"]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for certain paths
        path = request.url.path
        if any(path.startswith(p) for p in self.skip_paths):
            return cast(Response, await call_next(request))

        start_time = time.monotonic()
        method = request.method
        client_ip = request.client.host if request.client else "unknown"

        # Log request
        logger.info(
            "request_started",
            method=method,
            path=path,
            client_ip=client_ip,
            query=str(request.query_params) if request.query_params else "",
        )

        try:
            response = cast(Response, await call_next(request))
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)

            # Log response
            logger.info(
                "request_completed",
                method=method,
                path=path,
                status_code=response.status_code,
                duration_ms=duration_ms,
                client_ip=client_ip,
            )
            return response

        except Exception as exc:
            duration_ms = round((time.monotonic() - start_time) * 1000, 2)

            logger.error(
                "request_failed",
                method=method,
                path=path,
                duration_ms=duration_ms,
                client_ip=client_ip,
                error=str(exc),
                error_type=type(exc).__name__,
                exc_info=True,
            )
            raise
