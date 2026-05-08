"""Unit tests for Phase 2 step 2.3 — ``RedactedPromptContext``.

design.md §4 Phase 2 deliverable + acceptance:

- *Deliverable*: a wrapper that any credential value passing into
  ``prompt_template_ref`` resolution / model adapter is replaced
  with the literal ``<credential:redacted:<scope>>`` before the
  prompt enters the messages list.
- *Negative test*: passing a credential value into a prompt
  template is rejected at registry resolve time (not at provider
  adapter time); the prompt registry refuses templates whose
  rendered output equals or contains a credential ref token.
"""

from __future__ import annotations

from typing import Any

import pytest

from veracrawl.agents.prompt_redaction import (
    PromptCredentialLeakError,
    RedactedPromptContext,
)
from veracrawl.contracts.errors import PolicyViolation, VeraCrawlError
from veracrawl.ports.credential_vault import CredentialValue

# ---------------------------------------------------------------------------
# Happy path — plain templates render cleanly
# ---------------------------------------------------------------------------


def test_render_substitutes_plain_string_variables() -> None:
    ctx = RedactedPromptContext(name="Alice", role="agent")
    out = ctx.render("hello {name}, you are the {role}", template_ref="prompt:greeting")
    assert out == "hello Alice, you are the agent"


def test_render_accepts_mapping_positional_arg() -> None:
    ctx = RedactedPromptContext({"a": "X", "b": "Y"})
    out = ctx.render("{a}{b}", template_ref="prompt:x")
    assert out == "XY"


def test_render_kwargs_override_mapping_arg() -> None:
    ctx = RedactedPromptContext({"a": "old"}, a="new")
    out = ctx.render("{a}", template_ref="prompt:x")
    assert out == "new"


def test_same_instance_renders_multiple_templates_idempotently() -> None:
    ctx = RedactedPromptContext(x="1", y="2")
    assert ctx.render("{x}", template_ref="t1") == "1"
    assert ctx.render("{x}{y}", template_ref="t2") == "12"
    assert ctx.render("{x}", template_ref="t3") == "1"


def test_render_with_no_variables_is_identity() -> None:
    ctx = RedactedPromptContext()
    out = ctx.render("static prompt with no vars", template_ref="prompt:static")
    assert out == "static prompt with no vars"


# ---------------------------------------------------------------------------
# Refusal — credentials in context land as marker AND raise
# ---------------------------------------------------------------------------


def test_render_refuses_credential_value_in_context() -> None:
    """Core Phase 2 §4 acceptance test."""

    cred = CredentialValue(value="sk-live-abc", scope_ref="EBAY_PROD")
    ctx = RedactedPromptContext(token=cred)
    with pytest.raises(PromptCredentialLeakError) as excinfo:
        ctx.render("Authorization: {token}", template_ref="prompt:auth-injected")
    assert excinfo.value.template_ref == "prompt:auth-injected"


def test_render_refuses_credential_via_repr_format_flag() -> None:
    """``{cred!r}`` triggers ``__repr__`` which also emits the
    marker — must be caught by the boundary."""

    cred = CredentialValue(value="secret", scope_ref="X")
    ctx = RedactedPromptContext(cred=cred)
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("repr={cred!r}", template_ref="prompt:r")


def test_render_refuses_credential_via_str_format_flag() -> None:
    cred = CredentialValue(value="secret", scope_ref="X")
    ctx = RedactedPromptContext(cred=cred)
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("str={cred!s}", template_ref="prompt:s")


def test_render_refuses_credential_with_format_spec_padding() -> None:
    """``{cred:>40}`` invokes ``__format__`` with a spec; the
    marker stays intact under padding (Phase 2 step 2.1 contract)
    and must still be caught."""

    cred = CredentialValue(value="secret", scope_ref="X")
    ctx = RedactedPromptContext(cred=cred)
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("padded={cred:>40}", template_ref="prompt:padded")


def test_render_secret_value_never_appears_in_rendered_output_of_failed_path() -> None:
    """Even when the boundary raises, the rendered output that
    *would have been delivered* contains only the marker, not the
    secret. Verify by rendering with a try/except and inspecting
    the exception state — the rendered string must never carry
    the secret on any path."""

    secret = "sk-live-canary-xyz"
    cred = CredentialValue(value=secret, scope_ref="X")
    ctx = RedactedPromptContext(cred=cred)
    with pytest.raises(PromptCredentialLeakError) as excinfo:
        ctx.render("Authorization: {cred}", template_ref="prompt:auth")
    err = excinfo.value
    # The exception's string / repr / dict must not carry the
    # secret either — defense-in-depth across the leak vectors
    # ``CredentialScopeViolation`` already covers.
    text = f"{err!r} {err} {err.__dict__}"
    assert secret not in text


def test_multiple_credentials_in_context_still_refused() -> None:
    cred1 = CredentialValue(value="s1", scope_ref="A")
    cred2 = CredentialValue(value="s2", scope_ref="B")
    ctx = RedactedPromptContext(a=cred1, b=cred2)
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("{a} and {b}", template_ref="prompt:both")


def test_credential_alongside_plain_string_still_refused() -> None:
    cred = CredentialValue(value="s", scope_ref="X")
    ctx = RedactedPromptContext(name="Alice", token=cred)
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("hello {name}, your token is {token}", template_ref="prompt:mixed")


def test_render_refuses_attribute_traversal_into_private_slot() -> None:
    """Codex iter-1 critical: ``{cred._value}`` drills into the
    private slot via ``getattr`` (Python's ``string.Formatter``
    has no access control on private attributes). The boundary
    must refuse the template before format_map runs — otherwise
    the raw secret string lands in the rendered output and the
    marker regex never fires."""

    secret = "sk-live-private-slot-leak"
    cred = CredentialValue(value=secret, scope_ref="X")
    ctx = RedactedPromptContext(cred=cred)
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("token={cred._value}", template_ref="prompt:slot-attack")


def test_render_allows_attribute_access_on_non_credential_value() -> None:
    """Codex iter-3 important: normal ``{url.hostname}`` style
    templated formatting must work — only paths that actually reach
    a credential trip the boundary. Refusing all attribute access
    would over-restrict structured prompt contexts (URLs, lists,
    metadata dicts) that legitimate templates rely on."""

    from urllib.parse import urlsplit

    url = urlsplit("https://api.example.com/items")
    ctx = RedactedPromptContext(url=url)
    out = ctx.render("host={url.hostname}", template_ref="prompt:url")
    assert out == "host=api.example.com"


def test_render_allows_item_subscript_access_on_non_credential_value() -> None:
    """``{items[0]}`` style subscript also legitimate when the
    indexed value is not a credential."""

    ctx = RedactedPromptContext(items=["alpha", "beta"])
    out = ctx.render("first={items[0]}", template_ref="prompt:list")
    assert out == "first=alpha"


def test_render_refuses_attribute_traversal_through_custom_wrapper() -> None:
    """Codex iter-3 important: a custom object that holds a
    credential in its attributes is NOT walked by the structural
    context walk (custom objects are out of scope for the dict /
    list / tuple / set walk). The credential-aware formatter
    catches it instead — by intercepting attribute traversal and
    tripping the flag if any intermediate value is a
    ``CredentialValue``."""

    class _Wrapper:
        def __init__(self, cred: CredentialValue) -> None:
            self.cred = cred

    cred = CredentialValue(value="secret", scope_ref="EBAY_PROD")
    ctx = RedactedPromptContext(wrapper=_Wrapper(cred))
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("token={wrapper.cred}", template_ref="prompt:wrapped")


def test_render_refuses_drilling_into_credential_private_slot_via_wrapper() -> None:
    """Even drilling past the credential into its private ``_value``
    slot via a custom wrapper is caught — the intermediate
    ``wrapper.cred`` is the ``CredentialValue``, which trips the
    flag before traversal continues to ``_value``."""

    class _Wrapper:
        def __init__(self, cred: CredentialValue) -> None:
            self.cred = cred

    cred = CredentialValue(value="secret", scope_ref="X")
    ctx = RedactedPromptContext(wrapper=_Wrapper(cred))
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("v={wrapper.cred._value}", template_ref="prompt:wrap-deep")


def test_render_fails_closed_at_depth_cap() -> None:
    """Codex iter-3 important: the structural walk's depth cap
    must fail closed. Build a context graph that exceeds
    ``_MAX_CONTEXT_DEPTH`` (12) before any credential is reached;
    the walk must refuse rather than silently treat the deep
    structure as credential-free."""

    deep: Any = "leaf"
    for _ in range(20):
        deep = [deep]
    ctx = RedactedPromptContext(structure=deep)
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("static template", template_ref="prompt:deep")


def test_render_handles_cyclic_context_without_infinite_recursion() -> None:
    """Cycle detection in the structural walk: a self-referential
    list must not hang the walk. The walk should terminate (no
    credential found in the visited set) and render proceeds."""

    cyclic: list[Any] = []
    cyclic.append(cyclic)
    ctx = RedactedPromptContext(items=cyclic)
    # Render against a static template — no traversal into the
    # cyclic structure happens. The walk must terminate.
    out = ctx.render("static", template_ref="prompt:cyclic")
    assert out == "static"


def test_render_refuses_format_spec_truncation_of_marker() -> None:
    """Codex iter-1 important: ``{cred:.5}`` truncates the
    rendered marker to ``<cred`` — the marker regex would not fire
    on the truncated form, but the structural context walk catches
    the ``CredentialValue`` BEFORE format_map runs so no
    interpolation happens at all."""

    cred = CredentialValue(value="secret", scope_ref="X")
    ctx = RedactedPromptContext(cred=cred)
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("trunc={cred:.5}", template_ref="prompt:trunc")


def test_render_refuses_credential_reached_through_nested_format_spec() -> None:
    """Codex iter-2 critical: nested replacement fields inside
    format specs (e.g., ``{name:{wrapper.cred}}``) are resolved
    when format runs. If the inner traversal reaches a
    ``CredentialValue``, the credential-aware formatter must trip
    its flag — the same machinery that catches outer-field
    traversal handles nested fields too because ``vformat``
    recursively expands them."""

    class _Wrapper:
        def __init__(self, cred: CredentialValue) -> None:
            self.cred = cred

    cred = CredentialValue(value="secret", scope_ref="X")
    ctx = RedactedPromptContext(name="Alice", wrapper=_Wrapper(cred))
    with pytest.raises(PromptCredentialLeakError):
        ctx.render(
            "name={name:{wrapper.cred}}",
            template_ref="prompt:nested-cred",
        )


def test_render_refuses_credential_nested_in_dict_context() -> None:
    """Structural walk catches a credential nested inside a dict
    value — the template might never reach it, but having a
    credential in the context at all is a contract violation."""

    cred = CredentialValue(value="x", scope_ref="X")
    ctx = RedactedPromptContext(config={"auth": {"token": cred}})
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("static template", template_ref="prompt:nested-dict")


def test_render_refuses_credential_nested_in_list_context() -> None:
    cred = CredentialValue(value="x", scope_ref="X")
    ctx = RedactedPromptContext(tokens=[cred, "fake"])
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("static template", template_ref="prompt:nested-list")


def test_render_refuses_credential_nested_in_tuple_context() -> None:
    cred = CredentialValue(value="x", scope_ref="X")
    ctx = RedactedPromptContext(pair=("api_key", cred))
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("static template", template_ref="prompt:nested-tuple")


def test_template_with_literal_marker_is_refused() -> None:
    """A template author who pre-bakes the marker into the
    template string is also refused — no path through the
    boundary may emit a marker, regardless of how it got there."""

    ctx = RedactedPromptContext()
    with pytest.raises(PromptCredentialLeakError):
        ctx.render(
            "fake auth: <credential:redacted:FAKE>",
            template_ref="prompt:malicious",
        )


# ---------------------------------------------------------------------------
# Exception classification
# ---------------------------------------------------------------------------


def test_leak_error_is_caught_by_policy_violation() -> None:
    cred = CredentialValue(value="s", scope_ref="X")
    ctx = RedactedPromptContext(t=cred)
    with pytest.raises(PolicyViolation):
        ctx.render("{t}", template_ref="prompt:x")


def test_leak_error_is_caught_by_veracrawl_error() -> None:
    cred = CredentialValue(value="s", scope_ref="X")
    ctx = RedactedPromptContext(t=cred)
    with pytest.raises(VeraCrawlError):
        ctx.render("{t}", template_ref="prompt:x")


def test_leak_error_carries_template_ref_attribute() -> None:
    cred = CredentialValue(value="s", scope_ref="X")
    ctx = RedactedPromptContext(t=cred)
    with pytest.raises(PromptCredentialLeakError) as excinfo:
        ctx.render("{t}", template_ref="prompt:greeting:v3")
    assert excinfo.value.template_ref == "prompt:greeting:v3"


# ---------------------------------------------------------------------------
# Template-author errors propagate (don't silently drop)
# ---------------------------------------------------------------------------


def test_missing_variable_raises_keyerror() -> None:
    """A template that references a variable not present in the
    context must surface as :class:`KeyError` from
    ``str.format_map``. Silently dropping or replacing with empty
    string would mask template-author bugs in production."""

    ctx = RedactedPromptContext(name="Alice")
    with pytest.raises(KeyError):
        ctx.render("{missing}", template_ref="prompt:x")
