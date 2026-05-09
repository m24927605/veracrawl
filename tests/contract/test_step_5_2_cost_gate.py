"""Phase 5 step 5.2 — CostGatePort + InMemoryCostGate contract tests."""

from __future__ import annotations

import pytest

from veracrawl.agents.recovery.in_memory_cost_gate import InMemoryCostGate
from veracrawl.contracts.agent import TokenUsage
from veracrawl.ports.cost_gate import (
    CostGateExceeded,
    CostGatePort,
    RepeatedFailureSignatureExceeded,
)


def _usage() -> TokenUsage:
    return TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)


# --- Construction ----------------------------------------------------------


def test_gate_requires_at_least_one_cap() -> None:
    with pytest.raises(ValueError, match="at least one cost cap"):
        InMemoryCostGate()


def test_gate_rejects_negative_cap() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        InMemoryCostGate(per_run_cost_cap=-0.5)


def test_gate_rejects_non_finite_cap() -> None:
    with pytest.raises(ValueError, match="finite"):
        InMemoryCostGate(per_run_cost_cap=float("inf"))


def test_gate_rejects_threshold_below_2() -> None:
    with pytest.raises(ValueError, match="repeated_failure_threshold"):
        InMemoryCostGate(per_run_cost_cap=1.0, repeated_failure_threshold=1)


def test_gate_runtime_checkable() -> None:
    gate = InMemoryCostGate(per_run_cost_cap=1.0)
    assert isinstance(gate, CostGatePort)


# --- check passes when no cap breached -------------------------------------


def test_check_passes_under_caps() -> None:
    gate = InMemoryCostGate(per_run_cost_cap=10.0)
    gate.check(
        run_ref="run:1", objective_ref="objective:1", origin="https://example.com"
    )


def test_check_rejects_blank_inputs() -> None:
    gate = InMemoryCostGate(per_run_cost_cap=1.0)
    with pytest.raises(ValueError, match="run_ref"):
        gate.check(
            run_ref="   ", objective_ref="o:1", origin="https://x.com"
        )
    with pytest.raises(ValueError, match="objective_ref"):
        gate.check(
            run_ref="r:1", objective_ref="   ", origin="https://x.com"
        )
    with pytest.raises(ValueError, match="origin"):
        gate.check(run_ref="r:1", objective_ref="o:1", origin="   ")


# --- charge accumulates + raises on cap breach -----------------------------


def test_charge_under_per_run_cap_passes() -> None:
    gate = InMemoryCostGate(per_run_cost_cap=1.0)
    gate.charge(
        usage=_usage(),
        cost_usd=0.5,
        run_ref="run:1",
        objective_ref="o:1",
        origin="https://example.com",
    )


def test_charge_breach_per_run_cap_raises() -> None:
    gate = InMemoryCostGate(per_run_cost_cap=1.0)
    gate.charge(
        usage=_usage(),
        cost_usd=0.6,
        run_ref="run:1",
        objective_ref="o:1",
        origin="https://example.com",
    )
    with pytest.raises(CostGateExceeded) as exc_info:
        gate.charge(
            usage=_usage(),
            cost_usd=0.6,
            run_ref="run:1",
            objective_ref="o:1",
            origin="https://example.com",
        )
    assert exc_info.value.failed_cap == "per_run_cost_cap"
    assert exc_info.value.run_ref == "run:1"


def test_charge_breach_per_objective_cap_raises() -> None:
    gate = InMemoryCostGate(per_objective_cost_cap=1.0)
    gate.charge(
        usage=_usage(),
        cost_usd=0.6,
        run_ref="run:1",
        objective_ref="o:1",
        origin="https://example.com",
    )
    with pytest.raises(CostGateExceeded) as exc_info:
        gate.charge(
            usage=_usage(),
            cost_usd=0.6,
            run_ref="run:2",  # different run, same objective
            objective_ref="o:1",
            origin="https://example.com",
        )
    assert exc_info.value.failed_cap == "per_objective_cost_cap"


def test_charge_breach_per_host_cap_raises() -> None:
    gate = InMemoryCostGate(per_host_cost_cap=1.0)
    gate.charge(
        usage=_usage(),
        cost_usd=0.6,
        run_ref="run:1",
        objective_ref="o:1",
        origin="https://example.com",
    )
    with pytest.raises(CostGateExceeded) as exc_info:
        gate.charge(
            usage=_usage(),
            cost_usd=0.6,
            run_ref="run:2",  # different run + objective, same origin
            objective_ref="o:2",
            origin="https://example.com",
        )
    assert exc_info.value.failed_cap == "per_host_cost_cap"


def test_charge_tightest_cap_wins() -> None:
    """When multiple caps are breached, the order of checks
    in ``_refuse_if_breaches_cap`` decides which is reported.
    Per design.md: per_run is checked first because it's the
    most-bound-to-the-current-request cap."""

    gate = InMemoryCostGate(
        per_run_cost_cap=0.5,
        per_objective_cost_cap=10.0,
        per_host_cost_cap=10.0,
    )
    with pytest.raises(CostGateExceeded) as exc_info:
        gate.charge(
            usage=_usage(),
            cost_usd=1.0,
            run_ref="run:1",
            objective_ref="o:1",
            origin="https://x.com",
        )
    assert exc_info.value.failed_cap == "per_run_cost_cap"


def test_charge_rejects_negative_cost() -> None:
    gate = InMemoryCostGate(per_run_cost_cap=1.0)
    with pytest.raises(ValueError, match="non-negative"):
        gate.charge(
            usage=_usage(),
            cost_usd=-0.1,
            run_ref="run:1",
            objective_ref="o:1",
            origin="https://x.com",
        )


def test_charge_rejects_non_finite_cost() -> None:
    gate = InMemoryCostGate(per_run_cost_cap=1.0)
    with pytest.raises(ValueError, match="finite"):
        gate.charge(
            usage=_usage(),
            cost_usd=float("nan"),
            run_ref="run:1",
            objective_ref="o:1",
            origin="https://x.com",
        )


# --- repeated-failure detector ---------------------------------------------


def test_repeated_failure_signature_threshold_2_raises_on_second() -> None:
    gate = InMemoryCostGate(per_run_cost_cap=1.0)
    gate.check(
        run_ref="run:1",
        objective_ref="o:1",
        origin="https://x.com",
        failure_signature="abc123",
    )
    with pytest.raises(RepeatedFailureSignatureExceeded) as exc_info:
        gate.check(
            run_ref="run:1",
            objective_ref="o:1",
            origin="https://x.com",
            failure_signature="abc123",
        )
    assert exc_info.value.recurrence_count == 2


def test_repeated_failure_signature_isolated_per_objective() -> None:
    """Same signature in different objectives doesn't trip the
    counter — recovery is per-objective."""

    gate = InMemoryCostGate(per_run_cost_cap=1.0)
    gate.check(
        run_ref="run:1",
        objective_ref="o:1",
        origin="https://x.com",
        failure_signature="abc123",
    )
    gate.check(  # different objective
        run_ref="run:2",
        objective_ref="o:2",
        origin="https://x.com",
        failure_signature="abc123",
    )


def test_repeated_failure_signature_blank_rejected() -> None:
    gate = InMemoryCostGate(per_run_cost_cap=1.0)
    with pytest.raises(ValueError, match="failure_signature"):
        gate.check(
            run_ref="run:1",
            objective_ref="o:1",
            origin="https://x.com",
            failure_signature="   ",
        )


def test_check_without_failure_signature_does_not_increment_counter() -> None:
    gate = InMemoryCostGate(per_run_cost_cap=1.0)
    for _ in range(10):
        gate.check(
            run_ref="run:1",
            objective_ref="o:1",
            origin="https://x.com",
        )


def test_custom_repeated_failure_threshold() -> None:
    gate = InMemoryCostGate(per_run_cost_cap=1.0, repeated_failure_threshold=3)
    gate.check(
        run_ref="run:1",
        objective_ref="o:1",
        origin="https://x.com",
        failure_signature="abc",
    )
    gate.check(  # second occurrence — under threshold of 3
        run_ref="run:1",
        objective_ref="o:1",
        origin="https://x.com",
        failure_signature="abc",
    )
    with pytest.raises(RepeatedFailureSignatureExceeded):
        gate.check(  # third — trips
            run_ref="run:1",
            objective_ref="o:1",
            origin="https://x.com",
            failure_signature="abc",
        )


# --- exception sanity ------------------------------------------------------


def test_cost_gate_exceeded_rejects_blank_failed_cap() -> None:
    with pytest.raises(ValueError, match="failed_cap"):
        CostGateExceeded(failed_cap="   ", run_ref="r:1")


def test_repeated_failure_signature_exceeded_rejects_low_count() -> None:
    with pytest.raises(ValueError, match="recurrence_count"):
        RepeatedFailureSignatureExceeded(
            failure_signature="abc",
            objective_ref="o:1",
            recurrence_count=1,
        )
