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
import string
from collections.abc import Iterable, Mapping
from typing import Any, Final

from veracrawl.contracts.errors import PolicyViolation, VeraCrawlError
from veracrawl.ports.credential_vault import CredentialValue

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

# Hard cap on context-walk recursion depth. Practical contexts are
# shallow (<= 3 nested levels); the cap bounds work on accidentally
# cyclic / pathologically deep inputs.
_MAX_CONTEXT_DEPTH: Final[int] = 12


def _context_contains_credential(value: Any, depth: int = 0) -> bool:
    """Recursively walk ``value`` looking for a
    :class:`CredentialValue` instance. Depth-bounded to avoid
    pathological inputs.

    Walks dict / list / tuple / set / frozenset containers. Custom
    objects are NOT walked: a caller wrapping a credential inside
    a custom class still leaks if a template author drills into
    the wrapper via ``{wrapper.attr_chain}``, but the format-spec
    scan below refuses any complex field name traversal — so the
    only reachable surface from a template is the bare context
    keys, which this walk covers.
    """

    if depth >= _MAX_CONTEXT_DEPTH:
        return False
    if isinstance(value, CredentialValue):
        return True
    if isinstance(value, dict):
        return any(_context_contains_credential(v, depth + 1) for v in value.values())
    if isinstance(value, list | tuple | set | frozenset):
        return any(_context_contains_credential(v, depth + 1) for v in value)
    return False


def _template_uses_complex_field_access(template: str) -> bool:
    """Return ``True`` if the template references any field with
    attribute (``{name.attr}``) or item (``{name[idx]}``) traversal.

    Such traversal lets a template author drill into private
    attributes of context values — e.g., ``{cred._value}`` would
    return the raw secret string of a ``CredentialValue`` because
    Python's ``string.Formatter`` resolves ``.attr`` via
    ``getattr`` and there is no language-level access control on
    private slots. Refusing complex field access at the boundary
    keeps the contract "only the bare context keys reach
    ``__format__``" so the credential redaction overrides do
    their job.
    """

    formatter = string.Formatter()
    try:
        parsed: Iterable[tuple[str, str | None, str | None, str | None]] = (
            formatter.parse(template)
        )
    except ValueError:
        # Malformed template — let format_map raise the
        # ``ValueError`` later so the caller sees the template-
        # author error rather than a confusing "complex field"
        # refusal. Treat malformed as "no complex fields" here;
        # the actual format_map call will fail naturally.
        return False
    for _literal, field_name, _format_spec, _conversion in parsed:
        if field_name is None:
            continue
        if "." in field_name or "[" in field_name:
            return True
    return False


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

        Three layered defenses:

        1. *Structural context check*: walk the context recursively
           through dict / list / tuple / set containers; if any
           :class:`CredentialValue` is reachable, raise.
        2. *Template field-access scan*: refuse templates that use
           attribute (``{name.attr}``) or item (``{name[idx]}``)
           field access, which would let a template author drill
           into private slots of context values (e.g.,
           ``{cred._value}`` would emit the raw secret string).
        3. *Rendered-output marker scan*: catches a literal
           credential marker baked into the template string itself
           or surfaced via a path the structural walk does not
           cover.

        Raises :class:`PromptCredentialLeakError` if any of the
        three trip. Re-raises :class:`KeyError` /
        :class:`ValueError` from :meth:`str.format_map` unchanged
        for template-author errors (missing variable, malformed
        template); silent drop would mask production bugs.
        """

        for value in self._context.values():
            if _context_contains_credential(value):
                raise PromptCredentialLeakError(template_ref=template_ref)
        if _template_uses_complex_field_access(template):
            raise PromptCredentialLeakError(template_ref=template_ref)
        rendered = template.format_map(self._context)
        if _CREDENTIAL_MARKER_RE.search(rendered):
            raise PromptCredentialLeakError(template_ref=template_ref)
        return rendered


__all__ = [
    "PromptCredentialLeakError",
    "RedactedPromptContext",
]
