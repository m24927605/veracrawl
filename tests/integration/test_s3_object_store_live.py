from __future__ import annotations

import os
import subprocess
import time
from collections.abc import Iterator
from pathlib import Path

import pytest

from tests.helpers.object_store_fixture_assertions import assert_object_store_success
from veracrawl.cli.object_store import run_fixture


@pytest.fixture(scope="module")
def s3_endpoint() -> Iterator[tuple[str, str, str, str]]:
    explicit_endpoint = os.getenv("VERACRAWL_S3_ENDPOINT_URL")
    explicit_bucket = os.getenv("VERACRAWL_S3_BUCKET")
    explicit_access_key = os.getenv("VERACRAWL_S3_ACCESS_KEY_ID")
    explicit_secret_key = os.getenv("VERACRAWL_S3_SECRET_ACCESS_KEY")
    if all([explicit_endpoint, explicit_bucket, explicit_access_key, explicit_secret_key]):
        yield (
            str(explicit_endpoint),
            str(explicit_bucket),
            str(explicit_access_key),
            str(explicit_secret_key),
        )
        return
    if os.getenv("VERACRAWL_S3_DOCKER") != "1":
        pytest.skip("set VERACRAWL_S3_* vars or VERACRAWL_S3_DOCKER=1")
    boto3 = pytest.importorskip("boto3")
    config_module = pytest.importorskip("botocore.config")
    docker_available = subprocess.run(
        ["docker", "info", "--format", "{{.ServerVersion}}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if docker_available.returncode != 0:
        pytest.skip("Docker daemon is unavailable for live MinIO test")
    access_key = "veracrawl"
    secret_key = "veracrawl-secret"
    started = subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--rm",
            "-e",
            f"MINIO_ROOT_USER={access_key}",
            "-e",
            f"MINIO_ROOT_PASSWORD={secret_key}",
            "-p",
            "127.0.0.1::9000",
            "minio/minio:latest",
            "server",
            "/data",
            "--console-address",
            ":9001",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    container_id = started.stdout.strip()
    try:
        port_output = subprocess.run(
            ["docker", "port", container_id, "9000/tcp"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
        host, port = port_output.rsplit(":", maxsplit=1)
        endpoint_url = f"http://{host}:{port}"
        deadline = time.monotonic() + 90
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
                break
            except Exception:
                if time.monotonic() > deadline:
                    raise
                time.sleep(1)
        yield endpoint_url, "veracrawl-artifacts", access_key, secret_key
    finally:
        subprocess.run(
            ["docker", "rm", "-f", container_id],
            check=False,
            capture_output=True,
            text=True,
        )


def test_live_s3_object_store_fixtures(
    s3_endpoint: tuple[str, str, str, str],
    tmp_path: Path,
) -> None:
    endpoint_url, bucket, access_key, secret_key = s3_endpoint
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    for fixture_id in [
        "s3-object-store-conformance-success",
        "s3-object-store-idempotency-success",
        "s3-object-store-delete-success",
    ]:
        report = run_fixture(
            fixtures_root / fixture_id,
            profile="target",
            out=tmp_path / fixture_id,
            endpoint_url=endpoint_url,
            bucket=bucket,
            access_key_id=access_key,
            secret_access_key=secret_key,
        )
        assert_object_store_success(report)
        if fixture_id == "s3-object-store-idempotency-success":
            assert report.duplicate_deduped is True
