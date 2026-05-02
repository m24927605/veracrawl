"""Scale hardening fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.scale import ScaleFixtureManifest
from veracrawl.scale.hardening import ScaleHardeningResult, run_scale_hardening


class ScaleFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    completion_result: CompletenessResult
    operator_status: str
    queue_topology_ref: Ref | None = None
    queue_item_refs: list[Ref] = Field(default_factory=list)
    shard_lease_refs: list[Ref] = Field(default_factory=list)
    backpressure_signal_refs: list[Ref] = Field(default_factory=list)
    autoscaling_decision_refs: list[Ref] = Field(default_factory=list)
    dead_letter_record_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    dr_restore_report_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    missing_ref_fields: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_scale_fixture(
    manifest: ScaleFixtureManifest,
    *,
    profile: str,
) -> ScaleFixtureRunReport:
    result = run_scale_hardening(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        policy_decision_refs=[f"policy:{manifest.id}:scale"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: ScaleFixtureManifest,
    profile: str,
    result: ScaleHardeningResult,
) -> ScaleFixtureRunReport:
    report = result.report
    return ScaleFixtureRunReport(
        id=f"scale-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        run_ref=report.run_ref,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        queue_topology_ref=report.queue_topology_ref,
        queue_item_refs=report.queue_item_refs,
        shard_lease_refs=report.shard_lease_refs,
        backpressure_signal_refs=report.backpressure_signal_refs,
        autoscaling_decision_refs=report.autoscaling_decision_refs,
        dead_letter_record_refs=report.dead_letter_record_refs,
        failure_record_refs=report.failure_record_refs,
        recovery_action_refs=report.recovery_action_refs,
        dr_restore_report_refs=report.dr_restore_report_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        missing_ref_fields=report.missing_ref_fields,
    )


def run_fixture(fixture_dir: Path, *, profile: str, out: Path) -> ScaleFixtureRunReport:
    manifest = ScaleFixtureManifest.model_validate(_load_json_like(fixture_dir / "manifest.yaml"))
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_scale_fixture(manifest, profile=profile)
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
    parser = argparse.ArgumentParser(prog="veracrawl-scale")
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
                },
                sort_keys=True,
            )
        )
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
