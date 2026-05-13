"""``veracrawl-crawl`` — external crawl job runtime CLI.

Phase 1 introduced the spec parser + run-directory layout under
``--dry-run``. Phase 2 wires :class:`ExternalCrawlRunner` so the
default ``run`` invocation actually fetches.
"""

from __future__ import annotations

import argparse
import importlib
import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from veracrawl.contracts.crawl_job import (
    CrawlJobSpec,
    ExtractionMode,
    PrivateNetworkPolicy,
)
from veracrawl.external_crawl.runner import ExternalCrawlRunner
from veracrawl.runtime_support.logging import bootstrap_cli_logging

_RUN_ID_SAFE = re.compile(r"[^A-Za-z0-9_.-]+")
_DEFAULT_USER_AGENT = "veracrawl/0.1 (+https://github.com/m24927605/veracrawl)"
_DEFAULT_MAX_RESPONSE_BYTES = 2 * 1024 * 1024


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-crawl")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="Execute a crawl job from a spec file")
    run.add_argument("spec", help="Path to a CrawlJobSpec YAML or JSON file")
    run.add_argument(
        "--out",
        required=True,
        help="Run output root directory (one subdirectory per run is created)",
    )
    run.add_argument(
        "--run-id",
        default=None,
        help="Explicit run id; defaults to a slugified job id + UTC timestamp",
    )
    run.add_argument(
        "--dry-run",
        action="store_true",
        help="Lay down the run directory + stub report without fetching",
    )
    run.add_argument(
        "--user-agent",
        default=_DEFAULT_USER_AGENT,
        help=f"User-Agent header for fetches (default: {_DEFAULT_USER_AGENT!r})",
    )
    run.add_argument(
        "--max-response-bytes",
        type=int,
        default=_DEFAULT_MAX_RESPONSE_BYTES,
        help="Per-response size budget; oversize bodies fail the fetch",
    )
    run.add_argument(
        "--llm-provider",
        default=None,
        help=(
            "Python factory in 'module:callable' form returning a "
            "ModelProviderPortV2 instance. Required when the spec's "
            "extraction.mode is 'llm_assisted'."
        ),
    )
    run.add_argument(
        "--llm-model",
        default="stub-model",
        help="Model name forwarded to the provider when --llm-provider is set",
    )
    run.add_argument(
        "--ocr-language",
        default=None,
        help=(
            "OCR language hint (tesseract code, e.g. 'eng', 'chi_tra', "
            "'eng+jpn'). Overrides spec.extraction.ocr_language when set."
        ),
    )
    run.add_argument(
        "--llm-system-prompt",
        default=(
            "You extract structured fields from a single document. "
            "Every guess must include an evidence_quote that occurs "
            "verbatim in the supplied normalised text."
        ),
        help="System prompt for the LLM-assisted extractor",
    )

    return parser


def _load_spec(spec_path: Path) -> CrawlJobSpec:
    text = spec_path.read_text(encoding="utf-8")
    suffix = spec_path.suffix.lower()
    if suffix in {".yaml", ".yml"}:
        raw: Any = yaml.safe_load(text)
    elif suffix == ".json":
        raw = json.loads(text)
    else:
        # Best effort: try YAML (which is a superset of JSON) so a
        # mis-named file still works.
        raw = yaml.safe_load(text)
    if not isinstance(raw, dict):
        raise ValueError(
            f"spec file {spec_path} must contain a mapping at the top level"
        )
    return CrawlJobSpec.model_validate(raw)


def _derive_run_id(spec: CrawlJobSpec, explicit: str | None) -> str:
    if explicit is not None:
        if not explicit.strip():
            raise ValueError("--run-id must be non-empty")
        return explicit
    base = _RUN_ID_SAFE.sub("-", spec.id).strip("-") or "run"
    stamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%SZ")
    return f"{base}-{stamp}"


def _build_stub_report(spec: CrawlJobSpec, run_id: str) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "job_id": spec.id,
        "project_id": spec.project_id,
        "job_spec_hash": spec.content_hash(),
        "status": "created",
        "seed_urls": list(spec.seed_urls),
        "pages_fetched": 0,
        "pages_skipped": 0,
        "artifacts_written": 0,
        "extraction_candidates": 0,
        "evidence_packets": 0,
        "failures": [],
        "policy_denials": [],
        "replay_completeness_result": "pending",
        "created_at": datetime.now(tz=UTC).isoformat(),
    }


def _write_json_file(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8"
    )


def _resolve_factory(spec: str) -> Any:
    if ":" not in spec:
        raise ValueError(
            f"--llm-provider must be 'module:callable', got {spec!r}"
        )
    module_name, _, attr = spec.partition(":")
    module = importlib.import_module(module_name)
    factory = getattr(module, attr, None)
    if factory is None:
        raise ValueError(f"factory {attr!r} not found in module {module_name!r}")
    return factory


def _run(
    *,
    spec_path: Path,
    out_root: Path,
    run_id_override: str | None,
    dry_run: bool,
    user_agent: str,
    max_response_bytes: int,
    ocr_language: str | None,
    llm_provider_spec: str | None,
    llm_model: str,
    llm_system_prompt: str,
) -> int:
    if not spec_path.is_file():
        print(f"error: spec file not found: {spec_path}", file=sys.stderr)
        return 2

    try:
        spec = _load_spec(spec_path)
    except (ValidationError, ValueError, yaml.YAMLError, json.JSONDecodeError) as exc:
        print(f"error: invalid spec: {exc}", file=sys.stderr)
        return 3

    try:
        run_id = _derive_run_id(spec, run_id_override)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 4

    out_root.mkdir(parents=True, exist_ok=True)
    # Resolve concrete adapters dynamically so the CLI module stays
    # free of static ``veracrawl.adapters.*`` imports (architecture
    # rule enforced by ``tests/contract/*_import_boundaries.py``).
    store_module = importlib.import_module(
        "veracrawl.adapters.object_stores.local_fs_crawl_artifact_store"
    )
    fetcher_module = importlib.import_module(
        "veracrawl.adapters.network.httpx_crawl_fetcher"
    )
    # PDF text extraction is opt-in via the ``pdf`` extra. Soft-import
    # so an install without it still runs the rest of the pipeline;
    # PDFs in that case fall back to ``needs_review``. The ``pdf-ocr``
    # extra adds an OCR fallback for image-only PDFs; when both are
    # available we wire a HybridPdfTextExtractor automatically.
    try:
        pdf_module: Any | None = importlib.import_module(
            "veracrawl.adapters.document.pypdf_text_extractor"
        )
    except ImportError:
        pdf_module = None
    try:
        ocr_module: Any | None = importlib.import_module(
            "veracrawl.adapters.document.pytesseract_pdf_ocr_extractor"
        )
        hybrid_module: Any | None = importlib.import_module(
            "veracrawl.adapters.document.hybrid_pdf_text_extractor"
        )
    except ImportError:
        ocr_module = None
        hybrid_module = None
    rate_limiter_module = importlib.import_module(
        "veracrawl.adapters.network.aimd_rate_limiter"
    )
    store = store_module.LocalFsCrawlArtifactStore(root=out_root, run_id=run_id)
    spec_payload = spec.model_dump(mode="json")
    _write_json_file(store.run_root / "reports" / "job_spec.json", spec_payload)

    if dry_run:
        _write_json_file(
            store.run_root / "reports" / "run_report.json",
            _build_stub_report(spec, run_id),
        )
        print(str(store.run_root))
        return 0

    fetcher = fetcher_module.HttpxCrawlFetcher(
        user_agent=user_agent,
        max_response_bytes=max_response_bytes,
        allow_loopback=(
            spec.private_network_policy == PrivateNetworkPolicy.ALLOW_LOOPBACK_ONLY
        ),
    )
    resolved_ocr_language = (
        ocr_language if ocr_language is not None else spec.extraction.ocr_language
    )
    pdf_extractor: Any | None = None
    if pdf_module is not None:
        primary = pdf_module.PypdfTextExtractor()
        if ocr_module is not None and hybrid_module is not None:
            pdf_extractor = hybrid_module.HybridPdfTextExtractor(
                primary=primary,
                ocr=ocr_module.PytesseractPdfOcrExtractor(
                    language=resolved_ocr_language
                ),
            )
        else:
            pdf_extractor = primary
    rate_limiter = rate_limiter_module.InMemoryAimdLimiter()

    extractors_kwarg: dict[str, Any] = {}
    if spec.extraction.mode == ExtractionMode.LLM_ASSISTED:
        if llm_provider_spec is None:
            print(
                "error: extraction.mode=llm_assisted but --llm-provider was not given",
                file=sys.stderr,
            )
            return 5
        try:
            factory = _resolve_factory(llm_provider_spec)
            provider = factory()
        except (ValueError, ImportError) as exc:
            print(f"error: --llm-provider failed: {exc}", file=sys.stderr)
            return 6
        llm_module = importlib.import_module(
            "veracrawl.adapters.model_providers.llm_assisted_extractor"
        )
        provider_callable_module = importlib.import_module(
            "veracrawl.adapters.model_providers.provider_backed_llm_callable"
        )
        callable_ = provider_callable_module.ProviderBackedLlmCallable(
            provider=provider,
            model_name=llm_model,
            system_prompt=llm_system_prompt,
        )
        extractor = llm_module.LlmAssistedExtractor(
            callable=callable_,
            provider_ref=llm_provider_spec,
            schema_ref="schema:external-crawl/llm-assisted/v1",
        )
        extractors_kwarg["extractors"] = [extractor]

    runner = ExternalCrawlRunner(
        spec=spec,
        store=store,
        run_root=store.run_root,
        fetcher=fetcher,
        pdf_extractor=pdf_extractor,
        rate_limiter=rate_limiter,
        **extractors_kwarg,
    )
    runner.run()
    print(str(store.run_root))
    return 0


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-crawl"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run":
            return _run(
                spec_path=Path(args.spec),
                out_root=Path(args.out),
                run_id_override=args.run_id,
                dry_run=args.dry_run,
                user_agent=args.user_agent,
                max_response_bytes=args.max_response_bytes,
                ocr_language=args.ocr_language,
                llm_provider_spec=args.llm_provider,
                llm_model=args.llm_model,
                llm_system_prompt=args.llm_system_prompt,
            )
        return 2


if __name__ == "__main__":
    sys.exit(main())
