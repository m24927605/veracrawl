"""Unit tests for the ``veracrawl-crawl`` CLI skeleton.

Phase 1 scope: parse the CrawlJobSpec YAML/JSON, lay down the run
directory tree, persist the spec + a stub run report. Network and
fetching are wired in Phase 2.
"""

from __future__ import annotations

import json
from pathlib import Path

import yaml

from veracrawl.cli.crawl import main as crawl_main

_VALID_SPEC: dict[str, object] = {
    "id": "job:demo",
    "project_id": "project:demo",
    "objective": "Discover product pages on demo.example",
    "seed_urls": ["https://demo.example/"],
    "allowed_domains": ["demo.example"],
    "denied_domains": [],
    "max_depth": 2,
    "max_pages": 50,
    "max_runtime_seconds": 600,
    "per_origin_concurrency": 2,
    "rate_limit": {"requests_per_minute": 30, "crawl_delay_seconds": 1.0},
    "source_adapters": ["http", "sitemap"],
    "robots_policy": "obey",
    "private_network_policy": "deny",
    "artifact_policy": {
        "store_raw_html": True,
        "store_headers": True,
        "store_screenshots": False,
        "store_documents": True,
    },
    "extraction": {
        "mode": "deterministic",
        "schema_ref": None,
        "exploratory_schema_allowed": False,
    },
    "output": {
        "format": "jsonl",
        "include_raw_refs": True,
        "include_evidence": True,
    },
}


def _write_yaml(path: Path, payload: dict[str, object]) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=True), encoding="utf-8")


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_run_with_valid_yaml_spec_creates_run_directory(tmp_path: Path) -> None:
    spec_path = tmp_path / "job.yaml"
    out_dir = tmp_path / "runs"
    _write_yaml(spec_path, _VALID_SPEC)

    exit_code = crawl_main(
        ["run", str(spec_path), "--out", str(out_dir), "--dry-run"]
    )

    assert exit_code == 0
    runs = list(out_dir.iterdir())
    assert len(runs) == 1
    run_root = runs[0]
    for child in ("artifacts", "reports", "events", "outputs"):
        assert (run_root / child).is_dir(), child


def test_run_persists_job_spec_and_stub_report(tmp_path: Path) -> None:
    spec_path = tmp_path / "job.yaml"
    out_dir = tmp_path / "runs"
    _write_yaml(spec_path, _VALID_SPEC)

    crawl_main(["run", str(spec_path), "--out", str(out_dir), "--dry-run"])

    run_root = next(out_dir.iterdir())
    spec_artifact = run_root / "reports" / "job_spec.json"
    report_artifact = run_root / "reports" / "run_report.json"

    assert spec_artifact.is_file()
    assert report_artifact.is_file()

    persisted_spec = json.loads(spec_artifact.read_text("utf-8"))
    assert persisted_spec["id"] == "job:demo"

    report = json.loads(report_artifact.read_text("utf-8"))
    assert report["job_id"] == "job:demo"
    assert report["job_spec_hash"], "job_spec_hash must be present"
    assert report["status"] == "created"
    assert report["pages_fetched"] == 0
    assert report["seed_urls"] == ["https://demo.example/"]


def test_run_accepts_json_spec(tmp_path: Path) -> None:
    spec_path = tmp_path / "job.json"
    out_dir = tmp_path / "runs"
    _write_json(spec_path, _VALID_SPEC)

    assert (
        crawl_main(["run", str(spec_path), "--out", str(out_dir), "--dry-run"]) == 0
    )
    assert any(out_dir.iterdir())


def test_run_with_explicit_run_id(tmp_path: Path) -> None:
    spec_path = tmp_path / "job.yaml"
    out_dir = tmp_path / "runs"
    _write_yaml(spec_path, _VALID_SPEC)

    exit_code = crawl_main(
        [
            "run",
            str(spec_path),
            "--out",
            str(out_dir),
            "--run-id",
            "custom-run",
            "--dry-run",
        ]
    )

    assert exit_code == 0
    assert (out_dir / "custom-run").is_dir()


def test_run_missing_spec_file_returns_nonzero(tmp_path: Path) -> None:
    exit_code = crawl_main(
        [
            "run",
            str(tmp_path / "missing.yaml"),
            "--out",
            str(tmp_path / "runs"),
            "--dry-run",
        ]
    )
    assert exit_code != 0


def test_run_invalid_spec_returns_nonzero(tmp_path: Path) -> None:
    bad = dict(_VALID_SPEC)
    bad["allowed_domains"] = []  # forbidden
    spec_path = tmp_path / "job.yaml"
    _write_yaml(spec_path, bad)

    exit_code = crawl_main(
        ["run", str(spec_path), "--out", str(tmp_path / "runs"), "--dry-run"]
    )
    assert exit_code != 0


def test_run_id_is_stable_for_same_spec_path_when_explicit(tmp_path: Path) -> None:
    # When --run-id is explicit, two runs land in the same directory
    # and re-persisting the spec is safe (idempotent).
    spec_path = tmp_path / "job.yaml"
    out_dir = tmp_path / "runs"
    _write_yaml(spec_path, _VALID_SPEC)

    code_a = crawl_main(
        [
            "run",
            str(spec_path),
            "--out",
            str(out_dir),
            "--run-id",
            "rerun",
            "--dry-run",
        ]
    )
    code_b = crawl_main(
        [
            "run",
            str(spec_path),
            "--out",
            str(out_dir),
            "--run-id",
            "rerun",
            "--dry-run",
        ]
    )
    assert code_a == 0
    assert code_b == 0
