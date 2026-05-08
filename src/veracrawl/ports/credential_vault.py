"""``CredentialVaultPort`` — scoped customer credential retrieval.

Phase 2 step 2.1 introduces the hexagonal port for credential
retrieval. The port surface is intentionally narrow: callers ask
the vault for a value by ``(scope_ref, key)`` and get back an
opaque :class:`CredentialValue` whose default string conversions
are pre-redacted. The actual secret only escapes the wrapper via
:meth:`CredentialValue.reveal` — calling code that hands the
wrapper to a logger / repr / f-string / printer cannot
accidentally leak the secret.

Two implementations land across Phase 2:

* :class:`~veracrawl.adapters.credential_vault.env_var_vault.EnvVarVault`
  (this step, step 2.1): test / fixture impl that reads
  ``VERACRAWL_CRED_<scope>__<key>`` (double-underscore separator)
  from the process env.
* ``OutboxVaultClient`` (step 2.4): production impl that talks to
  a real vault (HashiCorp Vault / AWS Secrets Manager /
  customer-supplied) and emits ``CredentialUseRecord`` audit rows.

The port itself is independent of either impl. Callers depend on
the port surface only — design.md §3.3 hexagonal discipline.

Scope / key shape:

* Both ``scope_ref`` and ``key`` are env-var-safe identifiers:
  uppercase alphanumeric + underscore. The orchestrator
  translates a structured :class:`CredentialScope.id` to a
  vault-safe scope before calling the port; the vault does not
  re-derive the mapping (avoids two sources of truth).
* Empty / lowercase / dotted / dashed identifiers are rejected
  at the vault layer so a caller cannot smuggle path traversal
  into the env-var lookup.

Failure semantics:

* Missing entry → :class:`CredentialNotFoundError` (typed; the
  caller decides whether to retry, fall back, or escalate).
* Empty / whitespace-only value → treated as missing
  (``CredentialNotFoundError``); a vault that says "yes I have
  this credential" with an empty value is indistinguishable from
  a misconfiguration and the cooperative crawler must fail
  closed rather than send empty Authorization to the upstream.
"""

from __future__ import annotations

import re
from typing import Final, Protocol, runtime_checkable

# ``scope_ref`` is interpolated verbatim into the redaction marker
# (``<credential:redacted:<scope>>``). Constrain it to env-var-safe
# shape so a caller / vault adapter that accidentally passes a raw
# token or control-character payload as ``scope_ref`` cannot leak
# it through the very ``__repr__`` / ``__str__`` / ``__format__``
# paths the wrapper exists to make safe. The orchestrator translates
# structured ``CredentialScope.id`` values to vault-safe scopes at
# the wiring layer before calling the port.
_SAFE_SCOPE_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Z0-9_]+$")


class CredentialNotFoundError(KeyError):
    """The vault has no credential for the requested ``(scope, key)``.

    Inherits :class:`KeyError` so ``vault.get(scope_ref=..., key=...)``
    can be wrapped in ``try / except KeyError`` for callers that
    don't care about the typed shape, while typed callers can
    still ``except CredentialNotFoundError`` for precise dispatch.
    """


class CredentialValue:
    """An opaque wrapper around a credential string.

    Threat model — what the wrapper protects against:

    * Default Python string conversions (``__repr__`` / ``__str__``
      / ``__format__``) accidentally exposing the secret via
      f-strings, ``print()``, ``%s`` logging, or ``repr()``.
    * ``pickle.dumps`` silently emitting the secret to a stable
      on-disk form (refused via ``__reduce__``).
    * Equality-based timing or output leakage — identity-based
      ``__eq__`` / ``__hash__`` mean two wrappers around the same
      secret are *not* equal, so ``cred == known_value`` always
      compares False against a plain string.
    * Casual ``dir(cred)`` introspection in REPLs / debug consoles —
      private slot names are filtered out of ``__dir__``.

    Threat model — what the wrapper does NOT protect against:

    * Intentional attribute introspection. Python is not a
      capability-secure language and nothing here can stop a
      determined caller from doing ``object.__getattribute__(
      cred, "_value")`` or reading ``cred.__slots__``. The
      wrapper's contract is only that *accidental* paths
      (logging, serialization, equality, casual ``dir``) cannot
      leak. The :meth:`reveal` method exists so that the one
      legitimate read site is the one that calls it explicitly.
    * In-process memory inspection (a debugger, ``gc.get_referents``,
      or another extension reading process memory). Secrets that
      need that level of protection should be handled by an
      external KMS / HSM, not by a Python wrapper.

    The actual secret only escapes via :meth:`reveal`. Calling code
    that hands the wrapper to a logger / repr / f-string / printer
    cannot accidentally leak; intentional access remains possible.
    """

    __slots__ = ("_scope_ref", "_value")

    def __init__(self, *, value: str, scope_ref: str) -> None:
        if not value:
            raise ValueError("CredentialValue requires a non-empty value")
        if not value.strip():
            # Centralize the fail-closed whitespace rule on the
            # wrapper itself so a future production vault adapter
            # (step 2.4 ``OutboxVaultClient`` and beyond) cannot
            # return ``CredentialValue(value="   ")`` and end up
            # sending blank Authorization upstream.
            raise ValueError(
                "CredentialValue rejects whitespace-only values "
                "(treated as missing / fail-closed for the cooperative crawler)"
            )
        if not scope_ref:
            raise ValueError("CredentialValue requires a non-empty scope_ref")
        if not _SAFE_SCOPE_RE.fullmatch(scope_ref):
            # Refuse to interpolate arbitrary ``scope_ref`` content
            # into the redaction marker. The caller may have handed
            # us a secret-looking string; do not echo it in the
            # error either, since the exception text would itself
            # leak through logs / pytest output / telemetry.
            raise ValueError(
                f"CredentialValue scope_ref must match ``^[A-Z0-9_]+$`` "
                f"(env-var-safe identifier); rejected value of length "
                f"{len(scope_ref)} (redacted)"
            )
        self._value = value
        self._scope_ref = scope_ref

    def reveal(self) -> str:
        """Return the underlying secret string.

        The only path that exposes the value. Call sites should
        be tightly scoped (request-build path that feeds an
        ``Authorization`` header builder, vault audit logger);
        do not assign the return value to a long-lived variable
        if avoidable.
        """

        return self._value

    @property
    def scope_ref(self) -> str:
        """Return the (non-secret) scope reference."""

        return self._scope_ref

    def _redacted(self) -> str:
        return f"<credential:redacted:{self._scope_ref}>"

    def __repr__(self) -> str:
        return self._redacted()

    def __str__(self) -> str:
        return self._redacted()

    def __format__(self, format_spec: str) -> str:
        # Honor the format spec on the redacted marker (alignment,
        # width, fill) so f-strings behave predictably without
        # ever exposing the secret.
        return format(self._redacted(), format_spec)

    def __reduce__(self) -> tuple[type, tuple[str, ...]]:
        # Picking a credential into a stable on-disk form is
        # almost certainly a mis-use; reject ``pickle.dumps``
        # rather than silently emitting the raw secret.
        raise TypeError(
            "CredentialValue refuses pickle/copy serialization "
            "(would expose secret); use ``reveal()`` at the "
            "specific call site that needs it."
        )

    def __copy__(self) -> CredentialValue:
        # Shallow copy is harmless (same secret, same scope) but
        # is rarely the right call. Allow it for defensive coding
        # patterns; ``__reduce__`` already blocks pickle.
        return CredentialValue(value=self._value, scope_ref=self._scope_ref)

    def __deepcopy__(self, memo: dict[int, object]) -> CredentialValue:
        del memo
        return self.__copy__()

    def __dir__(self) -> list[str]:
        # Filter private slots out of casual REPL / debug-console
        # ``dir(cred)`` listings so an operator browsing the object
        # in a notebook / pdb session does not see ``_value`` as a
        # discoverable attribute. (The slot still exists; this only
        # protects the accidental-discovery path — see threat model
        # in the class docstring.)
        return [name for name in super().__dir__() if not name.startswith("_")]


@runtime_checkable
class CredentialVaultPort(Protocol):
    """Hexagonal port for scoped credential retrieval."""

    def get(self, *, scope_ref: str, key: str) -> CredentialValue:
        """Return the credential for ``(scope_ref, key)``.

        Raises :class:`CredentialNotFoundError` when the vault has
        no entry. Raises :class:`ValueError` when the
        ``scope_ref`` / ``key`` shape is invalid (the vault is
        not responsible for sanitising — but it must reject
        clearly-malformed identifiers so a caller cannot smuggle
        path traversal / env-var-name injection into the
        lookup).
        """


__all__ = [
    "CredentialNotFoundError",
    "CredentialValue",
    "CredentialVaultPort",
]
