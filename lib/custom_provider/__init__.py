"""Custom provider module."""

CUSTOM_PROVIDER_PREFIX = "custom-"


def make_provider_id(db_id: int) -> str:
    """Construct custom provider provider_id string, e.g. 'custom-3'."""
    return f"{CUSTOM_PROVIDER_PREFIX}{db_id}"


def parse_provider_id(provider_id: str) -> int:
    """Extract database ID from provider_id in format 'custom-3'.

    Raises:
        ValueError: if format is incorrect
    """
    return int(provider_id.removeprefix(CUSTOM_PROVIDER_PREFIX))


def is_custom_provider(provider_id: str) -> bool:
    """Check if provider_id is a custom provider."""
    return provider_id.startswith(CUSTOM_PROVIDER_PREFIX)
