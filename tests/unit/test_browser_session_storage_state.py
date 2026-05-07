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
import os
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

    def storage_state(self, *, path: str | None = None) -> dict[str, Any]:
        # Record the call shape and return a payload. The adapter
        # invokes this without ``path`` (atomic-write recipe in
        # codex iter-3 fix-up); legacy fake callers may still pass
        # path, so accept both.
        self.storage_state_calls.append({"path": path})
        payload = {"cookies": [{"name": "session", "value": "from:" + str(self.init_kwargs)}]}
        if path is not None:
            # Legacy code path — write to disk. The new adapter does
            # not exercise this branch; kept for fixture compatibility.
            Path(path).write_text(json.dumps(payload), encoding="utf-8")
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
    counts ``new_context`` calls; reuse means exactly 1 across all
    three observations (codex iter-1: replace the previous
    tautological ``session.context is session.context`` with
    captured-fake assertions)."""
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

    pw: _FakePlaywright = captured["pw"]
    # Exactly one browser launched across the whole session.
    assert len(pw.browsers) == 1
    # Exactly one context created — that is the reuse rule
    # (codex iter-4 important: assert via the fake's bookkeeping
    # rather than peeking through a public adapter property).
    browser = pw.browsers[0]
    assert len(browser.contexts) == 1, (
        "expected exactly one BrowserContext for three observations; got "
        f"{len(browser.contexts)} — context reuse is broken"
    )
    # Three pages on that one context, one per navigation. The
    # ``new_pages`` list lives on the same fake context object across
    # all three observations precisely because the adapter reused it.
    context = browser.contexts[0]
    assert len(context.new_pages) == 3
    # Route handler was registered + unregistered once per navigation
    # (the per-call cleanup contract from the iter-2 fix-up).
    assert context.routes_registered == 3
    assert context.routes_unregistered == 3


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
        "storage_state() must be called exactly once at session close"
    )
    # The adapter calls storage_state() WITHOUT a path (atomic write
    # recipe in codex iter-3 fix-up: get the dict, write it via
    # secure os.open + os.replace ourselves). Verify the file is on
    # disk in the configured directory.
    files = list(tmp_path.glob("*.storage_state.json"))
    assert len(files) == 1, "storage_state file must be on disk after close"
    assert files[0].parent == tmp_path


def test_storage_state_loaded_into_context_on_session_open(tmp_path: Path) -> None:
    """If a prior run wrote ``storage_state.json``, the next session
    re-hydrates the new context with it via ``new_context(storage_state=...)``.
    This is how cookies survive across runs."""
    # Simulate a prior run by pre-creating the file. The file MUST be
    # owner-only (0o600) on POSIX or the iter-5 read-path privacy
    # check quarantines it as untrusted.
    state_file = tmp_path / _storage_state_filename("run:rehydrate")
    state_file.write_text(
        json.dumps({"cookies": [{"name": "from-prior-run", "value": "x"}]}),
        encoding="utf-8",
    )
    if os.name == "posix":
        os.chmod(state_file, 0o600)

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

    # The adapter writes via secure os.open + os.replace itself, so
    # the canonical evidence is the filesystem state in tmp_path.
    saved_paths = sorted(tmp_path.glob("*.storage_state.json"))
    assert len(saved_paths) == 2, "distinct run_refs must produce distinct storage_state file names"
    assert len({p.name for p in saved_paths}) == 2
    # Both runs invoked storage_state() exactly once at session close.
    for entry in captured:
        context = entry["pw"].browsers[0].contexts[0]
        assert len(context.storage_state_calls) == 1


def test_run_a_does_not_load_run_b_state(tmp_path: Path) -> None:
    """If run B's storage_state file exists, run A must not pick it
    up — the file lookup is keyed on run_ref, not on whatever
    arbitrary file lives in the directory."""
    other_run_state = tmp_path / _storage_state_filename("run:other")
    other_run_state.write_text(
        json.dumps({"cookies": [{"name": "leaked", "value": "x"}]}),
        encoding="utf-8",
    )

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
    # One browser, one context, one page — even though
    # ``storage_state_dir`` is configured, the one-shot path is
    # transient (codex iter-2 important): NO storage_state= kwarg on
    # new_context, NO storage_state(path=...) call on close, and NO
    # JSON file written to disk.
    assert len(pw.browsers) == 1
    browser = pw.browsers[0]
    assert browser.closed
    assert len(browser.contexts) == 1
    context = browser.contexts[0]
    assert len(context.new_pages) == 1
    assert context.closed
    assert "storage_state" not in context.init_kwargs
    assert context.storage_state_calls == []
    assert list(tmp_path.glob("*.storage_state.json")) == []


# Codex iter-1 critical: filename collision regression -------------


@pytest.mark.parametrize(
    ("ref_a", "ref_b"),
    [
        # All three reduce to "run_a_b" under a naive ``[^A-Za-z0-9_.-]+``
        # → "_" sanitizer; the SHA-256 suffix must keep them distinct.
        ("run:a:b", "run:a/b"),
        ("run:a:b", "run:a?b"),
        ("run:a/b", "run:a?b"),
        # Different ref content, same sanitized prefix shape.
        ("run:fetch:eval", "run:fetch_eval"),
        # Pathological: the sanitizer collapses runs of unsafe chars.
        ("run::abc", "run:abc"),
    ],
)
def test_storage_state_filename_no_collision_under_naive_sanitization(
    ref_a: str, ref_b: str
) -> None:
    """Codex iter-1 critical: a non-injective filename derivation lets
    one run hydrate from another run's storage_state. Lock the
    no-collision rule with explicit pairs that the previous naive
    sanitizer collapsed."""
    assert _storage_state_filename(ref_a) != _storage_state_filename(ref_b), (
        f"distinct run_refs collided: {ref_a!r} and {ref_b!r}"
    )


def test_storage_state_filename_is_deterministic() -> None:
    """Same run_ref → same filename; replay determinism requires it."""
    assert _storage_state_filename("run:abc") == _storage_state_filename("run:abc")


# Codex iter-1 important: cleanup unconditional even on persistence failure


def test_browser_closes_when_storage_state_write_raises(tmp_path: Path) -> None:
    """If ``context.storage_state(path=...)`` raises (filesystem full,
    permissions denied, serializer bug), the browser and context
    must still close — leaking a Chromium process per failed run
    would build up to OOM in production."""

    captured: dict[str, Any] = {}

    @contextmanager
    def capturing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        captured["pw"] = pw
        yield pw

    # Subclass the fake context to raise when the adapter calls
    # ``storage_state()`` (no-arg, matches Playwright's actual API
    # after the iter-3 atomic-write refactor; codex iter-4 minor:
    # the previous version required a ``path`` kwarg and only
    # raised TypeError indirectly).
    class _FailingContext(_FakeContext):
        def storage_state(self, *, path: str | None = None) -> dict[str, Any]:
            self.storage_state_calls.append({"path": path})
            raise RuntimeError("simulated storage_state serialization failure")

    class _FailingBrowser(_FakeBrowser):
        def new_context(self, **kwargs: Any) -> _FakeContext:
            ctx = _FailingContext(self, kwargs)
            self.contexts.append(ctx)
            return ctx

    class _FailingChromium:
        def __init__(self, parent: _FakePlaywright) -> None:
            self._parent = parent

        def launch(self, *, headless: bool) -> _FakeBrowser:
            assert headless is True
            browser = _FailingBrowser()
            self._parent.browsers.append(browser)
            return browser

    @contextmanager
    def failing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        pw.chromium = _FailingChromium(pw)  # type: ignore[assignment]
        captured["pw"] = pw
        yield pw

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        playwright_factory=lambda: failing_factory,
    )
    # The session must NOT propagate the persistence failure to
    # the caller — this is best-effort persistence with logged
    # failure, not a fatal error.
    with adapter.open_session(run_ref="run:fail") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    pw: _FakePlaywright = captured["pw"]
    browser = pw.browsers[0]
    context = browser.contexts[0]
    # Cleanup ran despite the persistence error.
    assert context.closed, "BrowserContext.close() must run even when persistence raises"
    assert browser.closed, "Browser.close() must run even when persistence raises"


# Codex iter-1 important: file permissions ------------------------


def test_storage_state_file_is_owner_only(tmp_path: Path) -> None:
    """The persisted ``storage_state.json`` carries live cookies and
    origin storage; a world-readable file is a privacy regression.
    On POSIX systems we set ``chmod 0600``."""
    if os.name != "posix":  # noqa: SIM103 — explicit Windows skip
        pytest.skip("POSIX-only file mode check")

    adapter = _adapter(storage_state_dir=tmp_path)
    with adapter.open_session(run_ref="run:perm") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    files = list(tmp_path.glob("*.storage_state.json"))
    assert len(files) == 1
    mode = files[0].stat().st_mode & 0o777
    assert mode == 0o600, (
        f"storage_state file mode {oct(mode)} is broader than owner-only — "
        "anyone with read access to the directory can exfiltrate the "
        "session cookies"
    )


# Codex iter-2 important: one-shot observe must stay transient -----


def test_one_shot_observe_does_not_write_storage_state_when_dir_configured(
    tmp_path: Path,
) -> None:
    """The legacy ``adapter.observe(run_ref=..., target_url=...)``
    path is documented as transient. Even when the adapter is
    configured with ``storage_state_dir``, the one-shot path must
    not read or write the per-run storage_state file — otherwise
    two unrelated one-shot calls with the same ``run_ref`` would
    silently leak state through disk."""
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
    adapter.observe(
        run_ref="run:one-shot-transient",
        source_ref="source:fixture",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
    )

    pw: _FakePlaywright = captured["pw"]
    context = pw.browsers[0].contexts[0]
    # No storage_state= kwarg on new_context, no storage_state(path=...)
    # call on close, and no JSON file left on disk.
    assert "storage_state" not in context.init_kwargs
    assert context.storage_state_calls == []
    assert list(tmp_path.glob("*.storage_state.json")) == []


def test_one_shot_observe_does_not_load_prior_state(tmp_path: Path) -> None:
    """If a prior session wrote ``run:abc.storage_state.json``, a
    later one-shot ``observe(run_ref="run:abc", ...)`` must NOT
    re-hydrate from that file. The legacy path is transient."""
    state_file = tmp_path / _storage_state_filename("run:shared")
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(
        json.dumps({"cookies": [{"name": "from-session", "value": "x"}]}),
        encoding="utf-8",
    )

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
    adapter.observe(
        run_ref="run:shared",
        source_ref="source:fixture",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
    )
    pw: _FakePlaywright = captured["pw"]
    context = pw.browsers[0].contexts[0]
    assert "storage_state" not in context.init_kwargs


# Codex iter-2 important: per-observation cleanup robustness -------


def test_unroute_runs_when_page_close_raises(tmp_path: Path) -> None:
    """Inside a long-lived session, if ``page.close()`` raises during
    cleanup, the route handler must still get unregistered —
    otherwise route handlers stack across navigations and corrupt
    later observations' counters."""

    captured: dict[str, Any] = {}

    class _FailingClosePage(_FakePage):
        def close(self) -> None:
            raise RuntimeError("simulated page close failure")

    class _FailingClosePageContext(_FakeContext):
        def new_page(self) -> _FakePage:
            page = _FailingClosePage(self)
            self.new_pages.append(page)
            return page

    class _FailingClosePageBrowser(_FakeBrowser):
        def new_context(self, **kwargs: Any) -> _FakeContext:
            ctx = _FailingClosePageContext(self, kwargs)
            self.contexts.append(ctx)
            return ctx

    class _FailingClosePageChromium:
        def __init__(self, parent: _FakePlaywright) -> None:
            self._parent = parent

        def launch(self, *, headless: bool) -> _FakeBrowser:
            assert headless is True
            browser = _FailingClosePageBrowser()
            self._parent.browsers.append(browser)
            return browser

    @contextmanager
    def failing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        pw.chromium = _FailingClosePageChromium(pw)  # type: ignore[assignment]
        captured["pw"] = pw
        yield pw

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        playwright_factory=lambda: failing_factory,
    )
    with adapter.open_session(run_ref="run:cleanup-fail") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )
    pw: _FakePlaywright = captured["pw"]
    context = pw.browsers[0].contexts[0]
    # Route was registered AND unregistered, even though the page
    # close in between raised.
    assert context.routes_registered == 1
    assert context.routes_unregistered == 1, (
        "context.unroute must run even when page.close() raises"
    )


# Codex iter-3 important: browser cleanup on context-create failure


def test_browser_closes_when_context_create_raises(tmp_path: Path) -> None:
    """If ``browser.new_context(...)`` raises (corrupt prior storage_state,
    Playwright internal error, permission denied), the launched
    Chromium process must still close — leaking a process per failed
    setup builds up to OOM in production."""
    captured: dict[str, Any] = {}

    class _ContextCreateFailureBrowser(_FakeBrowser):
        def new_context(self, **kwargs: Any) -> _FakeContext:
            self.contexts.append(_FakeContext(self, kwargs))  # record attempt
            raise RuntimeError("simulated context create failure")

    class _ContextCreateFailureChromium:
        def __init__(self, parent: _FakePlaywright) -> None:
            self._parent = parent

        def launch(self, *, headless: bool) -> _FakeBrowser:
            assert headless is True
            browser = _ContextCreateFailureBrowser()
            self._parent.browsers.append(browser)
            return browser

    @contextmanager
    def failing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        pw.chromium = _ContextCreateFailureChromium(pw)  # type: ignore[assignment]
        captured["pw"] = pw
        yield pw

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        playwright_factory=lambda: failing_factory,
    )
    with pytest.raises(RuntimeError, match="simulated context create failure"):
        with adapter.open_session(run_ref="run:ctx-fail"):
            pass

    pw: _FakePlaywright = captured["pw"]
    assert len(pw.browsers) == 1
    assert pw.browsers[0].closed, (
        "browser.close() must run when context creation raises so the "
        "Chromium process is not leaked"
    )


# Codex iter-3 important: atomic + secure storage_state write -----


def test_storage_state_file_mode_is_set_during_create_not_after(
    tmp_path: Path,
) -> None:
    """The previous implementation called ``context.storage_state(path=...)``
    then ran ``os.chmod`` afterwards — a permission window controlled by
    the process umask sat between those two calls during which the file
    was readable by group/other. The fix uses ``os.open(...,
    O_CREAT|O_EXCL|O_WRONLY, 0o600)`` to set the mode atomically with
    creation. Verify the resulting file mode is correct on POSIX."""
    if os.name != "posix":  # noqa: SIM103 — explicit Windows skip
        pytest.skip("POSIX-only file mode check")

    adapter = _adapter(storage_state_dir=tmp_path)
    with adapter.open_session(run_ref="run:atomic") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )
    files = list(tmp_path.glob("*.storage_state.json"))
    assert len(files) == 1
    mode = files[0].stat().st_mode & 0o777
    assert mode == 0o600


def test_storage_state_write_clobbers_stale_temp_file(tmp_path: Path) -> None:
    """If a previous session crashed mid-write, a leftover ``.tmp``
    file might exist next to the final path. The atomic recipe uses
    ``O_EXCL`` so a stale temp would otherwise crash session close;
    the implementation removes any leftover temp before opening so
    a crashed prior run does not break the next one."""
    target_name = _storage_state_filename("run:after-crash")
    stale_tmp = tmp_path / (target_name + ".tmp")
    stale_tmp.write_text("garbage from prior crash", encoding="utf-8")

    adapter = _adapter(storage_state_dir=tmp_path)
    # Should not raise.
    with adapter.open_session(run_ref="run:after-crash") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    files = list(tmp_path.glob("*.storage_state.json"))
    assert len(files) == 1
    # The .tmp file is gone (consumed by the atomic rename).
    assert not stale_tmp.exists()


# Codex iter-3 minor: filename length cap ---------------------------


def test_storage_state_filename_caps_long_run_ref_prefix() -> None:
    """A pathologically long run_ref must not push the resulting
    filename past the filesystem ``NAME_MAX`` limit (255 on most
    POSIX filesystems). The prefix is capped; the digest provides
    the collision-resistant key."""
    long_ref = "run:" + ("very-long-segment" * 50)
    filename = _storage_state_filename(long_ref)
    # Stay safely below NAME_MAX=255 across all common filesystems.
    assert len(filename) <= 200
    # Two distinct long refs that share the cap-truncated prefix
    # must still produce distinct filenames thanks to the digest.
    other_long_ref = long_ref + "_distinct_suffix"
    assert _storage_state_filename(long_ref) != _storage_state_filename(other_long_ref)


# Codex iter-4 important: full-payload write (no truncation) ------


def test_storage_state_write_loops_until_complete(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``os.write`` may perform a partial write; the adapter must
    loop until every byte reaches the kernel buffer (codex iter-4
    important: a partial write would leave a truncated JSON file
    that later sessions try to hydrate from). Simulate a flaky
    ``os.write`` that returns 1 byte at a time and verify the
    final on-disk file contains the complete JSON payload."""
    import veracrawl.adapters.browser.playwright as playwright_module

    real_write = os.write
    write_call_count = {"count": 0}

    def slow_write(fd: int, data: bytes) -> int:
        # Hand back one byte at a time the first 32 calls, then
        # accept the rest in one shot.
        write_call_count["count"] += 1
        if write_call_count["count"] <= 32 and len(data) > 1:
            return real_write(fd, data[:1])
        return real_write(fd, data)

    monkeypatch.setattr(playwright_module.os, "write", slow_write)

    adapter = _adapter(storage_state_dir=tmp_path)
    with adapter.open_session(run_ref="run:partial-write") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    files = list(tmp_path.glob("*.storage_state.json"))
    assert len(files) == 1
    # The final file must contain valid JSON — a truncated write
    # would produce a JSON parse error here.
    payload = json.loads(files[0].read_text(encoding="utf-8"))
    # The fake's storage_state() returns a dict with a ``cookies``
    # key; verify the full payload survived the loop.
    assert "cookies" in payload
    # And the slow writer was actually exercised (otherwise the test
    # would not validate the loop behavior).
    assert write_call_count["count"] > 1


# Codex iter-5 important: read-path privacy boundary --------------


def test_storage_state_with_broad_permissions_is_quarantined(tmp_path: Path) -> None:
    """A pre-existing ``storage_state.json`` with mode broader than
    0o600 must NOT be ingested — it could have been written by a
    different user / a buggy producer / an attacker. Quarantine
    it and start the session with a fresh context."""
    if os.name != "posix":  # noqa: SIM103 — explicit Windows skip
        pytest.skip("POSIX-only file mode check")
    captured: dict[str, Any] = {}

    @contextmanager
    def capturing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        captured["pw"] = pw
        yield pw

    # Plant a world-readable storage_state file the attacker could
    # have written.
    state_file = tmp_path / _storage_state_filename("run:broad")
    state_file.write_text(
        json.dumps({"cookies": [{"name": "from-attacker", "value": "x"}]}),
        encoding="utf-8",
    )
    os.chmod(state_file, 0o644)  # broader than the 0o600 floor

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        playwright_factory=lambda: capturing_factory,
    )
    with adapter.open_session(run_ref="run:broad") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    pw: _FakePlaywright = captured["pw"]
    context = pw.browsers[0].contexts[0]
    # The attacker-readable file was NOT loaded into the new context.
    assert "storage_state" not in context.init_kwargs
    # The original file got quarantined out of the active path. The
    # new session does write its own state file at session close, so
    # the active path is non-empty again — what we verify is that a
    # quarantined copy exists with the attacker's content.
    quarantined = list(tmp_path.glob("*.quarantined-untrusted_permissions_or_symlink-*"))
    assert len(quarantined) == 1
    assert json.loads(quarantined[0].read_text(encoding="utf-8")) == {
        "cookies": [{"name": "from-attacker", "value": "x"}]
    }


def test_storage_state_symlink_is_quarantined(tmp_path: Path) -> None:
    """A symlink at ``storage_state_path`` must NOT be followed —
    an attacker could plant a symlink to a sensitive file and
    coerce Playwright into ingesting it as cookie state."""
    if os.name != "posix":  # noqa: SIM103 — explicit Windows skip
        pytest.skip("POSIX-only symlink check")

    captured: dict[str, Any] = {}

    @contextmanager
    def capturing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        captured["pw"] = pw
        yield pw

    # Real file with valid JSON ...
    real_file = tmp_path / "elsewhere.json"
    real_file.write_text(
        json.dumps({"cookies": [{"name": "elsewhere", "value": "x"}]}),
        encoding="utf-8",
    )
    # ... and a symlink at the storage_state path that points at it.
    state_path = tmp_path / _storage_state_filename("run:symlink")
    state_path.symlink_to(real_file)

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        playwright_factory=lambda: capturing_factory,
    )
    with adapter.open_session(run_ref="run:symlink") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    pw: _FakePlaywright = captured["pw"]
    context = pw.browsers[0].contexts[0]
    assert "storage_state" not in context.init_kwargs
    # The symlink got renamed out of the active path; verify a
    # quarantined entry exists. The session's own close writes a
    # fresh state file at the original path, so the path itself is
    # populated again — but with a regular file, not a symlink.
    quarantined = list(tmp_path.glob("*.quarantined-untrusted_permissions_or_symlink-*"))
    assert len(quarantined) == 1
    # The session-end write produced a regular file at the active
    # path, not a symlink (the symlink was moved out before the
    # write).
    if state_path.exists():
        assert state_path.is_file() and not state_path.is_symlink()


# Codex iter-5 important: corrupt-state recovery ------------------


def test_corrupt_storage_state_is_quarantined_and_session_continues(
    tmp_path: Path,
) -> None:
    """If ``browser.new_context(storage_state=...)`` raises (truncated
    JSON, schema mismatch, anything Playwright cannot parse), the
    adapter quarantines the bad file and retries ``new_context()``
    without prior state rather than aborting the run. Persisted
    state is a cache; a stale cache should not break the session."""

    captured: dict[str, Any] = {}

    # Plant a storage_state file with the right permissions but
    # invalid content shape — pass the privacy check, fail the
    # hydrate.
    state_file = tmp_path / _storage_state_filename("run:corrupt")
    state_file.write_text("{not really valid storage_state}", encoding="utf-8")
    if os.name == "posix":
        os.chmod(state_file, 0o600)

    class _CorruptHydrateBrowser(_FakeBrowser):
        def new_context(self, **kwargs: Any) -> _FakeContext:
            # Record the attempt before raising so the test can
            # introspect both the failed (with storage_state=...) and
            # subsequent (without) calls.
            ctx = _FakeContext(self, kwargs)
            self.contexts.append(ctx)
            if "storage_state" in kwargs:
                # Simulate Playwright parse failure on hydrate.
                raise RuntimeError("simulated playwright storage_state parse failure")
            return ctx

    class _CorruptHydrateChromium:
        def __init__(self, parent: _FakePlaywright) -> None:
            self._parent = parent

        def launch(self, *, headless: bool) -> _FakeBrowser:
            assert headless is True
            browser = _CorruptHydrateBrowser()
            self._parent.browsers.append(browser)
            return browser

    @contextmanager
    def failing_factory() -> Iterator[_FakePlaywright]:
        pw = _FakePlaywright()
        pw.chromium = _CorruptHydrateChromium(pw)  # type: ignore[assignment]
        captured["pw"] = pw
        yield pw

    adapter = PlaywrightBrowserObservationAdapter(
        fixture_id="step-1-1",
        target_url="https://example.test/",
        sandbox_policy=_sandbox(),
        storage_state_dir=tmp_path,
        playwright_factory=lambda: failing_factory,
    )
    # Session must NOT raise — corrupt cache → fresh context.
    with adapter.open_session(run_ref="run:corrupt") as session:
        session.observe(
            source_ref="source:fixture",
            target_url="https://example.test/",
            sandbox_policy=_sandbox(),
        )

    pw: _FakePlaywright = captured["pw"]
    browser = pw.browsers[0]
    # First new_context attempt (with storage_state) raised; the
    # adapter retried without storage_state. Both attempts are
    # recorded against the fake browser.
    assert len(browser.contexts) == 2
    first, second = browser.contexts
    assert "storage_state" in first.init_kwargs
    assert "storage_state" not in second.init_kwargs
    # The adapter quarantined the bad file before retry; the session
    # close then wrote a NEW file at the original path, so checking
    # the path itself is non-discriminating. The discriminating
    # check is that a quarantined copy exists with the original
    # corrupt content.
    quarantined = list(tmp_path.glob("*.quarantined-hydrate_failed-*"))
    assert len(quarantined) == 1
    assert quarantined[0].read_text(encoding="utf-8") == "{not really valid storage_state}"
