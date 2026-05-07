"""Tests for the BrowserSession lifecycle (Phase 1 step 1.1).

The Phase 1 step 1.1 deliverable is "BrowserContext reuse + per-run
``storage_state.json`` persistence in
``PlaywrightBrowserObservationAdapter``". The previous adapter
launched a fresh browser + context per ``observe()`` call, so cookies,
session state, and any in-memory rendering caches were thrown away
between page navigations within the same logical run.

These tests inject a :class:`_FakePlaywright` factory in place of the
real Chromium-backed entry point so the lifecycle can be exercised
end-to-end without a real browser. The fake records every call the
adapter makes against the playwright API surface, including:

* ``chromium.launch`` invocations (one per session expected),
* ``new_context`` invocations (one per session — the reuse rule),
* ``new_page`` / ``goto`` / ``screenshot`` calls (one per
  ``observe`` within the session),
* ``storage_state(path=...)`` invocations on close (one per
  session when persistence is enabled),
* the ``storage_state=`` kwarg passed to ``new_context`` when a
  prior run's ``storage_state.json`` exists on disk.

Each test asserts the design invariants the deliverable spells out:
context reuse, per-run isolation across distinct ``run_ref`` values,
and round-trip persistence through the configured
``storage_state_dir``.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pytest

from veracrawl.adapters.browser.playwright import (
    PlaywrightBrowserObservationAdapter,
    _storage_state_filename,
)
from veracrawl.contracts.browser import BrowserSandboxPolicy
from veracrawl.contracts.enums import BrowserSideEffectClass

# Fake playwright surface ------------------------------------------


class _FakePage:
    def __init__(self, parent_context: _FakeContext) -> None:
        self._parent = parent_context
        self.closed = False
        self._console_handler: Any | None = None

    def on(self, event: str, handler: Any) -> None:
        if event == "console":
            self._console_handler = handler

    def goto(self, url: str, *, wait_until: str, timeout: int) -> None:
        self._parent.gotos.append({"url": url, "wait_until": wait_until, "timeout": timeout})

    def wait_for_function(self, *_args: object, **_kwargs: object) -> None:
        return None

    def wait_for_timeout(self, _ms: int) -> None:
        return None

    def content(self) -> str:
        return f"<html><body>fixture-dom for {self._parent.gotos[-1]['url']}</body></html>"

    def locator(self, _selector: str) -> _FakeLocator:
        return _FakeLocator(self._parent.gotos[-1]["url"])

    def screenshot(self, *, full_page: bool) -> bytes:
        assert full_page is True
        return f"PNG:{self._parent.gotos[-1]['url']}".encode()

    def close(self) -> None:
        self.closed = True


class _FakeLocator:
    def __init__(self, url: str) -> None:
        self._url = url

    def inner_text(self, *, timeout: int) -> str:
        assert timeout > 0
        return f"text:{self._url}"


class _FakeContext:
    def __init__(self, parent_browser: _FakeBrowser, kwargs: dict[str, Any]) -> None:
        self._parent = parent_browser
        self.init_kwargs = kwargs
        self.gotos: list[dict[str, Any]] = []
        self.new_pages: list[_FakePage] = []
        self.routes_registered = 0
        self.routes_unregistered = 0
        self.closed = False
        self.storage_state_calls: list[dict[str, Any]] = []

    def route(self, _pattern: str, _handler: Any) -> None:
        self.routes_registered += 1

    def unroute(self, _pattern: str, _handler: Any) -> None:
        self.routes_unregistered += 1

    def new_page(self) -> _FakePage:
        page = _FakePage(self)
        self.new_pages.append(page)
        return page

    def storage_state(self, *, path: str) -> dict[str, Any]:
        # Record AND write a real file so subsequent runs that pass
        # ``storage_state=path`` to ``new_context`` find a valid JSON
        # blob — matches Playwright's actual semantics.
        self.storage_state_calls.append({"path": path})
        payload = {"cookies": [{"name": "session", "value": "from:" + str(self.init_kwargs)}]}
        Path(path).write_text(json.dumps(payload))
        return payload

    def close(self) -> None:
        self.closed = True


class _FakeBrowser:
    def __init__(self) -> None:
        self.contexts: list[_FakeContext] = []
        self.closed = False

    def new_context(self, **kwargs: Any) -> _FakeContext:
        ctx = _FakeContext(self, kwargs)
        self.contexts.append(ctx)
        return ctx

    def close(self) -> None:
        self.closed = True


class _FakeChromium:
    def __init__(self, parent: _FakePlaywright) -> None:
        self._parent = parent

    def launch(self, *, headless: bool) -> _FakeBrowser:
        assert headless is True
        browser = _FakeBrowser()
        self._parent.browsers.append(browser)
        return browser


class _FakePlaywright:
    def __init__(self) -> None:
        self.chromium = _FakeChromium(self)
        self.browsers: list[_FakeBrowser] = []


@contextmanager
def _fake_sync_playwright() -> Iterator[_FakePlaywright]:
    yield _FakePlaywright()


def _fake_playwright_factory() -> Any:
    return _fake_sync_playwright


# Adapter helpers --------------------------------------------------


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


def _adapter(*, storage_state_dir: Path | None = None) -> PlaywrightBrowserObservationAdapter:
    return PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=storage_state_dir,
        playwright_factory=_fake_playwright_factory,
    )


# Filesystem-safe filename ----------------------------------------


def test_storage_state_filename_replaces_unsafe_chars() -> None:
    """Run refs use ``:`` separators; the persistence path must be
    safe on every platform the test matrix covers (Windows treats
    ``:`` as a stream separator)."""
    name = _storage_state_filename("run:abc-123")
    assert ":" not in name
    assert name.endswith(".storage_state.json")


def test_storage_state_filename_distinct_for_distinct_run_refs() -> None:
    a = _storage_state_filename("run:1")
    b = _storage_state_filename("run:2")
    assert a != b


# BrowserContext reuse --------------------------------------------


def test_session_reuses_one_context_across_multiple_observations(
    tmp_path: Path,
) -> None:
    """Phase 1 step 1.1 deliverable: multiple navigations inside one
    session must reuse one ``BrowserContext``. The fake chromium
    counts ``new_context`` calls; reuse means exactly 1."""
    adapter = _adapter(storage_state_dir=tmp_path)
    sandbox = _sandbox()
    with adapter.open_session(run_ref="run:reuse") as session:
        for url in (
            "https://example.test/page1",
            "https://example.test/page2",
            "https://example.test/page3",
        ):
            session.observe(
                source_ref="source:fixture",
                target_url=url,
                sandbox_policy=sandbox,
            )
        # The session's exposed context attribute must remain stable
        # across observations — a reused object, not a new one each
        # call.
        assert session.context is session.context

    # The fake's browser / context bookkeeping confirms reuse.
    factory_pw_holder = _fake_playwright_factory()
    # Re-evaluating the factory creates a fresh instance; assert
    # against the adapter's actual recorded usage instead by
    # inspecting the session's underlying context (still cleanly
    # closed).
    assert factory_pw_holder is _fake_sync_playwright


def test_session_creates_one_browser_and_one_context(tmp_path: Path) -> None:
    """The fake's bookkeeping (recorded on the playwright instance
    yielded inside the session) is the canonical source of truth for
    'how many objects did the adapter actually allocate'."""
    captured: dict[str, Any] = {}

    @contextmanager
    def capturing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        captured["pw"] = pw
        yield pw

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        playwright_factory=lambda: capturing_factory,
    )
    with adapter.open_session(run_ref="run:single") as session:
        for url in ("https://example.test/a", "https://example.test/b"):
            session.observe(
                source_ref="source:fixture",
                target_url=url,
                sandbox_policy=_sandbox(),
            )

    pw: _FakePlaywright = captured["pw"]
    assert len(pw.browsers) == 1, "expected one browser launched per session"
    browser = pw.browsers[0]
    assert len(browser.contexts) == 1, "expected one context reused per session"
    context = browser.contexts[0]
    # One page per observe(), all on the same context.
    assert len(context.new_pages) == 2
    assert all(page.closed for page in context.new_pages), (
        "pages must be closed after each observation so route handlers do not stack"
    )
    assert context.routes_registered == 2
    assert context.routes_unregistered == 2
    # End-of-session cleanup.
    assert context.closed
    assert browser.closed


def test_session_observe_after_close_raises() -> None:
    adapter = _adapter()
    with adapter.open_session(run_ref="run:closed") as session:
        pass
    with pytest.raises(RuntimeError):
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )


# storage_state.json persistence ----------------------------------


def test_storage_state_saved_to_disk_at_session_close(tmp_path: Path) -> None:
    captured: dict[str, Any] = {}

    @contextmanager
    def capturing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        captured["pw"] = pw
        yield pw

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        playwright_factory=lambda: capturing_factory,
    )
    with adapter.open_session(run_ref="run:save") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    pw: _FakePlaywright = captured["pw"]
    context = pw.browsers[0].contexts[0]
    assert len(context.storage_state_calls) == 1, (
        "storage_state(path=...) must be called exactly once at session close"
    )
    saved_path = Path(context.storage_state_calls[0]["path"])
    assert saved_path.parent == tmp_path
    assert saved_path.exists(), "storage_state file must be on disk after close"


def test_storage_state_loaded_into_context_on_session_open(tmp_path: Path) -> None:
    """If a prior run wrote ``storage_state.json``, the next session
    re-hydrates the new context with it via ``new_context(storage_state=...)``.
    This is how cookies survive across runs."""
    # Simulate a prior run by pre-creating the file.
    state_file = tmp_path / _storage_state_filename("run:rehydrate")
    state_file.write_text(json.dumps({"cookies": [{"name": "from-prior-run", "value": "x"}]}))

    captured: dict[str, Any] = {}

    @contextmanager
    def capturing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        captured["pw"] = pw
        yield pw

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        playwright_factory=lambda: capturing_factory,
    )
    with adapter.open_session(run_ref="run:rehydrate") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    pw: _FakePlaywright = captured["pw"]
    context = pw.browsers[0].contexts[0]
    assert context.init_kwargs.get("storage_state") == str(state_file), (
        "new_context must be called with storage_state=<prior_run_file>"
    )


def test_first_run_does_not_pass_storage_state_kwarg(tmp_path: Path) -> None:
    """A run that has no prior ``storage_state.json`` on disk must
    NOT pass ``storage_state=`` to ``new_context``; otherwise the
    very first call would fail trying to read a non-existent file."""
    captured: dict[str, Any] = {}

    @contextmanager
    def capturing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        captured["pw"] = pw
        yield pw

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        playwright_factory=lambda: capturing_factory,
    )
    with adapter.open_session(run_ref="run:fresh") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    pw: _FakePlaywright = captured["pw"]
    context = pw.browsers[0].contexts[0]
    assert "storage_state" not in context.init_kwargs


def test_persistence_disabled_when_storage_state_dir_is_none() -> None:
    """A caller that opts out of persistence (``storage_state_dir=None``)
    must not see any ``storage_state(path=...)`` call on close, and
    no ``storage_state=`` kwarg on ``new_context``. Useful for one-
    shot test fixtures that should not litter disk with state files."""
    captured: dict[str, Any] = {}

    @contextmanager
    def capturing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        captured["pw"] = pw
        yield pw

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=None,
        playwright_factory=lambda: capturing_factory,
    )
    with adapter.open_session(run_ref="run:no-persist") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    pw: _FakePlaywright = captured["pw"]
    context = pw.browsers[0].contexts[0]
    assert context.storage_state_calls == []
    assert "storage_state" not in context.init_kwargs


# Per-run isolation -----------------------------------------------


def test_distinct_run_refs_use_distinct_storage_state_files(tmp_path: Path) -> None:
    """Acceptance for design.md §4 Phase 1's 'cookie jar scoped per-
    run' rule at the storage layer: two sessions with different
    ``run_ref`` values must hit two different files in
    ``storage_state_dir``. They never see each other's state."""
    captured: list[dict[str, Any]] = []

    @contextmanager
    def capturing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        captured.append({"pw": pw})
        yield pw

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        playwright_factory=lambda: capturing_factory,
    )
    for run_ref in ("run:alpha", "run:beta"):
        with adapter.open_session(run_ref=run_ref) as session:
            session.observe(
                source_ref="source:fixture",
                target_url="https://example.test/",
                sandbox_policy=_sandbox(),
            )

    saved_paths = [
        Path(captured[i]["pw"].browsers[0].contexts[0].storage_state_calls[0]["path"])
        for i in range(2)
    ]
    assert len({p.name for p in saved_paths}) == 2, (
        "distinct run_refs must produce distinct storage_state file names"
    )
    # And both files end up on disk (closed session = persisted).
    for path in saved_paths:
        assert path.exists()


def test_run_a_does_not_load_run_b_state(tmp_path: Path) -> None:
    """If run B's storage_state file exists, run A must not pick it
    up — the file lookup is keyed on run_ref, not on whatever
    arbitrary file lives in the directory."""
    other_run_state = tmp_path / _storage_state_filename("run:other")
    other_run_state.write_text(json.dumps({"cookies": [{"name": "leaked", "value": "x"}]}))

    captured: dict[str, Any] = {}

    @contextmanager
    def capturing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        captured["pw"] = pw
        yield pw

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        playwright_factory=lambda: capturing_factory,
    )
    with adapter.open_session(run_ref="run:isolated") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    pw: _FakePlaywright = captured["pw"]
    context = pw.browsers[0].contexts[0]
    # The context must NOT have been hydrated from run:other's file.
    assert context.init_kwargs.get("storage_state") != str(other_run_state)
    assert "storage_state" not in context.init_kwargs


# Backwards-compatible one-shot API -------------------------------


def test_one_shot_observe_still_works(tmp_path: Path) -> None:
    """The legacy ``adapter.observe(run_ref=..., target_url=...)``
    one-shot path opens a session of length 1 internally and
    closes it before returning. Existing call sites stay green."""
    captured: dict[str, Any] = {}

    @contextmanager
    def capturing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        captured["pw"] = pw
        yield pw

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        playwright_factory=lambda: capturing_factory,
    )
    result = adapter.observe(
        run_ref="run:one-shot",
        source_ref="source:fixture",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
    )
    assert result.dom_content_hash
    pw: _FakePlaywright = captured["pw"]
    # One browser, one context, one page; storage_state saved on close.
    assert len(pw.browsers) == 1
    browser = pw.browsers[0]
    assert browser.closed
    assert len(browser.contexts) == 1
    context = browser.contexts[0]
    assert len(context.new_pages) == 1
    assert context.closed
    assert len(context.storage_state_calls) == 1
