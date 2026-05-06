"""Deep crawl benchmark CLI."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from veracrawl.benchmarks.deep_crawl import (
    DeepCrawlCorpusResult,
    run_deep_crawl_quality_corpus,
)
from veracrawl.contracts.deep_crawl import DeepCrawlQualityManifest
from veracrawl.runtime_support.logging import bootstrap_cli_logging
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> DeepCrawlCorpusResult:
    manifest = DeepCrawlQualityManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    state_root = out / "state"
    if state_root.exists():
        shutil.rmtree(state_root)
    result = run_deep_crawl_quality_corpus(
        manifest=manifest,
        profile=profile,
        store=ReferencePersistenceStore(state_root),
    )
    _write_outputs(out, result)
    report = result.report
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(f"fixture {manifest.id} completion mismatch: {report.completion_result}")
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(f"fixture {manifest.id} status mismatch: {report.operator_status}")
    if (
        manifest.expected_failure_type is not None
        and report.failure_type != manifest.expected_failure_type
    ):
        raise ValueError(f"fixture {manifest.id} failure mismatch: {report.failure_type}")
    return result


def _write_outputs(out: Path, result: DeepCrawlCorpusResult) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "deep_crawl_report.json").write_text(
        json.dumps(result.report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "frontier_decisions.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.frontier_decisions],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "page_observations.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.page_observations],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "stop_reasons.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.stop_reasons],
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
                "site_count": result.report.site_count,
                "covered_page_count": result.report.covered_page_count,
                "observed_page_count": result.report.observed_page_count,
                "frontier_decision_count": result.report.frontier_decision_count,
                "stop_reason_count": result.report.stop_reason_count,
                "duplicate_suppressed_count": result.report.duplicate_suppressed_count,
                "replay_bundle_count": len(result.report.replay_bundle_refs),
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-deep-crawl-benchmark")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="quality")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-deep-crawl"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run":
            try:
                result = run_fixture(
                    Path(args.fixture_dir),
                    profile=args.profile,
                    out=Path(args.out),
                )
            except (OSError, RuntimeError, ValueError) as exc:
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
                        "site_count": report.site_count,
                        "covered_page_count": report.covered_page_count,
                        "frontier_decision_count": report.frontier_decision_count,
                    },
                    sort_keys=True,
                )
            )
            return 0
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
