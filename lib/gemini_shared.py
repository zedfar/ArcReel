"""
Gemini shared utility module.

Non-GeminiClient utilities extracted from gemini_client.py for reuse by image_backends / video_backends /
providers / media_generator and other modules, avoiding circular dependencies.

Contains:
- VERTEX_SCOPES — Vertex AI OAuth scopes
- RETRYABLE_ERRORS — Gemini-specific retryable error types (extends BASE_RETRYABLE_ERRORS)
- RateLimiter — Multi-model sliding window rate limiter
- _rate_limiter_limits_from_env / get_shared_rate_limiter / refresh_shared_rate_limiter
- with_retry_async — Generic retry decorator re-exported from lib.retry
"""

import asyncio
import logging
import threading
import time
from collections import deque
from typing import Optional

from .cost_calculator import cost_calculator
from .retry import BASE_RETRYABLE_ERRORS, with_retry_async

__all__ = [
    "BASE_RETRYABLE_ERRORS",
    "RETRYABLE_ERRORS",
    "VERTEX_SCOPES",
    "RateLimiter",
    "get_shared_rate_limiter",
    "refresh_shared_rate_limiter",
    "with_retry_async",
]

logger = logging.getLogger(__name__)

# OAuth scopes required for Vertex AI service account (shared constant, reused by gemini_client / video_backends / providers)
VERTEX_SCOPES = [
    "https://www.googleapis.com/auth/cloud-platform",
    "https://www.googleapis.com/auth/generative-language",
]

# Gemini-specific retryable error types (extends the base set)
RETRYABLE_ERRORS: tuple[type[Exception], ...] = BASE_RETRYABLE_ERRORS

# Attempt to import Google API error types
try:
    from google import genai  # Import genai to access its errors
    from google.api_core import exceptions as google_exceptions

    RETRYABLE_ERRORS = RETRYABLE_ERRORS + (
        google_exceptions.ResourceExhausted,  # 429 Too Many Requests
        google_exceptions.ServiceUnavailable,  # 503
        google_exceptions.DeadlineExceeded,  # Timeout
        google_exceptions.InternalServerError,  # 500
        genai.errors.ClientError,  # 4xx errors from new SDK
        genai.errors.ServerError,  # 5xx errors from new SDK
    )
except ImportError:
    pass


class RateLimiter:
    """
    Multi-model sliding window rate limiter
    """

    def __init__(self, limits_dict: dict[str, int] = None, *, request_gap: float = 3.1):
        """
        Args:
            limits_dict: {model_name: rpm} dictionary. Example: {"gemini-3-pro-image-preview": 20}
            request_gap: Minimum request interval (seconds), default 3.1
        """
        self.limits = limits_dict or {}
        self.request_gap = request_gap
        # Store request timestamps: {model_name: deque([timestamp1, timestamp2, ...])}
        self.request_logs: dict[str, deque] = {}
        self.lock = threading.Lock()

    def acquire(self, model_name: str):
        """
        Block until a token is acquired
        """
        if model_name not in self.limits:
            return  # No rate limit configured for this model

        limit = self.limits[model_name]
        if limit <= 0:
            return

        with self.lock:
            if model_name not in self.request_logs:
                self.request_logs[model_name] = deque()

            log = self.request_logs[model_name]

            while True:
                now = time.time()

                # Clean up old records older than 60 seconds
                while log and now - log[0] > 60:
                    log.popleft()

                # Enforce minimum request interval (user requirement > 3s)
                # Even after acquiring a token, ensure at least 3s gap from the last request
                # Get the latest request time (may have just been written by another thread)
                min_gap = self.request_gap
                if log:
                    last_request = log[-1]
                    gap = time.time() - last_request
                    if gap < min_gap:
                        time.sleep(min_gap - gap)
                        # Update time, check again
                        continue

                if len(log) < limit:
                    # Token acquired successfully
                    log.append(time.time())
                    return

                # Limit reached, calculate wait time
                # Wait until the earliest record expires
                wait_time = 60 - (now - log[0]) + 0.1  # Add 0.1s buffer
                if wait_time > 0:
                    time.sleep(wait_time)

    async def acquire_async(self, model_name: str):
        """
        Async block until a token is acquired
        """
        if model_name not in self.limits:
            return  # No rate limit configured for this model

        limit = self.limits[model_name]
        if limit <= 0:
            return

        while True:
            with self.lock:
                now = time.time()

                if model_name not in self.request_logs:
                    self.request_logs[model_name] = deque()

                log = self.request_logs[model_name]

                # Clean up old records older than 60 seconds
                while log and now - log[0] > 60:
                    log.popleft()

                min_gap = self.request_gap
                wait_needed = 0
                if log:
                    last_request = log[-1]
                    gap = now - last_request
                    if gap < min_gap:
                        # Release lock and wait asynchronously
                        wait_needed = min_gap - gap

                if len(log) >= limit:
                    # Limit reached, calculate wait time
                    wait_needed = max(wait_needed, 60 - (now - log[0]) + 0.1)

                if wait_needed == 0 and len(log) < limit:
                    # Token acquired successfully
                    log.append(now)
                    return

            # Async wait outside the lock
            if wait_needed > 0:
                await asyncio.sleep(wait_needed)
            else:
                await asyncio.sleep(0.1)  # Briefly yield control


_SHARED_IMAGE_MODEL_NAME = cost_calculator.DEFAULT_IMAGE_MODEL
_SHARED_VIDEO_MODEL_NAME = cost_calculator.DEFAULT_VIDEO_MODEL

_shared_rate_limiter: Optional["RateLimiter"] = None
_shared_rate_limiter_lock = threading.Lock()


def _rate_limiter_limits_from_env(
    *,
    image_rpm: int | None = None,
    video_rpm: int | None = None,
    image_model: str | None = None,
    video_model: str | None = None,
) -> dict[str, int]:
    if image_rpm is None:
        image_rpm = 15
    if video_rpm is None:
        video_rpm = 10
    if image_model is None:
        image_model = _SHARED_IMAGE_MODEL_NAME
    if video_model is None:
        video_model = _SHARED_VIDEO_MODEL_NAME

    limits: dict[str, int] = {}
    if image_rpm > 0:
        limits[image_model] = image_rpm
    if video_rpm > 0:
        limits[video_model] = video_rpm
    return limits


def get_shared_rate_limiter(
    *,
    image_rpm: int | None = None,
    video_rpm: int | None = None,
    image_model: str | None = None,
    video_model: str | None = None,
    request_gap: float | None = None,
) -> "RateLimiter":
    """
    Get the process-wide shared RateLimiter

    On first call, creates an instance based on parameters or environment variables.
    Subsequent calls return the same instance.

    - image_rpm / video_rpm: Requests per minute limit (read from environment variables if None)
    - request_gap: Minimum request interval (read from GEMINI_REQUEST_GAP environment variable if None, default 3.1)
    """
    global _shared_rate_limiter
    if _shared_rate_limiter is not None:
        return _shared_rate_limiter

    with _shared_rate_limiter_lock:
        if _shared_rate_limiter is not None:
            return _shared_rate_limiter

        limits = _rate_limiter_limits_from_env(
            image_rpm=image_rpm,
            video_rpm=video_rpm,
            image_model=image_model,
            video_model=video_model,
        )
        if request_gap is None:
            request_gap = 3.1
        _shared_rate_limiter = RateLimiter(limits, request_gap=request_gap)
        return _shared_rate_limiter


def refresh_shared_rate_limiter(
    *,
    image_rpm: int | None = None,
    video_rpm: int | None = None,
    image_model: str | None = None,
    video_model: str | None = None,
    request_gap: float | None = None,
) -> "RateLimiter":
    """
    Refresh the process-wide shared RateLimiter in-place.

    Updates model keys and request_gap. Parameters default to env vars when None.
    """
    limiter = get_shared_rate_limiter()
    new_limits = _rate_limiter_limits_from_env(
        image_rpm=image_rpm,
        video_rpm=video_rpm,
        image_model=image_model,
        video_model=video_model,
    )

    with limiter.lock:
        limiter.limits = new_limits
        if request_gap is not None:
            limiter.request_gap = request_gap

    return limiter
