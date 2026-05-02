"""Security/privacy lifecycle fixture runner CLI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.security_privacy import SecurityPrivacyFixtureManifest
from veracrawl.runtime_support.security_privacy import (
    SecurityPrivacyGateResult,
    run_security_privacy_gate,
)


class SecurityPrivacyFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    completion_result: CompletenessResult
    operator_status: str
    security_policy_check_refs: list[Ref] = Field(default_factory=list)
    credential_use_audit_refs: list[Ref] = Field(default_factory=list)
    prompt_taint_boundary_refs: list[Ref] = Field(default_factory=list)
    artifact_lifecycle_action_refs: list[Ref] = Field(default_factory=list)
    projection_cleanup_refs: list[Ref] = Field(default_factory=list)
    redacted_replay_refs: list[Ref] = Field(default_factory=list)
    observability_report_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    failure_record_refs: list[Ref] = Field(default_factory=list)
    recovery_action_refs: list[Ref] = Field(default_factory=list)
    redaction_map_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    leakage_count: int = 0
    raw_secret_leak_refs: list[Ref] = Field(default_factory=list)
    unsafe_action_refs: list[Ref] = Field(default_factory=list)
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _to_run_report(
    *,
    manifest: SecurityPrivacyFixtureManifest,
    profile: str,
    result: SecurityPrivacyGateResult,
) -> SecurityPrivacyFixtureRunReport:
    report = result.report
    return SecurityPrivacyFixtureRunReport(
        id=f"security-privacy-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        completion_result=report.result,
        operator_status=report.operator_status,
        security_policy_check_refs=report.security_policy_check_refs,
        credential_use_audit_refs=report.credential_use_audit_refs,
        prompt_taint_boundary_refs=report.prompt_taint_boundary_refs,
        artifact_lifecycle_action_refs=report.artifact_lifecycle_action_refs,
        projection_cleanup_refs=report.projection_cleanup_refs,
        redacted_replay_refs=report.redacted_replay_refs,
        observability_report_refs=report.observability_report_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        failure_record_refs=report.failure_record_refs,
        recovery_action_refs=report.recovery_action_refs,
        redaction_map_refs=report.redaction_map_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        leakage_count=report.leakage_count,
        raw_secret_leak_refs=report.raw_secret_leak_refs,
        unsafe_action_refs=report.unsafe_action_refs,
        contract_only_refs=report.contract_only_refs,
        missing_ref_fields=report.missing_ref_fields,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> SecurityPrivacyFixtureRunReport:
    manifest = SecurityPrivacyFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = _to_run_report(
        manifest=manifest,
        profile=profile,
        result=run_security_privacy_gate(fixture_id=manifest.id, scenario=manifest.scenario),
    )
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(
            f"fixture {manifest.id} completion mismatch: {report.completion_result}"
        )
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
    parser = argparse.ArgumentParser(prog="veracrawl-security-privacy")
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
        report = run_fixture(Path(args.fixture_dir), profile=args.profile, out=Path(args.out))
        print(json.dumps(report.model_dump(mode="json"), sort_keys=True))
        return 0
    parser.error(f"unsupported command {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
