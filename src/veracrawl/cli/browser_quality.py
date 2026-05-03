"""Browser quality benchmark CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
from pathlib import Path
from typing import Any, cast

from veracrawl.benchmarks.browser_quality import (
    BrowserQualityCorpusResult,
    run_browser_quality_corpus,
)
from veracrawl.contracts.browser import BrowserSandboxPolicy
from veracrawl.contracts.browser_quality import (
    BrowserQualityCorpusManifest,
    BrowserQualityTargetSpec,
)
from veracrawl.contracts.enums import BrowserSideEffectClass
from veracrawl.fetch.network_acquisition import build_network_request
from veracrawl.ports.browser import BrowserSourceAdapterPort
from veracrawl.ports.network import NetworkSourceAdapterPort
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _http_adapter_factory(
    fixture_ref: str,
    target: BrowserQualityTargetSpec,
) -> NetworkSourceAdapterPort:
    request = build_network_request(
        fixture_id=fixture_ref,
        target_url=target.target_url,
        policy_decision_refs=[f"policy:{fixture_ref}:network"],
        size_budget_bytes=131072,
        timeout_ms=target.max_runtime_ms,
    )
    adapter_module = importlib.import_module("veracrawl.adapters.network.stdlib_http")
    return cast(NetworkSourceAdapterPort, adapter_module.StdlibHttpSourceAdapter(request))


def _browser_adapter_factory(
    adapter_kind: str,
    fixture_ref: str,
    target: BrowserQualityTargetSpec,
    sandbox_policy: BrowserSandboxPolicy,
) -> BrowserSourceAdapterPort:
    if adapter_kind == "deterministic":
        adapter_module = importlib.import_module("veracrawl.adapters.browser.deterministic")
        return cast(
            BrowserSourceAdapterPort,
            adapter_module.DeterministicBrowserObservationAdapter(
                fixture_id=fixture_ref,
                target_url=target.target_url,
                sandbox_policy=sandbox_policy,
                side_effect_class=target.side_effect_class,
                rendered_text=" ".join(target.browser_required_fragments),
            ),
        )
    if adapter_kind == "playwright":
        adapter_module = importlib.import_module("veracrawl.adapters.browser.playwright")
        return cast(
            BrowserSourceAdapterPort,
            adapter_module.PlaywrightBrowserObservationAdapter(
                fixture_id=fixture_ref,
                target_url=target.target_url,
                sandbox_policy=sandbox_policy,
                side_effect_class=BrowserSideEffectClass.READ_ONLY,
                wait_for_text_fragments=target.browser_required_fragments,
            ),
        )
    raise ValueError(f"unsupported browser adapter: {adapter_kind}")


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
    browser_adapter: str,
) -> BrowserQualityCorpusResult:
    manifest = BrowserQualityCorpusManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    state_root = out / "state"
    if state_root.exists():
        shutil.rmtree(state_root)
    result = run_browser_quality_corpus(
        manifest=manifest,
        profile=profile,
        store=ReferencePersistenceStore(state_root),
        http_adapter_factory=_http_adapter_factory,
        browser_adapter_factory=lambda fixture_ref, target, sandbox: _browser_adapter_factory(
            browser_adapter,
            fixture_ref,
            target,
            sandbox,
        ),
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


def _write_outputs(out: Path, result: BrowserQualityCorpusResult) -> None:
    out.mkdir(parents=True, exist_ok=True)
    (out / "browser_quality_report.json").write_text(
        json.dumps(result.report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "browser_quality_observations.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.observations],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "browser_quality_deltas.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.deltas],
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
                "target_count": result.report.target_count,
                "browser_required_pass_count": (
                    result.report.browser_required_pass_count
                ),
                "recovered_fragment_count": result.report.recovered_fragment_count,
                "http_only_missing_count": result.report.http_only_missing_count,
                "dom_artifact_count": len(result.report.dom_artifact_refs),
                "screenshot_artifact_count": len(result.report.screenshot_artifact_refs),
                "replay_bundle_count": len(result.report.replay_bundle_refs),
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-browser-quality-benchmark")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="quality")
    run.add_argument("--browser-adapter", choices=["deterministic", "playwright"], required=True)
    run.add_argument("--out", required=True)
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
                browser_adapter=args.browser_adapter,
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
                    "target_count": report.target_count,
                    "browser_required_pass_count": report.browser_required_pass_count,
                    "recovered_fragment_count": report.recovered_fragment_count,
                },
                sort_keys=True,
            )
        )
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
