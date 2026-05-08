"""``LocalFsEvidenceArtifactStore`` — production default for
``EvidenceArtifactStorePort``.

Persists evidence payloads (HAR / DOM / response headers / etc.)
under a configurable root directory. Layout:

    <root>/<run_ref_hash>/<attempt_ref_hash>/<kind>-<digest12>.<ext>

Path-traversal hygiene: ``run_ref`` and ``attempt_ref`` are mapped
through a SHA-256 digest + safe-prefix scheme (the same idiom step
1.1 uses for ``storage_state.json`` filenames). Even if a caller
hands us ``run_ref="../etc/passwd"``, the persisted file lands
inside the configured root.

Concurrency: each ``put`` writes to a sibling tempfile (``O_CREAT |
O_EXCL | O_NOFOLLOW``) and ``os.replace``s into place. Two writers
with the same digest will land identical bytes on the same path —
``os.replace`` is atomic so the final file is never partial.

Privacy: HAR / DOM payloads contain redacted credentials but may
still carry PII (display names, addresses) from the underlying page.
Files are written with mode ``0o600`` (owner read/write only) and
the directory trees with mode ``0o700``. Lifecycle / retention
policy (max 7 days for failed runs, encrypted at rest, customer
withdrawal purge) lives in the Phase 6 ``ArtifactLifecycle`` gate —
this store handles intake, not eviction.
"""

from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Final

from veracrawl.ports.evidence_artifact_store import (
    ArtifactKind,
    EvidenceArtifactStoreError,
    EvidencePutResult,
    EvidenceRedactionRequired,
    kind_requires_redaction,
)
from veracrawl.runtime_support.logging import get_logger

_logger = get_logger(__name__)

# Reused from the storage_state filename pattern: 64-char prefix max
# keeps each component well inside POSIX NAME_MAX (255).
_REF_PREFIX_MAX: Final[int] = 32
# Owner read/write only — HAR / DOM payloads carry post-redaction
# residual data we should not expose by default.
_FILE_MODE: Final[int] = 0o600
_DIR_MODE: Final[int] = 0o700


# Map ``ArtifactKind`` → file extension. Keep in sync with the kinds
# defined in :class:`ArtifactKind`.
_EXTENSION_BY_KIND: Final[dict[ArtifactKind, str]] = {
    ArtifactKind.HAR: ".har.json",
    ArtifactKind.SCREENSHOT: ".png",
    ArtifactKind.DOM: ".dom.html",
    ArtifactKind.RESPONSE_HEADERS: ".headers.json",
    ArtifactKind.REQUEST_HEADERS: ".headers.json",
    ArtifactKind.TRACE: ".trace.zip",
    ArtifactKind.OTHER: ".bin",
}


def _safe_component(ref: str) -> str:
    """Map a caller-supplied ref to a filesystem-safe directory name.

    Same shape as step 1.1's ``_storage_state_filename``: a
    sanitised prefix concatenated with a SHA-256 digest. The digest
    is the collision-resistant key (so ``run:a:b`` and ``run:a/b``
    never collide); the prefix is purely cosmetic for operator
    debugging.
    """

    digest = hashlib.sha256(ref.encode("utf-8")).hexdigest()
    safe_chars: list[str] = []
    for ch in ref:
        if ch.isalnum() or ch in "_-.":
            safe_chars.append(ch)
        else:
            safe_chars.append("_")
    prefix = "".join(safe_chars)[:_REF_PREFIX_MAX].strip("._-") or "ref"
    return f"{prefix}-{digest[:32]}"


class LocalFsEvidenceArtifactStore:
    """Filesystem-backed :class:`EvidenceArtifactStorePort` impl.

    Construction:

    * ``root``: directory under which all artifacts land. Created
      with mode ``0o700`` if missing.

    Calls are safe from concurrent threads; each ``put`` stages a
    sibling tempfile and atomically renames it onto the final path.
    """

    def __init__(self, *, root: Path) -> None:
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(self._root, _DIR_MODE)
        except OSError:
            # Windows / non-POSIX may not honor chmod; we accept the
            # filesystem default ACLs there.
            _logger.debug("evidence_store_root_chmod_unsupported", path=str(self._root))

    def put(
        self,
        *,
        run_ref: str,
        attempt_ref: str,
        kind: ArtifactKind,
        payload: bytes,
        content_type: str,
        redaction_applied: bool,
    ) -> EvidencePutResult:
        del content_type  # extension comes from ``kind``; content_type is informational
        if kind_requires_redaction(kind) and not redaction_applied:
            raise EvidenceRedactionRequired(f"kind={kind.value} requires redaction_applied=True")
        digest = hashlib.sha256(payload).hexdigest()
        run_dir = self._root / _safe_component(run_ref)
        attempt_dir = run_dir / _safe_component(attempt_ref)
        try:
            run_dir.mkdir(parents=True, exist_ok=True)
            attempt_dir.mkdir(parents=True, exist_ok=True)
            try:
                os.chmod(run_dir, _DIR_MODE)
                os.chmod(attempt_dir, _DIR_MODE)
            except OSError:
                _logger.debug("evidence_store_dir_chmod_unsupported")
        except OSError as exc:
            raise EvidenceArtifactStoreError(f"failed to create evidence directory: {exc}") from exc

        extension = _EXTENSION_BY_KIND.get(kind, ".bin")
        filename = f"{kind.value}-{digest[:16]}{extension}"
        target = attempt_dir / filename
        # Atomic write: stage to a sibling tempfile, then ``os.replace``.
        # ``mkstemp`` opens with O_CREAT|O_EXCL|O_RDWR; on POSIX the
        # mode is honored from the caller. We pass ``dir=`` so the
        # tempfile sits on the same filesystem (atomic rename).
        try:
            fd, tmp_name = tempfile.mkstemp(
                prefix=f".{filename}.",
                suffix=".tmp",
                dir=str(attempt_dir),
            )
        except OSError as exc:
            raise EvidenceArtifactStoreError(f"failed to stage evidence tempfile: {exc}") from exc
        try:
            try:
                # Write through the raw fd — loop over partial writes
                # so a short ``os.write`` never leaves a truncated
                # artifact (same pattern step 1.1 uses for
                # ``storage_state.json``).
                written = 0
                while written < len(payload):
                    chunk = os.write(fd, payload[written:])
                    if chunk <= 0:
                        raise OSError(
                            f"os.write returned {chunk}; refusing to spin and "
                            "risk truncated evidence persistence"
                        )
                    written += chunk
                os.fsync(fd)
            finally:
                os.close(fd)
            try:
                os.chmod(tmp_name, _FILE_MODE)
            except OSError:
                _logger.debug("evidence_store_tmp_chmod_unsupported")
            os.replace(tmp_name, str(target))
        except OSError as exc:
            try:
                Path(tmp_name).unlink(missing_ok=True)
            except OSError:
                pass
            raise EvidenceArtifactStoreError(f"failed to persist evidence artifact: {exc}") from exc

        artifact_ref = (
            f"artifact:evidence:{kind.value}:{_safe_component(run_ref)}"
            f":{_safe_component(attempt_ref)}:{digest[:16]}"
        )
        return EvidencePutResult(
            artifact_ref=artifact_ref,
            content_digest_sha256=digest,
            size_bytes=len(payload),
            redaction_applied=redaction_applied,
        )

    def get(self, *, artifact_ref: str) -> bytes | None:
        path = self._path_for_ref(artifact_ref)
        if path is None or not path.is_file():
            return None
        try:
            return path.read_bytes()
        except OSError:
            _logger.exception("evidence_store_read_failed", artifact_ref=artifact_ref)
            return None

    # -- Internals ---------------------------------------------------

    def _path_for_ref(self, artifact_ref: str) -> Path | None:
        # ``artifact_ref`` shape:
        #   artifact:evidence:<kind>:<run_safe>:<attempt_safe>:<digest12>
        parts = artifact_ref.split(":")
        if len(parts) != 6 or parts[0] != "artifact" or parts[1] != "evidence":
            return None
        try:
            kind = ArtifactKind(parts[2])
        except ValueError:
            return None
        run_safe, attempt_safe, digest_short = parts[3], parts[4], parts[5]
        # Containment: each safe-component must be a single path
        # element (no separators / parents). The construction in
        # ``put`` guarantees this; we re-check here so a malicious
        # caller cannot read outside the root by hand-crafting a ref.
        for component in (run_safe, attempt_safe, digest_short):
            if "/" in component or "\\" in component or component in {"", "..", "."}:
                return None
        extension = _EXTENSION_BY_KIND.get(kind, ".bin")
        filename = f"{kind.value}-{digest_short}{extension}"
        return self._root / run_safe / attempt_safe / filename


__all__ = ["LocalFsEvidenceArtifactStore"]
