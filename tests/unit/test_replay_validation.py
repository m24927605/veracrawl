from __future__ import annotations

from tests.factories import full_replay_manifest, missing_replay_manifest
from veracrawl.contracts.enums import CompletenessResult, ReplayMissingRefBehavior
from veracrawl.runtime_events.replay import missing_replay_refs, validate_replay_manifest


def test_missing_replay_refs_are_reported() -> None:
    missing = missing_replay_refs(missing_replay_manifest())
    assert "event_cursor_refs" in missing
    assert "redaction_map_ref" in missing


def test_full_replay_manifest_passes() -> None:
    report = validate_replay_manifest(full_replay_manifest())
    assert report.completeness_result == CompletenessResult.PASS


def test_missing_refs_never_pass() -> None:
    fail_report = validate_replay_manifest(missing_replay_manifest())
    review_report = validate_replay_manifest(
        missing_replay_manifest(ReplayMissingRefBehavior.ALLOW_WITH_GAP_REPORT)
    )
    assert fail_report.completeness_result == CompletenessResult.FAIL
    assert review_report.completeness_result == CompletenessResult.NEEDS_REVIEW
