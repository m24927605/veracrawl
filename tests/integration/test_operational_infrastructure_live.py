from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest

from tests.helpers.infrastructure_fixture_assertions import assert_infrastructure_success
from veracrawl.cli.infrastructure import run_fixture


@pytest.fixture(scope="module")
def live_infrastructure() -> Iterator[tuple[str, str, str, str, str, str]]:
    explicit = (
        os.getenv("VERACRAWL_POSTGRES_DSN"),
        os.getenv("VERACRAWL_REDIS_URL"),
        os.getenv("VERACRAWL_S3_ENDPOINT_URL"),
        os.getenv("VERACRAWL_S3_BUCKET"),
        os.getenv("VERACRAWL_S3_ACCESS_KEY_ID"),
        os.getenv("VERACRAWL_S3_SECRET_ACCESS_KEY"),
    )
    if all(explicit):
        yield (
            str(explicit[0]),
            str(explicit[1]),
            str(explicit[2]),
            str(explicit[3]),
            str(explicit[4]),
            str(explicit[5]),
        )
        return
    if os.getenv("VERACRAWL_INFRASTRUCTURE_DOCKER") != "1":
        pytest.skip("set VERACRAWL_* live vars or VERACRAWL_INFRASTRUCTURE_DOCKER=1")
    psycopg = pytest.importorskip("psycopg")
    redis = pytest.importorskip("redis")
    boto3 = pytest.importorskip("boto3")
    config_module = pytest.importorskip("botocore.config")
    docker_available = subprocess.run(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if docker_available.returncode != 0:
        pytest.skip("Docker daemon is unavailable for live infrastructure test")
    containers: list[str] = []
    try:
        postgres_id = _docker_run(
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
            ]
        )
        containers.append(postgres_id)
        redis_id = _docker_run(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "-p",
                "127.0.0.1::6379",
                "redis:7-alpine",
            ]
        )
        containers.append(redis_id)
        s3_access = "veracrawl"
        s3_secret = "veracrawl-secret"
        minio_id = _docker_run(
            [
                "docker",
                "run",
                "-d",
                "--rm",
                "-e",
                f"MINIO_ROOT_USER={s3_access}",
                "-e",
                f"MINIO_ROOT_PASSWORD={s3_secret}",
                "-p",
                "127.0.0.1::9000",
                "minio/minio:latest",
                "server",
                "/data",
                "--console-address",
                ":9001",
            ]
        )
        containers.append(minio_id)
        postgres_host, postgres_port = _docker_host_port(postgres_id, "5432/tcp")
        redis_host, redis_port = _docker_host_port(redis_id, "6379/tcp")
        minio_host, minio_port = _docker_host_port(minio_id, "9000/tcp")
        postgres_dsn = (
            f"postgresql://veracrawl:veracrawl@{postgres_host}:{postgres_port}/veracrawl"
        )
        redis_url = f"redis://{redis_host}:{redis_port}/0"
        s3_endpoint = f"http://{minio_host}:{minio_port}"
        _wait_for_postgres(psycopg, postgres_dsn)
        _wait_for_redis(redis, redis_url)
        _wait_for_s3(boto3, config_module, s3_endpoint, s3_access, s3_secret)
        yield (
            postgres_dsn,
            redis_url,
            s3_endpoint,
            "veracrawl-infrastructure-artifacts",
            s3_access,
            s3_secret,
        )
    finally:
        for container_id in reversed(containers):
            subprocess.run(
                ["docker", "rm", "-f", container_id],
                check=False,
                capture_output=True,
                text=True,
            )


def test_live_operational_infrastructure_fixtures(
    live_infrastructure: tuple[str, str, str, str, str, str],
    tmp_path: Path,
) -> None:
    postgres_dsn, redis_url, s3_endpoint, s3_bucket, s3_access, s3_secret = live_infrastructure
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "operational-infrastructure-success",
        "operational-infrastructure-idempotency-success",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
            postgres_dsn=postgres_dsn,
            redis_url=redis_url,
            s3_endpoint_url=s3_endpoint,
            s3_bucket=s3_bucket,
            s3_access_key_id=s3_access,
            s3_secret_access_key=s3_secret,
        )
        assert_infrastructure_success(report)
        if fixture_id == "operational-infrastructure-idempotency-success":
            assert report.idempotency_deduped is True


def _docker_run(args: list[str]) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def _docker_host_port(container_id: str, port: str) -> tuple[str, str]:
    port_output = subprocess.run(
        ["docker", "port", container_id, port],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    host, host_port = port_output.rsplit(":", maxsplit=1)
    return host, host_port


def _wait_for_postgres(psycopg: Any, dsn: str) -> None:
    deadline = time.monotonic() + 90
    while True:
        try:
            with psycopg.connect(dsn, connect_timeout=2):
                return
        except Exception:
            if time.monotonic() > deadline:
                raise
            time.sleep(1)


def _wait_for_redis(redis: Any, redis_url: str) -> None:
    deadline = time.monotonic() + 90
    while True:
        try:
            client = redis.Redis.from_url(redis_url, decode_responses=True)
            client.ping()
            return
        except Exception:
            if time.monotonic() > deadline:
                raise
            time.sleep(1)


def _wait_for_s3(
    boto3: Any,
    config_module: Any,
    endpoint_url: str,
    access_key: str,
    secret_key: str,
) -> None:
    deadline = time.monotonic() + 120
    while True:
        try:
            client = boto3.client(
                "s3",
                endpoint_url=endpoint_url,
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key,
                region_name="us-east-1",
                config=config_module.Config(s3={"addressing_style": "path"}),
            )
            client.list_buckets()
            return
        except Exception:
            if time.monotonic() > deadline:
                raise
            time.sleep(1)
