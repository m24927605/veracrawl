# P0-1: HTTP Client（urllib → httpx）

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

當前 `StdlibHttpSourceAdapter` 是 `urllib` + 60 行皮，存在多項生產級致命問題：

- 沒有 connection pool（每 request 一條 TCP）、無 keep-alive、無 HTTP/2
- 預設 `timeout_ms=1000` — Amazon / Walmart / Shopee 動輒 3–10s 直接 timeout
- 寫死 UA `VeraCrawl-local-fixture/1` — Cloudflare / Akamai 立即 403
- `_RecordingRedirectHandler` 沒有 hop 上限、沒擋 cross-origin → SSRF / stack overflow 風險
- 完全沒有 proxy 支援（`grep proxy fetch/ adapters/` = 0）
- 沒有 retry / backoff / `Retry-After` 解析；429 直接 raise

爬蟲 reviewer 結論：**「丟到 prod 第一個禮拜就會死光」**。

## Scope

**In scope:**

- `src/veracrawl/adapters/network/stdlib_http.py` — 全檔重寫（保留檔名 + class 名以維持 hexagonal 邊界）
- `src/veracrawl/fetch/live_http.py:79` — 預設 `timeout_ms` 由 1000 → 30000（拆 connect / read 後寫進 contract）
- `src/veracrawl/fetch/network_acquisition.py:143` — 同上
- `pyproject.toml` — 新增依賴 `httpx`、`tenacity`

**Out of scope（留 P1 或之後）:**

- async / aiohttp 重構（先用 httpx 同步）
- 真實 proxy pool 整合（只開介面參數，不接後端）
- HTTP/3
- robots.txt UA 一致化（屬 P1-5）
- circuit breaker（屬 P1）

## Design

### 替換 stdlib_http.py 為 httpx

**保留的對外介面**：
- Class 名 `StdlibHttpSourceAdapter`（rename 到 `HttpxSourceAdapter` + 在 `__init__.py` 加 alias 也可，但簡單起見保留）
- 對外回傳的 `*Report` / `*Result` model 結構不動
- Port 介面（`ports/network/...`）不動

**新增的 constructor 參數**（皆有預設值）：

```python
class HttpxSourceAdapter:
    def __init__(
        self,
        *,
        connect_timeout_s: float = 10.0,
        read_timeout_s: float = 30.0,
        max_retries: int = 3,
        max_redirects: int = 5,
        user_agent: str = DEFAULT_CHROME_UA,
        proxy: str | None = None,            # 預留，None 時走直連
        verify_tls: bool = True,
    ): ...
```

**真實 Chrome UA 常數**（從 P1-5 robots UA 統一也會用到，先放此檔，後續可抽到 `contracts/`）：

```python
DEFAULT_CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
```

### Retry / Backoff

用 `tenacity` 實作：

- 可重試類別：
  - `httpx.ConnectError` / `httpx.ConnectTimeout` / `httpx.ReadTimeout`
  - HTTP `429`、`500`、`502`、`503`、`504`
- 致命類別（不 retry）：
  - 4xx 非 429（含 401 / 403 / 404 / 410）
  - SSL 錯誤
  - 已超過 `max_retries`
- 等待策略：`wait_exponential(multiplier=1, min=1, max=30)` + `wait_random(0, 1)` jitter
- `Retry-After` 解析：
  - 純數字 → 視為秒
  - HTTP-date（RFC 7231）→ `email.utils.parsedate_to_datetime` + 計算 delta
  - 解析失敗 → fallback exponential

### Redirect 控管

- httpx 預設 `follow_redirects=False`；自行迴圈處理避免 hop 失控
- 每跳檢查：
  - hop count > `max_redirects` → raise `RedirectLoopError`
  - cross-origin protocol downgrade（https → http）→ raise `ProtocolDowngradeError`
- 仍把每跳的 URL / status 記進 evidence（沿用既有 `_RecordingRedirectHandler` 的 ref 風格）

### Evidence 寫入完整化

失敗時的 evidence 必須包含：
- `status` (int)
- `response_headers` (dict, **脫敏 `Authorization`、`Cookie`、`Set-Cookie`、`Proxy-Authorization`**)
- `request_headers` (dict, 同樣脫敏)
- `final_url`
- `elapsed_ms`
- `attempt_number`

新增 helper：

```python
_SENSITIVE_HEADERS = frozenset({"authorization", "cookie", "set-cookie", "proxy-authorization"})

def _redact_headers(headers: Mapping[str, str]) -> dict[str, str]:
    return {k: ("<redacted>" if k.lower() in _SENSITIVE_HEADERS else v) for k, v in headers.items()}
```

### Proxy 介面

只開構造參數 + 傳給 httpx Client：

```python
client_kwargs = {}
if proxy:
    client_kwargs["proxies"] = proxy   # httpx 0.27+ 用 proxy=
```

不接 pool、不做 rotation。實作 `_setup_proxy_pool()` 留 P1。

## Dependencies

| Package | Status | Justification |
|---------|--------|---------------|
| `httpx` | NEW | 取代 `urllib`：connection pool / HTTP/2 / proper timeout / async-ready |
| `tenacity` | NEW | retry / backoff / jitter — 自寫易錯 |

兩個都是 well-maintained、license MIT/Apache、無 native deps。在 `pyproject.toml` 的 `[project] dependencies` 新增。

## Test Strategy

### 既有測試必須不破

```bash
pytest tests/ -k "stdlib_http or network_acquisition or live_http or source_coverage"
```

如有測試斷言 `urllib` 特定行為，更新測試對齊新行為，但不能放寬契約。

### 新增 unit tests

放在 `tests/adapters/network/test_httpx_source_adapter.py`：

1. **timeout 拆分**
   - 設 `connect_timeout_s=0.1`，目標 `10.255.255.1`（黑洞 IP）→ 0.1–0.5s 內 raise `ConnectTimeout`
   - 設 `read_timeout_s=0.1`，mock server 回 header 後睡 1s → raise `ReadTimeout`

2. **429 + Retry-After（秒）**
   - mock server 第一次回 429 + `Retry-After: 2`，第二次回 200
   - assert 第二次 request 在 first response 之後 ≥ 2.0s
   - assert `attempt_number == 2`

3. **429 + Retry-After（HTTP-date）**
   - `Retry-After: Wed, 21 Oct 2026 07:28:00 GMT`（10s 後）
   - 同上驗證等待

4. **致命 4xx 不重試**
   - mock 第一次回 403 → 立即 raise，`attempt_number == 1`
   - mock 第一次回 404 → 立即 raise，`attempt_number == 1`

5. **Redirect loop**
   - mock A → B → A → B → A → B（6 跳）
   - `max_redirects=5` → 第 6 跳 raise `RedirectLoopError`
   - 前 5 跳的 URL 都進 evidence

6. **Cross-origin downgrade 阻擋**
   - mock `https://x.test` → `http://x.test`（同 origin 但 protocol downgrade）
   - raise `ProtocolDowngradeError`

7. **Evidence 脫敏**
   - request 帶 `Authorization: Bearer secret`，response 帶 `Set-Cookie: sid=xxx`
   - 失敗時 evidence 中：
     - `request_headers["Authorization"] == "<redacted>"`
     - `response_headers["Set-Cookie"] == "<redacted>"`
     - 其他 header 原樣保留

8. **UA 注入**
   - `HttpxSourceAdapter(user_agent="MyBot/1")` → request `User-Agent` header == `MyBot/1`
   - 預設值 == `DEFAULT_CHROME_UA`

9. **Proxy 參數**
   - `HttpxSourceAdapter(proxy="http://127.0.0.1:9999")` → 目標走 proxy（用 `httpx.MockTransport` 驗證 client config）

### 新增 integration tests（`@pytest.mark.live`，預設 skip）

放在 `tests/adapters/network/test_httpx_source_adapter_live.py`：

```python
@pytest.mark.live
def test_real_chrome_ua_against_httpbin():
    adapter = HttpxSourceAdapter()
    result = adapter.fetch("https://httpbin.org/user-agent")
    assert "Chrome" in result.body
```

```python
@pytest.mark.live
def test_real_429_retry_after_against_httpbin():
    # httpbin 沒原生 429 endpoint，可用 https://httpbin.org/status/429
    ...
```

### Boundary test（既有）

```bash
pytest tests/contract/test_*_import_boundaries.py
```

確保 hexagonal 紀律不破。

## Acceptance Criteria

- [ ] `pyproject.toml` 新增 `httpx`、`tenacity` 依賴
- [ ] `src/veracrawl/adapters/network/stdlib_http.py` 不再 `import urllib`
- [ ] `grep "VeraCrawl-local-fixture\|VeraCrawl-real-benchmark\|VeraCrawl-browser-quality" src/` = 0
- [ ] 預設 connect/read timeout = 10s / 30s（檢查 `live_http.py:79` 與 `network_acquisition.py:143`）
- [ ] 9 個新 unit test 全綠
- [ ] 既有 contract test 全綠
- [ ] `pytest -m "not live"` 全綠
- [ ] `ruff check` 無新錯
- [ ] `mypy src/veracrawl/adapters/network/` 無新錯
- [ ] commit message 描述 why 而非 what

## Rollback

如發現 httpx 與 hexagonal port 介面不相容（例如 port 強制要求 sync 但 httpx 行為意外）：

1. 保留 plan 的 retry / Retry-After / redirect 邏輯
2. 把 transport layer 換回 `urllib3`（仍比 `urllib` 強，且純同步）
3. 在本檔加 `## Lessons` 章節記錄為何 httpx 不行

## Open Questions

- **Q1**：是否要支援 HTTP/2？httpx 需要 `httpx[http2]` extra 才能開。預設關閉？
  - 建議：先關，等 P1 driver 證明需要時再開

- **Q2**：Default UA 用 Mac Chrome 131 是否會被某些站當作可疑（因為 UA 太新）？
  - 建議：用 Chrome 131（2026-05 最新穩定版），有問題再回滾

- **Q3**：`HttpxSourceAdapter` 是否要 rename 為新名（避免「stdlib」誤導）？
  - 建議：rename → `HttpxSourceAdapter`，舊名保留 alias 一個 release 給呼叫端遷移

- **Q4**：proxy URL 接受 `socks5://`？
  - 需要 `httpx-socks` 額外包。建議：先只支援 `http://` / `https://`，SOCKS 列入 P1
