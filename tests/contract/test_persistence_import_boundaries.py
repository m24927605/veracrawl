from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports


def test_persistence_core_imports_do_not_depend_on_concrete_infrastructure() -> None:
    violations = forbidden_core_imports(Path(__file__).parents[2])
    assert violations == {}
