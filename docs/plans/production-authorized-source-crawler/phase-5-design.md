# Phase 5 design supplement — AI planning + recovery

## Status

| Field | Value |
|---|---|
| Phase | 5 (of 0..6) |
| Sub-steps | 4 (5.1, 5.2, 5.3, 5.4) |
| Plan-review iter | drafted (JIT supplement under the front-load-design workflow) |
| Implementation status | NOT STARTED |
| Authoritative parent spec | `design.md` §4 Phase 5 |
| Depends on | Phase 0 (`RecoveryDecision` / `RecoveryTrace` / `RuntimeFrontierOptimizationDecision`); Phase 3 (typed escalation); Phase 4 (`ModelProviderPortV2`, `TokenBudgetPort`, `SchemaExtractionRuntime`) |

## Why

design.md §4 Phase 5 is ~50 lines of deliverables. Phase 5 is the
*orchestration* phase: it pulls together the typed-failure
hierarchy from Phase 3 and the LLM-call surface from Phase 4
into a recovery loop with cost gates. The design supplement
front-loads the cost-gate composition rules + the cheap-
classifier-before-LLM ordering so codex review can focus on
specific gaps rather than re-deriving the architecture.

This supplement is also the **scope-honesty** document for
Phase 5 — like Phase 4, several acceptance items
(nightly cost regression on real LLM calls, replay determinism
across thousands of recorded runs, ≥80% cheap-classifier hit
rate measured on a real failure corpus) require operational
infrastructure that this attempt cannot provision. Phase 5
sub-step deliverables in this attempt are **building-block-
only**: ports, adapters, fixture-mode tests, production gates.
Operational acceptance is recorded as Phase 6 reservations.

## Scope — In (this attempt)

- **5.1** `RecoveryPort` + `LLMBackedRecovery` adapter +
  `CheapClassifierPort` (deterministic status / body-length /
  content-type heuristics; runs before any LLM call).
- **5.2** `CostGatePort` + `InMemoryCostGate` with per-
  objective + per-host + per-run caps + repeated-failure-
  signature hard-stop. Composes multiple budgets.
- **5.3** `AgentRunController` integrator wiring
  `RecoveryPort` + `CostGatePort` +
  `SchemaExtractionRuntime` + `AgentCredentialLifecycle`
  into a single `run(request) -> AgentRunResult` call. Builds
  `RecoveryTrace` per attempt.
- **5.4** Cheap-classifier corpus (Phase 5-internal
  fixtures). Tier A is a small set of obvious dead-host /
  410-Gone / robots-blocked status combinations; Phase 6
  step 6.5 ships the production corpus + the ≥80%-hit-rate
  acceptance test.

## Scope — Out (deferred)

- **Real LLM-driven recovery decisions on production data**:
  Phase 6 step 6.1 / 6.5. Requires real API keys + a
  multi-week corpus of production failures.
- **Per-objective + per-host daily cost cap with persistent
  rolling window**: Phase 5 ships in-memory caps (process-
  lifetime). Persistent rolling-7-day caps are Phase 6 step
  6.1 (depends on production persistence).
- **Replay determinism across thousands of recorded runs**:
  Phase 6 step 6.5 (depends on production persistence +
  artifact storage).
- **Cost regression test (per-objective cost stays within
  ±20% of prior 7-day median)**: Phase 6 step 6.5 (requires
  rolling cost data from production).
- **Cheap-classifier ≥80% hit rate on production failures**:
  Phase 6 step 6.5 (requires production failure corpus).

## Rollback

- **5.1, 5.2, 5.3** are pure module additions. Revert the
  commit to roll back. No data migration concern.
- **5.4** writes JSON corpus fixtures under
  `tests/fixtures/cheap_classifier/`. Rollback: revert + no
  cleanup needed (fixtures are idempotent).

## Open Questions

1. **Failure-signature shape**: design.md says "repeated-
   same-failure-signature hard stop after N=2". The signature
   must be deterministic given the failure shape. Resolution:
   `failure_signature = sha256(error_class_name +
   sanitized_url_origin + status_code).hexdigest()[:16]`. URL
   path is excluded so different paths on the same origin
   that fail the same way coalesce.

2. **Cost-gate granularity**: per-objective + per-host caps
   compose; does the recovery layer always check both, or
   short-circuit on whichever is tighter? Resolution: check
   both on every charge; raise `CostGateExceeded` with the
   tightest cap's identity in `failed_cap` so operator
   alerting can pin the right budget.

3. **Cheap-classifier vs LLM contract**: when is the cheap
   classifier authoritative vs advisory? Resolution: cheap
   classifier returns one of `dead_host` / `permanent_block` /
   `transient_unclear` / `escalate_to_llm`. The first two
   are authoritative (no LLM call). The latter two route
   through the LLM. This avoids burning LLM tokens on 410
   Gone / DNS-NXDOMAIN / connect-refused failures.

4. **`AgentRunController` retry budget**: design.md says
   `max_recovery_iterations` per attempt = 3. Does this
   include the initial call? Resolution: NO — the initial
   call is not a "recovery iteration". `max_recovery_iterations=3`
   means up to 4 total provider calls per attempt (1 initial
   + 3 recovery).

## Test Strategy

- Per sub-step contract / unit tests with `httpx.MockTransport`
  and stub `ModelProviderPortV2`.
- Property tests for cost-gate accumulation + repeated-
  failure-signature detection.
- Fixture-mode tests for `AgentRunController` end-to-end:
  one happy path, one cheap-classifier-short-circuit, one
  cost-cap-exceeded, one repeated-failure-hard-stop.
- All tests deterministic (frozen clock, deterministic
  failure signatures, no real network).

## Acceptance Criteria — Phase-level (this attempt)

- All sub-step acceptance test lists pass (`uv run pytest`).
- `mypy --strict` passes for all new modules.
- Charter regression test stays green.
- New ports declared `@runtime_checkable` Protocol.
- `RuntimeMode.PRODUCTION` raises
  `ProductionRuntimeNotImplemented` for production-deployment
  paths (distinguished from contract / fixture surface).
- Phase 6 step 6.1 / 6.5 can begin without Phase 5
  reservations blocking it.

**Operational acceptance items deferred to Phase 6** (see
"Scope — Out"):
- Live cost regression on real LLM calls.
- Persistent rolling-7-day caps.
- Cheap-classifier ≥80% hit rate on production corpus.
- Replay determinism across thousands of runs.

---

## Substep boundaries

```
5.1 RecoveryPort + LLMBackedRecovery + CheapClassifierPort
  ▼
5.2 CostGatePort + InMemoryCostGate
  ▼
5.4 Cheap-classifier corpus (parallel with 5.1)
  ▼
5.3 AgentRunController (consumes 5.1, 5.2, 5.4)
```

## Step 5.1 — `RecoveryPort` + `LLMBackedRecovery` + `CheapClassifierPort`

Port interface:

```python
@runtime_checkable
class RecoveryPort(Protocol):
    def decide(
        self,
        *,
        failure: FatalError | RetryableError | PolicyViolation,
        attempt_evidence_ref: Ref,
        run_ref: Ref,
        recovery_iteration: int,
    ) -> RecoveryDecision: ...


@runtime_checkable
class CheapClassifierPort(Protocol):
    def classify(
        self,
        *,
        failure: FatalError | RetryableError | PolicyViolation,
        attempt_evidence_ref: Ref,
    ) -> CheapClassifierVerdict: ...
```

`CheapClassifierVerdict` enum: `DEAD_HOST` (skip — no LLM)
/ `PERMANENT_BLOCK` (skip — no LLM) /
`TRANSIENT_UNCLEAR` (route to LLM) /
`ESCALATE_TO_LLM` (route to LLM).

`HeuristicCheapClassifier`:
- `404` / `410` + body-length < 256 → `DEAD_HOST`.
- `403` + cf-ray header → `PERMANENT_BLOCK` (Cloudflare;
  charter-respected — surface, never solve).
- `RobotsBlockedError` → `PERMANENT_BLOCK`.
- 5xx + retry-after present → `TRANSIENT_UNCLEAR` (let
  recovery decide; cheap retry might suffice).
- Any other failure → `ESCALATE_TO_LLM`.

`LLMBackedRecovery`:
- Calls cheap classifier first.
- For `DEAD_HOST` / `PERMANENT_BLOCK`: returns
  `RecoveryDecision(kind=ABANDON)` directly (no LLM call).
- For `TRANSIENT_UNCLEAR` / `ESCALATE_TO_LLM`: calls
  `SchemaExtractionRuntime.extract` with a recovery-prompt
  template that asks the model to choose
  `{different_url, escalate_adapter, request_review,
  abandon}`. Charges the call to the recovery cost gate.

## Step 5.2 — `CostGatePort` + `InMemoryCostGate`

Composes multiple `TokenBudget` instances:
- per-run cap (the agent runtime's main budget).
- per-objective cap (across all runs of the same objective).
- per-host cap (across all runs hitting the same origin).
- repeated-failure-signature counter (raises hard-stop on
  `>= N=2` recurrence within a single objective).

Boundary:

```python
class CostGatePort(Protocol):
    def check(
        self,
        *,
        run_ref: Ref,
        objective_ref: Ref,
        origin: str,
        failure_signature: str | None = None,
    ) -> None: ...

    def charge(
        self,
        *,
        usage: TokenUsage,
        run_ref: Ref,
        objective_ref: Ref,
        origin: str,
    ) -> None: ...
```

Raises `CostGateExceeded` (new exception class with `failed_cap`
identifying which cap tripped) for cap breaches and
`RepeatedFailureSignatureExceeded` for signature recurrence
N=2.

## Step 5.3 — `AgentRunController`

Integrator: `run(request: AgentRunRequest) -> AgentRunResult`.

Flow:
1. Resolve credential scope via `CredentialScopeRegistryPort`
   (Phase 2 step 2.5a).
2. Open `AgentCredentialLifecycle` context (Phase 2 step 2.5a).
3. For each URL in the frontier:
   a. `cost_gate.check(...)` — refuse if any cap breached.
   b. Call `SchemaExtractionRuntime.extract(...)` (Phase 4
      step 4.6).
   c. On `FatalError` / `PolicyViolation` /
      `RetryableError` (after Phase 1's transport retry
      budget exhausts): call `recovery.decide(...)`. Apply
      the `RecoveryDecision`:
      - `DIFFERENT_URL`: caller-provided URL replaces this
        one in the frontier.
      - `ESCALATE_ADAPTER`: try the next adapter in the
        Phase 3 escalation chain.
      - `REQUEST_REVIEW`: emit `OperatorReviewRequired`
        signal + halt this URL.
      - `ABANDON`: halt this URL.
   d. Track each iteration in `RecoveryTrace`.
4. Build `AgentRunResult` with the `LLMExtractionCandidate`s
   collected + `recovery_trace`.

Caps enforced inside the loop:
- `max_recovery_iterations=3` per URL.
- `cost_gate.charge(...)` after every successful provider
  call.
- Repeated-failure-signature count tracked across recovery
  iterations within the same run.

## Step 5.4 — Cheap-classifier corpus

`tests/fixtures/cheap_classifier/`:
- `dead_host_410.json` — 410 Gone fixtures.
- `cloudflare_403.json` — Cloudflare 403 + cf-ray fixtures.
- `transient_503.json` — 503 + retry-after fixtures.
- `escalate_other.json` — fixtures that should route to LLM.

Acceptance test: each fixture file's verdict matches the
`HeuristicCheapClassifier` output. Phase 6 step 6.5 ships
the production corpus + the ≥80% hit-rate regression.

---

## Codex recurring concerns coverage

| # | Coverage |
|---|---|
| 1 | Redaction: failure messages sanitized via the existing typed-error hierarchy (Phase 0.4). |
| 2 | PRODUCTION gate: `LLMBackedRecovery._production_decide` raises until Phase 6 step 6.1. |
| 5 | `from None` + `__context__`: cost-gate breach exceptions use capture-flag pattern (mirror Phase 2). |
| 6 | Identifier shape: `objective_ref` / `origin` / `failure_signature` validated at construction. |
| 13 | Free-form reasons: `CheapClassifierVerdict` is enum, no free-form. |
| 14 | Exception `__dict__`: `CostGateExceeded.failed_cap` is the cap id (sanitized), never the budget instance. |
| 16 | Doc/spec divergence: Phase 5 sub-step docstrings + this supplement aligned at draft time; revisited at iter-1 codex review. |

## Reservations + Phase 6 hand-off

| Item | Phase 6 step | Why deferred |
|---|---|---|
| Real LLM-driven recovery on production data | 6.1 / 6.5 | requires real API keys + production failure corpus |
| Persistent rolling-7-day cost caps | 6.1 | requires production persistence |
| Cost regression (±20% of 7-day median) | 6.5 | requires rolling cost data |
| Cheap-classifier ≥80% hit rate | 6.5 | requires production failure corpus |
| Replay determinism across thousands of runs | 6.5 | requires production persistence |
