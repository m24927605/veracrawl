from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_operational_dr_core_has_no_concrete_infrastructure_imports() -> None:
    root = Path(__file__).parents[2]
    violations = forbidden_core_imports(root)
    assert not violations


def test_operational_dr_cli_uses_dynamic_adapter_imports() -> None:
    root = Path(__file__).parents[2]
    imports = imported_modules(root / "src" / "veracrawl" / "cli" / "dr.py")
    assert "psycopg" not in imports
    assert "redis" not in imports
    assert "boto3" not in imports
    assert "botocore" not in imports
    assert "veracrawl.adapters.persistence.postgres" not in imports
    assert "veracrawl.adapters.queue_brokers.redis" not in imports
    assert "veracrawl.adapters.object_stores.s3" not in imports
