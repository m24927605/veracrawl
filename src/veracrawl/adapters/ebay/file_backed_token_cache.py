"""Phase 3 step 3.4 — file-backed eBay OAuth token cache.

Stores tokens at a caller-supplied path (typical default:
``.veracrawl/cache/ebay-oauth-tokens.json``). Atomic writes
via temp-file + rename. Read returns ``None`` on missing
file / malformed JSON / expired token (with safety margin).

Boundary invariants:

* Identifier shape on ``cache_key`` (codex recurring concern
  #6): pure identifier with optional underscores / dashes;
  refused otherwise so a key can't smuggle path separators.
* Path canonicalization (codex recurring concern #12): the
  cache file path is resolved at construction; reads /
  writes never interpret the cache_key as a path component.
* Atomic writes: temp file + ``os.rename`` so concurrent
  readers see either the prior or the new content, never
  a partial write.
* Stored timestamps are UTC; ``now`` arguments must be
  tz-aware (replay-deterministic clocks are tz-aware).
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_CACHE_KEY_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _ensure_tz_aware(name: str, value: datetime) -> None:
    if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
        raise ValueError(
            f"{name} must be a tz-aware datetime (replay-deterministic "
            "clocks are tz-aware)"
        )


def _ensure_cache_key(value: str) -> None:
    if not value or not _CACHE_KEY_RE.fullmatch(value):
        raise ValueError(
            "cache_key must match ^[A-Za-z0-9_-]+$ (path separators / "
            "spaces / unicode are refused so the key cannot smuggle "
            "path components)"
        )


class FileBackedEbayTokenCache:
    """Atomic JSON file-backed token cache."""

    def __init__(self, *, cache_path: Path | str) -> None:
        resolved = Path(cache_path).resolve(strict=False)
        # Ensure the parent directory exists so subsequent
        # writes don't fail on a fresh deployment.
        resolved.parent.mkdir(parents=True, exist_ok=True)
        self._cache_path = resolved
        self._lock = threading.Lock()

    @property
    def cache_path(self) -> Path:
        return self._cache_path

    def fetch(
        self,
        *,
        cache_key: str,
        now: datetime,
        safety_margin_seconds: int = 60,
    ) -> str | None:
        _ensure_cache_key(cache_key)
        _ensure_tz_aware("now", now)
        if safety_margin_seconds < 0:
            raise ValueError("safety_margin_seconds must be non-negative")
        payload = self._read_payload()
        entry = payload.get(cache_key)
        if not isinstance(entry, dict):
            return None
        access_token = entry.get("access_token")
        expires_at_str = entry.get("expires_at")
        if not isinstance(access_token, str) or not isinstance(expires_at_str, str):
            return None
        try:
            expires_at = datetime.fromisoformat(expires_at_str)
        except ValueError:
            return None
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        delta = (expires_at - now).total_seconds()
        if delta <= safety_margin_seconds:
            return None
        return access_token

    def store(
        self,
        *,
        cache_key: str,
        access_token: str,
        expires_at: datetime,
        minted_at: datetime,
    ) -> None:
        _ensure_cache_key(cache_key)
        _ensure_tz_aware("expires_at", expires_at)
        _ensure_tz_aware("minted_at", minted_at)
        if not access_token or not access_token.strip():
            raise ValueError("access_token must be a non-blank string")
        if expires_at <= minted_at:
            raise ValueError("expires_at must be strictly after minted_at")
        with self._lock:
            payload = self._read_payload()
            payload[cache_key] = {
                "access_token": access_token,
                "expires_at": expires_at.isoformat(),
                "minted_at": minted_at.isoformat(),
            }
            self._atomic_write(payload)

    def _read_payload(self) -> dict[str, Any]:
        if not self._cache_path.exists():
            return {}
        try:
            raw = self._cache_path.read_text(encoding="utf-8")
        except OSError:
            return {}
        if not raw.strip():
            return {}
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return {}
        if not isinstance(data, dict):
            return {}
        return data

    def _atomic_write(self, payload: dict[str, Any]) -> None:
        # Write to a temp file in the same directory, then
        # rename — guarantees readers see either the prior or
        # the new content, never a partial write.
        directory = self._cache_path.parent
        fd, tmp_path = tempfile.mkstemp(
            prefix=".ebay-token-", suffix=".json.tmp", dir=str(directory)
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fp:
                json.dump(payload, fp, sort_keys=True)
                fp.flush()
                os.fsync(fp.fileno())
            os.replace(tmp_path, self._cache_path)
        except Exception:
            # Best-effort cleanup of the temp file on failure.
            with __import__("contextlib").suppress(OSError):
                os.unlink(tmp_path)
            raise


__all__ = ["FileBackedEbayTokenCache"]
