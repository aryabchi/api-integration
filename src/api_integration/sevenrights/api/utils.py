import logging
from functools import wraps
from typing import Callable, Tuple, Type

import requests
from pydantic import ValidationError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)

# (no absolute imports needed; package-relative)

logger = logging.getLogger(__name__)


def _normalize_error(error) -> list[str]:
    """Normalize error field to list[str] format."""
    if error is None:
        return []
    if isinstance(error, str):
        return [error]
    if isinstance(error, list):
        return error
    return [str(error)]


def retry_network(
    attempts: int = 3,
    multiplier: int = 2,
    min_wait: float = 1.0,
    max_wait: float = 30.0,
    exception_types: Tuple[Type[Exception], ...] = (requests.ConnectionError,),
    logger: logging.Logger | None = None,
) -> Callable:
    """
    Decorator factory that returns a retry decorator for transient network errors.

    Args:
        attempts: Maximum number of total attempts.
        multiplier: Exponential backoff multiplier.
        min_wait: Minimum wait time in seconds.
        max_wait: Maximum wait time in seconds.
        exception_types: Tuple of exception types to retry on.
        logger: Logger instance; defaults to the caller module logger.

    Returns:
        Decorator that retries the wrapped callable on specified exceptions.
    """

    def decorator(func: Callable) -> Callable:
        _logger = logger or logging.getLogger(func.__module__)
        _retry = retry(
            stop=stop_after_attempt(attempts),
            wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
            retry=retry_if_exception_type(exception_types),
            before_sleep=before_sleep_log(_logger, logging.WARNING),
        )

        @_retry
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def _print_validation_errors(exc: ValidationError) -> None:
    logger.info("VALIDATION FAILED")
    logger.info("=" * 80)

    for idx, error in enumerate(exc.errors(), start=1):
        field = ".".join(str(x) for x in error["loc"])
        message = error["msg"]
        error_type = error["type"]

        logger.info(f"[{idx}] Field : {field}")
        logger.info(f"    Type  : {error_type}")
        logger.info(f"    Error : {message}")

    logger.info("=" * 80)
