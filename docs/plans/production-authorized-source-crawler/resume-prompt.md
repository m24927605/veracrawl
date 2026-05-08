# Resume prompt — production-authorized-source-crawler v2

> Paste the entire body below into a fresh Claude Code session
> after `/clear`. This document captures the rules, current
> state (as of master `5aa008a`), and environment quirks the
> previous session learned so the next session can pick up
> without re-deriving them.

---

你是一個全新的 Claude Code session,要從現有進度繼續執行 VeraCrawl
v2 production-authorized-source-crawler 的剩餘 33 個 steps
(Phase 1 step 1.2 ~ Phase 6 step 6.5)。

# 必讀順序

1. `docs/plans/production-authorized-source-crawler/implementation-prompt.md`
   ─ 完整工作流程、charter 邊界、anti-cheating 規則、38 個 steps 列表。
2. `docs/plans/p0-fix-pack/STATUS.md` ─ 當前進度紀錄。注意「v2
   production-authorized-source-crawler」區塊與「v2 phase X step Y
   reservations」段落,以及「v2 Phase 0/1 codex review log」表。
3. `docs/plans/production-authorized-source-crawler/design.md` ─ 設計
   來源,§3 ports/adapters/contracts/exception hierarchy、§4 phased
   delivery、§5-§7 acceptance gate 都會用到。
4. `AGENTS.md` 與 `docs/09-target-capability-model.md` §Safety Boundary
   (line 116) ─ charter 紅線,違反等於失敗。

# 已完成 Steps (不要重做)

| Step | Status | Master commit | Codex iter |
|------|--------|---------------|-----------|
| 0.1 | DONE | `a87f606` | n/a (pre-attempt) |
| 0.2 | DONE | `f21b7ec` | 4 (approved) |
| 0.3 | DONE_WITH_RESERVATIONS | `0ff7b28` | 5 |
| 0.4 | DONE_WITH_RESERVATIONS | `8d27548` | 5 |
| 1.1 | DONE_WITH_RESERVATIONS | `5aa008a` | 5 |

**Master HEAD 應為 `aa6990e` 或更新**(最後一個 commit 是 reassessment-20260507T181555Z.md)。如果不是,先停下來通知用戶。

# 累計 Reservations(5/8,2026-05-07 reassessment 後上限調整為 8)

1. **step 0.3**: 運行時 ReDoS hardening (timeout / alt regex engine)
   → Phase 2 step 2.2 follow-up
2. **step 0.4**: 結構化 `CredentialScopeViolation.reason` (取代 marker
   tuple) → Phase 2 step 2.2 follow-up
3. **step 1.1**: `tests/unit/test_browser_session_storage_state.py`
   refactor (>1000 行,fake browser 變體重複) → 純 code-quality
   follow-up,非 phase-tagged
4. **step 1.2**: 高並發 DNS resolution shaping for robots fetcher
   → Phase 1 step 1.6 live tests follow-up
5. **step 1.3**: post-iter-5 fix-up (1bf75d9) 處理 `RateLimitProhibited`
   contextmanager wrapping + malformed-port fallback userinfo strip,
   但無 iter-6 形式驗證 → Phase 1 step 1.6 live tests follow-up

如果再累計 3 個 reservation 觸發停損(8 上限),寫
`docs/plans/production-authorized-source-crawler/reassessment-{timestamp}.md`
並通知用戶。

詳細 reassessment 紀錄在
`docs/plans/production-authorized-source-crawler/reassessment-20260507T181555Z.md`。

# 我的 ait attempt id

```
0a4ea4442335e51ed8ba7fcd5b47e8a86d4a6eea:da7df723b19ab39d21915274fef71ecb:01KR0038H38F0MFMR0H7HGHEA4
```

每次 `ait attempt land --to master` 用這個 id。

# 環境準備(每次 session 開始驗證)

```bash
uv sync 2>&1 | tail -3
uv pip install pytest mypy ruff playwright 2>&1 | tail -3
uv run pytest 2>&1 | tail -3   # 應顯示 1973+ passed, 5 skipped
uv run pytest tests/unit/test_playwright_browser_adapter.py::test_module_does_not_ship_stealth_automation -q 2>&1 | tail -3   # charter regression,1 passed
git -C /Users/sin-chengchen/products/veracrawler/veracrawl log --oneline -1   # 應為 5aa008a 或更新
test -x ~/.claude/hooks/codex-review.sh && echo "codex hook OK"
```

任何一項失敗 → 重試一次,還失敗就通知用戶,不要 silently skip。

# 關鍵環境細節(前一個 session 踩過的雷)

## ait worktree = detached HEAD by design

每個 ait attempt 都是獨立 worktree,**detached HEAD 不是 bug 是設計**。
不要試圖 checkout `p0-fix-pack` 或其他 branch,branch ref 可能被
其他 worktree 佔用。直接在 detached HEAD 上 commit。

## codex CLI wrapper 必須繞過

`.ait/bin/codex` 是 AIT 包的 wrapper,輸出是 AIT-formatted JSON
metadata,`codex-review.sh` hook 解析不出 `approved`/`summary`/
`suggestions` 欄位 → 報「Codex CLI failed after retry」。**每次
跑 codex review 都要前置 PATH**:

```bash
BASELINE=<該 step 開始前的 master HEAD,通常是上一個 step land 後的 SHA>
CODEX_REVIEW_ITERATION=N PATH=/opt/homebrew/bin:$PATH \
  ~/.claude/hooks/codex-review.sh task $BASELINE --project-dir $PWD
```

不繞過會卡住整個流程。如果 codex 仍失敗,試 `which -a codex`
確認 `/opt/homebrew/bin/codex` 存在。

## ait attempt land 之後要 reset master worktree

`ait attempt land --to master <id>` 把 master HEAD 推進去,但不會
同步 master worktree (`/Users/sin-chengchen/products/veracrawler/veracrawl`)。
land 後會看到 `error: landed branch master but the original repository
is not clean` ─ master HEAD 已經更新,只是 working tree 沒同步。
跑這個就好(只在 master worktree 真的 clean 過、沒有遺留 work 時才能用):

```bash
git -C /Users/sin-chengchen/products/veracrawler/veracrawl reset --hard HEAD
```

如果 master worktree 不確定 clean(比如有 untracked 檔案疑似先前
工作),停下來通知用戶,不要強跑 reset --hard。

## logging boundary

Adapter / agents / fetch / extract / evidence / publish / 等
internal package 不能 `import logging` 或 `import structlog`。
要用 `from veracrawl.runtime_support.logging import get_logger` 然後
`_logger = get_logger(__name__)`。違反會被 `tests/contract/
test_logging_import_boundary.py` 擋下來。

# Per-Step 工作流程(嚴格遵守)

## 1. 讀 design.md §4 該 step 章節

找該 step 的 deliverables / acceptance criteria / dependencies。
Deliverables 模糊或衝突 → 停下來通知用戶,不要 improvise。

## 1.5 iter1 Pre-flight 6-點 mental scan(2026-05-07 reassessment 加入)

寫 test 之前必跑。觀察:codex iter5 仍出 important findings
比例約 83%,主因是 iter1 缺乏系統性 threat-modelling。在腦中
(不寫檔案)走一遍下面 6 維度,並在 commit message 的 WHY
段落裡明示**已檢查過**這 6 點,讓 codex 看得到覆蓋面:

1. **攻擊者控制輸入**:URL / origin / headers / robots body /
   port / userinfo / 任何字串字段在我的 code 裡的流向 + 例外
   字串是否 sanitise(避免 leak credentials / PII)。
2. **執行時序**:contextmanager / generator body / property /
   `__enter__` 何時跑;callback 在哪個 thread / lock 下執行;
   `@contextmanager` 的 yield 前後分別在 `__enter__` /
   `__exit__` 執行。
3. **並發**:mutable state 在多執行緒下的 race;permit / lock
   / semaphore 的 fairness + 失敗釋放;property reads 是否需要
   lock。
4. **失敗模式**:partial write、resolver failure、network
   error、disk full、信任 `Path.exists()` 而沒 `lstat()`、
   symlink、permission、corrupt persisted state 後的 retry 路徑。
5. **PRODUCTION mode**:我的 default 在 `RuntimeMode.PRODUCTION`
   是否 fail closed?有沒有 `ProductionRuntimeNotImplemented`
   gate?fixture 的測試走過的 path 是否真的是 production path?
6. **API 對稱性**:noop impl 跟 production impl 的 lifecycle /
   semantics 是否一致(release 誰負責、報告何時 mark、
   idempotency、permit 跨多 thread 的安全性)。

## 2. TDD red → green

1. 先寫 test (`tests/contract/test_step_X_Y_*.py` 或
   `tests/unit/test_step_X_Y_*.py`),每個 acceptance criterion 至少
   一個 test case。**並對 1.5 6 點掃描中發現的攻擊面 / 失敗模式
   / 並發 race 額外加測試**。
2. 跑 test 確認紅(import error 或 assertion 失敗均可)。
3. 實作,讓 test 變綠。
4. 跑這四個全綠才繼續:
   ```bash
   uv run ruff check <changed paths>
   uv run ruff format --check <changed paths>
   uv run mypy --strict <changed src paths>
   uv run pytest -q   # 全 suite
   ```

## 3. Atomic commit

```bash
git add <changed files>
git commit -m "$(cat <<'EOF'
<short title — Phase X step X.Y>

WHY <design rationale, not just what changed>...

Coverage: +N tests; existing M suite stays green for N+M total.
ruff format/check clean. mypy --strict clean. Charter regression
test still green.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
EOF
)"
```

Commit message 必須講 **why**,不只 what。提到 codex 反饋時引用
iter 編號(後續 fix-up commit 會延續這個 pattern)。

## 4. Codex Task Review(每個 step 必跑,最多 5 iter)

```bash
BASELINE=<該 step 開始前的 master HEAD>
CODEX_REVIEW_ITERATION=1 PATH=/opt/homebrew/bin:$PATH \
  ~/.claude/hooks/codex-review.sh task $BASELINE --project-dir $PWD
```

回應處理:

- `approved=true` → 進第 5 步同步 master。
- `approved=false` 且 N < 5:
  - critical / important findings → 寫修正 commit(改實作,不改測試
    繞過)。
  - minor findings → 可記為「accepted reservation」延後處理(本 step
    最多 3 個 minor reservation)。
  - 修正完跑 ruff/mypy/pytest 全綠 → N = N + 1,回第 4 步重跑。
- `approved=false` 且 N == 5:
  1. 列仍未解決 critical / important findings(完整列)。
  2. 對每個 finding 給判斷:
     - 「實際無風險,記為 accepted reservation」(限 minor 或可驗證
       無風險)
     - 「真實風險但本 step 範圍外」(記 P1 follow-up,引用 design.md
       哪節)
     - 「應該修但 codex 建議方向錯」(說明理由 + 改 commit。**不
       觸發 iter 6 codex run**,只做 post-iter-5 fix-up)
  3. STATUS.md「v2 Phase X codex review log」表 + 「v2 phase X
     step X.Y reservations」段落寫紀錄。
  4. step status = `DONE_WITH_RESERVATIONS`。
  5. 進第 5 步。

## 5. 同步 master

```bash
ait attempt land --to master 0a4ea4442335e51ed8ba7fcd5b47e8a86d4a6eea:da7df723b19ab39d21915274fef71ecb:01KR0038H38F0MFMR0H7HGHEA4
```

land 後預期看到 `error: landed branch master but the original
repository is not clean` ─ 這是正常的。再跑:

```bash
git -C /Users/sin-chengchen/products/veracrawler/veracrawl log --oneline -3   # 確認 HEAD 推進
git -C /Users/sin-chengchen/products/veracrawler/veracrawl reset --hard HEAD  # 同步 working tree
```

## 6. 更新 STATUS.md

- Step 表格(第二個): 加一行 `| X.Y | <title> | DONE / DONE_WITH_RESERVATIONS | <commit SHAs> | N (approved/...) | <reservations> |`
- Codex Review 紀錄表: 增量加每輪結果。
- 如果 DONE_WITH_RESERVATIONS,加一節「v2 phase X step X.Y
  reservations」說明未解 finding + Phase 哪步 follow-up。
- 提交 STATUS.md 為當 step 最後一個 commit:
  ```bash
  git add docs/plans/p0-fix-pack/STATUS.md
  git commit -m "Record Phase X step X.Y outcome in STATUS.md"
  ```
- 再跑一次 step 5 同步 master(STATUS.md 也要 land)。

# 失敗處理規則(停損)

## 連續 3 個 step codex 5 輪都過不了(失敗收尾)

依用戶 global CLAUDE.md「卡住 3 次重新評估架構」:
1. 停下。
2. 寫 `docs/plans/production-authorized-source-crawler/reassessment-{timestamp}.md`,
   評估是 design.md 缺陷 / dependency 沒滿足 / codex 標準太嚴。
3. 通知用戶。

## 累計 8 個 step 都 DONE_WITH_RESERVATIONS

當前已 5/8(2026-05-07 reassessment 後上限從 5 調整為 8)。
再 3 個就停,寫 reassessment,通知用戶。

## 環境問題(uv / mypy / ruff / playwright / codex 失敗)

- 第一次:重試。
- 第二次:通知用戶。
- 不 silently skip。

# 38 個 Steps(剩餘 33,依序執行)

## Phase 1 — 剩 5 steps

- **1.2** `RobotsPort` + 跨 redirect 重檢 + crawl_delay 落地
- **1.3** `RateLimiterPort` (per-(origin, route class, adapter type)
  AIMD with cooldown + jitter)
- **1.4** HAR capture via Playwright tracing + `EvidenceArtifactStorePort`
- **1.5** Per-attempt evidence + cross-redirect Authorization strip +
  ETag/Last-Modified conditional fetch + cookie jar scope
- **1.6** Live tests #1-#3 (httpbin headers / redirect-to / example.com,
  marker `@pytest.mark.live`)

## Phase 2 — 5 steps

- **2.1** `CredentialVaultPort` + `EnvVarVault`(test) + redacted
  `__repr__`/`__str__`
- **2.2** `SessionScopePolicy` + `StrictAllowlistScope` +
  `CredentialScopeViolation` 接線(消化 step 0.3/0.4 兩個
  reservation 的 runtime 部分)
- **2.3** `RedactedPromptContext` + prompt registry boundary
- **2.4** `AuthorizedSessionAdapter` + `CredentialUseRecord` outbox
- **2.5** Agent runtime credential lifecycle + 我們可控的 live test

## Phase 3 — 6 steps

- **3.1** `AccessControlClassifier`(Cloudflare/Turnstile/DataDome/
  PerimeterX/Akamai/login-wall/generic CAPTCHA → typed
  `AccessControlBlocked`)
- **3.2** `AdapterEscalationPort` + `PolicyDrivenEscalator`
- **3.3** `source_coverage_gate` 回歸驗證職責(不再跑 decision loop)
- **3.4** eBay OAuth token cache(file-backed + TTL + cross-worktree
  lock)
- **3.5** Amazon SP-API pagination + 401 token refresh + partial-batch
  tolerance
- **3.6** Live test #5(eBay browse-by-keyword)

## Phase 4 — 8 steps

- **4.1** `ModelProviderPort` v2 contract(messages/tools/response_format/
  streaming/token usage)
- **4.2** OpenAI Responses adapter v2 升級 + v1 deprecation shim
- **4.3** `AnthropicMessagesAdapter`
- **4.4** `PromptRegistryPort` + `YamlPromptRegistry`
- **4.5** `TokenBudgetPort` + `OutboxBackedBudget` + `TokenUsageEvent`
- **4.6** `schema_runtime.py` 重寫為 LLM-driven extraction
  (anchor-grounded + `FieldCitation`)。**順便處理 step 0.2 的
  `LLMExtractionCandidate` 命名 divergence**: design.md §3.5 說
  Phase 4 retire `processing.ExtractionCandidate` heuristic 並把
  bare name 還給 v2 LLM 版本。
- **4.7** `field_oracle` Tier A manual gold + Tier B official-API
  weak labels(含 adjudication)
- **4.8** Calibration layer(Platt/isotonic) + Brier/ECE/abstention
  PR-AUC metrics

## Phase 5 — 5 steps

- **5.1** `RecoveryPort`(`LLMBackedRecovery` + `HeuristicRecovery`
  兩 impl)
- **5.2** Cost gates(per-objective + per-host daily caps + 重複失敗
  hard stop)
- **5.3** Cheap classifier before LLM(status + body length +
  content-type heuristics)
- **5.4** Frontier scoring wired to LLM signals via `ModelProviderPort` v2
- **5.5** `AgentRunResult.recovery_trace` + replay 確定性 property test

## Phase 6 — 5 steps

- **6.1** `OtelObservabilityAdapter` + 真實 OTLP export
  (PRODUCTION mode 不再 raise)
- **6.2** `PresidioPiiAdapter`(`runtime_support/security_privacy.py`
  PRODUCTION mode)
- **6.3** DR live drill(real Postgres / Redis / S3 restore)
- **6.4** 7+ live integration tests in `tests/integration/live/`
- **6.5** Live failure classification + quarantine policy(typed
  category + replay repro check)

# 報告格式

## 每個 step 完成後(一行)

```
✅ Step X.Y: <名稱> | commits <SHA range> | codex iter N (approved/with-reservations) | tests +M
```

## 每個 phase 完成後

```markdown
## Phase X 完成
- Steps: N/M done, R with reservations
- Commits: <SHA range>
- Tests added: M cases (cumulative: total)
- Reservations: <list or none>
- Charter regression: ✅ green
- Master HEAD: <SHA>
```

## 全部 33 steps 完成後(最終 consolidated report)

依 implementation-prompt.md「全部 38 steps 完成後」章節格式,項目
包含: step 完成統計、codex 累計輪數、新增 tests/src 行數、未解
findings 總列、charter compliance audit、live regression 通過率、
field_oracle 量化指標、cost gate 觀察、PRODUCTION runtime mode 覆蓋、
是否達 V1 production spine gate 結論。

# Hard Constraints(不可違反,違反等於失敗)

## Charter 安全邊界(`docs/09:116`)

**禁止**任何形式的: WAF evasion / Stealth automation /
TLS-JA3 fingerprint impersonation / Ban-avoidance proxy tactics /
CAPTCHA solving / paywall bypass / login-wall circumvention /
Robots.txt 或 ToS bypass。

每個 phase 完成後,charter regression test 必須持續綠燈:
`tests/unit/test_playwright_browser_adapter.py::test_module_does_not_ship_stealth_automation`

## Hexagonal 紀律(`AGENTS.md`)

- 核心 packages 不得 `import` LangChain / LangGraph / CrewAI /
  AutoGen / Semantic Kernel
- 任何 model SDK / agent framework 必須在 `adapters/` 層
- domain layer 不得依賴 `adapters/`
- internal package 不得直接 `import logging` / `import structlog`
  (用 `runtime_support.logging.get_logger`)

## 工程紀律

- `mypy --strict` clean(必要時用 `# type: ignore[<rule>]` 加註解)
- `ruff check` + `ruff format --check` 全綠
- 全 `pytest` suite 100% pass(不可 `@pytest.mark.skip` 任何既有
  測試除非用戶明確同意)
- 每個 commit 為單一邏輯變更(atomic)
- 不跳過 commit hooks
- 不 amend commits(一律新 commit)
- 不 push 到 remote、不開 PR、不修改 git config

## Anti-cheating(嚴禁)

- ❌ 宣稱「完成」沒有機械可驗證證據(pytest log / ruff / mypy
  / codex approval / artifact path)
- ❌ 用 mock 繞過真實 code path under test(mock 應 mock 外部 I/O,
  不 mock 自家邏輯)
- ❌ 手改 fixture 讓測試假通過
- ❌ 新增 `@pytest.mark.skip` 除非用戶明確同意
- ❌ 簡化 acceptance criteria 來通過
- ❌ codex 失敗時改測試而不改實作
- ❌ 「猜測」或「假裝」實作 ─ 不確定就停下問用戶
- ❌ 跳過 codex review 因為「change is small」
- ❌ `RuntimeMode.PRODUCTION` 下用 fixture lookup 假裝已實作

# 開始

從 Phase 1 step 1.2 開始,依序執行。每個 step 完成後直接進下一個
(除非觸發停損規則或用戶要求暫停)。

每個 step 完成發一行報告,我可以中途打斷給指示。
