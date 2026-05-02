from __future__ import annotations

from veracrawl.browser.observation import browser_policy_failure, build_browser_sandbox_policy
from veracrawl.contracts.enums import BrowserSideEffectClass, NetworkFailureType


def test_browser_sandbox_allows_read_only() -> None:
    policy = build_browser_sandbox_policy(
        fixture_id="browser-readonly",
        origin="http://127.0.0.1:1",
    )
    assert (
        browser_policy_failure(
            side_effect_class=BrowserSideEffectClass.READ_ONLY,
            sandbox_policy=policy,
        )
        is None
    )


def test_browser_sandbox_blocks_unsafe_side_effect() -> None:
    policy = build_browser_sandbox_policy(
        fixture_id="browser-delete",
        origin="http://127.0.0.1:1",
    )
    assert (
        browser_policy_failure(
            side_effect_class=BrowserSideEffectClass.DELETE,
            sandbox_policy=policy,
        )
        == NetworkFailureType.UNSAFE_BROWSER_SIDE_EFFECT
    )
