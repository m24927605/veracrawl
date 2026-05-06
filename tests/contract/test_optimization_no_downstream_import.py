"""Boundary test: downstream modules must not import veracrawl.optimization.

The ``optimization/`` package is the high-level orchestrator that produces
runtime decisions; the downstream packages (``extract``, ``graph``,
``normalize``, ``publish``, ``scheduler``, ``ops``) consume those
decisions through ``contracts/optimization_runtime``. Importing the
producer's runtime module from a consumer creates the cycle this fix
removed.
"""

from __future__ import annotations

import re
from pathlib import Path

DOWNSTREAM_PACKAGES = (
    "extract",
    "graph",
    "normalize",
    "publish",
    "scheduler",
    "ops",
)

_OPTIMIZATION_IMPORT = re.compile(
    r"^\s*(?:from\s+veracrawl\.optimization\b|import\s+veracrawl\.optimization\b)",
    re.MULTILINE,
)


def test_downstream_packages_do_not_import_veracrawl_optimization() -> None:
    src = Path(__file__).resolve().parents[2] / "src" / "veracrawl"
    offenders: list[str] = []
    for package in DOWNSTREAM_PACKAGES:
        package_root = src / package
        if not package_root.is_dir():
            continue
        for py_file in package_root.rglob("*.py"):
            content = py_file.read_text(encoding="utf-8")
            for match in _OPTIMIZATION_IMPORT.finditer(content):
                line_no = content[: match.start()].count("\n") + 1
                offenders.append(
                    f"{py_file.relative_to(src.parent.parent)}:{line_no}: "
                    f"{match.group(0).strip()}"
                )
    assert not offenders, (
        "downstream packages must not import veracrawl.optimization.* "
        "(use veracrawl.contracts.optimization_runtime instead)\n  - "
        + "\n  - ".join(offenders)
    )


def test_runtime_runtime_reexports_contract_types() -> None:
    """Backwards-compat: existing call sites that still import the types
    from optimization.runtime must keep working."""
    from veracrawl.contracts.optimization_runtime import (
        RuntimeDedupeRankingResult as ContractDedupe,
    )
    from veracrawl.contracts.optimization_runtime import (
        RuntimeDomExtractionResult as ContractDom,
    )
    from veracrawl.optimization.runtime import (
        RuntimeDedupeRankingResult as ReExportDedupe,
    )
    from veracrawl.optimization.runtime import (
        RuntimeDomExtractionResult as ReExportDom,
    )

    assert ReExportDom is ContractDom
    assert ReExportDedupe is ContractDedupe
