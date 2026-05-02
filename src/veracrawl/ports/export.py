"""Export target port abstractions."""

from __future__ import annotations

from typing import Protocol

from veracrawl.contracts.export import (
    ExportAttempt,
    ExportDeliveryReceipt,
    ExportTargetSpec,
    ExportWithdrawalAttempt,
)


class ExportTargetPort(Protocol):
    """Destination adapter boundary for export targets."""

    def dispatch(
        self,
        *,
        target: ExportTargetSpec,
        attempt: ExportAttempt,
    ) -> ExportDeliveryReceipt:
        """Deliver output refs and return a canonical receipt."""

    def withdraw(
        self,
        *,
        target: ExportTargetSpec,
        attempt: ExportWithdrawalAttempt,
    ) -> ExportDeliveryReceipt:
        """Propagate withdrawal and return a canonical receipt."""
