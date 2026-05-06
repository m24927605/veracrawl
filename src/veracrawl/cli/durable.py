"""Durable runtime and scheduler fixture runner CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from pydantic import Field

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.durable import DurableFixtureManifest
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.event import CrawlRunEvent
from veracrawl.control.runtime import create_runtime_command
from veracrawl.review_replay.durable import validate_durable_recovery
from veracrawl.runtime_support.durable_store import DeterministicDurableStore
from veracrawl.runtime_support.logging import bootstrap_cli_logging
from veracrawl.scheduler.runtime import (
    LeaseTokenError,
    complete_frontier_item,
    enqueue_frontier_item,
    expire_lease,
    lease_next_frontier_item,
    scheduler_recovery_report,
)


class DurableFixtureRunReport(TimestampedModel):
    id: str
    fixture_id: str
    scenario: str
    profile: str
    run_ref: Ref
    status: str
    completion_result: CompletenessResult
    operator_status: str
    command_record_refs: list[Ref] = Field(default_factory=list)
    command_result_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    frontier_item_refs: list[Ref] = Field(default_factory=list)
    lease_refs: list[Ref] = Field(default_factory=list)
    scheduler_recovery_report_refs: list[Ref] = Field(default_factory=list)
    durable_recovery_report_ref: Ref
    missing_ref_fields: list[str] = Field(default_factory=list)
    diagnostics: list[str] = Field(default_factory=list)
    duplicate_command_deduped: bool = False
    event_count: int = 0
    outbox_count: int = 0
    reloaded: bool = False


def _load_json_like(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _command(fixture_id: str, *, duplicate: bool = False) -> Any:
    return create_runtime_command(
        command_id=f"cmd:{fixture_id}:durable{'-duplicate' if duplicate else ''}",
        command_type="durable_commit_command",
        target_aggregate_type="DurableFixture",
        target_aggregate_id=fixture_id,
        payload_ref=f"payload:{fixture_id}",
    )


def _force_event_gap(store: DeterministicDurableStore, *, run_ref: Ref) -> None:
    event = CrawlRunEvent(
        id=f"event:{run_ref}:3",
        run_id=run_ref,
        objective_id=f"objective:{run_ref}",
        crawl_plan_id=f"plan:{run_ref}",
        sequence=3,
        event_type="durable_fixture_gap_forced",
        event_type_spec_id="event-type:durable_fixture_gap_forced",
        payload_ref=f"payload:{run_ref}:gap",
        causation_id=f"cmd:{run_ref}:gap",
        correlation_id=f"corr:{run_ref}",
        trace_id=f"trace:{run_ref}:3",
        idempotency_key=f"event:{run_ref}:3",
    )
    store.force_append_event_for_fixture(event)


def run_durable_fixture(
    fixture_id: str,
    *,
    scenario: str,
    profile: str,
) -> DurableFixtureRunReport:
    run_ref = f"run:{fixture_id}"
    objective_ref = f"objective:{fixture_id}"
    plan_ref = f"plan:{fixture_id}"
    store = DeterministicDurableStore()
    artifact_ref = f"artifact:{fixture_id}:raw"
    expected_artifact_refs = [artifact_ref]
    store.register_artifact_ref(artifact_ref)

    command = _command(fixture_id)
    record, result, outbox, duplicate = store.handle_command(
        command,
        run_ref=run_ref,
        objective_ref=objective_ref,
        plan_ref=plan_ref,
        event_type="durable_command_committed",
        output_refs=[artifact_ref],
    )

    duplicate_deduped = False
    if scenario == "duplicate-command":
        _, duplicate_result, _, duplicate = store.handle_command(
            _command(fixture_id, duplicate=True).model_copy(
                update={
                    "idempotency_key": command.idempotency_key,
                    "target_aggregate_id": command.target_aggregate_id,
                }
            ),
            run_ref=run_ref,
            objective_ref=objective_ref,
            plan_ref=plan_ref,
            event_type="durable_command_committed",
            output_refs=[artifact_ref],
        )
        duplicate_deduped = duplicate and duplicate_result.id == result.id

    if scenario not in {"pending-outbox"}:
        store.mark_outbox_dispatched(outbox.id, dispatched_at_ref=f"clock:{outbox.id}:dispatched")

    if scenario == "event-gap":
        _force_event_gap(store, run_ref=run_ref)

    if scenario == "missing-artifact":
        store.remove_artifact_ref_for_fixture(artifact_ref)

    enqueue_frontier_item(
        store,
        item_id=f"frontier:{fixture_id}:1",
        run_ref=run_ref,
        source_ref=f"source:{fixture_id}",
        priority=10,
        policy_decision_refs=[f"policy:{fixture_id}:source"],
    )
    leased = lease_next_frontier_item(
        store,
        run_ref=run_ref,
        holder_ref="worker:durable-fixture",
        expires_at_ref=f"clock:{fixture_id}:lease-expiry",
    )
    if leased is None:
        raise ValueError("durable fixture could not lease frontier item")
    leased_item, lease = leased

    diagnostics: list[str] = []
    if scenario == "stale-lease":
        expire_lease(store, lease_ref=lease.id, reason_ref=f"lease-expired:{fixture_id}")
    elif scenario == "invalid-lease":
        try:
            complete_frontier_item(
                store,
                item_ref=leased_item.id,
                lease_ref=lease.id,
                lease_token_ref="lease-token:wrong",
                result_refs=[result.id],
            )
        except LeaseTokenError as exc:
            diagnostics.append(str(exc))
    else:
        complete_frontier_item(
            store,
            item_ref=leased_item.id,
            lease_ref=lease.id,
            lease_token_ref=lease.lease_token_ref,
            result_refs=[result.id],
        )

    reloaded = store.reopen()
    cursor = reloaded.build_event_cursor(run_ref)
    scheduler_report = scheduler_recovery_report(
        reloaded,
        run_ref=run_ref,
        report_id=f"scheduler-recovery:{fixture_id}",
    )
    recovery_report = validate_durable_recovery(
        run_ref=run_ref,
        command_record_refs=list(reloaded.backing.command_records),
        event_cursors=[cursor],
        outbox_records=reloaded.list_outbox(run_ref),
        artifact_refs=sorted(reloaded.backing.artifact_refs),
        expected_artifact_refs=expected_artifact_refs,
        frontier_item_refs=[frontier.id for frontier in reloaded.list_frontier_items(run_ref)],
        lease_refs=[queue_lease.id for queue_lease in reloaded.list_queue_leases(run_ref)],
        scheduler_report=scheduler_report,
        report_id=f"durable-recovery:{fixture_id}",
    )

    operator_status = recovery_report.operator_status
    if duplicate_deduped and recovery_report.completeness_result == CompletenessResult.PASS:
        operator_status = "duplicate_command_deduped"

    return DurableFixtureRunReport(
        id=f"durable-run-report:{fixture_id}",
        fixture_id=fixture_id,
        scenario=scenario,
        profile=profile,
        run_ref=run_ref,
        status=operator_status,
        completion_result=recovery_report.completeness_result,
        operator_status=operator_status,
        command_record_refs=list(reloaded.backing.command_records),
        command_result_refs=list(reloaded.backing.command_results),
        event_cursor_refs=[cursor.id],
        outbox_refs=list(reloaded.backing.outbox_records),
        artifact_refs=sorted(reloaded.backing.artifact_refs),
        frontier_item_refs=[frontier.id for frontier in reloaded.list_frontier_items(run_ref)],
        lease_refs=[queue_lease.id for queue_lease in reloaded.list_queue_leases(run_ref)],
        scheduler_recovery_report_refs=[scheduler_report.id],
        durable_recovery_report_ref=recovery_report.id,
        missing_ref_fields=recovery_report.missing_ref_fields,
        diagnostics=diagnostics + recovery_report.gap_report_refs,
        duplicate_command_deduped=duplicate_deduped,
        event_count=len(reloaded.stream_events(run_ref)),
        outbox_count=len(reloaded.list_outbox(run_ref)),
        reloaded=True,
    )


def run_fixture(fixture_dir: Path, *, profile: str, out: Path) -> DurableFixtureRunReport:
    manifest = DurableFixtureManifest.model_validate(_load_json_like(fixture_dir / "manifest.yaml"))
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    scenario = manifest.scenario
    report = run_durable_fixture(manifest.id, scenario=scenario, profile=profile)
    out.mkdir(parents=True, exist_ok=True)
    (out / "run_report.json").write_text(
        json.dumps(report.model_dump(mode="json"), sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="veracrawl-durable")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument("fixture_dir")
    run.add_argument("--profile", default="target")
    run.add_argument("--out", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    with bootstrap_cli_logging("veracrawl-durable"):
        parser = build_parser()
        args = parser.parse_args(argv)
        if args.command == "run":
            try:
                report = run_fixture(
                    Path(args.fixture_dir), profile=args.profile, out=Path(args.out)
                )
            except (OSError, ValueError) as exc:
                print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
                return 1
            print(
                json.dumps(
                    {
                        "ok": True,
                        "fixture_id": report.fixture_id,
                        "completion_result": report.completion_result.value,
                        "operator_status": report.operator_status,
                        "status": report.status,
                    },
                    sort_keys=True,
                )
            )
            return 0
        return 2


if __name__ == "__main__":
    sys.exit(main())
