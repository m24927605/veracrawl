# P0-1: HTTP Client（urllib → httpx）

## Status

| | |
|---|---|
| Iteration | v2 (after codex iteration 1 feedback) |
| Started | - |
| Completed | - |
| Commits | - |
| Codex plan review | iter 1: ❌ 1 critical + 10 important + 1 minor (see STATUS.md log) |
| Codex task review | - |

## Why

`src/veracrawl/adapters/network/stdlib_http.py` 是 `urllib` 包裝，多項生產級致命問題：

- **無 connection pool** — 每 request 一條 TCP；無 keep-alive；無 HTTP/2
- **L87 timeout 單一參數**（`request.timeout_ms`，呼叫端傳 1000ms）— 對 Amazon / Walmart 動輒 3–10s 直接 timeout
- **L84 寫死 UA `VeraCrawl-local-fixture/1`** — Cloudflare / Akamai 立即 403
- **L30-61 `_RecordingRedirectHandler` 沿用 stdlib 預設**：無顯式 hop 上限、無 cross-origin policy 檢查、**無 per-hop egress / private-network 重新驗證 → SSRF 風險**
- **無 proxy 支援**（`grep proxy fetch/ adapters/network/` = 0）
- **L92-97 exception 處理**：所有失敗都 wrap 成 `ValueError`，呼叫端 (`fetch/network_acquisition.py:170`) 只 catch `ValueError`；無 retry / backoff / `Retry-After` 解析

爬蟲 reviewer 結論：**「丟到 prod 第一個禮拜就會死光」**。

對齊 docs：
- `docs/02-production-architecture.md`（網路採集層 / hexagonal 邊界）
- `docs/07-data-contracts.md`（`NetworkRequest` / `NetworkResponse` / `NetworkFailureType` 契約）
- `docs/08-build-roadmap.md`（V1 HTTP-first profile）

## Scope

**In scope:**

- `src/veracrawl/adapters/network/stdlib_http.py` — 全檔重寫（保留 class 名 `StdlibHttpSourceAdapter`、保留構造 `__init__(self, request: NetworkRequest, *, config=None)`、保留 `execute(command)` 與 `last_result` 介面）
- `src/veracrawl/contracts/network.py` — 新增 `NetworkAttemptEvidence` model（artifact 內容契約，不破既有 ref-based 結構）
- `src/veracrawl/contracts/enums.py` `NetworkFailureType` — 新增缺失的 enum value（若 grep 後發現缺）
- `src/veracrawl/fetch/network_acquisition.py:170, 186-198` — 擴展 exception → `NetworkFailureType` mapping
- `src/veracrawl/fetch/live_http.py:79`、`src/veracrawl/fetch/network_acquisition.py:143` — 預設 `timeout_ms` 由 1000 → 30000
- `pyproject.toml` — 新增 `httpx>=0.27,<1.0`、`tenacity>=9.0`、`pytest-httpserver`（test-only）

**Out of scope（明確排除以對應 codex feedback #7）：**

- `VeraCrawl-real-benchmark` UA（在 `cli/product_availability_benchmark.py:37` robots check）— 屬 P1-5（robots UA 一致化）
- `VeraCrawl-browser-quality` UA — 屬 P0-2（playwright stealth）
- HTTP/2 / async / aiohttp — 屬 P1
- 真實 proxy pool / rotation — 只開介面，不接後端
- SOCKS5 proxy — 屬 P1
- circuit breaker / global rate limiter — 屬 P1

## Design

### 1. Adapter shape — **保留現有契約**

當前簽名（codex feedback #2）：

```python
class StdlibHttpSourceAdapter:
    def __init__(self, request: NetworkRequest) -> None: ...
    @property
    def last_result(self) -> NetworkClientResult | None: ...
    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult: ...
```

13 個 call site（`grep -rn StdlibHttpSourceAdapter`）全部用 `StdlibHttpSourceAdapter(request)`。

新增 **kwarg-only** 配置（不破壞既有呼叫）：

```python
@dataclass(frozen=True)
class HttpClientConfig:
    connect_timeout_s: float = 10.0
    read_timeout_s: float = 30.0
    max_attempts: int = 3                     # 總嘗試次數（含首次）
    max_redirects: int = 5
    user_agent: str = DEFAULT_CHROME_UA
    proxy: str | None = None                  # http:// or https://；其他 scheme 拒絕
    verify_tls: bool = True
    egress_allowlist: frozenset[str] = frozenset()  # 用於 redirect 重檢
    allow_private_network: bool = False
    sensitive_header_keys: frozenset[str] = frozenset({
        "authorization", "cookie", "set-cookie", "proxy-authorization",
    })

class StdlibHttpSourceAdapter:
    def __init__(
        self,
        request: NetworkRequest,
        *,
        config: HttpClientConfig | None = None,
    ) -> None: ...
```

`request.timeout_ms` 仍保留為 fallback：呼叫端傳 30000ms 對應 `read_timeout_s=30`。`config` 不傳時用預設值（為 P0-1 落地後的內部 callers 提供）。13 個既有 call site 不需要立即遷移。

### 2. 真實 Chrome UA（含維護策略）

```python
DEFAULT_CHROME_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/<MAJOR>.0.0.0 Safari/537.36"
)
```

`<MAJOR>` 取自模組常數 `_CHROME_MAJOR_VERSION = 131`（commit message 註明維護週期：每季度 review，列入 P1-X CHROME_VERSION_BUMP backlog）。

**Acceptance 不檢查具體版本號**（codex feedback #11），只檢查：
- 不以 `VeraCrawl-` 開頭
- 符合 regex `^Mozilla/5\.0 .* Chrome/\d+\.\d+\.\d+\.\d+`

### 3. Retry / Backoff — 顯式迴圈（不依賴 tenacity decorator 行為）

針對 codex feedback #5（httpx 不會 raise 429/5xx；tenacity 不自動讀 Retry-After；max_retries 語意模糊）：

```python
def _execute_attempt(self, http_request, *, attempt: int) -> _AttemptResult:
    """執行單次 attempt。回傳 _AttemptResult；不 raise transport 例外。
    raise 只發生於：致命 4xx、redirect 違規、protocol downgrade、proxy 違規。"""
    started = monotonic()
    try:
        response = self._client.send(http_request)
    except httpx.ConnectError as e:
        return _AttemptResult.transport_error(NetworkFailureType.NETWORK_TIMEOUT, str(e), elapsed_ms=int((monotonic()-started)*1000))
    except httpx.ConnectTimeout as e:
        return _AttemptResult.transport_error(NetworkFailureType.NETWORK_TIMEOUT, str(e), ...)
    except httpx.ReadTimeout as e:
        return _AttemptResult.transport_error(NetworkFailureType.NETWORK_TIMEOUT, str(e), ...)
    except httpx.ProxyError as e:
        # proxy 失敗 — 不 retry，致命
        raise _AdapterError(NetworkFailureType.ADAPTER_FAILURE, f"proxy_failure: {type(e).__name__}") from e
    return _AttemptResult.from_response(response, elapsed_ms=...)


def _is_retryable_response(response: httpx.Response) -> bool:
    return response.status_code in {429, 500, 502, 503, 504}


def _retry_loop(self, http_request) -> httpx.Response:
    last_failure_type = NetworkFailureType.NETWORK_TIMEOUT
    for attempt in range(1, self._config.max_attempts + 1):
        result = self._execute_attempt(http_request, attempt=attempt)
        self._record_attempt_evidence(attempt, result)

        if result.is_response and not _is_retryable_response(result.response):
            return result.response  # 成功或致命 4xx 都直接回（致命 4xx 由上層分類）
        if not result.is_response:
            last_failure_type = result.failure_type

        if attempt >= self._config.max_attempts:
            break

        wait_s = self._compute_wait(result, attempt)
        sleep(wait_s)

    raise _AdapterError(last_failure_type, "retry exhausted")


def _compute_wait(self, result: _AttemptResult, attempt: int) -> float:
    # 1. 若 response 有 Retry-After，優先（cap 至 60s）
    if result.is_response:
        retry_after = _parse_retry_after(result.response.headers.get("retry-after"))
        if retry_after is not None:
            return min(retry_after, 60.0)
    # 2. fallback：exponential with jitter
    base = min(2 ** (attempt - 1), 30)
    return base + random.uniform(0, 1)


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    value = value.strip()
    # 純秒數
    if value.isdigit():
        return float(value)
    # HTTP-date
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = (dt - datetime.now(timezone.utc)).total_seconds()
        return max(delta, 0.0)
    except (TypeError, ValueError):
        return None
```

關鍵語意（codex feedback #5）：
- `max_attempts = 3` ⇒ 1 次原始 + 2 次 retry（明確命名解決 ambiguity）
- 致命 4xx（401 / 403 / 404 / 410 / 422 等）**不 retry**
- 可重試集合 = `{429, 500, 502, 503, 504}` + transport exceptions
- `Retry-After` cap 60s（避免攻擊者用 1h Retry-After 拖死）

### 4. Per-hop Redirect Policy（critical SSRF fix — codex feedback #1）

httpx `follow_redirects=False`，自行迴圈，**每跳重新跑完整 policy**：

```python
def _execute_with_redirects(self, initial_url: str) -> httpx.Response:
    current_url = initial_url
    for hop in range(self._config.max_redirects + 1):
        request = self._build_httpx_request(current_url)
        response = self._retry_loop(request)

        if not _is_redirect_status(response.status_code):
            return response

        location = response.headers.get("location")
        if not location:
            raise _AdapterError(NetworkFailureType.REDIRECT_DENIED, "redirect missing Location")

        next_url = urljoin(current_url, location)

        # Per-hop policy（重點）
        self._validate_redirect_target(from_url=current_url, to_url=next_url, hop_index=hop)

        self._record_redirect_hop(from_url=current_url, to_url=next_url, status=response.status_code, hop=hop)
        current_url = next_url

    raise _AdapterError(NetworkFailureType.REDIRECT_DENIED, f"redirect loop > {self._config.max_redirects}")


def _validate_redirect_target(self, *, from_url: str, to_url: str, hop_index: int) -> None:
    parsed_from = urlparse(from_url)
    parsed_to = urlparse(to_url)

    # 1. Protocol downgrade（HTTPS → HTTP）
    if parsed_from.scheme == "https" and parsed_to.scheme == "http":
        raise _AdapterError(NetworkFailureType.REDIRECT_DENIED, "protocol_downgrade_https_to_http")

    # 2. 必須仍是 http/https
    if parsed_to.scheme not in {"http", "https"}:
        raise _AdapterError(NetworkFailureType.REDIRECT_DENIED, f"unsupported_scheme:{parsed_to.scheme}")

    # 3. Egress allowlist（per-hop 重檢，非只看初始 URL）
    if self._config.egress_allowlist:
        target_origin = f"{parsed_to.scheme}://{parsed_to.netloc}"
        if target_origin not in self._config.egress_allowlist:
            raise _AdapterError(NetworkFailureType.EGRESS_DENIED, f"redirect_off_allowlist:{target_origin}")

    # 4. Private network / loopback / link-local（重用 fetch/network_acquisition.is_private_network_url）
    if not self._config.allow_private_network and is_private_network_url(to_url):
        raise _AdapterError(NetworkFailureType.PRIVATE_NETWORK_DENIED, f"redirect_to_private:{parsed_to.hostname}")

    # 5. DNS rebinding 緩解：解析 hostname 至 IP，再次跑 private-network 檢查
    #    （DNS rebinding 完全防禦需要 connection-time hook；P0 提供基本層保護）
    try:
        resolved = socket.gethostbyname(parsed_to.hostname or "")
        if not self._config.allow_private_network and is_private_network_url(f"{parsed_to.scheme}://{resolved}"):
            raise _AdapterError(NetworkFailureType.PRIVATE_NETWORK_DENIED, f"dns_rebind_to_private:{resolved}")
    except (socket.gaierror, ValueError):
        # DNS 解析失敗 → 由 connection-time 處理（不在 policy 階段失敗）
        pass
```

注意：DNS rebinding 防護不完整（無法防 TOCTOU），但已涵蓋常見的「公開 hostname 解析至 RFC1918 IP」攻擊。完整防護需自訂 `httpx.Transport`，列 P1。

### 5. Evidence — 走 ref-based artifact（codex feedback #3）

**不擴 `NetworkResponse` 欄位**（避免破壞既有 contract validators），改用 sidecar artifact：

```python
# contracts/network.py — 新增
class NetworkAttemptEvidence(TimestampedModel):
    """單次 HTTP attempt 的詳細 evidence，作為 artifact JSON 內容。

    寫入 artifact_ref 對應的 store；NetworkResponse 透過 attempt_evidence_artifact_refs 引用。
    """
    id: str
    request_ref: Ref
    attempt_number: int
    started_at: datetime
    elapsed_ms: int
    request_method: str
    request_url: str
    request_headers_redacted: dict[str, str]   # 已脫敏
    response_status: int | None                # transport 失敗時為 None
    response_headers_redacted: dict[str, str] | None
    failure_class: str | None                  # 例如 "httpx.ConnectTimeout"
    failure_type: str | None                   # NetworkFailureType.value，若 attempt 失敗
```

`NetworkResponse` **新增一個 optional ref list**（不破壞 PASS validator，因為 default 空 list）：

```python
class NetworkResponse(TimestampedModel):
    # ... 既有欄位不動 ...
    attempt_evidence_artifact_refs: list[Ref] = Field(default_factory=list)
```

artifact 寫入：

```python
def _record_attempt_evidence(self, attempt: int, result: _AttemptResult) -> None:
    evidence = NetworkAttemptEvidence(
        id=f"attempt-evidence:{self.request.id}:{attempt}",
        request_ref=self.request.id,
        attempt_number=attempt,
        ...
        request_headers_redacted=_redact_headers(result.request_headers, self._config.sensitive_header_keys),
        response_headers_redacted=_redact_headers(result.response_headers, ...) if result.response_headers else None,
        ...
    )
    artifact_ref = f"artifact:{self.request.id}:attempt:{attempt}:{stable_hash(evidence.model_dump_json())[:12]}"
    self._evidence_artifacts.append((artifact_ref, evidence))
```

artifact 實際寫入 store（artifact_store port）由呼叫端注入的 store 處理；adapter 只回傳 ref 列表。

```python
def _redact_headers(headers: Mapping[str, str], sensitive: frozenset[str]) -> dict[str, str]:
    return {k: ("<redacted>" if k.lower() in sensitive else v) for k, v in headers.items()}
```

### 6. Exception → NetworkFailureType mapping（codex feedback #4）

`_AdapterError(failure_type, detail)` 為內部例外，**adapter 邊界向外 raise 時**轉成 `ValueError` 子類，attaching `failure_type` 屬性：

```python
class NetworkAdapterError(ValueError):
    """Base — 所有 adapter 失敗皆 ValueError 子類，與既有 catch 相容。"""
    def __init__(self, failure_type: NetworkFailureType, detail: str):
        self.failure_type = failure_type
        self.detail = detail
        super().__init__(f"{failure_type.value}: {detail}")

class NetworkAdapterTimeoutError(NetworkAdapterError):
    """保留向後相容名稱。"""
    def __init__(self, detail: str = "network request timed out"):
        super().__init__(NetworkFailureType.NETWORK_TIMEOUT, detail)
```

`fetch/network_acquisition.py:170` 既有 `except ValueError:` 仍會 catch（向後相容）；
`fetch/network_acquisition.py:186-198` 新增 try block 包 `execute_source_acquisition`，按 `failure_type` 分類至 `NetworkFailureType`：

```python
# fetch/network_acquisition.py — execute_http_network_acquisition 內
try:
    source_outcome = execute_source_acquisition(...)
except NetworkAdapterError as e:
    return _failure_report(
        fixture_id=fixture_id, request=request,
        failure_type=e.failure_type,
        policy_decision_refs=policy_refs,
    )
except ValueError as e:
    # 非 NetworkAdapterError 的 ValueError → ADAPTER_FAILURE（保險絲）
    return _failure_report(..., failure_type=NetworkFailureType.ADAPTER_FAILURE, ...)
```

需要新增 enum value（grep 確認；缺則加）：
- `RETRY_EXHAUSTED`（若不存在則 fallback 至 `NETWORK_TIMEOUT`，由 detail 區分）

### 7. httpx Proxy API（codex feedback #6）

固定 httpx `>=0.27,<1.0`，使用 `proxy=`（單數，0.27+）：

```python
client_kwargs: dict[str, Any] = {
    "timeout": httpx.Timeout(
        connect=self._config.connect_timeout_s,
        read=self._config.read_timeout_s,
        write=self._config.read_timeout_s,
        pool=self._config.connect_timeout_s,
    ),
    "verify": self._config.verify_tls,
    "follow_redirects": False,
    "headers": {"User-Agent": self._config.user_agent},
}
if self._config.proxy is not None:
    parsed = urlparse(self._config.proxy)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError(f"unsupported proxy scheme: {parsed.scheme} (only http/https)")
    client_kwargs["proxy"] = self._config.proxy

self._client = httpx.Client(**client_kwargs)
```

## Dependencies

| Package | Version | Status | Justification |
|---------|---------|--------|---------------|
| `httpx` | `>=0.27,<1.0` | NEW | 取代 `urllib`：connection pool / proper timeout 拆分 / proxy API；版本 pin 對齊 `proxy=` 介面 |
| `tenacity` | `>=9.0` | NEW | 提供 `wait_exponential` / jitter helpers；retry 主迴圈仍自寫，tenacity 僅做 jitter / wait helpers（避免 codex feedback #5 的 decorator 行為陷阱）|
| `pytest-httpserver` | latest | NEW (test only) | 取代 httpbin 依賴；可控 429 → 200 序列、可控 redirect chain；deterministic |

均為 well-maintained、license MIT/Apache、無 native deps。

## Test Strategy

### 既有測試必須不破

```bash
pytest tests/ -k "stdlib_http or network_acquisition or live_http or source_coverage or contract"
```

需更新預期的測試（fixture 假設 `urllib` 行為）：列出後逐一更新測試假設、不放寬契約。

### 新增 unit tests（`tests/adapters/network/test_httpx_source_adapter.py`）

全部用 `httpx.MockTransport` 或 `pytest-httpserver`，**無外部網路依賴**（codex feedback #9）：

1. **timeout 拆分**
   - `MockTransport` 模擬 connect 永不回（`httpx.ConnectTimeout`） → `attempt_evidence.failure_class == "httpx.ConnectTimeout"`
   - `MockTransport` 回 header 後 sleep > read_timeout → `httpx.ReadTimeout`

2. **429 + Retry-After（純秒）**
   - `pytest-httpserver` 第一次 `/test` 回 429 + `Retry-After: 2`，第二次 `/test` 回 200
   - 等待 ≥ 2.0s 後第二次成功；`attempt_evidence` 共 2 筆

3. **429 + Retry-After（HTTP-date）relative time**
   - 動態計算 HTTP-date：`(datetime.now(timezone.utc) + timedelta(seconds=2)).strftime("%a, %d %b %Y %H:%M:%S GMT")`
   - 驗證等待約 2s（codex feedback #11）

4. **Retry-After cap 60s**
   - 設 `Retry-After: 3600` → 實際等待 ≤ 60s

5. **致命 4xx 不重試**
   - 第一次回 403 → 立即由 `execute()` 透過 contract 邏輯回對應結果；evidence 只 1 筆 attempt

6. **可重試集合 5xx**
   - 第一次 500 → retry → 第二次 200 → 成功

7. **Redirect loop 上限**
   - `pytest-httpserver` `/a → /b → /a → /b → /a → /b → /a`（6 跳）
   - `max_redirects=5` → raise `NetworkAdapterError(REDIRECT_DENIED, "redirect loop > 5")`
   - 前 5 個 redirect_hop 都進 evidence

8. **Cross-origin protocol downgrade 阻擋**
   - `MockTransport` 對 `https://a.example/x` 回 302 `Location: http://a.example/x`
   - raise `NetworkAdapterError(REDIRECT_DENIED, "protocol_downgrade_...")`

9. **Per-hop egress allowlist**
   - allowlist = `{"https://a.example"}`
   - `/x` 回 302 `Location: https://b.example/y`
   - raise `NetworkAdapterError(EGRESS_DENIED, ...)`

10. **Per-hop private network block**
    - `/x` 回 302 `Location: http://127.0.0.1/admin`
    - raise `NetworkAdapterError(PRIVATE_NETWORK_DENIED, ...)`

11. **Evidence 脫敏**
    - request 帶 `Authorization: Bearer secret`，response 帶 `Set-Cookie: sid=xxx`
    - assert `attempt_evidence.request_headers_redacted["Authorization"] == "<redacted>"`
    - assert `attempt_evidence.response_headers_redacted["Set-Cookie"] == "<redacted>"`
    - 其他 header 原樣保留

12. **UA 注入 + 預設**
    - 不傳 config → request `User-Agent` 不以 `VeraCrawl-` 開頭、符合 Chrome regex
    - 傳 `config=HttpClientConfig(user_agent="MyBot/1")` → header `User-Agent == "MyBot/1"`

13. **Proxy scheme 驗證**
    - `HttpClientConfig(proxy="socks5://127.0.0.1:1080")` → `__init__` raise `ValueError`
    - `proxy="http://127.0.0.1:9999"` → 通過，httpx Client config 含 `proxy` key

14. **Failure type mapping**
    - 觸發每種 failure 路徑，assert `e.failure_type` 對應的 `NetworkFailureType` 值

15. **Backwards compat: 既有 callers**
    - `StdlibHttpSourceAdapter(request)` 不傳 config → 應 work，行為使用 default config（除了預設 timeout 由 request.timeout_ms 覆蓋）

### 新增 integration tests（`@pytest.mark.live`，預設 skip）

`tests/adapters/network/test_httpx_source_adapter_live.py`：

```python
@pytest.mark.live
def test_real_chrome_ua_against_httpbin():
    """驗證真實環境下 UA 不被視為 bot（example.com / httpbin.org/headers）。"""
    request = build_network_request(target_url="https://httpbin.org/headers", ...)
    adapter = StdlibHttpSourceAdapter(request)
    adapter.execute(_source_command_for_network(request))
    body = json.loads(adapter.last_result.body_text)
    assert "Chrome" in body["headers"]["User-Agent"]
    assert "VeraCrawl" not in body["headers"]["User-Agent"]

@pytest.mark.live
def test_real_redirect_recording():
    """httpbin.org/redirect-to?url=... 真實 redirect 路徑能被 record。"""
    ...

# NOTE: 不再用 httpbin.org/status/429 測 retry-to-200（codex feedback #10）：
# httpbin 的 429 endpoint 永遠回 429。retry 行為已在 unit test 用 pytest-httpserver 驗證完整。
```

### Boundary test（既有 + 新增）

```bash
pytest tests/contract/test_*_import_boundaries.py
```

## Acceptance Criteria

- [ ] `pyproject.toml` 含 `httpx>=0.27,<1.0`、`tenacity>=9.0`、`pytest-httpserver`（dev / test）
- [ ] `src/veracrawl/adapters/network/stdlib_http.py` 不再 `import urllib.request` / `urllib.error`
- [ ] `grep "VeraCrawl-local-fixture" src/veracrawl/adapters/network/` = 0（**僅檢查 P0-1 scope 的 UA**；codex feedback #7）
- [ ] `src/veracrawl/adapters/network/stdlib_http.py` 預設 UA 通過 regex `^Mozilla/5\.0 .* Chrome/\d+\.\d+\.\d+\.\d+`
- [ ] 13 個既有 call site 不需修改（通過既有 contract test 驗證）
- [ ] 預設 connect/read timeout = 10s / 30s（檢查 `HttpClientConfig.connect_timeout_s` / `read_timeout_s`）
- [ ] `live_http.py:79` 與 `network_acquisition.py:143` 預設 `timeout_ms` ≥ 30000
- [ ] `contracts/network.py` 含 `NetworkAttemptEvidence` model
- [ ] `contracts/network.py` 的 `NetworkResponse.attempt_evidence_artifact_refs` 為 optional list
- [ ] 15 個新 unit test 全綠
- [ ] 既有 contract test 全綠
- [ ] `pytest -m "not live"` 全綠
- [ ] `ruff check` 無新錯
- [ ] `mypy src/veracrawl/adapters/network/` 無新錯
- [ ] commit message 描述 why（含 codex feedback 對應的設計決策）

## Rollback

- 若 httpx `proxy=` 在某些 macOS / linux 環境不一致：
  - pin httpx 至已驗證的具體版本（如 `>=0.27.2,<0.28`）
- 若 `pytest-httpserver` 與 fixture 互動有問題：
  - fallback `httpx.MockTransport` 自寫 transport scenarios
- 若 `NetworkAttemptEvidence` 加入 `NetworkResponse.attempt_evidence_artifact_refs` 觸發既有 PASS validator 嚴格檢查：
  - 改用獨立 `NetworkAttemptEvidenceReport` 並透過 `NetworkAcquisitionReport.failure_report_refs` 引用（仍 ref-based，不破壞既有 model）
- 若 per-hop allowlist policy 與 `network_policy_failure` 既有邏輯重複：
  - 抽 helper `validate_url_against_policy(url, *, allowlist, allow_private)` 兩處共用

## Open Questions

- **Q1**：HTTP/2 是否要支援？
  - codex feedback #12 指出 motivation 與 dependencies 矛盾
  - **決定**：移除 HTTP/2 自 motivation；P0 不做。**Acceptance 不提**
  - P1 評估時加 `httpx[http2]` extra

- **Q2**：DNS rebinding 完整防護
  - 當前 design 在 redirect policy 內做 DNS resolve，仍有 TOCTOU
  - 完整防禦需自訂 `httpx.Transport` 在連線層擋
  - **決定**：P0 提供基本層（resolve + 重檢），完整 transport-level 列 P1

- **Q3**：`NetworkAttemptEvidence` 的 `request_method` 是否要全 enum？
  - 目前 `NetworkRequest.method` 已限制為 `{"GET", "HEAD"}`
  - **決定**：用 `str` 即可，evidence 不重複契約限制

- **Q4**：13 個 call site 是否在本 P0 內遷移為 config-aware？
  - **決定**：不遷移。P0-1 只保證向後相容；call site 遷移列為 P0-1 後續 follow-up（仍 P0 範圍但獨立 commit）

- **Q5**：`max_attempts` 預設值
  - 當前 design `max_attempts=3`（1 原始 + 2 retry）
  - 對 e-commerce 可能需要 5（特別 Cloudflare 需要 warm-up）
  - **決定**：預設 3，呼叫端可注入；保守起點，避免拖長 P95 latency

- **Q6**：`Retry-After` cap 60s 是否合理？
  - 過短會違反站點意圖；過長會被 DOS
  - **決定**：60s 足夠涵蓋常見 throttle window，極端 case 由呼叫端 catch + 自決定 cooldown
