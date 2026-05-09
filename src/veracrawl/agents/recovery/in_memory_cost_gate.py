"""Phase 5 step 5.2 — in-memory cost gate.

Composes a per-run + per-objective + per-host cap with
repeated-failure-signature detection. Process-lifetime
state — persistent rolling-7-day caps are Phase 6 step 6.1
(production persistence).
"""

from __future__ import annotations

import math
import threading

from veracrawl.contracts.agent import TokenUsage
from veracrawl.contracts.common import Ref
from veracrawl.ports.cost_gate import (
    CostGateExceeded,
    RepeatedFailureSignatureExceeded,
)

_REPEATED_FAILURE_HARD_STOP_THRESHOLD = 2


class InMemoryCostGate:
    """Composable in-memory cap enforcer.

    Construct with a tuple of cost caps:

    * ``per_run_cost_cap`` — total $ across the run.
    * ``per_objective_cost_cap`` — total $ across all runs of
      the same objective (process-lifetime).
    * ``per_host_cost_cap`` — total $ across all runs hitting
      the same origin (process-lifetime).

    Any cap may be ``None`` to disable. Construction refuses
    if all four caps are None (no enforcement gate is
    almost always a wiring bug).
    """

    def __init__(
        self,
        *,
        per_run_cost_cap: float | None = None,
        per_objective_cost_cap: float | None = None,
        per_host_cost_cap: float | None = None,
        repeated_failure_threshold: int = _REPEATED_FAILURE_HARD_STOP_THRESHOLD,
    ) -> None:
        if all(
            cap is None
            for cap in (per_run_cost_cap, per_objective_cost_cap, per_host_cost_cap)
        ):
            raise ValueError(
                "InMemoryCostGate requires at least one cost cap; "
                "passing all None disables enforcement which is "
                "almost always a wiring bug"
            )
        for name, cap in (
            ("per_run_cost_cap", per_run_cost_cap),
            ("per_objective_cost_cap", per_objective_cost_cap),
            ("per_host_cost_cap", per_host_cost_cap),
        ):
            if cap is None:
                continue
            if not math.isfinite(cap):
                raise ValueError(f"{name} must be a finite number")
            if cap < 0:
                raise ValueError(f"{name} must be non-negative")
        if repeated_failure_threshold < 2:
            raise ValueError(
                "repeated_failure_threshold must be >= 2"
            )
        self._per_run_cost_cap = per_run_cost_cap
        self._per_objective_cost_cap = per_objective_cost_cap
        self._per_host_cost_cap = per_host_cost_cap
        self._repeated_failure_threshold = repeated_failure_threshold
        self._run_costs: dict[Ref, float] = {}
        self._objective_costs: dict[Ref, float] = {}
        self._host_costs: dict[str, float] = {}
        self._failure_counters: dict[tuple[Ref, str], int] = {}
        self._lock = threading.Lock()

    def check(
        self,
        *,
        run_ref: Ref,
        objective_ref: Ref,
        origin: str,
        failure_signature: str | None = None,
    ) -> None:
        self._validate_inputs(
            run_ref=run_ref, objective_ref=objective_ref, origin=origin
        )
        with self._lock:
            self._refuse_if_breaches_cap(
                run_ref=run_ref,
                objective_ref=objective_ref,
                origin=origin,
            )
            if failure_signature is not None:
                if not failure_signature.strip():
                    raise ValueError("failure_signature must be non-blank when present")
                key = (objective_ref, failure_signature)
                count = self._failure_counters.get(key, 0) + 1
                self._failure_counters[key] = count
                if count >= self._repeated_failure_threshold:
                    raise RepeatedFailureSignatureExceeded(
                        failure_signature=failure_signature,
                        objective_ref=objective_ref,
                        recurrence_count=count,
                    )

    def charge(
        self,
        *,
        usage: TokenUsage,
        cost_usd: float,
        run_ref: Ref,
        objective_ref: Ref,
        origin: str,
    ) -> None:
        self._validate_inputs(
            run_ref=run_ref, objective_ref=objective_ref, origin=origin
        )
        if not math.isfinite(cost_usd):
            raise ValueError("cost_usd must be a finite number")
        if cost_usd < 0:
            raise ValueError("cost_usd must be non-negative")
        del usage  # unused in cost-only gate; reserved for future
        with self._lock:
            self._run_costs[run_ref] = self._run_costs.get(run_ref, 0.0) + cost_usd
            self._objective_costs[objective_ref] = (
                self._objective_costs.get(objective_ref, 0.0) + cost_usd
            )
            self._host_costs[origin] = self._host_costs.get(origin, 0.0) + cost_usd
            self._refuse_if_breaches_cap(
                run_ref=run_ref,
                objective_ref=objective_ref,
                origin=origin,
            )

    def _validate_inputs(
        self,
        *,
        run_ref: Ref,
        objective_ref: Ref,
        origin: str,
    ) -> None:
        if not run_ref or not run_ref.strip():
            raise ValueError("run_ref must be non-blank")
        if not objective_ref or not objective_ref.strip():
            raise ValueError("objective_ref must be non-blank")
        if not origin or not origin.strip():
            raise ValueError("origin must be non-blank")

    def _refuse_if_breaches_cap(
        self, *, run_ref: Ref, objective_ref: Ref, origin: str
    ) -> None:
        run_cost = self._run_costs.get(run_ref, 0.0)
        objective_cost = self._objective_costs.get(objective_ref, 0.0)
        host_cost = self._host_costs.get(origin, 0.0)
        if (
            self._per_run_cost_cap is not None
            and run_cost > self._per_run_cost_cap
        ):
            raise CostGateExceeded(
                failed_cap="per_run_cost_cap", run_ref=run_ref
            )
        if (
            self._per_objective_cost_cap is not None
            and objective_cost > self._per_objective_cost_cap
        ):
            raise CostGateExceeded(
                failed_cap="per_objective_cost_cap", run_ref=run_ref
            )
        if (
            self._per_host_cost_cap is not None
            and host_cost > self._per_host_cost_cap
        ):
            raise CostGateExceeded(
                failed_cap="per_host_cost_cap", run_ref=run_ref
            )


__all__ = ["InMemoryCostGate"]
