"""Crawler intelligence optimization benchmark CLI."""

from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path
from typing import Any

from veracrawl.benchmarks.crawler_optimization import (
    CrawlerOptimizationBenchmarkResult,
    run_crawler_optimization_benchmark,
)
from veracrawl.contracts.crawler_optimization import CrawlerOptimizationManifest
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.optimization.objective_evidence import (
    OptimizationObjectiveEvidenceRun,
    objective_evidence_summary,
    run_deterministic_objective_evidence,
)
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
) -> CrawlerOptimizationBenchmarkResult:
    manifest = CrawlerOptimizationManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    state_root = out / "state"
    if state_root.exists():
        shutil.rmtree(state_root)
    result = run_crawler_optimization_benchmark(
        manifest=manifest,
        profile=profile,
        store=ReferencePersistenceStore(state_root),
    )
    _write_outputs(out, result)
    report = result.report
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


def _write_outputs(out: Path, result: CrawlerOptimizationBenchmarkResult) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "crawler_optimization_report.json", result.report.model_dump(mode="json"))
    _write_json(out / "architecture.json", result.architecture.model_dump(mode="json"))
    _write_json(
        out / "algorithm_recommendations.json",
        [item.model_dump(mode="json") for item in result.algorithm_recommendations],
    )
    _write_json(
        out / "frontier_scores.json",
        [item.model_dump(mode="json") for item in result.frontier_scores],
    )
    _write_json(
        out / "dom_contexts.json",
        [item.model_dump(mode="json") for item in result.dom_contexts],
    )
    _write_json(
        out / "extractor_attempts.json",
        [item.model_dump(mode="json") for item in result.extractor_attempts],
    )
    _write_json(
        out / "canonicalization_decisions.json",
        [item.model_dump(mode="json") for item in result.canonicalization_decisions],
    )
    _write_json(
        out / "duplicate_suppression_records.json",
        [item.model_dump(mode="json") for item in result.duplicate_suppression_records],
    )
    _write_json(
        out / "ranking_scores.json",
        [item.model_dump(mode="json") for item in result.ranking_scores],
    )
    _write_json(
        out / "metric_slices.json",
        [item.model_dump(mode="json") for item in result.metric_slices],
    )
    _write_json(out / "summary.json", _summary(result))


def run_objective_gate(
    fixture_dir: Path,
    *,
    out: Path,
) -> OptimizationObjectiveEvidenceRun:
    manifest = CrawlerOptimizationManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if manifest.expected_completion_result != CompletenessResult.PASS:
        raise ValueError("objective gate evidence requires a passing optimization fixture")
    result = run_deterministic_objective_evidence(
        fixture_id="optimization-objective-gate-success",
        run_ref=f"run:{manifest.id}",
        profile_ref="profile:optimization",
        claim_scope_ref=f"claim:optimization-objective:{manifest.id}",
    )
    _write_objective_gate_outputs(out, result)
    if result.objective_release_gate.completion_result != CompletenessResult.PASS:
        raise ValueError("optimization objective release gate did not pass")
    return result


def _write_objective_gate_outputs(
    out: Path,
    result: OptimizationObjectiveEvidenceRun,
) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "metric_slice.json", result.metric.model_dump(mode="json"))
    _write_json(
        out / "lower_optimization_integrations.json",
        [item.model_dump(mode="json") for item in result.lower_integrations],
    )
    _write_json(
        out / "optimization_regression_release_gate.json",
        result.regression_gate.model_dump(mode="json"),
    )
    _write_json(
        out / "optimization_objective_score.json",
        result.objective_score.model_dump(mode="json"),
    )
    _write_json(
        out / "agent_decision_loop_evidence.json",
        result.agent_decision_loop.model_dump(mode="json"),
    )
    _write_json(
        out / "optimization_objective_release_gate.json",
        result.objective_release_gate.model_dump(mode="json"),
    )
    _write_json(out / "summary.json", objective_evidence_summary(result))


def _summary(result: CrawlerOptimizationBenchmarkResult) -> dict[str, object]:
    report = result.report
    return {
        "ok": report.completion_result == CompletenessResult.PASS,
        "fixture_id": report.fixture_id,
        "completion_result": report.completion_result.value,
        "operator_status": report.operator_status,
        "failure_type": report.failure_type.value if report.failure_type else None,
        "frontier_score_count": len(report.frontier_score_refs),
        "dom_context_count": len(report.dom_context_refs),
        "extractor_attempt_count": len(report.extractor_attempt_refs),
        "identity_decision_count": len(report.identity_decision_refs),
        "ranking_score_count": len(report.ranking_score_refs),
        "precision": report.precision,
        "recall": report.recall,
        "extraction_accuracy": report.extraction_accuracy,
        "duplicate_rate": report.duplicate_rate,
        "cost_per_success": report.cost_per_success,
        "latency_p95_ms": report.latency_p95_ms,
        "ranking_ndcg": report.ranking_ndcg,
        "llm_token_savings_rate": report.llm_token_savings_rate,
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-crawler-optimization")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="optimization")
    run.add_argument("--out", required=True)
    objective_gate = sub.add_parser("run-objective-gate")
    objective_gate.add_argument("fixture_dir")
    objective_gate.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        try:
            result = run_fixture(Path(args.fixture_dir), profile=args.profile, out=Path(args.out))
        except (OSError, RuntimeError, ValueError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
            return 1
        print(json.dumps(_summary(result), sort_keys=True))
        return 0
    if args.command == "run-objective-gate":
        try:
            objective_result = run_objective_gate(Path(args.fixture_dir), out=Path(args.out))
        except (OSError, RuntimeError, ValueError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
            return 1
        print(json.dumps(objective_evidence_summary(objective_result), sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
