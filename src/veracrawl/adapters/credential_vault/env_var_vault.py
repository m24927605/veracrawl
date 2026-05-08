"""``EnvVarVault`` — test / fixture impl of ``CredentialVaultPort``.

Reads credentials from process environment variables of shape
``VERACRAWL_CRED_<scope>_<key>``. Scope and key must be env-var-safe
identifiers (uppercase alphanumeric + underscore); the vault
rejects anything else so a caller cannot smuggle env-var-name
injection or path-traversal-shaped strings into the lookup.

This impl is for **tests / fixtures only** — the production
``OutboxVaultClient`` (Phase 2 step 2.4) does the real audit-
logged retrieval. The wiring layer (``AuthorizedSessionAdapter``)
gates against using ``EnvVarVault`` under
``RuntimeMode.PRODUCTION``; the vault itself does not enforce
the gate (a clean separation lets the env-var vault remain
useful for e2e fixtures that legitimately want production-mode
without a real secrets backend).
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import Final

from veracrawl.ports.credential_vault import (
    CredentialNotFoundError,
    CredentialValue,
)

_ENV_PREFIX: Final[str] = "VERACRAWL_CRED_"
_SAFE_IDENT_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Z0-9_]+$")


def _validate_identifier(name: str, *, kind: str) -> None:
    if not name:
        raise ValueError(f"{kind} must be non-empty")
    if not _SAFE_IDENT_RE.fullmatch(name):
        raise ValueError(
            f"{kind} {name!r} must match ``^[A-Z0-9_]+$`` (uppercase, digits, "
            "underscore only — env-var-safe identifier)"
        )


class EnvVarVault:
    """Test / fixture credential vault backed by process env vars.

    Construction parameters:

    * ``environ``: optional ``Mapping`` to read from. Defaults to
      :data:`os.environ`. Tests inject a dict so they don't have
      to pollute the real process env.

    The vault is read-only — there is no ``set`` / ``put`` method
    because tests should set env vars (or pass an ``environ``
    dict) before constructing the vault.
    """

    def __init__(self, *, environ: Mapping[str, str] | None = None) -> None:
        self._environ: Mapping[str, str] = environ if environ is not None else os.environ

    def get(self, *, scope_ref: str, key: str) -> CredentialValue:
        _validate_identifier(scope_ref, kind="scope_ref")
        _validate_identifier(key, kind="key")
        env_name = f"{_ENV_PREFIX}{scope_ref}_{key}"
        raw = self._environ.get(env_name)
        if raw is None:
            raise CredentialNotFoundError(
                f"no credential at env var {env_name} (scope_ref={scope_ref!r}, key={key!r})"
            )
        if not raw.strip():
            # An empty / whitespace-only value is indistinguishable
            # from a misconfiguration; fail closed rather than send
            # empty Authorization upstream.
            raise CredentialNotFoundError(
                f"credential at env var {env_name} is empty / whitespace-only "
                "(treated as missing — fail-closed for cooperative crawler)"
            )
        return CredentialValue(value=raw, scope_ref=scope_ref)


__all__ = ["EnvVarVault"]
