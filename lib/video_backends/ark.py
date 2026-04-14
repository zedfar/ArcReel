"""ArkVideoBackend — Volcano Ark video generation backend."""

from __future__ import annotations

import asyncio
import logging

import httpx

from lib.ark_shared import create_ark_client
from lib.providers import PROVIDER_ARK
from lib.retry import DOWNLOAD_BACKOFF_SECONDS, DOWNLOAD_MAX_ATTEMPTS, with_retry_async
from lib.video_backends.base import (
    VideoCapability,
    VideoGenerationRequest,
    VideoGenerationResult,
    download_video,
    poll_with_retry,
)

logger = logging.getLogger(__name__)


class ArkVideoBackend:
    """Ark (Volcano Ark) video generation backend."""

    DEFAULT_MODEL = "doubao-seedance-1-5-pro-251215"

    _MODEL_CAPABILITIES: dict[str, set[VideoCapability]] = {
        "doubao-seedance-2-0-260128": {
            VideoCapability.TEXT_TO_VIDEO,
            VideoCapability.IMAGE_TO_VIDEO,
            VideoCapability.GENERATE_AUDIO,
            VideoCapability.SEED_CONTROL,
        },
        "doubao-seedance-2-0-fast-260128": {
            VideoCapability.TEXT_TO_VIDEO,
            VideoCapability.IMAGE_TO_VIDEO,
            VideoCapability.GENERATE_AUDIO,
            VideoCapability.SEED_CONTROL,
        },
    }

    _DEFAULT_CAPABILITIES: set[VideoCapability] = {
        VideoCapability.TEXT_TO_VIDEO,
        VideoCapability.IMAGE_TO_VIDEO,
        VideoCapability.GENERATE_AUDIO,
        VideoCapability.SEED_CONTROL,
        VideoCapability.FLEX_TIER,
    }

    def __init__(
        self,
        *,
        api_key: str | None = None,
        model: str | None = None,
    ):
        self._client = create_ark_client(api_key=api_key)
        self._model = model or self.DEFAULT_MODEL
        self._capabilities = self._MODEL_CAPABILITIES.get(self._model, self._DEFAULT_CAPABILITIES)

    @property
    def name(self) -> str:
        return PROVIDER_ARK

    @property
    def model(self) -> str:
        return self._model

    @property
    def capabilities(self) -> set[VideoCapability]:
        return self._capabilities

    async def generate(self, request: VideoGenerationRequest) -> VideoGenerationResult:
        """Generate video. Task creation and polling phases have separate retry, avoiding transient errors that cause task recreation."""
        task_id = await self._create_task(request)
        return await self._poll_until_done(task_id, request)

    @with_retry_async()
    async def _create_task(self, request: VideoGenerationRequest) -> str:
        """Create an Ark video generation task (with retry protection)."""
        # 1. Build content list
        content = [{"type": "text", "text": request.prompt}]

        if request.start_image:
            from lib.image_backends.base import image_to_base64_data_uri

            data_uri = image_to_base64_data_uri(request.start_image)
            content.append(
                {
                    "type": "image_url",
                    "image_url": {"url": data_uri},
                }
            )

        # 2. Build API params
        create_params = {
            "model": self._model,
            "content": content,
            "ratio": request.aspect_ratio,
            "duration": request.duration_seconds,
            "resolution": request.resolution,
            "generate_audio": request.generate_audio,
            "watermark": False,
            "service_tier": request.service_tier,
        }
        if request.seed is not None:
            create_params["seed"] = request.seed

        # 3. Create task (sync SDK call, run in executor)
        create_result = await asyncio.to_thread(
            self._client.content_generation.tasks.create,
            **create_params,
        )
        logger.info("Ark task created: %s", create_result.id)
        return create_result.id

    @staticmethod
    @with_retry_async(
        max_attempts=DOWNLOAD_MAX_ATTEMPTS,
        backoff_seconds=DOWNLOAD_BACKOFF_SECONDS,
        retry_if=lambda e: (
            isinstance(e, httpx.HTTPStatusError)
            and e.response.status_code == 400
            and "video_not_ready" in str(e.response.text)
        ),
    )
    async def _download_video_with_retry(video_url: str, output_path) -> None:
        """Separately retry video download to avoid quota waste from regenerating video on download failure.

        Ark video URL may not be ready even after task succeeds (returns 400 video_not_ready).
        Retry only for this transient state; other HTTP errors and network transients are handled by inner download_video.
        """
        await download_video(video_url, output_path)

    async def _poll_until_done(self, task_id: str, request: VideoGenerationRequest) -> VideoGenerationResult:
        """Poll task status until completion. Retry transient errors only for the current poll request."""
        poll_interval = 10 if request.service_tier == "default" else 60
        max_wait_time = 600 if request.service_tier == "default" else 3600

        result = await poll_with_retry(
            poll_fn=lambda: asyncio.to_thread(self._client.content_generation.tasks.get, task_id=task_id),
            is_done=lambda r: r.status == "succeeded",
            is_failed=lambda r: (
                f"Ark video generation failed: {getattr(r, 'error', None) or 'Unknown error'}"
                if r.status in ("failed", "expired")
                else None
            ),
            poll_interval=poll_interval,
            max_wait=max_wait_time,
            label="Ark",
            on_progress=lambda r, elapsed: logger.info(
                "Ark video generating... Status: %s, waited %d seconds", r.status, int(elapsed)
            ),
        )

        # Download video
        video_url = result.content.video_url
        await self._download_video_with_retry(video_url, request.output_path)

        # Extract result metadata
        seed = getattr(result, "seed", None)
        usage_tokens = None
        if hasattr(result, "usage") and result.usage:
            usage_tokens = getattr(result.usage, "completion_tokens", None)

        return VideoGenerationResult(
            video_path=request.output_path,
            provider=PROVIDER_ARK,
            model=self._model,
            duration_seconds=request.duration_seconds,
            video_uri=video_url,
            seed=seed,
            usage_tokens=usage_tokens,
            task_id=task_id,
            generate_audio=request.generate_audio,
        )
