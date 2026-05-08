"""``EnvVarVault`` — test / fixture impl of ``CredentialVaultPort``.

Reads credentials from process environment variables of shape
``VERACRAWL_CRED_<scope>__<key>`` (double-underscore separator).
Scope and key must be env-var-safe identifiers (uppercase
alphanumeric + underscore); the vault rejects anything else so a
caller cannot smuggle env-var-name injection or path-traversal-
shaped strings into the lookup.

The double-underscore separator keeps the mapping unambiguous
when both scope and key contain underscores:
``(scope='A_B', key='C')`` → ``..._A_B__C``;
``(scope='A', key='B_C')`` → ``..._A__B_C`` — different env vars,
no aliasing.

This impl is for **tests / fixtures only** — the production
``OutboxVaultClient`` (Phase 2 step 2.4) does the real audit-
logged retrieval. ``EnvVarVault`` enforces a production-mode
gate at ``get`` time: under ``RuntimeMode.PRODUCTION``, every
``get`` raises :class:`ProductionRuntimeNotImplemented`. This
ensures an unaudited credential path can never appear in
production even if a wiring regression slipped past the
adapter layer (defense in depth).
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
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    current_mode,
)

_ENV_PREFIX: Final[str] = "VERACRAWL_CRED_"
# Double underscore disambiguates ``(scope='A_B', key='C')`` from
# ``(scope='A', key='B_C')`` — both would otherwise alias to
# ``VERACRAWL_CRED_A_B_C`` and silently cross-pollute scope.
_ENV_SEP: Final[str] = "__"
_SAFE_IDENT_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Z0-9_]+$")


def _validate_identifier(name: str, *, kind: str) -> None:
    if not name:
        raise ValueError(f"{kind} must be non-empty")
    if not _SAFE_IDENT_RE.fullmatch(name):
        # Don't echo the rejected identifier — the caller may have
        # handed us a secret-looking string and the exception text
        # would carry it into logs / telemetry. Length only.
        raise ValueError(
            f"{kind} must match ``^[A-Z0-9_]+$`` (uppercase, digits, "
            f"underscore only — env-var-safe identifier); rejected value "
            f"of length {len(name)} (redacted)"
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
        # Defense-in-depth: the wiring layer (step 2.4) swaps in
        # ``OutboxVaultClient`` for production, but refuse here
        # too so a wiring regression cannot silently route
        # production credentials through this fixture adapter.
        if current_mode() is RuntimeMode.PRODUCTION:
            raise ProductionRuntimeNotImplemented(
                backend="env_var_vault",
                gate="credential_vault",
            )
        _validate_identifier(scope_ref, kind="scope_ref")
        _validate_identifier(key, kind="key")
        env_name = f"{_ENV_PREFIX}{scope_ref}{_ENV_SEP}{key}"
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
