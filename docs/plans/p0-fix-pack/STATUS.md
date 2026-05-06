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
