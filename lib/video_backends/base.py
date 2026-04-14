"""Video generation service layer core interface definitions and shared utilities."""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

import httpx

from lib.retry import BASE_RETRYABLE_ERRORS, _should_retry, with_retry_async

logger = logging.getLogger(__name__)

# Image suffix → MIME type mapping (shared by multiple backends)
IMAGE_MIME_TYPES: dict[str, str] = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".webp": "image/webp",
}


async def poll_with_retry[T](
    *,
    poll_fn: Callable[[], Awaitable[T]],
    is_done: Callable[[T], bool],
    is_failed: Callable[[T], str | None],
    poll_interval: float,
    max_wait: float,
    retryable_errors: tuple[type[Exception], ...] = BASE_RETRYABLE_ERRORS,
    label: str = "",
    on_progress: Callable[[T, float], None] | None = None,
) -> T:
    """Generic async polling helper with transient error retry and timeout control.

    Args:
        poll_fn: Async function called each poll, returns latest status.
        is_done: Determines if poll result indicates task completion.
        is_failed: Determines if poll result indicates task failure, returns error message or None.
        poll_interval: Interval between polls (seconds).
        max_wait: Maximum wait time (seconds), raises TimeoutError on timeout.
        retryable_errors: Tuple of retryable exception types.
        label: Log prefix (e.g. "Ark", "Gemini").
        on_progress: Optional progress callback, called after each non-terminal poll.
    """
    start = time.monotonic()
    prefix = f"{label} " if label else ""

    while True:
        elapsed = time.monotonic() - start
        if elapsed >= max_wait:
            raise TimeoutError(f"{prefix}Task timeout ({max_wait:.0f} seconds)")

        await asyncio.sleep(poll_interval)

        try:
            result = await poll_fn()
        except Exception as e:
            if _should_retry(e, retryable_errors):
                logger.warning("%sPolling exception (will retry): %s - %s", prefix, type(e).__name__, str(e)[:200])
                continue
            raise

        error_msg = is_failed(result)
        if error_msg is not None:
            raise RuntimeError(error_msg)

        if is_done(result):
            return result

        if on_progress is not None:
            on_progress(result, time.monotonic() - start)


@with_retry_async()
async def download_video(url: str, output_path: Path, *, timeout: int = 120) -> None:
    """Stream download video from URL to local file (with transient error retry)."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    async with httpx.AsyncClient() as http_client:
        async with http_client.stream("GET", url, timeout=timeout) as resp:
            if resp.status_code >= 400:
                # In streaming mode, must read response body first, otherwise HTTPStatusError.response.text is unavailable
                await resp.aread()
            resp.raise_for_status()
            with open(output_path, "wb") as f:
                async for chunk in resp.aiter_bytes(chunk_size=65536):
                    f.write(chunk)


class VideoCapability(StrEnum):
    """Video backend capability enumeration."""

    TEXT_TO_VIDEO = "text_to_video"
    IMAGE_TO_VIDEO = "image_to_video"
    GENERATE_AUDIO = "generate_audio"
    NEGATIVE_PROMPT = "negative_prompt"
    VIDEO_EXTEND = "video_extend"
    SEED_CONTROL = "seed_control"
    FLEX_TIER = "flex_tier"


@dataclass
class VideoGenerationRequest:
    """Generic video generation request. Each Backend ignores unsupported fields."""

    prompt: str
    output_path: Path
    aspect_ratio: str = "9:16"
    duration_seconds: int = 5
    resolution: str = "1080p"
    start_image: Path | None = None
    generate_audio: bool = True

    # Veo-specific
    negative_prompt: str | None = None

    # Project context (for constructing file service URLs, etc.)
    project_name: str | None = None

    # Seedance-specific
    service_tier: str = "default"
    seed: int | None = None


@dataclass
class VideoGenerationResult:
    """Generic video generation result."""

    video_path: Path
    provider: str
    model: str
    duration_seconds: int

    video_uri: str | None = None
    seed: int | None = None
    usage_tokens: int | None = None
    task_id: str | None = None
    generate_audio: bool | None = None


class VideoBackend(Protocol):
    """Video generation backend protocol."""

    @property
    def name(self) -> str: ...

    @property
    def model(self) -> str: ...

    @property
    def capabilities(self) -> set[VideoCapability]: ...

    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult: ...
