"""Phase 1 smoke test: static-site harness + ``veracrawl-crawl run`` CLI.

The actual crawl loop lands in Phase 2; this test only proves the
harness works and the CLI lays down the expected directory tree when
pointed at a real (local) URL.
"""

from __future__ import annotations

import json
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest
import yaml

from tests.integration._static_site import serve_static_site
from veracrawl.cli.crawl import main as crawl_main


@pytest.fixture
def static_site_url() -> Iterator[str]:
    yield from serve_static_site()


def test_static_site_serves_root_page(static_site_url: str) -> None:
    with urllib.request.urlopen(static_site_url + "/") as response:
        body = response.read().decode("utf-8")
    assert "Static Site Fixture" in body


def test_static_site_serves_sitemap(static_site_url: str) -> None:
    with urllib.request.urlopen(static_site_url + "/sitemap.xml") as response:
        body = response.read().decode("utf-8")
    assert "<urlset" in body
    assert "page-a.html" in body


def test_crawl_cli_accepts_local_static_site_spec(
    tmp_path: Path, static_site_url: str
) -> None:
    spec = {
        "id": "job:static-site",
        "project_id": "project:demo",
        "objective": "Smoke-test the external crawl CLI skeleton",
        "seed_urls": [static_site_url + "/"],
        "allowed_domains": ["127.0.0.1"],
        "denied_domains": [],
        "max_depth": 1,
        "max_pages": 5,
        "max_runtime_seconds": 30,
        "per_origin_concurrency": 1,
        "rate_limit": {"requests_per_minute": 60, "crawl_delay_seconds": 0.0},
        "source_adapters": ["http"],
        "robots_policy": "obey",
        "private_network_policy": "deny",
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
            "static-site-smoke",
            "--dry-run",
        ]
    )

    assert exit_code == 0
    run_root = out_root / "static-site-smoke"
    report_path = run_root / "reports" / "run_report.json"
    assert report_path.is_file()
    report = json.loads(report_path.read_text("utf-8"))
    assert report["job_id"] == "job:static-site"
    assert report["status"] == "created"
