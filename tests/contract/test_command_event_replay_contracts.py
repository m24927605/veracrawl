from __future__ import annotations

import pytest
from pydantic import ValidationError

from tests.factories import command, event, full_replay_manifest, missing_replay_manifest
from veracrawl.contracts.command import CommandResult
from veracrawl.contracts.enums import (
    CommandResultStatus,
    CommandStatus,
    CompletenessResult,
    ReplayMissingRefBehavior,
)
from veracrawl.contracts.errors import ReplayValidationError
from veracrawl.runtime_events.event_store import InMemoryEventStore
from veracrawl.runtime_events.replay import validate_replay_manifest


def test_command_transitions_are_constrained() -> None:
    proposed = command()
    accepted = proposed.transition(CommandStatus.ACCEPTED)
    committed = accepted.transition(CommandStatus.COMMITTED)
    assert committed.status == CommandStatus.COMMITTED
    with pytest.raises(ValueError):
        committed.transition(CommandStatus.ACCEPTED)


def test_command_result_requires_events_or_reasons() -> None:
    CommandResult(
        id="result:1",
        command_id="cmd:1",
        result=CommandResultStatus.COMMITTED,
        emitted_event_refs=["event:1"],
    )
    with pytest.raises(ValidationError):
        CommandResult(id="result:2", command_id="cmd:1", result=CommandResultStatus.REJECTED)


def test_event_store_requires_contiguous_sequences() -> None:
    store = InMemoryEventStore()
    store.append(event(1))
    with pytest.raises(ReplayValidationError):
        store.append(event(3))
    assert [item.sequence for item in store.stream("run:1")] == [1]


def test_replay_manifest_passes_only_with_required_refs() -> None:
    report = validate_replay_manifest(full_replay_manifest())
    assert report.completeness_result == CompletenessResult.PASS

    failed = validate_replay_manifest(missing_replay_manifest())
    assert failed.completeness_result == CompletenessResult.FAIL
    assert "command_result_refs" in failed.missing_ref_fields

    review = validate_replay_manifest(
        missing_replay_manifest(ReplayMissingRefBehavior.ALLOW_WITH_GAP_REPORT)
    )
    assert review.completeness_result == CompletenessResult.NEEDS_REVIEW
