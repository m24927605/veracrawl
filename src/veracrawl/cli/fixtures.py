"""Fixture/oracle validation CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.errors import FixtureValidationError
from veracrawl.contracts.fixture import (
    BenchmarkFixtureManifest,
    DRRestoreOracle,
    ExpectedEventSequenceOracle,
    ExpectedEvidenceCoverageOracle,
    ExpectedGraphOracle,
    ExpectedOutputOracle,
    FailureInjectionPlan,
    ReplayBundleOracle,
    ThresholdSpec,
)


def _load_json_like(path: Path) -> dict[str, Any]:
    try:
        with path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except FileNotFoundError as exc:
        raise FixtureValidationError(f"missing fixture file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise FixtureValidationError(f"fixture file must contain canonical JSON: {path}") from exc
    if not isinstance(data, dict):
        raise FixtureValidationError(f"fixture file must contain an object: {path}")
    return data


ORACLE_MODELS: dict[str, type[BaseModel]] = {
    "expected_outputs": ExpectedOutputOracle,
    "expected_evidence": ExpectedEvidenceCoverageOracle,
    "expected_events": ExpectedEventSequenceOracle,
    "expected_graph": ExpectedGraphOracle,
    "expected_dr_restore": DRRestoreOracle,
    "expected_replay": ReplayBundleOracle,
    "failure_injection": FailureInjectionPlan,
    "thresholds": ThresholdSpec,
}


def _contains_raw_secret(path: Path) -> bool:
    if not path.exists() or path.is_dir():
        return False
    text = path.read_text(encoding="utf-8")
    return "RAW_SECRET" in text or "agent_visible_secret" in text


def _expected_status_for_scenario(scenario: str) -> CompletenessResult:
    if scenario == "replay-missing-ref":
        return CompletenessResult.FAIL
    if scenario == "missing-evidence":
        return CompletenessResult.NEEDS_REVIEW
    if scenario == "adapter-mismatch":
        return CompletenessResult.FAIL
    return CompletenessResult.PASS


def validate_fixture(fixture_dir: Path, *, profile: str) -> dict[str, Any]:
    manifest_path = fixture_dir / "manifest.yaml"
    manifest = BenchmarkFixtureManifest.model_validate(_load_json_like(manifest_path))
    if profile not in manifest.profile_refs:
        raise FixtureValidationError(f"fixture {manifest.id} does not support profile {profile}")

    loaded_oracles: dict[str, Any] = {}
    for oracle_name, relative_path in manifest.oracles.items():
        if oracle_name not in ORACLE_MODELS:
            raise FixtureValidationError(f"unknown oracle type {oracle_name}")
        oracle_path = fixture_dir / relative_path
        try:
            loaded_oracles[oracle_name] = ORACLE_MODELS[oracle_name].model_validate(
                _load_json_like(oracle_path)
            )
        except ValidationError as exc:
            raise FixtureValidationError(f"invalid oracle {oracle_path}: {exc}") from exc

    for artifact_path in manifest.artifacts.values():
        artifact = fixture_dir / artifact_path
        if not artifact.exists():
            raise FixtureValidationError(f"missing artifact expectation: {artifact}")

    for path in fixture_dir.rglob("*"):
        if _contains_raw_secret(path):
            raise FixtureValidationError(f"raw secret material found in fixture output: {path}")

    expected_replay = loaded_oracles.get("expected_replay")
    if not isinstance(expected_replay, ReplayBundleOracle):
        raise FixtureValidationError("expected_replay oracle is required")

    actual_status = _expected_status_for_scenario(manifest.scenario)
    if actual_status != expected_replay.expected_completeness_result:
        raise FixtureValidationError(
            f"scenario {manifest.scenario} produced {actual_status.value}, "
            f"expected {expected_replay.expected_completeness_result.value}"
        )

    if manifest.scenario == "missing-evidence":
        evidence = loaded_oracles.get("expected_evidence")
        if not isinstance(evidence, ExpectedEvidenceCoverageOracle):
            raise FixtureValidationError("missing-evidence fixture requires evidence oracle")
        if evidence.missing_evidence_behavior == CompletenessResult.PASS:
            raise FixtureValidationError("missing evidence must not produce pass")

    if manifest.scenario == "adapter-mismatch":
        failure = loaded_oracles.get("failure_injection")
        if not isinstance(failure, FailureInjectionPlan):
            raise FixtureValidationError("adapter-mismatch fixture requires failure oracle")
        if failure.expected_operator_visible_status != "adapter_mismatch":
            raise FixtureValidationError("adapter mismatch diagnostics are required")

    return {
        "fixture_id": manifest.id,
        "scenario": manifest.scenario,
        "profile": profile,
        "completeness_result": actual_status.value,
        "oracle_count": len(loaded_oracles),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-fixture")
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
            report = validate_fixture(Path(args.fixture_dir), profile=args.profile)
        except FixtureValidationError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
            return 1
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "run_report.json").write_text(
            json.dumps({"ok": True, **report}, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        print(json.dumps({"ok": True, **report}, sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
