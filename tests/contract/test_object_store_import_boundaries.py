from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_object_store_core_imports_do_not_depend_on_s3_sdks_or_adapters() -> None:
    root = Path(__file__).parents[2]
    violations = forbidden_core_imports(root)
    assert not violations


def test_object_store_cli_uses_dynamic_adapter_imports() -> None:
    root = Path(__file__).parents[2]
    imports = imported_modules(root / "src" / "veracrawl" / "cli" / "object_store.py")
    assert "boto3" not in imports
    assert "botocore" not in imports
    assert "veracrawl.adapters.object_stores.s3" not in imports
