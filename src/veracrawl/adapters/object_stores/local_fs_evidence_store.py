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

Concurrency: each ``put`` stages bytes via :func:`tempfile.mkstemp`
(``O_CREAT | O_EXCL | O_RDWR`` with mode ``0o600``) and ``os.replace``s
the result into place. Two writers with the same digest land
identical bytes on the same path — ``os.replace`` is atomic so the
final file is never partial. The :func:`get` path uses ``lstat``-
based containment checks to refuse symlinks anywhere on the route
from root to artifact.

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
            # Codex iter-3 important #6: ``mkdir(exist_ok=True)`` happily
            # uses an existing symlink that points outside the root.
            # Verify each directory we touch is a real directory (not a
            # symlink) BEFORE writing through it. If a pre-existing
            # entry is not a real dir, refuse the put — silently writing
            # through a swapped symlink would land bytes outside the
            # configured root.
            self._ensure_real_dir(run_dir)
            self._ensure_real_dir(attempt_dir)
            try:
                os.chmod(run_dir, _DIR_MODE)
                os.chmod(attempt_dir, _DIR_MODE)
            except OSError:
                _logger.debug("evidence_store_dir_chmod_unsupported")
        except OSError as exc:
            raise EvidenceArtifactStoreError(f"failed to create evidence directory: {exc}") from exc

        extension = _EXTENSION_BY_KIND.get(kind, ".bin")
        # Codex iter-3 important #5: ``digest[:16]`` gave only 64 bits
        # of collision resistance in both filename + ref. At crawler
        # scale a SHA-256 prefix collision is realistically reachable
        # under adversarial input. Use the full 64-hex-char digest in
        # both the filename and ``artifact_ref`` so the artifact
        # identity matches the content-addressed contract.
        filename = f"{kind.value}-{digest}{extension}"
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
            f":{_safe_component(attempt_ref)}:{digest}"
        )
        return EvidencePutResult(
            artifact_ref=artifact_ref,
            content_digest_sha256=digest,
            size_bytes=len(payload),
            redaction_applied=redaction_applied,
        )

    @staticmethod
    def _ensure_real_dir(path: Path) -> None:
        """Refuse to operate through a symlink at ``path``.

        Idempotent ``mkdir(parents=True, exist_ok=True, mode=0o700)``
        if the path is missing; if the path exists, ``lstat``-check
        that it is a regular directory. A symlink at this position
        would let a compromised local process redirect writes
        outside the configured root, so we raise instead of writing
        through it.
        """

        import stat as _stat

        try:
            info = path.lstat()
        except FileNotFoundError:
            path.mkdir(parents=True, exist_ok=True, mode=_DIR_MODE)
            return
        if not _stat.S_ISDIR(info.st_mode):
            raise OSError(
                f"evidence-store directory is not a real directory: {path} "
                f"(mode={oct(info.st_mode)}); refusing to write through it"
            )

    def get(self, *, artifact_ref: str) -> bytes | None:
        """Read an evidence artifact by ref.

        Symlink-safe + TOCTOU-safe (codex iter-3 important #7):

        * Walk from the configured root down to the artifact using
          ``os.open(O_NOFOLLOW | O_DIRECTORY)`` for each directory
          component and ``os.open(O_NOFOLLOW | O_RDONLY)`` for the
          file. ``O_NOFOLLOW`` makes the open fail (``ELOOP``) when
          the target component is a symlink, even if a concurrent
          process swaps it between our check and our open.
        * The descriptor is the same kernel object the open
          validated, so a post-open swap (``replace`` or rename
          underneath us) cannot redirect the read elsewhere.
        * On systems where ``O_NOFOLLOW`` is not defined (rare
          today), we degrade to ``lstat``-then-``read_bytes`` with
          a documented TOCTOU window — the path is still
          containment-checked.
        """

        path = self._path_for_ref(artifact_ref)
        if path is None:
            return None
        nofollow = getattr(os, "O_NOFOLLOW", None)
        directory_flag = getattr(os, "O_DIRECTORY", 0)
        if nofollow is None:
            return self._fallback_lstat_read(artifact_ref=artifact_ref, path=path)
        # Compute components from root → leaf. ``path`` was
        # constructed by us inside the configured root, so we know
        # the prefix; we still re-derive it here to keep the
        # traversal explicit and independent of construction.
        try:
            relative = path.relative_to(self._root)
        except ValueError:
            return None
        parts = relative.parts
        if not parts:
            return None
        # Open the root directly without O_NOFOLLOW (we trust the
        # configured root path itself; symlink hardening kicks in
        # below the root).
        try:
            root_fd = os.open(str(self._root), os.O_RDONLY | directory_flag)
        except OSError:
            return None
        try:
            current_fd = root_fd
            # Descend into intermediate directories. The last
            # component is the file; everything before it must be a
            # directory.
            for component in parts[:-1]:
                try:
                    next_fd = os.open(
                        component,
                        os.O_RDONLY | directory_flag | nofollow,
                        dir_fd=current_fd,
                    )
                except OSError:
                    _logger.warning(
                        "evidence_store_get_refused_unsafe_ancestor",
                        artifact_ref=artifact_ref,
                        component=component,
                    )
                    return None
                if current_fd != root_fd:
                    os.close(current_fd)
                current_fd = next_fd
            # Open the leaf file with O_NOFOLLOW so a symlink at the
            # leaf is rejected.
            try:
                leaf_fd = os.open(
                    parts[-1],
                    os.O_RDONLY | nofollow,
                    dir_fd=current_fd,
                )
            except OSError:
                _logger.warning(
                    "evidence_store_get_refused_unsafe_leaf",
                    artifact_ref=artifact_ref,
                )
                return None
            try:
                # Confirm regular file.
                info = os.fstat(leaf_fd)
                import stat as _stat

                if not _stat.S_ISREG(info.st_mode):
                    return None
                # Read the whole file via the descriptor.
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(leaf_fd, 65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                return b"".join(chunks)
            finally:
                os.close(leaf_fd)
        finally:
            if current_fd != root_fd:
                try:
                    os.close(current_fd)
                except OSError:
                    pass
            try:
                os.close(root_fd)
            except OSError:
                pass

    def _fallback_lstat_read(self, *, artifact_ref: str, path: Path) -> bytes | None:
        """Fallback for systems without ``O_NOFOLLOW``.

        Same lstat-based ancestor walk as the original implementation;
        documented as TOCTOU-prone but better than nothing on
        platforms where the kernel does not support no-follow opens.
        """

        import stat as _stat

        try:
            info = path.lstat()
        except OSError:
            return None
        if not _stat.S_ISREG(info.st_mode):
            return None
        for parent in path.parents:
            if parent == self._root:
                break
            try:
                p_info = parent.lstat()
            except OSError:
                return None
            if not _stat.S_ISDIR(p_info.st_mode):
                return None
        try:
            return path.read_bytes()
        except OSError:
            _logger.exception("evidence_store_read_failed", artifact_ref=artifact_ref)
            return None

    # -- Internals ---------------------------------------------------

    def _path_for_ref(self, artifact_ref: str) -> Path | None:
        # ``artifact_ref`` shape:
        #   artifact:evidence:<kind>:<run_safe>:<attempt_safe>:<digest>
        parts = artifact_ref.split(":")
        if len(parts) != 6 or parts[0] != "artifact" or parts[1] != "evidence":
            return None
        try:
            kind = ArtifactKind(parts[2])
        except ValueError:
            return None
        run_safe, attempt_safe, digest = parts[3], parts[4], parts[5]
        # Containment: each safe-component must be a single path
        # element (no separators / parents). The construction in
        # ``put`` guarantees this; we re-check here so a malicious
        # caller cannot read outside the root by hand-crafting a ref.
        for component in (run_safe, attempt_safe, digest):
            if "/" in component or "\\" in component or component in {"", "..", "."}:
                return None
        # Validate digest shape: 64 lowercase hex chars (SHA-256 hex
        # digest length). Refuse anything else so a hand-crafted ref
        # cannot read a file with an unexpected name.
        if len(digest) != 64 or not all(c in "0123456789abcdef" for c in digest):
            return None
        extension = _EXTENSION_BY_KIND.get(kind, ".bin")
        filename = f"{kind.value}-{digest}{extension}"
        return self._root / run_safe / attempt_safe / filename


__all__ = ["LocalFsEvidenceArtifactStore"]
