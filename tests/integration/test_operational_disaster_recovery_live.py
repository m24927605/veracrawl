from __future__ import annotations

from pathlib import Path

from tests.helpers.dr_fixture_assertions import assert_dr_success
from veracrawl.cli.dr import run_fixture

pytest_plugins = ("tests.integration.test_operational_infrastructure_live",)


def test_live_operational_disaster_recovery_fixture(
    live_infrastructure: tuple[str, str, str, str, str, str],
    tmp_path: Path,
) -> None:
    postgres_dsn, redis_url, s3_endpoint, s3_bucket, s3_access, s3_secret = live_infrastructure
    fixtures_root = Path(__file__).parents[2] / "tests" / "fixtures"
    report = run_fixture(
        fixtures_root / "dr-restore-success",
        profile="target",
        out=tmp_path / "dr-restore-success",
        postgres_dsn=postgres_dsn,
        redis_url=redis_url,
        s3_endpoint_url=s3_endpoint,
        s3_bucket=s3_bucket,
        s3_access_key_id=s3_access,
        s3_secret_access_key=s3_secret,
    )
    assert_dr_success(report)
