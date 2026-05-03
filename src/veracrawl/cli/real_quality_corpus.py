"""Expanded real-world public quality corpus CLI."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

from veracrawl.benchmarks.real_world_quality import (
    RealWorldQualityCorpusResult,
    run_real_world_quality_corpus,
)
from veracrawl.cli import real_benchmark
from veracrawl.contracts.real_world_quality import RealWorldQualityCorpusManifest
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> RealWorldQualityCorpusResult:
    manifest = RealWorldQualityCorpusManifest.model_validate(
        real_benchmark._load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    state_root = out / "real_world" / "state"
    if state_root.exists():
        shutil.rmtree(state_root)
    result = run_real_world_quality_corpus(
        manifest=manifest,
        profile=profile,
        store=ReferencePersistenceStore(state_root),
        adapter_factory=real_benchmark._adapter_factory,
        robots_fetcher=real_benchmark._fetch_robots,
    )
    report = result.report
    _write_outputs(out, result)
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

    return result


def _write_outputs(out: Path, result: RealWorldQualityCorpusResult) -> None:
    out.mkdir(parents=True, exist_ok=True)
    real_world_dir = out / "real_world"
    real_world_dir.mkdir(parents=True, exist_ok=True)
    (out / "quality_report.json").write_text(
        json.dumps(result.report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "quality_site_observations.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.quality_observations],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "pattern_coverage.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.pattern_coverage],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (real_world_dir / "run_report.json").write_text(
        json.dumps(
            result.real_world_result.report.model_dump(mode="json"),
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (real_world_dir / "site_observations.json").write_text(
        json.dumps(
            [
                item.model_dump(mode="json")
                for item in result.real_world_result.observations
            ],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "summary.json").write_text(
        json.dumps(
            {
                "ok": result.report.completion_result.value == "pass",
                "fixture_id": result.report.fixture_id,
                "completion_result": result.report.completion_result.value,
                "operator_status": result.report.operator_status,
                "declared_target_count": result.report.declared_target_count,
                "passing_target_count": result.report.passing_target_count,
                "origin_count": result.report.origin_count,
                "pattern_family_count": result.report.pattern_family_count,
                "artifact_count": len(result.report.artifact_refs),
                "replay_bundle_count": len(result.report.replay_bundle_refs),
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-real-quality-corpus")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="quality")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        try:
            result = run_fixture(Path(args.fixture_dir), profile=args.profile, out=Path(args.out))
        except (OSError, ValueError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
            return 1
        report = result.report
        print(
            json.dumps(
                {
                    "ok": True,
                    "fixture_id": report.fixture_id,
                    "completion_result": report.completion_result.value,
                    "operator_status": report.operator_status,
                    "declared_target_count": report.declared_target_count,
                    "passing_target_count": report.passing_target_count,
                    "origin_count": report.origin_count,
                    "pattern_family_count": report.pattern_family_count,
                },
                sort_keys=True,
            )
        )
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
