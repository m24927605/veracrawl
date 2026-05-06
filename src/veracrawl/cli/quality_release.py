"""Cost, latency, stability quality release gate CLI."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from veracrawl.benchmarks.quality_release import (
    QualityReleaseGateResult,
    run_quality_release_gate,
)
from veracrawl.contracts.quality_release import QualityReleaseManifest
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
) -> QualityReleaseGateResult:
    manifest = QualityReleaseManifest.model_validate(_load_json_like(fixture_dir / "manifest.yaml"))
    state_root = out / "state"
    if state_root.exists():
        shutil.rmtree(state_root)
    result = run_quality_release_gate(
        manifest=manifest,
        profile=profile,
        store=ReferencePersistenceStore(state_root),
    )
    _write_outputs(out, result)
    report = result.report
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(f"fixture {manifest.id} completion mismatch: {report.completion_result}")
    if report.release_decision != manifest.expected_release_decision:
        raise ValueError(f"fixture {manifest.id} decision mismatch: {report.release_decision}")
    if (
        manifest.expected_failure_type is not None
        and report.failure_type != manifest.expected_failure_type
    ):
        raise ValueError(f"fixture {manifest.id} failure mismatch: {report.failure_type}")
    return result


def _write_outputs(out: Path, result: QualityReleaseGateResult) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "quality_release_report.json").write_text(
        json.dumps(result.report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "quality_gate_refs.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.quality_gates],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "stability_runs.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.stability_runs],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    report = result.report
    (out / "summary.json").write_text(
        json.dumps(
            {
                "ok": report.completion_result.value == "pass",
                "fixture_id": report.fixture_id,
                "completion_result": report.completion_result.value,
                "release_decision": report.release_decision.value,
                "observed_quality_gate_count": report.observed_quality_gate_count,
                "stability_run_count": report.stability_run_count,
                "total_cost_usd": report.total_cost_usd,
                "p95_latency_ms": report.p95_latency_ms,
                "throughput_pages_per_minute": report.throughput_pages_per_minute,
                "retry_rate": report.retry_rate,
                "token_count": report.token_count,
                "model_call_count": report.model_call_count,
                "stability_variance": report.stability_variance,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-quality-release-gate")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="quality")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-quality-release"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run":
            try:
                result = run_fixture(
                    Path(args.fixture_dir), profile=args.profile, out=Path(args.out)
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
                        "release_decision": report.release_decision.value,
                        "observed_quality_gate_count": report.observed_quality_gate_count,
                        "stability_run_count": report.stability_run_count,
                    },
                    sort_keys=True,
                )
            )
            return 0
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
