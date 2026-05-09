"""Phase 6 step 6.2 — charter regression test.

Scans ``src/`` for the five forbidden stealth-automation
patterns from ``docs/09 §Safety Boundary`` and fails if any
reappears in production code:

1. ``navigator.webdriver`` (override / patch)
2. ``plugins`` (fake plugin enumeration)
3. ``languages`` (fake navigator.languages override)
4. ``chrome.runtime`` (fake Chrome runtime stub)
5. Permissions API patches

Per the charter (``docs/09 §Safety Boundary`` line 116):

> VeraCrawl must support authorized and controlled
> acquisition. It must not include mechanisms for CAPTCHA
> solving, paywall bypass, credential theft, login-wall
> circumvention, WAF evasion, stealth automation,
> ban-avoidance proxy tactics, or bypassing robots, terms,
> or customer authorization policy.

The test allowlists ``src/veracrawl/adapters/browser/playwright.py``
(which mentions the patterns by name in its safety-boundary
docstring, documenting that these patterns were *removed*
and must not be re-added).

The test also fails if any new file invokes
``page.add_init_script(`` — the Playwright API the original
stealth scripts used. Any future legitimate use must justify
itself and update this allowlist.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_SRC_ROOT = Path(__file__).resolve().parents[2] / "src" / "veracrawl"

# Files allowed to mention the forbidden patterns by name
# (only in their safety-boundary docstrings).
_PATTERN_DOCSTRING_ALLOWLIST = {
    "src/veracrawl/adapters/browser/playwright.py",
}

# Files allowed to call ``page.add_init_script`` for
# legitimate non-stealth use (none today; future entries
# must include a justification comment in the test file).
_ADD_INIT_SCRIPT_ALLOWLIST: set[str] = set()

_FORBIDDEN_PATTERNS: tuple[str, ...] = (
    r"navigator\.webdriver",
    r"chrome\.runtime",
    # ``plugins`` and ``languages`` are common English words —
    # we look for the override-shape ``Object\.defineProperty`` /
    # ``__defineGetter__`` near them, which is the stealth
    # script signature.
    r"Object\.defineProperty.*\bplugins\b",
    r"Object\.defineProperty.*\blanguages\b",
    r"navigator\.permissions\.query",
)

_PATTERN_RE = re.compile("|".join(_FORBIDDEN_PATTERNS))
_ADD_INIT_SCRIPT_RE = re.compile(r"\.add_init_script\s*\(")


def _project_relative(path: Path) -> str:
    """Render ``path`` as ``src/veracrawl/...`` for allowlist matching."""

    parts = path.parts
    if "src" in parts:
        idx = parts.index("src")
        return "/".join(parts[idx:])
    return str(path)


def _walk_src_files() -> list[Path]:
    if not _SRC_ROOT.is_dir():
        pytest.skip(f"src tree missing: {_SRC_ROOT}")
    return sorted(_SRC_ROOT.rglob("*.py"))


def test_no_forbidden_stealth_patterns_in_src() -> None:
    """No file (except the documented allowlist) contains any
    of the five forbidden stealth-automation patterns."""

    offenders: list[tuple[str, int, str]] = []
    for path in _walk_src_files():
        rel = _project_relative(path)
        if rel in _PATTERN_DOCSTRING_ALLOWLIST:
            continue
        for line_no, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.strip()
            # Skip pure-comment lines; charter-test concern is
            # production code, not annotations.
            if stripped.startswith("#"):
                continue
            if _PATTERN_RE.search(line):
                offenders.append((rel, line_no, line.rstrip()))
    assert not offenders, (
        "Charter regression: forbidden stealth patterns found in "
        f"src/. Offenders: {offenders!r}"
    )


def test_no_unauthorized_add_init_script_calls() -> None:
    """``page.add_init_script(`` is the API the original
    stealth scripts used. Any new caller must justify itself
    and be added to ``_ADD_INIT_SCRIPT_ALLOWLIST`` with a
    comment explaining the legitimate non-stealth use."""

    offenders: list[tuple[str, int, str]] = []
    for path in _walk_src_files():
        rel = _project_relative(path)
        if rel in _ADD_INIT_SCRIPT_ALLOWLIST:
            continue
        for line_no, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            # Skip docstring lines that describe the API (those
            # are documentation, not invocation).
            if "page.add_init_script" in stripped and (
                stripped.startswith('"')
                or stripped.startswith("'")
                or "``" in stripped
            ):
                continue
            if _ADD_INIT_SCRIPT_RE.search(line):
                offenders.append((rel, line_no, line.rstrip()))
    assert not offenders, (
        "Charter regression: page.add_init_script() called outside "
        f"allowlist. Offenders: {offenders!r}"
    )


def test_charter_allowlist_files_still_exist() -> None:
    """The allowlist references real files; if a refactor
    moves the playwright adapter, the test must update too."""

    for rel in _PATTERN_DOCSTRING_ALLOWLIST:
        full = _SRC_ROOT.parents[1] / rel
        assert full.exists(), (
            f"charter allowlist references missing file: {rel}"
        )
