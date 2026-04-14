"""
Ark (Volcano Ark) shared utility module.

Shared by text_backends / image_backends / video_backends / providers.

Contains:
- ARK_BASE_URL — Volcano Ark API base URL
- resolve_ark_api_key — API Key resolution (with environment variable fallback)
- create_ark_client — Ark client factory
"""

from __future__ import annotations

import os

ARK_BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"


def resolve_ark_api_key(api_key: str | None = None) -> str:
    """Resolve Ark API Key with environment variable fallback."""
    resolved = api_key or os.environ.get("ARK_API_KEY")
    if not resolved:
        raise ValueError("Ark API Key not provided. Configure it on the Global Settings → Providers page.")
    return resolved


def create_ark_client(*, api_key: str | None = None):
    """Create Ark client, validate api_key and construct it."""
    from volcenginesdkarkruntime import Ark

    return Ark(base_url=ARK_BASE_URL, api_key=resolve_ark_api_key(api_key))
