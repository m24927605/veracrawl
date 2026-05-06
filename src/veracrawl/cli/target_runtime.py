"""Target crawl runtime fixture runner CLI."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from pydantic import ValidationError

from veracrawl.contracts.target_runtime import (
    TargetAdapterBackedSourceManifest,
    TargetAdapterBackedSourceRecord,
    TargetProcessingEvidenceManifest,
    TargetProcessingEvidenceRecord,
    TargetRuntimeFixtureManifest,
    TargetRuntimeReport,
    TargetSourceCorpusManifest,
)
from veracrawl.runtime_support.logging import bootstrap_cli_logging
from veracrawl.target_runtime.runner import run_target_runtime_fixture


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _load_module(module_name: str) -> ModuleType:
    return importlib.import_module(module_name)


def _adapter_records_for(
    fixture_dir: Path,
    *,
    adapter_backed_source_ref: str,
    source_corpus_ref: str | None,
) -> tuple[TargetAdapterBackedSourceManifest, list[TargetAdapterBackedSourceRecord]]:
    if source_corpus_ref is None:
        raise ValueError("adapter-backed target runtime requires source_corpus_ref")
    adapter_manifest = TargetAdapterBackedSourceManifest.model_validate(
        _load_json_like(fixture_dir / adapter_backed_source_ref)
    )
    source_corpus = TargetSourceCorpusManifest.model_validate(
        _load_json_like(fixture_dir / source_corpus_ref)
    )
    module = _load_module("veracrawl.adapters.sources.target_runtime")
    builder = cast(
        Callable[..., list[TargetAdapterBackedSourceRecord]],
        module.__dict__["build_adapter_backed_source_records"],
    )
    return adapter_manifest, builder(
        fixture_dir=fixture_dir,
        adapter_manifest=adapter_manifest,
        source_corpus=source_corpus,
    )


def _processing_records_for(
    fixture_dir: Path,
    *,
    processing_evidence_ref: str,
    adapter_records: list[TargetAdapterBackedSourceRecord] | None,
) -> tuple[TargetProcessingEvidenceManifest, list[TargetProcessingEvidenceRecord]]:
    if not adapter_records:
        raise ValueError("processing/evidence target runtime requires adapter records")
    processing_manifest = TargetProcessingEvidenceManifest.model_validate(
        _load_json_like(fixture_dir / processing_evidence_ref)
    )
    module = _load_module("veracrawl.adapters.sources.target_processing")
    builder = cast(
        Callable[..., list[TargetProcessingEvidenceRecord]],
        module.__dict__["build_processing_evidence_records"],
    )
    return processing_manifest, builder(
        processing_manifest=processing_manifest,
        adapter_records=adapter_records,
    )


def run_fixture(fixture_dir: Path, *, profile: str, out: Path) -> TargetRuntimeReport:
    manifest = TargetRuntimeFixtureManifest.model_validate(
        _load_json_like(fixture_dir / "manifest.yaml")
    )
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    adapter_manifest: TargetAdapterBackedSourceManifest | None = None
    adapter_records: list[TargetAdapterBackedSourceRecord] | None = None
    processing_manifest: TargetProcessingEvidenceManifest | None = None
    processing_records: list[TargetProcessingEvidenceRecord] | None = None
    if manifest.adapter_backed_source_ref is not None:
        adapter_manifest, adapter_records = _adapter_records_for(
            fixture_dir,
            adapter_backed_source_ref=manifest.adapter_backed_source_ref,
            source_corpus_ref=manifest.source_corpus_ref,
        )
    if manifest.processing_evidence_ref is not None:
        processing_manifest, processing_records = _processing_records_for(
            fixture_dir,
            processing_evidence_ref=manifest.processing_evidence_ref,
            adapter_records=adapter_records,
        )
    result = run_target_runtime_fixture(
        fixture_id=manifest.id,
        scenario=manifest.scenario,
        profile=profile,
        fixture_dir=fixture_dir,
        source_corpus_ref=manifest.source_corpus_ref,
        adapter_manifest=adapter_manifest,
        adapter_records=adapter_records,
        processing_manifest=processing_manifest,
        processing_records=processing_records,
    )
    report = result.report
    if report.status != manifest.expected_status:
        raise ValueError(f"expected status {manifest.expected_status}, got {report.status}")
    if report.completion_result != manifest.expected_completion_result:
        raise ValueError(
            "expected completion result "
            f"{manifest.expected_completion_result}, got {report.completion_result}"
        )
    if report.operator_status != manifest.expected_operator_status:
        raise ValueError(
            f"expected operator status {manifest.expected_operator_status}, "
            f"got {report.operator_status}"
        )
    if report.failure_type != manifest.expected_failure_type:
        raise ValueError(
            f"expected failure type {manifest.expected_failure_type}, got {report.failure_type}"
        )
    if len(set(report.covered_patterns)) < manifest.expected_pattern_count:
        raise ValueError(
            f"expected {manifest.expected_pattern_count} patterns, "
            f"got {len(set(report.covered_patterns))}"
        )
    if len(report.source_observation_refs) < manifest.expected_source_observation_count:
        raise ValueError(
            f"expected {manifest.expected_source_observation_count} source observations, "
            f"got {len(report.source_observation_refs)}"
        )
    if len(report.source_adapter_result_refs) < manifest.expected_adapter_result_count:
        raise ValueError(
            f"expected {manifest.expected_adapter_result_count} source adapter results, "
            f"got {len(report.source_adapter_result_refs)}"
        )
    if len(report.processing_evidence_refs) < manifest.expected_processing_evidence_count:
        raise ValueError(
            f"expected {manifest.expected_processing_evidence_count} processing records, "
            f"got {len(report.processing_evidence_refs)}"
        )
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-target-runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-target-runtime"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run":
            try:
                report = run_fixture(
                    Path(args.fixture_dir), profile=args.profile, out=Path(args.out)
                )
            except (OSError, ValueError, ValidationError) as exc:
                print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
                return 1
            print(
                json.dumps(
                    {
                        "ok": True,
                        "fixture_id": report.fixture_id,
                        "status": report.status.value,
                        "completion_result": report.completion_result.value,
                        "operator_status": report.operator_status,
                    },
                    sort_keys=True,
                )
            )
            return 0
        return 2


if __name__ == "__main__":
    sys.exit(main())
