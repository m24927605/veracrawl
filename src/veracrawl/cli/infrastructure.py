"""Operational runtime infrastructure fixture runner CLI."""

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

from veracrawl.artifact_lifecycle.object_store_conformance import (
    OperationalObjectStoreAdapter,
    run_object_store_conformance,
)
from veracrawl.contracts.artifact import ObjectStoreAdapterSpec
from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    RuntimeInfrastructureAdapterFamily,
)
from veracrawl.contracts.infrastructure import (
    RuntimeInfrastructureFixtureManifest,
    RuntimeInfrastructureSpec,
)
from veracrawl.contracts.persistence import PersistenceAdapterSpec
from veracrawl.contracts.scale import QueueBrokerAdapterSpec
from veracrawl.persistence.adapter_conformance import (
    OperationalPersistenceAdapter,
    run_postgres_adapter_conformance,
)
from veracrawl.runtime_support.infrastructure_gate import (
    RuntimeInfrastructureGateResult,
    run_runtime_infrastructure_gate,
    run_runtime_infrastructure_runtime_unavailable_gate,
    runtime_infrastructure_spec,
)
from veracrawl.runtime_support.logging import bootstrap_cli_logging
from veracrawl.scale.broker_conformance import (
    OperationalQueueBrokerAdapter,
    run_queue_broker_conformance,
)


class RuntimeInfrastructureFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    completion_result: CompletenessResult
    operator_status: str
    infrastructure_spec_ref: Ref | None = None
    live_adapter_families: list[RuntimeInfrastructureAdapterFamily] = Field(default_factory=list)
    persistence_report_refs: list[Ref] = Field(default_factory=list)
    queue_broker_report_refs: list[Ref] = Field(default_factory=list)
    object_store_report_refs: list[Ref] = Field(default_factory=list)
    persistence_adapter_refs: list[Ref] = Field(default_factory=list)
    queue_broker_adapter_refs: list[Ref] = Field(default_factory=list)
    object_store_adapter_refs: list[Ref] = Field(default_factory=list)
    transaction_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    idempotency_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    queue_topology_refs: list[Ref] = Field(default_factory=list)
    queue_item_refs: list[Ref] = Field(default_factory=list)
    broker_operation_refs: list[Ref] = Field(default_factory=list)
    queue_operation_refs: list[Ref] = Field(default_factory=list)
    lease_refs: list[Ref] = Field(default_factory=list)
    heartbeat_refs: list[Ref] = Field(default_factory=list)
    ack_refs: list[Ref] = Field(default_factory=list)
    nack_refs: list[Ref] = Field(default_factory=list)
    dead_letter_refs: list[Ref] = Field(default_factory=list)
    fencing_token_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    object_operation_refs: list[Ref] = Field(default_factory=list)
    content_digest_refs: list[Ref] = Field(default_factory=list)
    read_result_refs: list[Ref] = Field(default_factory=list)
    head_refs: list[Ref] = Field(default_factory=list)
    list_refs: list[Ref] = Field(default_factory=list)
    delete_refs: list[Ref] = Field(default_factory=list)
    lifecycle_state_refs: list[Ref] = Field(default_factory=list)
    retention_policy_refs: list[Ref] = Field(default_factory=list)
    privacy_policy_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    contract_only_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    missing_ref_fields: list[str] = Field(default_factory=list)
    idempotency_deduped: bool = False


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_module(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


def _postgres_adapter_spec(fixture_id: str, policy_refs: list[Ref]) -> PersistenceAdapterSpec:
    module = _load_module("veracrawl.adapters.persistence.postgres")
    spec_builder = cast(
        Callable[[str, list[Ref]], PersistenceAdapterSpec],
        module.__dict__["postgres_adapter_spec"],
    )
    return spec_builder(fixture_id, policy_refs)


def _postgres_adapter(
    fixture_id: str,
    policy_refs: list[Ref],
    dsn: str,
) -> tuple[OperationalPersistenceAdapter, PersistenceAdapterSpec]:
    module = _load_module("veracrawl.adapters.persistence.postgres")
    adapter_factory = cast(
        Callable[[str], OperationalPersistenceAdapter],
        module.__dict__["PostgresPersistenceAdapter"],
    )
    return adapter_factory(dsn), _postgres_adapter_spec(fixture_id, policy_refs)


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


def _redis_adapter(
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


def _s3_adapter_spec(
    fixture_id: str,
    policy_refs: list[Ref],
    retention_refs: list[Ref],
    privacy_refs: list[Ref],
) -> ObjectStoreAdapterSpec:
    module = _load_module("veracrawl.adapters.object_stores.s3")
    spec_builder = cast(
        Callable[..., ObjectStoreAdapterSpec],
        module.__dict__["s3_object_store_adapter_spec"],
    )
    return spec_builder(
        fixture_id,
        policy_refs,
        retention_refs=retention_refs,
        privacy_refs=privacy_refs,
    )


def _s3_adapter(
    fixture_id: str,
    policy_refs: list[Ref],
    retention_refs: list[Ref],
    privacy_refs: list[Ref],
    *,
    endpoint_url: str,
    bucket: str,
    access_key_id: str,
    secret_access_key: str,
) -> tuple[OperationalObjectStoreAdapter, ObjectStoreAdapterSpec]:
    module = _load_module("veracrawl.adapters.object_stores.s3")
    adapter_factory = cast(Callable[..., object], module.__dict__["S3ObjectStoreAdapter"])
    adapter = adapter_factory(
        endpoint_url,
        bucket=bucket,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
        namespace=f"veracrawl-{fixture_id}",
    )
    return (
        cast(OperationalObjectStoreAdapter, adapter),
        _s3_adapter_spec(fixture_id, policy_refs, retention_refs, privacy_refs),
    )


def _spec_for_manifest(
    manifest: RuntimeInfrastructureFixtureManifest,
    policy_refs: list[Ref],
    fairness_refs: list[Ref],
    backpressure_refs: list[Ref],
    retention_refs: list[Ref],
    privacy_refs: list[Ref],
) -> RuntimeInfrastructureSpec:
    persistence_spec = _postgres_adapter_spec(manifest.id, policy_refs)
    queue_spec = _redis_adapter_spec(manifest.id, policy_refs, fairness_refs, backpressure_refs)
    object_spec = _s3_adapter_spec(manifest.id, policy_refs, retention_refs, privacy_refs)
    return runtime_infrastructure_spec(
        manifest.id,
        persistence_adapter_ref=persistence_spec.id,
        queue_broker_adapter_ref=queue_spec.id,
        object_store_adapter_ref=object_spec.id,
        policy_decision_refs=policy_refs,
    )


def run_runtime_infrastructure_fixture(
    manifest: RuntimeInfrastructureFixtureManifest,
    *,
    profile: str,
    postgres_dsn: str | None = None,
    redis_url: str | None = None,
    s3_endpoint_url: str | None = None,
    s3_bucket: str | None = None,
    s3_access_key_id: str | None = None,
    s3_secret_access_key: str | None = None,
) -> RuntimeInfrastructureFixtureRunReport:
    policy_refs = [f"policy:{manifest.id}:runtime-infrastructure"]
    fairness_refs = [f"fairness-scope:{manifest.id}:site"]
    backpressure_refs = [f"backpressure-signal:{manifest.id}:lag"]
    retention_refs = [f"retention-policy:{manifest.id}:artifacts"]
    privacy_refs = [f"privacy-policy:{manifest.id}:artifacts"]
    spec = _spec_for_manifest(
        manifest,
        policy_refs,
        fairness_refs,
        backpressure_refs,
        retention_refs,
        privacy_refs,
    )
    if manifest.scenario == "operational-infrastructure-runtime-unavailable":
        result = run_runtime_infrastructure_runtime_unavailable_gate(
            fixture_id=manifest.id,
            spec=spec,
        )
    elif manifest.scenario.startswith("infrastructure-missing-"):
        result = run_runtime_infrastructure_gate(
            fixture_id=manifest.id,
            scenario=manifest.scenario,
            spec=spec,
            persistence=None,
            queue_broker=None,
            object_store=None,
        )
    elif manifest.scenario.startswith("operational-infrastructure-"):
        result = _run_live_gate(
            manifest,
            spec=spec,
            policy_refs=policy_refs,
            fairness_refs=fairness_refs,
            backpressure_refs=backpressure_refs,
            retention_refs=retention_refs,
            privacy_refs=privacy_refs,
            postgres_dsn=postgres_dsn,
            redis_url=redis_url,
            s3_endpoint_url=s3_endpoint_url,
            s3_bucket=s3_bucket,
            s3_access_key_id=s3_access_key_id,
            s3_secret_access_key=s3_secret_access_key,
        )
    else:
        raise ValueError(f"unsupported runtime infrastructure scenario: {manifest.scenario}")
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _run_live_gate(
    manifest: RuntimeInfrastructureFixtureManifest,
    *,
    spec: RuntimeInfrastructureSpec,
    policy_refs: list[Ref],
    fairness_refs: list[Ref],
    backpressure_refs: list[Ref],
    retention_refs: list[Ref],
    privacy_refs: list[Ref],
    postgres_dsn: str | None,
    redis_url: str | None,
    s3_endpoint_url: str | None,
    s3_bucket: str | None,
    s3_access_key_id: str | None,
    s3_secret_access_key: str | None,
) -> RuntimeInfrastructureGateResult:
    resolved_dsn = postgres_dsn or os.getenv("VERACRAWL_POSTGRES_DSN")
    resolved_redis_url = redis_url or os.getenv("VERACRAWL_REDIS_URL")
    resolved_s3_endpoint = s3_endpoint_url or os.getenv("VERACRAWL_S3_ENDPOINT_URL")
    resolved_s3_bucket = s3_bucket or os.getenv("VERACRAWL_S3_BUCKET")
    resolved_s3_access = s3_access_key_id or os.getenv("VERACRAWL_S3_ACCESS_KEY_ID")
    resolved_s3_secret = s3_secret_access_key or os.getenv("VERACRAWL_S3_SECRET_ACCESS_KEY")
    if not all(
        [
            resolved_dsn,
            resolved_redis_url,
            resolved_s3_endpoint,
            resolved_s3_bucket,
            resolved_s3_access,
            resolved_s3_secret,
        ]
    ):
        raise ValueError(
            f"fixture {manifest.id} requires Postgres DSN, Redis URL, "
            "S3 endpoint, bucket, access key, and secret"
        )
    persistence_store, persistence_spec = _postgres_adapter(
        manifest.id,
        policy_refs,
        str(resolved_dsn),
    )
    queue_broker, queue_spec = _redis_adapter(
        manifest.id,
        policy_refs,
        fairness_refs,
        backpressure_refs,
        str(resolved_redis_url),
    )
    object_store, object_spec = _s3_adapter(
        manifest.id,
        policy_refs,
        retention_refs,
        privacy_refs,
        endpoint_url=str(resolved_s3_endpoint),
        bucket=str(resolved_s3_bucket),
        access_key_id=str(resolved_s3_access),
        secret_access_key=str(resolved_s3_secret),
    )
    scenarios = _component_scenarios(manifest.scenario)
    persistence_result = run_postgres_adapter_conformance(
        fixture_id=manifest.id,
        scenario=scenarios[0],
        store=persistence_store,
        adapter_spec=persistence_spec,
        policy_decision_refs=policy_refs,
    )
    queue_result = run_queue_broker_conformance(
        fixture_id=manifest.id,
        scenario=scenarios[1],
        broker=queue_broker,
        adapter_spec=queue_spec,
    )
    object_result = run_object_store_conformance(
        fixture_id=manifest.id,
        scenario=scenarios[2],
        store=object_store,
        adapter_spec=object_spec,
    )
    return run_runtime_infrastructure_gate(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        spec=runtime_infrastructure_spec(
            manifest.id,
            persistence_adapter_ref=persistence_spec.id,
            queue_broker_adapter_ref=queue_spec.id,
            object_store_adapter_ref=object_spec.id,
            policy_decision_refs=policy_refs,
        ),
        persistence=persistence_result,
        queue_broker=queue_result,
        object_store=object_result,
    )


def _component_scenarios(scenario: str) -> tuple[str, str, str]:
    if scenario == "operational-infrastructure-idempotency-success":
        return (
            "postgres-reopen-idempotency-success",
            "redis-broker-idempotency-success",
            "s3-object-store-idempotency-success",
        )
    return (
        "postgres-adapter-conformance-success",
        "redis-broker-conformance-success",
        "s3-object-store-conformance-success",
    )


def _to_run_report(
    *,
    manifest: RuntimeInfrastructureFixtureManifest,
    profile: str,
    result: RuntimeInfrastructureGateResult,
) -> RuntimeInfrastructureFixtureRunReport:
    report = result.report
    return RuntimeInfrastructureFixtureRunReport(
        id=f"runtime-infrastructure-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        infrastructure_spec_ref=report.infrastructure_spec_ref,
        live_adapter_families=report.live_adapter_families,
        persistence_report_refs=report.persistence_report_refs,
        queue_broker_report_refs=report.queue_broker_report_refs,
        object_store_report_refs=report.object_store_report_refs,
        persistence_adapter_refs=report.persistence_adapter_refs,
        queue_broker_adapter_refs=report.queue_broker_adapter_refs,
        object_store_adapter_refs=report.object_store_adapter_refs,
        transaction_refs=report.transaction_refs,
        command_record_refs=report.command_record_refs,
        idempotency_record_refs=report.idempotency_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        queue_topology_refs=report.queue_topology_refs,
        queue_item_refs=report.queue_item_refs,
        broker_operation_refs=report.broker_operation_refs,
        queue_operation_refs=report.queue_operation_refs,
        lease_refs=report.lease_refs,
        heartbeat_refs=report.heartbeat_refs,
        ack_refs=report.ack_refs,
        nack_refs=report.nack_refs,
        dead_letter_refs=report.dead_letter_refs,
        fencing_token_refs=report.fencing_token_refs,
        artifact_refs=report.artifact_refs,
        object_operation_refs=report.object_operation_refs,
        content_digest_refs=report.content_digest_refs,
        read_result_refs=report.read_result_refs,
        head_refs=report.head_refs,
        list_refs=report.list_refs,
        delete_refs=report.delete_refs,
        lifecycle_state_refs=report.lifecycle_state_refs,
        retention_policy_refs=report.retention_policy_refs,
        privacy_policy_refs=report.privacy_policy_refs,
        failure_record_refs=report.failure_record_refs,
        recovery_action_refs=report.recovery_action_refs,
        policy_decision_refs=report.policy_decision_refs,
        contract_only_refs=report.contract_only_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        missing_ref_fields=report.missing_ref_fields,
        idempotency_deduped=report.idempotency_deduped,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
    postgres_dsn: str | None = None,
    redis_url: str | None = None,
    s3_endpoint_url: str | None = None,
    s3_bucket: str | None = None,
    s3_access_key_id: str | None = None,
    s3_secret_access_key: str | None = None,
) -> RuntimeInfrastructureFixtureRunReport:
    manifest = RuntimeInfrastructureFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_runtime_infrastructure_fixture(
        manifest,
        profile=profile,
        postgres_dsn=postgres_dsn,
        redis_url=redis_url,
        s3_endpoint_url=s3_endpoint_url,
        s3_bucket=s3_bucket,
        s3_access_key_id=s3_access_key_id,
        s3_secret_access_key=s3_secret_access_key,
    )
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
    parser = argparse.ArgumentParser(prog="veracrawl-infrastructure")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--postgres-dsn")
    run.add_argument("--redis-url")
    run.add_argument("--s3-endpoint-url")
    run.add_argument("--s3-bucket")
    run.add_argument("--s3-access-key-id")
    run.add_argument("--s3-secret-access-key")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-infrastructure"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run":
            try:
                report = run_fixture(
                    Path(args.fixture_dir),
                    profile=args.profile,
                    out=Path(args.out),
                    postgres_dsn=args.postgres_dsn,
                    redis_url=args.redis_url,
                    s3_endpoint_url=args.s3_endpoint_url,
                    s3_bucket=args.s3_bucket,
                    s3_access_key_id=args.s3_access_key_id,
                    s3_secret_access_key=args.s3_secret_access_key,
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
                        "idempotency_deduped": report.idempotency_deduped,
                        "live_adapter_families": [
                            family.value for family in report.live_adapter_families
                        ],
                    },
                    sort_keys=True,
                )
            )
            return 0
        return 2


if __name__ == "__main__":
    sys.exit(main())
