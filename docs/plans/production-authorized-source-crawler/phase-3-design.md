# Phase 3 design supplement — Access-control classification + escalation

This supplement expands `design.md` §4 Phase 3 (~60 lines) into
implementation-ready detail. Phase 0 already shipped the contracts
this phase consumes (`AccessControlBlocked`, `AccessControlProvider`,
`AdapterEscalationDecision`, `AdapterEscalationPolicy`, the
design-allowed transitions table); Phase 1 supplied the transport
(`StdlibHttpSourceAdapter` + `NetworkAttemptEvidence`); Phase 2
supplied authorized-session credential plumbing
(`CredentialVaultPort`, `SessionScopePolicy`, `RedactedPromptContext`).
Phase 3 wires the classification + escalation runtime on top.

## Capability cliff

A single `fetch this product` call walks the strict DAG:

```
API_SOURCE → HTTP
HTTP → BROWSER_SNAPSHOT
HTTP → AUTHORIZED_SESSION
BROWSER_SNAPSHOT → AUTHORIZED_SESSION
API_SOURCE → AUTHORIZED_SESSION
```

(`AUTHORIZED_SESSION` is terminal — Phase 0
`_ALLOWED_ESCALATION_TRANSITIONS` does not list any outgoing
transition.) The chain classifies access-control challenges
correctly, **never tries to evade them**, and emits a typed
escalation decision per transition. The orchestrator sees a
deterministic chain it can replay; the operator sees a typed audit
trail of every escalation.

If a fetch needs to retry against an authorized session after the
session itself fails (e.g., session token revoked), that is a
**new run**, not a continuation of the same chain — `RunBudget` is
re-evaluated, the chain starts over from the most-favourable
viable starting point. Phase 3 does not orchestrate the
re-evaluation; the run-control layer (Phase 5 / `AgentRunRequest`
lifecycle) does.

## Substep boundaries

Per the new "logical-boundary-only" splitting rule, Phase 3 ships
6 sub-steps. Each is a single cohesive concern; no further split
is justified.

| Sub-step | Title | LOC est | Logical boundary |
|---|---|---|---|
| 3.1 | `AccessControlClassifierPort` + `HeuristicClassifier` | ~250 | Pure detection — no I/O, no policy |
| 3.2 | `AdapterEscalationPort` + `PolicyDrivenEscalator` | ~300 | Pure decision — consumes typed failures, emits typed decisions |
| 3.3 | `source_coverage_gate` revert to evaluative | ~150 | Refactor: remove live-decision branches; keep evidence-completeness validation |
| 3.4 | eBay OAuth token cache (`FileBackedEbayTokenCache`) | ~200 | File-backed cache + cross-worktree lock, isolated from rest of Phase 3 |
| 3.5 | Amazon SP-API pagination + token refresh + partial-batch | ~350 | Single Amazon-specific adapter; cohesive feature set (3 features only meaningful together) |
| 3.6 | Live test #5: eBay browse-by-keyword | ~150 | Live test, gated by `@pytest.mark.live` |

3.5 explicitly stays merged: pagination yields a token, token
refresh runs on 401 mid-pagination, partial-batch tolerance handles
the case where token refresh succeeds for some pages but not
others. Splitting them would force test fixtures to share a fake
SP-API harness across files — false separation.

## Step 3.1 — `AccessControlClassifierPort` + `HeuristicClassifier`

### Port interface

```python
# src/veracrawl/ports/access_control_classifier.py
from collections.abc import Mapping
from typing import Protocol, runtime_checkable

import httpx

# Phase 0 contract module
from veracrawl.contracts.network import AccessControlBlocked
from veracrawl.contracts.shared import Ref

@runtime_checkable
class AccessControlClassifierPort(Protocol):
    """Classifies an HTTP response as either ``allowed`` or
    blocked-by-an-origin-protection. Pure logic — no I/O. Output
    is either ``None`` (not blocked) or :class:`AccessControlBlocked`.

    ``response_headers`` accepts ``httpx.Headers`` (preferred — it
    correctly represents multiple ``Set-Cookie`` values via
    ``.get_list``) OR a plain ``Mapping[str, str]`` (single-value
    fallback for fixture / test contexts where multi-value
    headers are not exercised). The classifier internally calls
    ``headers.get_list("set-cookie")`` when the input is an
    ``httpx.Headers`` instance and falls back to
    ``headers.get("set-cookie", "")`` (single value, document the
    limitation in the docstring) for plain mappings.
    """

    def classify(
        self,
        *,
        response_status: int,
        response_headers: httpx.Headers | Mapping[str, str],
        response_body: bytes,
        request_url: str,
        run_ref: Ref,
        attempt_evidence_ref: Ref | None = None,
    ) -> AccessControlBlocked | None: ...
```

`Ref` lives at `veracrawl.contracts.shared`; existing Phase 0
types use it. `AccessControlBlocked` is the Phase 0 record at
`veracrawl.contracts.network`.

### Detection rules (HeuristicClassifier default impl)

Each rule consumes (status, headers, body) and emits at least one
`detection_signal_ref` per match (signals are interned strings of
the form `signal:cf-ray-header-present`, `signal:body-cf-chl-form`,
etc.). Multiple matches → **most-specific vendor wins** per the
precedence order below, signals union.

**Authoritative precedence order** (highest specificity first;
break ties by alphabetical vendor name):

```
TURNSTILE > CLOUDFLARE > DATADOME > PERIMETERX > AKAMAI > LOGIN_WALL > GENERIC_CAPTCHA > UNKNOWN
```

Rationale: `TURNSTILE` is Cloudflare's challenge widget — pages
serving Turnstile typically *also* carry `cf-ray`, but the
Turnstile signal is more specific (a Turnstile page IS a CAPTCHA
page; a `cf-ray` page may be allowed traffic). Generic catchers
go last so a vendor-specific match always wins.

| Vendor | Detection signals (any-of triggers, evaluated in precedence order above) |
|---|---|
| `TURNSTILE` | body contains `cf-turnstile` script tag; body contains `challenges.cloudflare.com/turnstile` |
| `CLOUDFLARE` | `cf-ray` header present + status 403/503; body contains `<form id="challenge-form"`; header value `Server: cloudflare` + status 403 |
| `DATADOME` | `x-datadome` header present; body contains `data-dome-protection`; header value `Server: DataDome` |
| `PERIMETERX` | response carries `Set-Cookie` with cookie name `_pxhd`; body contains `Px-Captcha`; header value `Server: PerimeterX` |
| `AKAMAI` | header value `Server: AkamaiGHost` + status 403/406; body contains `Reference #18.` (Akamai error fingerprint); response carries `Set-Cookie` with cookie name `akamai-bot-manager` |
| `LOGIN_WALL` | status 401 AND `WWW-Authenticate` header present (presence only — value not inspected); status 302 with `Location` header value matching `/login`, `/signin`, `/auth/` (literal path-prefix match against the Location URL's path component); body contains `<form action="/login"` |
| `GENERIC_CAPTCHA` | body contains `<form name="captcha"` OR `g-recaptcha` OR `hcaptcha`; status 200 + body length < 1 KiB + body contains `verify you are human` |
| `UNKNOWN` | status `403` OR `429` with no other vendor match (operator review). Status `503` falls through to `None` unless a vendor signal matches — we don't treat bare 503 as access control because legitimate transient outages share the status. |

Body inspection: cap at first 64 KiB only (avoid consuming entire
multi-MB pages just to check for a marker). Rationale: real
challenge pages are < 4 KiB; legitimate content > 64 KiB cannot
be a challenge page in practice.

### Threat model

The classifier inspects header *names* AND a small allowlisted set
of header *values* (`Server`, `Location`, `Set-Cookie` cookie
name only — never cookie value, never `Authorization`, never any
header carrying caller-supplied credentials). Body inspection is
literal substring search against fixed markers, never any
caller-controlled pattern.

| Surface | Caller-supplied? | Redaction / boundary guarantee |
|---|---|---|
| `request_url` | yes (caller's URL) | Pass through to `AccessControlBlocked.url` (Phase 0 contract validates http(s) absolute) |
| `response_headers` (names) | from origin | All names compared case-insensitively to fixed allowlist; never logged in classifier output |
| `response_headers` (values) | from origin | Only `Server` (vendor fingerprint), `Location` (login-redirect detection — path-prefix only), and `Set-Cookie` cookie *names* (split on `=`, take first segment) are inspected. `WWW-Authenticate` value never inspected (presence only). Other headers' values never read. None logged in classifier output. |
| `response_body` | from origin | Capped at 64 KiB; literal substring search; never logged or persisted by the classifier |
| `attempt_evidence_ref` | caller-supplied | Pass through (already a Ref) |
| `run_ref` | caller-supplied | Pass through |

Classifier output `AccessControlBlocked` carries `detection_signal_refs`
(stable opaque identifiers from a fixed enum-shaped string
registry, e.g., `signal:cf-ray-header-present`) — never raw header
values, never body fragments. A misclassification log is
reproducible (same signals = same decision) without leaking
upstream headers / cookies to operator review.

### Acceptance tests (`tests/unit/test_step_3_1_heuristic_classifier.py`)

1. `test_cloudflare_challenge_form_classified_as_cloudflare` — body with `<form id="challenge-form"` + status 503 → `detected_provider == CLOUDFLARE`
2. `test_cloudflare_ray_header_classified` — `cf-ray: ...` + status 403 → CLOUDFLARE
3. `test_turnstile_classified_above_cloudflare_when_both_present` — Turnstile signal + cf-ray both present → TURNSTILE wins (priority order)
4. `test_datadome_x_datadome_header` → DATADOME
5. `test_perimeterx_pxhd_cookie` → PERIMETERX
6. `test_akamai_reference_fingerprint` → AKAMAI
7. `test_akamai_bot_manager_cookie` → AKAMAI
8. `test_login_wall_401_with_www_authenticate` → LOGIN_WALL
9. `test_login_wall_302_to_login_path` → LOGIN_WALL
10. `test_generic_captcha_recaptcha_form` → GENERIC_CAPTCHA
11. `test_generic_captcha_hcaptcha_form` → GENERIC_CAPTCHA
12. `test_unknown_403_no_signal_returns_unknown_with_signal` → UNKNOWN with at least one signal (the bare-403 signal)
13. `test_status_200_clean_body_returns_none` (allowed → return `None`)
14. `test_status_429_no_vendor_signal_returns_unknown` → UNKNOWN
15. `test_body_capped_at_64kib_does_not_scan_beyond_cap` — status `200` + body 1 MiB with marker at offset 70 KiB returns `None` (status 200 + no other vendor signal → not blocked; defense against pathological inputs). Same status `200` + body 1 MiB with marker at offset 4 KiB returns vendor. Use status 200 specifically to avoid the `UNKNOWN`-on-403/429 fallback so the assertion is unambiguous.
16. `test_classifier_never_returns_provider_without_signal` — property: every non-`None` output has `len(detection_signal_refs) >= 1`
17. `test_signal_strings_are_stable_for_replay` — same input → same `detection_signal_refs` (set equality)
18. `test_classifier_does_not_modify_inputs` — call, then assert headers + body unchanged
19. `test_protocol_satisfied_by_test_double` — minimal `_AlwaysAllow` impl satisfies `AccessControlClassifierPort`
20. `test_classifier_response_body_not_in_output` — output `__dict__` and `str(...)` do not contain any byte from a body that included a 32-byte unique canary

### Codex recurring concerns coverage

- (a) `raise Error(reason_str)`: classifier never raises — returns `None` or `AccessControlBlocked`. N/A.
- (l) Path-canonicalization: classifier inspects the request_url only via Phase 0's `_is_http_url` check (already path-aware). N/A new.
- (n) Exception `__dict__` leak: classifier doesn't raise. The `AccessControlBlocked` dataclass is Phase 0; redaction already shipped. N/A new.
- (o) Test depends on real-engine timing: N/A — pure logic.
- (p) Spec/doc divergence: keep `design.md` Phase 3 text aligned with this supplement; STATUS.md row added at first commit.

## Step 3.2 — `AdapterEscalationPort` + `PolicyDrivenEscalator`

### Port interface

```python
# src/veracrawl/ports/adapter_escalation.py
from typing import Protocol, runtime_checkable

@runtime_checkable
class AdapterEscalationPort(Protocol):
    """Decides whether to escalate from one adapter type to another
    given a typed failure. Pure decision — no I/O.

    Returns either:
    * :class:`AdapterEscalationDecision` (escalate to target adapter); or
    * ``None`` (do not escalate — caller decides retry / abandon /
      operator review based on the failure type and remaining budget).
    """

    def decide(
        self,
        *,
        from_adapter_type: AdapterType,
        # Exactly one of `failure` or `js_render_evidence_ref` is non-None.
        # `failure` for the failure-driven branches; `js_render_evidence_ref`
        # for the success-driven JS-render escalation (HTTP returned a
        # 200 with a skeleton + <script> bundle, evidence captured by
        # the orchestrator's HTML pre-parser, ref points at the
        # NetworkAttemptEvidence + a serialized js_render_decision payload).
        failure: NetworkAdapterError | AccessControlBlocked | None,
        js_render_evidence_ref: Ref | None,
        policy: AdapterEscalationPolicy,
        run_ref: Ref,
        escalations_used: int,
        scope_covers_authorized_session: bool,
    ) -> AdapterEscalationDecision | None: ...
```

### Failure types accepted by the escalator

The escalator is a pure decision function over typed failures. The
transport / API-source layer is responsible for raising one of the
following from a fetch attempt; the escalator inspects the type
hierarchy:

| Failure class | Inherits | Maps to |
|---|---|---|
| `NetworkPolicyForbiddenError` (existing, Phase 0) | `NetworkAdapterError, FatalError` | terminal (401/403/404/410) |
| `NetworkTimeoutError` (existing) | `NetworkAdapterError, RetryableError` | retry on same adapter |
| `AccessControlBlocked` (existing, Phase 0 contract — passed to escalator as a typed value, not raised) | dataclass / not exception | escalate to AUTHORIZED_SESSION when scope covers |
| `ApiSourceOutageError` (NEW, Phase 3 step 3.2) | `NetworkAdapterError, RetryableError` | escalate to HTTP — distinct from generic transport timeout |

`ApiSourceOutageError` is introduced specifically to disambiguate
"the API SOURCE backend is hard-down or rate-limited at the
provider level (eBay/Amazon API quota exhausted, AWS region
outage)" from "the network connection timed out". The orchestrator
raises it when an API-source adapter fails after its own internal
retry budget OR when the adapter receives an explicit "service
unavailable" status from the provider's API (eBay 503 with
`X-EBAY-API-ERRORS`, SP-API 429 with `Retry-After` indicating quota
exhaustion). A generic `NetworkTimeoutError` does NOT trigger the
escalation — the transport retries it locally (Phase 1 step 1.3
AIMD limiter handles rate); only `ApiSourceOutageError` is
"give up on this adapter type, try the next one".

### Decision algorithm

Evaluated in declared order; first match wins.

```
decide(from, failure, policy, escalations_used, scope_covers_session, document_is_js):
  # 1. Budget exhaustion — orchestrator caller's responsibility to track.
  if escalations_used >= policy.max_escalations_per_run:
    return None

  # 2. Terminal failures — never escalate, regardless of from-adapter.
  if isinstance(failure, FatalError):
    return None

  # 3. Access-control blocked — authorized session if scope covers; else terminal.
  if isinstance(failure, AccessControlBlocked):
    if scope_covers_session and AUTHORIZED_SESSION in policy.allowed_transitions.get(from, ()):
      return decision(from, AUTHORIZED_SESSION,
                      signature=ACCESS_CONTROL_BLOCKED,
                      triggered_by_ref=failure.id)
    return None

  # 4. ApiSourceOutageError — escalate API_SOURCE to HTTP.
  #    Note: this branch is BEFORE the generic RetryableError branch
  #    so the more-specific subclass takes precedence.
  if isinstance(failure, ApiSourceOutageError):
    if from == API_SOURCE and HTTP in policy.allowed_transitions.get(API_SOURCE, ()):
      return decision(API_SOURCE, HTTP,
                      signature=API_SOURCE_UNAVAILABLE,
                      triggered_by_ref=failure.id)
    return None

  # 5. Generic RetryableError (transport timeout, etc.) — retry on same
  #    adapter, never escalate. Caller (transport / orchestrator) handles
  #    cooldown + retry.
  if isinstance(failure, RetryableError):
    return None

  # 6. JS-rendered document path. Caller passes a non-None
  #    `js_render_evidence_ref` exactly when its HTML pre-parser
  #    classified the prior 200 response as a JS skeleton.
  if js_render_evidence_ref is not None:
    if BROWSER_SNAPSHOT in policy.allowed_transitions.get(from, ()):
      return decision(from, BROWSER_SNAPSHOT,
                      signature=JS_RENDERED_DOCUMENT,
                      triggered_by_ref=js_render_evidence_ref)
    return None

  return None
```

### Each transition explicitly defined

The capability-cliff chain
`API_SOURCE → HTTP → AUTHORIZED_SESSION → BROWSER_SNAPSHOT → AUTHORIZED_SESSION`
is the union of these single-step transitions, each gated by
both `policy.allowed_transitions` AND a typed trigger:

| From → To | Trigger | Signature |
|---|---|---|
| `API_SOURCE → HTTP` | `ApiSourceOutageError` (provider quota / outage) | `API_SOURCE_UNAVAILABLE` |
| `API_SOURCE → AUTHORIZED_SESSION` | `AccessControlBlocked` AND scope covers | `ACCESS_CONTROL_BLOCKED` |
| `HTTP → AUTHORIZED_SESSION` | `AccessControlBlocked` AND scope covers | `ACCESS_CONTROL_BLOCKED` |
| `HTTP → BROWSER_SNAPSHOT` | `document_is_js_rendered=True` AND `policy.allowed_transitions[HTTP]` permits | `JS_RENDERED_DOCUMENT` |
| `BROWSER_SNAPSHOT → AUTHORIZED_SESSION` | `AccessControlBlocked` AND scope covers (post-render auth wall) | `ACCESS_CONTROL_BLOCKED` |

`AUTHORIZED_SESSION` is terminal in `_ALLOWED_ESCALATION_TRANSITIONS`
(Phase 0 source_adapter.py) — once the chain reaches it, escalation
stops. The "AUTHORIZED_SESSION → BROWSER_SNAPSHOT → AUTHORIZED_SESSION"
loop in the capability-cliff prose actually represents *two
separate runs* against the same scope (browser run hits auth wall
again later); the escalator never produces it as a single chain.
The capability-cliff phrasing in `design.md` was loose; this
supplement narrows it to the strictly-DAG transition table above.

### Failure-signature enum

```python
# src/veracrawl/contracts/escalation.py (new module)
class EscalationFailureSignature(StrEnum):
    ACCESS_CONTROL_BLOCKED = "access_control_blocked"
    JS_RENDERED_DOCUMENT = "js_rendered_document"
    API_SOURCE_UNAVAILABLE = "api_source_unavailable"
```

The Phase 0 `AdapterEscalationDecision.failure_signature` field is
already a `str`. The Phase 3 escalator passes `enum.value` so the
serialized form is stable across releases (Phase 2 step 2.2b
lesson).

### Threat model

`failure` carries upstream error info; `policy` is internal config.
The decision's `reason` field uses the structured enum so no
free-form caller string lands on the exception or in audit logs.

### Acceptance tests (`tests/unit/test_step_3_2_policy_driven_escalator.py`)

1. `test_http_403_does_not_escalate_to_browser` (regression for codex critical #4 / important #7) — failure of type `NetworkPolicyForbiddenError` (FatalError) with `from=HTTP` + browser allowed in policy → returns `None`
2. `test_http_404_does_not_escalate_to_browser` → None
3. `test_http_401_does_not_escalate_to_browser` → None
4. `test_access_control_blocked_with_scope_escalates_to_authorized_session` → decision with `to=AUTHORIZED_SESSION`
5. `test_access_control_blocked_without_scope_does_not_escalate_to_browser` → None (regression: `AccessControlBlocked` never goes to browser)
6. `test_retryable_error_does_not_escalate` (transport-class retry stays on same adapter)
7. `test_js_rendered_document_escalates_http_to_browser_when_policy_allows`
8. `test_js_rendered_document_does_not_escalate_when_policy_disallows`
9. `test_api_source_unavailable_escalates_to_http`
10. `test_max_escalations_exhausted_returns_none` — `escalations_used == policy.max_escalations_per_run`
11. `test_decision_carries_structured_failure_signature` — `decision.failure_signature == EscalationFailureSignature.X.value` for each refusal class. The `AdapterEscalationDecision.failure_signature` Phase 0 field is `str`; the escalator passes `enum.value` so the on-the-wire form is the stable string. Test asserts string equality (not type identity).
12. `test_decision_returns_none_when_escalations_at_or_above_budget` — boundary test for `escalations_used` semantics (codex iter-1 minor: the property-test framing claimed mutation that the pure `decide()` API does not do; replace with the boundary-check tests above plus an orchestrator-level test in step 3.3 that asserts the orchestrator increments and the chain length is ≤ `max_escalations_per_run`)
13. `test_decision_has_triggered_by_ref` — every decision references the failure that motivated it
14. `test_api_source_outage_error_escalates_api_source_to_http` — `ApiSourceOutageError` (RetryableError subclass) on `from=API_SOURCE` returns decision to HTTP
15. `test_generic_retryable_timeout_does_not_escalate_api_source` — `NetworkTimeoutError` (RetryableError, NOT `ApiSourceOutageError`) returns None even with API_SOURCE→HTTP allowed
16. `test_protocol_satisfied_by_test_double`

### Codex recurring concerns coverage

- (a) Exception with reason: `decision.reason` is structured (`EscalationFailureSignature` enum). ✓
- (b) Production gate: `PolicyDrivenEscalator` is pure logic — no production gate needed. Document explicitly.
- (m) Free-form `reason`: replaced with enum. ✓

## Step 3.3 — `source_coverage_gate` revert to evaluative

Existing `source_coverage_gate` runs live decisions; design says it
should be evaluative only (validate recorded chain's evidence
completeness, never run the chain itself). This is a refactor:
identify the live-decision call sites, replace with assertions over
the run record's structured event sequence.

### Run-record schema for evaluation

The gate consumes a `SourceCoverageRunRecord` (existing Phase 0
type if present; otherwise NEW for Phase 3 step 3.3 — verify at
implementation time and add to Phase 0 contracts file in the same
commit if missing). Required ordering rule: the record carries an
`events: list[SourceCoverageEvent]` list in **emission order**
(monotonic by `timestamp` field, ties broken by insertion index).
Each `SourceCoverageEvent` is a tagged-union via `event_kind`:

```python
class SourceCoverageEventKind(StrEnum):
    ATTEMPT_STARTED = "attempt_started"          # adapter starts a fetch
    ATTEMPT_EVIDENCE = "attempt_evidence"        # NetworkAttemptEvidence ref
    ACCESS_CONTROL_BLOCKED = "access_control_blocked"  # AccessControlBlocked ref
    ESCALATION_DECIDED = "escalation_decided"    # AdapterEscalationDecision ref
    ATTEMPT_FAILED = "attempt_failed"            # typed failure ref + class name
    ATTEMPT_SUCCEEDED = "attempt_succeeded"      # adapter result ref

@dataclass(frozen=True, slots=True)
class SourceCoverageEvent:
    timestamp: datetime  # tz-aware
    sequence_index: int  # monotonically increasing per run, tie-break
    event_kind: SourceCoverageEventKind
    adapter_type: AdapterType
    payload_ref: Ref  # points to the corresponding contract record

    # Denormalized fields required for the gate to validate without
    # ref-resolution. Populated by the orchestrator when it appends
    # the event; the original payload_ref still points to the
    # canonical contract record for audit.
    failure_signature: str | None = None       # set on ESCALATION_DECIDED + ATTEMPT_FAILED
    from_adapter_type: AdapterType | None = None  # set on ESCALATION_DECIDED
    to_adapter_type: AdapterType | None = None    # set on ESCALATION_DECIDED
    failure_class_name: str | None = None      # set on ATTEMPT_FAILED (e.g., "NetworkPolicyForbiddenError", "ApiSourceOutageError")
```

The denormalization keeps the gate stateless and ref-resolution-
free: it inspects only the flattened event sequence. The original
contract refs (`payload_ref`) remain for downstream audit /
replay tooling that needs the full record.

"Preceding evidence/failure" in the test list below means: scan
events backward from the `ESCALATION_DECIDED` event, find the most
recent `ATTEMPT_FAILED` or `ACCESS_CONTROL_BLOCKED` event whose
`adapter_type` matches `decision.from_adapter_type`. If no such
event exists, the escalation is unjustified.

### Acceptance tests (`tests/unit/test_step_3_3_source_coverage_gate_evaluative.py`)

1. `test_gate_no_longer_invokes_classifier_or_escalator` — gate run on a fixture record raises 0 `Mock.call`s on classifier/escalator stubs
2. `test_gate_reports_missing_attempt_evidence` — record with `ESCALATION_DECIDED` event but no preceding `ATTEMPT_EVIDENCE` from the same `from_adapter_type` is flagged
3. `test_gate_reports_unjustified_escalation` — `ESCALATION_DECIDED` whose `failure_signature` doesn't correspond to any preceding `ATTEMPT_FAILED` / `ACCESS_CONTROL_BLOCKED` event flagged
4. `test_gate_uses_sequence_index_for_ordering` — events with identical timestamps are ordered by `sequence_index`
5. `test_gate_chain_length_at_most_max_escalations_per_run` — count of `ESCALATION_DECIDED` events ≤ policy's `max_escalations_per_run` (orchestrator-level invariant moved here per codex iter-1 minor)
6. `test_gate_passes_complete_chain` — well-formed record passes
7. `test_gate_idempotent` — same input → same output

### Codex recurring concerns coverage

- (p) Spec/doc divergence: this step explicitly aligns implementation with `design.md` "evaluative role" wording. Document the before/after in commit message.

## Step 3.4 — eBay OAuth token cache (`FileBackedEbayTokenCache`)

File-backed, TTL'd, lockable across worktree runs. Caches OAuth
client-credentials tokens issued by eBay so a single token serves
multiple runs until its TTL expires (~7200 s typically); if a run
hits 401 mid-pagination, the cache is invalidated for that key
(scope_ref) and a fresh token fetched.

### `EbayTokenCachePort` (Protocol — defined here, not at step 3.6)

```python
# src/veracrawl/ports/ebay_token_cache.py
from typing import Protocol, runtime_checkable
from datetime import datetime
from veracrawl.ports.credential_vault import CredentialValue

@runtime_checkable
class EbayTokenCachePort(Protocol):
    """Port for caching eBay OAuth tokens between runs.

    The port surface is narrow: ``get`` returns a CredentialValue
    or None; ``put`` stores a value with a tz-aware ``expires_at``;
    ``invalidate`` removes a scope_ref entry. No streaming /
    bulk operations — a per-call read-modify-write semantics is
    sufficient for the typical 1 token / 24h flow."""

    def get(self, scope_ref: str) -> CredentialValue | None: ...
    def put(self, scope_ref: str, *, value: str, expires_at: datetime) -> None: ...
    def invalidate(self, scope_ref: str) -> None: ...
```

Step 3.4 ships `FileBackedEbayTokenCache` as the default impl;
step 3.6 wires it into `EbayBrowseAdapter`. Phase 6 deployment
work can swap in a Vault-backed alternate impl without touching
either module.

### Interface

```python
# src/veracrawl/adapters/credential_vault/ebay_oauth_token_cache.py
@dataclass(frozen=True, slots=True)
class CachedToken:
    access_token: str  # CredentialValue-wrapped at the boundary that uses it
    expires_at: datetime  # tz-aware
    scope_ref: str
    fetched_at: datetime

class FileBackedEbayTokenCache:
    """Per-worktree-run JSON file at ``.veracrawl/cache/ebay-oauth-tokens.json``.
    Cross-worktree lock via ``fcntl.flock`` on the same file. TTL'd;
    expired entries are pruned on read.
    """

    def __init__(self, *, cache_dir: Path, clock: Callable[[], datetime] = ...) -> None: ...
    def get(self, scope_ref: str) -> CredentialValue | None: ...
    def put(self, scope_ref: str, *, value: str, expires_at: datetime) -> None: ...
    def invalidate(self, scope_ref: str) -> None: ...
```

The token value is stored on disk as a string, but every read goes
through `CredentialValue(value=..., scope_ref=...)` so the in-memory
representation cannot leak via logging.

### Threat model

| Surface | Risk | Mitigation |
|---|---|---|
| Cache file on disk | secrets stored in plain JSON | File mode `0o600`; directory mode `0o700`; mode-tightening via `fchmod` (Phase 1 step 1.4 lesson — atomic open + tighten); production deployment override path documented below |
| Concurrent worktree access | two runs racing on token refresh | `fcntl.flock(LOCK_EX)` on a **separate stable lockfile** (`<cache>.lock`, never replaced); the cache `<cache>.json` itself uses temp + atomic `os.replace`. The lockfile is created at `__init__` time and never replaced, so the lock target stays stable across concurrent writers. Lock acquisition order: acquire flock on `<cache>.lock` → read current `<cache>.json` (or treat missing as empty) → write new content to `<cache>.json.tmp.<pid>` → `os.replace` into place → release flock. Tests cover the two-writer race (test 5 below). |
| TTL skew | clock drift | inject `clock` for tests; production reads `datetime.now(UTC)` |
| Cache corruption | bad JSON or partial write | atomic write via `os.O_TMPFILE`-style temp + rename; on read failure, fail-closed (treat as cache miss + emit a structured log event) |
| Logged file path | `cache_dir` could carry user identifying info | Error / log messages report file existence + size + mode only, never absolute path; canary test asserts no `cache_dir` substring in any emitted log line |
| `CredentialValue` reveal logging | accidental `print` / formatting | `CredentialValue.__repr__` / `__str__` redaction guarantee from Phase 2 step 2.1 covers this; one regression test asserts the cached secret never lands in `caplog.records` |

### Production-mode acceptance (codex iter-1 important coverage)

`FileBackedEbayTokenCache` is a permitted production credential
store under the project's credential architecture **only when**:

1. The cache directory is owned by the runtime user (`os.geteuid()`
   matches `cache_dir.stat().st_uid`); construction raises
   `RuntimeError` if not.
2. The cache file is `0o600` and the directory is `0o700`;
   construction enforces and tests assert.
3. No log line emitted by the cache contains the cached secret
   (regression test with canary token in the cache + caplog
   inspection).
4. No log line emitted by the cache contains the absolute
   `cache_dir` path (privacy of file-system layout).
5. `RuntimeMode.PRODUCTION` does NOT raise
   `ProductionRuntimeNotImplemented` for this adapter — but every
   construction that fails (1) or (2) raises a typed error so a
   misconfigured deployment fails closed at startup, not at first
   token fetch.

For deployments that require off-disk credential storage (Vault
sidecar / OS keychain / KMS-backed file), the orchestrator wires
a different `EbayTokenCachePort` impl. Step 3.4 ships only the
file-backed default + the port; alternate impls are Phase 6
deployment work.

### Platform support

`fcntl.flock` is POSIX-only (Linux/macOS). The cache `__init__`
checks `sys.platform`:

- `linux` / `darwin`: full lock semantics.
- `win32`: skip locking; emit a startup warning structured-log
  event (`{"event": "ebay_token_cache_no_lock_on_win32"}`) and
  document the race-condition risk in the class docstring.
  Tests on win32 use `pytest.mark.skipif(sys.platform == "win32", reason="POSIX flock only")`
  for the concurrent-write test only; all other tests are
  cross-platform.

### Acceptance tests (`tests/unit/test_step_3_4_ebay_oauth_cache.py`)

1. `test_put_then_get_round_trip_returns_credential_value`
2. `test_get_returns_none_for_missing_scope`
3. `test_get_returns_none_after_ttl_expires` (inject clock)
4. `test_invalidate_removes_entry`
5. `test_concurrent_put_serialized_via_flock` — spawn 2 processes (subprocess) each calling `put` against same cache_dir; lockfile is created once and stable; assert no torn write (file readable as JSON after both complete) AND both writes' values are present (last writer wins, but neither produces corruption)
6. `test_cache_file_mode_is_0600` — after `put`, `os.stat(cache_file).st_mode & 0o777 == 0o600`
7. `test_cache_dir_mode_is_0700_when_created`
8. `test_lockfile_separate_from_cache_file` — `<cache>.lock` exists distinct from `<cache>.json`; lockfile is never replaced
9. `test_corrupt_cache_file_treated_as_miss` — write garbage to file, then `get` returns `None` and emits a structured-log event
10. `test_atomic_write_no_partial_under_simulated_crash` — patch `os.replace` to raise after temp write; assert original file unchanged
11. `test_credential_value_returned_does_not_leak_secret_via_repr`
12. `test_clock_injection_works`
13. `test_owner_mismatch_raises_at_construction` — patch `os.geteuid()` to differ from `cache_dir.stat().st_uid`; `__init__` raises `RuntimeError`
14. `test_directory_mode_too_permissive_raises_at_construction` — pre-create `cache_dir` with mode 0o755; `__init__` either tightens to 0o700 OR raises — pick "raise" (loud failure beats silent change)
15. `test_log_messages_do_not_contain_absolute_cache_path` — capture all structured-log events during put + get + invalidate; assert no `cache_dir` substring appears
16. `test_caplog_does_not_contain_cached_secret` — put a canary token (`canary-secret-DEADBEEF`); run get + invalidate; assert no `caplog.records` message body contains the canary
17. `test_production_mode_does_not_raise` — under `RuntimeMode.PRODUCTION`, `__init__` succeeds when ownership/mode are correct (positive control for the production-acceptance contract)

### Codex recurring concerns coverage

- (b) Production gate: explicitly documented as a known limitation; no `ProductionRuntimeNotImplemented` because the on-disk cache IS the production behavior for eBay (operational decision). Override pathway = wire a different `EbayTokenCachePort` impl in production.
- (n) Exception `__dict__`: cache file path could leak in error messages. Sanitize: error messages report file existence + size only, not full path contents.

## Step 3.5 — Amazon SP-API pagination + token refresh + partial-batch

Amazon SP-API specifics: cursor-based pagination via `nextToken`;
401 mid-pagination triggers a token refresh once per run (further
401s after refresh are terminal); partial-batch tolerance — if
pages 1-3 of a batch succeed and page 4 fails terminally, return
the 3 succeeded pages alongside the typed failure for page 4 so
the orchestrator sees both pieces.

### Interface

```python
# src/veracrawl/adapters/sources/amazon_sp_api.py

@dataclass(frozen=True, slots=True)
class AmazonSpApiPaginationBudget:
    """Per-list-call budget. Distinct from RunBudget — RunBudget is
    the run-level total; this is the call-level cap so a single
    pathological endpoint cannot consume the run budget alone."""

    max_pages: int                # hard cap on pages fetched per call
    max_runtime_seconds: float    # wall-clock cap on the whole pagination loop

@dataclass(frozen=True, slots=True)
class AmazonSpApiPaginatedResult:
    pages: list[AmazonSpApiPage]
    final_failure: AmazonSpApiPaginationFailure | None  # None on full success

class AmazonSpApiAdapter:
    """SP-API client with cursor pagination, 401-once token refresh,
    and partial-batch result. Wraps an HTTP transport (injectable
    for tests) and a credential vault (Phase 2)."""

    def __init__(
        self,
        *,
        http_transport: httpx.BaseTransport,
        vault: CredentialVaultPort,
        scope_policy: SessionScopePolicy,
        clock: Callable[[], datetime] = ...,
        monotonic: Callable[[], float] = time.monotonic,
    ) -> None: ...

    def list(
        self,
        *,
        endpoint: str,
        params: Mapping[str, str],
        scope_ref: str,
        run_ref: Ref,
        budget: AmazonSpApiPaginationBudget,
    ) -> AmazonSpApiPaginatedResult: ...
```

### Transport contract

The injected `httpx.BaseTransport` is the **post-retry** transport:
the underlying Phase 1 retry / AIMD / robots checks all complete
before a response surfaces here. The adapter therefore sees one
of:

* `httpx.Response` with a final HTTP status (200, 401, 404, 503, ...)
* a raised `NetworkAdapterError` subclass (FatalError / RetryableError
  / PolicyViolation) — final after the underlying retry budget
  exhausted.

The adapter NEVER sees raw network exceptions (`ConnectError`, etc.)
— Phase 1 step 1.5 wraps them. RetryableError surfacing here means
"transport gave up". The pagination loop:

* Sees `httpx.Response 401` first time → vault.invalidate → retry
  same page (refresh path).
* Sees `httpx.Response 401` second time on same call → return
  partial result with `final_failure`.
* Sees `httpx.Response` with `4xx` other than 401 → return partial
  result with `final_failure`.
* Sees `httpx.Response 5xx` → return partial result (Phase 1
  retry already exhausted by the time it reaches here).
* Sees raised `RetryableError` → return partial result with
  `final_failure(kind=RETRY_EXHAUSTED)`.
* Sees raised `FatalError` → return partial result with
  `final_failure(kind=FATAL)`.
* Sees raised `PolicyViolation` → propagate (never wrap).
* Sees `httpx.Response 200` → parse + accumulate page; loop.

### Pagination algorithm

```
list(endpoint, params, scope_ref, run_ref, budget):
  pages = []
  next_token = params.get("nextToken")
  refresh_used = False
  deadline = monotonic() + budget.max_runtime_seconds
  while True:
    if len(pages) >= budget.max_pages:
      return AmazonSpApiPaginatedResult(pages, AmazonSpApiPaginationFailure(
          kind=BUDGET_PAGES_EXCEEDED))
    if monotonic() >= deadline:
      return AmazonSpApiPaginatedResult(pages, AmazonSpApiPaginationFailure(
          kind=BUDGET_RUNTIME_EXCEEDED))

    page_params = {**params, "nextToken": next_token} if next_token else params
    try:
      response = transport.handle_request(httpx.Request("GET", endpoint, params=page_params))
    except FatalError as exc:
      return AmazonSpApiPaginatedResult(pages, AmazonSpApiPaginationFailure(
          kind=FATAL, triggered_by=exc))
    except RetryableError as exc:
      return AmazonSpApiPaginatedResult(pages, AmazonSpApiPaginationFailure(
          kind=RETRY_EXHAUSTED, triggered_by=exc))
    # PolicyViolation propagates — never wrap.

    if response.status_code == 401:
      if not refresh_used:
        refresh_used = True
        vault.invalidate(scope_ref)
        continue  # retry SAME page with fresh token
      return AmazonSpApiPaginatedResult(pages, AmazonSpApiPaginationFailure(
          kind=AUTH_REFRESH_EXHAUSTED, response_status=401))
    if response.status_code >= 400:
      return AmazonSpApiPaginatedResult(pages, AmazonSpApiPaginationFailure(
          kind=HTTP_ERROR, response_status=response.status_code))

    pages.append(parse_page(response))
    next_token = parse_next_token(response)
    if next_token is None:
      return AmazonSpApiPaginatedResult(pages, None)
```

`AmazonPaginationFailureKind(StrEnum)`:
`AUTH_REFRESH_EXHAUSTED` / `HTTP_ERROR` / `RETRY_EXHAUSTED` /
`FATAL` / `BUDGET_PAGES_EXCEEDED` / `BUDGET_RUNTIME_EXCEEDED`.

### Threat model

| Surface | Risk | Mitigation |
|---|---|---|
| `params` (caller dict) | could carry credential string | At `list()` entry (NOT construction — `params` is a per-call argument): walk values; refuse if any value `isinstance(CredentialValue)` (typed leak) OR if any value matches a credential-marker substring per Phase 0 step 0.4's `_REDACTABLE_MARKERS` tuple (`password`, `token=`, `api_key`, `aws_access_key`, ...). Raise `TypeError` for the typed case; raise `ValueError` for the marker-shaped string case. The marker-tuple check is best-effort and documented as not catching arbitrary unrecognized secrets — callers are still responsible for not passing raw secrets through non-vault paths. |
| `endpoint` | path injection / canonicalization mismatch | Validate by parsing through `urllib.parse.urlsplit`; require `scheme == ""`, `netloc == ""`, `path` starts with `/`, path matches `^/[A-Za-z0-9_\-/.]+$` (allow case + dot, but no `..`/`%2e`/`%2f`/`\` per Phase 2 step 2.2a ambiguous-path rules). Reject `//` doubled slashes. SP-API paths in practice: `/listings/2021-08-01/items/{sellerId}/{sku}`, `/orders/v0/orders` — both pass. Test list explicitly covers a few real-world SP-API paths. |
| `nextToken` from server | could be malicious shape | treat as opaque string; pass through; cap length at 4 KiB |
| 401 refresh loop | runaway if refresh+retry both 401 | hard cap: 1 refresh per `list()` call (state on the call, not the adapter) |

### Acceptance tests (`tests/unit/test_step_3_5_amazon_sp_api.py`)

1. `test_single_page_no_next_token_returns_one_page`
2. `test_multi_page_pagination_concatenates_results`
3. `test_401_first_call_triggers_refresh_and_succeeds_returns_full_result` — first 401 invalidates vault, second call (with fresh credential) returns 200; result contains all pages
4. `test_401_after_refresh_returns_partial_result_with_failure` — first 401 → refresh → second 401 → result has accumulated pages + non-None `final_failure`
5. `test_404_terminal_returns_partial_result_with_failure`
6. `test_retryable_error_returns_partial_with_retry_exhausted_kind` — test 6 was named "propagates" in iter-1 but the transport contract says converted; test asserts the conversion (codex iter-2 important: align)
7. `test_credential_value_in_params_raises_type_error`
8. `test_marker_string_secret_in_params_raises_value_error` — params containing `"api_key=sk-..."` literal raises ValueError from the marker-substring check
9. `test_endpoint_with_dotdot_rejected`
10. `test_endpoint_with_encoded_slash_rejected`
11. `test_endpoint_with_doubled_slashes_rejected`
12. `test_endpoint_with_real_sp_api_orders_path_accepted` — `/orders/v0/orders` passes
13. `test_endpoint_with_real_sp_api_listings_path_accepted` — `/listings/2021-08-01/items/A1/SKU-1` passes
14. `test_next_token_capped_at_4_kib`
15. `test_pagination_uses_scope_policy_check_per_page` — mock scope policy, assert called once per page
16. `test_list_writes_credential_use_record_per_page` — Phase 2 step 2.4b integration: each page emits one `CredentialUseRecord`
17. `test_partial_result_replay_deterministic` — record + replay reproduces exact page set
18. `test_clock_injection_for_token_refresh_timing`
19. `test_budget_max_pages_exceeded_returns_partial` — budget says max 3, server has 10 pages → result has 3 pages + `BUDGET_PAGES_EXCEEDED`
20. `test_budget_runtime_exceeded_returns_partial` — inject monotonic that advances past deadline; assert `BUDGET_RUNTIME_EXCEEDED`
21. `test_503_at_first_page_returns_zero_pages_with_http_error` (subclass of partial-batch test, but `pages == []` end of accumulator)
22. `test_policy_violation_propagates_unwrapped` — `transport.handle_request` raises `CredentialScopeViolation` → adapter does NOT swallow; propagates to caller

### Codex recurring concerns coverage

- (a, m) Refusal reasons: `AmazonSpApiPaginationFailure` carries structured `failure_kind: AmazonPaginationFailureKind(StrEnum)`.
- (b) Production gate: this IS the production adapter; no `ProductionRuntimeNotImplemented`. Test injects `httpx.MockTransport`.
- (l) Path canonicalization on `endpoint`.
- (i) URL handling for response headers (Phase 0 contracts already validate).

## Step 3.6 — eBay Browse adapter + live test #5

This step ships **two** files:

1. `src/veracrawl/adapters/sources/ebay_browse.py` —
   `EbayBrowseAdapter`, the production adapter the live test
   exercises. Codex iter-1 correctly flagged that step 3.4 alone
   does not produce a usable adapter; the cache feeds an adapter
   that the live test invokes. Adapter responsibilities:
   - Fetch OAuth token via `EbayTokenCachePort` (cache hit) or
     refresh path (cache miss).
   - Issue Browse API requests (`GET /buy/browse/v1/item_summary/search?q=...`).
   - Wire credential through `AuthorizedSessionAdapter` (Phase 2
     step 2.4b — at the time step 3.6 lands, that adapter exists).
   - Apply `SessionScopePolicy` per request (Phase 2 step 2.2a).
   - Emit `CredentialUseRecord` per request (Phase 2 step 2.4b
     integration).

   Adapter interface mirrors `AmazonSpApiAdapter` shape — pagination
   loop with budget; transport contract identical (see step 3.5).

2. `tests/integration/live/test_step_3_6_ebay_browse_keyword.py` —
   the live test. Marker `@pytest.mark.live`. Marker
   `@pytest.mark.skipif(...)` if any of the required credentials
   are absent so CI without secrets cleanly skips.

   Credential contract (codex iter-2 important — explicit definition):
   - `VERACRAWL_CRED_EBAY_PROD__CLIENT_ID` (Phase 2 step 2.1 env-var
     vault format) — eBay OAuth client ID.
   - `VERACRAWL_CRED_EBAY_PROD__CLIENT_SECRET` — eBay OAuth client
     secret.
   - The test wires `FileBackedEbayTokenCache` (step 3.4) plus an
     `EbayOAuthTokenFetcher` (small helper internal to step 3.6:
     posts to `https://api.ebay.com/identity/v1/oauth2/token` with
     `grant_type=client_credentials` + Basic-auth header built from
     `client_id:client_secret`; returns access token + expires_in;
     no scope_refs of its own — the cache's `scope_ref` is simply
     `EBAY_PROD`). Token endpoint URL is hardcoded for the live test
     because eBay's prod endpoint is the only relevant target.
   - **No** `VERACRAWL_CRED_EBAY_PROD__OAUTH` — that was a misnomer in
     iter-1. The live test fetches the OAuth token itself; an env
     var carrying a pre-fetched access token would be redundant
     (and short-lived since these tokens expire in 2h).
   - Skipped if either CLIENT_ID or CLIENT_SECRET is missing; the
     skip is loud (test prints a structured-log explaining the
     skip reason).

   Issues a browse query for a benign keyword (`"laptop"`); asserts
   ≥1 product returned within
   `AmazonSpApiPaginationBudget(max_pages=10, max_runtime_seconds=30)`
   (the `EbayBrowseAdapter` reuses the same budget shape since the
   pagination semantics are equivalent).

### Acceptance tests

Adapter unit tests (`tests/unit/test_step_3_6_ebay_browse_adapter.py`):

1. `test_browse_uses_cached_token_on_second_call` — first call hits cache miss, fetches; second call uses cache (counter assertion)
2. `test_browse_emits_one_credential_use_record_per_request`
3. `test_browse_pagination_respects_budget`
4. `test_browse_401_invalidates_cache_and_retries_once`
5. `test_browse_propagates_credential_scope_violation_unwrapped`

Live tests (`tests/integration/live/test_step_3_6_ebay_browse_keyword.py`):

6. `test_ebay_browse_returns_at_least_one_product` (live, marker `@pytest.mark.live`)
7. `test_ebay_browse_stays_within_run_budget` — measures elapsed wall-clock + page count, asserts ≤ budget
8. `test_ebay_browse_token_cache_serves_second_call_in_same_run` — second call within the same test process uses the cache

### Threat model

The live test must not commit response payloads to the repo (eBay
data may contain seller PII). Use `tests/integration/live/_artifacts/<run-id>/`
which is gitignored.

### Codex recurring concerns coverage

- (b) Production gate: live tests run under `RuntimeMode.PRODUCTION`. ✓
- Live test fragility (2026-05-08 reassessment lesson): assert minimal
  invariants (≥1 product, status 200) — never assert specific product
  counts or eBay-controlled field values that drift over time.

## Cross-cutting decisions

### Open question — operator review channel

`AccessControlBlocked` with `UNKNOWN` provider needs operator review.
Phase 3 emits the typed event; the *channel* (Slack / email / queue)
is Phase 6's `OtelObservabilityAdapter`. Document this dependency:
Phase 3 ships a `NoopOperatorReviewChannel` placeholder; Phase 6
swaps in the real channel.

### Open question — partial result vs full failure

Decision: 3.5 returns partial pages on terminal failure (codex
iter-1-style choice). Rationale: the orchestrator can use accumulated
pages while flagging the gap; treating the whole batch as failed
loses information already paid for.

### Expected reservations / explicit dependencies

Phase 3 is mostly pure-logic + a single file-backed cache, but
two known dependencies remain unresolved at end of Phase 3 and
are recorded here as explicit risks (codex iter-2 minor — "none
expected" was overconfident given the items below):

1. **Operator review channel for `UNKNOWN` access-control vendor**:
   Phase 3 emits the typed `AccessControlBlocked(detected_provider=UNKNOWN)`
   event, but the channel that *delivers* the operator review
   request (Slack / email / queue / dashboard) lives in Phase 6's
   `OtelObservabilityAdapter`. Phase 3 ships
   `NoopOperatorReviewChannel` placeholder; Phase 6 swaps in real
   delivery. **Risk**: under `RuntimeMode.PRODUCTION` between Phase
   3 and Phase 6, an UNKNOWN classification is logged but no human
   is paged. Mitigation: ship Phase 3 with a structured-log event
   that an external alerting rule (e.g., Datadog / Splunk) can
   match on, even before Phase 6 ships the canonical channel.

2. **Alternate (off-disk) eBay token cache implementations**:
   `FileBackedEbayTokenCache` is the only impl Phase 3 ships. A
   Vault-sidecar / OS-keychain / KMS-backed alternate is Phase 6
   deployment work. The `EbayTokenCachePort` (defined here) is the
   substitution surface — alternate impls swap in via wiring.
   **Risk**: deployments with stricter on-disk-secret prohibitions
   block Phase 3 from production rollout until Phase 6 ships an
   alternate. Mitigation: production-acceptance gate (test 17 in
   step 3.4) explicitly documents the on-disk acceptance contract.

If Phase 3 implementation surfaces additional reservations beyond
these two, log them in STATUS.md per the standard reservation
process.

## Codex recurring concerns — Phase-wide coverage

| # | Concern | Phase 3 coverage |
|---|---|---|
| a | Caller-string in exception | Decision + classifier never raise on caller input; failures use structured enums |
| b | Fixture/test-only class production gate | 3.4 cache is production; 3.5 adapter is production; classifier is pure logic |
| c | `_private` slot `__dir__` filter | No new `_private` slots holding secrets in Phase 3 |
| d | Cycle detection / depth cap | N/A — no recursion |
| e | `from None` + `__context__` | N/A — no re-raise |
| f | Caller-supplied identifier shape | 3.5 `endpoint` validated `^[a-z0-9/-]+$`; `scope_ref` already validated by Phase 2 step 2.1 |
| g | Unbounded loop wall-clock budget | 3.5 pagination capped by `policy.max_escalations_per_run`-equivalent (`max_pages` from `RunBudget`); 3.5 401 refresh hard-capped at 1 |
| h | `getattr` on user object | N/A |
| i | URL handling defensive | 3.1 reads URL only via Phase 0 `_is_http_url`; 3.5 `endpoint` regex-validated |
| j | Third-party dep upper bound | No new third-party deps |
| k | Private-module dep | N/A |
| l | Path canonicalization | 3.5 `endpoint` regex refuses `..`/`.`/encoded slashes |
| m | Free-form `reason` | All Phase 3 reason fields use structured enums (`EscalationFailureSignature`, `AmazonPaginationFailureKind`) |
| n | Exception `__dict__` | 3.4 cache errors report file metadata only, not paths/contents |
| o | Real-engine timing | 3.4 + 3.5 inject `clock`; live tests assert wall-clock budget without micro-asserts |
| p | Spec/doc divergence | This supplement IS the spec for Phase 3; design.md cross-reference added at first commit |
