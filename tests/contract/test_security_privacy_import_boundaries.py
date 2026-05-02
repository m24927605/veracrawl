from __future__ import annotations

from pathlib import Path

from tests.helpers.import_boundary import forbidden_core_imports, imported_modules


def test_security_privacy_core_has_no_forbidden_imports() -> None:
    root = Path(__file__).parents[2]
    violations = forbidden_core_imports(root)
    assert not violations


def test_security_privacy_runtime_and_cli_are_framework_and_vendor_neutral() -> None:
    root = Path(__file__).parents[2]
    forbidden = {
        "openai",
        "agents",
        "langchain",
        "langgraph",
        "crewai",
        "autogen",
        "semantic_kernel",
        "playwright",
        "selenium",
        "boto3",
        "botocore",
        "google.cloud",
        "azure",
        "psycopg",
        "redis",
        "hvac",
        "authlib",
    }
    for relative in [
        "src/veracrawl/runtime_support/security_privacy.py",
        "src/veracrawl/cli/security_privacy.py",
    ]:
        imports = imported_modules(root / relative)
        assert not {
            name
            for name in imports
            for forbidden_name in forbidden
            if name == forbidden_name or name.startswith(f"{forbidden_name}.")
        }
