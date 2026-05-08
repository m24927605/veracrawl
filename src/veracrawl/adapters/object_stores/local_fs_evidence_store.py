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

    def __init__(
        self,
        *,
        root: Path,
        max_payload_bytes: int | None = 256 * 1024 * 1024,
    ) -> None:
        """``root``: store root dir (must not be a symlink).

        ``max_payload_bytes``: optional per-artifact size cap (default
        256 MiB). A bad caller or runaway capture should not exhaust
        local disk; ``put`` raises :class:`EvidenceArtifactStoreError`
        when the payload exceeds the cap. Pass ``None`` to disable the
        cap (test fixtures may want this).
        """

        self._max_payload_bytes = max_payload_bytes
        # Reject a symlink at the configured root. This is a
        # sensitive evidence location; if someone configured the
        # store against a symlink we'd ``chmod`` the link's target
        # below and trust the link's resolution for the lifetime
        # of the store. ``lstat`` does not follow links.
        import stat as _stat

        if root.is_symlink() or (root.exists() and not _stat.S_ISDIR(root.lstat().st_mode)):
            raise EvidenceArtifactStoreError(
                f"evidence-store root must be a real directory, not a symlink: {root}"
            )
        self._root = root
        self._root.mkdir(parents=True, exist_ok=True, mode=_DIR_MODE)
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
        if self._max_payload_bytes is not None and len(payload) > self._max_payload_bytes:
            raise EvidenceArtifactStoreError(
                f"evidence payload exceeds max_payload_bytes "
                f"({len(payload)} > {self._max_payload_bytes})"
            )
        digest = hashlib.sha256(payload).hexdigest()
        run_safe = _safe_component(run_ref)
        attempt_safe = _safe_component(attempt_ref)
        extension = _EXTENSION_BY_KIND.get(kind, ".bin")
        # Use the full 64-hex-char digest in both filename and ref so
        # the artifact identity is collision-resistant under
        # adversarial input.
        filename = f"{kind.value}-{digest}{extension}"
        # Codex iter-4 critical: previous put used path-based ``lstat``
        # checks then ``tempfile.mkstemp(dir=...)`` that follows the
        # path again — TOCTOU window where a local process could swap
        # ``run_dir`` / ``attempt_dir`` to a symlink between the
        # check and the write. Use descriptor-based traversal:
        # ``os.open(O_DIRECTORY | O_NOFOLLOW, dir_fd=...)`` for each
        # component so each handle is bound to the kernel object the
        # check validated. ``os.O_NOFOLLOW`` makes the open fail
        # (ELOOP) if a component is a symlink, even after a post-
        # check swap.
        directory_flag = getattr(os, "O_DIRECTORY", 0)
        try:
            root_fd = os.open(str(self._root), os.O_RDONLY | directory_flag)
        except OSError as exc:
            raise EvidenceArtifactStoreError(f"failed to open evidence-store root: {exc}") from exc
        run_fd: int | None = None
        attempt_fd: int | None = None
        try:
            run_fd = self._mkdir_and_open(root_fd, run_safe)
            attempt_fd = self._mkdir_and_open(run_fd, attempt_safe)
            self._write_atomic(attempt_fd, filename, payload)
        except OSError as exc:
            raise EvidenceArtifactStoreError(f"failed to persist evidence artifact: {exc}") from exc
        finally:
            for fd in (attempt_fd, run_fd, root_fd):
                if fd is not None:
                    try:
                        os.close(fd)
                    except OSError:
                        pass

        artifact_ref = f"artifact:evidence:{kind.value}:{run_safe}:{attempt_safe}:{digest}"
        return EvidencePutResult(
            artifact_ref=artifact_ref,
            content_digest_sha256=digest,
            size_bytes=len(payload),
            redaction_applied=redaction_applied,
        )

    @staticmethod
    def _mkdir_and_open(parent_fd: int, name: str) -> int:
        """Create + open a child directory under ``parent_fd``.

        Uses ``os.mkdir(dir_fd=...)`` to create the directory under
        the parent fd (relative path, no path traversal possible),
        then ``os.open(O_DIRECTORY | O_NOFOLLOW, dir_fd=...)`` so a
        post-create symlink swap cannot redirect the descriptor.
        """

        nofollow = getattr(os, "O_NOFOLLOW", 0)
        directory_flag = getattr(os, "O_DIRECTORY", 0)
        try:
            os.mkdir(name, mode=_DIR_MODE, dir_fd=parent_fd)
        except FileExistsError:
            pass  # idempotent
        return os.open(
            name,
            os.O_RDONLY | directory_flag | nofollow,
            dir_fd=parent_fd,
        )

    @staticmethod
    def _write_atomic(parent_fd: int, filename: str, payload: bytes) -> None:
        """Stage ``payload`` into a tempfile under ``parent_fd``,
        then atomically rename onto ``filename``.

        Tempfile is opened with ``O_CREAT | O_EXCL | O_NOFOLLOW |
        O_RDWR`` relative to ``parent_fd`` — the descriptor is bound
        to the staging file the kernel just created, so a concurrent
        symlink swap cannot redirect the write. The final
        ``os.rename(src, dst, src_dir_fd=, dst_dir_fd=)`` is also
        descriptor-relative.
        """

        nofollow = getattr(os, "O_NOFOLLOW", 0)
        # Random tempfile name so concurrent writers don't collide.
        tmp_name = f".{filename}.{os.urandom(8).hex()}.tmp"
        flags = os.O_CREAT | os.O_EXCL | os.O_RDWR | nofollow
        fd = os.open(tmp_name, flags, _FILE_MODE, dir_fd=parent_fd)
        renamed = False
        try:
            try:
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
            os.rename(tmp_name, filename, src_dir_fd=parent_fd, dst_dir_fd=parent_fd)
            renamed = True
        finally:
            # Always clean up the staging file if we didn't get to
            # rename it — partial writes / errors must not leave
            # tempfiles cluttering the evidence dir.
            if not renamed:
                try:
                    os.unlink(tmp_name, dir_fd=parent_fd)
                except OSError:
                    pass

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
