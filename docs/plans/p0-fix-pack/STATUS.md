# P0 Fix Pack — Status

## v2 production-authorized-source-crawler — Phase 0 → 6 progress

| Step | Title | Status | Commits (this attempt) | Codex iter | Reservations |
|------|-------|--------|------------------------|------------|--------------|
| 0.1 | Exception mixins (RetryableError / FatalError / PolicyViolation) | DONE | a87f606 (master) | n/a (pre-attempt) | none |
| 0.2 | Agent contracts (Message / ToolCall / ToolSpec / ResponseFormat / TokenUsage / TokenBudget / LLMExtractionCandidate / FieldCitation / FieldConfidence / RecoveryDecision / RecoveryTrace) | DONE | a08a147, c522826, 5098605, f21b7ec | 4 (approved) | 1 — see "v2 phase 0 step 0.2 reservations" below |
| 0.3 | Network / source-adapter / security-privacy contracts (NetworkAttemptEvidence / AccessControlBlocked / AdapterEscalationDecision / AdapterEscalationPolicy / CredentialScope / CredentialUseRecord) | DONE_WITH_RESERVATIONS | afa5190, ea4feb6, 5d0fc76, d95daa3, 14862f9, 6b4137d | 5 (rejected at iter-5; iter-5 findings addressed in post-iter-5 commit 6b4137d but not re-reviewed) | 1 — see "v2 phase 0 step 0.3 reservations" below |
| 0.4 | Boundary tests + 補齊 PolicyViolation 子類 (TokenBudgetExceeded / StructuredOutputViolation / CredentialScopeViolation + 5 NetworkAdapterError 子類) | DONE_WITH_RESERVATIONS | 0756310, 6d01606, 65d38d7, 177b53f, 80a3e9a, 0194304 | 5 (rejected at iter-5; iter-5 finding addressed in post-iter-5 commit 0194304 but not re-reviewed) | 1 — see "v2 phase 0 step 0.4 reservations" below |
| 1.1 | BrowserContext reuse + per-run storage_state.json persistence | DONE_WITH_RESERVATIONS | c4315d5, 9e30858, d0d6f2e, cc06de2, f7af465, 33aab34 | 5 (rejected at iter-5; iter-5 important findings addressed in post-iter-5 commit 33aab34 but not re-reviewed) | 1 — see "v2 phase 1 step 1.1 reservations" below |

**Attempt id**: `0a4ea4442335e51ed8ba7fcd5b47e8a86d4a6eea:da7df723b19ab39d21915274fef71ecb:01KR0038H38F0MFMR0H7HGHEA4`

### v2 phase 0 step 0.2 reservations

- **`ExtractionCandidate` naming divergence** (Phase 4 follow-up): design.md §3.5 listed `ExtractionCandidate` under `contracts/agent.py`, but the bare name is owned by the V1 `processing.ExtractionCandidate` heuristic contract across ~13 production imports, the foundation registry's `"ExtractionCandidate"` entry, and 8 internal target-coverage references. Phase 0 ships the v2 LLM-driven shape under the implementation-only name `LLMExtractionCandidate` plus a module-local alias inside `agent.py`. design.md was updated in commit f21b7ec to make Phase 4's reclaim of the bare name explicit; `FieldCitation` / `FieldConfidence` already ship under spec names since they have no V1 collision. **Phase 4 step 4.6** retires the legacy class and reclaims the bare name as the canonical registry/package surface.

### v2 phase 0 step 0.3 reservations

- **Runtime ReDoS hardening for `CredentialScope.allowed_route_patterns`** (Phase 2 step 2.2 follow-up): codex iter-5 important finding flagged that the substring-based nested-quantifier check missed shapes like `(a+)+`, `([a-z]+)+`, and nested alternation groups. Commit 6b4137d (post-iter-5) replaced the substring check with a structural AST walk over Python's `re._parser` that catches every `MAX_REPEAT` / `MIN_REPEAT` / `POSSESSIVE_REPEAT` operator nested inside another, so all those shapes are now refused at the contract layer. Two gaps remain that are squarely runtime concerns and belong to **Phase 2 step 2.2's `StrictAllowlistScope`**: (a) regex matches still run on the standard Python engine, which has no per-match timeout — a sufficiently pathological input could still wedge the matcher even though the AST is well-formed; (b) attacker-controlled URL paths in production hit the regex on every request, so a runtime hardening layer (timeout, alternative engine, e.g., `re2` or a glob-only DSL) is needed even with the contract-layer AST guard. The contract-layer AST detector is the appropriate Phase 0 fix; runtime defenses are Phase 2's job.

### v2 phase 0 step 0.4 reservations

- **Structured / safe-by-construction `CredentialScopeViolation.reason`** (Phase 2 step 2.2 follow-up): codex iter-5 important finding flagged that even after broadening the redaction marker tuple, the `reason` field remains free-form text — a producer could in principle pass arbitrary content that contains a credential / PII shape outside the (now-larger) marker tuple. Commit 0194304 (post-iter-5) expanded the marker tuple to cover credential markers + OAuth/OIDC parameters + session/cookie/CSRF tokens + JWTs + PII fields like `email=` / `ssn=` / `phone=`. The remaining gap is structural: a free-form string can never be 100% leak-proof via substring matching alone. **Phase 2 step 2.2** can replace `reason` with a structured (enum-coded) shape such that callers can only express known refusal reasons (`origin_not_allowed` / `route_not_allowed` / `method_not_allowed` / `expired` / etc.) — that closes the leak structurally instead of via a marker tuple. The current marker-tuple approach is the appropriate Phase 0 fix because Phase 0 is contracts-only / no behavior change; replacing the field's type is a Phase 2 redesign.

### v2 phase 1 step 1.1 reservations

- **`tests/unit/test_browser_session_storage_state.py` size + repeated fake variants** (code-organization follow-up, not Phase-tagged): codex iter-5 minor flagged that the test file grew over 1000 lines with multiple inline `_FailingContext` / `_FailingClosePageContext` / `_CorruptHydrateContext` fake browser variants that mostly differ in one method override. The file ships with 31 passing tests covering the full lifecycle but is expensive to review and maintain in this shape. A future refactor should extract the fake browser primitives into a shared `tests/_helpers/fake_playwright.py` module (or a pytest fixture factory) that lets each regression test focus on its specific override. This is a code-quality concern only — there is no correctness gap and the fakes do exercise distinct code paths. Not blocking on Phase 2; track as a low-priority refactor whenever the test file gets touched again.

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
