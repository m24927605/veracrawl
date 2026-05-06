"""Tests for veracrawl.runtime_support.runtime_mode."""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Iterator

import pytest

from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    current_mode,
    with_runtime_mode,
)


@pytest.fixture(autouse=True)
def _isolate_env_and_contextvar(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Each test starts with a clean env var and an unset contextvar."""
    monkeypatch.delenv("VERACRAWL_RUNTIME_MODE", raising=False)
    yield


def test_default_mode_is_fixture() -> None:
    assert current_mode() == RuntimeMode.FIXTURE


def test_env_var_production(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERACRAWL_RUNTIME_MODE", "production")
    assert current_mode() == RuntimeMode.PRODUCTION


def test_env_var_fixture(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERACRAWL_RUNTIME_MODE", "fixture")
    assert current_mode() == RuntimeMode.FIXTURE


def test_env_var_case_insensitive(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERACRAWL_RUNTIME_MODE", "PRODUCTION")
    assert current_mode() == RuntimeMode.PRODUCTION
    monkeypatch.setenv("VERACRAWL_RUNTIME_MODE", "Fixture")
    assert current_mode() == RuntimeMode.FIXTURE


def test_invalid_env_value_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERACRAWL_RUNTIME_MODE", "staging")
    with pytest.raises(ValueError, match=r"VERACRAWL_RUNTIME_MODE='staging'"):
        current_mode()


def test_with_runtime_mode_overrides_default() -> None:
    assert current_mode() == RuntimeMode.FIXTURE
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        assert current_mode() == RuntimeMode.PRODUCTION
    # Restored on exit.
    assert current_mode() == RuntimeMode.FIXTURE


def test_with_runtime_mode_overrides_env_var(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERACRAWL_RUNTIME_MODE", "production")
    assert current_mode() == RuntimeMode.PRODUCTION
    with with_runtime_mode(RuntimeMode.FIXTURE):
        assert current_mode() == RuntimeMode.FIXTURE
    # Env var-derived mode resumed on exit.
    assert current_mode() == RuntimeMode.PRODUCTION


def test_with_runtime_mode_nested() -> None:
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        assert current_mode() == RuntimeMode.PRODUCTION
        with with_runtime_mode(RuntimeMode.FIXTURE):
            assert current_mode() == RuntimeMode.FIXTURE
            with with_runtime_mode(RuntimeMode.PRODUCTION):
                assert current_mode() == RuntimeMode.PRODUCTION
            assert current_mode() == RuntimeMode.FIXTURE
        assert current_mode() == RuntimeMode.PRODUCTION
    assert current_mode() == RuntimeMode.FIXTURE


def test_with_runtime_mode_yields_the_mode() -> None:
    with with_runtime_mode(RuntimeMode.PRODUCTION) as mode:
        assert mode == RuntimeMode.PRODUCTION


def test_production_runtime_not_implemented_carries_fields() -> None:
    err = ProductionRuntimeNotImplemented(
        backend="observability", gate="run_observability_gate"
    )
    assert err.backend == "observability"
    assert err.gate == "run_observability_gate"
    assert isinstance(err, NotImplementedError)


def test_production_runtime_not_implemented_message_includes_hint() -> None:
    err = ProductionRuntimeNotImplemented(backend="dr", gate="run_dr_drill")
    msg = str(err)
    assert "dr" in msg
    assert "run_dr_drill" in msg
    # Hint that helps the user recover quickly during bootstrap.
    assert "VERACRAWL_RUNTIME_MODE=fixture" in msg


def test_runtime_mode_str_value_is_stable() -> None:
    # Wire-format the env var parses against; do not change without coordinating
    # with the env var documentation in runtime_mode.__doc__.
    assert RuntimeMode.FIXTURE.value == "fixture"
    assert RuntimeMode.PRODUCTION.value == "production"


def test_contextvar_isolated_from_threads() -> None:
    """ContextVars do NOT auto-propagate to new threads. Asserting current
    behavior so a future change to that semantics is surfaced explicitly."""
    captured: list[RuntimeMode] = []

    def worker() -> None:
        captured.append(current_mode())

    with with_runtime_mode(RuntimeMode.PRODUCTION):
        t = threading.Thread(target=worker)
        t.start()
        t.join()

    # Worker thread saw the default, not the parent's PRODUCTION binding.
    assert captured == [RuntimeMode.FIXTURE]


def test_contextvar_propagates_within_async_task() -> None:
    """Async tasks created inside the same context inherit the mode."""
    captured: list[RuntimeMode] = []

    async def task() -> None:
        captured.append(current_mode())

    async def run() -> None:
        with with_runtime_mode(RuntimeMode.PRODUCTION):
            await asyncio.create_task(task())

    asyncio.run(run())
    assert captured == [RuntimeMode.PRODUCTION]
