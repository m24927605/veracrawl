"""Phase 3 step 3.1 — access-control classifier port.

The classifier reads HTTP response shape (status code, headers,
body fingerprints) and produces an ``AccessControlBlocked``
contract identifying the origin-side protection (Cloudflare /
Turnstile / DataDome / PerimeterX / Akamai / login-wall /
generic CAPTCHA) WITHOUT attempting any bypass. The
orchestrator (Phase 3 step 3.2 ``AdapterEscalationPort`` /
Phase 5 ``RecoveryPort``) decides what to do next: escalate
to authorized session, request operator review, or abandon.

Charter §Safety Boundary (docs/09:116): VeraCrawl
"must not include mechanisms for ... WAF evasion, stealth
automation, ban-avoidance proxy tactics, or bypassing
robots, terms, or customer authorization policy". The
classifier is the *labeling* layer — it produces typed
audit trails of who blocked what, never attempts a bypass.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from veracrawl.contracts.common import Ref
from veracrawl.contracts.network import AccessControlBlocked


@runtime_checkable
class AccessControlClassifierPort(Protocol):
    """Detect origin-side access-control technology from HTTP response shape."""

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
        """Return ``AccessControlBlocked`` if the response shape
        matches a known protection fingerprint; ``None`` otherwise.

        ``response_body_excerpt`` is a sanitized prefix of the
        response body (max 4 KiB; longer bodies are truncated by
        the caller). The classifier never inspects the full body
        to keep the detection cheap.
        """

        ...


__all__ = ["AccessControlClassifierPort"]
