"""Demo example file lints + parses cleanly.

If someone edits ``examples/crawl/static-site-job.yaml`` and breaks
its schema, this test catches it before users see a runtime error.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from veracrawl.contracts.crawl_job import (
    CrawlJobSpec,
    ExtractionMode,
    PrivateNetworkPolicy,
)


def test_demo_static_site_job_yaml_parses_as_crawl_job_spec() -> None:
    path = Path(__file__).resolve().parents[2] / "examples" / "crawl" / "static-site-job.yaml"
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    spec = CrawlJobSpec.model_validate(raw)
    # Sanity-check the most operator-meaningful fields.
    assert spec.seed_urls[0].startswith("http://127.0.0.1")
    assert spec.private_network_policy == PrivateNetworkPolicy.ALLOW_LOOPBACK_ONLY
    assert spec.extraction.mode == ExtractionMode.NONE
    # Content hash is stable across reloads of the same YAML.
    raw2 = yaml.safe_load(path.read_text(encoding="utf-8"))
    spec2 = CrawlJobSpec.model_validate(raw2)
    assert spec.content_hash() == spec2.content_hash()
