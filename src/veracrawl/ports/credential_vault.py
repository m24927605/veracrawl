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
  ``VERACRAWL_CRED_<scope>_<key>`` from the process env.
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

from typing import Protocol, runtime_checkable


class CredentialNotFoundError(KeyError):
    """The vault has no credential for the requested ``(scope, key)``.

    Inherits :class:`KeyError` so ``vault.get(scope_ref=..., key=...)``
    can be wrapped in ``try / except KeyError`` for callers that
    don't care about the typed shape, while typed callers can
    still ``except CredentialNotFoundError`` for precise dispatch.
    """


class CredentialValue:
    """An opaque wrapper around a credential string.

    The wrapper's default string conversions (``__repr__`` /
    ``__str__`` / ``__format__``) emit a redaction marker so the
    secret cannot leak via:

    * f-strings (``f"token={cred}"``) — calls ``__format__``
    * ``print(cred)`` / ``str(cred)`` — calls ``__str__``
    * ``logger.info("got %s", cred)`` — calls ``__str__`` /
      ``__repr__`` depending on the formatter
    * ``repr(cred)`` / ``[cred]`` — calls ``__repr__``

    The actual secret only escapes via :meth:`reveal`. Calling
    code that hands the wrapper to a logger / repr / printer
    cannot accidentally leak.

    Equality / hashing default to identity (``object.__eq__`` /
    ``object.__hash__``) so two wrappers around the same secret
    are *not* considered equal — preventing a caller that
    accidentally compares to a string from leaking the secret
    via ``cred == known_value`` timing or output.
    """

    __slots__ = ("_scope_ref", "_value")

    def __init__(self, *, value: str, scope_ref: str) -> None:
        if not value:
            raise ValueError("CredentialValue requires a non-empty value")
        if not scope_ref:
            raise ValueError("CredentialValue requires a non-empty scope_ref")
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
        del format_spec
        return self._redacted()

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
