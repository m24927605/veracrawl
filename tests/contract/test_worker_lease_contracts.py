"""Contract tests for ``WorkerLease`` + ``WorkOutcome`` (s16)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError

from veracrawl.contracts.worker_lease import WorkerLease, WorkOutcome

_T = datetime(2026, 5, 15, 12, 0, tzinfo=UTC)


def _lease(**overrides: object) -> WorkerLease:
    payload: dict[str, object] = {
        "id": "lease:w:1",
        "lease_ref": "lease:w:1",
        "work_item_ref": "work:1",
        "worker_id": "w:1",
        "acquired_at": _T,
        "expires_at": _T + timedelta(seconds=60),
        "aimd_state_ref": "aimd:w:1:window=1",
        "budget_ref": "budget:1",
    }
    payload.update(overrides)
    return WorkerLease(**payload)  # type: ignore[arg-type]


def test_worker_lease_rejects_blank_id() -> None:
    with pytest.raises((ValidationError, ValueError), match="id"):
        _lease(id=" ")


def test_worker_lease_rejects_blank_lease_ref() -> None:
    with pytest.raises((ValidationError, ValueError), match="lease_ref"):
        _lease(lease_ref=" ")


def test_worker_lease_rejects_blank_work_item_ref() -> None:
    with pytest.raises((ValidationError, ValueError), match="work_item_ref"):
        _lease(work_item_ref=" ")


def test_worker_lease_rejects_blank_worker_id() -> None:
    with pytest.raises((ValidationError, ValueError), match="worker_id"):
        _lease(worker_id=" ")


def test_worker_lease_rejects_naive_acquired_at() -> None:
    with pytest.raises((ValidationError, ValueError), match="acquired_at"):
        _lease(acquired_at=datetime(2026, 5, 15, 12, 0))


def test_worker_lease_rejects_aware_non_utc_acquired_at() -> None:
    with pytest.raises((ValidationError, ValueError), match="acquired_at"):
        _lease(acquired_at=datetime(
            2026, 5, 15, 12, 0,
            tzinfo=timezone(timedelta(hours=8)),
        ))


def test_worker_lease_rejects_expires_before_acquired() -> None:
    with pytest.raises((ValidationError, ValueError), match="expires_at"):
        _lease(expires_at=_T - timedelta(seconds=1))


def test_worker_lease_rejects_extra_fields() -> None:
    with pytest.raises(ValidationError):
        WorkerLease(  # type: ignore[call-arg]
            id="lease:1", lease_ref="lease:1", work_item_ref="work:1",
            worker_id="w:1", acquired_at=_T,
            expires_at=_T + timedelta(seconds=60),
            aimd_state_ref="aimd:w:1", budget_ref="budget:1",
            unexpected_extra="boom",
        )


def test_work_outcome_requires_error_kind_on_failure() -> None:
    with pytest.raises((ValidationError, ValueError), match="error_kind"):
        WorkOutcome(success=False)


def test_work_outcome_accepts_success_without_error_kind() -> None:
    outcome = WorkOutcome(success=True)
    assert outcome.success is True
    assert outcome.error_kind is None
