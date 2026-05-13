"""Tests for OCR language plumbing (job spec → CLI flag → extractor)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from veracrawl.adapters.document.pytesseract_pdf_ocr_extractor import (
    PytesseractPdfOcrExtractor,
)
from veracrawl.cli.crawl import main as crawl_main
from veracrawl.contracts.crawl_job import (
    CrawlJobSpec,
    ExtractionMode,
    ExtractionSpec,
)


def test_extraction_spec_defaults_ocr_language_to_eng() -> None:
    spec = ExtractionSpec(
        mode=ExtractionMode.NONE,
        schema_ref=None,
        exploratory_schema_allowed=False,
    )
    assert spec.ocr_language == "eng"


def test_extraction_spec_accepts_custom_language() -> None:
    spec = ExtractionSpec(
        mode=ExtractionMode.DETERMINISTIC,
        schema_ref=None,
        exploratory_schema_allowed=False,
        ocr_language="chi_tra+eng",
    )
    assert spec.ocr_language == "chi_tra+eng"


def test_extraction_spec_rejects_blank_ocr_language() -> None:
    with pytest.raises(ValidationError, match="ocr_language"):
        ExtractionSpec(
            mode=ExtractionMode.NONE,
            schema_ref=None,
            exploratory_schema_allowed=False,
            ocr_language="   ",
        )


def test_pytesseract_extractor_constructor_accepts_language() -> None:
    extractor = PytesseractPdfOcrExtractor(language="chi_tra")
    # The language is stored privately; test through behaviour-adjacent
    # invariant: constructing with a valid language must succeed.
    assert extractor is not None


def test_pytesseract_extractor_rejects_blank_language() -> None:
    with pytest.raises(ValueError, match="language"):
        PytesseractPdfOcrExtractor(language="  ")


def _spec_dict(ocr_language: str = "eng") -> dict[str, object]:
    return {
        "id": "job:ocr-lang",
        "project_id": "project:ocr",
        "objective": "ocr language plumbing test",
        "seed_urls": ["https://demo.example/"],
        "allowed_domains": ["demo.example"],
        "denied_domains": [],
        "max_depth": 1,
        "max_pages": 5,
        "max_runtime_seconds": 30,
        "per_origin_concurrency": 1,
        "rate_limit": {"requests_per_minute": 30, "crawl_delay_seconds": None},
        "source_adapters": ["http"],
        "robots_policy": "obey",
        "private_network_policy": "deny",
        "artifact_policy": {
            "store_raw_html": True,
            "store_headers": True,
            "store_screenshots": False,
            "store_documents": True,
        },
        "extraction": {
            "mode": "none",
            "schema_ref": None,
            "exploratory_schema_allowed": False,
            "ocr_language": ocr_language,
        },
        "output": {
            "format": "jsonl",
            "include_raw_refs": True,
            "include_evidence": True,
        },
    }


def test_cli_dry_run_round_trips_ocr_language_from_spec(tmp_path: Path) -> None:
    spec_path = tmp_path / "job.yaml"
    spec_path.write_text(
        yaml.safe_dump(_spec_dict(ocr_language="jpn")), encoding="utf-8"
    )
    out_dir = tmp_path / "runs"
    exit_code = crawl_main(
        ["run", str(spec_path), "--out", str(out_dir), "--dry-run"]
    )
    assert exit_code == 0
    run_root = next(out_dir.iterdir())
    spec_back = CrawlJobSpec.model_validate(
        yaml.safe_load((run_root / "reports" / "job_spec.json").read_text())
    )
    assert spec_back.extraction.ocr_language == "jpn"


def test_extraction_spec_minimal_yaml_parses_without_ocr_language() -> None:
    # Backwards-compat: older job specs that don't declare
    # ``ocr_language`` keep working (default applies).
    payload = _spec_dict()
    payload["extraction"] = {  # drop ocr_language
        "mode": "none",
        "schema_ref": None,
        "exploratory_schema_allowed": False,
    }
    spec = CrawlJobSpec.model_validate(payload)
    assert spec.extraction.ocr_language == "eng"
