from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports


def test_memory_core_has_no_concrete_dependency_imports() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}
