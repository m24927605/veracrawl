"""Phase 3 step 3.1 — heuristic access-control classifier.

Detects origin-side protection from response headers + body
fingerprints. The classifier is intentionally conservative:
* unique header signals (e.g., ``cf-ray``, ``x-datadome``)
  produce a confident classification;
* generic 403 / 429 without provider-specific signals
  produces ``UNKNOWN`` so the orchestrator knows it didn't
  identify a specific protection;
* unblocked responses (200/3xx/etc.) return ``None`` —
  there is no access-control event to surface.

The classifier never attempts a bypass and never fabricates
detection signals: every ``AccessControlBlocked`` carries
``detection_signal_refs`` listing the specific header / body
markers that triggered the classification.
"""

from __future__ import annotations

import hashlib
import re
import uuid

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import AccessControlProvider
from veracrawl.contracts.network import AccessControlBlocked

# Header signatures: header name (lowercased) → provider.
_HEADER_SIGNATURES: dict[str, AccessControlProvider] = {
    "cf-ray": AccessControlProvider.CLOUDFLARE,
    "cf-cache-status": AccessControlProvider.CLOUDFLARE,
    "x-datadome": AccessControlProvider.DATADOME,
    "x-datadome-cid": AccessControlProvider.DATADOME,
    "x-incap-ses": AccessControlProvider.UNKNOWN,  # Imperva — not in enum
    "x-perimeterx": AccessControlProvider.PERIMETERX,
    "_pxhd": AccessControlProvider.PERIMETERX,
    "akamai-grn": AccessControlProvider.AKAMAI,
    "x-akamai-transformed": AccessControlProvider.AKAMAI,
}

# Body fingerprints — minimal regex to avoid false positives.
_BODY_FINGERPRINTS: tuple[tuple[re.Pattern[str], AccessControlProvider], ...] = (
    (
        re.compile(r"<title>[^<]*Just a moment[^<]*</title>", re.IGNORECASE),
        AccessControlProvider.CLOUDFLARE,
    ),
    (
        re.compile(r"cf-turnstile-response", re.IGNORECASE),
        AccessControlProvider.TURNSTILE,
    ),
    (
        re.compile(r"datadome[._-]?challenge", re.IGNORECASE),
        AccessControlProvider.DATADOME,
    ),
    (
        re.compile(r"_pxCaptcha", re.IGNORECASE),
        AccessControlProvider.PERIMETERX,
    ),
    (
        re.compile(r'<input[^>]+name=["\']password["\']', re.IGNORECASE),
        AccessControlProvider.LOGIN_WALL,
    ),
    (
        re.compile(r"\bg-recaptcha\b", re.IGNORECASE),
        AccessControlProvider.GENERIC_CAPTCHA,
    ),
    (
        re.compile(r"\bhcaptcha[._-]\w+", re.IGNORECASE),
        AccessControlProvider.GENERIC_CAPTCHA,
    ),
)

_BLOCK_STATUS_CODES: frozenset[int] = frozenset({401, 403, 407, 429})


def _signal_ref(label: str, payload: str) -> Ref:
    """Hashed ref pinning the matched signal — replay can
    cross-reference without storing the raw response bytes."""

    digest = hashlib.sha256(f"{label}|{payload}".encode()).hexdigest()[:16]
    return f"signal:{label}:{digest}"


class HeuristicAccessControlClassifier:
    """Phase 3 step 3.1 default classifier."""

    def classify(
        self,
        *,
        url: str,
        run_ref: Ref,
        response_status: int,
        response_headers: dict[str, str],
        response_body_excerpt: str,
        attempt_evidence_ref: Ref | None = None,
    ) -> AccessControlBlocked | None:
        normalized_headers = {k.lower(): v for k, v in response_headers.items()}
        signals: list[Ref] = []
        detected: AccessControlProvider | None = None
        # Header signatures — strongest signal.
        for header_name, provider in _HEADER_SIGNATURES.items():
            if header_name in normalized_headers:
                signals.append(
                    _signal_ref("header", f"{header_name}={normalized_headers[header_name]!s}")
                )
                if detected is None:
                    detected = provider
        # Body fingerprints — secondary signal.
        for pattern, provider in _BODY_FINGERPRINTS:
            if pattern.search(response_body_excerpt):
                signals.append(_signal_ref("body", pattern.pattern))
                if detected is None:
                    detected = provider
        if detected is None:
            # No provider-specific signal. If the status code
            # is a known block status, surface as UNKNOWN so
            # the orchestrator knows we recognised "this is
            # blocked" without identifying which protection.
            if response_status in _BLOCK_STATUS_CODES:
                detected = AccessControlProvider.UNKNOWN
                signals.append(_signal_ref("status", str(response_status)))
            else:
                return None  # not blocked
        if not signals:
            # Defensive: should be unreachable, but guards the
            # contract requirement that detection_signal_refs
            # is non-empty.
            return None
        return AccessControlBlocked(
            id=f"access-control-blocked:{uuid.uuid4().hex}",
            run_ref=run_ref,
            url=url,
            detected_provider=detected,
            detection_signal_refs=signals,
            response_status=response_status,
            attempt_evidence_ref=attempt_evidence_ref,
        )


__all__ = ["HeuristicAccessControlClassifier"]
