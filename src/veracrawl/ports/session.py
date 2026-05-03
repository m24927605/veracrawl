"""Credentialed session port definitions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from veracrawl.contracts.common import Ref
from veracrawl.contracts.security_privacy import CredentialUseAudit


@dataclass(frozen=True)
class CredentialedSessionAdapterResult:
    session_adapter_result_ref: Ref
    session_state_ref: Ref
    redaction_map_refs: list[Ref]
    redacted_artifact_refs: list[Ref]
    redacted_replay_refs: list[Ref]
    policy_decision_refs: list[Ref]
    command_record_refs: list[Ref]
    event_cursor_refs: list[Ref]
    outbox_refs: list[Ref]


class CredentialedSessionAdapterPort(Protocol):
    def establish_session(
        self,
        *,
        fixture_id: str,
        credential_audit: CredentialUseAudit,
        target_origin: str,
    ) -> CredentialedSessionAdapterResult: ...
