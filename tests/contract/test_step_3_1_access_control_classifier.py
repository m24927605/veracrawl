"""Phase 3 step 3.1 — access-control classifier contract tests."""

from __future__ import annotations

from veracrawl.agents.access_control.heuristic_classifier import (
    HeuristicAccessControlClassifier,
)
from veracrawl.contracts.enums import AccessControlProvider
from veracrawl.contracts.network import AccessControlBlocked
from veracrawl.ports.access_control_classifier import AccessControlClassifierPort


def _classify(
    *,
    response_status: int = 403,
    response_headers: dict[str, str] | None = None,
    response_body_excerpt: str = "",
) -> AccessControlBlocked | None:
    classifier = HeuristicAccessControlClassifier()
    return classifier.classify(
        url="https://example.com/blocked",
        run_ref="run:phase-3-1:1",
        response_status=response_status,
        response_headers=response_headers or {},
        response_body_excerpt=response_body_excerpt,
        attempt_evidence_ref="attempt:1",
    )


# --- Header-based detection ------------------------------------------------


def test_cloudflare_cf_ray_header_classified() -> None:
    blocked = _classify(
        response_headers={"cf-ray": "abc123-DEN"},
    )
    assert blocked is not None
    assert blocked.detected_provider is AccessControlProvider.CLOUDFLARE
    assert blocked.detection_signal_refs


def test_datadome_x_datadome_header_classified() -> None:
    blocked = _classify(
        response_headers={"x-datadome": "blocked-by-datadome"},
    )
    assert blocked is not None
    assert blocked.detected_provider is AccessControlProvider.DATADOME


def test_perimeterx_header_classified() -> None:
    blocked = _classify(
        response_headers={"x-perimeterx": "challenge"},
    )
    assert blocked is not None
    assert blocked.detected_provider is AccessControlProvider.PERIMETERX


def test_akamai_header_classified() -> None:
    blocked = _classify(
        response_headers={"akamai-grn": "0.abc"},
    )
    assert blocked is not None
    assert blocked.detected_provider is AccessControlProvider.AKAMAI


def test_header_case_insensitive_match() -> None:
    blocked = _classify(
        response_headers={"CF-RAY": "abc123-DEN"},
    )
    assert blocked is not None
    assert blocked.detected_provider is AccessControlProvider.CLOUDFLARE


# --- Body fingerprint detection -------------------------------------------


def test_cloudflare_just_a_moment_body_classified() -> None:
    blocked = _classify(
        response_body_excerpt="<title>Just a moment...</title>",
    )
    assert blocked is not None
    assert blocked.detected_provider is AccessControlProvider.CLOUDFLARE


def test_turnstile_body_classified() -> None:
    blocked = _classify(
        response_body_excerpt="<input name='cf-turnstile-response'/>",
    )
    assert blocked is not None
    assert blocked.detected_provider is AccessControlProvider.TURNSTILE


def test_login_wall_body_classified() -> None:
    blocked = _classify(
        response_body_excerpt='<input type="password" name="password"/>',
    )
    assert blocked is not None
    assert blocked.detected_provider is AccessControlProvider.LOGIN_WALL


def test_recaptcha_body_classified() -> None:
    blocked = _classify(
        response_body_excerpt='<div class="g-recaptcha"></div>',
    )
    assert blocked is not None
    assert blocked.detected_provider is AccessControlProvider.GENERIC_CAPTCHA


# --- Unknown / status-only detection --------------------------------------


def test_403_without_provider_signal_returns_unknown() -> None:
    blocked = _classify(response_status=403)
    assert blocked is not None
    assert blocked.detected_provider is AccessControlProvider.UNKNOWN


def test_429_without_provider_signal_returns_unknown() -> None:
    blocked = _classify(response_status=429)
    assert blocked is not None
    assert blocked.detected_provider is AccessControlProvider.UNKNOWN


def test_200_with_no_signals_returns_none() -> None:
    """No access-control event to surface for a successful response."""

    blocked = _classify(response_status=200)
    assert blocked is None


def test_404_without_provider_signal_returns_none() -> None:
    """404 is not a block status — that's a missing resource."""

    blocked = _classify(response_status=404)
    assert blocked is None


# --- Detection signals + attempt evidence ---------------------------------


def test_blocked_payload_carries_detection_signal_refs() -> None:
    blocked = _classify(
        response_headers={"cf-ray": "abc123"},
        response_body_excerpt="<title>Just a moment...</title>",
    )
    assert blocked is not None
    # Both header AND body matches → at least 2 signals.
    assert len(blocked.detection_signal_refs) >= 2


def test_blocked_payload_attempt_evidence_ref_propagated() -> None:
    blocked = _classify(
        response_headers={"cf-ray": "abc123"},
    )
    assert blocked is not None
    assert blocked.attempt_evidence_ref == "attempt:1"


def test_runtime_checkable() -> None:
    classifier = HeuristicAccessControlClassifier()
    assert isinstance(classifier, AccessControlClassifierPort)


# --- Charter: no bypass attempt --------------------------------------------


def test_classifier_never_modifies_response() -> None:
    """Smoke check: classification is read-only. The
    classifier consumes headers + body but never returns a
    'modified URL to retry against' or similar bypass hint."""

    classifier = HeuristicAccessControlClassifier()
    blocked = classifier.classify(
        url="https://example.com/blocked",
        run_ref="run:1",
        response_status=403,
        response_headers={"cf-ray": "abc"},
        response_body_excerpt="<title>Just a moment...</title>",
        attempt_evidence_ref=None,
    )
    assert blocked is not None
    # The contract surface only carries labels + audit refs;
    # there is no "retry_url" / "challenge_token" / "solver_hint"
    # field anywhere.
    public_attrs = set(type(blocked).model_fields)
    forbidden_attrs = {
        "retry_url",
        "challenge_token",
        "solver_hint",
        "bypass_strategy",
    }
    assert not (public_attrs & forbidden_attrs)
