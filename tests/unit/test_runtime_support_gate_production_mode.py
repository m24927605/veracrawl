"""Production-mode regression tests for runtime_support gates.

When ``RuntimeMode.PRODUCTION`` is active, the four runtime_support gate
modules must raise :class:`ProductionRuntimeNotImplemented` instead of
silently returning a fixture-style "runtime_unavailable" report. This
test set holds the contract.

The corresponding fixture-mode behavior is exercised by the
``test_*_gate.py`` modules sitting alongside this one; those tests do
not set ``VERACRAWL_RUNTIME_MODE`` so they continue to run in the
default fixture mode.
"""

from __future__ import annotations

import pytest

from veracrawl.runtime_support.disaster_recovery import (
    dr_restore_plan,
    run_operational_dr_gate,
    run_operational_dr_runtime_unavailable_gate,
)
from veracrawl.runtime_support.infrastructure_gate import (
    run_runtime_infrastructure_gate,
    run_runtime_infrastructure_runtime_unavailable_gate,
    runtime_infrastructure_spec,
)
from veracrawl.runtime_support.observability import (
    run_operational_observability_data_surface_only_gate,
    run_operational_observability_gate,
    run_operational_observability_runtime_unavailable_gate,
)
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    with_runtime_mode,
)
from veracrawl.runtime_support.security_privacy import run_security_privacy_gate


def test_observability_gate_raises_in_production() -> None:
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        with pytest.raises(ProductionRuntimeNotImplemented) as exc:
            run_operational_observability_gate(
                fixture_id="fx-1",
                scenario="ok",
                telemetry_backend_ref=None,
                collector_handoff_ref=None,
            )
    assert exc.value.backend == "observability"
    assert exc.value.gate == "run_operational_observability_gate"


def test_observability_unavailable_gate_raises_in_production() -> None:
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        with pytest.raises(ProductionRuntimeNotImplemented):
            run_operational_observability_runtime_unavailable_gate(fixture_id="fx-2")


def test_observability_data_surface_only_gate_raises_in_production() -> None:
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        with pytest.raises(ProductionRuntimeNotImplemented):
            run_operational_observability_data_surface_only_gate(fixture_id="fx-3")


def test_dr_gate_raises_in_production() -> None:
    plan = dr_restore_plan(
        "fx-4",
        policy_decision_refs=["policy:fx-4:dr"],
        approval_decision_refs=["approval:fx-4:dr"],
    )
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        with pytest.raises(ProductionRuntimeNotImplemented) as exc:
            run_operational_dr_gate(
                fixture_id="fx-4",
                scenario="ok",
                plan=plan,
                runtime_infrastructure_report=None,
            )
    assert exc.value.backend == "disaster_recovery"


def test_dr_unavailable_gate_raises_in_production() -> None:
    plan = dr_restore_plan(
        "fx-5",
        policy_decision_refs=["policy:fx-5:dr"],
        approval_decision_refs=["approval:fx-5:dr"],
    )
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        with pytest.raises(ProductionRuntimeNotImplemented):
            run_operational_dr_runtime_unavailable_gate(fixture_id="fx-5", plan=plan)


def test_dr_restore_plan_does_not_raise_in_production() -> None:
    """Pure data constructor: must remain callable in any runtime mode."""
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        plan = dr_restore_plan(
            "fx-pure",
            policy_decision_refs=["policy:fx-pure:dr"],
            approval_decision_refs=["approval:fx-pure:dr"],
        )
    assert plan.id == "dr-restore-plan:fx-pure"


def test_security_privacy_gate_raises_in_production() -> None:
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        with pytest.raises(ProductionRuntimeNotImplemented) as exc:
            run_security_privacy_gate(fixture_id="fx-6", scenario="ok")
    assert exc.value.backend == "security_privacy"


def test_infrastructure_gate_raises_in_production() -> None:
    spec = runtime_infrastructure_spec(
        "fx-7",
        persistence_adapter_ref="persistence:fx-7",
        queue_broker_adapter_ref="queue:fx-7",
        object_store_adapter_ref="object:fx-7",
        policy_decision_refs=["policy:fx-7:infra"],
    )
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        with pytest.raises(ProductionRuntimeNotImplemented) as exc:
            run_runtime_infrastructure_gate(
                fixture_id="fx-7",
                scenario="ok",
                spec=spec,
                persistence=None,
                queue_broker=None,
                object_store=None,
            )
    assert exc.value.backend == "infrastructure"


def test_infrastructure_unavailable_gate_raises_in_production() -> None:
    spec = runtime_infrastructure_spec(
        "fx-8",
        persistence_adapter_ref="persistence:fx-8",
        queue_broker_adapter_ref="queue:fx-8",
        object_store_adapter_ref="object:fx-8",
        policy_decision_refs=["policy:fx-8:infra"],
    )
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        with pytest.raises(ProductionRuntimeNotImplemented):
            run_runtime_infrastructure_runtime_unavailable_gate(
                fixture_id="fx-8", spec=spec
            )


def test_infrastructure_spec_does_not_raise_in_production() -> None:
    """Pure data constructor: must remain callable in any runtime mode."""
    with with_runtime_mode(RuntimeMode.PRODUCTION):
        spec = runtime_infrastructure_spec(
            "fx-pure",
            persistence_adapter_ref="persistence:fx-pure",
            queue_broker_adapter_ref="queue:fx-pure",
            object_store_adapter_ref="object:fx-pure",
            policy_decision_refs=["policy:fx-pure:infra"],
        )
    assert spec.id == "runtime-infrastructure-spec:fx-pure"


def test_default_mode_does_not_raise() -> None:
    """Belt-and-suspenders: with no env / context, the default is FIXTURE
    and the gates run their normal scenario lookup without raising.
    """
    # No with_runtime_mode wrapper => default FIXTURE.
    result = run_security_privacy_gate(fixture_id="fx-default", scenario="ok")
    assert result.report is not None  # successful fixture-mode call
