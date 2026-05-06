# P0 Fix Pack — Status

| ID | Title | Status | Started | Completed | Commits | Notes |
|----|-------|--------|---------|-----------|---------|-------|
| P0-1 | HTTP client (urllib → httpx) | PLAN_REVIEW | 2026-05-06 | - | - | iter 1 ❌ → v2 written |
| P0-2 | Playwright stealth + context reuse | NOT_STARTED | - | - | - | - |
| P0-3 | OpenAI adapter fix | NOT_STARTED | - | - | - | - |
| P0-4 | Tool Gateway gating | NOT_STARTED | - | - | - | - |
| P0-5 | Structured logging | NOT_STARTED | - | - | - | - |
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

- **目前活躍項**：無
- **連續失敗次數**：0
- **最後一次更新**：2026-05-06（首次建立）

## 阻塞 / 待人類決策

無。

## Codex Review 紀錄

| 階段 | 對象 | Iteration | 結果 | 修正方向 |
|------|------|-----------|------|----------|
| plan | p0-1-http-client.md | 1 | ❌ | 1 critical (per-hop SSRF) + 10 important + 1 minor |
| plan | p0-1-http-client.md | 2 | ❌ | 3 critical (failure-prop, allowlist-wiring, 4xx) + 8 important + 2 minor |

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
