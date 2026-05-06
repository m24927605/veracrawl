"""Boundary tests for the logging surface.

The project's logging contract (see
``src/veracrawl/runtime_support/logging.py``) requires non-infrastructure
modules to consume ``get_logger`` rather than reach for stdlib ``logging``
or ``structlog`` directly. This keeps redaction, correlation_id, and
configure_logging idempotency centralized.

The CLI subpackage is allowed to import stdlib ``logging`` because pytest
helpers and unittest interop sometimes need it; raw ``import structlog``
in CLI files is still forbidden.

The runtime_support package itself implements the logging surface and
must be allowed to import both modules. The runtime_support gates that
predate this contract may still keep raw ``import logging`` (rollback
path until they are migrated).
"""

from __future__ import annotations

import re
from pathlib import Path

# Subpackages whose .py files MUST NOT import stdlib logging or structlog
# directly. They get logging through veracrawl.runtime_support.logging.
_INTERNAL_PACKAGES = (
    "adapters",
    "agents",
    "browser",
    "fetch",
    "extract",
    "optimization",
    "normalize",
    "evidence",
    "publish",
    "graph",
    "graph_memory",
    "memory",
    "scheduler",
    "runtime_events",
    "target_runtime",
)

_RAW_LOGGING_IMPORT = re.compile(
    r"^\s*(?:import\s+logging\b|from\s+logging\b|import\s+structlog\b|from\s+structlog\b)",
    re.MULTILINE,
)

_RAW_STRUCTLOG_ONLY = re.compile(
    r"^\s*(?:import\s+structlog\b|from\s+structlog\b)",
    re.MULTILINE,
)


def _src_root() -> Path:
    return Path(__file__).resolve().parents[2] / "src" / "veracrawl"


def test_internal_packages_do_not_import_stdlib_logging_or_structlog() -> None:
    src = _src_root()
    offenders: list[str] = []
    for package in _INTERNAL_PACKAGES:
        package_root = src / package
        if not package_root.is_dir():
            continue
        for py_file in package_root.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            for match in _RAW_LOGGING_IMPORT.finditer(content):
                line_no = content[: match.start()].count("\n") + 1
                offenders.append(
                    f"{py_file.relative_to(src.parent.parent)}:{line_no}: "
                    f"{match.group(0).strip()}"
                )
    assert not offenders, (
        "internal modules must use 'from veracrawl.runtime_support.logging "
        "import get_logger'; raw imports of logging/structlog are forbidden\n"
        "  - " + "\n  - ".join(offenders)
    )


def test_cli_subpackage_does_not_import_structlog_directly() -> None:
    """CLI may import stdlib logging (unittest interop) but not structlog."""
    src = _src_root() / "cli"
    offenders: list[str] = []
    for py_file in src.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for match in _RAW_STRUCTLOG_ONLY.finditer(content):
            line_no = content[: match.start()].count("\n") + 1
            offenders.append(
                f"{py_file.relative_to(src.parent.parent.parent)}:{line_no}: "
                f"{match.group(0).strip()}"
            )
    assert not offenders, (
        "CLI files must not import structlog directly; use "
        "veracrawl.runtime_support.logging.get_logger\n"
        "  - " + "\n  - ".join(offenders)
    )


def test_logging_module_can_import_logging_and_structlog() -> None:
    """Sanity: the infrastructure modules themselves are exempt."""
    src = _src_root()
    logging_file = src / "runtime_support" / "logging.py"
    redaction_file = src / "runtime_support" / "_log_redaction.py"
    assert _RAW_LOGGING_IMPORT.search(logging_file.read_text(encoding="utf-8"))
    # _log_redaction is pure stdlib; it doesn't actually import logging or
    # structlog (it implements a structlog-shaped processor without the dep).
    # Just assert it parses without import errors via a quick sanity grep.
    assert "import re" in redaction_file.read_text(encoding="utf-8")
