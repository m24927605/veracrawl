"""End-to-end CLI test: ``veracrawl-crawl run`` against the local static site.

Validates the goal-doc acceptance criterion: invoking the CLI on a
YAML spec writes raw artifacts, output JSONL files, an event log,
and a final run report — all without ``--dry-run``.
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


def test_cli_crawl_run_executes_and_writes_outputs(
    tmp_path: Path, site_url: str
) -> None:
    spec = {
        "id": "job:cli-e2e",
        "project_id": "project:cli-e2e",
        "objective": "End-to-end CLI crawl over the static site fixture",
        "seed_urls": [site_url + "/"],
        "allowed_domains": ["127.0.0.1"],
        "denied_domains": [],
        "max_depth": 2,
        "max_pages": 10,
        "max_runtime_seconds": 30,
        "per_origin_concurrency": 1,
        "rate_limit": {"requests_per_minute": 120, "crawl_delay_seconds": 0.0},
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
            "mode": "none",
            "schema_ref": None,
            "exploratory_schema_allowed": False,
        },
        "output": {
            "format": "jsonl",
            "include_raw_refs": True,
            "include_evidence": False,
        },
    }
    spec_path = tmp_path / "job.yaml"
    spec_path.write_text(yaml.safe_dump(spec, sort_keys=True), encoding="utf-8")
    out_root = tmp_path / "runs"

    exit_code = crawl_main(
        [
            "run",
            str(spec_path),
            "--out",
            str(out_root),
            "--run-id",
            "cli-e2e",
        ]
    )
    assert exit_code == 0

    run_root = out_root / "cli-e2e"
    report_path = run_root / "reports" / "run_report.json"
    documents_path = run_root / "outputs" / "documents.jsonl"
    links_path = run_root / "outputs" / "links.jsonl"
    events_path = run_root / "events" / "frontier.jsonl"

    assert report_path.is_file()
    assert documents_path.is_file()
    assert links_path.is_file()
    assert events_path.is_file()

    report = json.loads(report_path.read_text("utf-8"))
    assert report["status"] == "completed"
    # 3 HTML + 1 linked text doc.
    assert report["pages_fetched"] == 4
    assert report["job_id"] == "job:cli-e2e"

    raw_html_dir = run_root / "artifacts" / "raw-html"
    assert any(p.suffix == ".html" for p in raw_html_dir.iterdir())
