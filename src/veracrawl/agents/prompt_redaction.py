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

import _string  # CPython-public field-name parser; same one ``string.Formatter`` uses internally
import re
import string
from collections.abc import Mapping
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


def _context_contains_credential(
    value: Any,
    depth: int = 0,
    seen: set[int] | None = None,
) -> bool:
    """Recursively walk ``value`` looking for a
    :class:`CredentialValue` instance.

    Walks dict / list / tuple / set / frozenset containers. Custom
    objects are NOT walked here — they get covered by the
    credential-aware formatter at render time, which intercepts
    every traversal step regardless of the parent type.

    Cycle detection via ``id``-based ``seen`` set so the walk
    terminates on accidentally cyclic structures. Depth cap is a
    belt-and-suspenders bound on accidentally deep inputs;
    **fail-closed** at the cap (treat as credential-bearing) so
    a credential nested past the cap cannot silently slip through
    (codex iter-3 important).
    """

    if depth >= _MAX_CONTEXT_DEPTH:
        return True  # fail closed
    if isinstance(value, CredentialValue):
        return True
    if seen is None:
        seen = set()
    obj_id = id(value)
    if obj_id in seen:
        return False
    if isinstance(value, dict):
        seen.add(obj_id)
        return any(
            _context_contains_credential(v, depth + 1, seen) for v in value.values()
        )
    if isinstance(value, list | tuple | set | frozenset):
        seen.add(obj_id)
        return any(_context_contains_credential(v, depth + 1, seen) for v in value)
    return False


class _CredentialAwareFormatter(string.Formatter):
    """``string.Formatter`` subclass that trips a flag whenever a
    field resolution path passes through a :class:`CredentialValue`.

    Overrides :meth:`get_field` to walk attribute / item traversal
    manually (the same logic the stdlib uses, via
    ``_string.formatter_field_name_split``); after every step,
    checks whether the current value is a ``CredentialValue``. If
    so, the formatter records the breach via ``credential_reached``
    and returns a benign sentinel so render does not error
    mid-format — :meth:`RedactedPromptContext.render` checks the
    flag after ``vformat`` and raises :class:`PromptCredentialLeakError`.

    Why intercept at traversal: ``str.format_map`` (stdlib) goes
    through C code that bypasses Python-level overrides. Using
    ``string.Formatter().vformat`` instead routes through this
    subclass so traversal is observable. Catches:

    * ``{cred._value}`` (top-level credential, attribute traversal)
    * ``{wrapper.cred}`` (custom object holding a credential)
    * ``{wrapper.cred._value}`` (deeper traversal into a credential's
      private slot — even though ``_value`` is a string, the
      intermediate ``wrapper.cred`` is the credential and trips the
      flag)
    * ``{name:{wrapper.cred}}`` (nested replacement field in a
      format spec — handled by the same ``vformat`` machinery)
    """

    def __init__(self) -> None:
        super().__init__()
        self.credential_reached = False

    def get_field(
        self,
        field_name: str,
        args: Any,
        kwargs: Any,
    ) -> tuple[Any, Any]:
        first, rest = _string.formatter_field_name_split(field_name)
        obj = self.get_value(first, args, kwargs)
        if isinstance(obj, CredentialValue):
            self.credential_reached = True
            return "", first
        for is_attr, i in rest:
            obj = getattr(obj, i) if is_attr else obj[i]
            if isinstance(obj, CredentialValue):
                self.credential_reached = True
                return "", first
        return obj, first


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

        1. *Structural context walk* — recursively walks the
           context through dict / list / tuple / set containers
           with cycle detection and fail-closed depth cap; refuses
           if any :class:`CredentialValue` is reachable. Catches
           the common case of a credential supplied directly or
           nested inside a structured config dict.
        2. *Credential-aware formatter* — uses a
           ``string.Formatter`` subclass that intercepts field-
           name traversal (``{name.attr}`` / ``{name[idx]}`` /
           nested replacement fields inside format specs) and
           trips a flag if any traversal step reaches a
           :class:`CredentialValue`. Catches the case of a custom
           object in the context that holds a credential as an
           attribute — the structural walk does not descend into
           arbitrary objects, but the formatter does.
        3. *Rendered-output marker scan* — catches a literal
           credential marker baked into the template string
           itself, plus belt-and-suspenders coverage if any
           future ``__format__`` path emits the marker without
           going through the formatter's tracked traversal.

        Normal templated formatting (``{url.hostname}``,
        ``{items[0]}``, etc.) is **allowed**: only paths that
        actually reach a credential value trip the boundary.

        Raises :class:`PromptCredentialLeakError` if any defense
        trips. Re-raises :class:`KeyError` / :class:`ValueError`
        from the formatter unchanged for template-author errors
        (missing variable, malformed template); silent drop would
        mask production bugs.
        """

        for value in self._context.values():
            if _context_contains_credential(value):
                raise PromptCredentialLeakError(template_ref=template_ref)
        formatter = _CredentialAwareFormatter()
        rendered = formatter.vformat(template, (), self._context)
        if formatter.credential_reached:
            raise PromptCredentialLeakError(template_ref=template_ref)
        if _CREDENTIAL_MARKER_RE.search(rendered):
            raise PromptCredentialLeakError(template_ref=template_ref)
        return rendered


__all__ = [
    "PromptCredentialLeakError",
    "RedactedPromptContext",
]
