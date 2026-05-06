# P0 Fix Pack — Status

| ID | Title | Status | Started | Completed | Commits | Notes |
|----|-------|--------|---------|-----------|---------|-------|
| P0-1 | HTTP client (urllib → httpx) | BLOCKED | 2026-05-06 | - | - | 3 連敗，等候用戶決策 |
| P0-2 | Playwright stealth + context reuse | NOT_STARTED | - | - | - | - |
| P0-3 | OpenAI adapter fix | IN_PROGRESS (sub-step 1/N) | 2026-05-06 | - | 4c9bce1 | RAW_RESPONSE_LEAK + bogus model name fixed; httpx/structured-output/retry deferred |
| P0-4 | Tool Gateway gating | NOT_STARTED | - | - | - | - |
| P0-5 | Structured logging | IN_PROGRESS (sub-step 5/8) | 2026-05-06 | - | sub-steps 1-4: 7 commits | redaction + logging.py + 62 個 CLI 全部包 bootstrap；剩 sub-step 5（內部模組 logger 使用）+ 6-8（boundary tests） |
| P0-6 | CI workflow | NOT_STARTED | - | - | - | - |
| P0-7 | Break optimization cycle | NOT_STARTED | - | - | - | - |
| P0-8 | Runtime mode (prod vs fixture) | NOT_STARTED | - | - | - | - |

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
