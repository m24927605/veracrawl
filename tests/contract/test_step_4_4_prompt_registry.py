"""Phase 4 step 4.4 — PromptRegistryPort contract tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from veracrawl.adapters.prompt_registry.json_prompt_registry import (
    JsonPromptRegistry,
)
from veracrawl.agents.prompt_redaction import PromptCredentialLeakError
from veracrawl.contracts.prompt_registry import PromptTemplate
from veracrawl.ports.credential_vault import CredentialValue
from veracrawl.ports.prompt_registry import (
    PromptRegistryPort,
    PromptTemplateLoadError,
    PromptTemplateNotFoundError,
    PromptTemplateVariableError,
)


def _write_template(
    root: Path,
    *,
    role: str,
    name: str,
    version: str,
    template: str,
    variables: list[str],
    output_schema_class: str | None = None,
) -> str:
    role_dir = root / role
    role_dir.mkdir(parents=True, exist_ok=True)
    ref = f"{role}/{name}.{version}"
    payload = {
        "ref": ref,
        "role": role,
        "name": name,
        "version": version,
        "template": template,
        "variables": variables,
    }
    if output_schema_class is not None:
        payload["output_schema_class"] = output_schema_class
    (role_dir / f"{name}.{version}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    return ref


# --- PromptTemplate validators ---------------------------------------------


def test_prompt_template_round_trips() -> None:
    template = PromptTemplate(
        ref="extractor/product.v1",
        role="extractor",
        name="product",
        version="v1",
        template="extract {url}",
        variables=["url"],
    )
    assert template.ref == "extractor/product.v1"


def test_prompt_template_rejects_mismatched_ref() -> None:
    with pytest.raises(ValueError, match="ref must equal"):
        PromptTemplate(
            ref="extractor/wrong.v1",
            role="extractor",
            name="product",
            version="v1",
            template="extract {url}",
            variables=["url"],
        )


def test_prompt_template_rejects_blank_template_body() -> None:
    with pytest.raises(ValueError, match="non-blank"):
        PromptTemplate(
            ref="extractor/product.v1",
            role="extractor",
            name="product",
            version="v1",
            template="   ",
            variables=[],
        )


def test_prompt_template_rejects_invalid_version_shape() -> None:
    with pytest.raises(ValueError, match="version"):
        PromptTemplate(
            ref="extractor/product.v1",
            role="extractor",
            name="product",
            version="1.0",
            template="extract {url}",
            variables=["url"],
        )


def test_prompt_template_rejects_dotted_path_traversal_in_role() -> None:
    """``role`` must be a pure identifier — ``..`` would let a
    file path escape the registry root."""

    with pytest.raises(ValueError, match="role"):
        PromptTemplate(
            ref="../traversal/product.v1",
            role="../traversal",
            name="product",
            version="v1",
            template="extract {url}",
            variables=["url"],
        )


# --- JsonPromptRegistry ----------------------------------------------------


def test_resolve_known_template_returns_parsed_record(tmp_path: Path) -> None:
    ref = _write_template(
        tmp_path,
        role="extractor",
        name="product",
        version="v1",
        template="Extract product details for {url}",
        variables=["url"],
    )
    registry = JsonPromptRegistry(root=tmp_path)
    template = registry.resolve(ref)
    assert template.ref == ref
    assert template.template == "Extract product details for {url}"


def test_resolve_unknown_ref_raises_not_found(tmp_path: Path) -> None:
    registry = JsonPromptRegistry(root=tmp_path)
    with pytest.raises(PromptTemplateNotFoundError):
        registry.resolve("extractor/nonexistent.v1")


def test_resolve_malformed_json_raises_load_error(tmp_path: Path) -> None:
    role_dir = tmp_path / "extractor"
    role_dir.mkdir()
    (role_dir / "broken.v1.json").write_text("not valid json", encoding="utf-8")
    registry = JsonPromptRegistry(root=tmp_path)
    with pytest.raises(PromptTemplateLoadError, match="invalid JSON"):
        registry.resolve("extractor/broken.v1")


def test_resolve_non_object_root_raises_load_error(tmp_path: Path) -> None:
    role_dir = tmp_path / "extractor"
    role_dir.mkdir()
    (role_dir / "list.v1.json").write_text('["a", "b"]', encoding="utf-8")
    registry = JsonPromptRegistry(root=tmp_path)
    with pytest.raises(PromptTemplateLoadError, match="JSON must be an object"):
        registry.resolve("extractor/list.v1")


def test_resolve_disagreement_between_file_and_ref_raises(tmp_path: Path) -> None:
    role_dir = tmp_path / "extractor"
    role_dir.mkdir()
    payload = {
        "ref": "extractor/sneaky.v1",
        "role": "extractor",
        "name": "sneaky",
        "version": "v1",
        "template": "do thing",
        "variables": [],
    }
    (role_dir / "wrong.v1.json").write_text(json.dumps(payload), encoding="utf-8")
    registry = JsonPromptRegistry(root=tmp_path)
    with pytest.raises(PromptTemplateLoadError, match="file ref does not match"):
        registry.resolve("extractor/wrong.v1")


def test_resolve_declared_variables_must_match_template_body(
    tmp_path: Path,
) -> None:
    role_dir = tmp_path / "extractor"
    role_dir.mkdir()
    payload = {
        "ref": "extractor/mismatch.v1",
        "role": "extractor",
        "name": "mismatch",
        "version": "v1",
        "template": "Extract {url} from {origin}",
        "variables": ["url"],  # missing ``origin``
    }
    (role_dir / "mismatch.v1.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    registry = JsonPromptRegistry(root=tmp_path)
    with pytest.raises(
        PromptTemplateLoadError, match="declared variables disagree"
    ):
        registry.resolve("extractor/mismatch.v1")


def test_resolve_caches_templates(tmp_path: Path) -> None:
    ref = _write_template(
        tmp_path,
        role="extractor",
        name="product",
        version="v1",
        template="Extract {url}",
        variables=["url"],
    )
    registry = JsonPromptRegistry(root=tmp_path)
    first = registry.resolve(ref)
    # Mutate the file; a fresh load would fail because content
    # is now different. Cache hit should return the original.
    (tmp_path / "extractor" / "product.v1.json").write_text(
        "now broken", encoding="utf-8"
    )
    second = registry.resolve(ref)
    assert first is second


def test_render_produces_expected_string(tmp_path: Path) -> None:
    ref = _write_template(
        tmp_path,
        role="extractor",
        name="product",
        version="v1",
        template="Extract product at {url}",
        variables=["url"],
    )
    registry = JsonPromptRegistry(root=tmp_path)
    rendered = registry.render(ref, {"url": "https://example.com/widget"})
    assert rendered == "Extract product at https://example.com/widget"


def test_render_refuses_extra_context_variables(tmp_path: Path) -> None:
    ref = _write_template(
        tmp_path,
        role="extractor",
        name="product",
        version="v1",
        template="Extract product at {url}",
        variables=["url"],
    )
    registry = JsonPromptRegistry(root=tmp_path)
    with pytest.raises(PromptTemplateVariableError) as exc_info:
        registry.render(
            ref, {"url": "https://example.com/widget", "extra": "smuggled"}
        )
    assert "extra" in exc_info.value.extra


def test_render_refuses_missing_context_variables(tmp_path: Path) -> None:
    ref = _write_template(
        tmp_path,
        role="extractor",
        name="product",
        version="v1",
        template="Extract product at {url}",
        variables=["url"],
    )
    registry = JsonPromptRegistry(root=tmp_path)
    with pytest.raises(PromptTemplateVariableError) as exc_info:
        registry.render(ref, {})
    assert "url" in exc_info.value.missing


def test_render_refuses_credential_in_context(tmp_path: Path) -> None:
    """Phase 2 step 2.3 boundary: a CredentialValue in the
    context is refused at render time."""

    ref = _write_template(
        tmp_path,
        role="extractor",
        name="product",
        version="v1",
        template="Extract product with token {token}",
        variables=["token"],
    )
    registry = JsonPromptRegistry(root=tmp_path)
    cred = CredentialValue(value="sk-secret-canary", scope_ref="EBAY_PROD")
    with pytest.raises(PromptCredentialLeakError):
        registry.render(ref, {"token": cred})


def test_path_traversal_via_ref_blocked(tmp_path: Path) -> None:
    """A traversal-shaped ref must be refused — either as
    not-found (no file at the resolved path) or as a
    sanitized load error if the path escapes the registry
    root. Either way, the resolver must NOT return content
    from outside the root."""

    registry = JsonPromptRegistry(root=tmp_path)
    with pytest.raises((PromptTemplateNotFoundError, PromptTemplateLoadError)):
        registry.resolve("../escape.v1")


def test_runtime_checkable_protocol(tmp_path: Path) -> None:
    registry = JsonPromptRegistry(root=tmp_path)
    assert isinstance(registry, PromptRegistryPort)
