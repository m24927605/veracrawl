"""Real agent/model adapter runtime fixture runner CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from veracrawl.agents.real_adapter_runtime import (
    AgentModelAdapterRuntimeResult,
    AgentRuntimeBinding,
    ModelRuntimeBinding,
    run_real_agent_model_adapter_runtime,
)
from veracrawl.contracts.agent_model_runtime import AgentModelAdapterFixtureManifest
from veracrawl.contracts.common import Ref
from veracrawl.ports.agent_runtime import AgentRuntimePort, ModelProviderPort
from veracrawl.runtime_support.logging import bootstrap_cli_logging


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_module(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


def _runtime_refs(fixture_id: str, scenario: str) -> tuple[Ref | None, Ref | None, Ref | None]:
    return (
        None
        if scenario == "agent-model-adapter-missing-run-control"
        else f"production-run-control-report:{fixture_id}",
        None
        if scenario == "agent-model-adapter-missing-live-normalization"
        else f"live-normalization-runtime-report:{fixture_id}",
        None
        if scenario == "agent-model-adapter-missing-schema-extraction"
        else f"schema-extraction-runtime-report:{fixture_id}",
    )


def _model_bindings(manifest: AgentModelAdapterFixtureManifest) -> list[ModelRuntimeBinding]:
    provider_names = manifest.provider_names or ["Local model runtime"]
    if manifest.scenario == "agent-model-adapter-runtime-unavailable":
        return [
            ModelRuntimeBinding(
                provider_name=name,
                model_id="unavailable",
                model_version="unavailable",
                runtime_ref=f"model-runtime:{manifest.id}:{_slug(name)}:unavailable",
                adapter_module_ref=f"adapter-module:{manifest.id}:{_slug(name)}",
                port=None,
            )
            for name in provider_names
        ]

    module = _load_module("veracrawl.adapters.model_providers.local_runtime")
    builder = cast(Callable[[], object], module.__dict__["build_model_provider"])
    provider = cast(ModelProviderPort, builder())
    provider_name = cast(str, getattr(provider, "provider_name", provider_names[0]))
    model_id = cast(str, getattr(provider, "model_id", "veracrawl-local-deterministic"))
    model_version = cast(str, getattr(provider, "model_version", "1"))
    return [
        ModelRuntimeBinding(
            provider_name=provider_name,
            model_id=model_id,
            model_version=model_version,
            runtime_ref=f"model-runtime:{manifest.id}:{_slug(provider_name)}:local",
            adapter_module_ref="module:veracrawl.adapters.model_providers.local_runtime",
            port=provider,
        )
    ]


def _agent_bindings(manifest: AgentModelAdapterFixtureManifest) -> list[AgentRuntimeBinding]:
    framework_names = manifest.framework_names or ["VeraCrawl Native Runtime"]
    if manifest.scenario == "agent-model-adapter-runtime-unavailable":
        return [
            AgentRuntimeBinding(
                framework_name=name,
                runtime_spec_id=f"agent-runtime-spec:{manifest.id}:{_slug(name)}",
                runtime_ref=f"agent-runtime:{manifest.id}:{_slug(name)}:unavailable",
                adapter_module_ref=f"adapter-module:{manifest.id}:{_slug(name)}",
                port=None,
            )
            for name in framework_names
        ]

    module = _load_module("veracrawl.adapters.agent_frameworks.native_runtime")
    builder = cast(Callable[[], object], module.__dict__["build_agent_runtime"])
    runtime = cast(AgentRuntimePort, builder())
    framework_name = cast(str, getattr(runtime, "framework_name", framework_names[0]))
    return [
        AgentRuntimeBinding(
            framework_name=framework_name,
            runtime_spec_id=f"agent-runtime-spec:{manifest.id}:{_slug(framework_name)}",
            runtime_ref=f"agent-runtime:{manifest.id}:{_slug(framework_name)}:native",
            adapter_module_ref="module:veracrawl.adapters.agent_frameworks.native_runtime",
            port=runtime,
        )
    ]


def run_agent_model_adapter_fixture(
    manifest: AgentModelAdapterFixtureManifest,
    *,
    profile: str,
) -> AgentModelAdapterRuntimeResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    run_control_ref, normalization_ref, schema_extraction_ref = _runtime_refs(
        manifest.id,
        manifest.scenario,
    )
    return run_real_agent_model_adapter_runtime(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        run_control_report_ref=run_control_ref,
        live_normalization_runtime_report_ref=normalization_ref,
        schema_extraction_runtime_report_ref=schema_extraction_ref,
        model_bindings=_model_bindings(manifest),
        agent_bindings=_agent_bindings(manifest),
        policy_decision_refs=[f"policy:{manifest.id}:agent-model-adapter"],
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> AgentModelAdapterRuntimeResult:
    manifest = AgentModelAdapterFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    result = run_agent_model_adapter_fixture(manifest, profile=profile)
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
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-agent-model-runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-agent-model-runtime"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run":
            try:
                result = run_fixture(
                    Path(args.fixture_dir), profile=args.profile, out=Path(args.out)
                )
            except (OSError, ValueError, RuntimeError) as exc:
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
                    },
                    sort_keys=True,
                )
            )
            return 0
        return 2


def _slug(name: str) -> str:
    return name.lower().replace(" ", "-").replace("/", "-")


if __name__ == "__main__":
    sys.exit(main())
