# P0-2: Playwright Stealth + Context Reuse

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

當前 Playwright adapter 在生產環境完全無法存活：

- `chromium.launch(headless=True)` 裸跑 + UA 寫死 `VeraCrawl-browser-quality/1` → `navigator.webdriver = true`、缺 plugins / WebGL fingerprint → Cloudflare Turnstile / DataDome / PerimeterX 立即 block
- 已知 Walmart 阻擋（commit `bcc129e`）、Shopee render limitation（commit `d410379`）codebase 只是「分類記錄」、沒規避邏輯
- CAPTCHA 偵測只 `_is_access_control_page` 字串 match，偵測到只 `return None`
- `route_handler` 對非 allowlist origin 一律 `route.abort()` → CDN / image / font / JS 在不同 origin 時整頁壞掉
- `wait_until="load"` + 固定 `wait_for_timeout(250)` → SPA / lazy-load 永遠抓不到完整 DOM
- `max_runtime_ms=1000` 對 SPA 是笑話
- 每次 observe 都 launch + close browser → 記憶體洩漏 + fingerprint 重複 + 無 cookie / session 持久化

## Scope

**In scope:**

- `src/veracrawl/adapters/browser/playwright.py:63-100` — 引入 stealth、route_handler 黑名單模式、改 wait 策略
- `src/veracrawl/browser/observation.py:33` — `max_runtime_ms` 預設 1000 → 30000
- 新增：`src/veracrawl/adapters/browser/_stealth.py` — stealth patches 集中處
- 新增：`BrowserContext` reuse 機制（在 `playwright.py` 內，不破壞 port 介面）
- `pyproject.toml` — 新增 `playwright-stealth`（或 `patchright`，見 Design）

**Out of scope:**

- 真實 CAPTCHA solver 整合（2Captcha / CapSolver）— 列 P1
- Residential proxy pool 整合 — 跟 P0-1 共用 proxy 介面，不擴大
- 人類行為模擬（mouse jitter / scroll）— 列 P1
- TLS / JA3 fingerprint 處理 — 屬 HTTP layer，超出 browser scope

## Design

### Stealth library 選擇：`playwright-stealth`

**評估比較：**

| Lib | Pros | Cons | 結論 |
|-----|------|------|------|
| `playwright-stealth` | 維護穩定、API 簡單、port from `puppeteer-extra-plugin-stealth` | 部分 evasion 落後最新 detector | ✅ **採用** |
| `patchright` | 更激進的 patches、最新 evasion | API 不穩、import 路徑與官方 playwright 衝突 | ❌ 風險高 |

理由寫進 commit message。日後若 detector 演進，可在 `_stealth.py` 補手寫 patch。

### Stealth 套用點

```python
# src/veracrawl/adapters/browser/_stealth.py
from playwright_stealth import stealth_sync, Stealth

def apply_stealth(context_or_page) -> None:
    stealth_sync(context_or_page)
```

在 `PlaywrightBrowserAdapter` 建 context 後立即套用。每個 page 不重複套（context-level 即可）。

### BrowserContext Reuse

當前每次 `observe()` 都 `launch + new_context + new_page + close`。改為：

```python
class PlaywrightBrowserAdapter:
    def __init__(self, *, storage_state_path: Path | None = None, ...):
        self._playwright = None
        self._browser = None
        self._context = None
        self._storage_state_path = storage_state_path

    def _ensure_context(self) -> BrowserContext:
        if self._playwright is None:
            self._playwright = sync_playwright().start()
            self._browser = self._playwright.chromium.launch(headless=True)
            self._context = self._browser.new_context(
                user_agent=DEFAULT_CHROME_UA,
                viewport={"width": 1920, "height": 1080},
                locale="en-US",
                timezone_id="America/Los_Angeles",
                storage_state=str(self._storage_state_path)
                    if self._storage_state_path and self._storage_state_path.exists()
                    else None,
            )
            apply_stealth(self._context)
        return self._context

    def close(self) -> None:
        if self._context and self._storage_state_path:
            self._context.storage_state(path=str(self._storage_state_path))
        for resource in (self._context, self._browser, self._playwright):
            if resource is not None:
                try:
                    resource.close() if hasattr(resource, "close") else resource.stop()
                except Exception:
                    pass
        self._context = self._browser = self._playwright = None

    def __enter__(self): return self
    def __exit__(self, *args): self.close()
```

每次 `observe()` 開新 page、結束關 page，但保留 context。呼叫端用 `with` block 管理生命週期。

### Route Handler：黑名單模式

當前白名單（`route.abort()` 非 allowlist）改為黑名單：

```python
DEFAULT_BLOCK_RESOURCE_TYPES = frozenset({
    "media",      # video / audio
    "font",       # 可選
})

DEFAULT_BLOCK_DOMAIN_SUBSTRINGS = frozenset({
    "doubleclick.net",
    "googlesyndication.com",
    "google-analytics.com",
    "facebook.net",
    # ... 標準廣告 / tracker domain
})

def _route_handler(route: Route) -> None:
    req = route.request
    if req.resource_type in DEFAULT_BLOCK_RESOURCE_TYPES:
        return route.abort()
    if any(s in req.url for s in DEFAULT_BLOCK_DOMAIN_SUBSTRINGS):
        return route.abort()
    route.continue_()
```

呼叫端可注入自己的 blocklist：

```python
PlaywrightBrowserAdapter(blocked_domains=frozenset({...}), blocked_resource_types=frozenset({...}))
```

### Wait 策略

替換 `wait_until="load"` + `wait_for_timeout(250)`：

```python
def _navigate(self, page: Page, url: str, *, max_runtime_ms: int) -> None:
    page.goto(
        url,
        wait_until="domcontentloaded",
        timeout=max_runtime_ms,
    )
    # 顯式等 networkidle 或 selector，二擇一
    if self._wait_selector:
        page.wait_for_selector(self._wait_selector, timeout=max_runtime_ms)
    else:
        page.wait_for_load_state("networkidle", timeout=max_runtime_ms)
```

`_wait_selector` 從 contract / fixture 注入（例如 Amazon 等 `#productTitle`）。預設走 networkidle。

### `max_runtime_ms` 預設

`src/veracrawl/browser/observation.py:33` 預設 1000 → 30000。所有呼叫端都檢查（grep `max_runtime_ms=1000`）並對齊。

### Access-control 偵測 + escalation hook

保留現有 `_is_access_control_page` 邏輯，但偵測到時不再 silently `return None`：

```python
class AccessControlBlocked(Exception):
    """偵測到 CAPTCHA / Cloudflare / DataDome 等 access control 頁面"""
    def __init__(self, url: str, indicators: list[str]):
        self.url = url
        self.indicators = indicators
        super().__init__(f"access control at {url}: {indicators}")

# 在 observe() 結尾
if _is_access_control_page(content):
    indicators = _extract_access_control_indicators(content)
    if self._on_access_control_blocked:
        self._on_access_control_blocked(url, indicators)  # callback hook for proxy rotation / cooldown
    raise AccessControlBlocked(url=url, indicators=indicators)
```

callback 預設 `None`（仍會 raise），P1 接 escalation。

## Dependencies

| Package | Status | Justification |
|---------|--------|---------------|
| `playwright-stealth` | NEW | Headless 偵測規避；自寫 patches 易錯且難維護 |

`playwright` 已存在（從現有 import 確認）。確保版本支援 `Stealth` 物件 API（≥ 2.0）。

## Test Strategy

### 既有測試必須不破

```bash
pytest tests/adapters/browser/ tests/browser/ tests/cli/test_browser_*
```

部分 fixture 寫死 `wait_until="load"` 行為的測試需要更新預期。

### 新增 unit tests（`tests/adapters/browser/test_playwright_adapter.py`）

1. **Context reuse**：連續 3 次 `observe()` 期間，`browser.new_context` 只被呼叫一次（用 mock 計數）

2. **Storage state 持久化**：
   - 給定 `storage_state_path=tmp_path / "state.json"`
   - 第一次 observe 後 close → 檔案存在
   - 重建 adapter → context 帶入舊 cookies（檢查 `context._options.storage_state`）

3. **Blocklist 模式**：
   - blocked_domains={`tracker.example`}
   - mock route 對 `https://tracker.example/x.js` → assert `route.abort()` 被呼叫
   - mock route 對 `https://main.example/x.js` → assert `route.continue_()` 被呼叫

4. **Wait selector 注入**：
   - `wait_selector="#main"` → assert `page.wait_for_selector("#main", ...)` 被呼叫

5. **AccessControlBlocked 拋出**：
   - mock content 含 `"access denied"` → raise `AccessControlBlocked`
   - 沒設 callback → 直接 raise
   - 有設 callback → callback 先被呼叫（記錄參數），然後才 raise

6. **`max_runtime_ms=30000` 預設**：
   - 不傳 max_runtime_ms → `page.goto(timeout=30000)`

7. **Stealth 套用**：
   - `apply_stealth` 被呼叫一次（context 建立後）

### 新增 integration tests（`@pytest.mark.live`，預設 skip）

`tests/adapters/browser/test_playwright_adapter_live.py`：

```python
@pytest.mark.live
def test_navigator_webdriver_false():
    with PlaywrightBrowserAdapter() as adapter:
        result = adapter.observe("https://example.com", evaluate="() => navigator.webdriver")
        assert result.evaluation is False  # 或 undefined

@pytest.mark.live
def test_real_navigation_screenshot():
    with PlaywrightBrowserAdapter() as adapter:
        report = adapter.observe("https://example.com")
        assert report.dom_artifact_ref is not None
        assert report.screenshot_artifact_ref is not None
        assert "Example Domain" in report.body
```

### Boundary test

```bash
pytest tests/contract/test_*_import_boundaries.py
```

## Acceptance Criteria

- [ ] `pyproject.toml` 新增 `playwright-stealth`
- [ ] `src/veracrawl/adapters/browser/playwright.py` import 自 `_stealth.py`
- [ ] `grep "VeraCrawl-browser" src/veracrawl/adapters/browser/` = 0
- [ ] `grep "wait_for_timeout(250)" src/` = 0
- [ ] `grep "max_runtime_ms=1000" src/` = 0
- [ ] `src/veracrawl/browser/observation.py:33` 預設 `max_runtime_ms = 30000`
- [ ] 7 個新 unit test 全綠
- [ ] 既有 contract test 全綠
- [ ] `AccessControlBlocked` 在 `src/veracrawl/adapters/browser/` 內定義（不外洩到 ports）
- [ ] `pytest -m "not live"` 全綠
- [ ] commit message 描述 why（含 stealth lib 選擇理由）

## Rollback

- 若 `playwright-stealth` 與當前 playwright 版本不相容：
  - 改用 `patchright` 或自寫最小 stealth patches（webdriver / chrome obj / plugins / languages 四項）
- 若 context reuse 導致記憶體洩漏 / state 污染：
  - 加 `max_observations_per_context` 參數，超過自動 recreate
- 若黑名單模式破壞既有 evidence test：
  - 黑名單預設改空集合（呼叫端必須 opt-in）

## Open Questions

- **Q1**：`storage_state_path` 預設何處？`~/.veracrawl/state/<adapter>.json`？還是必須由呼叫端注入？
  - 建議：必填、由呼叫端決定（避免 adapter 自作主張寫 home dir）

- **Q2**：是否需要 per-domain context（每個 host 一個獨立 context 避免 cross-site cookie 洩漏）？
  - 建議：先 single context，列 P1 評估

- **Q3**：`AccessControlBlocked` 的 indicators 要不要分類（cloudflare / datadome / captcha / generic）？
  - 建議：先用 `list[str]` 字串集合，分類延後到 access-control 規避邏輯實作時再做
