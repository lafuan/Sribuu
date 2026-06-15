"""
Structured logging module untuk Sribuu.
Menggunakan structlog dengan output console (development) dan JSON (production).
"""

import logging
import sys
from typing import Any

import structlog

__all__ = ["get_logger", "configure_logging", "structlog"]


def configure_logging(*, debug: bool = False, json_output: bool = False) -> None:
    """Configure structlog for the application.

    Args:
        debug: Enable debug-level logging.
        json_output: Use JSON format (for production/log aggregation).
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso")

    shared_processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.set_exc_info,
        timestamper,
    ]

    if json_output:
        # Production: JSON to stdout, pickled by log aggregators
        structlog.configure(
            processors=[
                *shared_processors,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    else:
        # Development: colored console output
        structlog.configure(
            processors=[
                *shared_processors,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.dev.ConsoleRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

    # Set root logger level
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=level,
    )

    # Silence noisy libraries
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("watchfiles").setLevel(logging.WARNING)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (defaults to module name).

    Returns:
        Configured structlog logger.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("user_login", user_id=42, email="user@example.com")
    """
    return structlog.get_logger(name or __name__)
