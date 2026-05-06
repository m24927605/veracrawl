"""Tests for PlaywrightBrowserObservationAdapter configuration surface.

The adapter cannot be exercised end-to-end without a real Chromium
install, so these tests focus on the configuration shape: defaults, the
new constructor kwargs, the stealth init-script bundle, and module
hygiene (no legacy fingerprint UA in the source).
"""

from __future__ import annotations

import pytest

from veracrawl.adapters.browser._stealth import DEFAULT_STEALTH_INIT_SCRIPTS
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


# Module hygiene.


def test_module_has_no_legacy_fingerprint_user_agent() -> None:
    import veracrawl.adapters.browser.playwright as module

    source = module.__file__
    assert source is not None
    with open(source, encoding="utf-8") as fh:
        content = fh.read()
    assert "VeraCrawl-browser-quality" not in content
    assert "VeraCrawl-local-fixture" not in content


def test_default_user_agent_is_real_chrome() -> None:
    adapter = _adapter()
    assert "Chrome/" in adapter.user_agent
    assert "Mozilla/5.0" in adapter.user_agent
    assert "VeraCrawl" not in adapter.user_agent


def test_user_agent_can_be_overridden() -> None:
    adapter = _adapter(user_agent="MyBot/1.0")
    assert adapter.user_agent == "MyBot/1.0"


# Wait strategy.


def test_default_wait_until_is_domcontentloaded() -> None:
    """Was 'load' previously, which on SPA targets sat blocking on
    tracking pixels that never resolve. ``domcontentloaded`` reflects the
    DOM-ready signal callers actually want."""
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


# Stealth init scripts.


def test_default_stealth_scripts_are_applied() -> None:
    adapter = _adapter()
    # The list comes through unchanged, instance is independent of the source.
    assert adapter.stealth_init_scripts == list(DEFAULT_STEALTH_INIT_SCRIPTS)


def test_stealth_scripts_cover_known_detection_vectors() -> None:
    bundle = "\n".join(DEFAULT_STEALTH_INIT_SCRIPTS)
    # Each of these patches must exist in the default bundle.
    assert "navigator" in bundle and "webdriver" in bundle
    assert "navigator" in bundle and "plugins" in bundle
    assert "navigator" in bundle and "languages" in bundle
    assert "window.chrome" in bundle or "chrome.runtime" in bundle
    assert "permissions" in bundle.lower() or "Permission" in bundle


def test_stealth_scripts_can_be_replaced() -> None:
    adapter = _adapter(stealth_init_scripts=("// custom",))
    assert adapter.stealth_init_scripts == ["// custom"]


def test_stealth_scripts_can_be_disabled_with_empty_tuple() -> None:
    adapter = _adapter(stealth_init_scripts=())
    assert adapter.stealth_init_scripts == []


def test_stealth_scripts_instance_independent() -> None:
    """Mutating the adapter's list must not affect the module default."""
    adapter1 = _adapter()
    adapter1.stealth_init_scripts.clear()
    adapter2 = _adapter()
    assert len(adapter2.stealth_init_scripts) == len(DEFAULT_STEALTH_INIT_SCRIPTS)


# Required vs optional configuration.


def test_required_kwargs_enforced() -> None:
    with pytest.raises(TypeError):
        PlaywrightBrowserObservationAdapter(  # type: ignore[call-arg]
            fixture_id="x", target_url="https://x.test"
        )
