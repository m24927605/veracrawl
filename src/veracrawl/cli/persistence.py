"""Persistence runtime fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.persistence import PersistenceFixtureManifest
from veracrawl.persistence.runtime import PersistenceRuntimeResult, run_persistence_queue_runtime
from veracrawl.runtime_support.logging import bootstrap_cli_logging


class PersistenceFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    adapter_ref: Ref | None = None
    transaction_ref: Ref | None = None
    command_record_refs: list[Ref] = Field(default_factory=list)
    idempotency_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_ref: Ref | None = None
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    queue_operation_refs: list[Ref] = Field(default_factory=list)
    lease_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
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


def run_persistence_fixture(
    manifest: PersistenceFixtureManifest,
    *,
    profile: str,
    state_root: Path,
) -> PersistenceFixtureRunReport:
    result = run_persistence_queue_runtime(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        root=state_root,
        policy_decision_refs=[f"policy:{manifest.id}:persistence"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: PersistenceFixtureManifest,
    profile: str,
    result: PersistenceRuntimeResult,
) -> PersistenceFixtureRunReport:
    report = result.report
    return PersistenceFixtureRunReport(
        id=f"persistence-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        adapter_ref=report.adapter_ref,
        transaction_ref=report.transaction_ref,
        command_record_refs=report.command_record_refs,
        idempotency_record_refs=report.idempotency_record_refs,
        event_cursor_ref=report.event_cursor_ref,
        outbox_refs=report.outbox_refs,
        artifact_refs=report.artifact_refs,
        queue_operation_refs=report.queue_operation_refs,
        lease_refs=report.lease_refs,
        failure_record_refs=report.failure_record_refs,
        recovery_action_refs=report.recovery_action_refs,
        policy_decision_refs=report.policy_decision_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        missing_ref_fields=report.missing_ref_fields,
        duplicate_deduped=result.duplicate_deduped,
        event_count=result.event_count,
        outbox_count=result.outbox_count,
        reloaded=result.reloaded,
    )


def run_fixture(fixture_dir: Path, *, profile: str, out: Path) -> PersistenceFixtureRunReport:
    manifest = PersistenceFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    state_root = out / "state"
    report = run_persistence_fixture(manifest, profile=profile, state_root=state_root)
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
    parser = argparse.ArgumentParser(prog="veracrawl-persistence")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-persistence"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run":
            try:
                report = run_fixture(
                    Path(args.fixture_dir), profile=args.profile, out=Path(args.out)
                )
            except (OSError, ValueError) as exc:
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
