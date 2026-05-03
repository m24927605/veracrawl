"""Real-world benchmark corpus runner CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, cast

from veracrawl.benchmarks.real_world import (
    RealWorldBenchmarkResult,
    RobotsFetchResult,
    run_real_world_benchmark_corpus,
)
from veracrawl.contracts.real_world_benchmark import (
    RealWorldBenchmarkCorpusManifest,
    RealWorldBenchmarkSiteSpec,
)
from veracrawl.fetch.network_acquisition import build_network_request
from veracrawl.ports.network import NetworkSourceAdapterPort
from veracrawl.runtime_support.persistence_store import ReferencePersistenceStore

_USER_AGENT = "VeraCrawl-real-benchmark/1"


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _adapter_factory(
    fixture_id: str,
    site: RealWorldBenchmarkSiteSpec,
) -> NetworkSourceAdapterPort:
    request = build_network_request(
        fixture_id=fixture_id,
        target_url=site.target_url,
        policy_decision_refs=[f"policy:{fixture_id}:network"],
        size_budget_bytes=site.size_budget_bytes,
        timeout_ms=site.timeout_ms,
    )
    adapter_module = importlib.import_module("veracrawl.adapters.network.stdlib_http")
    return cast(NetworkSourceAdapterPort, adapter_module.StdlibHttpSourceAdapter(request))


def _fetch_robots(site: RealWorldBenchmarkSiteSpec) -> RobotsFetchResult:
    request = urllib.request.Request(
        site.robots_url,
        headers={"User-Agent": _USER_AGENT},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=site.timeout_ms / 1000) as response:
            body = response.read().decode("utf-8", errors="replace")
            return RobotsFetchResult(status_code=int(response.status), body_text=body)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return RobotsFetchResult(status_code=int(exc.code), body_text=body)
    except urllib.error.URLError as exc:
        raise OSError(str(exc)) from exc


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
) -> RealWorldBenchmarkResult:
    manifest = RealWorldBenchmarkCorpusManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    state_root = out / "state"
    if state_root.exists():
        shutil.rmtree(state_root)
    result = run_real_world_benchmark_corpus(
        manifest=manifest,
        profile=profile,
        store=ReferencePersistenceStore(state_root),
        adapter_factory=_adapter_factory,
        robots_fetcher=_fetch_robots,
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

    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    (out / "site_observations.json").write_text(
        json.dumps(
            [item.model_dump(mode="json") for item in result.observations],
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out / "summary.json").write_text(
        json.dumps(
            {
                "ok": report.completion_result == manifest.expected_completion_result,
                "fixture_id": manifest.id,
                "completion_result": report.completion_result.value,
                "operator_status": report.operator_status,
                "site_count": len(result.observations),
                "artifact_count": len(report.artifact_refs),
                "replay_bundle_count": len(report.replay_bundle_refs),
            },
            sort_keys=True,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-real-benchmark")
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
                    "site_count": len(result.observations),
                },
                sort_keys=True,
            )
        )
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
