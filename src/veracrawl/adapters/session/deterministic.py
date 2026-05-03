"""Deterministic credentialed session adapter."""

from __future__ import annotations

from veracrawl.contracts.security_privacy import CredentialUseAudit
from veracrawl.ports.session import CredentialedSessionAdapterResult


class DeterministicCredentialedSessionAdapter:
    def establish_session(
        self,
        *,
        fixture_id: str,
        credential_audit: CredentialUseAudit,
        target_origin: str,
    ) -> CredentialedSessionAdapterResult:
        return CredentialedSessionAdapterResult(
            session_adapter_result_ref=f"source-result:{fixture_id}:authorized-session",
            session_state_ref=f"session-state-redacted:{fixture_id}:scoped",
            redaction_map_refs=[*credential_audit.redaction_map_refs],
            redacted_artifact_refs=[f"artifact-redacted:{fixture_id}:session"],
            redacted_replay_refs=[credential_audit.replay_bundle_ref],
            policy_decision_refs=[
                *credential_audit.policy_decision_refs,
                f"policy:{fixture_id}:session-adapter",
            ],
            command_record_refs=[
                *credential_audit.command_refs,
                f"durable-command:{fixture_id}:session-adapter",
            ],
            event_cursor_refs=[f"event-cursor:{fixture_id}:session-adapter"],
            outbox_refs=[f"outbox:{fixture_id}:session-adapter"],
        )
