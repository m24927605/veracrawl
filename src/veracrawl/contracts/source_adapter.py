"""Source adapter contract models."""

from __future__ import annotations

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import AdapterResultStatus, AdapterType, SourceAdapterResultType

# Allowed adapter-type escalation transitions per design.md §3.2 (the
# "Adapter escalation chain" diagram, corrected per codex critical #1
# in the v1 review). The chain encodes:
#   - API_SOURCE → HTTP (rate limit / outage path)
#   - API_SOURCE → AUTHORIZED_SESSION (auth issue path)
#   - HTTP → AUTHORIZED_SESSION (access-control blocked + creds available)
#   - HTTP → BROWSER_SNAPSHOT (rendering required, NOT anti-bot escalation)
#   - BROWSER_SNAPSHOT → AUTHORIZED_SESSION (rendered + auth wall)
# AUTHORIZED_SESSION is terminal — escalation cannot leave it because
# downgrading off authorized session has no design-supported semantics.
# Other AdapterType members (SITEMAP / RSS / DOCUMENT_SOURCE /
# FILE_IMPORT / MANUAL_SEED / PRIOR_SNAPSHOT) are non-fetch sources
# whose work product is consumed elsewhere, not escalation targets.
_ALLOWED_ESCALATION_TRANSITIONS: dict[AdapterType, frozenset[AdapterType]] = {
    AdapterType.API_SOURCE: frozenset({AdapterType.HTTP, AdapterType.AUTHORIZED_SESSION}),
    AdapterType.HTTP: frozenset({AdapterType.AUTHORIZED_SESSION, AdapterType.BROWSER_SNAPSHOT}),
    AdapterType.BROWSER_SNAPSHOT: frozenset({AdapterType.AUTHORIZED_SESSION}),
}

ADAPTER_RESULT_MAPPING: dict[AdapterType, set[SourceAdapterResultType]] = {
    AdapterType.HTTP: {
        SourceAdapterResultType.FETCH_RESULT,
        SourceAdapterResultType.BLOCKED_SOURCE,
    },
    AdapterType.SITEMAP: {
        SourceAdapterResultType.DISCOVERED_LINKS,
        SourceAdapterResultType.BLOCKED_SOURCE,
    },
    AdapterType.RSS: {
        SourceAdapterResultType.DISCOVERED_LINKS,
        SourceAdapterResultType.BLOCKED_SOURCE,
    },
    AdapterType.BROWSER_SNAPSHOT: {
        SourceAdapterResultType.BROWSER_SNAPSHOT,
        SourceAdapterResultType.BLOCKED_SOURCE,
    },
    AdapterType.AUTHORIZED_SESSION: {
        SourceAdapterResultType.SESSION_STATE,
        SourceAdapterResultType.BLOCKED_SOURCE,
    },
    AdapterType.API_SOURCE: {
        SourceAdapterResultType.API_PAYLOAD,
        SourceAdapterResultType.BLOCKED_SOURCE,
    },
    AdapterType.DOCUMENT_SOURCE: {
        SourceAdapterResultType.DOCUMENT_ARTIFACT,
        SourceAdapterResultType.BLOCKED_SOURCE,
    },
    AdapterType.FILE_IMPORT: {SourceAdapterResultType.FILE_ARTIFACT},
    AdapterType.MANUAL_SEED: {SourceAdapterResultType.SEED_PLAN},
    AdapterType.PRIOR_SNAPSHOT: {SourceAdapterResultType.PRIOR_SNAPSHOT_REF},
}


class SourceAdapterSpec(TimestampedModel):
    id: str
    name: str
    version: str
    adapter_type: AdapterType
    supported_source_types: list[str] = Field(default_factory=list)
    metadata_schema_ref: Ref
    transformation_schema_ref: Ref
    default_rate_limits: dict[str, object] = Field(default_factory=dict)
    credential_requirements: list[str] = Field(default_factory=list)
    policy_refs: list[Ref] = Field(default_factory=list)
    idempotency_key_template: str
    freshness_semantics: dict[str, object] = Field(default_factory=dict)


class SourceAdapterResult(TimestampedModel):
    id: str
    run_id: str
    adapter_spec_id: str
    adapter_type: AdapterType
    result_type: SourceAdapterResultType
    output_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    replay_event_refs: list[Ref] = Field(default_factory=list)
    idempotency_key: str
    status: AdapterResultStatus

    @model_validator(mode="after")
    def validate_result_mapping(self) -> SourceAdapterResult:
        if self.result_type not in ADAPTER_RESULT_MAPPING[self.adapter_type]:
            raise ValueError(
                f"{self.adapter_type.value} cannot emit result_type {self.result_type.value}"
            )
        if self.status == AdapterResultStatus.BLOCKED:
            if self.result_type != SourceAdapterResultType.BLOCKED_SOURCE:
                raise ValueError("blocked adapter results must use blocked_source result_type")
            if not self.policy_decision_refs:
                raise ValueError("blocked adapter results require policy_decision_refs")
        if self.status == AdapterResultStatus.SUCCEEDED and not self.output_refs:
            raise ValueError("succeeded adapter results require output_refs")
        if self.result_type in {
            SourceAdapterResultType.SEED_PLAN,
            SourceAdapterResultType.PRIOR_SNAPSHOT_REF,
            SourceAdapterResultType.DOCUMENT_ARTIFACT,
            SourceAdapterResultType.FILE_ARTIFACT,
            SourceAdapterResultType.SESSION_STATE,
        }:
            forbidden = [
                ref for ref in self.output_refs if ref.startswith(("fetch:", "page_snapshot:"))
            ]
            if forbidden:
                raise ValueError("non-fetch adapter result must not emit fetch/page snapshot refs")
        return self


class SourceAdapterCommand(TimestampedModel):
    command_envelope_id: str
    adapter_spec: SourceAdapterSpec
    source_ref: Ref
    policy_snapshot_ref: Ref
    deterministic_clock_ref: Ref | None = None
    randomness_seed_ref: Ref | None = None
    credential_scope_ref: Ref | None = None


# ---------------------------------------------------------------------------
# v2 contracts (production-authorized-source-crawler design §3.5).
#
# The Phase 3 ``PolicyDrivenEscalator`` walks adapter types in a
# policy-bounded chain (HTTP → BROWSER_SNAPSHOT → AUTHORIZED_SESSION,
# never the reverse, and never to anything the policy hasn't admitted)
# and emits an ``AdapterEscalationDecision`` per transition. The
# ``AdapterEscalationPolicy`` is the static spec orchestrators load
# from config; it is NOT mutated at runtime.
# ---------------------------------------------------------------------------


class AdapterEscalationDecision(TimestampedModel):
    """Typed transition from one adapter type to another within a run.

    Produced by the Phase 3 ``PolicyDrivenEscalator`` whenever a
    failure (typed via ``failure_signature``) makes it pointless to
    retry the same adapter type — for example, an HTTP adapter
    receiving a Cloudflare challenge escalates to an authorized
    session adapter that is allowed to carry a credential. The
    ``triggered_by_ref`` points to the structured failure that
    motivated the transition (typically ``NetworkAttemptEvidence``
    or ``AccessControlBlocked``).
    """

    id: str
    run_ref: Ref
    from_adapter_type: AdapterType
    to_adapter_type: AdapterType
    reason: str
    failure_signature: str
    policy_ref: Ref
    triggered_by_ref: Ref

    @model_validator(mode="after")
    def validate_decision(self) -> AdapterEscalationDecision:
        if self.from_adapter_type is self.to_adapter_type:
            raise ValueError(
                "adapter escalation decision must change adapter_type "
                "(from_adapter_type != to_adapter_type)"
            )
        allowed = _ALLOWED_ESCALATION_TRANSITIONS.get(self.from_adapter_type, frozenset())
        if self.to_adapter_type not in allowed:
            raise ValueError(
                f"adapter escalation decision {self.from_adapter_type.value} → "
                f"{self.to_adapter_type.value} is not in the design-allowed "
                f"escalation chain (design.md §3.2); allowed targets from "
                f"{self.from_adapter_type.value}: "
                f"{sorted(t.value for t in allowed)}"
            )
        if not self.reason.strip():
            raise ValueError("adapter escalation decision reason must be non-blank")
        if not self.failure_signature.strip():
            raise ValueError("adapter escalation decision failure_signature must be non-blank")
        return self


class AdapterEscalationPolicy(TimestampedModel):
    """Static spec describing which adapter-type transitions are allowed.

    ``allowed_transitions`` keys are the source adapter types; values
    are the lists of admissible target adapter types. The structure is
    asymmetric on purpose — escalating HTTP → AUTHORIZED_SESSION does
    not imply the reverse is allowed. ``requires_review`` flips the
    policy into "every escalation needs an operator approval" mode,
    used for sensitive sources. ``max_escalations_per_run`` caps
    runaway chains; the docstring rules out zero / negative because a
    policy that admits no transitions is a misconfiguration (callers
    should drop the policy ref instead).
    """

    id: str
    name: str
    allowed_transitions: dict[AdapterType, list[AdapterType]] = Field(default_factory=dict)
    requires_review: bool = False
    max_escalations_per_run: int = 1

    @model_validator(mode="after")
    def validate_policy(self) -> AdapterEscalationPolicy:
        if not self.name.strip():
            raise ValueError("adapter escalation policy name must be non-blank")
        if self.max_escalations_per_run < 1:
            raise ValueError(
                "adapter escalation policy max_escalations_per_run must be >= 1; "
                "drop the policy ref to express 'no escalation allowed'"
            )
        for source, targets in self.allowed_transitions.items():
            if not targets:
                raise ValueError(
                    f"adapter escalation policy entry {source.value} has empty target list; "
                    "drop the entry instead of recording dead policy"
                )
            if source in targets:
                raise ValueError(
                    f"adapter escalation policy must not list {source.value} as its own target"
                )
            if len(set(targets)) != len(targets):
                raise ValueError(
                    f"adapter escalation policy entry {source.value} contains duplicate targets"
                )
            design_allowed = _ALLOWED_ESCALATION_TRANSITIONS.get(source, frozenset())
            disallowed = sorted(t.value for t in targets if t not in design_allowed)
            if disallowed:
                raise ValueError(
                    f"adapter escalation policy entry {source.value} → "
                    f"{disallowed} is not in the design-allowed escalation chain "
                    f"(design.md §3.2); allowed targets from {source.value}: "
                    f"{sorted(t.value for t in design_allowed)}"
                )
        return self
