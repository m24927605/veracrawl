# P0 Fix Pack — Status

## v2 production-authorized-source-crawler — Phase 0 → 6 progress

| Step | Title | Status | Commits (this attempt) | Codex iter | Reservations |
|------|-------|--------|------------------------|------------|--------------|
| 0.1 | Exception mixins (RetryableError / FatalError / PolicyViolation) | DONE | a87f606 (master) | n/a (pre-attempt) | none |
| 0.2 | Agent contracts (Message / ToolCall / ToolSpec / ResponseFormat / TokenUsage / TokenBudget / LLMExtractionCandidate / FieldCitation / FieldConfidence / RecoveryDecision / RecoveryTrace) | DONE | a08a147, c522826, 5098605, f21b7ec | 4 (approved) | 1 — see "v2 phase 0 step 0.2 reservations" below |
| 0.3 | Network / source-adapter / security-privacy contracts (NetworkAttemptEvidence / AccessControlBlocked / AdapterEscalationDecision / AdapterEscalationPolicy / CredentialScope / CredentialUseRecord) | DONE_WITH_RESERVATIONS | afa5190, ea4feb6, 5d0fc76, d95daa3, 14862f9, 6b4137d | 5 (rejected at iter-5; iter-5 findings addressed in post-iter-5 commit 6b4137d but not re-reviewed) | 1 — see "v2 phase 0 step 0.3 reservations" below |
| 0.4 | Boundary tests + 補齊 PolicyViolation 子類 (TokenBudgetExceeded / StructuredOutputViolation / CredentialScopeViolation + 5 NetworkAdapterError 子類) | DONE_WITH_RESERVATIONS | 0756310, 6d01606, 65d38d7, 177b53f, 80a3e9a, 0194304 | 5 (rejected at iter-5; iter-5 finding addressed in post-iter-5 commit 0194304 but not re-reviewed) | 1 — see "v2 phase 0 step 0.4 reservations" below |
| 1.1 | BrowserContext reuse + per-run storage_state.json persistence | DONE_WITH_RESERVATIONS | c4315d5, 9e30858, d0d6f2e, cc06de2, f7af465, 33aab34 | 5 (rejected at iter-5; iter-5 important findings addressed in post-iter-5 commit 33aab34 but not re-reviewed) | 1 — see "v2 phase 1 step 1.1 reservations" below |
| 1.2 | RobotsPort + UrllibRobotsParser + cross-redirect re-check + crawl_delay parse | DONE_WITH_RESERVATIONS | 04aac13, 908c631, 0f14bdf, 744b8d8, ca7e4bc, ccd3eb7 | 5 (rejected at iter-5; iter-5 critical/important/minor findings addressed in post-iter-5 commit ccd3eb7 but not re-reviewed) | 1 — see "v2 phase 1 step 1.2 reservations" below |
| 1.3 | RateLimiterPort + InMemoryAimdLimiter + StdlibHttpSourceAdapter wiring | DONE_WITH_RESERVATIONS | 210e1b6, 91b8534, c6a1f7c, 45c69af, 27678d8, 1bf75d9 | 5 (rejected at iter-5; iter-5 important findings addressed in post-iter-5 commit 1bf75d9 but not re-reviewed) | 1 — see "v2 phase 1 step 1.3 reservations" below |
| 1.4 | EvidenceArtifactStorePort + LocalFsEvidenceArtifactStore + HAR capture (Playwright record_har_path) + structural HAR redaction | DONE_WITH_RESERVATIONS | b903217, 6d5c0bd, e72de1c, a2c7a4e, 9b75afe, 44e3169 | 5 (rejected at iter-5; iter-5 critical findings addressed in post-iter-5 commit 44e3169 but not re-reviewed) | 1 — see "v2 phase 1 step 1.4 reservations" below |
| 1.5 | Per-attempt NetworkAttemptEvidence + cross-redirect Authorization/Cookie strip + ETag/Last-Modified conditional fetch + per-run/per-origin cookie jar | DONE_WITH_RESERVATIONS | 635e419, 290b51c, 360e934, 8006864, 5c2e2e6, 1e8ba28 | 5 (rejected at iter-5; iter-5 important findings addressed in post-iter-5 commit 1e8ba28 but not re-reviewed) | 1 — see "v2 phase 1 step 1.5 reservations" below |
| 1.6a | Live test #1: httpbin.org/headers (Chrome UA reaches origin + AIMD limiter engaged + conditional cache populates ETag) | DONE_WITH_RESERVATIONS | 4f44ffb, 1e70b4c, 401f149, 87f4dc2, 42209c1, b8fb9cc | 5 (rejected at iter-5; iter-5 important findings addressed in post-iter-5 commit b8fb9cc but not re-reviewed) | 1 — see "v2 phase 1 step 1.6a reservations" below |
| 1.6b | Live test #2: httpbin.org/redirect-to (redirect-hop evidence + per-attempt evidence per hop + redirect_hop_refs on response) | DONE | 8954114, cd39ecc, 944d1d0 | 3 (approved) | none |
| 1.6c | Live test #3: example.com DOM + screenshot + HAR persisted via evidence store | DONE | cc5f3ad, eeeb2f9 | 2 (approved) | none |
| 2.1 | CredentialVaultPort + EnvVarVault (test/fixture impl) + opaque CredentialValue (auto-redacted repr/str/format/dir) | DONE_WITH_RESERVATIONS | 5426095, fc0cd8b, 5d739e3, d30e781, 1ebb164, fb420f0 | 5 (rejected at iter-5; iter-5 important findings addressed in post-iter-5 commit fb420f0 but not re-reviewed) | 1 — see "v2 phase 2 step 2.1 reservations" below |
| 2.2a | SessionScopePolicy port + StrictAllowlistScope core matcher (origin/route/method/expiry; defensive URL parse; userinfo refusal; path-canonicalization refusal; route length cap; invalid-scope invariant) | DONE_WITH_RESERVATIONS | a5ab243, 50dbef8, 0418866, db24b60, b86efff, 1cf4efe | 5 (rejected at iter-5; iter-5 important finding addressed in iter-5 commit 1cf4efe in-iteration) | 1 — see "v2 phase 2 step 2.2a reservations" below |

**Attempt id**: `0a4ea4442335e51ed8ba7fcd5b47e8a86d4a6eea:da7df723b19ab39d21915274fef71ecb:01KR0038H38F0MFMR0H7HGHEA4`

### v2 phase 0 step 0.2 reservations

- **`ExtractionCandidate` naming divergence** (Phase 4 follow-up): design.md §3.5 listed `ExtractionCandidate` under `contracts/agent.py`, but the bare name is owned by the V1 `processing.ExtractionCandidate` heuristic contract across ~13 production imports, the foundation registry's `"ExtractionCandidate"` entry, and 8 internal target-coverage references. Phase 0 ships the v2 LLM-driven shape under the implementation-only name `LLMExtractionCandidate` plus a module-local alias inside `agent.py`. design.md was updated in commit f21b7ec to make Phase 4's reclaim of the bare name explicit; `FieldCitation` / `FieldConfidence` already ship under spec names since they have no V1 collision. **Phase 4 step 4.6** retires the legacy class and reclaims the bare name as the canonical registry/package surface.

### v2 phase 0 step 0.3 reservations

- **Runtime ReDoS hardening for `CredentialScope.allowed_route_patterns`** (Phase 2 step 2.2 follow-up): codex iter-5 important finding flagged that the substring-based nested-quantifier check missed shapes like `(a+)+`, `([a-z]+)+`, and nested alternation groups. Commit 6b4137d (post-iter-5) replaced the substring check with a structural AST walk over Python's `re._parser` that catches every `MAX_REPEAT` / `MIN_REPEAT` / `POSSESSIVE_REPEAT` operator nested inside another, so all those shapes are now refused at the contract layer. Two gaps remain that are squarely runtime concerns and belong to **Phase 2 step 2.2's `StrictAllowlistScope`**: (a) regex matches still run on the standard Python engine, which has no per-match timeout — a sufficiently pathological input could still wedge the matcher even though the AST is well-formed; (b) attacker-controlled URL paths in production hit the regex on every request, so a runtime hardening layer (timeout, alternative engine, e.g., `re2` or a glob-only DSL) is needed even with the contract-layer AST guard. The contract-layer AST detector is the appropriate Phase 0 fix; runtime defenses are Phase 2's job.

### v2 phase 0 step 0.4 reservations

- **Structured / safe-by-construction `CredentialScopeViolation.reason`** (Phase 2 step 2.2 follow-up): codex iter-5 important finding flagged that even after broadening the redaction marker tuple, the `reason` field remains free-form text — a producer could in principle pass arbitrary content that contains a credential / PII shape outside the (now-larger) marker tuple. Commit 0194304 (post-iter-5) expanded the marker tuple to cover credential markers + OAuth/OIDC parameters + session/cookie/CSRF tokens + JWTs + PII fields like `email=` / `ssn=` / `phone=`. The remaining gap is structural: a free-form string can never be 100% leak-proof via substring matching alone. **Phase 2 step 2.2** can replace `reason` with a structured (enum-coded) shape such that callers can only express known refusal reasons (`origin_not_allowed` / `route_not_allowed` / `method_not_allowed` / `expired` / etc.) — that closes the leak structurally instead of via a marker tuple. The current marker-tuple approach is the appropriate Phase 0 fix because Phase 0 is contracts-only / no behavior change; replacing the field's type is a Phase 2 redesign.

### v2 phase 1 step 1.1 reservations

- **`tests/unit/test_browser_session_storage_state.py` size + repeated fake variants** (code-organization follow-up, not Phase-tagged): codex iter-5 minor flagged that the test file grew over 1000 lines with multiple inline `_FailingContext` / `_FailingClosePageContext` / `_CorruptHydrateContext` fake browser variants that mostly differ in one method override. The file ships with 31 passing tests covering the full lifecycle but is expensive to review and maintain in this shape. A future refactor should extract the fake browser primitives into a shared `tests/_helpers/fake_playwright.py` module (or a pytest fixture factory) that lets each regression test focus on its specific override. This is a code-quality concern only — there is no correctness gap and the fakes do exercise distinct code paths. Not blocking on Phase 2; track as a low-priority refactor whenever the test file gets touched again.

### v2 phase 1 step 1.6a reservations

- **304 short-circuit + artifact_ref reuse not asserted in the live suite** (Phase 6 step 6.4 follow-up): the live test originally tried a TWO-fetch round trip against `httpbin.org/etag/<v>` to assert second fetch returns 304 + reuses the cached `artifact_ref`. The fixture-mode tests (`tests/contract/test_step_1_5_*.py`) already cover the contract via `MockTransport` with deterministic 304 control. The live test was relaxed to assert end-to-end *cache population* (200 → ETag lands in cache) only, because httpbin's ETag endpoint may quote/transform the supplied tag value server-side, and asserting on the wire 304 was fragile to provider behavior rather than product regressions. Phase 6 step 6.4 (live failure classification) will revisit this when the real-target-drift tagging protocol is in place.

- **`Authorization` header redaction live test deferred to fixture mode** (intentional, not phase-tagged): codex iter-1 important rejected sending an `Authorization: Bearer LIVE_TEST_TOKEN_REDACT_ME` header to public httpbin.org (third-party CDN logs may capture it). The auth-redaction case stays in the fixture-mode suite where `MockTransport` + a controlled echo handler provides equivalent end-to-end coverage without leaking credential-shaped headers to a public service.

Status = DONE_WITH_RESERVATIONS because iter 5 was the last formal review under the 5-iter cap. Post-iter-5 commit b8fb9cc addresses the iter-5 important findings (live ETag round-trip narrowed to cache-population, doc consistency, comment trim).

### v2 phase 1 step 1.5 reservations

- **Multiple iter-5 deferred items + cross-port conformance + streaming-spool put** (Phase 6 / code-quality follow-ups): commit 1e8ba28 addresses the most impactful iter-5 findings — partial NetworkClientResult on failure paths (synthesizes a 502 placeholder + carries accumulated redirect_hops + attempt_evidences for replay), parametric cross-origin strip across all sensitive headers (Authorization / Cookie / Proxy-Authorization / X-Api-Key / X-Auth-Token / X-Session-Token / X-CSRF-Token), CookieRecord.value declared `field(repr=False)` so default __repr__ doesn't leak credentials via accidental f-string / log lines, CachedConditional whitespace-only validation, Expires + Max-Age=0 deletion test coverage. Deferred items:
  - **Sensitive-header constant duplication** between `contracts/network.py._SENSITIVE_HEADER_NAMES`, `stdlib_http._CROSS_ORIGIN_STRIP_HEADERS`, and `stdlib_http._EVIDENCE_REDACT_HEADERS`. Security-equivalent today (manually aligned) but a single shared constant would prevent silent divergence on future credential-header additions. Refactor concern, not blocking.
  - **`NetworkClientResult` declared positional rather than `kw_only=True`**: changing this would break 13+ existing call sites that use positional construction. Tracked as a Phase 6 cleanup when those callers can be migrated together.
  - **Adapter-level conformance tests against a real CookieJarPort**: `InMemoryCookieJar` unit tests cover per-origin / per-run scoping; an adapter-level conformance suite would catch regressions where the wiring loses scope. Code-quality follow-up.
  - **`InMemoryConditionalCache.put` materializes full body before size cap**: the per-entry size cap fires after `response.content` is read. A streaming-spool implementation (chunk-then-decide) is Phase 6 territory when S3 / encrypted-at-rest store adapters land.
  - **`cookies_for` returns `dict[str, str]` instead of ordered `list[(name, value)]`**: practical for current flows but loses RFC 6265 ordering when multiple cookies share a name across paths. Production impact small (real flows rarely have cross-path name collisions).
  - **`NoopCookieJar` documented as production default**: correct for opt-in cookie support; loud failure on production misconfiguration is a Phase 6 deployment-config concern.
  - **`_make_command(source_ref=...)` test helper parameter**: invalid command/request pairs in some tests; passes only because the adapter currently ignores `command.source_ref`. Test polish.
  Status = DONE_WITH_RESERVATIONS because iter 5 was the last formal review under the 5-iter cap.

### v2 phase 1 step 1.4 reservations

- **Step 1.4 over-iterated; multiple deferred items + design.md narrowing not yet reconciled with implementation/resume prompts** (Phase 6 / step 1.5 follow-ups): commit 44e3169 addresses iter-5 critical findings (camelCase / kebab-case / dot-case OAuth/OIDC token redaction; fail-closed wholesale redaction of malformed name-value / cookie array entries; persistent root fd opened with O_NOFOLLOW + O_DIRECTORY at __init__ via fchmod, used for all subsequent put/get to defeat post-construction root swaps). Multiple iter-5 findings remain deferred:
  - **Source-of-truth reconciliation**: design.md L409 narrowed step 1.4 to `record_har_path` only, but `EvidenceArtifactStorePort` doc still lists "HAR + screenshots + DOM + headers" and the implementation/resume prompts still reference `tracing.start({snapshots, screenshots})`. Reconcile when Phase 6 `ArtifactLifecycle` lands (it owns the screenshots + DOM persistence path).
  - **Per-attempt evidence isolation across HAR-on-context-close semantics** (Phase 1 step 1.5 follow-up): Playwright finalizes HAR on `context.close()`, so a reused per-run BrowserContext only emits one HAR per session. Phase 1 step 1.5 ("per-attempt NetworkAttemptEvidence") owns the per-attempt isolation policy — likely by closing + re-opening contexts at attempt boundaries or by indexing the run-level HAR.
  - **`_pick_har_path` silent skips on hardening failures**: production already raises when the dir cannot be created; remaining branches (non-directory, mode-tightening failure, candidate-already-exists) log + return None. Tightening these to PRODUCTION-mode raises is a Phase 6 hardening item.
  - **`get` integrity verification**: `EvidenceArtifactStorePort.get` returns bytes without re-verifying the SHA-256 encoded in the artifact_ref. A tampered local file would slip through. Add digest re-check on read in a follow-up.
  - **`put` payload-size in-memory model**: port takes `bytes`, not a stream. A streaming / chunked put surface is a Phase 6 expansion when S3 / encrypted-at-rest store adapters land. The 256 MiB default `max_payload_bytes` mitigates DoS in the meantime.
  - **IPv6 host bracket preservation in URL rebuild**: `urlsplit(...).hostname` strips the `[...]` brackets, so `http://[::1]:8080/` rebuilds incorrectly. Real-world impact small (cooperative crawler rarely hits literal IPv6 hosts) but surface a follow-up.
  - **Per-run / per-attempt directory mode normalization on existing dirs** + atomic-write concurrent-reader assertion + comprehensive contract-test parametrisation across noop + LocalFs + iter-N comment cleanup: code-quality follow-ups, not phase-tagged.
  Status = DONE_WITH_RESERVATIONS because iter 5 was the last formal review under the 5-iter cap; the post-iter-5 fix-up addresses the 3 critical findings but is not formally codex-verified.

### v2 phase 1 step 1.3 reservations

- **Post-iter-5 fix-up landed without formal codex re-verification** (per the 5-iter cap protocol): commit 1bf75d9 addresses both iter-5 important findings — (a) the `RateLimitProhibited` translation in `_send_with_rate_limit` was wrapping only the bare `acquire(...)` call, but `InMemoryAimdLimiter.acquire` is a `@contextmanager` whose body runs on `__enter__`, so the exception escaped uncaught; the catch now wraps the `with` block so a `Request-rate: 0/N` floor surfaces as `RobotsBlockedError` end-to-end (regression test `test_rate_limit_prohibited_with_real_limiter_translates_to_robots_blocked` exercises this path with a real `InMemoryAimdLimiter`); (b) `_normalize_origin`'s malformed-port fallback returned `origin.lower()` and preserved userinfo + path — credentials would have leaked into bucket keys, telemetry, and `RateLimitProhibited` exception messages for inputs like `https://user:secret@example.com:bad/path`; the fallback now builds from `parts.scheme` + `parts.hostname` and surfaces the bad port as a `<malformed-port>` token, preserving bucket-key determinism without leaking secrets. Status = DONE_WITH_RESERVATIONS because iter 5 was the last formal review; the fix-up is correct under the unit + contract tests but did not receive an iter-6 codex green-light. Phase 1 step 1.6 live tests will exercise both paths against real infrastructure and provide an additional verification surface.

### v2 phase 2 step 2.1 reservations

- **CredentialValue threat model is accidental-leak-only** (Phase 6 hardening follow-up): codex iter-5 important flagged that `_value` is a discoverable slot — `object.__getattribute__(cred, "_value")` retrieves the secret without going through `reveal()`. Commit fb420f0 (post-iter-5) addresses the casual-discovery path with `__dir__` filtering (`_value` / `_scope_ref` no longer surface in REPL / debugger / notebook listings) and tightens the docstring to make the threat-model boundary explicit (protects against logging / serialization / equality / casual `dir`; does NOT protect against intentional `__getattribute__` or in-process memory inspection — those need an external KMS / HSM). The remaining gap is structural: Python is not capability-secure, and the underlying `_value` slot still exists. Further hardening (e.g., closure-based opaque handle, ctypes-backed locked memory, or separating reveal into a context-manager that zeroes after use) is **Phase 6** territory once the production `OutboxVaultClient` lands and the threat model includes determined adversaries with code-execution access. The current contract is adequate for the cooperative-crawler use case where the threat is engineering-mistake-driven log leakage, not active compromise.
- **`reveal()` returns `str` rather than a one-shot context-managed reveal**: a future caller may bind the revealed string to a long-lived variable and re-leak it through ordinary string handling. Step 2.4 (`AuthorizedSessionAdapter`) wraps every `reveal()` site in tight scope (request-build path that immediately writes the `Authorization` header and discards). A context-managed `with cred.reveal_once() as raw:` API would tighten the contract further but is **Phase 2 step 2.4** territory once we have the canonical reveal call sites to migrate; introducing it now would just add an unused surface.
Status = DONE_WITH_RESERVATIONS because iter 5 was the last formal review under the 5-iter cap. Post-iter-5 commit fb420f0 addresses the iter-5 important findings (env-var-shape error redaction in not-found / empty-value branches, `__dir__` filter for casual-discovery, design.md double-underscore separator sync).

### v2 phase 2 step 2.2a reservations

- **Runtime ReDoS hardening still pending** (Phase 2 step 2.2c follow-up): codex flagged "no per-match timeout / no linear-time engine" as an important finding in iters 2, 3, 4, *and* 5 of step 2.2a. Step 2.2a ships two runtime mitigations on top of the contract-layer AST guard for nested quantifiers (Phase 0 step 0.3): (a) a 4 KiB hard cap on the route path the matcher will run against (bounds the worst-case work any single ``re.match`` can do on an attacker-controlled URL), and (b) an ambiguous-path refusal that rejects ``..`` / ``.`` segments + encoded ``%2e``/``%2f``/``%5c``/``%00`` + raw backslash before regex match (bypasses upstream-normalization mismatches like ``/v1/items/../admin``). The remaining gap is per-match timeout / engine: contract-valid patterns with ambiguous alternations (e.g., ``(a|aa)+``) can still backtrack catastrophically on much shorter inputs than the cap. Pulling the fix into 2.2a was considered each iteration and rejected because it adds a third-party dependency (``regex>=2024`` for ``timeout=`` kwarg, ``google-re2`` for linear-time matching) or a worker-pool integration that is a meaningful scope expansion for an atomic step. **Phase 2 step 2.2c** owns the upgrade — most likely path is adding the ``regex`` library and switching ``re.match`` to ``regex.match(timeout=0.1)``, which catches the catastrophic-backtracking shapes without changing the contract grammar. Until then, the credential gate has the contract-layer AST guard + 4 KiB cap + ambiguous-path refusal as defense in depth, which closes the realistic deployment risk (an adversary controls the *URL*, not the *pattern*) without the dependency cost.
Status = DONE_WITH_RESERVATIONS because iter 5 was the last formal review under the 5-iter cap. Iter-5 finding was fixed in iter-5 itself (1cf4efe — userinfo in ``allowed_origins`` now raises ``RuntimeError`` symmetrically with the iter-4 invalid-origin invariant).

### v2 phase 1 step 1.2 reservations

- **High-concurrency DNS resolution for `make_httpx_robots_fetcher` private-network guard** (Phase 1 step 1.6 follow-up): codex iter-5 important flagged that `_is_private_host` only blocked literal IPs / `localhost` and that hostnames resolving to private IPs slipped through `allow_private_network=False`. Commit ccd3eb7 (post-iter-5) added `_host_resolves_to_private` with an injected DNS resolver (`socket.getaddrinfo` default) that fails closed on resolver failure or any private answer. The remaining gap is a runtime-shape concern: each robots fetch under high concurrency now does a synchronous DNS query inside the per-hop policy check, with no caching / connection pool. The current implementation is correct and adequate for Phase 1's contract / unit-test scope; production load shaping (DNS cache, async resolver, or transport-level connection policy that re-validates the resolved peer) belongs to **Phase 1 step 1.6 live tests** where we wire the production fetcher into a real run loop and can measure the overhead. The fail-closed behavior (refuse on resolver failure) is the appropriate Phase 1.2 default since cooperative crawlers must not contact unresolvable hosts when private-network access is forbidden.

## v2 Phase 0 codex review log

| Step | Iter | Result | Key findings |
|------|------|--------|--------------|
| 0.2 | 1 | ❌ rejected | important: spec-name `ExtractionCandidate`/`FieldCitation`/`FieldConfidence` not exposed; non-finite floats accepted by cost validators; whitespace-only strings accepted as required identifiers |
| 0.2 | 2 | ❌ rejected | important: `source_url`/`alternative_url` accept non-http schemes; CHEAP_CLASSIFIER `cost_usd` not pinned to 0; new contracts not registered in FOUNDATION_CONTRACTS; minor: `ResponseFormat` allows `schema_name`/`strict` outside JSON_SCHEMA |
| 0.2 | 3 | ❌ rejected | important: spec-name `ExtractionCandidate`/`FieldCitation`/`FieldConfidence` still not in registry under spec names; package exports diverge from design.md §3.5 |
| 0.2 | 4 | ✅ approved | no production-blocking issues |
| 0.3 | 1 | ❌ rejected | important: `allowed_route_patterns` empty allowed; `allowed_origins` validates as URL not origin (path/query/fragment leak through); `CredentialUseRecord` allows transport failure without `attempt_evidence_ref`; `AdapterEscalationPolicy` doesn't enforce design.md §3.2 escalation chain; minor: tests don't cover all of the above |
| 0.3 | 2 | ❌ rejected | important: `CredentialScope.expires_at` time-dependent validation breaks replay determinism (rejected past expiry at construction) |
| 0.3 | 3 | ❌ rejected | important: `credential_handle_ref` accepts raw secrets like `raw_secret:...` / `password=...`; `NetworkAttemptEvidence` headers stored without redaction validation (Authorization/Cookie/X-Api-Key leak risk); minor: `AdapterEscalationPolicy` allows empty `allowed_transitions` |
| 0.3 | 4 | ❌ rejected | important: route-pattern grammar admits ReDoS patterns (`.*` catch-all, no anchoring requirement); minor: `AccessControlProvider` enum not exposed at package root |
| 0.3 | 5 | ❌ rejected | important: substring-based ReDoS detection misses `(a+)+` / `([a-z]+)+` / nested alternation groups; minor: `CredentialScope` docstring contradicts shape-only validator. **Both findings addressed in post-iter-5 commit 6b4137d** (structural AST walk for nested quantifiers + docstring update); status = DONE_WITH_RESERVATIONS because no formal iter-6 review per the 5-iter cap protocol. Runtime ReDoS hardening (timeout / alt engine) deferred to Phase 2 step 2.2 |
| 0.4 | 1 | ❌ rejected | important: `CredentialScopeViolation` formats raw caller-supplied origin/route/scope_ref/reason directly; `TokenBudgetExceeded` / `StructuredOutputViolation` defined inside OpenAI adapter (provider coupling); minor: leak test uses benign inputs |
| 0.4 | 2 | ❌ rejected | important: `scope_ref` not redacted; `requested_route` only `_redact_field` (misses non-marker query params); `_redact_url` raises `ValueError` on malformed URL; minor: `ModelProviderError` message still says "OpenAI Responses API" after move |
| 0.4 | 3 | ❌ rejected | important: `classify_provider_error` falls back to bare `ModelProviderError` for unknown codes (no marker); raw values stored on public exception attrs leak via `__dict__` / `vars(err)`; minor: tests import via re-export path only |
| 0.4 | 4 | ❌ rejected | important: malformed URL fallback through `_redact_field` lets non-marker secrets slip; provider-neutral exceptions sit under `adapters/` (core `OutboxBackedBudget` cannot import); `classify_network_failure` for unmapped enum values returns bare `NetworkAdapterError` without marker |
| 0.4 | 5 | ❌ rejected | important: `reason` field redaction still uses narrow marker tuple — `session=` / `email=` / `jwt=` / `code=` / `access_token=` slip through. **Finding addressed in post-iter-5 commit 0194304** (expanded marker tuple to cover OAuth / session / CSRF / JWT / PII parameter names); status = DONE_WITH_RESERVATIONS because no formal iter-6 review per the 5-iter cap protocol. Structural / safe-by-construction `reason` deferred to Phase 2 step 2.2 |
| 1.1 | 1 | ❌ rejected | critical: `_storage_state_filename` collision (`run:a:b`/`run:a/b`/`run:a?b` all map to same file); important: persistence has no cleanup/retention controls; cleanup not guaranteed if storage_state write raises; tautological context-reuse test |
| 1.1 | 2 | ❌ rejected | important: `_observe_on_context` cleanup not robust on failures (page assigned conditionally, unroute skipped on close failure); legacy `observe()` no longer transient (reads/writes storage_state when dir configured); minor: tests use `Path.write_text()` without explicit encoding |
| 1.1 | 3 | ❌ rejected | important: browser leak if context creation fails (browser launched before context try/finally); storage_state file permission window (write then chmod, not atomic); minor: filename can exceed POSIX `NAME_MAX` for long run_refs |
| 1.1 | 4 | ❌ rejected | important: `os.write` partial-write risk (single call without loop); `BrowserSession.context` public property weakens adapter boundary; minor: failing-context fake had wrong signature for the new no-arg `storage_state()` API |
| 1.1 | 5 | ❌ rejected | important: storage_state load trusts pre-existing file via `Path.exists()` only (symlink + broad-mode file accepted); corrupt/stale `storage_state.json` aborts entire session instead of fresh-context retry; minor: test file >1000 lines with repeated fake variants. **Both important findings addressed in post-iter-5 commit 33aab34** (read-path lstat + S_ISREG + 0o600 mode check + symlink/broad-mode quarantine; corrupt-state try/except + quarantine + retry without storage_state); status = DONE_WITH_RESERVATIONS because no formal iter-6 review per the 5-iter cap protocol. Test refactor deferred as code-quality follow-up |
| 1.2 | 1 | ❌ rejected | important: cache key was scheme+host only, mixing per-UA robots; on-disk body wrote `str(RobotFileParser)` instead of fetched bytes; tests only `pytest.raises(RobotsBlockedError)` without asserting acquisition contract; minor: 5xx test comment typo |
| 1.2 | 2 | ❌ rejected | critical: `NoopRobotsPort` default silently bypasses robots in production; UrllibRobotsParser docstring suggested `StdlibHttpSourceAdapter` as fetcher (recursive); important: `None` failure result not cached → repeated robots fetches during outage; monotonic time persisted to disk |
| 1.2 | 3 | ❌ rejected | important: `make_httpx_robots_fetcher` disabled redirect-follow, `_build_parser` parsed any 3xx body as no-rules → allow-all (redirected `/robots.txt` bypass) |
| 1.2 | 4 | ❌ rejected | important: robots fetcher has no egress / private-network policy → SSRF boundary regression (robots fetch hits private host before main adapter would refuse); `_build_parser` treats every <300 status as robots body (204/205/206 → allow-all); on-disk write not atomic; minor: `_check_robots` drops `policy_decision_refs` |
| 1.2 | 5 | ❌ rejected | critical: redirect SSRF gap — `follow_redirects=True` lets httpx contact a redirect target before per-hop policy check; important: `_is_private_host` only blocks literal IPs (hostname → private IP slips through DNS); minor: SHA-1 truncated to 16 hex chars admits collisions that would mix robots policy. **All three findings addressed in post-iter-5 commit ccd3eb7** (manual per-hop redirect with policy check ahead of every hop; DNS-aware `_host_resolves_to_private` with injected resolver and fail-closed semantics; full-length sha256 + cache_key stored in disk meta and verified on read); status = DONE_WITH_RESERVATIONS because no formal iter-6 review per the 5-iter cap protocol. High-concurrency DNS resolution shaping deferred to Phase 1 step 1.6 live tests |
| 1.3 | 1 | ❌ rejected | important: `RateLimitPermit` claims one-shot AIMD mutation but has no enforcement (duplicate `report_*` could double-count or stack decreases); `RateLimitFloor.request_rate=(0, N)` returned `inf` and would have hung a worker in `time.sleep`; minor: `_normalize_origin` left schemeless paths attached so paths split bucket state; concurrency test never asserted worker completion / exceptions |
| 1.3 | 2 | ❌ rejected | important: `_normalize_origin` built from `parts.netloc` preserved userinfo so credentialed URLs leaked into bucket keys + telemetry + `RateLimitProhibited` messages; minor: `released` / `reported` properties read mutable flags without lock; `NoopRateLimiter.report_*` released the permit while production left release to the context manager (semantic mismatch) |
| 1.3 | 3 | ❌ rejected | important: `.ait-context.md` accidentally committed (transient AIT session metadata); production HTTP path not wired to consult `RateLimiterPort`, so Phase 1 step 1.3 acceptance for cooperative pacing was not actually met; minor: `Codex iter-N` process-note comments in code |
| 1.3 | 4 | ❌ rejected | important: `RateLimitProhibited` not handled — should map to typed cooperative refusal (now `RobotsBlockedError`); `Retry-After` not propagated to `report_throttled` so cooldown ignored server hint; minor: `_logger` imported but unused |
| 1.3 | 5 | ❌ rejected | important: `RateLimitProhibited` translation wrapped only the bare `acquire(...)` call but `InMemoryAimdLimiter.acquire` is a `@contextmanager`, so prohibition raised on `__enter__` escaped uncaught; `_normalize_origin`'s malformed-port fallback returned `origin.lower()` and preserved userinfo. **Both findings addressed in post-iter-5 commit 1bf75d9** (`except RateLimitProhibited` now wraps the `with` block end-to-end with a real `InMemoryAimdLimiter` regression test using `request_rate=(0, 60)`; malformed-port fallback now builds from `parts.scheme` + `parts.hostname` + `<malformed-port>` token); status = DONE_WITH_RESERVATIONS because no formal iter-6 review per the 5-iter cap protocol |
| 1.4 | 1 | ❌ rejected | critical: cookie array name redaction missed `session`/`sid`/`csrf`/`auth_token` (cookies-by-name are credential-by-construction); important: `_redact_content` doesn't apply canaries to non-text MIMEs; `_last_har_artifact_ref` not reset between sessions; HAR capture gated by `persist`; `LocalFsEvidenceArtifactStore.get` doesn't refuse symlink traversal |
| 1.4 | 2 | ❌ rejected | critical: URL `request.url` / `response.redirectURL` only canary-scrubbed (sensitive query params + userinfo survive); `response.content.text` only redacted for text/json/form MIMEs (binary base64 PDFs / images / archives leak); important: `TRACE` in REDACTION_REQUIRED_KINDS but Playwright trace zips can't be field-level redacted; noop store ref keys only payload (production scopes by run+attempt+kind); invalid HAR shape returns synthetic empty HAR instead of raising; `test_noop_put_accepts_unredacted_screenshot` weakens contract; tests don't parametrise across all kinds; pytest.raises too broad; tracing scope still narrowed; minor: docstring inconsistency |
| 1.4 | 3 | ❌ rejected | critical: HAR staging dir lacks owner-only permissions (Playwright write window leaks unredacted bytes); test malformed-entry doesn't assert leak markers absent; important: production gate misses `har_capture_dir` requirement; HAR persistence failures swallowed silently; `digest[:16]` only 64 bits collision resistance; put doesn't symlink-check run/attempt dirs; get reopens path after lstat (TOCTOU); noop ref also 16-hex truncation; URL fragment unconditional drop; malformed URL drops host context; canaries miss creator/_/cache fields; minor: docstring outdated |
| 1.4 | 4 | ❌ rejected | critical: HAR staging not unlinked on context-create raise; put has TOCTOU (lstat + mkstemp follows path again); important: design narrowing inconsistent with port doc; deterministic HAR staging path can collide with stale; production silently disables HAR on staging-dir setup failure; symlink root accepted; no payload size cap; is_sensitive_key misses `session`/`sid`/`apiKey`/`authToken`/`code`/`jwt`; canaries not scrubbed in dict keys; encoded canary regression coverage missing; minor: contract tests only run noop |
| 1.4 | 5 | ❌ rejected | critical: camelCase OAuth/OIDC tokens (`accessToken`/`refreshToken`/`idToken`/`sessionToken`) miss redaction; malformed HAR name/value arrays passed through verbatim; root path TOCTOU on subsequent put/get reopens. **All three critical findings addressed in post-iter-5 commit 44e3169** (camelCase normalization in `_is_har_sensitive_key`; fail-closed wholesale redaction for non-dict array entries; persistent `_root_fd` opened with O_NOFOLLOW + O_DIRECTORY at __init__, fchmod-tightened, used for all put/get descriptor walks); status = DONE_WITH_RESERVATIONS because no formal iter-6 review per the 5-iter cap protocol. Multiple iter-5 important findings deferred — see "v2 phase 1 step 1.4 reservations" |
| 1.5 | 1 | ❌ rejected | critical: cookie path handling not RFC 6265 default-path; important: 304 short-circuit doesn't reuse cached body_artifact_ref; cookie Path attribute taken verbatim without validation; conditional cache only bounded by entry count |
| 1.5 | 2 | ❌ rejected | critical: Secure cookies accepted from non-HTTPS responses (RFC 6265bis violation); important: artifact_ref naming mismatch (`cached:` vs `raw-html:`); cookie cross-origin leak after Auth strip; cookie jar unbounded; HttpClientConfig.extra_headers mutable post-construction |
| 1.5 | 3 | ❌ rejected | important: CachedConditional invariants documented but not enforced; CookieJarSnapshot exposes raw values; 304 ref-reuse test doesn't verify reuse from first emission; cross-origin strip tests only cover Authorization (not Cookie/Proxy-Auth); Set-Cookie response header redaction in evidence not tested |
| 1.5 | 4 | ❌ rejected | critical: cross-origin strip misses X-Api-Key/X-Auth-Token/X-Session-Token/X-CSRF-Token; important: run_ref defaults to hardcoded fixture (cross-run leak risk); failure paths don't publish partial NetworkClientResult; conditional caching materializes full body before size budget; CachedConditional rejects only None for empty-string check; ConditionalCachePort missing clear_run; CookieJarSnapshot raw-by-default; NetworkClientResult positional construction breaks back-compat |
| 1.5 | 5 | ❌ rejected | important: failure paths still don't populate _last_result with partial evidence; CachedConditional whitespace-only validation; CookieRecord raw values in default repr; NoopCookieJar production default; cross-origin strip parametric coverage incomplete; Expires+Max-Age=0 deletion test missing. **All addressed in post-iter-5 commit 1e8ba28** (`_build_partial_failure_result` synthesizes 502 placeholder carrying accumulated evidence; parametric strip across all sensitive headers; CookieRecord.value with `field(repr=False)`; CachedConditional `.strip()` validation; +5 cookie tests for Expires future/past/invalid + Max-Age=0 deletion); status = DONE_WITH_RESERVATIONS because no formal iter-6 review per the 5-iter cap protocol |
| 1.6a | 1 | ❌ rejected | important: sent Authorization header to public httpbin.org (CDN log leak risk); wall-clock-only AIMD timing test could pass with a no-op limiter; tests not under RuntimeMode.PRODUCTION; minor: dead Accept-Language code |
| 1.6a | 2 | ❌ rejected | important: `current_rate_per_second` creates the bucket on read so prior `bucket_key in _buckets` was tautological; conditional-cache test only proved caching not the 304 round trip; unused LocalFsEvidenceArtifactStore import; minor: package doc claimed shipping #1-#3 |
| 1.6a | 3 | ❌ rejected | important: `_production_config` built configs without `egress_allowlist` / `allow_private_network=False` (live path used permissive defaults); minor: `_make_command` hardcoded source_ref while conditional-cache test used a different URL; module docstring still mentioned Accept-Language |
| 1.6a | 4 | ❌ rejected (codex critical CLAIM was incorrect — verified) | critical (incorrect): codex claimed `addopts = "-q -m 'not live'"` makes `pytest -m live` evaluate as `not live and live` → empty selection. Verified incorrect: pytest CLI `-m` REPLACES (not composes with) the addopts `-m` expression; `pytest -m live` collects 3 live tests cleanly. Documented the precedence behavior as a defensive mitigation. important: ETag substring assertion fragile to httpbin transformation; relaxed to non-empty + non-whitespace |
| 1.6a | 5 | ❌ rejected | important: 304 round-trip live test depends on httpbin's exact ETag-matching semantics (server-side quote/hash transformation); package docstring inconsistent with pyproject `addopts` shape; minor: pyproject comment embedded test count; live test over-commented with iteration history. **All addressed in post-iter-5 commit b8fb9cc** (304 round trip narrowed to cache-population assertion in the live suite — fixture-mode tests retain the deterministic 304 short-circuit + artifact_ref reuse contract; package docstring + pyproject comment trimmed; iteration-history comments removed); status = DONE_WITH_RESERVATIONS because no formal iter-6 review per the 5-iter cap protocol |
| 1.6b | 1 | ❌ rejected | important: stale `__init__.py` saying "1.6b: ... (later)"; STATUS.md missing 1.6b row; minor: iter-N review history in module docstring; inaccurate timeout comment |
| 1.6b | 2 | ❌ rejected | important: STATUS.md committed `IN_PROGRESS (codex review) | TBD`; minor: docstring claimed "Two HTTP round trips" while file has 3 tests × 2 = 6 |
| 1.6b | 3 | ✅ **approved** | no blocking findings; minor: 3 tests each perform the same live redirect (acceptable for gated live suite) |
| 1.6c | 1 | ❌ rejected | important: codex hallucinated `pytest -m live -k phase1` selection (verified absent from design.md, dismissed); module-level `_chromium_available()` launched Chromium at collection time even on `-m 'not live'` runs |
| 1.6c | 2 | ✅ **approved** | no blocking findings; minor: package doc still said 1.6c pending; comment about open_session-vs-observe inaccurate (both share lifecycle code) |
| 2.1 | 1 | ❌ rejected | important: `CredentialValue._redacted` interpolates `scope_ref` verbatim — a raw token / control-character payload passed as scope leaks via `__repr__`/`__str__`/`__format__`; `EnvVarVault` lacks production-mode gate (wiring regression could route prod credentials through env vars unaudited) |
| 2.1 | 2 | ❌ rejected | important: `CredentialValue.__init__` only rejects empty value, not whitespace — a future production vault adapter could ship blank Authorization upstream; minor: `__format__` ignored format_spec (alignment / width silently dropped) |
| 2.1 | 3 | ❌ rejected | important: `ValueError` on bad scope_ref echoes raw rejected value (caller may have passed a secret-looking string, exception text leaks it through logs / pytest output); env-var encoding ambiguous — `(scope='A_B', key='C')` and `(scope='A', key='B_C')` both alias to `VERACRAWL_CRED_A_B_C`; minor: same redaction concern in EnvVarVault identifier validator |
| 2.1 | 4 | ❌ rejected | important: port docstring still documents single-underscore env var shape after iter-3 switched impl + tests to double underscore (operators following spec would configure wrong variable); minor: `Codex iter-N` process markers in code comments should be replaced with durable rationale prose |
| 2.1 | 5 | ❌ rejected | important: `EnvVarVault` not-found / empty-value errors echo constructed env var + raw scope_ref/key (uppercase-digit tokens like AWS access key IDs pass shape regex but are still secrets); `CredentialValue._value` is a discoverable slot via `dir(cred)` (casual REPL / debugger introspection bypasses reveal contract); design.md lagged behind iter-3 double-underscore switch. **All three findings addressed in post-iter-5 commit fb420f0** (length-only redacted markers in both env-var error branches; `__dir__` filter hides `_value` / `_scope_ref` from casual introspection + explicit threat-model docstring narrowing the contract to accidental-leak-only paths; design.md updated to double-underscore env var shape with disambiguation rationale); status = DONE_WITH_RESERVATIONS because no formal iter-6 review per the 5-iter cap protocol. CredentialValue capability-secure hardening (closure-based opaque handle, ctypes-backed locked memory, one-shot context-managed reveal) deferred to Phase 6 / Phase 2 step 2.4 |
| 2.2a | 1 | ❌ rejected | important: ``re.search`` allowed unanchored prefix bypass (``/v1/items`` matched ``/prefix/v1/items``); ``urlsplit`` / ``parts.port`` raised plain ``ValueError`` on malformed authorities (contradicts typed-refusal contract) |
| 2.2a | 2 | ❌ rejected | important: runtime ReDoS deferral with no mitigation in 2.2a (credential gate relied solely on contract-time AST guard); userinfo-bearing request URL would pass origin/route/method check before vault credential attached; minor: protocol-coverage smoke test claimed more than ``isinstance`` actually verifies |
| 2.2a | 3 | ❌ rejected | important: path-canonicalization bypass — ``/v1/items/../admin`` literally matched ``^/v1/items`` regex but normalized to ``/admin`` after upstream; runtime ReDoS still partial (4 KiB cap insufficient — ambiguous alternations backtrack on shorter inputs); minor: per-request normalize-allowed-origins recompute (perf, deferred); minor: false claim that pytest unavailable in codex sandbox (locally verified) |
| 2.2a | 4 | ❌ rejected | important: empty userinfo bypass (``https://@host/...`` and ``https://:@host/...`` carry ``@`` delimiter but parse to empty username/password — truthiness check missed them); runtime ReDoS still demanded (third recurrence); silent sentinel for invalid scope origin masked contract bypass as ``origin_not_allowed`` |
| 2.2a | 5 | ❌ rejected | important: ``_normalize_allowed_origin`` ignored ``has_userinfo`` flag — a contract-bypass scope with ``allowed_origins=["https://user:pass@host"]`` would normalize to bare host and authorize requests, defeating the credential-scope guarantee. **Finding addressed in iter-5 commit 1cf4efe** (refuse userinfo-bearing allowed_origin with ``RuntimeError("validation bypass")`` symmetrically with iter-4 invalid-origin invariant); status = DONE_WITH_RESERVATIONS because no formal iter-6 review per the 5-iter cap protocol. Runtime ReDoS hardening (per-match timeout / re2 / glob-only DSL) deferred to **Phase 2 step 2.2c** per the predefined plan split |

## V1 (Sept 2026) — preserved

| ID | Title | Status | Started | Completed | Commits | Notes |
|----|-------|--------|---------|-----------|---------|-------|
| P0-1 | HTTP client (urllib → httpx) | DONE | 2026-05-06 | 2026-05-07 | (this commit) | urllib → httpx；retry/Retry-After；per-hop redirect SSRF (opt-in via config)；real Chrome UA；NetworkAdapterError(ValueError) with failure_type；20 個新 unit test |
| P0-2 | Playwright rendering stability | RETRACTED → DONE (narrowed scope) | 2026-05-07 | 2026-05-07 | 3225002 + (revert commit) | original commit shipped 5 stealth init scripts which violate docs/09:116 §Safety Boundary ("stealth automation" is forbidden); reverted. Final scope = real Chrome UA + locale + Accept-Language for rendering stability under authorized access only. context reuse stays P1. |
| P0-3 | OpenAI adapter fix | DONE (substantively) | 2026-05-06 | 2026-05-07 | 4c9bce1 + (this commit) | RAW_RESPONSE_LEAK + bogus model + urllib→httpx + retry/Retry-After + max_output_tokens raised；structured output schema wiring 列 P1 |
| P0-4 | Tool Gateway gating | IN_PROGRESS (sub-step 1/N) | 2026-05-06 | - | (this commit) | policy-aware allowlist + per-actor quota + audit log；legacy mode 保留向後相容 |
| P0-5 | Structured logging | DONE (substantively) | 2026-05-06 | 2026-05-06 | sub-steps 1-4 + boundary | infrastructure complete; boundary test 強制 internal 不能 raw import logging/structlog；P1 follow-up：CLI 非合約 print 遷移、3 個內部模組 logger demo |
| P0-6 | CI workflow | DONE | 2026-05-06 | 2026-05-06 | (this commit) | ci.yml + nightly.yml + dependabot.yml + live marker registered |
| P0-7 | Break optimization cycle | DONE | 2026-05-06 | 2026-05-06 | (this commit) | 2 types 移至 contracts/optimization_runtime.py；6 個下游 import 改 contracts；boundary test 強制 |
| P0-8 | Runtime mode (prod vs fixture) | DONE | 2026-05-06 | 2026-05-06 | cd02719 + (this commit) | foundation + 4 個 gate 接線完成；9 個 production-mode regression test |

## Status 值

- `NOT_STARTED` — 尚未開始
- `PLAN_REVIEW` — 該 plan 在跑 codex plan review
- `IN_PROGRESS` — 實作中
- `TASK_REVIEW` — 已 commit，在跑 codex task review
- `DONE` — task review 通過
- `BLOCKED` — 卡住（在 Notes 寫原因 + 連續失敗次數）

## 全局狀態

- **目前活躍項**：P0-1（BLOCKED）、P0-5（BLOCKED）
- **連續失敗次數**：P0-1=3、P0-5=3
- **最後一次更新**：2026-05-06

## 共同 Pattern 觀察（兩個 P0 plan 都 3 連敗）

| 維度 | P0-1（HTTP client） | P0-5（structured logging） |
|---|---|---|
| iter 1 | 1 critical + 10 important + 1 minor | 0 critical + 6 important + 3 minor |
| iter 2 | 3 critical + 8 important + 2 minor | 0 critical + 8 important + 3 minor |
| iter 3 | 2 critical + 6 important + 2 minor | 0 critical + 9 important + 3 minor |
| 趨勢 | 議題從契約 / SSRF 收斂到 details | 始終是 details，design 從未被質疑 |
| 關鍵差異 | P0-1 確有 critical 設計問題（SSRF / 失敗傳播）| P0-5 design 健全；codex 在挑寫作精度 |

**觀察**：codex plan review 的標準極高，每輪都會找到「缺漏的覆蓋」、「邊角 case」、「術語誤用」等。短期內難以一次過審。

## 阻塞 / 待人類決策

**P0-1 計畫 codex 連續 3 輪未通過。** 依用戶 CLAUDE.md 規範必須停下來重新評估。

iter 3 主要新問題：
1. **critical**：v3 將所有 retryable 失敗（含 transport timeout）retry 耗盡後映射至 `RETRY_EXHAUSTED`，但 unit test 6/7 期望 `NETWORK_TIMEOUT` → 自相矛盾
2. **critical**：SSRF 防護只覆蓋 redirect target；初始 request URL 未在 adapter 內 re-validate（雖然 acquisition 層有 `network_policy_failure` 檢查，但 adapter 不應假設上游必跑）
3. retry pseudocode 用 `response if 'response' in locals() else None` 會跨 iteration 讀到 stale response
4. `execute_source_acquisition` 改不吞 `NetworkAdapterError` 影響非 HTTP adapter（browser / structured source 等）— 需 call-site 分析
5. failure_report 沒帶 attempt_evidences / redirect_hops 部分結果
6. `RETRY_EXHAUSTED` enum 需在 `_failure_report` 的 operator_status mapping 加對應字串
7. redirect policy 未涵蓋：relative Location、malformed、missing scheme/host、credentialed URL、非 http(s) scheme、跨 redirect 的 header 處理（Authorization 是否帶過去）
8. DNS rebinding test / streaming size-budget test 在純 `httpx.MockTransport` 不可行（需 DNS injection / 自訂 streaming response）

觀察：每輪 codex 都解 12+ 議題但又揭露新層次。問題核心是 P0-1 的範圍太大，跨：
- adapter 層（HTTP client）
- contract 層（NetworkResponse / FailureType / AttemptEvidence）
- ports 層（NetworkClientResult）
- fetch 層（acquisition.py 的失敗傳播）
- test infrastructure（DNS / streaming injection）

**建議用戶選擇**：
- (a) 繼續 iter 4-5（風險：仍可能不過；context 持續累積）
- (b) **將 P0-1 拆為 4 個子項**並各自走 plan review：
  - P0-1a｜HTTP client 替換（urllib → httpx + UA + timeout，不含 SSRF / retry）
  - P0-1b｜Retry / Retry-After 處理
  - P0-1c｜Per-hop SSRF 加固（redirect + initial URL + DNS resolve）
  - P0-1d｜Size budget streaming + evidence
- (c) 跳過 plan review（接受當前 v3 為 working draft），直接進 TDD 實作；codex task review 抓殘留
- (d) 暫停 P0-1，先處理較簡單的 P0（P0-5 logging / P0-6 CI / P0-8 runtime mode），累積 codex review pattern 經驗後再回頭做 P0-1

## P0-5 Sub-steps

P0-5 拆為以下 atomic sub-steps，每個獨立 commit + codex task review：

1. **redaction processor** — ✅ DONE（commits `bd9b249`, `9517030`, `254ed97`, `787eb8f`；codex task review 4 輪後 approved）
   - follow-up minor：`test_processor_replaces_sensitive_primitive_at_depth_cap` 增加 `REDACTED_DEEP in serialized` 斷言
2. **structlog dependency + `logging.py` 核心** — ✅ DONE（一次 commit；用戶決策跳過 codex task review per commit）
3. `bootstrap_cli_logging` context manager + 1 個代表性 CLI 遷移
4. 其他 67 個 CLI entry points 注入 bootstrap
5. 3 個內部模組（stdlib_http / tool_gateway / observability）展示 get_logger 用法
6. 非合約 print 從代表性 CLI 移除
7. boundary tests（限制範圍 import 規則）
8. 30 個 CLI bootstrap AST scan boundary test

## Codex Review 紀錄

| 階段 | 對象 | Iteration | 結果 | 修正方向 |
|------|------|-----------|------|----------|
| plan | p0-1-http-client.md | 1 | ❌ | 1 critical (per-hop SSRF) + 10 important + 1 minor |
| plan | p0-1-http-client.md | 2 | ❌ | 3 critical (failure-prop, allowlist-wiring, 4xx) + 8 important + 2 minor |
| plan | p0-1-http-client.md | 3 | ❌ | 2 critical (retry-semantics 矛盾, initial-URL SSRF) + 6 important + 2 minor — **3 連敗，停止重新評估** |
| plan | p0-5-logging.md | 1 | ❌ | 6 important + 3 minor (no critical)：129 prints 全在 cli/、structlog factory 與 caplog 不容、idempotency、thread contextvar 錯誤聲明、entry-point 缺清單、無 redaction policy、import boundary 設計衝突 |
| plan | p0-5-logging.md | 2 | ❌ | 8 important + 3 minor (still no critical)：BoundLogger 型別矛盾、idempotency level 不真實生效、reset 動 root handlers 影響 caplog、bootstrap 缺 cid AST 檢查、prog binding leakage、runtime entry inventory 不夠具體、CLI scope/commit 訊息語義不清、import boundary 太寬、ANSI test 不可行 |
| plan | p0-5-logging.md | 3 | ❌ | 9 important + 3 minor (still no critical)：propagate=False vs caplog 矛盾、structured fields 不在 record.attr、entry-point 數應為 68 不是 30、AST 檢查太弱、cli_token 邏輯誤、bind_runtime_context 缺設計、結構化 error print 分類不清、correlation 覆蓋與 Why 矛盾、boundary 漏列 11 個套件 — **3 連敗，停 plan review，改走 TDD** |
| task | bd9b249 (P0-5 sub-step 1: redaction processor) | 1 | ❌ | 3 important：top-level only redaction（缺 recursive）、漏 password/private_key/x-api-key/session_id/csrf 等 sensitive key、STATUS.md scope 過大宣稱 |
| task | bd9b249..9517030 fix-up | 2 | ❌ | 1 important：depth cap 是 fail-open，sensitive 值在深層仍會洩漏；應 fail-closed 用 placeholder 取代整個 sub-tree |
| task | 9517030..254ed97 fix-up | 3 | ❌ | 1 important：fail-closed 後仍可能漏 primitive — 簡化為 cap 處全部替換 REDACTED_DEEP（含 primitive） |
| task | 254ed97..787eb8f fix-up | 4 | ✅ | **approved**！只剩 1 minor：建議 regression test 增加 `REDACTED_DEEP in serialized` 斷言（記為 P0-5 sub-step 1 follow-up） |

iter 1 主要問題：
1. **critical**：redirect 只擋 HTTPS→HTTP downgrade，未對 redirect target 重跑 egress / private-network / DNS-rebind policy
2. constructor 不相容當前 13 個 call site（`StdlibHttpSourceAdapter(request)` 是 request-bound，plan 提案 config-only `fetch("url")`）
3. 既有 `NetworkResponse` ref-based contract 無法承載 plan 提的 headers / elapsed / attempt_number 證據；需擴 contract 或走 sidecar artifact
4. `execute_source_acquisition` 只 catch `ValueError`，plan 的 test 期望 raw httpx 例外 → 需 deterministic 例外 → `NetworkFailureType` 映射
5. retry 設計含糊（httpx 不會自 raise 429/5xx；tenacity 不自動讀 Retry-After；max_retries 語意不明）
6. httpx proxy API 用了過時的 `proxies` 而非 0.27+ 的 `proxy=`
7. acceptance 含 P0-2 / P1-5 scope 的 UA grep（real-benchmark / browser-quality）
8. AGENTS.md spec 追溯要求 — 但用戶已拔除 spec-kit
9. 測試用 10.255.255.1 黑洞 IP / `https://x.test` / `MockTransport` 驗 proxy 等不可靠
10. live test 用 httpbin.org/status/429 永遠回 429 無法驗 retry-to-200
11. 寫死 `Wed, 21 Oct 2026 ...` HTTP-date / `Chrome 131` 字面值
12. HTTP/2 motivation 與 dependencies 矛盾

v3 修正策略（iter 2 主要問題）：

iter 2 critical：
1. `execute_source_acquisition` 內部 catch `ValueError` 會吞掉 `NetworkAdapterError` → 必須改 acquisition.py 使其不吞此 type
2. `egress_allowlist` 在 adapter config 預設空集合，但 13 個 call site 用 `StdlibHttpSourceAdapter(request)` 不傳 config → 跨域 redirect 仍未擋 → factory + 接線到 `execute_http_network_acquisition`
3. retry 迴圈把 401/403/404/410/422 當 success 回，但呼叫端假設「any adapter result is success」→ 必須明確決定 4xx 是「成功 HTTP 採集」（status 寫進 NetworkResponse）

iter 2 important：
4. evidence 沒有 artifact_store 注入點 → 改為 inline list（無 store 依賴）
5. raise 時 `last_result` 為 None → 失敗仍 populate 部分結果
6. `RETRY_EXHAUSTED` enum 不存在 + last_failure_type 對 retryable 5xx 未更新
7. `MockTransport` 無注入點 → 加 `transport=` constructor kwarg
8. retry 計時測試會睡 2-60s flaky → 注入 `sleep_fn`、`clock_fn`；`_compute_wait` 變 pure function 直接驗
9. timeout 雙來源（config vs request.timeout_ms）邏輯矛盾 → 規則：config 顯式注入時 canonical；無 config 時用 request.timeout_ms
10. 沒做 size_budget streaming → 用 `httpx.iter_bytes` streaming
11. exception mapping 太粗（ConnectError 全部 → NETWORK_TIMEOUT）→ DNS/refused/TLS/proxy 細分

iter 2 minor：
12. 列 tenacity 但實際自寫 → 移除 tenacity，stdlib random.uniform
13. HTTP/2 motivation 與 scope 矛盾 → 徹底移除

v3 主要新增結構：
- `NetworkClientResult.attempt_evidences: list[NetworkAttemptEvidence]`（inline）
- `NetworkFailureType.RETRY_EXHAUSTED` 新 enum
- `build_http_adapter_for_acquisition` factory 接線 allowlist
- `transport` / `sleep_fn` / `clock_fn` 注入點
- 4xx 設計決策：視為「成功 HTTP 採集」，status 帶出去由上游分類
- exception mapping 表格化
- streaming size budget enforcement
- `_compute_wait` pure function（測試直接驗）

v2 修正策略：
- 保留現有 constructor + execute() 介面，新加 `*, config=None` kwarg
- 自寫 retry loop，不依賴 tenacity decorator；明確 `max_attempts`（含首次）
- per-hop redirect 重跑完整 policy（egress + private + DNS resolve + protocol）
- 證據走 sidecar artifact `NetworkAttemptEvidence`，不破現有 ref-based contract
- 例外全部 `ValueError` 子類附 `failure_type` 屬性，向後相容 catch
- pin `httpx>=0.27,<1.0` + `proxy=`
- acceptance 只驗 P0-1 scope 的 UA
- 用 `pytest-httpserver` 取代 httpbin / 黑洞 IP
- 移除 HTTP/2 自 motivation（列 P1）
- 對齊 `docs/02-production-architecture.md` + `docs/07-data-contracts.md`（spec 追溯改走 docs/，因 spec-kit 已拔）


## 完成清單

P0 全綠後，產出：
- 新增 / 修改 / 刪除檔案統計
- 測試新增數量 + 覆蓋率變化
- 已知未解問題（不要藏）
- 需要人工決策的 open questions
