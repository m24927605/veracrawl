"""Runtime execution mode (fixture vs production).

Many runtime support gates currently look up a fixture *scenario* string
and return a hard-coded report. That is fine for contract tests and
deterministic replay, but in production it means a request without a
recognized scenario walks the same code path and silently returns a
"runtime_unavailable" report — the gate appears to have run, but no real
backend was invoked. The team treats this as a critical correctness gap.

This module introduces an explicit ``RuntimeMode`` boundary that callers
can inspect and gate code against. Two modes:

- ``RuntimeMode.FIXTURE`` (default): the existing scenario-lookup
  behavior is preserved. Used by tests, contract demos, and replay
  drivers.
- ``RuntimeMode.PRODUCTION``: any code path that has not yet been
  implemented for production must raise
  :class:`ProductionRuntimeNotImplemented`, never silently return a
  fixture-style report.

Mode resolution order:

1. The most-recent ``with with_runtime_mode(...)`` context (a
   ``ContextVar`` lookup), if any.
2. The ``VERACRAWL_RUNTIME_MODE`` environment variable (case-insensitive,
   ``fixture`` or ``production``).
3. The default ``RuntimeMode.FIXTURE`` for backward compatibility.

Wiring this enum through the four runtime_support gate modules is the
follow-up sub-step (P0-8 sub-step 2). This commit ships the
infrastructure only; existing gates continue to behave exactly as before
until they explicitly call ``current_mode()``.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from enum import StrEnum

_ENV_VAR = "VERACRAWL_RUNTIME_MODE"


class RuntimeMode(StrEnum):
    FIXTURE = "fixture"
    PRODUCTION = "production"


_DEFAULT_MODE = RuntimeMode.FIXTURE
_mode_var: ContextVar[RuntimeMode | None] = ContextVar(
    "veracrawl_runtime_mode", default=None
)


class ProductionRuntimeNotImplemented(NotImplementedError):
    """Raised when a runtime_support code path runs in production mode but
    has not yet been wired to a real backend.

    Carries ``backend`` (e.g. ``"observability"``) and ``gate``
    (e.g. ``"run_observability_gate"``) so logs and dashboards can
    distinguish which gate / backend pair needs implementation, and
    includes a fix hint in the message so users hitting it during
    bootstrap know to either implement the backend or set
    ``VERACRAWL_RUNTIME_MODE=fixture`` for contract testing.
    """

    def __init__(self, *, backend: str, gate: str) -> None:
        self.backend = backend
        self.gate = gate
        super().__init__(
            f"production backend {backend!r} not implemented for {gate!r}; "
            f"set VERACRAWL_RUNTIME_MODE=fixture for contract testing or "
            f"implement the production path"
        )


def current_mode() -> RuntimeMode:
    """Return the active :class:`RuntimeMode` per the resolution order
    documented in the module docstring."""
    contextual = _mode_var.get()
    if contextual is not None:
        return contextual
    raw = os.getenv(_ENV_VAR)
    if raw is not None:
        try:
            return RuntimeMode(raw.lower())
        except ValueError as exc:
            valid = ", ".join(m.value for m in RuntimeMode)
            raise ValueError(
                f"{_ENV_VAR}={raw!r} is invalid; expected one of: {valid}"
            ) from exc
    return _DEFAULT_MODE


@contextmanager
def with_runtime_mode(mode: RuntimeMode) -> Iterator[RuntimeMode]:
    """Bind a runtime mode for the duration of the context.

    Nests safely (an inner ``with_runtime_mode`` overrides the outer for
    the inner scope; on exit the outer value is restored). Tests that
    need to assert behavior in a specific mode without setting an
    environment variable use this helper.
    """
    token = _mode_var.set(mode)
    try:
        yield mode
    finally:
        _mode_var.reset(token)
