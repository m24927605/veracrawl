from __future__ import annotations

from pathlib import Path


def assert_required_paths_exist(base: Path, relative_paths: list[str]) -> None:
    missing = [path for path in relative_paths if not (base / path).exists()]
    assert not missing, f"missing fixture paths: {missing}"
