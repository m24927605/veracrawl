"""Phase 4 step 4.4 — prompt-template registry port.

Adapters implement this against an on-disk template store
(``JsonPromptRegistry`` in ``adapters/prompt_registry``) or
any equivalent backing (in-memory test fixture, future YAML
store, etc.). The port shape:

* ``resolve(ref)`` returns the parsed
  :class:`PromptTemplate`. Raises
  :class:`PromptTemplateNotFoundError` when the ref is
  unknown; raises :class:`PromptTemplateLoadError` when the
  backing file is malformed (cannot be parsed, missing
  required fields, output class non-importable).
* ``render(ref, context)`` resolves the template and renders
  it through Phase 2 step 2.3
  :class:`RedactedPromptContext.render`. Refuses with
  :class:`PromptCredentialLeakError` when a rendered output
  contains a credential. Refuses with
  :class:`PromptTemplateVariableError` when the context
  declares a variable not in the template's ``variables``
  list, or when the template references an undeclared
  variable.

The port is ``@runtime_checkable``. Phase 4 step 4.6
``schema_runtime`` consumes it.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Protocol, runtime_checkable

from veracrawl.contracts.errors import FatalError, PolicyViolation, VeraCrawlError
from veracrawl.contracts.prompt_registry import PromptTemplate


class PromptTemplateNotFoundError(VeraCrawlError, FatalError):
    """Raised when a ``PromptTemplateRef`` does not resolve."""

    def __init__(self, *, template_ref: str) -> None:
        # ``template_ref`` is sanitized at the upstream caller —
        # our callers pass the validated ref shape. Echo only the
        # ref itself, never any rendered content.
        self.template_ref = template_ref
        super().__init__(f"prompt template {template_ref!r} not found")


class PromptTemplateLoadError(VeraCrawlError, FatalError):
    """Raised when a backing template file cannot be loaded
    (malformed JSON, missing required fields, or the declared
    ``output_schema_class`` is not importable). Sanitized — the
    raised error message does NOT include the file content."""

    def __init__(self, *, template_ref: str, reason: str) -> None:
        self.template_ref = template_ref
        self.reason = reason
        super().__init__(
            f"failed to load prompt template {template_ref!r}: {reason}"
        )


class PromptTemplateVariableError(VeraCrawlError, PolicyViolation):
    """Raised when render-time context does not match the
    template's declared variables. Either the context declares
    extra variables (potential leak vector) or the template
    references variables the context did not provide.
    Sanitized — the raised error message names the variable
    without echoing values."""

    def __init__(self, *, template_ref: str, missing: list[str], extra: list[str]) -> None:
        self.template_ref = template_ref
        self.missing = sorted(missing)
        self.extra = sorted(extra)
        super().__init__(
            f"prompt template {template_ref!r} variable mismatch — "
            f"missing={self.missing} extra={self.extra}"
        )


@runtime_checkable
class PromptRegistryPort(Protocol):
    """Resolve and render prompt templates with credential boundary."""

    def resolve(self, ref: str) -> PromptTemplate:
        """Return the parsed template for ``ref`` or raise."""

        ...

    def render(self, ref: str, context: Mapping[str, Any]) -> str:
        """Resolve + render ``ref`` against ``context``.

        Refuses (a) unknown refs, (b) malformed templates,
        (c) variable-set mismatches between the context and
        the template, (d) rendered outputs containing a
        credential redaction marker (Phase 2 step 2.3
        ``RedactedPromptContext`` boundary, applied
        internally).
        """

        ...


__all__ = [
    "PromptRegistryPort",
    "PromptTemplateLoadError",
    "PromptTemplateNotFoundError",
    "PromptTemplateVariableError",
]
