"""Import-boundary tests for s8.a contracts + ports."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[2] / "src" / "veracrawl"
_STDLIB = set(sys.stdlib_module_names)

_DRIFT_REPORT = _ROOT / "contracts" / "drift_report.py"
_REPAIR_PROPOSAL = _ROOT / "contracts" / "repair_proposal.py"
_EXTRACTION_OUTCOME = _ROOT / "contracts" / "extraction_outcome.py"
_DRIFT_PORT = _ROOT / "ports" / "drift_detection.py"
_REPAIR_PORT = _ROOT / "ports" / "repair.py"


def _imports(source: str) -> list[str]:
    out: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            out.extend(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level + (node.module or "")
            for a in node.names:
                out.append(f"{prefix}.{a.name}" if prefix else a.name)
    return out


def _allowlist(path: Path, *, extra_prefixes: tuple[str, ...] = ()) -> None:
    for module in _imports(path.read_text()):
        if module.startswith("."):
            pytest.fail(f"{path.name} forbids relative imports: {module!r}")
        if module.split(".", 1)[0] in _STDLIB:
            continue
        if module.split(".", 1)[0] in {"pydantic"}:
            continue
        if module.startswith("veracrawl.contracts."):
            continue
        if any(module.startswith(p) for p in extra_prefixes):
            continue
        pytest.fail(f"{path.name} imports forbidden module: {module!r}")


def test_drift_report_contract_imports_allowlist() -> None:
    _allowlist(_DRIFT_REPORT)


def test_repair_proposal_contract_imports_allowlist() -> None:
    _allowlist(_REPAIR_PROPOSAL)


def test_extraction_outcome_contract_imports_allowlist() -> None:
    _allowlist(_EXTRACTION_OUTCOME)


def test_drift_detection_port_imports_allowlist() -> None:
    _allowlist(_DRIFT_PORT)


def test_repair_port_imports_allowlist() -> None:
    _allowlist(_REPAIR_PORT)
