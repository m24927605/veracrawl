"""Contract tests for ``veracrawl.contracts.crawl_planner`` (s1).

Implements the s1 plan's red list, section ``tests/contract/
test_crawl_planner_contracts.py``. The s1 plan lives at
``docs/plans/general-purpose-crawler-agentification/
s1-crawl-planner-port-contract.md``.

Every test exercises one declared pydantic validator invariant on
``PlannedSeed`` / ``AdapterPrior`` / ``FrontierPriorityHint`` /
``PlanRequest`` / ``PlanDecision``. The red phase asserts each
validator rejects a deliberately malformed payload; the green
phase implements just enough validator code to make the test
pass. No test mocks the model under test.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.crawl_planner import (
    AdapterPrior,
    FrontierMatchKind,
    FrontierPriorityHint,
    PlanDecision,
    PlannedSeed,
    PlanRequest,
)
from veracrawl.contracts.enums import AdapterType


# ---------------------------------------------------------------------------
# Shared minimal payloads. Each builder returns a dict that constructs a
# *valid* model when expanded, so individual tests can override one field
# to provoke a single named validator.
# ---------------------------------------------------------------------------


def _valid_planned_seed_payload() -> dict[str, object]:
    return {
        "canonical_url": "https://example.com/seed",
        "priority_score": 0.5,
        "adapter_hint": AdapterType.HTTP,
        "rationale_ref": "rationale:test:seed",
    }


def _valid_adapter_prior_payload() -> dict[str, object]:
    return {
        "adapter_type": AdapterType.HTTP,
        "weight": 0.7,
        "rationale_ref": "rationale:test:prior",
    }


def _valid_frontier_priority_hint_payload() -> dict[str, object]:
    return {
        "match_kind": FrontierMatchKind.URL_PREFIX,
        "match_value": "https://example.com/",
        "priority_delta": 0.25,
        "rationale_ref": "rationale:test:hint",
    }


def _valid_plan_request_payload() -> dict[str, object]:
    return {
        "id": "plan-request:test:1",
        "run_ref": "run:test:1",
        "objective_ref": "objective:test:1",
        "seed_urls": ["https://example.com/a"],
        "budget_ref": "budget:test:1",
        "policy_snapshot_ref": "policy-snapshot:test:1",
        "policy_decision_refs": ["policy:test:allow"],
        "replay_config_ref": "replay-config:test:1",
    }


def _valid_plan_decision_payload() -> dict[str, object]:
    request_id = "plan-request:test:1"
    adapter_ref = "adapter:deterministic-crawl-planner:v1"
    return {
        "id": "plan-decision:test:1",
        "request_ref": request_id,
        "planner_adapter_ref": adapter_ref,
        "planned_seeds": [PlannedSeed(**_valid_planned_seed_payload())],
        "adapter_priors": [AdapterPrior(**_valid_adapter_prior_payload())],
        "frontier_priority_hints": [],
        "extraction_strategy_refs": [],
        "replay_refs": [request_id, adapter_ref],
        "policy_decision_refs": ["policy:test:allow"],
    }


# ---------------------------------------------------------------------------
# Test 1 — PlannedSeed validator: canonical_url must be absolute http(s).
# ---------------------------------------------------------------------------


def test_planned_seed_rejects_non_http_url() -> None:
    payload = _valid_planned_seed_payload() | {"canonical_url": "file:///tmp/x"}
    with pytest.raises(ValidationError, match="canonical_url"):
        PlannedSeed(**payload)


# ---------------------------------------------------------------------------
# Test 2 — PlannedSeed validator: priority_score in [0.0, 1.0].
# ---------------------------------------------------------------------------


def test_planned_seed_rejects_priority_out_of_range() -> None:
    payload = _valid_planned_seed_payload() | {"priority_score": 1.5}
    with pytest.raises(ValidationError, match="priority_score"):
        PlannedSeed(**payload)


# ---------------------------------------------------------------------------
# Test 2a — PlannedSeed validator: rationale_ref non-blank. (Iter-4 finding 1.)
# ---------------------------------------------------------------------------


def test_planned_seed_rejects_blank_rationale_ref() -> None:
    payload = _valid_planned_seed_payload() | {"rationale_ref": ""}
    with pytest.raises(ValidationError, match="rationale_ref"):
        PlannedSeed(**payload)


# ---------------------------------------------------------------------------
# Test 3 — AdapterPrior validator: weight in [0.0, 1.0].
# ---------------------------------------------------------------------------


def test_adapter_prior_rejects_weight_out_of_range() -> None:
    payload = _valid_adapter_prior_payload() | {"weight": -0.1}
    with pytest.raises(ValidationError, match="weight"):
        AdapterPrior(**payload)


# ---------------------------------------------------------------------------
# Test 3a — AdapterPrior validator: rationale_ref non-blank. (Iter-4 finding 1.)
# ---------------------------------------------------------------------------


def test_adapter_prior_rejects_blank_rationale_ref() -> None:
    payload = _valid_adapter_prior_payload() | {"rationale_ref": ""}
    with pytest.raises(ValidationError, match="rationale_ref"):
        AdapterPrior(**payload)


# ---------------------------------------------------------------------------
# Test 4 — FrontierPriorityHint validator: priority_delta in [-1.0, 1.0].
# ---------------------------------------------------------------------------


def test_frontier_priority_hint_rejects_delta_out_of_range() -> None:
    payload = _valid_frontier_priority_hint_payload() | {"priority_delta": 2.0}
    with pytest.raises(ValidationError, match="priority_delta"):
        FrontierPriorityHint(**payload)


# ---------------------------------------------------------------------------
# Test 5 — FrontierPriorityHint validator: match_value non-blank.
# ---------------------------------------------------------------------------


def test_frontier_priority_hint_rejects_blank_match_value() -> None:
    payload = _valid_frontier_priority_hint_payload() | {"match_value": ""}
    with pytest.raises(ValidationError, match="match_value"):
        FrontierPriorityHint(**payload)


# ---------------------------------------------------------------------------
# Test 6 — FrontierPriorityHint validator: match_value consistent with kind.
# ---------------------------------------------------------------------------


def test_frontier_priority_hint_rejects_match_value_inconsistent_with_kind() -> None:
    payload = _valid_frontier_priority_hint_payload() | {
        "match_kind": FrontierMatchKind.URL_PREFIX,
        "match_value": "not-a-url",
    }
    with pytest.raises(ValidationError, match="match_value"):
        FrontierPriorityHint(**payload)


# ---------------------------------------------------------------------------
# Test 6a — FrontierPriorityHint validator: rationale_ref non-blank. (Iter-4 finding 1.)
# ---------------------------------------------------------------------------


def test_frontier_priority_hint_rejects_blank_rationale_ref() -> None:
    payload = _valid_frontier_priority_hint_payload() | {"rationale_ref": ""}
    with pytest.raises(ValidationError, match="rationale_ref"):
        FrontierPriorityHint(**payload)


# ---------------------------------------------------------------------------
# Test 7 — PlanRequest validator: seed_urls non-empty.
# ---------------------------------------------------------------------------


def test_plan_request_rejects_empty_seed_urls() -> None:
    payload = _valid_plan_request_payload() | {"seed_urls": []}
    with pytest.raises(ValidationError, match="seed_urls"):
        PlanRequest(**payload)


# ---------------------------------------------------------------------------
# Test 8 — PlanRequest validator: every seed_urls entry is http(s).
# ---------------------------------------------------------------------------


def test_plan_request_rejects_non_http_seed_url() -> None:
    payload = _valid_plan_request_payload() | {"seed_urls": ["file:///tmp"]}
    with pytest.raises(ValidationError, match="seed_urls"):
        PlanRequest(**payload)


# ---------------------------------------------------------------------------
# Test 9 — PlanRequest validator: seed_urls duplicates rejected.
# ---------------------------------------------------------------------------


def test_plan_request_rejects_duplicate_seed_urls() -> None:
    payload = _valid_plan_request_payload() | {
        "seed_urls": ["https://a.example", "https://a.example"],
    }
    with pytest.raises(ValidationError, match="duplicate"):
        PlanRequest(**payload)


# ---------------------------------------------------------------------------
# Test 10 — PlanRequest validator: objective_ref non-blank.
# ---------------------------------------------------------------------------


def test_plan_request_rejects_blank_objective_ref() -> None:
    payload = _valid_plan_request_payload() | {"objective_ref": ""}
    with pytest.raises(ValidationError, match="objective_ref"):
        PlanRequest(**payload)


# ---------------------------------------------------------------------------
# Test 10a — PlanRequest validator: policy_decision_refs non-empty. (Iter-2 finding 1.)
# ---------------------------------------------------------------------------


def test_plan_request_rejects_empty_policy_decision_refs() -> None:
    payload = _valid_plan_request_payload() | {"policy_decision_refs": []}
    with pytest.raises(ValidationError, match="policy_decision_refs"):
        PlanRequest(**payload)


# ---------------------------------------------------------------------------
# Tests 10b–10f — PlanRequest validator: every scalar ref non-blank. (Iter-4 finding 1.)
# Discrete tests rather than parametrized so the count is unambiguous against
# the s1 plan's Acceptance Criterion 1.
# ---------------------------------------------------------------------------


def test_plan_request_rejects_blank_id() -> None:
    payload = _valid_plan_request_payload() | {"id": ""}
    with pytest.raises(ValidationError, match="id"):
        PlanRequest(**payload)


def test_plan_request_rejects_blank_run_ref() -> None:
    payload = _valid_plan_request_payload() | {"run_ref": ""}
    with pytest.raises(ValidationError, match="run_ref"):
        PlanRequest(**payload)


def test_plan_request_rejects_blank_budget_ref() -> None:
    payload = _valid_plan_request_payload() | {"budget_ref": ""}
    with pytest.raises(ValidationError, match="budget_ref"):
        PlanRequest(**payload)


def test_plan_request_rejects_blank_policy_snapshot_ref() -> None:
    payload = _valid_plan_request_payload() | {"policy_snapshot_ref": ""}
    with pytest.raises(ValidationError, match="policy_snapshot_ref"):
        PlanRequest(**payload)


def test_plan_request_rejects_blank_replay_config_ref() -> None:
    payload = _valid_plan_request_payload() | {"replay_config_ref": ""}
    with pytest.raises(ValidationError, match="replay_config_ref"):
        PlanRequest(**payload)


# ---------------------------------------------------------------------------
# Test 11 — PlanDecision validator: planned_seeds non-empty.
# ---------------------------------------------------------------------------


def test_plan_decision_rejects_empty_planned_seeds() -> None:
    payload = _valid_plan_decision_payload() | {"planned_seeds": []}
    with pytest.raises(ValidationError, match="planned_seeds"):
        PlanDecision(**payload)


# ---------------------------------------------------------------------------
# Test 12 — PlanDecision validator: adapter_priors non-empty.
# ---------------------------------------------------------------------------


def test_plan_decision_rejects_empty_adapter_priors() -> None:
    payload = _valid_plan_decision_payload() | {"adapter_priors": []}
    with pytest.raises(ValidationError, match="adapter_priors"):
        PlanDecision(**payload)


# ---------------------------------------------------------------------------
# Test 13 — PlanDecision validator: adapter_priors adapter_type values unique.
# ---------------------------------------------------------------------------


def test_plan_decision_rejects_duplicate_adapter_types() -> None:
    duplicate = [
        AdapterPrior(
            adapter_type=AdapterType.HTTP,
            weight=0.5,
            rationale_ref="rationale:test:a",
        ),
        AdapterPrior(
            adapter_type=AdapterType.HTTP,
            weight=0.4,
            rationale_ref="rationale:test:b",
        ),
    ]
    payload = _valid_plan_decision_payload() | {"adapter_priors": duplicate}
    with pytest.raises(ValidationError, match="adapter_priors"):
        PlanDecision(**payload)


# ---------------------------------------------------------------------------
# Test 14 — PlanDecision validator: adapter_priors weight sum ≤ 1.0 + 1e-9.
# ---------------------------------------------------------------------------


def test_plan_decision_rejects_adapter_priors_sum_above_one() -> None:
    over_one = [
        AdapterPrior(
            adapter_type=AdapterType.HTTP,
            weight=0.5,
            rationale_ref="rationale:test:a",
        ),
        AdapterPrior(
            adapter_type=AdapterType.SITEMAP,
            weight=0.5,
            rationale_ref="rationale:test:b",
        ),
        AdapterPrior(
            adapter_type=AdapterType.RSS,
            weight=0.5,
            rationale_ref="rationale:test:c",
        ),
    ]
    payload = _valid_plan_decision_payload() | {"adapter_priors": over_one}
    with pytest.raises(ValidationError, match="sum"):
        PlanDecision(**payload)


# ---------------------------------------------------------------------------
# Test 14a — PlanDecision validator: request_ref non-blank. (Iter-4 finding 1.)
# ---------------------------------------------------------------------------


def test_plan_decision_rejects_blank_request_ref() -> None:
    payload = _valid_plan_decision_payload() | {
        "request_ref": "",
        "replay_refs": ["adapter:deterministic-crawl-planner:v1"],
    }
    with pytest.raises(ValidationError, match="request_ref"):
        PlanDecision(**payload)


# ---------------------------------------------------------------------------
# Test 14b — PlanDecision validator: planner_adapter_ref non-blank. (Iter-4 finding 1.)
# ---------------------------------------------------------------------------


def test_plan_decision_rejects_blank_planner_adapter_ref() -> None:
    payload = _valid_plan_decision_payload() | {
        "planner_adapter_ref": "",
        "replay_refs": ["plan-request:test:1"],
    }
    with pytest.raises(ValidationError, match="planner_adapter_ref"):
        PlanDecision(**payload)


# ---------------------------------------------------------------------------
# Test 15 — PlanDecision validator: request_ref appears in replay_refs. (Iter-1 finding 2.)
# ---------------------------------------------------------------------------


def test_plan_decision_rejects_missing_request_ref_in_replay_refs() -> None:
    payload = _valid_plan_decision_payload() | {
        "replay_refs": ["adapter:deterministic-crawl-planner:v1"],
    }
    with pytest.raises(ValidationError, match="request_ref"):
        PlanDecision(**payload)


# ---------------------------------------------------------------------------
# Test 16 — PlanDecision validator: planner_adapter_ref appears in replay_refs. (Iter-1 finding 2.)
# ---------------------------------------------------------------------------


def test_plan_decision_rejects_missing_planner_adapter_ref_in_replay_refs() -> None:
    payload = _valid_plan_decision_payload() | {
        "replay_refs": ["plan-request:test:1"],
    }
    with pytest.raises(ValidationError, match="planner_adapter_ref"):
        PlanDecision(**payload)


# ---------------------------------------------------------------------------
# Test 17 — PlanDecision validator: policy_decision_refs non-empty.
# ---------------------------------------------------------------------------


def test_plan_decision_rejects_empty_policy_decision_refs() -> None:
    payload = _valid_plan_decision_payload() | {"policy_decision_refs": []}
    with pytest.raises(ValidationError, match="policy_decision_refs"):
        PlanDecision(**payload)
