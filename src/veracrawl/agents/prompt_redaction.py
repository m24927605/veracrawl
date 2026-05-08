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

# ``template_ref`` is stored as a public attribute on
# ``PromptCredentialLeakError`` and lands in log lines via
# ``__dict__`` / ``vars()`` / ``logging.exception``. Constrain it
# to a stable opaque-ID shape so a caller cannot smuggle a URL,
# token, query string, or PII parameter through the exception
# (codex iter-4 important).
_TEMPLATE_REF_RE: Final[re.Pattern[str]] = re.compile(
    r"^[a-z][a-zA-Z0-9_:.\-]*$"
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
    :class:`CredentialValue` instance — including inside custom
    objects' ``__dict__`` and ``__slots__``.

    Walks the standard container types (dict / list / tuple / set
    / frozenset) AND descends into custom-class instances by
    inspecting their ``__dict__`` (regular attributes) and
    ``__slots__`` (slot-only classes). This covers the
    ``LeakyWrapper(cred)`` attack codex iter-4 flagged: a custom
    class whose ``__format__`` reveals the secret would otherwise
    bypass both the structural walk and the credential-aware
    formatter, because ``vformat`` calls the wrapper's
    ``__format__`` on the bare wrapper value rather than reaching
    the credential through traversal.

    Cycle detection via ``id``-based ``seen`` set; fail-closed
    depth cap so a credential nested past depth 12 cannot silently
    slip through (codex iter-3 important).
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
        # Walk both keys AND values — a ``CredentialValue`` used
        # as a mapping key would violate the contract just as
        # surely as one used as a value, even though templates
        # rarely format keys directly.
        for key, sub_value in value.items():
            if _context_contains_credential(key, depth + 1, seen):
                return True
            if _context_contains_credential(sub_value, depth + 1, seen):
                return True
        return False
    if isinstance(value, list | tuple | set | frozenset):
        seen.add(obj_id)
        return any(_context_contains_credential(v, depth + 1, seen) for v in value)
    # Primitives can't host a credential — short-circuit before
    # attempting attribute introspection (faster + avoids edge
    # cases on int/float/bool/etc. which all have ``__dict__`` via
    # their type but not as instance dicts).
    if isinstance(value, str | bytes | bytearray | int | float | bool | complex) or value is None:
        return False
    seen.add(obj_id)
    # ``vars(value)`` reads ``__dict__`` directly without invoking
    # ``__getattribute__``, so a context object with a custom
    # attribute hook does not get its hook fired during the walk
    # (codex iter-5 important — minimize side effects). Falls back
    # to ``None`` for slot-only types.
    try:
        instance_dict = vars(value)
    except TypeError:
        instance_dict = None
    if isinstance(instance_dict, dict) and any(
        _context_contains_credential(v, depth + 1, seen) for v in instance_dict.values()
    ):
        return True
    # Slot walking still uses ``getattr`` (the slot descriptor's
    # ``__get__``); wrap in try/except so any descriptor that
    # raises is treated as "no credential here" rather than
    # crashing the walk. This is the unavoidable side-effect path
    # for slot-only classes; documented limitation.
    slot_names = getattr(type(value), "__slots__", ())
    if isinstance(slot_names, str):
        slot_names = (slot_names,)
    for slot in slot_names:
        try:
            slot_value = getattr(value, slot)
        except (AttributeError, Exception):  # noqa: BLE001 — defensive
            continue
        if _context_contains_credential(slot_value, depth + 1, seen):
            return True
    return False


class _CredentialAwareFormatter(string.Formatter):
    """``string.Formatter`` subclass that trips a flag whenever a
    field's final resolved value is a :class:`CredentialValue`.

    Belt-and-suspenders for the structural context walk: by the
    time ``render`` calls into ``vformat``, the structural walk
    has already refused contexts containing a credential anywhere
    reachable through dict / list / tuple / set / frozenset
    containers AND through custom objects' ``__dict__`` /
    ``__slots__``. This subclass catches the residual case where
    a credential somehow slipped past the walk and is being
    formatted directly.

    Implementation strategy: override :meth:`format_field` (which
    receives the *final* resolved value before it is formatted via
    ``__format__``). No traversal is done by this subclass —
    delegating field-name parsing entirely to the stdlib
    formatter avoids the partial-reimplementation drift codex
    iter-5 flagged on the iter-4 ``_split_field_name`` helper.
    """

    def __init__(self) -> None:
        super().__init__()
        self.credential_reached = False

    def format_field(self, value: Any, format_spec: str) -> str:
        if isinstance(value, CredentialValue):
            self.credential_reached = True
            return ""
        result: str = super().format_field(value, format_spec)
        return result


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
        # Sanitize the template_ref before storing on the
        # exception. The public attribute lands in log lines via
        # ``__dict__`` / ``vars()`` / ``logging.exception``; an
        # unvalidated caller could smuggle a URL query, token,
        # or PII parameter through this field. Constrain to the
        # documented opaque-ID shape; replace anything else with
        # ``[REDACTED]`` (length-only) so the exception still
        # carries a non-secret signal for triage.
        if _TEMPLATE_REF_RE.fullmatch(template_ref):
            self.template_ref = template_ref
        else:
            self.template_ref = f"[REDACTED:len={len(template_ref)}]"
        super().__init__(
            f"prompt template {self.template_ref!r} resolved to output "
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
