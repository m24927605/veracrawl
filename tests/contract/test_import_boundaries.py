from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports


def test_core_does_not_import_adapters_or_frameworks() -> None:
    root = Path(__file__).resolve().parents[2]
    assert forbidden_core_imports(root) == {}
