"""Official ecommerce API benchmark CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any, cast

from veracrawl.benchmarks.ecommerce_official_api import (
    EcommerceOfficialApiBenchmarkResult,
    run_ecommerce_official_api_benchmark,
)
from veracrawl.contracts.ecommerce_official_api import (
    EcommerceOfficialApiBenchmarkManifest,
    EcommerceOfficialApiTargetSpec,
)
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.ports.ecommerce_official_api import EcommerceOfficialApiAdapterPort
from veracrawl.runtime_support.logging import bootstrap_cli_logging


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


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


def _adapter_factory(target: EcommerceOfficialApiTargetSpec) -> EcommerceOfficialApiAdapterPort:
    if target.platform == "amazon":
        module = importlib.import_module("veracrawl.adapters.official_apis.amazon")
        adapter_cls = cast(type[object], module.__dict__["AmazonCreatorsApiAdapter"])
        return cast(EcommerceOfficialApiAdapterPort, adapter_cls())
    if target.platform == "ebay":
        module = importlib.import_module("veracrawl.adapters.official_apis.ebay")
        adapter_cls = cast(type[object], module.__dict__["EbayBrowseApiAdapter"])
        return cast(EcommerceOfficialApiAdapterPort, adapter_cls())
    raise ValueError(f"unsupported official ecommerce API platform: {target.platform}")


def run_fixture(
    fixture_dir: Path,
    *,
    profile: str,
    out: Path,
    dotenv: Path | None = None,
    require_pass: bool = False,
) -> EcommerceOfficialApiBenchmarkResult:
    _load_dotenv(dotenv)
    manifest = EcommerceOfficialApiBenchmarkManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    result = run_ecommerce_official_api_benchmark(
        manifest=manifest,
        profile=profile,
        adapter_factory=_adapter_factory,
    )
    _write_outputs(out, result)
    if require_pass and result.report.completion_result != CompletenessResult.PASS:
        raise ValueError(
            f"fixture {manifest.id} did not pass: {result.report.completion_result.value}"
        )
    return result


def _write_outputs(out: Path, result: EcommerceOfficialApiBenchmarkResult) -> None:
    out.mkdir(parents=True, exist_ok=True)
    _write_json(out / "run_report.json", result.report.model_dump(mode="json"))
    _write_json(
        out / "site_results.json",
        [item.model_dump(mode="json") for item in result.site_results],
    )
    _write_json(
        out / "field_evidence.json",
        [item.model_dump(mode="json") for item in result.field_evidence],
    )
    _write_json(
        out / "source_fetches.json",
        [item.model_dump(mode="json") for item in result.source_fetches],
    )
    _write_json(
        out / "redacted_artifacts.json",
        [item.model_dump(mode="json") for item in result.redacted_artifacts],
    )
    _write_json(
        out / "authorized_sources.json",
        [item.model_dump(mode="json") for item in result.authorized_sources],
    )
    _write_json(
        out / "summary.json",
        {
            "ok": result.report.completion_result == CompletenessResult.PASS,
            "fixture_id": result.report.fixture_id,
            "completion_result": result.report.completion_result.value,
            "operator_status": result.report.operator_status,
            "target_site_count": result.report.target_site_count,
            "passing_site_count": len(result.report.passing_site_result_refs),
            "blocked_site_count": len(result.report.blocked_site_result_refs),
            "field_evidence_count": len(result.field_evidence),
            "authorized_source_count": len(result.authorized_sources),
            "source_fetch_count": len(result.source_fetches),
        },
    )


def _write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-ecommerce-official-api")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run-live")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    run.add_argument("--dotenv")
    run.add_argument("--require-pass", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-ecommerce-official-api"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run-live":
            try:
                result = run_fixture(
                    Path(args.fixture_dir),
                    profile=args.profile,
                    out=Path(args.out),
                    dotenv=Path(args.dotenv) if args.dotenv else None,
                    require_pass=args.require_pass,
                )
            except (OSError, RuntimeError, ValueError) as exc:
                print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
                return 1
            report = result.report
            print(
                json.dumps(
                    {
                        "ok": report.completion_result == CompletenessResult.PASS,
                        "fixture_id": report.fixture_id,
                        "completion_result": report.completion_result.value,
                        "operator_status": report.operator_status,
                        "passing_site_count": len(report.passing_site_result_refs),
                        "blocked_site_count": len(report.blocked_site_result_refs),
                    },
                    sort_keys=True,
                )
            )
            return 0
        return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
