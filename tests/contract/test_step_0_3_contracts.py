"""Contract tests for Phase 0 step 0.3.

Adds six framework-neutral contracts the v2 design (see
docs/plans/production-authorized-source-crawler/design.md §3.5)
needs in phases 1-3:

* ``NetworkAttemptEvidence`` (``contracts.network``) — per-attempt
  evidence sidecar populated by Phase 1 cooperative HTTP / browser
  paths (``NetworkClientResult.attempt_evidences``).
* ``AccessControlBlocked`` (``contracts.network``) — typed payload
  produced by the Phase 3 ``AccessControlClassifier`` when it
  recognises Cloudflare / DataDome / etc. fingerprints. Charter-
  respected: classify and surface, never solve.
* ``AdapterEscalationDecision`` and ``AdapterEscalationPolicy``
  (``contracts.source_adapter``) — policy-driven transition between
  adapter types (e.g., HTTP → AUTHORIZED_SESSION) used by Phase 3
  ``PolicyDrivenEscalator``.
* ``CredentialScope`` and ``CredentialUseRecord``
  (``contracts.security_privacy``) — the scope spec the Phase 2
  ``StrictAllowlistScope`` enforces, and the outbox record the
  ``AuthorizedSessionAdapter`` writes on every credential-bearing
  request. Both must reference credentials by *handle*; the actual
  secret is never stored on either contract.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from veracrawl.contracts.enums import AccessControlProvider, AdapterType
from veracrawl.contracts.network import AccessControlBlocked, NetworkAttemptEvidence
from veracrawl.contracts.security_privacy import CredentialScope, CredentialUseRecord
from veracrawl.contracts.source_adapter import (
    AdapterEscalationDecision,
    AdapterEscalationPolicy,
)

# NetworkAttemptEvidence ------------------------------------------


def _valid_attempt_evidence(**overrides: object) -> NetworkAttemptEvidence:
    defaults: dict[str, object] = {
        "id": "attempt-evidence:1",
        "run_ref": "run:1",
        "request_ref": "network-request:1",
        "attempt_number": 1,
        "request_method": "GET",
        "request_url": "https://example.test/p/1",
        "request_headers_redacted": {"User-Agent": "VeraCrawl/1.0"},
        "response_status": 200,
        "response_headers_redacted": {"Content-Type": "text/html"},
        "elapsed_ms": 142,
        "redirect_hop_count": 0,
    }
    defaults.update(overrides)
    return NetworkAttemptEvidence.model_validate(defaults)


def test_attempt_evidence_minimal_valid_with_response() -> None:
    ev = _valid_attempt_evidence()
    assert ev.failure_class is None
    assert ev.response_status == 200


def test_attempt_evidence_minimal_valid_without_response() -> None:
    ev = _valid_attempt_evidence(
        response_status=None,
        response_headers_redacted=None,
        failure_class="network_timeout",
    )
    assert ev.response_status is None
    assert ev.failure_class == "network_timeout"


def test_attempt_evidence_rejects_zero_attempt_number() -> None:
    with pytest.raises(ValidationError):
        _valid_attempt_evidence(attempt_number=0)


def test_attempt_evidence_rejects_negative_elapsed() -> None:
    with pytest.raises(ValidationError):
        _valid_attempt_evidence(elapsed_ms=-1)


def test_attempt_evidence_rejects_non_http_url() -> None:
    with pytest.raises(ValidationError):
        _valid_attempt_evidence(request_url="file:///etc/passwd")


def test_attempt_evidence_rejects_blank_method() -> None:
    with pytest.raises(ValidationError):
        _valid_attempt_evidence(request_method="")


def test_attempt_evidence_rejects_negative_redirect_count() -> None:
    with pytest.raises(ValidationError):
        _valid_attempt_evidence(redirect_hop_count=-1)


def test_attempt_evidence_rejects_status_out_of_range() -> None:
    with pytest.raises(ValidationError):
        _valid_attempt_evidence(response_status=99)


def test_attempt_evidence_rejects_response_headers_without_status() -> None:
    """A populated response headers dict but a None status means the
    producer mis-recorded the result — either the request reached an
    origin (status set) or it failed before any response headers
    arrived (both None)."""
    with pytest.raises(ValidationError):
        _valid_attempt_evidence(
            response_status=None,
            response_headers_redacted={"Content-Type": "text/html"},
            failure_class="network_timeout",
        )


def test_attempt_evidence_rejects_status_without_headers() -> None:
    with pytest.raises(ValidationError):
        _valid_attempt_evidence(
            response_status=200,
            response_headers_redacted=None,
        )


def test_attempt_evidence_no_response_requires_failure_class() -> None:
    with pytest.raises(ValidationError):
        _valid_attempt_evidence(
            response_status=None,
            response_headers_redacted=None,
            failure_class=None,
        )


# AccessControlBlocked --------------------------------------------


def _valid_access_control_blocked(**overrides: object) -> AccessControlBlocked:
    defaults: dict[str, object] = {
        "id": "access-control-blocked:1",
        "run_ref": "run:1",
        "url": "https://example.test/p/1",
        "detected_provider": AccessControlProvider.CLOUDFLARE,
        "detection_signal_refs": ["evidence:cf-cookie-fingerprint"],
        "response_status": 403,
    }
    defaults.update(overrides)
    return AccessControlBlocked.model_validate(defaults)


def test_access_control_blocked_minimal_valid() -> None:
    blocked = _valid_access_control_blocked()
    assert blocked.detected_provider is AccessControlProvider.CLOUDFLARE
    assert blocked.attempt_evidence_ref is None


def test_access_control_blocked_with_attempt_evidence_ref() -> None:
    blocked = _valid_access_control_blocked(attempt_evidence_ref="attempt-evidence:1")
    assert blocked.attempt_evidence_ref == "attempt-evidence:1"


def test_access_control_blocked_unknown_provider_allowed() -> None:
    """A genuinely unrecognised wall must still produce a typed
    contract with provider=UNKNOWN; otherwise the classifier's
    fallback case has nowhere to land."""
    blocked = _valid_access_control_blocked(detected_provider=AccessControlProvider.UNKNOWN)
    assert blocked.detected_provider is AccessControlProvider.UNKNOWN


def test_access_control_blocked_rejects_empty_detection_signals() -> None:
    """A claim of detection without evidence is exactly the kind of
    silent false-positive the charter forbids — surface only what
    evidence supports."""
    with pytest.raises(ValidationError):
        _valid_access_control_blocked(detection_signal_refs=[])


def test_access_control_blocked_rejects_non_http_url() -> None:
    with pytest.raises(ValidationError):
        _valid_access_control_blocked(url="file:///etc/passwd")


def test_access_control_blocked_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        _valid_access_control_blocked(response_status=99)


# AdapterEscalationDecision ---------------------------------------


def _valid_escalation_decision(**overrides: object) -> AdapterEscalationDecision:
    defaults: dict[str, object] = {
        "id": "escalation-decision:1",
        "run_ref": "run:1",
        "from_adapter_type": AdapterType.HTTP,
        "to_adapter_type": AdapterType.AUTHORIZED_SESSION,
        "reason": "access_control_blocked:cloudflare",
        "failure_signature": "cf:example.test:403",
        "policy_ref": "policy:adapter-escalation",
        "triggered_by_ref": "access-control-blocked:1",
    }
    defaults.update(overrides)
    return AdapterEscalationDecision.model_validate(defaults)


def test_escalation_decision_minimal_valid() -> None:
    decision = _valid_escalation_decision()
    assert decision.from_adapter_type is AdapterType.HTTP
    assert decision.to_adapter_type is AdapterType.AUTHORIZED_SESSION


def test_escalation_decision_rejects_self_escalation() -> None:
    with pytest.raises(ValidationError):
        _valid_escalation_decision(
            from_adapter_type=AdapterType.HTTP,
            to_adapter_type=AdapterType.HTTP,
        )


def test_escalation_decision_rejects_blank_reason() -> None:
    with pytest.raises(ValidationError):
        _valid_escalation_decision(reason="   ")


def test_escalation_decision_rejects_blank_signature() -> None:
    with pytest.raises(ValidationError):
        _valid_escalation_decision(failure_signature="")


# AdapterEscalationPolicy -----------------------------------------


def _valid_escalation_policy(**overrides: object) -> AdapterEscalationPolicy:
    defaults: dict[str, object] = {
        "id": "policy:adapter-escalation",
        "name": "default-escalation",
        "allowed_transitions": {
            AdapterType.HTTP: [AdapterType.BROWSER_SNAPSHOT, AdapterType.AUTHORIZED_SESSION],
            AdapterType.BROWSER_SNAPSHOT: [AdapterType.AUTHORIZED_SESSION],
        },
        "requires_review": False,
        "max_escalations_per_run": 3,
    }
    defaults.update(overrides)
    return AdapterEscalationPolicy.model_validate(defaults)


def test_escalation_policy_minimal_valid() -> None:
    policy = _valid_escalation_policy()
    assert policy.requires_review is False
    assert policy.max_escalations_per_run == 3


def test_escalation_policy_rejects_zero_max_escalations() -> None:
    """A policy that allows zero escalations is functionally an
    always-deny policy and almost certainly indicates a wiring bug.
    A producer expressing 'no escalation allowed' should drop the
    policy reference instead."""
    with pytest.raises(ValidationError):
        _valid_escalation_policy(max_escalations_per_run=0)


def test_escalation_policy_rejects_negative_max_escalations() -> None:
    with pytest.raises(ValidationError):
        _valid_escalation_policy(max_escalations_per_run=-1)


def test_escalation_policy_rejects_blank_name() -> None:
    with pytest.raises(ValidationError):
        _valid_escalation_policy(name="   ")


def test_escalation_policy_rejects_self_transition_in_allowed() -> None:
    """``HTTP → HTTP`` does no escalation work and indicates a
    misconfigured policy."""
    with pytest.raises(ValidationError):
        _valid_escalation_policy(
            allowed_transitions={
                AdapterType.HTTP: [AdapterType.HTTP, AdapterType.AUTHORIZED_SESSION],
            },
        )


def test_escalation_policy_rejects_empty_transition_value() -> None:
    """An entry mapping a source adapter type to an empty list of
    targets is dead policy — the producer should omit the entry
    instead."""
    with pytest.raises(ValidationError):
        _valid_escalation_policy(
            allowed_transitions={AdapterType.HTTP: []},
        )


def test_escalation_policy_rejects_duplicate_targets() -> None:
    with pytest.raises(ValidationError):
        _valid_escalation_policy(
            allowed_transitions={
                AdapterType.HTTP: [AdapterType.AUTHORIZED_SESSION, AdapterType.AUTHORIZED_SESSION],
            },
        )


# CredentialScope --------------------------------------------------


def _valid_credential_scope(**overrides: object) -> CredentialScope:
    defaults: dict[str, object] = {
        "id": "credential-scope:ebay",
        "credential_handle_ref": "credential-vault:ebay-prod",
        "allowed_origins": ["https://api.ebay.com"],
        "allowed_route_patterns": ["^/buy/browse/v1/.*"],
        "allowed_methods": ["GET"],
    }
    defaults.update(overrides)
    return CredentialScope.model_validate(defaults)


def test_credential_scope_minimal_valid() -> None:
    scope = _valid_credential_scope()
    assert scope.expires_at is None
    assert scope.allowed_methods == ["GET"]


def test_credential_scope_with_expiration() -> None:
    expiry = datetime.now(tz=UTC) + timedelta(days=30)
    scope = _valid_credential_scope(expires_at=expiry)
    assert scope.expires_at == expiry


def test_credential_scope_rejects_blank_handle() -> None:
    with pytest.raises(ValidationError):
        _valid_credential_scope(credential_handle_ref="   ")


def test_credential_scope_rejects_empty_allowed_origins() -> None:
    """A scope without allowed origins admits no requests; it's a
    misconfiguration, not a valid 'deny all'."""
    with pytest.raises(ValidationError):
        _valid_credential_scope(allowed_origins=[])


def test_credential_scope_rejects_non_http_origin() -> None:
    with pytest.raises(ValidationError):
        _valid_credential_scope(allowed_origins=["javascript:alert(1)"])


def test_credential_scope_rejects_unsupported_method() -> None:
    with pytest.raises(ValidationError):
        _valid_credential_scope(allowed_methods=["TRACE"])


def test_credential_scope_rejects_lowercase_method() -> None:
    with pytest.raises(ValidationError):
        _valid_credential_scope(allowed_methods=["get"])


def test_credential_scope_rejects_empty_allowed_methods() -> None:
    with pytest.raises(ValidationError):
        _valid_credential_scope(allowed_methods=[])


def test_credential_scope_rejects_naive_expiration() -> None:
    """Naive datetimes (no tzinfo) make replay non-deterministic
    across machines — only timezone-aware values are accepted, in
    line with the rest of the contracts package."""
    with pytest.raises(ValidationError):
        _valid_credential_scope(expires_at=datetime(2026, 12, 31))  # noqa: DTZ001


def test_credential_scope_accepts_past_expiration() -> None:
    """Contracts validate shape, not time-of-day truth. A scope
    serialized while valid must still be loadable by the registry,
    audit replay, and outbox replay paths after expiry; otherwise
    deterministic round-trips would break the moment a scope's TTL
    elapsed. ``StrictAllowlistScope`` (Phase 2 step 2.2) is the
    runtime policy that rejects expired scopes at request build
    time."""
    expiry = datetime(2020, 1, 1, tzinfo=UTC)
    scope = _valid_credential_scope(expires_at=expiry)
    assert scope.expires_at == expiry


# CredentialUseRecord ---------------------------------------------


def _valid_credential_use_record(**overrides: object) -> CredentialUseRecord:
    defaults: dict[str, object] = {
        "id": "credential-use:1",
        "run_ref": "run:1",
        "credential_scope_ref": "credential-scope:ebay",
        "request_url": "https://api.ebay.com/buy/browse/v1/item/123",
        "request_method": "GET",
        "response_status": 200,
        "timestamp_used": datetime.now(tz=UTC),
    }
    defaults.update(overrides)
    return CredentialUseRecord.model_validate(defaults)


def test_credential_use_record_minimal_valid() -> None:
    record = _valid_credential_use_record()
    assert record.attempt_evidence_ref is None


def test_credential_use_record_with_failure() -> None:
    record = _valid_credential_use_record(
        response_status=None,
        attempt_evidence_ref="attempt-evidence:1",
    )
    assert record.response_status is None
    assert record.attempt_evidence_ref == "attempt-evidence:1"


def test_credential_use_record_rejects_non_http_url() -> None:
    with pytest.raises(ValidationError):
        _valid_credential_use_record(request_url="file:///etc/passwd")


def test_credential_use_record_rejects_blank_method() -> None:
    with pytest.raises(ValidationError):
        _valid_credential_use_record(request_method="")


def test_credential_use_record_rejects_invalid_status() -> None:
    with pytest.raises(ValidationError):
        _valid_credential_use_record(response_status=99)


def test_credential_use_record_rejects_naive_timestamp() -> None:
    with pytest.raises(ValidationError):
        _valid_credential_use_record(timestamp_used=datetime(2026, 5, 7, 0, 0, 0))  # noqa: DTZ001


# Codex iter-1 fix-up: route patterns required + compilable -------


def test_credential_scope_rejects_empty_route_patterns() -> None:
    """An origin-only scope (no route patterns) would let
    StrictAllowlistScope admit any path under the origin, defeating
    the docs/09 fine-grained scope rule."""
    with pytest.raises(ValidationError):
        _valid_credential_scope(allowed_route_patterns=[])


def test_credential_scope_rejects_uncompilable_route_pattern() -> None:
    """A bogus regex (e.g., trailing ``[``) is silently fail-open at
    request time on most regex implementations; reject it here so
    StrictAllowlistScope never has to see one."""
    with pytest.raises(ValidationError):
        _valid_credential_scope(allowed_route_patterns=["^/bad("])


@pytest.mark.parametrize(
    "catch_all",
    [
        ".*",
        ".+",
        "^.*$",
        "^.+$",
        "^/$",
        "/",
        "^/.*$",
        "/.*",
        "/.+",
    ],
)
def test_credential_scope_rejects_catch_all_route_pattern(catch_all: str) -> None:
    """A catch-all route pattern would let StrictAllowlistScope admit
    every URL under the origin, defeating the fine-grained scope
    rule. The ``allowed_origins`` field already expresses
    origin-wide policy."""
    with pytest.raises(ValidationError):
        _valid_credential_scope(allowed_route_patterns=[catch_all])


@pytest.mark.parametrize(
    "unanchored",
    [
        "buy/browse/v1/.*",  # missing leading /
        ".*/api",  # not path-anchored
        "browse",  # bare path component
    ],
)
def test_credential_scope_rejects_unanchored_route_pattern(unanchored: str) -> None:
    """The contract requires path anchoring so origin policy stays
    expressed via ``allowed_origins`` and route policy stays
    expressed via ``allowed_route_patterns``."""
    with pytest.raises(ValidationError):
        _valid_credential_scope(allowed_route_patterns=[unanchored])


@pytest.mark.parametrize(
    "redos",
    [
        "^/buy/(.*)+/v1",
        "^/buy/(.+)+",
        "^/(.*)*",
        "^/(.+)*",
        "^/(.*?)+",
        "^/(.+?)+",
    ],
)
def test_credential_scope_rejects_redos_prone_route_pattern(redos: str) -> None:
    """Nested-quantifier constructs like ``(.*)+`` are catastrophic-
    backtracking ReDoS risk. Refuse at the contract layer; runtime-
    side hardening is Phase 2 step 2.2's job."""
    with pytest.raises(ValidationError):
        _valid_credential_scope(allowed_route_patterns=[redos])


def test_credential_scope_rejects_oversize_route_pattern() -> None:
    big = "^/buy/browse/v1/" + "x" * 300
    with pytest.raises(ValidationError):
        _valid_credential_scope(allowed_route_patterns=[big])


def test_credential_scope_accepts_realistic_route_patterns() -> None:
    """Realistic patterns the design's V1 targets actually use must
    keep validating."""
    scope = _valid_credential_scope(
        allowed_route_patterns=[
            "^/buy/browse/v1/item/.*",
            "/products/[0-9]+",
            "^/api/v[0-9]+/orders/.+/items$",
        ],
    )
    assert len(scope.allowed_route_patterns) == 3


# Codex iter-1 fix-up: origin-only validation ---------------------


@pytest.mark.parametrize(
    "bad_origin",
    [
        "https://api.ebay.com/buy/browse/v1/item",  # path > "/"
        "https://api.ebay.com/?q=x",  # query
        "https://api.ebay.com/#frag",  # fragment
        "https://user:pass@api.ebay.com",  # userinfo
    ],
)
def test_credential_scope_rejects_non_origin_url(bad_origin: str) -> None:
    with pytest.raises(ValidationError):
        _valid_credential_scope(allowed_origins=[bad_origin])


def test_credential_scope_accepts_origin_with_root_path() -> None:
    """Some producers normalize origins with a trailing ``/``; that's
    still origin-only. Accepting it avoids spurious rejections."""
    scope = _valid_credential_scope(allowed_origins=["https://api.ebay.com/"])
    assert scope.allowed_origins == ["https://api.ebay.com/"]


def test_credential_scope_accepts_origin_with_port() -> None:
    scope = _valid_credential_scope(allowed_origins=["https://api.ebay.com:8443"])
    assert scope.allowed_origins[0].endswith(":8443")


# Codex iter-1 fix-up: transport-failure invariant ----------------


def test_credential_use_record_transport_failure_requires_attempt_evidence() -> None:
    """A credential-bearing request that produced no HTTP response
    (timeout / connection refused / TLS error) must carry an
    attempt_evidence_ref so the audit trail can replay the failure;
    otherwise the audit shows credential use with no link to the
    failure mode."""
    with pytest.raises(ValidationError):
        _valid_credential_use_record(
            response_status=None,
            attempt_evidence_ref=None,
        )


def test_credential_use_record_transport_failure_with_attempt_evidence_ok() -> None:
    record = _valid_credential_use_record(
        response_status=None,
        attempt_evidence_ref="attempt-evidence:1",
    )
    assert record.attempt_evidence_ref == "attempt-evidence:1"


# Codex iter-1 fix-up: design-allowed escalation chain ------------


@pytest.mark.parametrize(
    ("from_type", "to_type"),
    [
        (AdapterType.AUTHORIZED_SESSION, AdapterType.HTTP),  # downgrade off auth
        (AdapterType.AUTHORIZED_SESSION, AdapterType.BROWSER_SNAPSHOT),
        (AdapterType.BROWSER_SNAPSHOT, AdapterType.HTTP),  # reverse
        (AdapterType.HTTP, AdapterType.API_SOURCE),  # reverse
        (AdapterType.SITEMAP, AdapterType.HTTP),  # not in chain
        (AdapterType.RSS, AdapterType.AUTHORIZED_SESSION),  # not in chain
    ],
)
def test_escalation_decision_rejects_disallowed_transition(
    from_type: AdapterType, to_type: AdapterType
) -> None:
    with pytest.raises(ValidationError):
        _valid_escalation_decision(from_adapter_type=from_type, to_adapter_type=to_type)


@pytest.mark.parametrize(
    ("from_type", "to_type"),
    [
        (AdapterType.API_SOURCE, AdapterType.HTTP),
        (AdapterType.API_SOURCE, AdapterType.AUTHORIZED_SESSION),
        (AdapterType.HTTP, AdapterType.AUTHORIZED_SESSION),
        (AdapterType.HTTP, AdapterType.BROWSER_SNAPSHOT),
        (AdapterType.BROWSER_SNAPSHOT, AdapterType.AUTHORIZED_SESSION),
    ],
)
def test_escalation_decision_accepts_design_allowed_transition(
    from_type: AdapterType, to_type: AdapterType
) -> None:
    decision = _valid_escalation_decision(
        from_adapter_type=from_type,
        to_adapter_type=to_type,
    )
    assert decision.from_adapter_type is from_type
    assert decision.to_adapter_type is to_type


def test_escalation_policy_rejects_reverse_transition_in_allowed_map() -> None:
    """A policy that admits ``AUTHORIZED_SESSION → HTTP`` would let
    ``PolicyDrivenEscalator`` walk back off authorized session,
    contradicting design.md §3.2's terminal rule."""
    with pytest.raises(ValidationError):
        _valid_escalation_policy(
            allowed_transitions={
                AdapterType.AUTHORIZED_SESSION: [AdapterType.HTTP],
            },
        )


def test_escalation_policy_rejects_non_chain_source_type() -> None:
    """``SITEMAP``/``RSS`` etc. are non-fetch sources; they don't
    participate in the escalation chain. A policy keying on them
    is dead policy and almost certainly a wiring bug."""
    with pytest.raises(ValidationError):
        _valid_escalation_policy(
            allowed_transitions={AdapterType.SITEMAP: [AdapterType.HTTP]},
        )


# Codex iter-3 fix-up: credential handle leak guard ----------------


@pytest.mark.parametrize(
    "leak",
    [
        "raw_secret:ebay-api-prod-12345",
        "password=hunter2",
        "TOKEN=abc.def.ghi",
        "api_key:sk-xxx",
        "AWS_SECRET_ACCESS_KEY=...",
        "postgres://user:pass@host/db",
    ],
)
def test_credential_scope_rejects_handle_that_looks_like_secret(leak: str) -> None:
    """A producer that accidentally pastes the credential value into
    ``credential_handle_ref`` would persist a raw secret into the
    foundation registry — exactly the failure mode the docs/09
    privacy classification forbids. Reuse the existing sensitive-
    marker tripwire to fail-closed at construction."""
    with pytest.raises(ValidationError):
        _valid_credential_scope(credential_handle_ref=leak)


# Codex iter-3 fix-up: header redaction guard ----------------------


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("Authorization", "Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig"),
        ("Cookie", "session=abc123def"),
        ("Set-Cookie", "auth_token=xyz; HttpOnly"),
        ("X-Api-Key", "sk_live_xxx"),
        ("Proxy-Authorization", "Basic dXNlcjpwYXNz"),
        ("X-Auth-Token", "token-12345"),
    ],
)
def test_attempt_evidence_rejects_unredacted_request_header(name: str, value: str) -> None:
    with pytest.raises(ValidationError):
        _valid_attempt_evidence(request_headers_redacted={name: value})


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("Set-Cookie", "session=abc123def"),
        ("X-Api-Key", "sk_live_xxx"),
    ],
)
def test_attempt_evidence_rejects_unredacted_response_header(name: str, value: str) -> None:
    with pytest.raises(ValidationError):
        _valid_attempt_evidence(response_headers_redacted={name: value})


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("Authorization", "[REDACTED]"),
        ("Cookie", "<REDACTED>"),
        ("X-Api-Key", "***"),
        ("Authorization", ""),  # empty is also acceptable
        ("Authorization", "Bearer ***"),  # marker embedded
    ],
)
def test_attempt_evidence_accepts_redacted_request_header(name: str, value: str) -> None:
    ev = _valid_attempt_evidence(request_headers_redacted={name: value})
    assert name in ev.request_headers_redacted


def test_attempt_evidence_header_check_is_case_insensitive() -> None:
    """``authorization`` / ``Authorization`` / ``AUTHORIZATION`` all
    name the same HTTP header. The redaction guard normalises case
    so an attacker can't sidestep by varying capitalisation."""
    with pytest.raises(ValidationError):
        _valid_attempt_evidence(
            request_headers_redacted={"authorization": "Bearer abc.def.ghi"},
        )


def test_attempt_evidence_does_not_check_non_sensitive_headers() -> None:
    """Non-sensitive headers like ``User-Agent`` carry meaningful
    values that look nothing like redaction markers; the guard
    must not reject them."""
    ev = _valid_attempt_evidence(
        request_headers_redacted={"User-Agent": "VeraCrawl/1.0 (+https://example.test)"}
    )
    assert "User-Agent" in ev.request_headers_redacted


# Codex iter-3 fix-up: empty allowed_transitions rejection ---------


def test_escalation_policy_rejects_empty_allowed_transitions() -> None:
    """An escalation policy with no transitions admits no work and
    contradicts the docstring's 'drop the policy ref instead' rule."""
    with pytest.raises(ValidationError):
        _valid_escalation_policy(allowed_transitions={})
