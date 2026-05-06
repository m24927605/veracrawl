# P0 Fix Pack

修復多視角 code review（Staff Architect × 2 + 資深爬蟲 + AI/LLM 工程師）發現的 8 項 P0 阻塞問題。

## 共識結論

當前 codebase 是 **contract / fixture-driven scaffolding**，不是 production-ready 系統。架構抽象（ports / contracts / hexagonal）做得乾淨，但 adapter / runtime 層的真實行為幾乎是空的。Tests 通過 ≠ 能上 prod。

## 文件結構

```
docs/plans/p0-fix-pack/
├── README.md                       # 本檔（索引 + 規範）
├── STATUS.md                       # 進度追蹤（每完成一項就更新）
├── p0-1-http-client.md             # urllib → httpx + retry/backoff/UA
├── p0-2-browser-stealth.md         # Playwright stealth + context reuse
├── p0-3-openai-adapter.md          # 修 OpenAI adapter（model name / tools / error path）
├── p0-4-tool-gateway.md            # Tool Gateway 真實 gating
├── p0-5-logging.md                 # 接 structured logging（structlog）
├── p0-6-ci-workflow.md             # GitHub Actions CI / nightly
├── p0-7-optimization-cycle.md      # 打破 optimization 循環依賴
└── p0-8-runtime-mode.md            # runtime_support 區分 prod vs fixture
```

## 工作流程

每份 plan 走相同流程：

1. **Plan review**：對該 plan 跑 codex plan review
   ```bash
   CODEX_REVIEW_ITERATION=1 ~/.claude/hooks/codex-review.sh plan \
     docs/plans/p0-fix-pack/p0-N-*.md --project-dir $PWD
   ```
   未過修正最多 5 次

2. **Implement (TDD)**：
   - a. 寫 / 更新測試（red）
   - b. 實作（green）
   - c. refactor（如必要）
   - d. `git commit`（單一邏輯變更）

3. **Task review**：對 commit 跑 codex task review
   ```bash
   BASELINE=$(git rev-parse HEAD~1) && CODEX_REVIEW_ITERATION=1 \
     ~/.claude/hooks/codex-review.sh task $BASELINE --project-dir $PWD
   ```
   未過修正最多 5 次

4. **更新 STATUS.md**：標記該 P0 為 DONE，記下 commit SHA

## 全域工程約束

- YAGNI / DRY / 最簡方案；不擴大 scope
- 每個 commit 可編譯、可測；不跳過 commit hooks
- 不刪測試、不停用 lint
- 不引入新依賴除非 P0 必要（必要時在該 plan 的 `## Dependencies` 章節說明）
- 修改前先讀現有測試與 contract，理解約束才動程式碼
- 連續 3 次同一項失敗就停下來重新評估架構；5 次仍失敗則停止並通知用戶
- 全程繁體中文溝通；程式碼註解預設不寫

## 邊界

- 不做 P0 / P1 清單外的改動（看到髒程式碼忍住）
- 不引入新模型 / 新 provider / 新 framework，除非 P0 必要
- 不重寫 hexagonal 架構，只在現有 ports / adapters 內補實作
- 不刪除既有 fixture（先標記 fixture-only，遷移留給後續 PR）

## 不要做

- 不要寫 README / 額外 docs（除非該 plan 列出）
- 不要 `git push` / 開 PR（用戶決定何時開）
- 不要 `git commit --amend`（一律新 commit）
- 不要 mock 真實外部依賴；integration test 用 `@pytest.mark.live` + skip

## P1 後續（P0 全綠後）

1. 重設計 `ModelProviderPort`（messages / tools / streaming / structured_output / token usage）
2. 集中 `Settings(BaseSettings)`，啟動 fail-fast 驗證所有 env var
3. 領域型 exception（`RetryableError` / `FatalError` / `PolicyViolation`）
4. eBay OAuth token cache（檔案級 + TTL）
5. robots.txt UA 一致 + `crawl_delay()` 落地
6. 接 OTel SDK，`TraceSpan` / `MetricSample` 真實 export
7. `objective_evidence.py` 移出 `src/` 至 `tests/fixtures/` 或 `benchmarks/`
8. 統一 `ReleaseGate` Protocol，收斂 11 個 `*ReleaseGate` class

## Recovery（context 爆掉後接手）

1. 先讀 `STATUS.md` 知道哪些 P0 已 done / in-progress / blocked
2. 讀下一個 P0 的 plan 檔
3. 讀該 plan 的 `## Scope` 章節列出的實際 source files
4. 依該 plan 的 `## Acceptance` 機械驗證條件實作
5. 完成後跑 codex task review，更新 `STATUS.md`
