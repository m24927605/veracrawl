"""Contract tests for Phase 1 step 1.2 wiring of ``RobotsPort`` into
``StdlibHttpSourceAdapter``.

design.md §4 Phase 1 deliverables: ``robots.txt`` enforcement on
**every** initial URL **and** every redirect target, using the same
single source-of-truth user-agent. A robots-blocked URL must raise
:class:`RobotsBlockedError`, which is a ``PolicyViolation`` mixin —
the orchestrator records-and-terminates rather than retries.

Boundary acceptance: existing tests must keep passing without any
robots configuration. The default port is :class:`NoopRobotsPort`,
which is a permissive no-op.
"""

from __future__ import annotations

import httpx
import pytest

from veracrawl.adapters.network.stdlib_http import (
    HttpClientConfig,
    RobotsBlockedError,
    StdlibHttpSourceAdapter,
)
from veracrawl.contracts.enums import AdapterType
from veracrawl.contracts.network import NetworkRequest
from veracrawl.contracts.source_adapter import SourceAdapterCommand
from veracrawl.fetch.acquisition import source_adapter_spec
from veracrawl.ports.robots import NoopRobotsPort, RobotsAdvice
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    with_runtime_mode,
)


def _make_request(url: str = "https://example.test/p/1") -> NetworkRequest:
    return NetworkRequest(
        id="network-request:step-1-2",
        run_ref="run:fixture",
        source_ref=url,
        url=url,
        method="GET",
        headers_ref="headers:step-1-2:request",
        policy_decision_refs=["policy:fixture:default"],
        egress_policy_ref="policy:fixture:egress",
        private_network_policy_ref="policy:fixture:private-network",
        robots_policy_ref="policy:fixture:robots",
        rate_budget_ref="rate:fixture:default",
        size_budget_bytes=1_000_000,
        timeout_ms=10_000,
        idempotency_key="idem:step-1-2",
    )


def _make_command() -> SourceAdapterCommand:
    return SourceAdapterCommand(
        command_envelope_id="cmd:step-1-2",
        adapter_spec=source_adapter_spec(AdapterType.HTTP),
        source_ref="https://example.test/p/1",
        policy_snapshot_ref="policy:fixture:default",
        deterministic_clock_ref="clock:fixture",
        randomness_seed_ref="random:fixture",
    )


class _StubRobotsPort:
    """Minimal port stub for stdlib_http wiring tests."""

    def __init__(
        self,
        *,
        advice: RobotsAdvice | None = None,
        per_url_advice: dict[str, RobotsAdvice] | None = None,
    ) -> None:
        self._advice = advice or RobotsAdvice(is_allowed=True)
        self._per_url = per_url_advice or {}
        self.calls: list[tuple[str, str]] = []

    def evaluate(self, url: str, *, user_agent: str) -> RobotsAdvice:
        self.calls.append((url, user_agent))
        return self._per_url.get(url, self._advice)


def _ok_transport(body: str = "<html>ok</html>") -> httpx.MockTransport:
    def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, content=body.encode("utf-8"), headers={"content-type": "text/html"}
        )

    return httpx.MockTransport(_handler)


def _redirect_transport(redirects: dict[str, str]) -> httpx.MockTransport:
    """A transport that returns 301 → ``redirects[from_url]``, then 200."""

    def _handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url in redirects:
            return httpx.Response(
                301,
                headers={"location": redirects[url], "content-type": "text/plain"},
            )
        return httpx.Response(
            200, content=b"<html>ok</html>", headers={"content-type": "text/html"}
        )

    return httpx.MockTransport(_handler)


def test_initial_url_robots_check_passes_for_allowed_url() -> None:
    robots = _StubRobotsPort(advice=RobotsAdvice(is_allowed=True))
    adapter = StdlibHttpSourceAdapter(
        _make_request("https://example.test/p/1"),
        config=HttpClientConfig(robots_port=robots),
        transport=_ok_transport(),
    )
    adapter.execute(_make_command())
    # Single host visited → port consulted once for the initial URL.
    assert robots.calls == [
        ("https://example.test/p/1", HttpClientConfig().user_agent),
    ]


def test_initial_url_robots_block_raises_robots_blocked_error() -> None:
    robots = _StubRobotsPort(advice=RobotsAdvice(is_allowed=False))
    adapter = StdlibHttpSourceAdapter(
        _make_request("https://example.test/admin"),
        config=HttpClientConfig(robots_port=robots),
        transport=_ok_transport(),
    )
    with pytest.raises(RobotsBlockedError):
        adapter.execute(_make_command())


def test_redirect_target_robots_check_runs_per_hop() -> None:
    redirects = {
        "https://example.test/start": "https://example.test/middle",
        "https://example.test/middle": "https://example.test/end",
    }
    robots = _StubRobotsPort(advice=RobotsAdvice(is_allowed=True))
    adapter = StdlibHttpSourceAdapter(
        _make_request("https://example.test/start"),
        config=HttpClientConfig(robots_port=robots),
        transport=_redirect_transport(redirects),
    )
    adapter.execute(_make_command())
    # 1 initial + 2 redirect targets = 3 robots evaluations.
    assert [call[0] for call in robots.calls] == [
        "https://example.test/start",
        "https://example.test/middle",
        "https://example.test/end",
    ]


def test_redirect_target_robots_block_terminates() -> None:
    redirects = {"https://example.test/ok": "https://example.test/admin"}
    robots = _StubRobotsPort(
        per_url_advice={
            "https://example.test/admin": RobotsAdvice(
                is_allowed=False, disallow_reason="Disallow: /admin"
            ),
        }
    )
    adapter = StdlibHttpSourceAdapter(
        _make_request("https://example.test/ok"),
        config=HttpClientConfig(robots_port=robots),
        transport=_redirect_transport(redirects),
    )
    with pytest.raises(RobotsBlockedError):
        adapter.execute(_make_command())


def test_cross_origin_redirect_robots_check_uses_target_host() -> None:
    redirects = {"https://a.example.test/start": "https://b.example.test/end"}
    robots = _StubRobotsPort(advice=RobotsAdvice(is_allowed=True))
    adapter = StdlibHttpSourceAdapter(
        _make_request("https://a.example.test/start"),
        config=HttpClientConfig(robots_port=robots),
        transport=_redirect_transport(redirects),
    )
    adapter.execute(_make_command())
    # Both hosts must be evaluated — robots.txt for ``b.example.test``
    # is what gates the second hop.
    assert [call[0] for call in robots.calls] == [
        "https://a.example.test/start",
        "https://b.example.test/end",
    ]


def test_robots_port_uses_configured_user_agent() -> None:
    robots = _StubRobotsPort(advice=RobotsAdvice(is_allowed=True))
    config = HttpClientConfig(user_agent="VeraCrawl/test", robots_port=robots)
    adapter = StdlibHttpSourceAdapter(
        _make_request("https://example.test/"),
        config=config,
        transport=_ok_transport(),
    )
    adapter.execute(_make_command())
    assert robots.calls == [("https://example.test/", "VeraCrawl/test")]


def test_default_robots_port_is_noop_so_existing_callers_unaffected() -> None:
    """No robots_port in config → behaves as if robots wasn't a thing.

    The default ``NoopRobotsPort`` is permissive; existing fixture
    tests that don't know about robots must keep working unchanged.
    """

    adapter = StdlibHttpSourceAdapter(
        _make_request("https://example.test/p/1"),
        transport=_ok_transport(),
    )
    result = adapter.execute(_make_command())
    assert result.status.value == "succeeded"


# -- codex iter-1 regression -------------------------------------


def test_robots_blocked_error_is_value_error_subclass() -> None:
    """``RobotsBlockedError`` must satisfy the existing ``except ValueError``
    handler in ``fetch.acquisition`` / ``fetch.network_acquisition``.

    Codex iter-1 important asked us to assert the public execute /
    diagnostic contract rather than only ``pytest.raises``. The
    acquisition layer's existing handler is ``except ValueError``;
    every ``NetworkAdapterError`` subclass — including
    ``RobotsBlockedError`` (PolicyViolation mixin) — inherits
    ``ValueError`` so the legacy handler keeps matching without code
    changes. This test pins that contract for ``RobotsBlockedError``
    specifically so a future refactor cannot silently break the
    acquisition-layer wiring.
    """

    assert issubclass(RobotsBlockedError, ValueError)


# -- codex iter-2 regression: production-mode gate ----------------


def test_production_mode_with_default_noop_port_fails_closed() -> None:
    """Codex iter-2 critical: ``NoopRobotsPort`` default in production
    silently bypasses robots. The adapter must fail closed when
    constructed under ``RuntimeMode.PRODUCTION`` with no real port.
    """

    with with_runtime_mode(RuntimeMode.PRODUCTION):
        with pytest.raises(ProductionRuntimeNotImplemented) as exc:
            StdlibHttpSourceAdapter(
                _make_request("https://example.test/p/1"),
                transport=_ok_transport(),
            )
    assert exc.value.backend == "robots"


def test_production_mode_with_real_port_succeeds() -> None:
    """Production mode must accept any non-noop port — the gate only
    refuses to silently bypass; it does not refuse legitimate wiring."""

    real_port = _StubRobotsPort(advice=RobotsAdvice(is_allowed=True))
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        adapter = StdlibHttpSourceAdapter(
            _make_request("https://example.test/p/1"),
            config=HttpClientConfig(robots_port=real_port),
            transport=_ok_transport(),
        )
    result = adapter.execute(_make_command())
    assert result.status.value == "succeeded"


def test_fixture_mode_with_noop_port_keeps_working() -> None:
    """Fixture mode keeps the design's "default no-op for boundary
    acceptance" — the gate is production-only.
    """

    with with_runtime_mode(RuntimeMode.FIXTURE):
        adapter = StdlibHttpSourceAdapter(
            _make_request("https://example.test/p/1"),
            config=HttpClientConfig(robots_port=NoopRobotsPort()),
            transport=_ok_transport(),
        )
    result = adapter.execute(_make_command())
    assert result.status.value == "succeeded"


def test_robots_blocked_error_carries_policy_decision_refs() -> None:
    """Codex iter-4 minor: ``_check_robots`` previously dropped
    ``policy_decision_refs`` when raising, breaking replay / audit
    traceability for blocked decisions. The error detail now embeds
    them so downstream diagnostics keep the chain.
    """

    robots = _StubRobotsPort(advice=RobotsAdvice(is_allowed=False, disallow_reason="forbidden"))
    adapter = StdlibHttpSourceAdapter(
        _make_request("https://example.test/admin"),
        config=HttpClientConfig(robots_port=robots),
        transport=_ok_transport(),
    )
    cmd = _make_command()
    # The default fixture command's ``policy_snapshot_ref`` doesn't
    # have commas, so the adapter falls back to
    # ``request.policy_decision_refs``. Check that those refs are in
    # the error detail.
    expected_ref = adapter.request.policy_decision_refs[0]
    with pytest.raises(RobotsBlockedError) as exc:
        adapter.execute(cmd)
    assert "policy_decision_refs=" in str(exc.value)
    assert expected_ref in str(exc.value)


def test_acquisition_layer_handler_catches_robots_blocked_error() -> None:
    """Simulates ``execute_source_acquisition``'s ``except ValueError``
    catch path when the adapter raises ``RobotsBlockedError``.

    The acquisition layer treats a caught ``ValueError`` as a typed
    failure (the source_result is set to ``None`` and a failure
    report is built downstream). We don't reproduce the full
    acquisition wiring here — that's covered by other tests — but we
    verify the critical link: the exception type is catchable via
    the historic ``ValueError`` handler.
    """

    robots = _StubRobotsPort(advice=RobotsAdvice(is_allowed=False, disallow_reason="forbidden"))
    adapter = StdlibHttpSourceAdapter(
        _make_request("https://example.test/forbidden"),
        config=HttpClientConfig(robots_port=robots),
        transport=_ok_transport(),
    )
    caught: ValueError | None = None
    try:
        adapter.execute(_make_command())
    except ValueError as exc:  # acquisition.py line 326 catches this
        caught = exc
    assert caught is not None
    assert isinstance(caught, RobotsBlockedError)
