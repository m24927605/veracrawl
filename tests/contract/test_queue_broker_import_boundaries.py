from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_queue_broker_core_imports_do_not_depend_on_redis_or_adapters() -> None:
    root = Path(__file__).parents[2]
    violations = forbidden_core_imports(root)
    assert not violations


def test_queue_broker_cli_uses_dynamic_adapter_imports() -> None:
    root = Path(__file__).parents[2]
    imports = imported_modules(root / "src" / "veracrawl" / "cli" / "queue_broker.py")
    assert "redis" not in imports
    assert "veracrawl.adapters.queue_brokers.redis" not in imports
