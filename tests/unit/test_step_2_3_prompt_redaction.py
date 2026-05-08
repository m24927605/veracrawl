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


def test_render_refuses_attribute_traversal_into_public_property() -> None:
    """Even ``{cred.scope_ref}`` (which would NOT leak the secret —
    scope_ref is non-secret by design) is refused. The contract
    is "no credential reaches the prompt at all" — even via a
    non-secret accessor — so callers cannot accidentally develop
    a habit of relying on credential properties in prompts."""

    cred = CredentialValue(value="x", scope_ref="EBAY_PROD")
    ctx = RedactedPromptContext(cred=cred)
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("scope={cred.scope_ref}", template_ref="prompt:scope")


def test_render_refuses_item_subscript_access() -> None:
    """``{name[0]}`` is the subscript form of complex field
    access. Refused for the same reason as ``.attr``: subscript
    can index into list-of-credentials or dict-of-credentials
    structures past the structural-walk's container check."""

    ctx = RedactedPromptContext(items=["a", "b"])
    with pytest.raises(PromptCredentialLeakError):
        ctx.render("first={items[0]}", template_ref="prompt:subscript")


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


def test_render_refuses_nested_field_inside_format_spec() -> None:
    """Codex iter-2 critical: ``{name:{wrapper._private}}`` lets a
    template author smuggle attribute traversal inside the format
    spec. The outer field name is just ``name`` — top-level scan
    misses it. The format-spec scan must recurse into nested
    replacement fields and refuse any complex traversal anywhere
    in the parse tree."""

    ctx = RedactedPromptContext(name="Alice", wrapper="benign")
    with pytest.raises(PromptCredentialLeakError):
        ctx.render(
            "name={name:{wrapper.something}}",
            template_ref="prompt:nested-spec",
        )


def test_render_refuses_deeply_nested_field_inside_format_spec() -> None:
    """Belt-and-suspenders: even at multiple nesting levels, the
    recursive scan must still find complex field access."""

    ctx = RedactedPromptContext(a="A", b="B", c="C", d="D")
    with pytest.raises(PromptCredentialLeakError):
        ctx.render(
            "x={a:{b:{c.attr}}}",
            template_ref="prompt:deeply-nested",
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
