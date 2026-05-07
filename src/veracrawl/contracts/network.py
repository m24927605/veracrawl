"""Network acquisition contracts."""

from __future__ import annotations

from urllib.parse import urlparse

from pydantic import Field, model_validator

from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import (
    AccessControlProvider,
    CompletenessResult,
    LiveHttpAcquisitionFailureType,
)


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _is_valid_http_status(value: int) -> bool:
    return 100 <= value <= 599


# Header names whose value carries a credential or session secret.
# When NetworkAttemptEvidence stores these, the value must already be
# redacted by the producer; persisting the raw bearer / cookie / api
# key into evidence defeats the contract's privacy classification and
# the design's per-attempt redaction acceptance criteria (Phase 1).
_SENSITIVE_HEADER_NAMES = frozenset(
    {
        "authorization",
        "cookie",
        "set-cookie",
        "proxy-authorization",
        "x-api-key",
        "x-auth-token",
        "x-session-token",
        "x-csrf-token",
    }
)
_REDACTION_MARKERS = ("[REDACTED]", "<REDACTED>", "***", "REDACTED")


def _header_value_looks_redacted(value: str) -> bool:
    """A redacted header value is empty or contains a redaction marker.

    The producer is responsible for the actual redaction; this contract
    just verifies the producer didn't forget — a missed redaction is
    almost always an upstream wiring bug, and persisting the raw value
    into a privacy-classified evidence row is exactly the regression we
    want to catch at construction time.
    """
    if not value.strip():
        return True
    upper = value.upper()
    return any(marker in upper for marker in _REDACTION_MARKERS)


def _validate_redacted_headers(headers: dict[str, str], field_name: str) -> None:
    for raw_name, raw_value in headers.items():
        if raw_name.lower() in _SENSITIVE_HEADER_NAMES and not _header_value_looks_redacted(
            raw_value
        ):
            raise ValueError(
                f"{field_name} sensitive header {raw_name!r} value must be redacted; "
                "expected a redaction marker (e.g., '[REDACTED]') or empty string"
            )


class NetworkRequest(TimestampedModel):
    id: str
    run_ref: Ref
    source_ref: Ref
    url: str
    method: str = "GET"
    headers_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    egress_policy_ref: Ref
    private_network_policy_ref: Ref
    robots_policy_ref: Ref
    rate_budget_ref: Ref
    size_budget_bytes: int
    timeout_ms: int
    idempotency_key: str

    @model_validator(mode="after")
    def validate_request(self) -> NetworkRequest:
        if not _is_http_url(self.url):
            raise ValueError("network request url must be absolute http(s)")
        if self.method not in {"GET", "HEAD"}:
            raise ValueError("network request method must be read-only")
        if not self.policy_decision_refs:
            raise ValueError("network request requires policy decisions")
        if self.size_budget_bytes < 1 or self.timeout_ms < 1:
            raise ValueError("network request budgets must be positive")
        return self


class RedirectHop(TimestampedModel):
    id: str
    request_ref: Ref
    sequence: int
    from_url: str
    to_url: str
    status_code: int
    policy_decision_refs: list[Ref] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_hop(self) -> RedirectHop:
        if self.sequence < 1:
            raise ValueError("redirect sequence must be positive")
        if not _is_http_url(self.from_url) or not _is_http_url(self.to_url):
            raise ValueError("redirect urls must be absolute http(s)")
        if not self.policy_decision_refs:
            raise ValueError("redirect hop requires policy decisions")
        return self


class NetworkResponse(TimestampedModel):
    id: str
    request_ref: Ref
    status_code: int
    final_url: str
    headers_ref: Ref
    raw_artifact_ref: Ref | None = None
    content_digest: str | None = None
    content_type: str | None = None
    body_size_bytes: int = 0
    redirect_hop_refs: list[Ref] = Field(default_factory=list)
    timing_ref: Ref

    @model_validator(mode="after")
    def validate_response(self) -> NetworkResponse:
        if not _is_http_url(self.final_url):
            raise ValueError("network response final_url must be absolute http(s)")
        if self.status_code < 100 or self.status_code > 599:
            raise ValueError("network response status_code must be valid HTTP")
        if self.body_size_bytes < 0:
            raise ValueError("network response body size cannot be negative")
        if 200 <= self.status_code < 400:
            if not self.raw_artifact_ref or not self.content_digest or not self.content_type:
                raise ValueError("successful network response requires raw artifact metadata")
        return self


class NetworkAcquisitionReport(TimestampedModel):
    id: str
    run_ref: Ref
    network_request_ref: Ref | None = None
    network_response_ref: Ref | None = None
    redirect_hop_refs: list[Ref] = Field(default_factory=list)
    browser_step_ref: Ref | None = None
    source_acquisition_report_ref: Ref | None = None
    artifact_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    recovery_report_refs: list[Ref] = Field(default_factory=list)
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    operator_status: str
    completion_result: CompletenessResult

    @model_validator(mode="after")
    def validate_report(self) -> NetworkAcquisitionReport:
        if self.completion_result == CompletenessResult.PASS:
            required = {
                "network_request_ref": self.network_request_ref,
                "source_acquisition_report_ref": self.source_acquisition_report_ref,
                "artifact_refs": self.artifact_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "recovery_report_refs": self.recovery_report_refs,
            }
            if not (self.network_response_ref or self.browser_step_ref):
                required["network_response_or_browser_step_ref"] = None
            missing = [name for name, value in required.items() if not value]
            if missing or self.missing_ref_fields:
                raise ValueError(f"passing network acquisition report missing refs: {missing}")
        if self.completion_result != CompletenessResult.PASS and not (
            self.failure_report_refs or self.missing_ref_fields
        ):
            raise ValueError(
                "non-pass network acquisition report requires failures or missing refs"
            )
        return self


class LiveHttpAcquisitionReport(TimestampedModel):
    id: str
    fixture_id: str
    run_ref: Ref
    run_control_report_ref: Ref | None = None
    production_persistence_report_ref: Ref | None = None
    network_request_ref: Ref | None = None
    network_response_ref: Ref | None = None
    redirect_hop_refs: list[Ref] = Field(default_factory=list)
    source_acquisition_report_ref: Ref | None = None
    source_adapter_result_refs: list[Ref] = Field(default_factory=list)
    fetch_attempt_refs: list[Ref] = Field(default_factory=list)
    fetch_result_refs: list[Ref] = Field(default_factory=list)
    page_snapshot_refs: list[Ref] = Field(default_factory=list)
    source_observation_refs: list[Ref] = Field(default_factory=list)
    artifact_refs: list[Ref] = Field(default_factory=list)
    content_hash_refs: list[Ref] = Field(default_factory=list)
    canonical_url_refs: list[Ref] = Field(default_factory=list)
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref | None = None
    failure_report_refs: list[Ref] = Field(default_factory=list)
    missing_ref_fields: list[str] = Field(default_factory=list)
    failure_type: LiveHttpAcquisitionFailureType | None = None
    operator_status: str
    completion_result: CompletenessResult
    diagnostics: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_live_http_report(self) -> LiveHttpAcquisitionReport:
        if self.completion_result == CompletenessResult.PASS:
            required: dict[str, object] = {
                "run_control_report_ref": self.run_control_report_ref,
                "production_persistence_report_ref": self.production_persistence_report_ref,
                "network_request_ref": self.network_request_ref,
                "network_response_ref": self.network_response_ref,
                "source_acquisition_report_ref": self.source_acquisition_report_ref,
                "source_adapter_result_refs": self.source_adapter_result_refs,
                "fetch_attempt_refs": self.fetch_attempt_refs,
                "fetch_result_refs": self.fetch_result_refs,
                "page_snapshot_refs": self.page_snapshot_refs,
                "source_observation_refs": self.source_observation_refs,
                "artifact_refs": self.artifact_refs,
                "content_hash_refs": self.content_hash_refs,
                "canonical_url_refs": self.canonical_url_refs,
                "policy_decision_refs": self.policy_decision_refs,
                "command_record_refs": self.command_record_refs,
                "event_cursor_refs": self.event_cursor_refs,
                "outbox_refs": self.outbox_refs,
                "replay_bundle_ref": self.replay_bundle_ref,
            }
            missing = [name for name, value in required.items() if not value]
            if (
                missing
                or self.failure_type is not None
                or self.failure_report_refs
                or self.missing_ref_fields
            ):
                raise ValueError(f"passing live HTTP acquisition report missing refs: {missing}")
        elif not (self.failure_type and (self.failure_report_refs or self.missing_ref_fields)):
            raise ValueError("non-pass live HTTP acquisition report requires typed diagnostics")
        return self


class LiveHttpAcquisitionFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    path: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: CompletenessResult
    expected_operator_status: str
    expected_failure_type: LiveHttpAcquisitionFailureType | None = None
    negative_case: bool = False
    required_ref_types: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_live_http_fixture(self) -> LiveHttpAcquisitionFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("live HTTP fixture must support target profile")
        if not self.required_ref_types:
            raise ValueError("live HTTP fixture must declare required ref types")
        if self.negative_case:
            if self.expected_completion_result == CompletenessResult.PASS:
                raise ValueError("negative live HTTP fixture must not expect pass")
            if self.expected_failure_type is None:
                raise ValueError("negative live HTTP fixture requires failure type")
        return self


class NetworkFixtureManifest(TimestampedModel):
    id: str
    scenario: str
    acquisition_type: str
    path: str
    profile_refs: list[str] = Field(default_factory=list)
    expected_completion_result: str
    expected_operator_status: str
    negative_case: bool = False

    @model_validator(mode="after")
    def validate_fixture(self) -> NetworkFixtureManifest:
        if "target" not in self.profile_refs:
            raise ValueError("network fixture must support target profile")
        if self.acquisition_type not in {"http", "browser"}:
            raise ValueError("network fixture acquisition_type must be http or browser")
        if self.negative_case and self.expected_completion_result == "pass":
            raise ValueError("negative network fixture must not expect pass")
        return self


# ---------------------------------------------------------------------------
# v2 contracts (production-authorized-source-crawler design §3.5).
#
# Phase 1 populates ``NetworkAttemptEvidence`` on every HTTP / browser
# attempt. Phase 3 ``AccessControlClassifier`` produces
# ``AccessControlBlocked`` when origin-side protection is detected;
# the contract is charter-scoped — the classifier identifies and
# surfaces, never solves or bypasses (``docs/09:116`` §Safety Boundary).
# ---------------------------------------------------------------------------


class NetworkAttemptEvidence(TimestampedModel):
    """Per-attempt evidence sidecar populated by the cooperative HTTP /
    browser paths.

    Phase 1 attaches one ``NetworkAttemptEvidence`` per attempt to
    ``NetworkClientResult.attempt_evidences`` so retry / redirect /
    failure analysis has a typed record per try. Headers must already
    be redacted by the producer — this contract stores the redacted
    view; it does not perform redaction itself. The combination of
    ``response_status is None`` and ``response_headers_redacted is
    None`` indicates the request never reached an HTTP response
    (timeout, connection refused, TLS error); in that case
    ``failure_class`` is required so the orchestrator can classify
    the attempt.
    """

    id: str
    run_ref: Ref
    request_ref: Ref
    attempt_number: int
    request_method: str
    request_url: str
    request_headers_redacted: dict[str, str] = Field(default_factory=dict)
    response_status: int | None = None
    response_headers_redacted: dict[str, str] | None = None
    elapsed_ms: int
    failure_class: str | None = None
    redirect_hop_count: int = 0

    @model_validator(mode="after")
    def validate_attempt_evidence(self) -> NetworkAttemptEvidence:
        if not _is_http_url(self.request_url):
            raise ValueError("attempt evidence request_url must be absolute http(s)")
        if not self.request_method.strip():
            raise ValueError("attempt evidence request_method must be non-blank")
        if self.attempt_number < 1:
            raise ValueError("attempt evidence attempt_number must be >= 1")
        if self.elapsed_ms < 0:
            raise ValueError("attempt evidence elapsed_ms must be non-negative")
        if self.redirect_hop_count < 0:
            raise ValueError("attempt evidence redirect_hop_count must be non-negative")
        if self.response_status is not None and not _is_valid_http_status(self.response_status):
            raise ValueError("attempt evidence response_status must be a valid HTTP status")
        if self.response_status is None and self.response_headers_redacted is not None:
            raise ValueError("attempt evidence cannot record response headers without a status")
        if self.response_status is not None and self.response_headers_redacted is None:
            raise ValueError(
                "attempt evidence with response_status requires response_headers_redacted"
            )
        if self.response_status is None and self.failure_class is None:
            raise ValueError(
                "attempt evidence with no response requires failure_class to classify the attempt"
            )
        _validate_redacted_headers(
            self.request_headers_redacted, "attempt evidence request_headers_redacted"
        )
        if self.response_headers_redacted is not None:
            _validate_redacted_headers(
                self.response_headers_redacted,
                "attempt evidence response_headers_redacted",
            )
        return self


class AccessControlBlocked(TimestampedModel):
    """Typed payload from the Phase 3 ``AccessControlClassifier``.

    The classifier reads response headers, body fingerprints, and
    challenge markers to identify which origin-side protection is in
    front of the URL (Cloudflare / Turnstile / DataDome / PerimeterX
    / Akamai / login-wall / generic CAPTCHA) and produces an
    ``AccessControlBlocked`` instead of attempting any kind of
    bypass. Downstream policy (``AdapterEscalationPolicy`` / Phase 5
    ``RecoveryPort``) decides whether to escalate to authorized
    session, request operator review, or abandon.

    A claim of detection without supporting evidence is a silent
    false positive — ``detection_signal_refs`` must therefore be
    non-empty.
    """

    id: str
    run_ref: Ref
    url: str
    detected_provider: AccessControlProvider
    detection_signal_refs: list[Ref] = Field(default_factory=list)
    response_status: int
    attempt_evidence_ref: Ref | None = None

    @model_validator(mode="after")
    def validate_access_control_blocked(self) -> AccessControlBlocked:
        if not _is_http_url(self.url):
            raise ValueError("access control blocked url must be absolute http(s)")
        if not _is_valid_http_status(self.response_status):
            raise ValueError("access control blocked response_status must be valid HTTP")
        if not self.detection_signal_refs:
            raise ValueError("access control blocked requires at least one detection_signal_ref")
        return self
