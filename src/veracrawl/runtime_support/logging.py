"""Structured logging for VeraCrawl.

Provides a small, scoped logging layer on top of structlog that:

- Owns the ``veracrawl`` named logger only (does not touch the root logger),
  so pytest ``caplog``, host applications, and other libraries are unaffected.
- Renders structured events as JSON by default (``console`` format available
  for local dev) with timestamp, level, logger name, contextvars, and
  sensitive-key redaction (see ``_log_redaction``).
- Exposes ``with_correlation_id`` for binding a per-run correlation ID and
  ``bootstrap_cli_logging`` (context manager) for CLI entry points to set
  up logging plus a correlation ID without leaking ``cli=...`` into
  subsequent invocations in the same process.

Environment variables:

- ``VERACRAWL_LOG_LEVEL`` — DEBUG / INFO / WARNING / ERROR / CRITICAL (default INFO)
- ``VERACRAWL_LOG_FORMAT`` — json / console (default json)
- ``VERACRAWL_RUN_ID`` — explicit correlation ID for ``bootstrap_cli_logging``
  (otherwise a uuid4 is generated)

Invalid env values fall back to defaults with a meta-logger warning rather
than raising.
"""

from __future__ import annotations

import logging
import os
import sys
import uuid
from collections.abc import Iterator as _Iterator
from collections.abc import Mapping, MutableMapping
from contextlib import contextmanager
from contextvars import ContextVar, Token
from dataclasses import dataclass
from typing import Any

import structlog
from structlog.stdlib import BoundLogger
from structlog.types import Processor

from veracrawl.runtime_support._log_redaction import RedactSensitiveProcessor

_VERACRAWL_LOGGER_NAME = "veracrawl"
_VERACRAWL_HANDLER_TAG = "veracrawl-stream-handler"

_VALID_LEVELS = frozenset({"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"})
_VALID_FORMATS = frozenset({"json", "console"})

_correlation_id_var: ContextVar[str | None] = ContextVar(
    "veracrawl_correlation_id", default=None,
)

_meta_logger = logging.getLogger("veracrawl._meta")


@dataclass(frozen=True)
class _LoggingState:
    level: int
    log_format: str


_current_state: _LoggingState | None = None


def _correlation_id_processor(
    _logger: Any, _method_name: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    cid = _correlation_id_var.get()
    if cid is not None:
        event_dict.setdefault("correlation_id", cid)
    return event_dict


def _resolve_level(value: str | None) -> int:
    raw = value if value is not None else os.getenv("VERACRAWL_LOG_LEVEL", "INFO")
    requested = raw.upper()
    if requested not in _VALID_LEVELS:
        _meta_logger.warning(
            "invalid VERACRAWL_LOG_LEVEL=%r; falling back to INFO", requested
        )
        requested = "INFO"
    return int(getattr(logging, requested))


def _resolve_format(value: str | None) -> str:
    raw = value if value is not None else os.getenv("VERACRAWL_LOG_FORMAT", "json")
    requested = raw.lower()
    if requested not in _VALID_FORMATS:
        _meta_logger.warning(
            "invalid VERACRAWL_LOG_FORMAT=%r; falling back to json", requested
        )
        requested = "json"
    return requested


def _build_processors(log_format: str) -> list[Processor]:
    processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        _correlation_id_processor,
        RedactSensitiveProcessor(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if log_format == "console":
        # Force colors off so output shape is predictable across TTY / pytest.
        processors.append(structlog.dev.ConsoleRenderer(colors=False))
    else:
        processors.append(structlog.processors.JSONRenderer(sort_keys=True))
    return processors


def configure_logging(
    *,
    level: str | None = None,
    log_format: str | None = None,
) -> None:
    """Configure the ``veracrawl`` scoped logger.

    Idempotent: calling with the same effective config is a no-op. Calling
    with a different config rebuilds the handler and reapplies the level so
    changes take effect (no early-return short-circuit).

    Does not modify the root logger, so pytest ``caplog`` and host
    application handlers are unaffected.
    """
    global _current_state

    log_level = _resolve_level(level)
    fmt = _resolve_format(log_format)

    new_state = _LoggingState(level=log_level, log_format=fmt)
    if new_state == _current_state:
        return

    veracrawl_logger = logging.getLogger(_VERACRAWL_LOGGER_NAME)
    veracrawl_logger.setLevel(log_level)
    # Remove existing tagged handlers to avoid duplicate emission on
    # repeated configure calls. Only handlers we ourselves installed are
    # touched (host-app handlers tagged differently are left alone).
    for handler in list(veracrawl_logger.handlers):
        if getattr(handler, "_veracrawl_tag", None) == _VERACRAWL_HANDLER_TAG:
            veracrawl_logger.removeHandler(handler)

    new_handler = logging.StreamHandler(sys.stderr)
    new_handler.setLevel(log_level)
    new_handler._veracrawl_tag = _VERACRAWL_HANDLER_TAG  # type: ignore[attr-defined]
    veracrawl_logger.addHandler(new_handler)
    # Disable propagation so structured records do not double-emit through
    # root's lastResort handler. Tests that need record-level introspection
    # use ``caplog.set_level(level, logger="veracrawl")`` or capture stderr
    # with ``capfd``.
    veracrawl_logger.propagate = False

    structlog.configure(
        processors=_build_processors(fmt),
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=False,
    )

    _current_state = new_state


def reset_logging() -> None:
    """Test-fixture helper. Removes our tagged handlers and resets structlog.

    Does NOT remove root logger handlers — that would clobber pytest
    ``caplog`` and host-application handlers.
    """
    global _current_state
    veracrawl_logger = logging.getLogger(_VERACRAWL_LOGGER_NAME)
    for handler in list(veracrawl_logger.handlers):
        if getattr(handler, "_veracrawl_tag", None) == _VERACRAWL_HANDLER_TAG:
            veracrawl_logger.removeHandler(handler)
    veracrawl_logger.propagate = True  # restore default
    structlog.reset_defaults()
    _current_state = None


def get_logger(name: str | None = None) -> BoundLogger:
    """Return a scoped structlog logger under the ``veracrawl`` namespace.

    Names not already under ``veracrawl`` are prefixed; passing ``None``
    returns the root ``veracrawl`` logger. Names like ``"veracrawling.foo"``
    are NOT considered scoped (must be exactly ``veracrawl`` or start with
    ``veracrawl.``).

    Returns ``structlog.get_logger(name)`` directly — this is a lazy proxy
    that materializes its processor pipeline on EACH method call when
    structlog is configured with ``cache_logger_on_first_use=False``.
    Calling ``get_logger`` before ``configure_logging`` is therefore safe
    (the eventual ``.info(...)`` call uses the configuration that is
    active at the moment of emission, not the moment of acquisition).
    """
    actual = name or _VERACRAWL_LOGGER_NAME
    if actual != _VERACRAWL_LOGGER_NAME and not actual.startswith(
        f"{_VERACRAWL_LOGGER_NAME}."
    ):
        actual = f"{_VERACRAWL_LOGGER_NAME}.{actual}"
    # The runtime type is BoundLoggerLazyProxy, but the API contract that
    # callers depend on is BoundLogger's surface (info/warning/error/bind).
    return structlog.get_logger(actual)  # type: ignore[no-any-return]


@contextmanager
def with_correlation_id(cid: str) -> _Iterator[str]:
    """Bind a correlation ID for the lifetime of the context.

    Nests safely: an inner ``with_correlation_id`` overrides the outer for
    the inner scope; on exit the outer value is restored.

    contextvars propagate to async tasks created in the same context but
    NOT to new threads. To carry a correlation ID into a thread, the caller
    must explicitly capture and re-set it inside the thread target.
    """
    token = _correlation_id_var.set(cid)
    try:
        yield cid
    finally:
        _correlation_id_var.reset(token)


def _generate_run_id() -> str:
    return str(uuid.uuid4())


@contextmanager
def bootstrap_cli_logging(prog: str) -> _Iterator[None]:
    """CLI entry-point setup. Configure logging + bind cli/correlation context.

    Use as::

        def main() -> int:
            with bootstrap_cli_logging("veracrawl-runtime"):
                return _run(...)

    On exit, the ``cli=prog`` binding is removed (no leakage between
    invocations in the same process or test suite). The correlation ID
    is taken from ``VERACRAWL_RUN_ID`` if set, else a uuid4 is generated.
    """
    configure_logging()
    cid = os.getenv("VERACRAWL_RUN_ID") or _generate_run_id()
    cli_tokens: Mapping[str, Token[Any]] = structlog.contextvars.bind_contextvars(
        cli=prog
    )
    cid_token = _correlation_id_var.set(cid)
    try:
        yield
    finally:
        _correlation_id_var.reset(cid_token)
        # Restore previous values (or absence) for cli contextvar — safer
        # than ``unbind_contextvars`` for nested invocations.
        structlog.contextvars.reset_contextvars(**cli_tokens)
