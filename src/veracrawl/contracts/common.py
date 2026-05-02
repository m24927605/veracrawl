"""Shared contract primitives."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, field_validator

Ref: TypeAlias = str


def utc_now() -> datetime:
    return datetime.now(tz=UTC)


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", exclude_none=False)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list | tuple | set):
        return [_jsonable(item) for item in value]
    return value


def canonical_json(value: Any) -> str:
    value = _jsonable(value)
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def stable_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class VeraModel(BaseModel):
    """Base model for executable VeraCrawl contracts."""

    model_config = ConfigDict(extra="forbid", validate_assignment=True, populate_by_name=True)

    def canonical_json(self) -> str:
        return canonical_json(self)

    def content_hash(self) -> str:
        return stable_hash(self)


class TimestampedModel(VeraModel):
    created_at: datetime = Field(default_factory=utc_now)

    @field_validator("created_at")
    @classmethod
    def require_utc(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamp must be timezone-aware")
        return value.astimezone(UTC)
