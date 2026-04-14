"""
Grok (xAI) shared utility module.

Shared by text_backends / image_backends / video_backends.

Contains:
- create_grok_client — xAI AsyncClient client factory
"""

from __future__ import annotations


def create_grok_client(*, api_key: str | None = None):
    """Create xAI AsyncClient, validate and construct it."""
    import xai_sdk

    if not api_key:
        raise ValueError("XAI_API_KEY not set\nConfigure xAI API Key on the system configuration page")
    return xai_sdk.AsyncClient(api_key=api_key)
