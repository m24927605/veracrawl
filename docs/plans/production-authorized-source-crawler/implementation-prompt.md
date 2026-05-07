# Implementation prompt — production-authorized-source-crawler phases 0–6

> Paste the entire body below into a fresh Claude Code session (after `/clear`).
> The prompt is self-contained; it does not depend on prior conversation
> context. The repo's `docs/plans/production-authorized-source-crawler/design.md`
> is the source of truth for what each phase / step ships.

---

# 角色

你是 Staff Engineer + 資深爬蟲 + 資深 AI/LLM 系統工程師複合身分,負責實作 VeraCrawl
v2 設計文件的全部 38 個剩餘 steps(Phase 0 step 2 ~ Phase 6 step 5)。

VeraCrawl 由 AI agent 撰寫;吞吐量不是約束。**正確性、設計符合度、charter 合規、
真實實作**才是約束。

# Repo & 文件

- Master worktree: `/Users/sin-chengchen/products/veracrawler/veracrawl`
- Active worktree: `/Users/sin-chengchen/products/veracrawler/veracrawl/.ait/workspaces/attempt-0001-01kqyqq7q0dj3yh05am761jks1`
- Active branch: `p0-fix-pack`(master 與此 branch 已同步至 `a87f606` 或更新)
- 設計文件: `docs/plans/production-authorized-source-crawler/design.md`
- 進度紀錄: `docs/plans/p0-fix-pack/STATUS.md`(沿用,新增 v2 phase 區塊)
- Anchor docs(必讀以確認規範):
  - `docs/01-product-definition.md`
  - `docs/02-production-architecture.md`
  - `docs/06-agent-system-design.md`
  - `docs/07-data-contracts.md`
  - `docs/08-build-roadmap.md`
  - `docs/09-target-capability-model.md`(特別 §Safety Boundary L116)
  - `AGENTS.md`(Hard Constraints + Python And Agent Framework Boundary)

# Hard Constraints(不可違反,違反等於失敗)

## Charter 安全邊界(`docs/09:116`)

**禁止**任何形式的:

- WAF evasion(Cloudflare 5s solver、Turnstile bypass、DataDome / PerimeterX / Akamai 規避)
- Stealth automation(`navigator.webdriver` / `plugins` / `languages` / `chrome.runtime` / Permissions API patches)
- TLS / JA3 fingerprint impersonation(`curl_cffi --impersonate` 等)
- Ban-avoidance proxy tactics(residential rotation 作為 evasion 用途)
- CAPTCHA solving / paywall bypass / login-wall circumvention
- Robots.txt / ToS / customer authorization bypass

每個 phase 完成後,charter regression test 必須持續綠燈:
`tests/unit/test_playwright_browser_adapter.py::test_module_does_not_ship_stealth_automation`

## Hexagonal 紀律(`AGENTS.md`)

- 核心 packages 不得 `import` LangChain / LangGraph / CrewAI / AutoGen / Semantic Kernel
- 任何 model SDK / agent framework 必須在 `adapters/` 層
- domain layer 不得依賴 `adapters/`

## 工程紀律

- `mypy --strict` clean
- `ruff check` + `ruff format --check` 全綠
- 全 `pytest` suite 100% pass(不可 `@pytest.mark.skip` 任何既有測試除非用戶明確同意)
- 每個 commit 為單一邏輯變更(atomic)
- 不跳過 commit hooks
- 不 amend commits(一律新 commit)
- 不 push 到 remote、不開 PR、不修改 git config

## 不准做的事(anti-cheating)

- ❌ 不得宣稱「完成」而沒有機械可驗證證據(pytest log、ruff/mypy 輸出、codex approval、artifact path)
- ❌ 不得用 mock 繞過真實 code path under test(mock 應 mock 外部 I/O,不 mock 自家邏輯)
- ❌ 不得手改 fixture 讓測試假通過
- ❌ 不得新增 `@pytest.mark.skip` 除非用戶明確同意
- ❌ 不得簡化 acceptance criteria 來通過
- ❌ 不得在 codex review 失敗時改測試而不改實作
- ❌ 不得「猜測」或「假裝」實作 — 不確定就停下來問用戶
- ❌ 不得跳過 codex review 因為「change is small」
- ❌ 不得在 `RuntimeMode.PRODUCTION` 下用 fixture lookup 假裝已實作

# Per-Step 工作流程(嚴格遵守)

對每一個 step:

## 1. 讀規範

讀 `design.md §4` 該 phase 章節找該 step 的:

- Deliverables(必須全部 ship)
- Acceptance criteria(必須全部機械可驗證通過)
- Dependencies(必須先確認前置 phase / step 已完成)

如果 deliverables 模糊、依賴衝突、或 charter 邊界不明 → **停下來通知用戶**,不要 improvise。

## 2. TDD 實作

1. 寫測試(red)— 必須對 deliverables 的每個 acceptance criterion 有對應 test case
2. 實作(green)
3. refactor(如必要)
4. 跑:
   ```
   uv run ruff check <changed paths>
   uv run ruff format --check <changed paths>
   uv run mypy --strict <changed src paths>
   uv run pytest -q  # 全 suite,不只新檔
   ```
5. 全綠才繼續;否則先修

## 3. Atomic Commit

- 一個 step = 一個 logical commit(必要時可拆 2-3 個 sub-commits 但屬同一 step)
- Commit message 必須描述 **why**,不只 what
- 結尾加:
  ```
  Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
  ```

## 4. Codex Task Review(每個 step 必跑,最多 5 次)

```
BASELINE=$(git rev-parse HEAD~1)  # 該 step 開始前的 HEAD
CODEX_REVIEW_ITERATION=N ~/.claude/hooks/codex-review.sh task $BASELINE --project-dir $PWD
```

### 處理 codex 回應

- **`approved=true`**:step 完成。更新 STATUS.md(記 commit SHA + iteration N + 任何 minor reservation)→ 進入第 5 步同步 master
- **`approved=false` 且 N < 5**:
  - 讀 suggestions
  - 對 critical / important findings 寫修正 commit(**不修測試規避** — 修真實實作)
  - 對 minor findings 可記錄為「accepted with reservation」延後處理(最多 3 個)
  - 跑 ruff / mypy / pytest 全綠
  - N = N + 1,回到第 4 步重跑 codex review
- **`approved=false` 且 N == 5**:你決定修復方式:
  1. 列出仍未解決的 critical / important findings(complete list)
  2. 對每個 finding 給出明確判斷:
     - 「實際無風險,記為 accepted reservation」(限 minor / 可驗證無風險)
     - 「真實風險但本 step 範圍外」(記為 P1 follow-up,引用 design.md 哪節)
     - 「應該修但 codex 建議方向錯」(給出你的修法理由 + 改 commit)
  3. 在 STATUS.md「Codex Review 紀錄」記下:
     - 5 輪 iteration 的關鍵 findings
     - 你的最終決策 + 理由
     - 未解決 findings 的 follow-up tracking
  4. 標記 step status = `DONE_WITH_RESERVATIONS`
  5. 進入下一步

## 5. 同步 master

```
git -C /Users/sin-chengchen/products/veracrawler/veracrawl merge --ff-only p0-fix-pack
```

驗證 fast-forward 成功;若失敗(不應該發生)則停下來通知用戶。

## 6. 更新 STATUS.md

- Step 表格:標 `DONE` / `DONE_WITH_RESERVATIONS` + commit SHAs + codex iter 數
- Codex Review 紀錄:增量追加每輪結果

# 失敗處理規則

## 連續 3 個 step 失敗(codex 5 輪都過不了)

依用戶 global CLAUDE.md「卡住 3 次重新評估架構」:

1. 停下來
2. 重新評估:是 design.md 有缺陷?是 dependencies 沒滿足?是 codex review 太嚴?
3. 寫一份 reassessment markdown 到 `docs/plans/production-authorized-source-crawler/reassessment-{timestamp}.md`
4. 通知用戶等指示,不繼續

## 5 個 step 都用 `DONE_WITH_RESERVATIONS` 結尾

即使沒連續失敗,但累積 5 個 reservations 表示 design 或 codex review 標準有系統性偏差:

1. 停下來
2. 寫 reassessment
3. 通知用戶

## 環境問題(`uv` / `mypy` / `ruff` / `playwright` 安裝失敗)

- 第一次失敗:嘗試 `uv sync` / `uv pip install pytest mypy ruff` 修復
- 第二次失敗:通知用戶
- 不要 silently skip 因為 tool 失敗

# 38 個 Steps 順序

依 `design.md §4` 順序執行,phase 間不可跳過:

## Phase 0(contracts + exception hierarchy)— 3 steps 剩餘

- **0.2** Agent contracts: `Message`, `ToolCall`, `ToolSpec`, `ResponseFormat`, `TokenUsage`, `TokenBudget`, `ExtractionCandidate`, `FieldCitation`, `FieldConfidence`, `RecoveryDecision`, `RecoveryTrace`
- **0.3** Network/source_adapter/security_privacy contracts: `NetworkAttemptEvidence`, `AccessControlBlocked`, `AdapterEscalationDecision`, `AdapterEscalationPolicy`, `CredentialScope`, `CredentialUseRecord`
- **0.4** Boundary tests + 補齊 PolicyViolation 子類: `TokenBudgetExceeded`, `StructuredOutputViolation`, `CredentialScopeViolation`

## Phase 1(cooperative HTTP + browser baseline)— 6 steps

- **1.1** BrowserContext reuse + `storage_state.json` 持久化
- **1.2** `RobotsPort`(fetch + cache + 跨 redirect 重檢 + crawl_delay 落地)
- **1.3** `RateLimiterPort`(per-(origin, route class, adapter type) AIMD with cooldown + jitter)
- **1.4** HAR capture via Playwright tracing + `EvidenceArtifactStorePort`
- **1.5** Per-attempt evidence + cross-redirect Authorization strip + ETag/Last-Modified conditional fetch + cookie jar scope
- **1.6** Live tests #1-#3(`@pytest.mark.live`: httpbin headers / redirect-to / example.com)

## Phase 2(authorized session subsystem)— 5 steps

- **2.1** `CredentialVaultPort` + `EnvVarVault`(test)+ redacted `__repr__`/`__str__`
- **2.2** `SessionScopePolicy` + `StrictAllowlistScope` + `CredentialScopeViolation`
- **2.3** `RedactedPromptContext` + prompt registry boundary(拒絕 credential 進 prompt)
- **2.4** `AuthorizedSessionAdapter` + `CredentialUseRecord` outbox
- **2.5** Agent runtime credential lifecycle + 我們可控的 live test

## Phase 3(access control classification + escalation)— 6 steps

- **3.1** `AccessControlClassifier`(Cloudflare / Turnstile / DataDome / PerimeterX / Akamai / login-wall / generic CAPTCHA → typed `AccessControlBlocked`)
- **3.2** `AdapterEscalationPort` + `PolicyDrivenEscalator`
- **3.3** `source_coverage_gate` 回歸驗證職責(不再跑 decision loop)
- **3.4** eBay OAuth token cache(file-backed + TTL + cross-worktree lock)
- **3.5** Amazon SP-API pagination + 401 token refresh + partial-batch tolerance
- **3.6** Live test #5(eBay browse-by-keyword)

## Phase 4(LLM provider port v2 + extraction)— 8 steps

- **4.1** `ModelProviderPort` v2 contract(messages / tools / response_format / streaming / token usage)
- **4.2** OpenAI Responses adapter v2 升級 + v1 deprecation shim
- **4.3** `AnthropicMessagesAdapter`
- **4.4** `PromptRegistryPort` + `YamlPromptRegistry`(含 immutable version refs + experiment manifest)
- **4.5** `TokenBudgetPort` + `OutboxBackedBudget` + `TokenUsageEvent`
- **4.6** `schema_runtime.py` 重寫為 LLM-driven extraction(anchor-grounded + `FieldCitation`)
- **4.7** `field_oracle` Tier A manual gold + Tier B official-API weak labels(含 adjudication)
- **4.8** Calibration layer(Platt / isotonic)+ Brier/ECE/abstention PR-AUC metrics

## Phase 5(AI planning + recovery)— 5 steps

- **5.1** `RecoveryPort`(`LLMBackedRecovery` + `HeuristicRecovery` 兩 impl)
- **5.2** Cost gates(per-objective + per-host daily caps + repeated-failure hard stop)
- **5.3** Cheap classifier before LLM(status + body length + content-type heuristics)
- **5.4** Frontier scoring wired to LLM signals via `ModelProviderPort` v2
- **5.5** `AgentRunResult.recovery_trace` + replay 確定性 property test

## Phase 6(V1 production spine gate)— 5 steps

- **6.1** `OtelObservabilityAdapter` + 真實 OTLP export(PRODUCTION mode 不再 raise)
- **6.2** `PresidioPiiAdapter`(`runtime_support/security_privacy.py` PRODUCTION mode)
- **6.3** DR live drill(real Postgres / Redis / S3 restore)
- **6.4** 7+ live integration tests in `tests/integration/live/`
- **6.5** Live failure classification + quarantine policy(typed category + replay repro check)

# 真實實作的硬性要求

每個 phase 完成後,下面這些 capability **必須真實**而不是 fixture refs:

## Phase 1 完成後

- BrowserContext 真的跨 navigation reuse(assert via mock playwright + call counts)
- robots.txt 真的被 fetch + parse + 套用(live test against httpbin/robots.txt 變體)
- AIMD rate limiter 真的記錄 success / 429 並調整(property test 驗 token bucket math)
- HAR file 真的存在於 artifact store(檔案存在 + JSON valid)

## Phase 2 完成後

- Credential 從 `EnvVarVault` 真的能取得 + scope 真的驗證
- Credential 不會出現在 prompt registry resolved output(assert via property test)
- `AuthorizedSessionAdapter` 真的注入 header + 真的 audit 寫 outbox

## Phase 3 完成後

- `AccessControlClassifier` 真的能 classify Cloudflare / DataDome 等的 fingerprint pattern(assert via fixture HTML samples)
- `AdapterEscalationPort` 真的 walk 鏈(HTTP→browser only when policy allows)
- eBay token cache 真的避免重複 OAuth(property test:呼叫 N 次只 OAuth 1 次)

## Phase 4 完成後

- LLM 真的被 call(live test against OpenAI / Anthropic with real API keys)
- `ExtractionCandidate` 真的有 anchor-grounded citations(assert citation refs exist in DOM)
- `field_oracle` Tier A 真的有手工驗證資料(≥50 entries,commit 進 repo 或 fixture)
- Calibration 真的計算 Brier/ECE(real numbers, not stubs)

## Phase 5 完成後

- `RecoveryPort` 真的能在 typed failure 時提出 alternative(不是 hardcoded 回 abandon)
- Cost gate 真的 enforce(property test:超過 cap 真的 raise)

## Phase 6 完成後

- OTel collector 真的收到 spans(local OTLP collector + assertion)
- PRODUCTION mode 真的不 raise `NotImplementedError` 對 live test 走過的 path
- Live regression 真的對外部 service 跑(不是 mock httpbin)

# 報告格式

## 每個 step 完成後(一行)

```
✅ Step X.Y: <名稱> | commit <SHA> | codex iter N (approved/with-reservations) | tests +M
```

## 每個 phase 完成後(短結構化報告)

```
## Phase X 完成
- Steps: N/M done, R with reservations
- Commits: <SHA range>
- Tests added: M cases (cumulative: total)
- Reservations: <list or none>
- Charter regression: ✅ green
- Master HEAD: <SHA>
```

## 全部 38 steps 完成後(最終 consolidated report)

- Step 完成統計(`DONE` / `DONE_WITH_RESERVATIONS` / 失敗)
- Codex review 累計輪數 + approved 比率
- 累計新增 tests 數量 + suite runtime
- 累計新增 src/ 行數 + 新增 dependencies
- 未解決的 codex findings 總列(critical / important 列出每個 + follow-up)
- Charter compliance audit(boundary test 結果)
- Live regression 通過率
- `field_oracle` 量化指標(Brier / ECE / abstention PR-AUC)
- Cost gate 實際觀察(per-objective、per-host daily 觸發次數)
- PRODUCTION runtime mode 覆蓋(哪些 path 實作、哪些仍 `NotImplementedError`)
- 結論:是否達到 V1 production spine gate acceptance(§7)?是 / 否 + 證據

# 環境準備

工作前先驗證:

```
uv sync 2>&1 | tail -3
uv pip install pytest mypy ruff 2>&1 | tail -3
uv run pytest -q 2>&1 | tail -3  # 應顯示 1500+ tests pass
test -x ~/.claude/hooks/codex-review.sh && echo "codex hook OK"
git log --oneline -1  # 應顯示 a87f606 或更新
```

任何一項失敗 → 通知用戶,不開始 step 0.2。

# 開始

從 Phase 0 step 2 開始,依序執行。每個 step 完成後直接進入下一個(除非觸發停損規則)。
