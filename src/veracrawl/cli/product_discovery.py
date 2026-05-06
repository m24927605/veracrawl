"""Query-driven product discovery CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from veracrawl.benchmarks.product_availability import (
    ProductAvailabilityAgentBinding,
    ProductAvailabilityModelBinding,
)
from veracrawl.benchmarks.product_discovery import (
    ProductDiscoveryBenchmarkResult,
    run_product_discovery_benchmark,
)
from veracrawl.benchmarks.real_world import RobotsFetchResult
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.product_availability import ProductAvailabilityTargetSpec
from veracrawl.contracts.product_discovery import (
    ProductDiscoveryBenchmarkManifest,
    ProductDiscoverySourceSpec,
)
from veracrawl.fetch.network_acquisition import build_network_request
from veracrawl.ports.agent_runtime import AgentRuntimePort, ModelProviderPort
from veracrawl.ports.network import NetworkSourceAdapterPort
from veracrawl.runtime_support.logging import bootstrap_cli_logging
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore

_USER_AGENT = "VeraCrawl-real-benchmark/1"


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_module(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


def _load_dotenv(path: Path | None = None) -> None:
    path = path or (Path.home() / ".env")
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", maxsplit=1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def _discovery_adapter_factory(
    fixture_id: str,
    source: ProductDiscoverySourceSpec,
) -> NetworkSourceAdapterPort:
    request = build_network_request(
        fixture_id=fixture_id,
        target_url=source.search_url,
        policy_decision_refs=[f"policy:{fixture_id}:network"],
        size_budget_bytes=source.size_budget_bytes,
        timeout_ms=source.timeout_ms,
    )
    adapter_module = importlib.import_module("veracrawl.adapters.network.stdlib_http")
    return cast(NetworkSourceAdapterPort, adapter_module.StdlibHttpSourceAdapter(request))


def _product_adapter_factory(
    fixture_id: str,
    target: ProductAvailabilityTargetSpec,
) -> NetworkSourceAdapterPort:
    request = build_network_request(
        fixture_id=fixture_id,
        target_url=target.target_url,
        policy_decision_refs=[f"policy:{fixture_id}:network"],
        size_budget_bytes=target.size_budget_bytes,
        timeout_ms=target.timeout_ms,
    )
    adapter_module = importlib.import_module("veracrawl.adapters.network.stdlib_http")
    return cast(NetworkSourceAdapterPort, adapter_module.StdlibHttpSourceAdapter(request))


def _fetch_discovery_robots(source: ProductDiscoverySourceSpec) -> RobotsFetchResult:
    return _fetch_robots(source.robots_url, source.timeout_ms, source.allowed_robots_status_codes)


def _fetch_product_robots(target: ProductAvailabilityTargetSpec) -> RobotsFetchResult:
    return _fetch_robots(target.robots_url, target.timeout_ms, target.allowed_robots_status_codes)


def _fetch_robots(
    robots_url: str,
    timeout_ms: int,
    _allowed_status_codes: list[int],
) -> RobotsFetchResult:
    request = urllib.request.Request(
        robots_url,
        headers={"User-Agent": _USER_AGENT},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_ms / 1000) as response:
            body = response.read().decode("utf-8", errors="replace")
            return RobotsFetchResult(status_code=int(response.status), body_text=body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return RobotsFetchResult(status_code=int(exc.code), body_text=body)
    except urllib.error.URLError as exc:
        raise OSError(str(exc)) from exc


def _model_binding(
    manifest: ProductDiscoveryBenchmarkManifest,
    *,
    provider_kind: str,
    openai_model: str | None,
) -> ProductAvailabilityModelBinding:
    if provider_kind == "openai":
        _load_dotenv()
        module = _load_module("veracrawl.adapters.model_providers.openai_responses")
        builder = cast(Callable[..., object], module.__dict__["build_model_provider"])
        provider = cast(ModelProviderPort, builder(model_id=openai_model))
    else:
        module = _load_module("veracrawl.adapters.model_providers.local_runtime")
        builder = cast(Callable[[], object], module.__dict__["build_model_provider"])
        provider = cast(ModelProviderPort, builder())
    provider_name = cast(str, getattr(provider, "provider_name", manifest.provider_names[0]))
    model_id = cast(str, getattr(provider, "model_id", "veracrawl-local-deterministic"))
    model_version = cast(str, getattr(provider, "model_version", "1"))
    return ProductAvailabilityModelBinding(
        provider_name=provider_name,
        model_id=model_id,
        model_version=model_version,
        runtime_ref=f"model-runtime:{manifest.id}:{_slug(provider_name)}",
        port=provider,
    )


def _agent_binding(
    manifest: ProductDiscoveryBenchmarkManifest,
) -> ProductAvailabilityAgentBinding:
    module = _load_module("veracrawl.adapters.agent_frameworks.native_runtime")
    builder = cast(Callable[[], object], module.__dict__["build_agent_runtime"])
    runtime = cast(AgentRuntimePort, builder())
    framework_name = cast(str, getattr(runtime, "framework_name", manifest.framework_names[0]))
    return ProductAvailabilityAgentBinding(
        framework_name=framework_name,
        runtime_spec_id=f"agent-runtime-spec:{manifest.id}:{_slug(framework_name)}",
        runtime_ref=f"agent-runtime:{manifest.id}:{_slug(framework_name)}",
        port=runtime,
    )


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
    model_provider: str = "local",
    openai_model: str | None = None,
) -> ProductDiscoveryBenchmarkResult:
    manifest = ProductDiscoveryBenchmarkManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    state_root = out / "state"
    if state_root.exists():
        shutil.rmtree(state_root)
    out.mkdir(parents=True, exist_ok=True)
    result = run_product_discovery_benchmark(
        manifest=manifest,
        profile=profile,
        store=ReferencePersistenceStore(state_root),
        discovery_adapter_factory=_discovery_adapter_factory,
        product_adapter_factory=_product_adapter_factory,
        discovery_robots_fetcher=_fetch_discovery_robots,
        product_robots_fetcher=_fetch_product_robots,
        model_binding=_model_binding(
            manifest,
            provider_kind=model_provider,
            openai_model=openai_model,
        ),
        agent_binding=_agent_binding(manifest),
    )
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
    _write_outputs(out, result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-product-discovery")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    run.add_argument(
        "--model-provider",
        choices=["local", "openai"],
        default="local",
        help="Model provider adapter to use for framework-neutral model calls.",
    )
    run.add_argument(
        "--openai-model",
        default=None,
        help="OpenAI model id when --model-provider openai is used.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-product-discovery"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run":
            try:
                result = run_fixture(
                    Path(args.fixture_dir),
                    profile=args.profile,
                    out=Path(args.out),
                    model_provider=args.model_provider,
                    openai_model=args.openai_model,
                )
            except (OSError, ValueError, RuntimeError) as exc:
                print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
                return 1
            print(json.dumps(_summary(result), sort_keys=True))
            return 0
        return 2


def _write_outputs(out: Path, result: ProductDiscoveryBenchmarkResult) -> None:
    _write_json(out / "discovery_report.json", result.report.model_dump(mode="json"))
    _write_json(
        out / "discovered_candidates.json",
        [item.model_dump(mode="json") for item in result.candidates],
    )
    if result.derived_product_availability_manifest is not None:
        _write_json(
            out / "derived_product_availability_manifest.json",
            result.derived_product_availability_manifest.model_dump(mode="json"),
        )
    if result.product_availability_result is not None:
        product = result.product_availability_result
        _write_json(
            out / "product_availability_report.json",
            product.report.model_dump(mode="json"),
        )
        _write_json(
            out / "site_results.json",
            [item.model_dump(mode="json") for item in product.site_results],
        )
        _write_json(
            out / "field_evidence.json",
            [item.model_dump(mode="json") for item in product.field_evidence],
        )
        _write_json(
            out / "offer_records.json",
            [item.model_dump(mode="json") for item in product.offer_records],
        )
        _write_json(
            out / "offer_projection_report.json",
            product.offer_projection_report.model_dump(mode="json"),
        )
    _write_json(
        out / "ranked_offers.json",
        [item.model_dump(mode="json") for item in result.ranked_offers],
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


def _summary(result: ProductDiscoveryBenchmarkResult) -> dict[str, object]:
    report = result.report
    product = result.product_availability_result
    return {
        "ok": report.completion_result
        in {CompletenessResult.PASS, CompletenessResult.NEEDS_REVIEW},
        "fixture_id": report.fixture_id,
        "completion_result": report.completion_result.value,
        "operator_status": report.operator_status,
        "source_count": report.source_count,
        "discovered_candidate_count": len(report.discovered_candidate_refs),
        "ranked_offer_count": len(report.ranked_offer_refs),
        "blocked_source_count": len(report.blocked_source_refs),
        "product_passing_site_count": (
            len(product.report.passing_site_result_refs) if product is not None else 0
        ),
        "product_blocked_site_count": (
            len(product.report.blocked_site_result_refs) if product is not None else 0
        ),
        "field_evidence_count": (
            len(product.report.field_evidence_refs) if product is not None else 0
        ),
        "model_call_trace_count": len(report.model_call_trace_refs),
        "agent_action_trace_count": len(report.agent_action_trace_refs),
        "tool_call_trace_count": len(report.tool_call_trace_refs),
        "context_bundle_trace_count": len(report.context_bundle_trace_refs),
        "blocked_source_refs": report.blocked_source_refs,
    }


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )


def _slug(value: str) -> str:
    return value.lower().replace(" ", "-").replace("/", "-").replace(":", "-")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
