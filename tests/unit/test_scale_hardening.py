from __future__ import annotations

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.scale.hardening import run_scale_hardening


def test_scale_success_scenarios_emit_replayable_refs() -> None:
    for scenario in [
        "scale-sharding-success",
        "backpressure-autoscale-success",
        "dead-letter-recovery-success",
    ]:
        result = run_scale_hardening(
            fixture_id=f"unit-{scenario}",
            scenario=scenario,
            policy_decision_refs=["policy:unit:scale"],
        )
        assert result.report.completion_result == CompletenessResult.PASS
        assert result.topology is not None
        assert result.queue_items
        assert result.shard_leases
        assert result.backpressure_signals
        assert result.autoscaling_decisions
        assert result.dead_letter_records


def test_scale_negative_scenarios_emit_failures() -> None:
    expectations = {
        "stale-lease-without-recovery": "stale_lease_without_recovery",
        "unfair-site-starvation": "unfair_site_starvation",
        "autoscale-without-policy": "autoscale_without_policy",
        "dead-letter-missing-failure-record": "dead_letter_missing_failure_record",
        "replay-missing-scale-refs": "replay_missing_scale_refs",
    }
    for scenario, operator_status in expectations.items():
        result = run_scale_hardening(
            fixture_id=f"unit-{scenario}",
            scenario=scenario,
            policy_decision_refs=["policy:unit:scale"],
        )
        assert result.report.completion_result == CompletenessResult.FAIL
        assert result.report.operator_status == operator_status
        assert result.report.missing_ref_fields
