"""Tests for veracrawl.runtime_support.logging."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections.abc import Iterator
from typing import Any

import pytest
import structlog

from veracrawl.runtime_support.logging import (
    bootstrap_cli_logging,
    configure_logging,
    get_logger,
    reset_logging,
    with_correlation_id,
)


@pytest.fixture(autouse=True)
def _logging_isolation(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Each test starts with a fresh logging config and clean contextvars / env."""
    monkeypatch.delenv("VERACRAWL_LOG_LEVEL", raising=False)
    monkeypatch.delenv("VERACRAWL_LOG_FORMAT", raising=False)
    monkeypatch.delenv("VERACRAWL_RUN_ID", raising=False)
    reset_logging()
    structlog.contextvars.clear_contextvars()
    yield
    reset_logging()
    structlog.contextvars.clear_contextvars()


def _read_records(err: str) -> list[dict[str, Any]]:
    """Parse JSON-format stderr output into a list of records."""
    lines = [line for line in err.strip().split("\n") if line.strip()]
    return [json.loads(line) for line in lines]


def test_configure_logging_default_json(capfd: pytest.CaptureFixture[str]) -> None:
    configure_logging()
    get_logger("veracrawl.test").info("hello", k=1)
    _, err = capfd.readouterr()
    records = _read_records(err)
    assert len(records) == 1
    record = records[0]
    assert record["event"] == "hello"
    assert record["k"] == 1
    assert "timestamp" in record
    assert record["level"] == "info"
    assert record["logger"] == "veracrawl.test"


def test_configure_logging_console_format(capfd: pytest.CaptureFixture[str]) -> None:
    configure_logging(log_format="console")
    get_logger("veracrawl.test").info("hello")
    _, err = capfd.readouterr()
    assert err.strip()
    # Console output is human-readable, not JSON
    assert not err.strip().startswith("{")


def test_log_level_filters(capfd: pytest.CaptureFixture[str]) -> None:
    configure_logging(level="ERROR")
    log = get_logger("veracrawl.test")
    log.info("not visible")
    log.error("visible")
    _, err = capfd.readouterr()
    assert "visible" in err
    assert "not visible" not in err


def test_idempotent_no_duplicate_handlers() -> None:
    configure_logging()
    configure_logging()
    configure_logging()
    veracrawl_logger = logging.getLogger("veracrawl")
    tagged = [
        h for h in veracrawl_logger.handlers
        if getattr(h, "_veracrawl_tag", None) == "veracrawl-stream-handler"
    ]
    assert len(tagged) == 1


def test_idempotent_level_change_takes_effect(
    capfd: pytest.CaptureFixture[str],
) -> None:
    configure_logging(level="INFO")
    log = get_logger("veracrawl.test")
    log.info("first")
    _, err1 = capfd.readouterr()
    assert "first" in err1

    configure_logging(level="ERROR")
    log.info("second-filtered")
    log.error("third-shows")
    _, err2 = capfd.readouterr()
    assert "second-filtered" not in err2
    assert "third-shows" in err2


def test_reset_does_not_touch_root_handlers() -> None:
    root_handlers_before = list(logging.getLogger().handlers)
    configure_logging()
    reset_logging()
    root_handlers_after = list(logging.getLogger().handlers)
    assert root_handlers_before == root_handlers_after


def test_invalid_level_falls_back_to_info(capfd: pytest.CaptureFixture[str]) -> None:
    configure_logging(level="NOT_A_LEVEL")
    log = get_logger("veracrawl.test")
    log.info("info-should-show")
    _, err = capfd.readouterr()
    assert "info-should-show" in err


def test_invalid_format_falls_back_to_json(capfd: pytest.CaptureFixture[str]) -> None:
    configure_logging(log_format="not_a_format")
    get_logger("veracrawl.test").info("hello")
    _, err = capfd.readouterr()
    record = _read_records(err)[0]
    assert record["event"] == "hello"


def test_env_var_level_is_read(
    capfd: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VERACRAWL_LOG_LEVEL", "ERROR")
    configure_logging()
    log = get_logger("veracrawl.test")
    log.info("filtered")
    log.error("shows")
    _, err = capfd.readouterr()
    assert "filtered" not in err
    assert "shows" in err


def test_env_var_format_is_read(
    capfd: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VERACRAWL_LOG_FORMAT", "console")
    configure_logging()
    get_logger("veracrawl.test").info("hello")
    _, err = capfd.readouterr()
    assert not err.strip().startswith("{")


def test_correlation_id_in_logs(capfd: pytest.CaptureFixture[str]) -> None:
    configure_logging()
    log = get_logger("veracrawl.test")
    with with_correlation_id("abc-123"):
        log.info("with-cid")
    log.info("without-cid")
    _, err = capfd.readouterr()
    records = _read_records(err)
    assert len(records) == 2
    assert records[0]["correlation_id"] == "abc-123"
    assert "correlation_id" not in records[1]


def test_correlation_id_nested(capfd: pytest.CaptureFixture[str]) -> None:
    configure_logging()
    log = get_logger("veracrawl.test")
    with with_correlation_id("outer"):
        log.info("o1")
        with with_correlation_id("inner"):
            log.info("inner-msg")
        log.info("o2")
    _, err = capfd.readouterr()
    records = _read_records(err)
    assert records[0]["correlation_id"] == "outer"
    assert records[1]["correlation_id"] == "inner"
    assert records[2]["correlation_id"] == "outer"


def test_correlation_id_async_same_context(capfd: pytest.CaptureFixture[str]) -> None:
    """contextvars DO propagate to async tasks created in the same context."""
    configure_logging()
    log = get_logger("veracrawl.test")

    async def task() -> None:
        log.info("from-task")

    async def run() -> None:
        with with_correlation_id("from-async"):
            await asyncio.create_task(task())

    asyncio.run(run())
    _, err = capfd.readouterr()
    record = _read_records(err)[0]
    assert record["correlation_id"] == "from-async"


def test_correlation_id_thread_isolated(capfd: pytest.CaptureFixture[str]) -> None:
    """contextvars do NOT auto-propagate to new threads (regression: codex iter 3)."""
    configure_logging()
    log = get_logger("veracrawl.test")

    def worker() -> None:
        log.info("from-thread")

    with with_correlation_id("main"):
        t = threading.Thread(target=worker)
        t.start()
        t.join()

    _, err = capfd.readouterr()
    records = _read_records(err)
    assert len(records) == 1
    assert "correlation_id" not in records[0]


def test_redaction_processor_active_in_pipeline(
    capfd: pytest.CaptureFixture[str],
) -> None:
    configure_logging()
    get_logger("veracrawl.test").info("auth_call", api_key="sk-secret", user="alice")
    _, err = capfd.readouterr()
    record = _read_records(err)[0]
    assert record["api_key"] == "<redacted>"
    assert record["user"] == "alice"


def test_get_logger_returns_logger_with_method_surface() -> None:
    """get_logger returns a structlog logger object with the expected API.

    The runtime type is BoundLoggerLazyProxy until first method call; the
    API contract is the BoundLogger method surface (info/warning/error/bind).
    """
    configure_logging()
    log = get_logger("veracrawl.test")
    assert hasattr(log, "info")
    assert hasattr(log, "warning")
    assert hasattr(log, "error")
    assert hasattr(log, "bind")


def test_get_logger_acquired_before_configure_still_works(
    capfd: pytest.CaptureFixture[str],
) -> None:
    """A logger acquired before configure_logging() must still emit through
    the post-configure pipeline.

    Regression: an earlier implementation called .bind() in get_logger,
    which captured the structlog config at acquisition time. That snapshot
    bypassed the pipeline configured later, breaking CLI patterns that
    declare a module-level logger.
    """
    log = get_logger("veracrawl.cli.test")
    configure_logging()
    log.info("late-emit")
    _, err = capfd.readouterr()
    record = _read_records(err)[0]
    assert record["event"] == "late-emit"


def test_get_logger_normalizes_unscoped_name(
    capfd: pytest.CaptureFixture[str],
) -> None:
    configure_logging()
    get_logger("foo").info("hello")
    _, err = capfd.readouterr()
    record = _read_records(err)[0]
    assert record["logger"] == "veracrawl.foo"


def test_get_logger_does_not_match_lookalike(
    capfd: pytest.CaptureFixture[str],
) -> None:
    """`veracrawling.foo` is NOT under the `veracrawl` namespace."""
    configure_logging()
    get_logger("veracrawling.foo").info("hello")
    _, err = capfd.readouterr()
    record = _read_records(err)[0]
    # Normalized to veracrawl.veracrawling.foo (defensive prefix)
    assert record["logger"] == "veracrawl.veracrawling.foo"


def test_get_logger_root_name(capfd: pytest.CaptureFixture[str]) -> None:
    configure_logging()
    log = get_logger()
    log.info("from-root")
    _, err = capfd.readouterr()
    record = _read_records(err)[0]
    assert record["logger"] == "veracrawl"


def test_bootstrap_cli_logging_binds_cli_and_cid(
    capfd: pytest.CaptureFixture[str],
) -> None:
    log = get_logger("veracrawl.cli.test")
    with bootstrap_cli_logging("veracrawl-test"):
        log.info("inside")
    _, err = capfd.readouterr()
    record = _read_records(err)[0]
    assert record["cli"] == "veracrawl-test"
    assert record["correlation_id"]  # auto-generated uuid


def test_bootstrap_cli_logging_unbinds_on_exit(
    capfd: pytest.CaptureFixture[str],
) -> None:
    log = get_logger("veracrawl.cli.test")
    with bootstrap_cli_logging("veracrawl-test"):
        log.info("inside")
    log.info("outside")
    _, err = capfd.readouterr()
    records = _read_records(err)
    assert records[0]["cli"] == "veracrawl-test"
    assert "cli" not in records[1]
    assert "correlation_id" not in records[1]


def test_bootstrap_cli_logging_uses_env_run_id(
    capfd: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VERACRAWL_RUN_ID", "explicit-id")
    with bootstrap_cli_logging("veracrawl-test"):
        get_logger("veracrawl.cli.test").info("hello")
    _, err = capfd.readouterr()
    record = _read_records(err)[0]
    assert record["correlation_id"] == "explicit-id"


def test_bootstrap_cli_logging_no_leak_between_sequential_invocations(
    capfd: pytest.CaptureFixture[str],
) -> None:
    log = get_logger("veracrawl.cli.test")
    with bootstrap_cli_logging("a"):
        log.info("from-a")
    with bootstrap_cli_logging("b"):
        log.info("from-b")
    _, err = capfd.readouterr()
    records = _read_records(err)
    assert records[0]["cli"] == "a"
    assert records[1]["cli"] == "b"
    # cid must be different between invocations (auto-generated)
    assert records[0]["correlation_id"] != records[1]["correlation_id"]
