"""
API Key management routes.

Provides endpoints for creating, listing, and deleting API Keys.
"""

import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.exc import IntegrityError

from lib.db import async_session_factory
from lib.db.repositories.api_key_repository import ApiKeyRepository
from server.auth import (
    API_KEY_PREFIX,
    CurrentUser,
    CurrentUserInfo,
    _hash_api_key,
    invalidate_api_key_cache,
)

router = APIRouter()


def _require_jwt_auth(user: CurrentUserInfo) -> None:
    """Ensure request is authenticated with JWT (not API Key). API Key management operations cannot be executed by API Key itself."""
    if user.sub.startswith("apikey:"):
        raise HTTPException(status_code=403, detail="API Key cannot perform this operation, please use JWT authentication")


API_KEY_DEFAULT_EXPIRY_DAYS = 30


def _generate_api_key() -> str:
    """Generate API Key in format arc-<32 random hex characters>."""
    random_part = secrets.token_hex(16)  # 32 hex chars
    return f"{API_KEY_PREFIX}{random_part}"


def _default_expires_at() -> datetime:
    return datetime.now(UTC) + timedelta(days=API_KEY_DEFAULT_EXPIRY_DAYS)


class CreateApiKeyRequest(BaseModel):
    name: str
    expires_days: int | None = Field(None, ge=0)  # None uses default 30 days, 0 means never expires


class CreateApiKeyResponse(BaseModel):
    id: int
    name: str
    key: str  # Full key, returned only on creation
    key_prefix: str
    created_at: str
    expires_at: str | None


class ApiKeyInfo(BaseModel):
    id: int
    name: str
    key_prefix: str
    created_at: str
    expires_at: str | None
    last_used_at: str | None


@router.post("/api-keys", status_code=201)
async def create_api_key(
    body: CreateApiKeyRequest,
    _user: CurrentUser,
) -> CreateApiKeyResponse:
    """Create new API Key. Full key appears in response only once, cannot be viewed afterwards."""
    _require_jwt_auth(_user)
    key = _generate_api_key()
    key_hash = _hash_api_key(key)
    key_prefix = key[:8]  # e.g. "arc-abcd"

    if body.expires_days == 0:
        expires_at: datetime | None = None
    elif body.expires_days is not None:
        expires_at = datetime.now(UTC) + timedelta(days=body.expires_days)
    else:
        expires_at = _default_expires_at()

    try:
        async with async_session_factory() as session:
            async with session.begin():
                repo = ApiKeyRepository(session)
                row = await repo.create(
                    name=body.name,
                    key_hash=key_hash,
                    key_prefix=key_prefix,
                    expires_at=expires_at,
                )
    except IntegrityError:
        raise HTTPException(status_code=409, detail=f"Name '{body.name}' already exists")

    return CreateApiKeyResponse(
        id=row["id"],
        name=row["name"],
        key=key,
        key_prefix=row["key_prefix"],
        created_at=row["created_at"],
        expires_at=row["expires_at"],
    )


@router.get("/api-keys")
async def list_api_keys(
    _user: CurrentUser,
) -> list[ApiKeyInfo]:
    """Query metadata of all API Keys (without full key)."""
    _require_jwt_auth(_user)
    async with async_session_factory() as session:
        async with session.begin():
            repo = ApiKeyRepository(session)
            rows = await repo.list_all()

    return [ApiKeyInfo(**row) for row in rows]


@router.delete("/api-keys/{key_id}", status_code=204)
async def delete_api_key(
    key_id: int,
    _user: CurrentUser,
) -> None:
    """Delete (revoke) specified API Key and immediately clear in-memory cache."""
    _require_jwt_auth(_user)
    async with async_session_factory() as session:
        async with session.begin():
            repo = ApiKeyRepository(session)
            row = await repo.get_by_id(key_id)
            if row is None:
                raise HTTPException(status_code=404, detail=f"API Key {key_id} does not exist")
            key_hash = row["key_hash"]
            # Invalidate cache before deleting from DB: even if the transaction crashes after commit,
            # cache is already cleared, preventing a grace period where DB is deleted but cache still valid.
            invalidate_api_key_cache(key_hash)
            deleted = await repo.delete(key_id)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"API Key {key_id} does not exist")
