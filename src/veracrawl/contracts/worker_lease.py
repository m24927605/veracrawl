"""``WorkerLease`` + ``WorkOutcome`` + ``BudgetGate`` (s16)."""

from __future__ import annotations

from datetime import UTC, datetime

from veracrawl.contracts.common import Ref, VeraModel


def _require(cond: bool, msg: str) -> None:
    if not cond:
        raise ValueError(msg)


def _is_utc(d: datetime) -> bool:
    return d.tzinfo is not None and d.utcoffset() == UTC.utcoffset(d)


class WorkerLease(VeraModel):
    id: str
    lease_ref: Ref
    work_item_ref: Ref
    worker_id: str
    acquired_at: datetime
    expires_at: datetime
    aimd_state_ref: Ref
    budget_ref: Ref

    def model_post_init(self, __context: object) -> None:
        _require(bool(self.id.strip()), "id must be non-blank")
        _require(bool(self.lease_ref.strip()), "lease_ref must be non-blank")
        _require(
            bool(self.work_item_ref.strip()),
            "work_item_ref must be non-blank",
        )
        _require(bool(self.worker_id.strip()), "worker_id must be non-blank")
        _require(_is_utc(self.acquired_at), "acquired_at must be UTC")
        _require(_is_utc(self.expires_at), "expires_at must be UTC")
        _require(
            self.expires_at > self.acquired_at,
            "expires_at must be strictly after acquired_at",
        )
        _require(
            bool(self.aimd_state_ref.strip()),
            "aimd_state_ref must be non-blank",
        )
        _require(bool(self.budget_ref.strip()), "budget_ref must be non-blank")


class WorkOutcome(VeraModel):
    """Result handed back to ``WorkerLeasePort.release``."""

    success: bool
    error_kind: str | None = None

    def model_post_init(self, __context: object) -> None:
        if not self.success:
            _require(
                self.error_kind is not None
                and bool(self.error_kind.strip()),
                "error_kind must be non-blank when success=False",
            )


__all__ = ["WorkOutcome", "WorkerLease"]
