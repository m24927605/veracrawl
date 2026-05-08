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

## Codebase ground-truth (verified at iter-3)

| Symbol | Actual location | Correction from iter-2 |
|---|---|---|
| `Ref` | `veracrawl.contracts.common` | iter-2 said `contracts.shared` (does not exist) |
| `NetworkAdapterError` | `veracrawl.adapters.network.stdlib_http` | OK |
| `RobotsBlockedError`, `RedirectDeniedError`, `EgressDeniedError`, `RetryExhaustedError`, `AdapterFailureError`, `RateBudgetExceededError`, `PrivateNetworkDeniedError`, `SizeBudgetExceededError`, `UnsafeBrowserSideEffectError`, `MissingNetworkArtifactError`, `NetworkTimeoutError` | `veracrawl.adapters.network.stdlib_http` | iter-2 referenced non-existent `NetworkPolicyForbiddenError` |
| `AccessControlBlocked`, `AdapterEscalationDecision`, `AdapterEscalationPolicy`, `AccessControlProvider` | `veracrawl.contracts.network` / `source_adapter` / `enums` (Phase 0) | OK |
| `_REDACTABLE_MARKERS` (Phase 0.4) | `veracrawl.contracts.errors` (private) | iter-2 implied importable; **action**: Phase 3 step 3.5 must FIRST expose a public re-export `veracrawl.contracts.errors.REDACTABLE_MARKERS` (no underscore) before consuming |
| `SourceCoverageAdapterExecutionRecord`, `SourceCoverageAdapterReport` | `veracrawl.contracts.source_coverage` (Phase 0) | iter-2 invented `SourceCoverageRunRecord`; **action**: Phase 3 step 3.3 integrates with existing types |
| `AuthorizedSessionAdapter` | NOT YET IMPLEMENTED (Phase 2 step 2.4b dependency) | step 3.6 builds on step 2.4b; phases must execute in order |

`NetworkAdapterError` itself is the parent for all transport
failures. The `FatalError` mixin (`RetryExhaustedError`,
`AdapterFailureError`, `SizeBudgetExceededError`,
`MissingNetworkArtifactError`) is what Phase 3 step 3.2 inspects via
`isinstance(failure, FatalError)`. Concrete 401/403/404 status
mapping is the orchestrator's responsibility (it builds the
`NetworkAdapterError` from the response status); Phase 3 does NOT
introduce a new "ForbiddenError" class.

## Substep boundaries

Per the new "logical-boundary-only" splitting rule, Phase 3 ships
7 sub-steps (3.5 split into 3.5a/3.5b at iter-3 because LWA + SigV4
signing IS a true logical boundary distinct from pagination
mechanics). Each is a single cohesive concern.

| Sub-step | Title | LOC est | Logical boundary |
|---|---|---|---|
| 3.1 | `AccessControlClassifierPort` + `HeuristicClassifier` | ~250 | Pure detection — no I/O, no policy |
| 3.2 | `AdapterEscalationPort` + `PolicyDrivenEscalator` | ~300 | Pure decision — consumes typed failures, emits typed decisions |
| 3.3 | `source_coverage_gate` revert to evaluative | ~250 | Refactor: integrate with existing `SourceCoverageAdapterExecutionRecord` / `SourceCoverageAdapterReport`; add cross-record consistency assertions |
| 3.4 | eBay OAuth token cache (`EbayTokenCachePort` + `FileBackedEbayTokenCache`) | ~250 | File-backed cache + cross-worktree lock, isolated from rest of Phase 3 |
| **3.5a** | Amazon SP-API paginator (transport-only) | ~300 | Pure pagination over a pre-signed transport; injectable transport for tests |
| **3.5b** | LWA-only signing transport (`AmazonSpApiLwaTransport`) | ~250 | Real production credential / signing path — wraps an inner `httpx.BaseTransport` to add an `x-amz-access-token` header from a fresh LWA token; talks to `https://api.amazon.com/auth/o2/token` for `grant_type=refresh_token` exchange. **No AWS SigV4** — Amazon SP-API removed the SigV4 requirement effective 2023-10-02 (per `developer-docs.amazon.com/sp-api/.../sp-api-will-no-longer-require-aws-iam-or-aws-signature-version-4`); only the LWA bearer token is required. **Live-validation of full 3.5b stack deferred to Phase 6 step 6.4** because real LWA credentials require SP-API developer-account approval — not available in CI. |
| 3.6 | eBay browse adapter + live test #5 | ~250 | eBay OAuth fetcher + browse adapter + `@pytest.mark.live` test |

iter-3 codex finding: a single SP-API "list" call requires regional
host + LWA token + AWS SigV4 — the iter-2 sketch glossed this. 3.5
splits into:

- **3.5a** ships the *paginator* (cursor pagination + 401 refresh
  + partial-batch result + budget) over an injectable
  `httpx.BaseTransport`. Tests inject a `MockTransport` that
  doesn't sign anything. The paginator is provider-neutral
  (rebrandable as `CursorPaginatedAdapter` for a future eBay
  Inventory API or similar — no Amazon specifics).

- **3.5b** ships the *LWA-only signed transport* — a
  `BaseTransport` wrapper that fetches LWA refresh tokens from
  `https://api.amazon.com/auth/o2/token` (using
  `grant_type=refresh_token` + a long-lived refresh token from the
  vault) and adds the resulting access token as the
  `x-amz-access-token` header on each outgoing request. Per
  Amazon's 2023-10-02 SP-API changelog, AWS SigV4 / IAM are no
  longer required — only LWA bearer tokens. Production-only; tests
  for 3.5b are fixture-mode against canned LWA token responses.

  Interface sketch:

  ```python
  # src/veracrawl/adapters/sources/amazon_sp_api_lwa_transport.py

  @dataclass(frozen=True, slots=True)
  class LwaCredentialBundle:
      """LWA application credentials for SP-API refresh-token flow."""
      lwa_client_id: str
      lwa_client_secret: str  # stored as CredentialValue at construction
      refresh_token: str       # stored as CredentialValue at construction

  class AmazonSpApiLwaTransport(httpx.BaseTransport):
      """Wraps an inner BaseTransport and adds the
      ``x-amz-access-token`` header to outgoing requests, refreshing
      the token when it expires (5-min skew).

      The transport caches the access token in an injectable
      `EbayTokenCachePort`-shaped store (`SpApiLwaTokenCachePort`,
      defined here) so multiple worktree runs share a single token.
      """

      def __init__(
          self,
          *,
          inner: httpx.BaseTransport,
          credentials: LwaCredentialBundle,
          token_cache: SpApiLwaTokenCachePort,
          marketplace_endpoint: str,  # e.g., "https://sellingpartnerapi-na.amazon.com"
          clock: Callable[[], datetime] = ...,
      ) -> None: ...

      def handle_request(self, request: httpx.Request) -> httpx.Response: ...
  ```

  Test coverage (`tests/unit/test_step_3_5b_lwa_transport.py`):

  1. `test_first_call_fetches_token_from_lwa_endpoint`
  2. `test_subsequent_calls_use_cached_token_until_expiry`
  3. `test_token_refresh_on_expiry_with_5_minute_skew`
  4. `test_4xx_token_endpoint_response_raises_provider_auth_failed`
  5. `test_x_amz_access_token_header_present_on_signed_requests`
  6. `test_marketplace_endpoint_required_at_construction`
  7. `test_credentials_logged_only_via_credentialvalue_redaction`
  8. `test_token_endpoint_url_hardcoded_to_amazon_lwa_endpoint`

  Live validation deferred to Phase 6 step 6.4 (requires
  SP-API developer-account approval).

This split lets 3.5a ship cleanly with full unit-test coverage; 3.5b
ships with full unit coverage but its end-to-end live correctness
is acknowledged as a Phase 6 dependency. The capability-cliff goal
("walks API_SOURCE → HTTP fall-through") is achieved by 3.5a + 3.5b
together; 3.5a alone is a usable demo / regression harness.

## Step 3.1 — `AccessControlClassifierPort` + `HeuristicClassifier`

### Port interface

```python
# src/veracrawl/ports/access_control_classifier.py
from collections.abc import Mapping
from typing import Protocol, runtime_checkable

import httpx

# Phase 0 contract module
from veracrawl.contracts.network import AccessControlBlocked
from veracrawl.contracts.common import Ref

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

`Ref` lives at `veracrawl.contracts.common` (verified — see
ground-truth table at top); `AccessControlBlocked` is the Phase 0
record at `veracrawl.contracts.network`.

### ID generation strategy (replay-deterministic)

Phase 0 contracts (`AccessControlBlocked`, `AdapterEscalationDecision`)
require stable `id` fields. Strategy: each ID is the SHA-256 hex of
a canonical-form composite key:

```
classifier_id = sha256(
    f"{run_ref}|{request_url}|{response_status}|{detected_provider.value}|"
    f"{','.join(sorted(detection_signal_refs))}"
).hexdigest()[:32]

decision_id = sha256(
    f"{run_ref}|{from_adapter_type.value}|{to_adapter_type.value}|"
    f"{failure_signature}|{triggered_by_ref}|{escalations_used}"
).hexdigest()[:32]
```

Truncated to 32 hex chars (128 bits). Replay determinism: same
inputs → same ID. `policy_ref` for the decision comes from the
caller (the orchestrator already has the policy in scope before
calling `decide()`); add as required parameter:

```python
def decide(
    *,
    from_adapter_type: AdapterType,
    failure: ...,
    js_render_evidence_ref: Ref | None,
    policy: AdapterEscalationPolicy,
    policy_ref: Ref,                 # NEW iter-3: from caller
    run_ref: Ref,
    escalations_used: int,
    scope_covers_authorized_session: bool,
    review_provider: ReviewProviderPort | None = None,  # see requires_review below
) -> AdapterEscalationDecision | None: ...
```

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
        # Exactly one of `failure` or `js_render_evidence_ref` is non-None
        # (acceptance-tested invariant — see test 17 below).
        # `failure` for the failure-driven branches; `js_render_evidence_ref`
        # for the success-driven JS-render escalation (HTTP returned a
        # 200 with a skeleton + <script> bundle, evidence captured by
        # the orchestrator's HTML pre-parser, ref points at the
        # NetworkAttemptEvidence + a serialized js_render_decision payload).
        failure: NetworkAdapterError | AccessControlBlocked | None,
        js_render_evidence_ref: Ref | None,
        # Caller-supplied evidence ref the decision will record as
        # ``triggered_by_ref``. For ``failure`` of type
        # ``AccessControlBlocked``, this is the AccessControlBlocked.id
        # (it has an ``id`` field per Phase 0). For
        # ``failure`` of type ``NetworkAdapterError`` (which has NO
        # ``id`` field — it's a plain Exception subclass), the caller
        # passes the ref of the preceding ``NetworkAttemptEvidence``
        # captured by the transport. For the JS-render branch, this
        # equals ``js_render_evidence_ref``. Required (non-None).
        triggered_by_ref: Ref,
        policy: AdapterEscalationPolicy,
        policy_ref: Ref,                 # for AdapterEscalationDecision.policy_ref
        run_ref: Ref,
        escalations_used: int,
        scope_covers_authorized_session: bool,
        review_provider: OperatorReviewProviderPort | None = None,
    ) -> AdapterEscalationDecision | None: ...
```

### Failure types accepted by the escalator

The escalator is a pure decision function over typed failures. The
transport / API-source layer is responsible for raising one of the
following from a fetch attempt; the escalator inspects the type
hierarchy:

| Failure class | Inherits | Maps to |
|---|---|---|
| Status-fatal failure (NEW for Phase 3 step 3.2 — `HttpStatusFatalError(NetworkAdapterError, FatalError)`) | `NetworkAdapterError, FatalError` | terminal (401/403/404/410). Phase 3 introduces this single new class because Phase 1's `stdlib_http` covers transport-level failures (timeout, retry-exhausted, redirect-denied) but does NOT classify status-as-fatal — status mapping is the orchestrator / classifier layer's responsibility. The transport returns the response as-is for 4xx; the orchestrator constructs `HttpStatusFatalError(status_code=401)` (or 403 / 404 / 410 — the four codes design.md explicitly calls out as terminal) before invoking the escalator. Tests pass an `HttpStatusFatalError` instance directly. |
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
                      triggered_by_ref=triggered_by_ref)
    return None

  # 4. ApiSourceOutageError — escalate API_SOURCE to HTTP.
  #    Note: this branch is BEFORE the generic RetryableError branch
  #    so the more-specific subclass takes precedence.
  if isinstance(failure, ApiSourceOutageError):
    if from == API_SOURCE and HTTP in policy.allowed_transitions.get(API_SOURCE, ()):
      return decision(API_SOURCE, HTTP,
                      signature=API_SOURCE_UNAVAILABLE,
                      triggered_by_ref=triggered_by_ref)
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

### `requires_review` flag handling

The Phase 0 `AdapterEscalationPolicy.requires_review: bool` flag,
when `True`, gates every escalation behind operator approval.
The escalator integrates as follows:

```
# After step 4 / 5 / 6 in decide() determines a target adapter:
if policy.requires_review:
    if review_provider is None:
        # Caller forgot to wire review channel for a review-required policy
        raise RuntimeError(
            "AdapterEscalationPolicy.requires_review=True but no review_provider passed; "
            "wire OperatorReviewProviderPort or set requires_review=False"
        )
    approval = review_provider.request_approval(
        run_ref=run_ref,
        from_adapter_type=from,
        to_adapter_type=target,
        failure_signature=signature,
        triggered_by_ref=triggered_by_ref,
    )
    if approval is None:
        return None  # operator denied OR timed out
return decision(from, target, signature, triggered_by_ref, policy_ref)
```

`OperatorReviewProviderPort` (Protocol):

```python
@runtime_checkable
class OperatorReviewProviderPort(Protocol):
    """Phase 3 ships ``NoopOperatorReviewProvider`` (always returns
    None — denial). Phase 6 swaps in ``OtelOperatorReviewProvider``
    that pages a real Slack / queue channel and waits for approval."""

    def request_approval(
        self,
        *,
        run_ref: Ref,
        from_adapter_type: AdapterType,
        to_adapter_type: AdapterType,
        failure_signature: str,
        triggered_by_ref: Ref,
    ) -> Ref | None: ...  # approval_decision_ref or None
```

Test coverage in 3.2 acceptance list (added):

- `test_requires_review_with_no_provider_raises_runtimeerror`
- `test_requires_review_with_noop_provider_returns_none` (denial)
- `test_requires_review_with_approving_provider_returns_decision`

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

1. `test_http_403_does_not_escalate_to_browser` (regression for codex critical #4 / important #7) — failure of type `HttpStatusFatalError(status_code=403)` with `from=HTTP` + browser allowed in policy → returns `None`
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

Existing `source_coverage_gate` (`src/veracrawl/source_coverage_gate.py`)
runs live decisions; design says it should be evaluative only
(validate recorded chain's evidence completeness, never run the
chain itself). This is a refactor: identify the live-decision
call sites, replace with assertions over the existing Phase 0
records (`SourceCoverageAdapterExecutionRecord` per adapter +
`SourceCoverageAdapterReport` per run).

### Integration with existing schema (codex iter-3 important)

iter-2 invented `SourceCoverageRunRecord` / `SourceCoverageEvent`,
which contradicted the Phase 0 contracts already in
`src/veracrawl/contracts/source_coverage.py`. Phase 0 ships:

* `SourceCoverageAdapterExecutionRecord` — per-adapter execution,
  fields include `adapter_type`, `fetch_attempt_refs`,
  `policy_decision_refs`, `credential_audit_refs`,
  `replay_bundle_ref`, `result: CompletenessResult`.
* `SourceCoverageAdapterReport` — per-run summary, fields include
  `adapter_execution_refs`, `verified_adapter_types`,
  `policy_decision_refs`, `replay_bundle_ref`,
  `completion_result`.

The Phase 3 evaluative gate therefore consumes these existing
records and validates **cross-record consistency** without
introducing new Phase 0 types.

### Gate input contract (no live ref resolution)

The gate is pure logic. Callers (orchestrator / replay tooling)
resolve all refs **before** invoking the gate; the gate itself
does NOT load anything from a registry / repository. Input shape:

```python
@dataclass(frozen=True, slots=True)
class SourceCoverageGateInput:
    report: SourceCoverageAdapterReport
    executions: tuple[SourceCoverageAdapterExecutionRecord, ...]  # all execution records
    escalation_decisions: tuple[AdapterEscalationDecision, ...]   # all decisions for this run
    access_control_blocks: tuple[AccessControlBlocked, ...]       # all classifier outputs for this run
    network_attempt_evidences: tuple[NetworkAttemptEvidence, ...]  # all attempt evidences for this run
    policy: AdapterEscalationPolicy   # the policy that governed this run
```

Caller is responsible for ensuring the input is internally
consistent (records are all from the same run; no orphans). The
gate validates the chain semantics, not the resolution.

### Validation rules

1. Order the executions by `created_at` (TimestampedModel field —
   tz-aware), tie-break by execution `id` lexicographic.
2. For each `AdapterEscalationDecision` in
   `escalation_decisions` (also ordered by `created_at` then
   `id`):
   - Find the most recent execution at-or-before
     `decision.created_at` whose `adapter_type ==
     decision.from_adapter_type`. If none, **flag** as unjustified.
   - For `failure_signature == ACCESS_CONTROL_BLOCKED`: assert
     the preceding execution's `policy_decision_refs` contains a
     ref equal to one of the input `access_control_blocks`'s
     `id`s.
   - For `failure_signature in (API_SOURCE_UNAVAILABLE,
     JS_RENDERED_DOCUMENT)`: assert the preceding execution's
     `fetch_attempt_refs` contains a ref equal to one of the
     input `network_attempt_evidences`'s `id`s. For
     `API_SOURCE_UNAVAILABLE`, additionally assert the matched
     `NetworkAttemptEvidence.failure_class` (Phase 0 field —
     verified at iter-4) equals `"ApiSourceOutageError"`.
3. Assert `len(escalation_decisions) <=
   policy.max_escalations_per_run`.
4. Assert `report.verified_adapter_types` is a subset of
   `{e.adapter_type for e in executions if e.result ==
   CompletenessResult.PASS}`.

The existing record fields (`fetch_attempt_refs`,
`policy_decision_refs`, etc.) carry enough information that no
schema enrichment is needed for these checks.

### Acceptance tests (`tests/unit/test_step_3_3_source_coverage_gate_evaluative.py`)

1. `test_gate_no_longer_invokes_classifier_or_escalator` — gate run on a fixture record raises 0 `Mock.call`s on classifier/escalator stubs
2. `test_gate_reports_unjustified_escalation_decision` — fixture has an `AdapterEscalationDecision` whose `from_adapter_type` doesn't match the preceding execution record's adapter_type
3. `test_gate_reports_missing_fetch_attempt_for_http_to_browser_escalation` — escalation decision JS_RENDERED_DOCUMENT but the HTTP execution record's `fetch_attempt_refs` is empty
4. `test_gate_reports_chain_exceeds_max_escalations_per_run` — chain has 3 decisions, policy says `max_escalations_per_run=1`
5. `test_gate_orders_executions_by_timestamp_then_id` — two execution records with identical timestamps; assert deterministic ordering by id
6. `test_gate_passes_complete_chain` — well-formed report with valid escalation chain
7. `test_gate_idempotent` — same input → same output / `CompletenessResult`
8. `test_gate_replay_property_same_input_yields_same_final_adapter` (codex iter-3 important — parent design property test): construct two structurally-equal reports → gate produces identical `verified_adapter_types`
9. `test_gate_replay_property_evidence_digest_stable` (codex iter-3 important — parent design property test): hash of all `fetch_attempt_refs` ∪ `page_snapshot_refs` ∪ `credential_audit_refs` is stable across runs of the gate on the same input

### Non-introduction of new Phase 0 contracts

This step is a refactor of the gate plus possibly an enrichment
of `SourceCoverageAdapterExecutionRecord` if and only if a
required cross-reference cannot be resolved with the current
fields. **At implementation time**, verify whether existing fields
suffice:

- `adapter_type` ✓
- `policy_decision_refs` (escalation decisions ride here) ✓
- `fetch_attempt_refs` (network evidence) ✓
- `replay_bundle_ref` ✓
- timestamp (via TimestampedModel) ✓

If implementation discovers a gap, it lands as a Phase 0 contract
extension with a separate design.md note + commit, NOT an
opportunistic addition during step 3.3 refactor.

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
5. `test_concurrent_put_serialized_via_flock` — spawn 2 processes (subprocess) each calling `put` against same cache_dir, **with distinct scope_refs** (process A puts `EBAY_PROD_A`, process B puts `EBAY_PROD_B`). Assert: lockfile is created once and stable; resulting cache file is valid JSON; both scope_ref keys are present in the final cache (lockfile prevents one writer from clobbering the other's read-modify-write on a different key). For same-scope concurrent writes, last-writer-wins is the documented semantics — covered by a separate test below.

5a. `test_concurrent_put_same_scope_last_writer_wins_no_corruption` — same setup but both processes target the same scope_ref. Assert: cache file is valid JSON; the final value for the scope is one of the two writers' values (not torn / not partial); no corruption.
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
class PaginationBudget:
    """Per-list-call budget. Generic — used by AmazonSpApiPaginator
    AND eBay browse adapter. Distinct from RunBudget (run-level
    total); this is the call-level cap so a single pathological
    endpoint cannot consume the run budget alone.

    Lives at ``veracrawl.contracts.adapter_pagination`` (NEW Phase 3
    contract module — the file is created when step 3.5a lands).
    """

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
        http_transport: httpx.BaseTransport,  # MockTransport in tests; AmazonSpApiLwaTransport in production
        vault: CredentialVaultPort,
        scope_policy: SessionScopePolicy,
        token_cache: SpApiLwaTokenCachePort,  # for invalidate-on-401 (vault has no invalidate method)
        marketplace_endpoint: str,  # e.g., "https://sellingpartnerapi-na.amazon.com"; validated at __init__: must be https://*.amazon.com or https://sandbox.* per SP-API regional endpoints list
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
        budget: PaginationBudget,
    ) -> AmazonSpApiPaginatedResult: ...
```

`marketplace_endpoint` is the regional SP-API base URL — see
`developer-docs.amazon.com/sp-api/docs/marketplace-ids`. Production
values: `https://sellingpartnerapi-na.amazon.com` (North America),
`https://sellingpartnerapi-eu.amazon.com` (Europe),
`https://sellingpartnerapi-fe.amazon.com` (Far East). Tests use
`https://sandbox.sellingpartnerapi-na.amazon.com`.

The full request URL the paginator constructs is
`f"{marketplace_endpoint}{endpoint}?<params>"`; the validated
`endpoint` regex is path-only (no scheme/host). Validation at
construction time refuses non-HTTPS / non-Amazon hosts so a
misconfigured caller cannot accidentally point at the wrong
service.

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
        token_cache.invalidate(scope_ref)  # cache has invalidate; vault does not
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
| `params` (caller dict) | could carry credential string | At `list()` entry (NOT construction — `params` is a per-call argument): walk values; refuse if any value `isinstance(CredentialValue)` (typed leak) OR if any value matches a credential-marker substring per the **public** `veracrawl.contracts.errors.REDACTABLE_MARKERS` constant. Raise `TypeError` for the typed case; raise `ValueError` for the marker-shaped string case. The marker-tuple check is best-effort and documented as not catching arbitrary unrecognized secrets — callers are still responsible for not passing raw secrets through non-vault paths. **Prerequisite (must land in step 3.5a's first commit)**: re-export `_REDACTABLE_MARKERS` (Phase 0.4 private) as `REDACTABLE_MARKERS` (no underscore) in `veracrawl.contracts.errors`'s `__all__`. The underscore prefix on the original was an implementation detail; the constant is intentionally stable. The re-export is a one-line addition that doesn't change the value or alphabetize the markers. |
| `endpoint` | path injection / canonicalization mismatch | Validate by parsing through `urllib.parse.urlsplit`; require `scheme == ""`, `netloc == ""`, `path` starts with `/`, path matches `^/[A-Za-z0-9_\-/.]+$` (allow case + dot, but no `..`/`%2e`/`%2f`/`\` per Phase 2 step 2.2a ambiguous-path rules). Reject `//` doubled slashes via a separate explicit check (`"//" not in path`) since the regex does not exclude doubled slashes. SP-API paths in practice: `/listings/2021-08-01/items/{sellerId}/{sku}`, `/orders/v0/orders` — both pass. Test list explicitly covers a few real-world SP-API paths. |
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

   **Runtime mode** (codex iter-3 critical — `EnvVarVault` raises
   `ProductionRuntimeNotImplemented` under PRODUCTION; iter-2
   said the live test ran under PRODUCTION which contradicted the
   Phase 2 step 2.1 vault gate). Resolution: the live test runs
   under `RuntimeMode.FIXTURE` against a real network endpoint.
   Phase 1 step 1.6 live tests (`tests/integration/live/test_step_1_6*.py`)
   established this precedent — issuing real HTTP requests under
   fixture mode is acceptable when the test exercises a
   capability that needs a live endpoint to validate (vendor
   detection, real OAuth round-trip, real eBay Browse API
   surface) without claiming "production runtime correctness".
   Production runtime correctness for eBay browse lives in
   Phase 6 step 6.4 once `OutboxVaultClient` (Phase 2 step 2.4a)
   ships and a vault adapter that DOES allow PRODUCTION reads
   (e.g., HashiCorp Vault sidecar) is wired in.

   Credential contract (codex iter-2 important — explicit definition):
   - `VERACRAWL_CRED_EBAY_PROD__CLIENT_ID` (Phase 2 step 2.1 env-var
     vault format) — eBay OAuth client ID.
   - `VERACRAWL_CRED_EBAY_PROD__CLIENT_SECRET` — eBay OAuth client
     secret.
   - The test wires `FileBackedEbayTokenCache` (step 3.4) plus an
     `EbayOAuthTokenFetcher` (small helper internal to step 3.6:
     posts to `https://api.ebay.com/identity/v1/oauth2/token` with
     URL-encoded body
     `grant_type=client_credentials&scope=https%3A%2F%2Fapi.ebay.com%2Foauth%2Fapi_scope`
     (per `developer.ebay.com/api-docs/static/oauth-client-credentials-grant.html`
     — the `scope` parameter is required, not optional) + Basic-auth
     header built from `client_id:client_secret`; returns access
     token + expires_in; the cache's `scope_ref` is the constant
     `EBAY_PROD` for the Browse API). Token endpoint URL is
     hardcoded for the live test because eBay's prod endpoint is
     the only relevant target.
   - **No** `VERACRAWL_CRED_EBAY_PROD__OAUTH` — that was a misnomer in
     iter-1. The live test fetches the OAuth token itself; an env
     var carrying a pre-fetched access token would be redundant
     (and short-lived since these tokens expire in 2h).
   - Skipped if either CLIENT_ID or CLIENT_SECRET is missing; the
     skip is loud (test prints a structured-log explaining the
     skip reason).

   Issues a browse query for a benign keyword (`"laptop"`); asserts
   ≥1 product returned within
   `PaginationBudget(max_pages=10, max_runtime_seconds=30)`
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

- (b) Production gate: step 3.6 live test runs under `RuntimeMode.FIXTURE` (per Phase 1 step 1.6 precedent and step 3.6 runtime-mode resolution above). The Phase 0.4 production gates on `EnvVarVault` / production-only paths are not exercised; the test validates the eBay vendor / OAuth flow / cache hit behavior against a real endpoint without claiming production-runtime correctness. Production runtime is Phase 6 step 6.4.
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
| f | Caller-supplied identifier shape | 3.5 `endpoint` validated `^/[A-Za-z0-9_\-/.]+$` + explicit `"//" not in path` check + Phase 2 step 2.2a ambiguous-path rules (no `..` / `%2e` / `%2f` / `\`); `scope_ref` already validated by Phase 2 step 2.1 |
| g | Unbounded loop wall-clock budget | 3.5 pagination capped by `policy.max_escalations_per_run`-equivalent (`max_pages` from `RunBudget`); 3.5 401 refresh hard-capped at 1 |
| h | `getattr` on user object | N/A |
| i | URL handling defensive | 3.1 reads URL only via Phase 0 `_is_http_url`; 3.5 `endpoint` regex-validated |
| j | Third-party dep upper bound | No new third-party deps |
| k | Private-module dep | N/A |
| l | Path canonicalization | 3.5 `endpoint` regex refuses `..` / `.` / `%2e` / `%2f` / `%5c` / `\` plus rejects `//` doubled slashes |
| m | Free-form `reason` | All Phase 3 reason fields use structured enums (`EscalationFailureSignature`, `AmazonPaginationFailureKind`) |
| n | Exception `__dict__` | 3.4 cache errors report file metadata only, not paths/contents |
| o | Real-engine timing | 3.4 + 3.5 inject `clock`; live tests assert wall-clock budget without micro-asserts |
| p | Spec/doc divergence | This supplement IS the spec for Phase 3; design.md cross-reference added at first commit |
