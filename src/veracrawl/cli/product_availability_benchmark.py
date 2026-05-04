"""Product price and availability benchmark CLI."""

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
    ProductAvailabilityBenchmarkResult,
    ProductAvailabilityModelBinding,
    run_product_availability_benchmark,
)
from veracrawl.benchmarks.real_world import RobotsFetchResult
from veracrawl.contracts.browser import BrowserSandboxPolicy
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.product_availability import (
    ProductAvailabilityBenchmarkManifest,
    ProductAvailabilityTargetSpec,
)
from veracrawl.fetch.network_acquisition import build_network_request
from veracrawl.ports.agent_runtime import AgentRuntimePort, ModelProviderPort
from veracrawl.ports.browser import BrowserSourceAdapterPort
from veracrawl.ports.network import NetworkSourceAdapterPort
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


def _adapter_factory(
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


def _fetch_robots(target: ProductAvailabilityTargetSpec) -> RobotsFetchResult:
    request = urllib.request.Request(
        target.robots_url,
        headers={"User-Agent": _USER_AGENT},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=target.timeout_ms / 1000) as response:
            body = response.read().decode("utf-8", errors="replace")
            return RobotsFetchResult(status_code=int(response.status), body_text=body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return RobotsFetchResult(status_code=int(exc.code), body_text=body)
    except urllib.error.URLError as exc:
        raise OSError(str(exc)) from exc


def _browser_adapter_factory(
    fixture_id: str,
    target: ProductAvailabilityTargetSpec,
    sandbox: BrowserSandboxPolicy,
) -> BrowserSourceAdapterPort:
    adapter_module = importlib.import_module("veracrawl.adapters.browser.playwright")
    adapter = adapter_module.PlaywrightBrowserObservationAdapter(
        fixture_id=fixture_id,
        target_url=target.target_url,
        sandbox_policy=sandbox,
        wait_for_text_fragments=(),
    )
    return cast(BrowserSourceAdapterPort, adapter)


def _model_binding(
    manifest: ProductAvailabilityBenchmarkManifest,
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
    manifest: ProductAvailabilityBenchmarkManifest,
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
    browser_fallback: bool = False,
    browser_source_required: bool = False,
) -> ProductAvailabilityBenchmarkResult:
    manifest = ProductAvailabilityBenchmarkManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    state_root = out / "state"
    if state_root.exists():
        shutil.rmtree(state_root)
    out.mkdir(parents=True, exist_ok=True)
    result = run_product_availability_benchmark(
        manifest=manifest,
        profile=profile,
        store=ReferencePersistenceStore(state_root),
        adapter_factory=_adapter_factory,
        robots_fetcher=_fetch_robots,
        model_binding=_model_binding(
            manifest,
            provider_kind=model_provider,
            openai_model=openai_model,
        ),
        agent_binding=_agent_binding(manifest),
        browser_adapter_factory=(
            _browser_adapter_factory if browser_fallback or browser_source_required else None
        ),
        browser_source_required=browser_source_required,
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

    _write_json(out / "run_report.json", report.model_dump(mode="json"))
    _write_json(
        out / "site_results.json",
        [item.model_dump(mode="json") for item in result.site_results],
    )
    _write_json(
        out / "field_evidence.json",
        [item.model_dump(mode="json") for item in result.field_evidence],
    )
    _write_json(
        out / "offer_records.json",
        [item.model_dump(mode="json") for item in result.offer_records],
    )
    _write_json(
        out / "offer_projection_report.json",
        result.offer_projection_report.model_dump(mode="json"),
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
    parser = argparse.ArgumentParser(prog="veracrawl-product-availability-benchmark")
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
    run.add_argument(
        "--browser-fallback",
        action="store_true",
        help=(
            "Escalate HTTP-missing product identity, price, or availability to a "
            "read-only Playwright DOM observation adapter."
        ),
    )
    run.add_argument(
        "--browser-source-required",
        action="store_true",
        help=(
            "Require accepted product field evidence to come from a read-only "
            "browser DOM observation."
        ),
    )
    return parser


def main(argv: list[str] | None = None) -> int:
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
                browser_fallback=args.browser_fallback,
                browser_source_required=args.browser_source_required,
            )
        except (OSError, ValueError, RuntimeError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
            return 1
        print(json.dumps(_summary(result), sort_keys=True))
        return 0
    return 2


def _summary(result: ProductAvailabilityBenchmarkResult) -> dict[str, object]:
    report = result.report
    return {
        "ok": report.completion_result
        in {CompletenessResult.PASS, CompletenessResult.NEEDS_REVIEW},
        "fixture_id": report.fixture_id,
        "completion_result": report.completion_result.value,
        "operator_status": report.operator_status,
        "site_count": len(report.site_result_refs),
        "passing_site_count": len(report.passing_site_result_refs),
        "blocked_site_count": len(report.blocked_site_result_refs),
        "field_evidence_count": len(report.field_evidence_refs),
        "price_evidence_count": len(report.price_evidence_refs),
        "availability_evidence_count": len(report.availability_evidence_refs),
        "delivery_evidence_count": len(report.delivery_evidence_refs),
        "shipping_fee_evidence_count": len(report.shipping_fee_evidence_refs),
        "offer_record_count": len(report.offer_record_refs),
        "sortable_offer_count": len(result.offer_projection_report.sortable_offer_refs),
        "offer_projection_operator_status": (result.offer_projection_report.operator_status),
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
