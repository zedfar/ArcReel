"""Generic retry decorator with exponential backoff and jitter.

Does not depend on any specific provider SDK, can be reused by all backends.
Each provider can inject its own retryable exception types via retryable_errors parameter,
or implement fine-grained conditional retry via retry_if predicate.
"""

from __future__ import annotations

import asyncio
import functools
import logging
import random
from collections.abc import Callable

logger = logging.getLogger(__name__)

# Base retryable errors (does not depend on any SDK)
BASE_RETRYABLE_ERRORS: tuple[type[Exception], ...] = (
    ConnectionError,
    TimeoutError,
)

# String pattern matching: covers exception types not in list but are transient (case insensitive)
RETRYABLE_STATUS_PATTERNS = (
    "429",
    "resource_exhausted",
    "500",
    "502",
    "503",
    "504",
    "internalservererror",
    "internal server error",
    "serviceunavailable",
    "service unavailable",
    "bad gateway",
    "gateway timeout",
    "timed out",
    "timeout",
)

# Default retry config, referenced directly by backends to avoid magic numbers scattered in 9+ places
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_SECONDS: tuple[int, ...] = (2, 4, 8)

# Download phase retry config (more tolerant than generation phase because download failure doesn't waste quota)
DOWNLOAD_MAX_ATTEMPTS = 5
DOWNLOAD_BACKOFF_SECONDS: tuple[int, ...] = (5, 10, 20, 40)


def _should_retry(exc: Exception, retryable_errors: tuple[type[Exception], ...]) -> bool:
    """Determine whether an exception should be retried."""
    if isinstance(exc, retryable_errors):
        return True
    error_lower = str(exc).lower()
    return any(pattern in error_lower for pattern in RETRYABLE_STATUS_PATTERNS)


def with_retry_async(
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    backoff_seconds: tuple[int, ...] = DEFAULT_BACKOFF_SECONDS,
    retryable_errors: tuple[type[Exception], ...] = BASE_RETRYABLE_ERRORS,
    retry_if: Callable[[Exception], bool] | None = None,
):
    """Async function retry decorator with exponential backoff and jitter.

    When retry_if is specified, use that predicate instead of default _should_retry for retry determination,
    allowing caller precise control over which exceptions should be retried (e.g., only specific HTTP status codes).
    """

    predicate = retry_if if retry_if is not None else lambda e: _should_retry(e, retryable_errors)

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    is_last = attempt >= max_attempts - 1
                    if is_last or not predicate(e):
                        raise
                    wait_time = _compute_wait(attempt, backoff_seconds)
                    logger.warning("API call exception: %s - %s", type(e).__name__, str(e)[:200])
                    logger.warning("Retrying %d/%d in %.1f seconds...", attempt + 1, max_attempts - 1, wait_time)
                    await asyncio.sleep(wait_time)

            raise RuntimeError(f"with_retry_async: max_attempts={max_attempts}, no attempts executed")

        return wrapper

    return decorator


def _compute_wait(attempt: int, backoff_seconds: tuple[int, ...]) -> float:
    """Compute wait time for the attempt-th retry (with jitter)."""
    backoff_idx = min(attempt, len(backoff_seconds) - 1)
    return backoff_seconds[backoff_idx] + random.uniform(0, 2)
