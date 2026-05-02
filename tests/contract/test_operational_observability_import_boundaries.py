from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_operational_observability_core_has_no_forbidden_imports() -> None:
    root = Path(__file__).parents[2]
    violations = forbidden_core_imports(root)
    assert not violations


def test_operational_observability_runtime_and_cli_are_telemetry_backend_neutral() -> None:
    root = Path(__file__).parents[2]
    forbidden = {
        "prometheus_client",
        "opentelemetry",
        "grafana_client",
        "google.cloud.monitoring",
        "azure.monitor",
        "boto3",
        "botocore",
        "psycopg",
        "redis",
        "langchain",
        "langgraph",
        "crewai",
        "autogen",
        "semantic_kernel",
        "playwright",
        "selenium",
    }
    for relative in [
        "src/veracrawl/runtime_support/observability.py",
        "src/veracrawl/cli/observability.py",
    ]:
        imports = imported_modules(root / relative)
        assert not {
            name
            for name in imports
            for forbidden_name in forbidden
            if name == forbidden_name or name.startswith(f"{forbidden_name}.")
        }
