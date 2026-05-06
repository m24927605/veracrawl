"""One-off migration script: wrap each CLI main() body in bootstrap_cli_logging.

Usage:
    uv run python scripts/migrate_cli_bootstrap.py [--dry-run]

For each src/veracrawl/cli/*.py with a top-level ``def main(...)``:

1. Inserts ``from veracrawl.runtime_support.logging import bootstrap_cli_logging``
   after the last existing import.
2. Wraps the entire ``main()`` body in
   ``with bootstrap_cli_logging("veracrawl-<filename>"):``,
   indenting all body lines by an additional 4 spaces.

Idempotent: if ``bootstrap_cli_logging`` already appears in the file, the
file is skipped. The script verifies the result still parses as Python
before writing; on parse failure the file is left untouched and the
failure is reported.

Files explicitly skipped: ``__init__.py`` and ``runtime.py`` (already
migrated by hand in the prior commit).
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

CLI_DIR = Path("src/veracrawl/cli")
SKIP_FILES = frozenset({"__init__.py", "runtime.py"})
IMPORT_LINE = "from veracrawl.runtime_support.logging import bootstrap_cli_logging\n"


def _module_to_prog(stem: str) -> str:
    return f"veracrawl-{stem.replace('_', '-')}"


def _last_import_end_lineno(tree: ast.Module) -> int:
    last = 0
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            end = node.end_lineno or 0
            if end > last:
                last = end
    return last


def migrate(path: Path, *, dry_run: bool = False) -> str:
    source = path.read_text(encoding="utf-8")

    if "bootstrap_cli_logging" in source:
        return "skip:already-migrated"

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return f"FAIL:initial-parse:{e}"

    main_func = next(
        (
            node
            for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        ),
        None,
    )
    if main_func is None:
        return "skip:no-main"

    last_import = _last_import_end_lineno(tree)
    if last_import == 0:
        return "skip:no-imports"

    prog = _module_to_prog(path.stem)
    lines = source.splitlines(keepends=True)

    # Step 1: insert the import line just after the last existing import.
    lines.insert(last_import, IMPORT_LINE)

    # Step 2: re-parse with the new line in place, locate main() again so
    # line numbers reflect the inserted import.
    new_source = "".join(lines)
    try:
        new_tree = ast.parse(new_source)
    except SyntaxError as e:
        return f"FAIL:after-import-insert:{e}"

    main_func = next(
        (
            node
            for node in new_tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "main"
        ),
        None,
    )
    assert main_func is not None, "main() vanished after import insert"

    # Step 3: detect main()'s body indentation.
    body_first_line = main_func.body[0].lineno
    body_last_line = main_func.body[-1].end_lineno or main_func.body[-1].lineno
    body_first_text = lines[body_first_line - 1]
    indent_match = re.match(r"(\s*)", body_first_text)
    base_indent = indent_match.group(1) if indent_match else "    "
    if base_indent != "    ":
        return f"skip:unusual-indent={len(base_indent)}"

    # Step 4: build the new body — opening `with` line plus each existing
    # body line indented by an extra 4 spaces. Blank lines stay blank.
    new_body: list[str] = [f'{base_indent}with bootstrap_cli_logging("{prog}"):\n']
    for i in range(body_first_line - 1, body_last_line):
        line = lines[i]
        if line.strip() == "":
            new_body.append(line)
        else:
            new_body.append("    " + line)

    lines = lines[: body_first_line - 1] + new_body + lines[body_last_line:]
    new_source = "".join(lines)

    # Step 5: verify the rewritten source still parses.
    try:
        ast.parse(new_source)
    except SyntaxError as e:
        return f"FAIL:final-parse:{e}"

    if not dry_run:
        path.write_text(new_source, encoding="utf-8")
    return "ok"


def main() -> int:
    dry_run = "--dry-run" in sys.argv
    targets = sorted(CLI_DIR.glob("*.py"))

    counts: dict[str, int] = {}
    failures: list[tuple[str, str]] = []
    for path in targets:
        if path.name in SKIP_FILES:
            continue
        result = migrate(path, dry_run=dry_run)
        counts[result] = counts.get(result, 0) + 1
        if result.startswith("FAIL"):
            failures.append((path.name, result))
        print(f"{path.name}: {result}")

    print()
    print("Summary:")
    for k in sorted(counts):
        print(f"  {k}: {counts[k]}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
