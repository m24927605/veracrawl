"""Phase 4 step 4.4 — prompt-template registry contracts.

A ``PromptTemplate`` is a versioned, immutable bundle of:

* ``ref`` — opaque ``<role>/<name>.<version>`` identifier
  (matches ``_TEMPLATE_REF_RE`` in ``agents.prompt_redaction``
  so resolution refs are safe to surface in
  ``PromptCredentialLeakError``);
* ``role`` — orchestrator role consuming the template
  (e.g., ``"extractor"``, ``"classifier"``, ``"recovery"``);
* ``name`` — human-readable name within the role;
* ``version`` — string version (``"v1"``, ``"v2"``, ...);
* ``template`` — Python ``str.format_map``-style template body
  rendered through Phase 2 step 2.3
  ``RedactedPromptContext.render``;
* ``variables`` — declared variable names the template
  references (used to validate input completeness at resolve
  time);
* ``output_schema_class`` — dotted path to a Pydantic model
  the response should validate against (Phase 4 step 4.6
  ``schema_runtime`` consumes this; step 4.4 only stores it).

Templates are immutable refs: editing a v1 file in place is a
contract violation; new versions get a new file (``v2.json``)
and a new ref. The registry detects mutation via a
content-digest sidecar (Phase 4 follow-up; today the registry
loads on demand without a digest pin — captured as a
reservation).
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import Field, model_validator

from veracrawl.contracts.common import VeraModel

_PROMPT_TEMPLATE_REF_RE = re.compile(r"^[A-Za-z0-9_-]+/[A-Za-z0-9_-]+\.v\d+$")
_NAME_PART_RE = re.compile(r"^[A-Za-z0-9_-]+$")
_VERSION_RE = re.compile(r"^v\d+$")
_OUTPUT_CLASS_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+$")


class PromptTemplate(VeraModel):
    """Validated prompt-template record."""

    ref: str
    role: str
    name: str
    version: str
    template: str
    variables: list[str] = Field(default_factory=list)
    output_schema_class: str | None = None

    @model_validator(mode="after")
    def validate_template(self) -> PromptTemplate:
        # Identifier shapes (codex recurring concern #6).
        if not _PROMPT_TEMPLATE_REF_RE.fullmatch(self.ref):
            raise ValueError(
                "prompt template ref must match <role>/<name>.<vN>"
            )
        if not _NAME_PART_RE.fullmatch(self.role):
            raise ValueError("prompt template role must match ^[A-Za-z0-9_-]+$")
        if not _NAME_PART_RE.fullmatch(self.name):
            raise ValueError("prompt template name must match ^[A-Za-z0-9_-]+$")
        if not _VERSION_RE.fullmatch(self.version):
            raise ValueError("prompt template version must match ^v\\d+$")
        # Ref must agree with role/name/version.
        expected_ref = f"{self.role}/{self.name}.{self.version}"
        if self.ref != expected_ref:
            raise ValueError(
                f"prompt template ref must equal '<role>/<name>.<version>' "
                f"(expected {expected_ref!r})"
            )
        if not self.template or not self.template.strip():
            raise ValueError("prompt template body must be non-blank")
        # Variable shape — declared variables are pure
        # identifiers, no escapes, dots, or brackets. Duplicate
        # entries are refused so a malformed contract object
        # cannot drift past validation by being silently
        # collapsed to a set in the registry.
        seen: set[str] = set()
        for variable in self.variables:
            if not _NAME_PART_RE.fullmatch(variable):
                raise ValueError(
                    "prompt template variable names must match "
                    "^[A-Za-z0-9_-]+$"
                )
            if variable in seen:
                raise ValueError(
                    f"prompt template variables must be unique "
                    f"(duplicate: {variable!r})"
                )
            seen.add(variable)
        if self.output_schema_class is not None:
            if not _OUTPUT_CLASS_RE.fullmatch(self.output_schema_class):
                raise ValueError(
                    "prompt template output_schema_class must be a "
                    "dotted Python path"
                )
        return self


__all__ = ["PromptTemplate"]


def __getattr__(name: str) -> Any:
    # Reserved for future contract additions.
    raise AttributeError(name)
