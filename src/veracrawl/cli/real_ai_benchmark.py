"""Real-world AI agent benchmark runner CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from veracrawl.benchmarks.real_world import RealWorldBenchmarkResult
from veracrawl.benchmarks.real_world_ai_agent import (
    RealWorldAIAgentBenchmarkResult,
    RealWorldAIAgentBinding,
    RealWorldAIModelBinding,
    run_real_world_ai_agent_benchmark,
)
from veracrawl.cli import real_benchmark
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.real_world_ai_agent import RealWorldAIAgentBenchmarkManifest
from veracrawl.ports.agent_runtime import AgentRuntimePort, ModelProviderPort


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_module(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


def _model_binding(manifest: RealWorldAIAgentBenchmarkManifest) -> RealWorldAIModelBinding:
    module = _load_module("veracrawl.adapters.model_providers.local_runtime")
    builder = cast(Callable[[], object], module.__dict__["build_model_provider"])
    provider = cast(ModelProviderPort, builder())
    provider_name = cast(str, getattr(provider, "provider_name", manifest.provider_names[0]))
    model_id = cast(str, getattr(provider, "model_id", "veracrawl-local-deterministic"))
    model_version = cast(str, getattr(provider, "model_version", "1"))
    return RealWorldAIModelBinding(
        provider_name=provider_name,
        model_id=model_id,
        model_version=model_version,
        runtime_ref=f"model-runtime:{manifest.id}:{_slug(provider_name)}:local",
        port=provider,
    )


def _agent_binding(manifest: RealWorldAIAgentBenchmarkManifest) -> RealWorldAIAgentBinding:
    module = _load_module("veracrawl.adapters.agent_frameworks.native_runtime")
    builder = cast(Callable[[], object], module.__dict__["build_agent_runtime"])
    runtime = cast(AgentRuntimePort, builder())
    framework_name = cast(str, getattr(runtime, "framework_name", manifest.framework_names[0]))
    return RealWorldAIAgentBinding(
        framework_name=framework_name,
        runtime_spec_id=f"agent-runtime-spec:{manifest.id}:{_slug(framework_name)}",
        runtime_ref=f"agent-runtime:{manifest.id}:{_slug(framework_name)}:native",
        port=runtime,
    )


def _run_real_world_corpus(
    manifest: RealWorldAIAgentBenchmarkManifest,
    *,
    profile: str,
    out: Path,
) -> RealWorldBenchmarkResult:
    return real_benchmark.run_fixture(
        Path(manifest.real_world_corpus_fixture_path),
        profile=profile,
        out=out,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> RealWorldAIAgentBenchmarkResult:
    manifest = RealWorldAIAgentBenchmarkManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    out.mkdir(parents=True, exist_ok=True)
    real_world_result = (
        None
        if manifest.scenario == "real-world-ai-agent-missing-real-world-corpus"
        else _run_real_world_corpus(manifest, profile=profile, out=out / "real_world")
    )
    result = run_real_world_ai_agent_benchmark(
        manifest=manifest,
        profile=profile,
        real_world_result=real_world_result,
        model_binding=_model_binding(manifest),
        agent_binding=_agent_binding(manifest),
    )
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

    _write_json(out / "run_report.json", report.model_dump(mode="json"))
    _write_json(
        out / "decision_traces.json",
        [item.model_dump(mode="json") for item in result.decision_traces],
    )
    _write_json(
        out / "extraction_candidates.json",
        [item.model_dump(mode="json") for item in result.extraction_candidates],
    )
    _write_json(
        out / "model_requests.json",
        [item.model_dump(mode="json") for item in result.model_requests],
    )
    _write_json(
        out / "model_responses.json",
        [item.model_dump(mode="json") for item in result.model_responses],
    )
    _write_json(
        out / "model_call_traces.json",
        [item.model_dump(mode="json") for item in result.model_call_traces],
    )
    _write_json(
        out / "agent_run_requests.json",
        [item.model_dump(mode="json") for item in result.agent_run_requests],
    )
    _write_json(
        out / "agent_run_results.json",
        [item.model_dump(mode="json") for item in result.agent_run_results],
    )
    _write_json(
        out / "agent_action_traces.json",
        [item.model_dump(mode="json") for item in result.agent_action_traces],
    )
    _write_json(
        out / "tool_call_traces.json",
        [item.model_dump(mode="json") for item in result.tool_call_traces],
    )
    _write_json(
        out / "context_bundle_traces.json",
        [item.model_dump(mode="json") for item in result.context_bundle_traces],
    )
    _write_json(out / "summary.json", _summary(result))
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-real-ai-benchmark")
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
            result = run_fixture(Path(args.fixture_dir), profile=args.profile, out=Path(args.out))
        except (OSError, ValueError, RuntimeError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
            return 1
        print(json.dumps(_summary(result), sort_keys=True))
        return 0
    return 2


def _summary(result: RealWorldAIAgentBenchmarkResult) -> dict[str, object]:
    report = result.report
    return {
        "ok": report.completion_result == CompletenessResult.PASS,
        "fixture_id": report.fixture_id,
        "completion_result": report.completion_result.value,
        "operator_status": report.operator_status,
        "site_count": len(report.site_observation_refs),
        "decision_trace_count": len(report.decision_trace_refs),
        "model_call_trace_count": len(report.model_call_trace_refs),
        "agent_action_trace_count": len(report.agent_action_trace_refs),
        "tool_call_trace_count": len(report.tool_call_trace_refs),
        "context_bundle_trace_count": len(report.context_bundle_trace_refs),
        "extraction_candidate_count": len(report.extraction_candidate_refs),
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace("/", "-")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
