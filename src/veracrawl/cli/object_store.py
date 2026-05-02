"""Object store conformance fixture runner CLI."""

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
    ObjectStoreConformanceResult,
    OperationalObjectStoreAdapter,
    run_object_store_conformance,
    run_object_store_runtime_unavailable_conformance,
)
from veracrawl.contracts.artifact import ObjectStoreAdapterSpec, ObjectStoreFixtureManifest
from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult, ObjectStoreAdapterKind


class ObjectStoreFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    completion_result: CompletenessResult
    operator_status: str
    adapter_ref: Ref | None = None
    adapter_kind: ObjectStoreAdapterKind | None = None
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
    duplicate_deduped: bool = False
    object_count: int = 0
    read_content: str | None = None


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_module(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


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


def _operational_s3_adapter(
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


def run_object_store_fixture(
    manifest: ObjectStoreFixtureManifest,
    *,
    profile: str,
    endpoint_url: str | None = None,
    bucket: str | None = None,
    access_key_id: str | None = None,
    secret_access_key: str | None = None,
) -> ObjectStoreFixtureRunReport:
    policy_refs = [f"policy:{manifest.id}:object-store"]
    retention_refs = [f"retention-policy:{manifest.id}:artifacts"]
    privacy_refs = [f"privacy-policy:{manifest.id}:artifacts"]
    adapter_spec = _s3_adapter_spec(manifest.id, policy_refs, retention_refs, privacy_refs)
    if manifest.scenario == "s3-object-store-runtime-unavailable":
        result = run_object_store_runtime_unavailable_conformance(
            fixture_id=manifest.id,
            adapter_spec=adapter_spec,
        )
    elif manifest.scenario.startswith("object-store-missing-"):
        result = run_object_store_conformance(
            fixture_id=manifest.id,
            scenario=manifest.scenario,
            store=None,
            adapter_spec=adapter_spec,
        )
    elif manifest.scenario.startswith("s3-object-store-"):
        resolved_endpoint = endpoint_url or os.getenv("VERACRAWL_S3_ENDPOINT_URL")
        resolved_bucket = bucket or os.getenv("VERACRAWL_S3_BUCKET")
        resolved_access_key = access_key_id or os.getenv("VERACRAWL_S3_ACCESS_KEY_ID")
        resolved_secret_key = secret_access_key or os.getenv("VERACRAWL_S3_SECRET_ACCESS_KEY")
        if not all([resolved_endpoint, resolved_bucket, resolved_access_key, resolved_secret_key]):
            raise ValueError(
                f"fixture {manifest.id} requires S3 endpoint, bucket, access key, and secret"
            )
        adapter, adapter_spec = _operational_s3_adapter(
            manifest.id,
            policy_refs,
            retention_refs,
            privacy_refs,
            endpoint_url=str(resolved_endpoint),
            bucket=str(resolved_bucket),
            access_key_id=str(resolved_access_key),
            secret_access_key=str(resolved_secret_key),
        )
        result = run_object_store_conformance(
            fixture_id=manifest.id,
            scenario=manifest.scenario,
            store=adapter,
            adapter_spec=adapter_spec,
        )
    else:
        raise ValueError(f"unsupported object store scenario: {manifest.scenario}")
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: ObjectStoreFixtureManifest,
    profile: str,
    result: ObjectStoreConformanceResult,
) -> ObjectStoreFixtureRunReport:
    report = result.report
    return ObjectStoreFixtureRunReport(
        id=f"object-store-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        adapter_ref=report.adapter_ref,
        adapter_kind=report.adapter_kind,
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
        duplicate_deduped=result.duplicate_deduped,
        object_count=result.object_count,
        read_content=result.read_content,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
    endpoint_url: str | None = None,
    bucket: str | None = None,
    access_key_id: str | None = None,
    secret_access_key: str | None = None,
) -> ObjectStoreFixtureRunReport:
    manifest = ObjectStoreFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_object_store_fixture(
        manifest,
        profile=profile,
        endpoint_url=endpoint_url,
        bucket=bucket,
        access_key_id=access_key_id,
        secret_access_key=secret_access_key,
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
    parser = argparse.ArgumentParser(prog="veracrawl-object-store")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--endpoint-url")
    run.add_argument("--bucket")
    run.add_argument("--access-key-id")
    run.add_argument("--secret-access-key")
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
                endpoint_url=args.endpoint_url,
                bucket=args.bucket,
                access_key_id=args.access_key_id,
                secret_access_key=args.secret_access_key,
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
                    "object_count": report.object_count,
                },
                sort_keys=True,
            )
        )
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
