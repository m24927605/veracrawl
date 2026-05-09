"""Phase 4 step 4.4 — JSON-backed prompt registry adapter.

Templates live at ``<root>/<role>/<name>.<version>.json`` with
the ``PromptTemplate`` Pydantic shape. JSON (not YAML) keeps
the dependency surface tight (no PyYAML) — design.md mentions
``YamlPromptRegistry`` but the migration to YAML is recorded
as a Phase 6 reservation; the JSON shape is equivalent for the
extraction-pipeline flows Phase 4 needs.

Boundary invariants:

* Resolution is fail-closed: malformed JSON, missing required
  fields, ``output_schema_class`` not importable, or digest
  drift (Phase 6 reservation) → raise
  :class:`PromptTemplateLoadError`. Unknown ref →
  :class:`PromptTemplateNotFoundError`. Both errors carry the
  ref but never the file content.
* Path canonicalization: the registry root is resolved at
  construction; lookup paths are constructed from the
  validated ref shape ``<role>/<name>.<vN>``, then resolved
  via ``Path.resolve(strict=False)`` and verified to live
  under the root (codex recurring concern #12: path
  canonicalization). Symlinks and ``..`` components in the
  ref are blocked at the ref-shape validator (already enforced
  by ``PromptTemplate.validate_template``).
* Rendering refuses variable-set mismatches between context
  and template's declared ``variables`` (catches typos and
  smuggling of extra context values).
* Rendering goes through Phase 2 step 2.3
  :class:`RedactedPromptContext.render` — credential leaks
  raise :class:`PromptCredentialLeakError`.
"""

from __future__ import annotations

import importlib
import json
import string
import threading
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from veracrawl.agents.prompt_redaction import (
    PromptCredentialLeakError,
    RedactedPromptContext,
)
from veracrawl.contracts.prompt_registry import PromptTemplate
from veracrawl.ports.prompt_registry import (
    PromptTemplateLoadError,
    PromptTemplateNotFoundError,
    PromptTemplateVariableError,
)


def _extract_template_variables(template: str) -> set[str]:
    """Return the set of variable names referenced by a
    ``str.format_map``-style template body. Only the top-level
    field names are counted; ``{name.attr}`` is reported as
    ``name``, ``{items[0]}`` as ``items``.
    """

    formatter = string.Formatter()
    names: set[str] = set()
    for _literal, field_name, _format_spec, _conversion in formatter.parse(template):
        if not field_name:
            continue
        # Top-level identifier before the first ``.`` or ``[``.
        head = field_name
        for delim in (".", "["):
            head = head.split(delim, 1)[0]
        if head.isidentifier():
            names.add(head)
    return names


def _import_pydantic_class(dotted_path: str) -> Any:
    module_path, _, class_name = dotted_path.rpartition(".")
    if not module_path:
        raise PromptTemplateLoadError(
            template_ref=dotted_path,
            reason="output_schema_class is not a dotted path",
        )
    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        # Sanitize: the import error can include the module path,
        # but never echo arbitrary file content.
        raise PromptTemplateLoadError(
            template_ref=dotted_path,
            reason=f"output_schema_class module not importable: {module_path!r}",
        ) from exc
    if not hasattr(module, class_name):
        raise PromptTemplateLoadError(
            template_ref=dotted_path,
            reason=f"output_schema_class not found in {module_path!r}",
        )
    return getattr(module, class_name)


class JsonPromptRegistry:
    """File-system-backed JSON prompt registry."""

    def __init__(self, *, root: Path | str) -> None:
        resolved_root = Path(root).resolve(strict=False)
        if not resolved_root.exists():
            raise PromptTemplateLoadError(
                template_ref="<registry-root>",
                reason=f"prompt registry root does not exist: {resolved_root!r}",
            )
        if not resolved_root.is_dir():
            raise PromptTemplateLoadError(
                template_ref="<registry-root>",
                reason="prompt registry root must be a directory",
            )
        self._root = resolved_root
        self._cache: dict[str, PromptTemplate] = {}
        self._cache_lock = threading.Lock()

    def resolve(self, ref: str) -> PromptTemplate:
        cached = self._cache.get(ref)
        if cached is not None:
            return cached
        # ``PromptTemplate.validate_template`` (used at parse
        # time below) enforces the ref shape; do a defensive
        # pre-parse sanity check so we don't open paths that
        # don't match the validated shape.
        if "/" not in ref:
            raise PromptTemplateNotFoundError(template_ref=ref)
        # Build the on-disk path from the validated shape:
        # ``<root>/<role>/<name>.<version>.json``.
        try:
            role, rest = ref.split("/", 1)
            name_part, _, version = rest.rpartition(".")
        except ValueError as exc:
            raise PromptTemplateNotFoundError(template_ref=ref) from exc
        if not role or not name_part or not version:
            raise PromptTemplateNotFoundError(template_ref=ref)
        candidate = (self._root / role / f"{name_part}.{version}.json").resolve(
            strict=False
        )
        # Path canonicalization: ensure the resolved candidate
        # stays under the root (codex recurring concern #12).
        try:
            candidate.relative_to(self._root)
        except ValueError as exc:
            raise PromptTemplateLoadError(
                template_ref=ref,
                reason="resolved path escapes registry root",
            ) from exc
        if not candidate.exists():
            raise PromptTemplateNotFoundError(template_ref=ref)
        try:
            payload = json.loads(candidate.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise PromptTemplateLoadError(
                template_ref=ref, reason="invalid JSON"
            ) from exc
        if not isinstance(payload, dict):
            raise PromptTemplateLoadError(
                template_ref=ref, reason="top-level JSON must be an object"
            )
        # ``PromptTemplate`` Pydantic validators enforce the
        # rest of the shape; convert ValidationError into our
        # sanitized error type.
        try:
            template = PromptTemplate(**payload)
        except (ValueError, TypeError) as exc:
            raise PromptTemplateLoadError(
                template_ref=ref, reason="malformed PromptTemplate shape"
            ) from exc
        if template.ref != ref:
            raise PromptTemplateLoadError(
                template_ref=ref,
                reason="file ref does not match resolution ref",
            )
        if template.output_schema_class is not None:
            # Validate the output class is importable now so
            # callers do not discover the failure at extraction
            # time.
            _import_pydantic_class(template.output_schema_class)
        # Validate that declared variables agree with the
        # variables actually referenced by the template body.
        body_variables = _extract_template_variables(template.template)
        declared = set(template.variables)
        if body_variables != declared:
            missing = sorted(body_variables - declared)
            extra = sorted(declared - body_variables)
            raise PromptTemplateLoadError(
                template_ref=ref,
                reason=(
                    "declared variables disagree with template body — "
                    f"body-only={missing} declared-only={extra}"
                ),
            )
        with self._cache_lock:
            self._cache[ref] = template
        return template

    def render(self, ref: str, context: Mapping[str, Any]) -> str:
        template = self.resolve(ref)
        # Variable-set check happens at the registry layer
        # before ``RedactedPromptContext`` runs (which only
        # enforces the credential boundary, not the
        # variable-completeness contract).
        body_variables = set(template.variables)
        ctx_variables = set(context.keys())
        missing = body_variables - ctx_variables
        extra = ctx_variables - body_variables
        if missing or extra:
            raise PromptTemplateVariableError(
                template_ref=ref,
                missing=sorted(missing),
                extra=sorted(extra),
            )
        redacted_context = RedactedPromptContext(context)
        # ``RedactedPromptContext.render`` raises
        # ``PromptCredentialLeakError`` on credential leaks and
        # surfaces ``KeyError`` for any genuinely missing
        # variable (we already pre-checked, so this guards
        # against template authors using {} replacement-spec
        # tricks that bypass the ``Formatter.parse`` walk).
        try:
            return redacted_context.render(template.template, template_ref=ref)
        except PromptCredentialLeakError:
            raise
        except KeyError as exc:
            raise PromptTemplateVariableError(
                template_ref=ref, missing=[str(exc).strip("'")], extra=[]
            ) from None


__all__ = ["JsonPromptRegistry"]
