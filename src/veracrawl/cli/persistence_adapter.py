"""Persistence adapter conformance fixture runner CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult, PersistenceAdapterKind
from veracrawl.contracts.persistence import (
    PersistenceAdapterFixtureManifest,
    PersistenceAdapterSpec,
)
from veracrawl.persistence.adapter_conformance import (
    OperationalPersistenceAdapter,
    PersistenceAdapterConformanceResult,
    run_postgres_contract_conformance,
    run_sqlite_adapter_conformance,
)


class PersistenceAdapterFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    completion_result: CompletenessResult
    operator_status: str
    adapter_ref: Ref | None = None
    adapter_kind: PersistenceAdapterKind | None = None
    transaction_refs: list[Ref] = Field(default_factory=list)
    migration_record_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    idempotency_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    queue_operation_refs: list[Ref] = Field(default_factory=list)
    lease_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    contract_only_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    missing_ref_fields: list[str] = Field(default_factory=list)
    duplicate_deduped: bool = False
    event_count: int = 0
    outbox_count: int = 0
    reloaded: bool = False


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_module(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


def _sqlite_adapter(
    fixture_id: str,
    policy_refs: list[Ref],
    database_path: Path,
) -> tuple[OperationalPersistenceAdapter, PersistenceAdapterSpec]:
    module = _load_module("veracrawl.adapters.persistence.sqlite")
    adapter_factory = cast(
        Callable[[Path], OperationalPersistenceAdapter],
        module.__dict__["SQLitePersistenceAdapter"],
    )
    spec_builder = cast(
        Callable[[str, list[Ref]], PersistenceAdapterSpec],
        module.__dict__["sqlite_adapter_spec"],
    )
    return adapter_factory(database_path), spec_builder(fixture_id, policy_refs)


def _postgres_adapter_spec(fixture_id: str, policy_refs: list[Ref]) -> PersistenceAdapterSpec:
    module = _load_module("veracrawl.adapters.persistence.postgres_contract")
    spec_builder = cast(
        Callable[[str, list[Ref]], PersistenceAdapterSpec],
        module.__dict__["postgres_adapter_spec"],
    )
    return spec_builder(fixture_id, policy_refs)


def run_persistence_adapter_fixture(
    manifest: PersistenceAdapterFixtureManifest,
    *,
    profile: str,
    state_root: Path,
) -> PersistenceAdapterFixtureRunReport:
    policy_refs = [f"policy:{manifest.id}:persistence-adapter"]
    if manifest.scenario == "postgres-adapter-contract-harness":
        adapter_spec = _postgres_adapter_spec(manifest.id, policy_refs)
        result = run_postgres_contract_conformance(
            fixture_id=manifest.id,
            adapter_spec=adapter_spec,
            policy_decision_refs=policy_refs,
        )
    else:
        adapter, adapter_spec = _sqlite_adapter(
            manifest.id,
            policy_refs,
            state_root / "sqlite-conformance.db",
        )
        result = run_sqlite_adapter_conformance(
            fixture_id=manifest.id,
            scenario=manifest.scenario,
            store=adapter,
            adapter_spec=None
            if manifest.scenario == "adapter-missing-capability"
            else adapter_spec,
            policy_decision_refs=policy_refs,
        )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: PersistenceAdapterFixtureManifest,
    profile: str,
    result: PersistenceAdapterConformanceResult,
) -> PersistenceAdapterFixtureRunReport:
    report = result.report
    return PersistenceAdapterFixtureRunReport(
        id=f"persistence-adapter-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        adapter_ref=report.adapter_ref,
        adapter_kind=report.adapter_kind,
        transaction_refs=report.transaction_refs,
        migration_record_refs=report.migration_record_refs,
        command_record_refs=report.command_record_refs,
        idempotency_record_refs=report.idempotency_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        artifact_refs=report.artifact_refs,
        queue_operation_refs=report.queue_operation_refs,
        lease_refs=report.lease_refs,
        policy_decision_refs=report.policy_decision_refs,
        contract_only_refs=report.contract_only_refs,
        failure_record_refs=report.failure_record_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        missing_ref_fields=report.missing_ref_fields,
        duplicate_deduped=result.duplicate_deduped,
        event_count=result.event_count,
        outbox_count=result.outbox_count,
        reloaded=result.reloaded,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> PersistenceAdapterFixtureRunReport:
    manifest = PersistenceAdapterFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    state_root = out / "state"
    report = run_persistence_adapter_fixture(manifest, profile=profile, state_root=state_root)
    if report.completion_result.value != manifest.expected_completion_result:
        raise ValueError(f"fixture {manifest.id} completion mismatch: {report.completion_result}")
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-persistence-adapter")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        try:
            report = run_fixture(Path(args.fixture_dir), profile=args.profile, out=Path(args.out))
        except (AttributeError, ImportError, OSError, ValueError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
            return 1
        print(
            json.dumps(
                {
                    "ok": True,
                    "fixture_id": report.fixture_id,
                    "completion_result": report.completion_result.value,
                    "operator_status": report.operator_status,
                    "event_count": report.event_count,
                    "outbox_count": report.outbox_count,
                    "duplicate_deduped": report.duplicate_deduped,
                },
                sort_keys=True,
            )
        )
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
