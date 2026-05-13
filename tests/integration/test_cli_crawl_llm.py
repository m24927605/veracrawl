"""End-to-end CLI tests for the LLM-assisted extraction path.

Uses a stub provider so the integration test never touches a real
LLM. Verifies:

* ``extraction.mode=llm_assisted`` without ``--llm-provider`` fails;
* with a valid ``--llm-provider`` factory, the runner persists
  ``events/model_calls.jsonl`` and an evidence-bearing extraction
  candidate.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml

from tests.integration._static_site import serve_static_site
from veracrawl.cli.crawl import main as crawl_main


@pytest.fixture
def site_url() -> Iterator[str]:
    yield from serve_static_site()


def _spec(site_url: str) -> dict[str, object]:
    return {
        "id": "job:cli-llm",
        "project_id": "project:cli-llm",
        "objective": "Exercise the LLM-assisted extraction CLI wiring",
        "seed_urls": [site_url + "/page-a.html"],
        "allowed_domains": ["127.0.0.1"],
        "denied_domains": [],
        "max_depth": 0,
        "max_pages": 1,
        "max_runtime_seconds": 30,
        "per_origin_concurrency": 1,
        "rate_limit": {"requests_per_minute": 60, "crawl_delay_seconds": 0.0},
        "source_adapters": ["http"],
        "robots_policy": "warn",
        "private_network_policy": "allow_loopback_only",
        "artifact_policy": {
            "store_raw_html": True,
            "store_headers": True,
            "store_screenshots": False,
            "store_documents": False,
        },
        "extraction": {
            "mode": "llm_assisted",
            "schema_ref": "schema:external-crawl/llm-assisted/v1",
            "exploratory_schema_allowed": True,
        },
        "output": {
            "format": "jsonl",
            "include_raw_refs": True,
            "include_evidence": True,
        },
    }


def test_llm_assisted_mode_without_provider_fails(
    tmp_path: Path, site_url: str
) -> None:
    spec_path = tmp_path / "job.yaml"
    spec_path.write_text(yaml.safe_dump(_spec(site_url)), encoding="utf-8")
    out_dir = tmp_path / "runs"
    exit_code = crawl_main(
        ["run", str(spec_path), "--out", str(out_dir), "--run-id", "llm-fail"]
    )
    assert exit_code != 0


def test_llm_assisted_mode_with_stub_provider_emits_model_call_trace(
    tmp_path: Path, site_url: str
) -> None:
    spec_path = tmp_path / "job.yaml"
    spec_path.write_text(yaml.safe_dump(_spec(site_url)), encoding="utf-8")
    out_dir = tmp_path / "runs"

    exit_code = crawl_main(
        [
            "run",
            str(spec_path),
            "--out",
            str(out_dir),
            "--run-id",
            "llm-ok",
            "--llm-provider",
            "tests.integration._stub_llm_provider:make_provider",
            "--llm-model",
            "stub-model",
        ]
    )
    assert exit_code == 0

    run_root = out_dir / "llm-ok"
    candidates_path = run_root / "outputs" / "extraction_candidates.jsonl"
    model_calls_path = run_root / "events" / "model_calls.jsonl"

    assert candidates_path.is_file()
    candidates = [
        json.loads(line)
        for line in candidates_path.read_text("utf-8").splitlines()
        if line.strip()
    ]
    assert candidates, "stub provider's headline should produce a candidate"
    assert candidates[0]["fields"]["headline"] == "Page A"

    assert model_calls_path.is_file()
    traces = [
        json.loads(line)
        for line in model_calls_path.read_text("utf-8").splitlines()
        if line.strip()
    ]
    assert traces, "every LLM call must produce a ModelCallTrace"
    assert traces[0]["status"] == "ok"
