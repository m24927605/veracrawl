from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.helpers.persistence_adapter_fixture_assertions import assert_postgres_adapter_success
from veracrawl.cli.persistence_adapter import run_fixture


@pytest.fixture(scope="module")
def postgres_dsn() -> Iterator[str]:
    explicit_dsn = os.getenv("VERACRAWL_POSTGRES_DSN")
    if explicit_dsn:
        yield explicit_dsn
        return
    if os.getenv("VERACRAWL_POSTGRES_DOCKER") != "1":
        pytest.skip("set VERACRAWL_POSTGRES_DSN or VERACRAWL_POSTGRES_DOCKER=1")
    psycopg = pytest.importorskip("psycopg")
    docker_available = subprocess.run(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if docker_available.returncode != 0:
        pytest.skip("Docker daemon is unavailable for live Postgres test")
    started = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "-e",
            "POSTGRES_PASSWORD=veracrawl",
            "-e",
            "POSTGRES_USER=veracrawl",
            "-e",
            "POSTGRES_DB=veracrawl",
            "-p",
            "127.0.0.1::5432",
            "postgres:16-alpine",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    container_id = started.stdout.strip()
    try:
        port_output = subprocess.run(
            ["docker", "port", container_id, "5432/tcp"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        host, port = port_output.rsplit(":", maxsplit=1)
        dsn = f"postgresql://veracrawl:veracrawl@{host}:{port}/veracrawl"
        deadline = time.monotonic() + 60
        while True:
            try:
                with psycopg.connect(dsn, connect_timeout=2):
                    break
            except Exception:
                if time.monotonic() > deadline:
                    raise
                time.sleep(1)
        yield dsn
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_id],
            check=False,
            capture_output=True,
            text=True,
        )


def test_live_postgres_adapter_fixtures(postgres_dsn: str, tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "postgres-adapter-conformance-success",
        "postgres-reopen-idempotency-success",
        "postgres-queue-recovery-success",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
            postgres_dsn=postgres_dsn,
        )
        assert_postgres_adapter_success(report)
        if fixture_id == "postgres-reopen-idempotency-success":
            assert report.reloaded is True
            assert report.duplicate_deduped is True
            assert report.event_count == 1
            assert report.outbox_count == 1
