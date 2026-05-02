from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.helpers.queue_broker_fixture_assertions import assert_queue_broker_success
from veracrawl.cli.queue_broker import run_fixture


@pytest.fixture(scope="module")
def redis_url() -> Iterator[str]:
    explicit_url = os.getenv("VERACRAWL_REDIS_URL")
    if explicit_url:
        yield explicit_url
        return
    if os.getenv("VERACRAWL_REDIS_DOCKER") != "1":
        pytest.skip("set VERACRAWL_REDIS_URL or VERACRAWL_REDIS_DOCKER=1")
    redis = pytest.importorskip("redis")
    docker_available = subprocess.run(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if docker_available.returncode != 0:
        pytest.skip("Docker daemon is unavailable for live Redis test")
    started = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "-p",
            "127.0.0.1::6379",
            "redis:7-alpine",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    container_id = started.stdout.strip()
    try:
        port_output = subprocess.run(
            ["docker", "port", container_id, "6379/tcp"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        host, port = port_output.rsplit(":", maxsplit=1)
        url = f"redis://{host}:{port}/0"
        deadline = time.monotonic() + 60
        while True:
            try:
                client = redis.Redis.from_url(url, decode_responses=True)
                client.ping()
                break
            except Exception:
                if time.monotonic() > deadline:
                    raise
                time.sleep(1)
        yield url
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_id],
            check=False,
            capture_output=True,
            text=True,
        )


def test_live_redis_queue_broker_fixtures(redis_url: str, tmp_path: Path) -> None:
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "redis-broker-conformance-success",
        "redis-broker-idempotency-success",
        "redis-broker-dead-letter-success",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
            redis_url=redis_url,
        )
        assert_queue_broker_success(report)
        assert report.queued_count == 0
        assert report.dead_letter_count == 1
        if fixture_id == "redis-broker-idempotency-success":
            assert report.duplicate_deduped is True
