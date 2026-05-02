"""Runtime spine fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from veracrawl.control.runtime import RuntimeRunReport, run_runtime_fixture


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def run_fixture(fixture_dir: Path, *, profile: str, out: Path) -> RuntimeRunReport:
    manifest = _load_json_like(fixture_dir / "manifest.yaml")
    fixture_id = str(manifest.get("id") or fixture_dir.name)
    profile_refs = manifest.get("profile_refs", ["target"])
    if profile not in profile_refs:
        raise ValueError(f"fixture {fixture_id} does not support profile {profile}")
    scenario = manifest.get("scenario")
    report = run_runtime_fixture(
        fixture_id=fixture_id,
        scenario=str(scenario) if scenario is not None else None,
        profile=profile,
    )
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-runtime")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "run":
        try:
            report = run_fixture(Path(args.fixture_dir), profile=args.profile, out=Path(args.out))
        except (OSError, ValueError, ValidationError) as exc:
            print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
            return 1
        print(
            json.dumps(
                {
                    "ok": True,
                    "fixture_id": report.fixture_id,
                    "status": report.status,
                    "completion_result": report.completion_result.value,
                    "published": report.published,
                    "operator_status": report.operator_status,
                },
                sort_keys=True,
            )
        )
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
