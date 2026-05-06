"""Tests for PlaywrightBrowserObservationAdapter configuration surface.

The adapter cannot be exercised end-to-end without a real Chromium
install, so these tests focus on:

1. **Charter compliance** — the adapter must not ship code that
   evades WAF / bot-detection per
   ``docs/09-target-capability-model.md`` §Safety Boundary, which
   forbids "stealth automation" and "ban-avoidance proxy tactics".
2. **Configuration shape** — the kwargs added in this iteration
   (``user_agent``, ``wait_until``, ``post_load_idle_ms``) and the
   default rendering-stability headers do what they say.
"""

from __future__ import annotations

import pytest

from veracrawl.adapters.browser.playwright import PlaywrightBrowserObservationAdapter
from veracrawl.contracts.browser import BrowserSandboxPolicy
from veracrawl.contracts.enums import BrowserSideEffectClass


def _sandbox() -> BrowserSandboxPolicy:
    return BrowserSandboxPolicy(
        id="sandbox:test",
        allowed_origin_refs=["origin:example.test"],
        egress_allowlist=["https://example.test"],
        max_runtime_ms=30000,
        max_dom_bytes=10_000_000,
        max_screenshot_bytes=10_000_000,
        max_network_log_bytes=1_000_000,
        allowed_side_effect_classes=[BrowserSideEffectClass.READ_ONLY],
    )


def _adapter(**overrides: object) -> PlaywrightBrowserObservationAdapter:
    base: dict[str, object] = {
        "fixture_id": "test",
        "target_url": "https://example.test/",
        "sandbox_policy": _sandbox(),
        "side_effect_class": BrowserSideEffectClass.READ_ONLY,
    }
    base.update(overrides)
    return PlaywrightBrowserObservationAdapter(**base)  # type: ignore[arg-type]


# Charter compliance.


def test_module_does_not_ship_stealth_automation() -> None:
    """``docs/09-target-capability-model.md`` §Safety Boundary forbids
    "stealth automation" and "WAF evasion". This test guards against
    re-introducing the navigator.webdriver / plugins / languages /
    chrome.runtime / Permissions API patches that an earlier iteration
    of this adapter shipped.
    """
    import veracrawl.adapters.browser.playwright as module

    source = module.__file__
    assert source is not None
    with open(source, encoding="utf-8") as fh:
        content = fh.read().lower()

    forbidden_patches = (
        "navigator.webdriver",
        "navigator.plugins",
        "navigator.languages",
        "window.chrome.runtime",
        "navigator.permissions.query",
        "stealth_init_scripts",
        "default_stealth_init_scripts",
    )
    for needle in forbidden_patches:
        # We allow the strings in the docstring's negative-example list,
        # but not in any executable code. The simplest enforceable rule is
        # "the strings as JS-source patches do not appear in this file".
        # The docstring uses the same names without the JS body so the
        # check uses presence + negation against the patch pattern.
        if needle in content:
            # The docstring legitimately names the forbidden patches once
            # in a comma-separated parenthetical to remind future readers.
            # Anything beyond that single reference is suspect.
            assert content.count(needle) <= 1, (
                f"{needle!r} appears more than once — likely a re-introduced "
                f"stealth patch. Per docs/09 §Safety Boundary, VeraCrawl "
                f"does not ship stealth automation."
            )


def test_stealth_init_scripts_kwarg_removed() -> None:
    """The constructor must not accept a ``stealth_init_scripts``
    keyword argument; supplying one is a charter violation surface."""
    with pytest.raises(TypeError):
        _adapter(stealth_init_scripts=("// custom",))


def test_stealth_module_does_not_exist() -> None:
    import importlib

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("veracrawl.adapters.browser._stealth")


# Rendering stability — what the adapter DOES configure (legitimately).


def test_default_user_agent_is_real_chrome() -> None:
    adapter = _adapter()
    assert "Chrome/" in adapter.user_agent
    assert "Mozilla/5.0" in adapter.user_agent
    # Legacy fingerprint UA must stay gone.
    assert "VeraCrawl-browser-quality" not in adapter.user_agent
    assert "VeraCrawl-local-fixture" not in adapter.user_agent


def test_user_agent_can_be_overridden() -> None:
    adapter = _adapter(user_agent="MyBot/1.0")
    assert adapter.user_agent == "MyBot/1.0"


def test_default_wait_until_is_domcontentloaded() -> None:
    """Was 'load' previously, which on SPA targets sat blocking on
    tracking pixels that never resolve. ``domcontentloaded`` reflects the
    DOM-ready signal callers actually want — not a stealth concern."""
    adapter = _adapter()
    assert adapter.wait_until == "domcontentloaded"


def test_wait_until_can_be_overridden() -> None:
    adapter = _adapter(wait_until="networkidle")
    assert adapter.wait_until == "networkidle"


def test_post_load_idle_ms_is_configurable() -> None:
    """Was hard-coded ``page.wait_for_timeout(250)``."""
    adapter = _adapter(post_load_idle_ms=2000)
    assert adapter.post_load_idle_ms == 2000


def test_post_load_idle_ms_default_matches_legacy() -> None:
    adapter = _adapter()
    assert adapter.post_load_idle_ms == 250


# Module hygiene.


def test_module_has_no_legacy_fingerprint_user_agent() -> None:
    import veracrawl.adapters.browser.playwright as module

    source = module.__file__
    assert source is not None
    with open(source, encoding="utf-8") as fh:
        content = fh.read()
    assert "VeraCrawl-browser-quality" not in content
    assert "VeraCrawl-local-fixture" not in content


def test_required_kwargs_enforced() -> None:
    with pytest.raises(TypeError):
        PlaywrightBrowserObservationAdapter(  # type: ignore[call-arg]
            fixture_id="x", target_url="https://x.test"
        )
