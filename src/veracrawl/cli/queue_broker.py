"""Queue broker conformance fixture runner CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult, QueueBrokerAdapterKind
from veracrawl.contracts.scale import QueueBrokerAdapterSpec, QueueBrokerFixtureManifest
from veracrawl.scale.broker_conformance import (
    OperationalQueueBrokerAdapter,
    QueueBrokerConformanceResult,
    run_queue_broker_conformance,
    run_queue_broker_runtime_unavailable_conformance,
)


class QueueBrokerFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    completion_result: CompletenessResult
    operator_status: str
    adapter_ref: Ref | None = None
    adapter_kind: QueueBrokerAdapterKind | None = None
    queue_topology_ref: Ref | None = None
    queue_item_refs: list[Ref] = Field(default_factory=list)
    broker_operation_refs: list[Ref] = Field(default_factory=list)
    lease_refs: list[Ref] = Field(default_factory=list)
    heartbeat_refs: list[Ref] = Field(default_factory=list)
    ack_refs: list[Ref] = Field(default_factory=list)
    nack_refs: list[Ref] = Field(default_factory=list)
    dead_letter_refs: list[Ref] = Field(default_factory=list)
    fencing_token_refs: list[Ref] = Field(default_factory=list)
    retry_refs: list[Ref] = Field(default_factory=list)
    fairness_scope_refs: list[Ref] = Field(default_factory=list)
    backpressure_signal_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    contract_only_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    missing_ref_fields: list[str] = Field(default_factory=list)
    duplicate_deduped: bool = False
    queued_count: int = 0
    dead_letter_count: int = 0


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_module(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


def _redis_adapter_spec(
    fixture_id: str,
    policy_refs: list[Ref],
    fairness_refs: list[Ref],
    backpressure_refs: list[Ref],
) -> QueueBrokerAdapterSpec:
    module = _load_module("veracrawl.adapters.queue_brokers.redis")
    spec_builder = cast(
        Callable[..., QueueBrokerAdapterSpec],
        module.__dict__["redis_queue_broker_adapter_spec"],
    )
    return spec_builder(
        fixture_id,
        policy_refs,
        fairness_refs=fairness_refs,
        backpressure_refs=backpressure_refs,
    )


def _operational_redis_adapter(
    fixture_id: str,
    policy_refs: list[Ref],
    fairness_refs: list[Ref],
    backpressure_refs: list[Ref],
    redis_url: str,
) -> tuple[OperationalQueueBrokerAdapter, QueueBrokerAdapterSpec]:
    module = _load_module("veracrawl.adapters.queue_brokers.redis")
    adapter_factory = cast(Callable[..., object], module.__dict__["RedisQueueBrokerAdapter"])
    adapter = adapter_factory(redis_url, namespace=f"veracrawl-{fixture_id}")
    reset_namespace = getattr(adapter, "reset_namespace", None)
    if callable(reset_namespace):
        reset_namespace()
    return (
        cast(OperationalQueueBrokerAdapter, adapter),
        _redis_adapter_spec(fixture_id, policy_refs, fairness_refs, backpressure_refs),
    )


def run_queue_broker_fixture(
    manifest: QueueBrokerFixtureManifest,
    *,
    profile: str,
    redis_url: str | None = None,
) -> QueueBrokerFixtureRunReport:
    policy_refs = [f"policy:{manifest.id}:queue-broker"]
    fairness_refs = [f"fairness-scope:{manifest.id}:site"]
    backpressure_refs = [f"backpressure-signal:{manifest.id}:lag"]
    adapter_spec = _redis_adapter_spec(manifest.id, policy_refs, fairness_refs, backpressure_refs)
    if manifest.scenario == "redis-broker-runtime-unavailable":
        result = run_queue_broker_runtime_unavailable_conformance(
            fixture_id=manifest.id,
            adapter_spec=adapter_spec,
        )
    elif manifest.scenario.startswith("broker-missing-"):
        result = run_queue_broker_conformance(
            fixture_id=manifest.id,
            scenario=manifest.scenario,
            broker=None,
            adapter_spec=adapter_spec,
        )
    elif manifest.scenario.startswith("redis-broker-"):
        resolved_url = redis_url or os.getenv("VERACRAWL_REDIS_URL")
        if not resolved_url:
            raise ValueError(
                f"fixture {manifest.id} requires --redis-url or VERACRAWL_REDIS_URL"
            )
        adapter, adapter_spec = _operational_redis_adapter(
            manifest.id,
            policy_refs,
            fairness_refs,
            backpressure_refs,
            resolved_url,
        )
        result = run_queue_broker_conformance(
            fixture_id=manifest.id,
            scenario=manifest.scenario,
            broker=adapter,
            adapter_spec=adapter_spec,
        )
    else:
        raise ValueError(f"unsupported queue broker scenario: {manifest.scenario}")
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: QueueBrokerFixtureManifest,
    profile: str,
    result: QueueBrokerConformanceResult,
) -> QueueBrokerFixtureRunReport:
    report = result.report
    return QueueBrokerFixtureRunReport(
        id=f"queue-broker-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        adapter_ref=report.adapter_ref,
        adapter_kind=report.adapter_kind,
        queue_topology_ref=report.queue_topology_ref,
        queue_item_refs=report.queue_item_refs,
        broker_operation_refs=report.broker_operation_refs,
        lease_refs=report.lease_refs,
        heartbeat_refs=report.heartbeat_refs,
        ack_refs=report.ack_refs,
        nack_refs=report.nack_refs,
        dead_letter_refs=report.dead_letter_refs,
        fencing_token_refs=report.fencing_token_refs,
        retry_refs=report.retry_refs,
        fairness_scope_refs=report.fairness_scope_refs,
        backpressure_signal_refs=report.backpressure_signal_refs,
        failure_record_refs=report.failure_record_refs,
        recovery_action_refs=report.recovery_action_refs,
        policy_decision_refs=report.policy_decision_refs,
        contract_only_refs=report.contract_only_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        missing_ref_fields=report.missing_ref_fields,
        duplicate_deduped=result.duplicate_deduped,
        queued_count=result.queued_count,
        dead_letter_count=result.dead_letter_count,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
    redis_url: str | None = None,
) -> QueueBrokerFixtureRunReport:
    manifest = QueueBrokerFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_queue_broker_fixture(manifest, profile=profile, redis_url=redis_url)
    if report.completion_result.value != manifest.expected_completion_result:
        raise ValueError(f"fixture {manifest.id} completion mismatch: {report.completion_result}")
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    if (
        manifest.expected_failure_type is not None
        and report.operator_status != manifest.expected_failure_type.value
    ):
        raise ValueError(f"fixture {manifest.id} failure mismatch: {report.operator_status}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-queue-broker")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--redis-url")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        try:
            report = run_fixture(
                Path(args.fixture_dir),
                profile=args.profile,
                out=Path(args.out),
                redis_url=args.redis_url,
            )
        except (AttributeError, ImportError, OSError, RuntimeError, ValueError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
            return 1
        print(
            json.dumps(
                {
                    "ok": True,
                    "fixture_id": report.fixture_id,
                    "completion_result": report.completion_result.value,
                    "operator_status": report.operator_status,
                    "duplicate_deduped": report.duplicate_deduped,
                    "queued_count": report.queued_count,
                    "dead_letter_count": report.dead_letter_count,
                },
                sort_keys=True,
            )
        )
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
