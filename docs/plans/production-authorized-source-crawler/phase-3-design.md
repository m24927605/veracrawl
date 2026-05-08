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

A single `fetch this product` call walks
`API_SOURCE → HTTP → AUTHORIZED_SESSION → BROWSER_SNAPSHOT → AUTHORIZED_SESSION`
(through the design-allowed transitions only), classifies access-
control challenges correctly, **never tries to evade them**, and
emits a typed escalation decision per transition. The orchestrator
sees a deterministic chain it can replay; the operator sees a
typed audit trail of every escalation.

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
from typing import Protocol, runtime_checkable

@runtime_checkable
class AccessControlClassifierPort(Protocol):
    """Classifies an HTTP response as either ``allowed`` or
    blocked-by-an-origin-protection. Pure logic — no I/O. Output
    is either ``None`` (not blocked) or :class:`AccessControlBlocked`.
    """

    def classify(
        self,
        *,
        response_status: int,
        response_headers: Mapping[str, str],
        response_body: bytes,
        request_url: str,
        attempt_evidence_ref: Ref | None = None,
        run_ref: Ref,
    ) -> AccessControlBlocked | None: ...
```

### Detection rules (HeuristicClassifier default impl)

Each rule consumes (status, headers, body) and emits at least one
`detection_signal_ref` per match (signals are interned strings of
the form `signal:cf-ray-header-present`, `signal:body-cf-chl-form`,
etc.). Multiple matches → highest-priority vendor wins, signals
union.

| Vendor | Detection signals (any-of, priority order) |
|---|---|
| `CLOUDFLARE` | `cf-ray` header present + status 403/503; body contains `<form id="challenge-form"`; `Server: cloudflare` + status 403 |
| `TURNSTILE` | body contains `cf-turnstile` script tag; body contains `challenges.cloudflare.com/turnstile` |
| `DATADOME` | `x-datadome` header present; body contains `data-dome-protection`; `Server: DataDome` |
| `PERIMETERX` | `_pxhd` cookie set in response; body contains `Px-Captcha`; `Server: PerimeterX` |
| `AKAMAI` | `Server: AkamaiGHost` + status 403/406; body contains `Reference #18.` (Akamai error fingerprint); `akamai-bot-manager` cookie set |
| `LOGIN_WALL` | status 401 AND `WWW-Authenticate` header present; status 302 to known login path patterns (`/login`, `/signin`, `/auth/`); body contains `<form action="/login"` |
| `GENERIC_CAPTCHA` | body contains `<form name="captcha"` OR `g-recaptcha` OR `hcaptcha`; status 200 + body length < 1 KiB + body contains `verify you are human` |
| `UNKNOWN` | status 403 OR 429 with no other vendor match (operator review) |

Body inspection: cap at first 64 KiB only (avoid consuming entire
multi-MB pages just to check for a marker). Rationale: real
challenge pages are < 4 KiB; legitimate content > 64 KiB cannot
be a challenge page in practice.

### Threat model

| Surface | Caller-supplied? | Redaction at boundary |
|---|---|---|
| `request_url` | yes (caller's URL) | Pass through to `AccessControlBlocked.url` (Phase 0 contract validates http(s) absolute) |
| `response_headers` | from origin | Header values NOT inspected for credentials (only header *names* matter for vendor detection); never logged in classifier output |
| `response_body` | from origin | Capped at 64 KiB; never logged or persisted by the classifier |
| `attempt_evidence_ref` | caller-supplied | Pass through (already a Ref) |
| `run_ref` | caller-supplied | Pass through |

Classifier output `AccessControlBlocked` carries `detection_signal_refs`
(Refs into a `signals` registry / hard-coded enum-ish strings) — never
raw header values, never body fragments. This means a misclassification
log is reproducible (same signals = same decision) without leaking
upstream headers to operator review.

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
15. `test_body_capped_at_64kib_does_not_scan_beyond_cap` — body 1 MiB with marker at offset 70 KiB returns `None` (defense against pathological inputs); body 1 MiB with marker at offset 4 KiB returns vendor
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
        failure: NetworkAdapterError | AccessControlBlocked,
        policy: AdapterEscalationPolicy,
        run_ref: Ref,
        escalations_used: int,
        scope_covers_authorized_session: bool,
        document_is_js_rendered: bool,
    ) -> AdapterEscalationDecision | None: ...
```

### Decision algorithm

```
decide():
  if escalations_used >= policy.max_escalations_per_run:
    return None  # budget exhausted
  if isinstance(failure, FatalError):  # 401 / 404 / 410
    return None  # terminal — no escalation
  if isinstance(failure, AccessControlBlocked):
    if scope_covers_authorized_session and AUTHORIZED_SESSION in policy.allowed_transitions[from]:
      return decision(from→AUTHORIZED_SESSION, reason="access_control_blocked")
    return None  # no scope coverage → terminal
  if isinstance(failure, RetryableError):
    return None  # cooldown + retry handled by transport, NOT escalation
  if document_is_js_rendered and BROWSER_SNAPSHOT in policy.allowed_transitions[from]:
    return decision(from→BROWSER_SNAPSHOT, reason="js_rendered_document")
  if from == API_SOURCE and rate_limited_or_outage:
    return decision(API_SOURCE→HTTP, reason="api_source_unavailable")
  return None
```

`failure_signature` field on the decision is a structured enum
value (Phase 2 step 2.2b lesson — never free-form text). Define
`EscalationFailureSignature(StrEnum)`: `ACCESS_CONTROL_BLOCKED` /
`JS_RENDERED_DOCUMENT` / `API_SOURCE_UNAVAILABLE`.

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
11. `test_decision_carries_structured_failure_signature` — `decision.failure_signature` is an `EscalationFailureSignature` value
12. `test_property_chain_budget_monotonically_non_increasing` — Hypothesis: any sequence of typed failures + escalations sees `escalations_used` strictly increase
13. `test_decision_has_triggered_by_ref` — every decision references the failure that motivated it
14. `test_protocol_satisfied_by_test_double`

### Codex recurring concerns coverage

- (a) Exception with reason: `decision.reason` is structured (`EscalationFailureSignature` enum). ✓
- (b) Production gate: `PolicyDrivenEscalator` is pure logic — no production gate needed. Document explicitly.
- (m) Free-form `reason`: replaced with enum. ✓

## Step 3.3 — `source_coverage_gate` revert to evaluative

Existing `source_coverage_gate` runs live decisions; design says it
should be evaluative only (validate recorded chain's evidence
completeness, never run the chain itself). This is a refactor:
identify the live-decision call sites, replace with assertions over
`AdapterEscalationDecision[]` + `NetworkAttemptEvidence[]` from the
run record.

### Acceptance tests (`tests/unit/test_step_3_3_source_coverage_gate_evaluative.py`)

1. `test_gate_no_longer_invokes_classifier_or_escalator` — gate run on a fixture record raises 0 `Mock.call`s on classifier/escalator stubs
2. `test_gate_reports_missing_attempt_evidence` — record with `decision.from→to` transition but no preceding `NetworkAttemptEvidence` is flagged
3. `test_gate_reports_unjustified_escalation` — escalation decision whose `failure_signature` doesn't match any preceding failure flagged
4. `test_gate_passes_complete_chain` — well-formed record passes
5. `test_gate_idempotent` — same input → same output

### Codex recurring concerns coverage

- (p) Spec/doc divergence: this step explicitly aligns implementation with `design.md` "evaluative role" wording. Document the before/after in commit message.

## Step 3.4 — eBay OAuth token cache (`FileBackedEbayTokenCache`)

File-backed, TTL'd, lockable across worktree runs. Caches OAuth
client-credentials tokens issued by eBay so a single token serves
multiple runs until its TTL expires (~7200 s typically); if a run
hits 401 mid-pagination, the cache is invalidated for that key
(scope_ref) and a fresh token fetched.

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
| Cache file on disk | secrets stored in plain JSON | File mode `0o600`; directory mode `0o700`; mode-tightening via `fchmod` (Phase 1 step 1.4 lesson — atomic open + tighten); document on-disk persistence as known limitation; production deployment migrates to OS keychain or Vault sidecar |
| Concurrent worktree access | two runs racing on token refresh | `fcntl.flock(LOCK_EX)` on the cache file during read-modify-write; never holds the lock across network I/O |
| TTL skew | clock drift | inject `clock` for tests; production reads `datetime.now(UTC)` |
| Cache corruption | bad JSON or partial write | atomic write via `os.O_TMPFILE`-style temp + rename; on read failure, fail-closed (treat as cache miss + log a warning) |

### Acceptance tests (`tests/unit/test_step_3_4_ebay_oauth_cache.py`)

1. `test_put_then_get_round_trip_returns_credential_value`
2. `test_get_returns_none_for_missing_scope`
3. `test_get_returns_none_after_ttl_expires` (inject clock)
4. `test_invalidate_removes_entry`
5. `test_concurrent_put_serialized_via_flock` — spawn 2 threads each calling `put`; assert no torn write (file readable as JSON after both complete)
6. `test_cache_file_mode_is_0600` — after `put`, `os.stat(cache_file).st_mode & 0o777 == 0o600`
7. `test_cache_dir_mode_is_0700_when_created`
8. `test_corrupt_cache_file_treated_as_miss` — write garbage to file, then `get` returns `None` and logs warning
9. `test_atomic_write_no_partial_under_simulated_crash` — patch `os.replace` to raise after write; assert original file unchanged
10. `test_credential_value_returned_does_not_leak_secret_via_repr`
11. `test_clock_injection_works`
12. `test_production_mode_gate` — under `RuntimeMode.PRODUCTION`, document this is acceptable for the eBay-specific path because the on-disk persistence is a documented operational decision (Vault sidecar override is left as a Phase 6 wiring concern); ship the cache without production gate but with explicit class docstring noting the on-disk limitation

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
    ) -> None: ...

    def list(self, *, endpoint: str, params: Mapping[str, str], scope_ref: str, run_ref: Ref) -> AmazonSpApiPaginatedResult: ...
```

### Pagination algorithm

```
list():
  pages = []
  next_token = params.get("nextToken")
  refresh_used = False
  while True:
    page_params = {**params, "nextToken": next_token} if next_token else params
    response = transport.request(...) with credential injected
    if 401 and not refresh_used:
      refresh_used = True
      vault.invalidate(scope_ref)  # forces fresh token on next call
      continue  # retry SAME page
    if 401 and refresh_used:
      return AmazonSpApiPaginatedResult(pages, AmazonSpApiPaginationFailure(...))  # terminal
    if response is FatalError:
      return AmazonSpApiPaginatedResult(pages, AmazonSpApiPaginationFailure(...))
    if response is RetryableError:
      raise  # transport retry handled at layer below
    pages.append(parse_page(response))
    next_token = parse_next_token(response)
    if next_token is None:
      return AmazonSpApiPaginatedResult(pages, None)
```

### Threat model

| Surface | Risk | Mitigation |
|---|---|---|
| `params` (caller dict) | could carry credential string | refuse `params` value of `CredentialValue` type at construction (raise `TypeError`) |
| `endpoint` | path injection / attribute traversal | validate as `^[a-z0-9/-]+$` + must start with `/` |
| `nextToken` from server | could be malicious shape | treat as opaque string; pass through; cap length at 4 KiB |
| 401 refresh loop | runaway if refresh+retry both 401 | hard cap: 1 refresh per `list()` call (state on the call, not the adapter) |

### Acceptance tests (`tests/unit/test_step_3_5_amazon_sp_api.py`)

1. `test_single_page_no_next_token_returns_one_page`
2. `test_multi_page_pagination_concatenates_results`
3. `test_401_first_call_triggers_refresh_and_succeeds_returns_full_result` — first 401 invalidates vault, second call (with fresh credential) returns 200; result contains all pages
4. `test_401_after_refresh_returns_partial_result_with_failure` — first 401 → refresh → second 401 → result has accumulated pages + non-None `final_failure`
5. `test_404_terminal_returns_partial_result_with_failure`
6. `test_retryable_error_propagates_to_transport_layer`
7. `test_credential_in_params_raises_type_error`
8. `test_endpoint_with_dotdot_rejected`
9. `test_endpoint_with_encoded_slash_rejected`
10. `test_next_token_capped_at_4_kib`
11. `test_pagination_uses_scope_policy_check_per_page` — mock scope policy, assert called once per page
12. `test_list_writes_credential_use_record_per_page` — Phase 2 step 2.4b integration: each page emits one `CredentialUseRecord`
13. `test_partial_result_replay_deterministic` — record + replay reproduces exact page set
14. `test_clock_injection_for_token_refresh_timing`

### Codex recurring concerns coverage

- (a, m) Refusal reasons: `AmazonSpApiPaginationFailure` carries structured `failure_kind: AmazonPaginationFailureKind(StrEnum)`.
- (b) Production gate: this IS the production adapter; no `ProductionRuntimeNotImplemented`. Test injects `httpx.MockTransport`.
- (l) Path canonicalization on `endpoint`.
- (i) URL handling for response headers (Phase 0 contracts already validate).

## Step 3.6 — Live test #5: eBay browse-by-keyword

`tests/integration/live/test_step_3_6_ebay_browse_keyword.py`. Marker
`@pytest.mark.live`. Resolves credentials from env (`VERACRAWL_CRED_EBAY_PROD__OAUTH`,
Phase 2 step 2.1 contract). Issues a browse query for a benign
keyword; asserts ≥1 product returned within
`RunBudget(max_pages=10, max_runtime_seconds=30)`.

### Acceptance tests

1. `test_ebay_browse_returns_at_least_one_product` (live)
2. `test_ebay_browse_stays_within_run_budget` — measures elapsed wall-clock + page count, asserts ≤ budget
3. `test_ebay_browse_emits_one_credential_use_record_per_page`
4. `test_ebay_browse_token_cache_serves_second_call_in_same_run` (cache hit measured by counter on the cache impl)

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

### Reservations carried forward

None expected. Phase 3 is mostly pure-logic + a single file-backed
cache. The dataclass-heavy approach keeps surfaces narrow.

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
