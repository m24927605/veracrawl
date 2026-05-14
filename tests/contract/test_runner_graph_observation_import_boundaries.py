"""s6 import-boundary tests (tests 18, 19, 22)."""

from __future__ import annotations

import ast
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_RUNNER = _REPO / "src/veracrawl/external_crawl/runner.py"
_CLOCK = _REPO / "src/veracrawl/adapters/clocks/replaying_utc_clock.py"


_CLOCK_STDLIB_ALLOWLIST = {"__future__", "typing", "datetime", "collections.abc"}


def _parse(path: Path) -> ast.Module:
    return ast.parse(path.read_text(), filename=str(path))


# Test 22 — the clock adapter must be stdlib-only.
def test_replaying_utc_clock_import_boundaries() -> None:
    tree = _parse(_CLOCK)
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.level == 0, f"relative import not allowed: {ast.dump(node)}"
            module = node.module or ""
            assert not module.startswith("veracrawl"), (
                f"replaying_utc_clock must not import veracrawl.*: {module}"
            )
            assert module in _CLOCK_STDLIB_ALLOWLIST, (
                f"replaying_utc_clock ImportFrom not in stdlib allowlist: {module}"
            )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert not alias.name.startswith("veracrawl"), (
                    f"replaying_utc_clock must not import veracrawl.*: {alias.name}"
                )
                assert alias.name in _CLOCK_STDLIB_ALLOWLIST, (
                    f"replaying_utc_clock Import not in stdlib allowlist: {alias.name}"
                )
