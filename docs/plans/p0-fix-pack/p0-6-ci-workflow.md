# P0-6: CI Workflow

## Status
NOT_STARTED

| | |
|---|---|
| Started | - |
| Completed | - |
| Commits | - |
| Codex plan review | - |
| Codex task review | - |

## Why

- `.github/workflows/` **不存在**
- `pyproject.toml` 有 ruff / mypy / pytest 設定，但**沒有自動化 gate**
- `release_gate.py` 是 fixture runner，不是 deploy gate
- PR 進來與 push 上去都沒任何自動驗證 → P0-1 ~ P0-5 改完也無法防止 regression

## Scope

**In scope:**

- 新增 `.github/workflows/ci.yml`（PR + push 觸發；跑 ruff / mypy / pytest non-live）
- 新增 `.github/workflows/nightly.yml`（cron 觸發；跑 `@pytest.mark.live` 整合測試）
- 新增 `.github/dependabot.yml`（基礎依賴更新）
- 確保 `pytest.ini_options.markers` 有定義 `live` marker（避免 PytestUnknownMarkWarning）

**Out of scope:**

- Release / deploy workflow（屬 P1）
- Coverage reporting（codecov / coveralls）— 列 P1
- Container build / SBOM — 列 P1
- 自動 PR labelling — 不必要

## Design

### `ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - name: Install uv
        run: pip install uv
      - name: Install deps
        run: uv sync --frozen
      - name: ruff check
        run: uv run ruff check .
      - name: ruff format check
        run: uv run ruff format --check .

  type-check:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install uv
      - run: uv sync --frozen
      - run: uv run mypy src/

  test:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    strategy:
      matrix:
        python-version: ["3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
      - run: pip install uv
      - run: uv sync --frozen
      - name: Install Playwright browsers
        run: uv run playwright install --with-deps chromium
      - name: Run pytest (non-live)
        run: uv run pytest -m "not live" -v --maxfail=10
        env:
          VERACRAWL_LOG_LEVEL: WARNING
```

### `nightly.yml`

```yaml
name: Nightly Live Tests

on:
  schedule:
    - cron: "0 7 * * *"   # UTC 07:00 = 台灣 15:00
  workflow_dispatch:        # 允許手動觸發

jobs:
  live-tests:
    runs-on: ubuntu-latest
    timeout-minutes: 60
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install uv
      - run: uv sync --frozen
      - run: uv run playwright install --with-deps chromium
      - name: Run live tests
        run: uv run pytest -m "live" -v --maxfail=5
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          EBAY_CLIENT_ID: ${{ secrets.EBAY_CLIENT_ID }}
          EBAY_CLIENT_SECRET: ${{ secrets.EBAY_CLIENT_SECRET }}
          AMAZON_API_KEY: ${{ secrets.AMAZON_API_KEY }}
          # 其他 live test 需要的 secrets
          VERACRAWL_LOG_LEVEL: INFO
      - name: Upload test artifacts on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: live-test-artifacts
          path: |
            tests/_artifacts/
            **/htmlcov/
          retention-days: 7
```

### `pytest.ini_options.markers`

`pyproject.toml`：

```toml
[tool.pytest.ini_options]
markers = [
    "live: tests that hit real external services (skipped in CI default)",
]
```

預設 `pytest` 跑全部；`pytest -m "not live"` 跳過 live；`pytest -m "live"` 只跑 live。

### `.github/dependabot.yml`

```yaml
version: 2
updates:
  - package-ecosystem: pip
    directory: /
    schedule:
      interval: weekly
    open-pull-requests-limit: 5
    labels:
      - dependencies
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

## Dependencies

無新 Python 依賴。但需要：
- GitHub Actions secrets（`OPENAI_API_KEY` 等）— 由用戶在 GitHub repo settings 配置
- `playwright install` 在 CI 跑（這個依賴 P0-2 已加 `playwright-stealth`）

## Test Strategy

### 驗證 workflow 語法正確

本地用 `actionlint`（如果沒裝就 skip，不阻塞）：

```bash
actionlint .github/workflows/*.yml
```

或用 `act` 在本地 dry-run（可選，列 Open Question）。

### Workflow 行為驗證

只能在 GitHub 上實測：

1. 開一個臨時 PR（或本地用 `act`） → ci.yml 應該跑起來
2. 故意讓 ruff fail → ci.yml 應該紅
3. nightly.yml 用 `workflow_dispatch` 手動觸發測試（在 secrets 配置完後）

**這部分不能在程式碼層機械驗證**，所以 acceptance 列為「workflow 檔案語法合法」+「人工測試一輪」。

### CI 既有測試必須跑通

既有測試套件在 CI 第一次跑可能會發現：
- 測試環境有 missing fixture
- 測試在 `os.getenv` 沒設時行為不同
- 測試需要的 system package 沒裝（playwright deps）

第一次跑通可能要 fix 1-2 輪。如果發現是測試本身有 bug（不是 P0-6 引入），加開 sub-issue，不阻塞 P0-6。

## Acceptance Criteria

- [ ] `.github/workflows/ci.yml` 存在
- [ ] `.github/workflows/nightly.yml` 存在
- [ ] `.github/dependabot.yml` 存在
- [ ] `pyproject.toml` `[tool.pytest.ini_options.markers]` 含 `live`
- [ ] 用 `actionlint` 或 `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml'))"` 驗證 YAML 合法
- [ ] 推到 GitHub 後 ci.yml 跑綠（人工驗證一輪）
- [ ] commit message 描述 why（特別「之前 0 自動化 gate」）

## Rollback

- 如果 `uv sync --frozen` 在 CI 環境有問題（uv version 差異）：
  - fallback 到 `pip install -e .[dev]`
- 如果 Playwright install 太慢拖垮 CI：
  - 把 Playwright 相關 test 拆到 nightly
  - test job 改用 cache action 加速
- 如果某些既有 test 在 ubuntu-latest 失敗（macOS-only 行為）：
  - 加 `@pytest.mark.skip(condition=sys.platform != "darwin")` 並開 issue
  - 不修改 test 本體（屬 follow-up）

## Open Questions

- **Q1**：用 `uv` 還是 `pip` 作為 CI installer？
  - `uv.lock` 已存在 → 建議 `uv`
  - 但 `uv` 需要額外 install step
  - 結論：用 `uv`（參考既有 `uv.lock`）

- **Q2**：matrix 要不要跑 Python 3.11 + 3.12？
  - `pyproject.toml` 應有 `requires-python` 設定
  - 建議：先只 3.12（跟 `pyproject.toml` 對齊），broader matrix 列 P1

- **Q3**：nightly cron 時段
  - UTC 07:00 = 台灣 15:00（白天，方便看 result）
  - 也可改 UTC 19:00 = 台灣 03:00（半夜跑，早上看 result）
  - 建議：UTC 07:00（白天 fail 立即響應）

- **Q4**：要不要在 PR 加 `concurrency: cancel-in-progress`？
  - 建議：**加**，避免重複 push 浪費 CI runner

- **Q5**：是否需要 ruff 規則檢查 commit message（commitlint）？
  - 建議：**不需要**。專案 commit style 寬鬆，加 commitlint 反而摩擦

- **Q6**：workflow secrets 規劃
  - 列出需要的 secrets 給用戶（`OPENAI_API_KEY`、`EBAY_*`、`AMAZON_*` 等）
  - 在 nightly.yml 跑前提醒用戶配置
