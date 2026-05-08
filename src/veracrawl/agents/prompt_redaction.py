"""``RedactedPromptContext`` — Phase 2 step 2.3 prompt-redaction boundary.

Any credential value passing into prompt-template resolution must
land in the rendered output as the literal
``<credential:redacted:<scope>>`` marker — never as the raw secret.
:class:`~veracrawl.ports.credential_vault.CredentialValue` (Phase 2
step 2.1) already emits that marker via its ``__format__`` /
``__str__`` / ``__repr__`` overrides, so the redaction itself is
automatic when a credential is interpolated into a template via
``str.format_map`` (the standard rendering path). The registry
boundary's job is to *also* refuse to deliver a rendered output
that contains the marker: the marker's presence proves a caller
piped a credential into the template, and the design contract
(design.md §4 Phase 2) is that prompts must not carry credentials
at all — credential-bearing requests live in
``AuthorizedSessionAdapter`` (Phase 2 step 2.4).

The boundary therefore satisfies two properties simultaneously:

1. Defense in depth — even if a caller bypasses the rejection,
   the rendered output already has the marker, not the secret.
2. Refusal at the boundary — the registry raises
   :class:`PromptCredentialLeakError` so the offending caller is
   forced to migrate to the authorized-session path.

Phase 4 ``YamlPromptRegistry`` integrates this wrapper at the
``resolve_prompt`` boundary; Phase 2 step 2.3 ships the wrapper +
leak detector so the contract is locked before Phase 4 plugs in
the full registry.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from typing import Any, Final

from veracrawl.contracts.errors import PolicyViolation, VeraCrawlError

# Detects the credential redaction marker emitted by
# ``CredentialValue.__repr__`` / ``__str__`` / ``__format__``
# (Phase 2 step 2.1). The marker shape is
# ``<credential:redacted:<SCOPE>>`` where ``SCOPE`` matches the
# env-var-safe identifier regex enforced at ``CredentialValue``
# construction. Detecting the marker after render proves a
# ``CredentialValue`` was interpolated into the template.
_CREDENTIAL_MARKER_RE: Final[re.Pattern[str]] = re.compile(
    r"<credential:redacted:[A-Z0-9_]+>"
)


class PromptCredentialLeakError(VeraCrawlError, PolicyViolation):
    """Raised at prompt-template resolve time when a rendered
    output contains a credential redaction marker.

    Mixes :class:`PolicyViolation` so generic dispatch
    (``except PolicyViolation``) catches it alongside
    :class:`CredentialScopeViolation` and the other policy
    refusals.

    The error carries the template ref (the template ID, NOT the
    rendered text). The rendered output already has the redaction
    marker rather than the secret, but storing it on the
    exception is still a leakage path into log lines that walk
    ``__dict__``; keep the public attribute surface minimal.
    """

    def __init__(self, *, template_ref: str) -> None:
        self.template_ref = template_ref
        super().__init__(
            f"prompt template {template_ref!r} resolved to output "
            "containing a credential redaction marker — credentials "
            "must not flow into prompts. Use AuthorizedSessionAdapter "
            "(Phase 2 step 2.4) for credential-bearing requests instead."
        )


class RedactedPromptContext:
    """Render-side boundary that refuses prompts containing credentials.

    Construction accepts a context mapping (positional) and / or
    keyword arguments; both shapes merge into a single context dict.
    Keyword arguments win on conflicts — same semantics as
    ``dict.update``.

    :meth:`render` formats the supplied template against the merged
    context using :meth:`str.format_map`, then scans the rendered
    output for the credential redaction marker and raises
    :class:`PromptCredentialLeakError` if one is found.

    The class is stateless beyond the merged context; the same
    instance can render multiple templates safely. Re-rendering
    the same template is idempotent.
    """

    __slots__ = ("_context",)

    def __init__(
        self,
        context: Mapping[str, Any] | None = None,
        /,
        **kwargs: Any,
    ) -> None:
        merged: dict[str, Any] = {}
        if context is not None:
            merged.update(context)
        merged.update(kwargs)
        self._context = merged

    def render(self, template: str, *, template_ref: str) -> str:
        """Format ``template`` against the context; refuse credential leaks.

        Raises :class:`PromptCredentialLeakError` if the rendered
        output contains a credential redaction marker.
        Re-raises :class:`KeyError` from
        :meth:`str.format_map` unchanged when the template
        references a variable not in the context (a template-author
        error that should surface loudly, not be silently dropped).
        """

        rendered = template.format_map(self._context)
        if _CREDENTIAL_MARKER_RE.search(rendered):
            raise PromptCredentialLeakError(template_ref=template_ref)
        return rendered


__all__ = [
    "PromptCredentialLeakError",
    "RedactedPromptContext",
]
