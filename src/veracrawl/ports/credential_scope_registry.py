"""``CredentialScopeRegistryPort`` — resolve credential_scope_refs.

Phase 2 step 2.5a: the agent runtime resolves
``AgentRunRequest.credential_scope_refs`` to concrete
:class:`CredentialScope` records via this port at run start.
The port is narrow — one ``resolve`` method per scope_ref —
because the agent runtime needs the scopes to wire up
:class:`AuthorizedSessionAdapter` instances per credential.

Phase 6 step 6.1 wires the production
:class:`YamlCredentialScopeRegistry` (loads from
``credentials/scopes/<scope-ref>.yml``); Phase 2 ships the port
+ an in-memory fixture.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from veracrawl.contracts.common import Ref
from veracrawl.contracts.security_privacy import CredentialScope


class CredentialScopeRegistryError(Exception):
    """Raised when a scope_ref cannot be resolved.

    The scope_ref itself may carry caller-controlled content;
    the exception's text only reports a length-only redacted
    placeholder so the failed-lookup signal does not leak
    secret-shaped strings into log lines.
    """

    def __init__(self, *, scope_ref_length: int) -> None:
        self.scope_ref_length = scope_ref_length
        super().__init__(
            f"credential scope registry could not resolve scope_ref "
            f"of length {scope_ref_length} (redacted)"
        )


@runtime_checkable
class CredentialScopeRegistryPort(Protocol):
    """Resolve a scope_ref to a :class:`CredentialScope` record."""

    def resolve(self, scope_ref: Ref) -> CredentialScope:
        """Return the scope record. Raises
        :class:`CredentialScopeRegistryError` when the scope_ref
        is unknown."""


__all__ = [
    "CredentialScopeRegistryError",
    "CredentialScopeRegistryPort",
]
