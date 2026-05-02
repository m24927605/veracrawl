from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_persistence_adapter_core_imports_do_not_depend_on_concrete_storage() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}


def test_persistence_adapter_cli_uses_dynamic_adapter_imports() -> None:
    root = Path(__file__).parents[2]
    imports = imported_modules(root / "src" / "veracrawl" / "cli" / "persistence_adapter.py")
    assert "importlib" in imports
    assert "veracrawl.adapters.persistence.sqlite" not in imports
    assert "veracrawl.adapters.persistence.postgres_contract" not in imports
