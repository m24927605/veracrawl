"""Target website pattern coverage fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    CompletenessResult,
    TargetWebsitePattern,
    WebsitePatternCoverageFailureType,
)
from veracrawl.contracts.website_pattern import WebsitePatternCoverageFixtureManifest
from veracrawl.patterns.coverage import (
    WebsitePatternCoverageRuntimeResult,
    run_website_pattern_coverage_gate,
)


class WebsitePatternCoverageFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    completion_result: CompletenessResult
    operator_status: str
    coverage_record_refs: list[Ref] = Field(default_factory=list)
    covered_patterns: list[TargetWebsitePattern] = Field(default_factory=list)
    missing_patterns: list[TargetWebsitePattern] = Field(default_factory=list)
    unsupported_pattern_refs: list[Ref] = Field(default_factory=list)
    single_site_assumption_refs: list[Ref] = Field(default_factory=list)
    scaffold_only_refs: list[Ref] = Field(default_factory=list)
    unsafe_interaction_refs: list[Ref] = Field(default_factory=list)
    missing_pattern_specific_refs: list[Ref] = Field(default_factory=list)
    missing_replay_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    contract_only_refs: list[Ref] = Field(default_factory=list)
    missing_runtime_refs: list[Ref] = Field(default_factory=list)
    failure_type: WebsitePatternCoverageFailureType | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_website_pattern_coverage_fixture(
    manifest: WebsitePatternCoverageFixtureManifest,
    *,
    profile: str,
) -> WebsitePatternCoverageFixtureRunReport:
    result = run_website_pattern_coverage_gate(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        policy_decision_refs=[f"policy:{manifest.id}:website-pattern"],
    )
    return _to_run_report(manifest=manifest, profile=profile, result=result)


def _to_run_report(
    *,
    manifest: WebsitePatternCoverageFixtureManifest,
    profile: str,
    result: WebsitePatternCoverageRuntimeResult,
) -> WebsitePatternCoverageFixtureRunReport:
    report = result.report
    return WebsitePatternCoverageFixtureRunReport(
        id=f"website-pattern-fixture-run-report:{manifest.id}",
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        completion_result=report.completion_result,
        operator_status=report.operator_status,
        coverage_record_refs=report.coverage_record_refs,
        covered_patterns=report.covered_patterns,
        missing_patterns=report.missing_patterns,
        unsupported_pattern_refs=report.unsupported_pattern_refs,
        single_site_assumption_refs=report.single_site_assumption_refs,
        scaffold_only_refs=report.scaffold_only_refs,
        unsafe_interaction_refs=report.unsafe_interaction_refs,
        missing_pattern_specific_refs=report.missing_pattern_specific_refs,
        missing_replay_refs=report.missing_replay_refs,
        policy_decision_refs=report.policy_decision_refs,
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        contract_only_refs=report.contract_only_refs,
        missing_runtime_refs=report.missing_runtime_refs,
        failure_type=report.failure_type,
        failure_report_refs=report.failure_report_refs,
        missing_ref_fields=report.missing_ref_fields,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> WebsitePatternCoverageFixtureRunReport:
    manifest = WebsitePatternCoverageFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    report = run_website_pattern_coverage_fixture(manifest, profile=profile)
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(
            f"fixture {manifest.id} completion mismatch: {report.completion_result}"
        )
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    if (
        manifest.expected_failure_type is not None
        and report.failure_type != manifest.expected_failure_type
    ):
        raise ValueError(f"fixture {manifest.id} failure mismatch: {report.failure_type}")
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-website-patterns")
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
