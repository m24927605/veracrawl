# P0-1: HTTP Client（urllib → httpx）

## Status

| | |
|---|---|
| Iteration | v3 (after codex iterations 1, 2 feedback) |
| Started | - |
| Completed | - |
| Commits | - |
| Codex plan review | iter 1 ❌, iter 2 ❌ (see STATUS.md log) |
| Codex task review | - |

## Why

`src/veracrawl/adapters/network/stdlib_http.py` 是 `urllib` 包裝，多項生產級致命問題：

- **無 connection pool / 無 keep-alive**
- **L87 timeout 單一參數**（呼叫端傳 1000ms）— 對 e-commerce 站點動輒 3–10s 直接 timeout
- **L84 寫死 UA `VeraCrawl-local-fixture/1`** — Cloudflare / Akamai 立即 403
- **L30-61 redirect handler 沿用 stdlib 預設** — 無 hop 上限、**無 per-hop egress / private-network 重新驗證 → SSRF 風險**
- **無 proxy 支援**
- **L92-97 exception 處理**：所有失敗 wrap 成 `ValueError`，呼叫端 (`fetch/network_acquisition.py:170`) 只 catch `ValueError`；無 retry / backoff / `Retry-After` 解析
- **無 size budget enforcement**：當前讀完整 body 後才檢查 size，記憶體與 abuse 風險

對齊 docs：
- `docs/02-production-architecture.md`（網路採集層 / hexagonal 邊界）
- `docs/07-data-contracts.md`（`NetworkRequest` / `NetworkResponse` / `NetworkFailureType` 契約）
- `docs/08-build-roadmap.md`（V1 HTTP-first profile）

爬蟲 reviewer 結論：**「丟到 prod 第一個禮拜就會死光」**。

## Scope

**In scope:**

- `src/veracrawl/adapters/network/stdlib_http.py` — 全檔重寫；保留現有公開介面（class 名 `StdlibHttpSourceAdapter`、構造 `__init__(self, request, *, config=None, transport=None, sleep_fn=time.sleep, clock_fn=time.monotonic)`、`execute(command)` 與 `last_result`）
- `src/veracrawl/contracts/network.py`：
  - 新增 `NetworkAttemptEvidence` model（inline，作為 list 元素，非 ref）
  - **不擴 `NetworkRequest` / `NetworkResponse` 必填欄位**（避免破 PASS validators）；只在 `NetworkClientResult` 加 `attempt_evidences: list[NetworkAttemptEvidence]`
- `src/veracrawl/contracts/enums.py` `NetworkFailureType`：
  - 新增 `RETRY_EXHAUSTED`（codex iter-2 critical#3 / important#6）
- `src/veracrawl/ports/network.py`：
  - `NetworkClientResult` dataclass 新增 `attempt_evidences: list[NetworkAttemptEvidence]` field（dataclass 加 default `field(default_factory=list)`）
- `src/veracrawl/fetch/network_acquisition.py`：
  - 新增 factory `build_http_adapter_for_acquisition(request, *, egress_allowlist, allow_private_network, transport=None, sleep_fn=time.sleep)`
  - `execute_http_network_acquisition` 改用 factory；保留所有現有參數
  - 改寫 line 167-184 的 try/except：分流 `NetworkAdapterError`（依其 `failure_type` 直接成 `_failure_report`）vs 其他 `ValueError`（仍走 `ADAPTER_FAILURE`）
- `src/veracrawl/fetch/acquisition.py` `execute_source_acquisition`（codex iter-2 critical#1）：
  - 修改 try/except，**不吞** `NetworkAdapterError`（讓它穿透回 `execute_http_network_acquisition`，由那裡分類）；其他 `ValueError` 維持當前行為
- `src/veracrawl/fetch/live_http.py:79`、`network_acquisition.py:143` — 預設 `timeout_ms` 由 1000 → 30000
- `pyproject.toml` — 新增 `httpx>=0.27,<1.0`、`pytest-httpserver`（test only）；**不加 tenacity**（codex iter-2 minor#12）

**Out of scope（明確排除）:**

- 13 個既有 `StdlibHttpSourceAdapter(request)` call site（CLI / test）的 SSRF 加固 — 仍走 default-empty allowlist；屬 P1 後續遷移（**唯獨經由 `execute_http_network_acquisition` 路徑享 P0-1 SSRF 保護**）
- `VeraCrawl-real-benchmark` UA（屬 P1-5 robots UA 一致化）
- `VeraCrawl-browser-quality` UA（屬 P0-2）
- HTTP/2 / async / aiohttp（**自 motivation 移除**；P1）
- 真實 proxy pool / rotation
- SOCKS5 proxy
- circuit breaker / global rate limiter
- 完整 DNS-rebinding transport-level 防護（P0 提供基本 resolve-time 檢查；transport-level 列 P1）
- 4xx → `NetworkFailureType` 的應用層分類（**設計決策：P0-1 將 4xx 視為成功 HTTP 採集**，status 寫進 `NetworkResponse.status_code` 由上游分類；見 §3）
- artifact store 注入（evidence 走 inline list；persistent store 列 P1）

## Design

### 1. Adapter shape — **保留現有契約 + 注入 testability seam**

```python
@dataclass(frozen=True)
class HttpClientConfig:
    connect_timeout_s: float = 10.0
    read_timeout_s: float = 30.0
    max_attempts: int = 3                          # 總嘗試數（含首次）
    max_redirects: int = 5
    user_agent: str = DEFAULT_CHROME_UA
    proxy: str | None = None                       # http:// or https://
    verify_tls: bool = True
    egress_allowlist: frozenset[str] = frozenset() # ["https://x.example", ...]
    allow_private_network: bool = False
    sensitive_header_keys: frozenset[str] = frozenset({
        "authorization", "cookie", "set-cookie", "proxy-authorization",
    })
    retry_after_cap_s: float = 60.0


class StdlibHttpSourceAdapter:
    """保留 class 名稱（內部換 httpx 實作）。"""

    def __init__(
        self,
        request: NetworkRequest,
        *,
        config: HttpClientConfig | None = None,
        transport: httpx.BaseTransport | None = None,    # codex iter-2 important#7
        sleep_fn: Callable[[float], None] = time.sleep,  # codex iter-2 important#8
        clock_fn: Callable[[], float] = time.monotonic,
    ) -> None:
        self.request = request
        self._config = config or _default_config_from_request(request)
        self._sleep = sleep_fn
        self._clock = clock_fn
        self._client = self._build_client(transport)
        self._last_result: NetworkClientResult | None = None
        self._attempt_evidences: list[NetworkAttemptEvidence] = []
        self._redirect_hops: list[RedirectHop] = []

    @property
    def last_result(self) -> NetworkClientResult | None:
        return self._last_result

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        ...   # 失敗時仍 populate _last_result 部分內容（codex iter-2 important#5）
```

#### 1.1 Timeout 優先序（codex iter-2 important#9）

**規則**：`config` 若由呼叫端注入即為 canonical；不再用 `request.timeout_ms` 作 fallback。

當 `config=None` 時 `_default_config_from_request(request)` 從 `request` 構造一個 default config：
- `connect_timeout_s = 10.0`
- `read_timeout_s = max(min(request.timeout_ms / 1000, 60.0), 1.0)`（夾在 [1, 60]）
- 其他欄位走 `HttpClientConfig` 預設

`request.timeout_ms` **不再**對顯式 `config` 生效。Acceptance 寫死「config 顯式注入時，request.timeout_ms 被忽略」。

### 2. UA — 真實 Chrome（含維護策略）

```python
_CHROME_MAJOR = 131  # review quarterly; track in P1 backlog as "CHROME_VERSION_BUMP"

DEFAULT_CHROME_UA = (
    f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    f"AppleWebKit/537.36 (KHTML, like Gecko) "
    f"Chrome/{_CHROME_MAJOR}.0.0.0 Safari/537.36"
)
```

Acceptance 用 regex `^Mozilla/5\.0 .* Chrome/\d+\.\d+\.\d+\.\d+`（不寫死版本號）。

### 3. 4xx 處理決策（**回應 codex iter-2 critical#3**）

**設計決策：4xx 不在 adapter 層映射為 `NetworkFailureType`。**

- 401 / 403 / 404 / 410 / 422 等 → 直接 return `httpx.Response` → adapter 將 status_code 寫進 `NetworkResponse.status_code` → 視為「成功 HTTP 採集」
- 既有 `NetworkResponse` validator 對 status_code 200-399 才強制要求 `raw_artifact_ref / content_digest / content_type`；4xx/5xx 終態進來時 **若 retry 已耗盡** 仍當「採集 attempt 完成」回應，由上游應用層（policy / agent decision）決定如何分類
- **5xx 終態 retry 耗盡** → `NetworkAdapterError(RETRY_EXHAUSTED, "5xx_unrecoverable:status=503")` raise 出去
- **4xx 非 429** → 第一次出現即終止 retry 但 **仍回正常 response**（呼叫端拿到 status_code 自決定）

理由：
1. HTTP semantics 上 4xx 是 valid response，body 仍可能含結構化 error
2. 既有 `NetworkResponse` 對 4xx/5xx 已允許無 raw_artifact（見 `contracts/network.py:88-90`）
3. 應用層分類（404 → NOT_FOUND policy / 401 → AUTH_FAILED policy）已是其他模組責任

| HTTP 狀態 | 行為 | adapter raise? |
|---|---|---|
| 2xx | 回 response | 否 |
| 3xx | 進 redirect 處理（§4） | redirect 違規時 raise `REDIRECT_DENIED` |
| 401/403/404/410/422 等致命 4xx | 回 response（status 帶出去） | 否 |
| 429 | retry（§5） | retry 耗盡 raise `RETRY_EXHAUSTED` |
| 500/502/503/504 | retry（§5） | retry 耗盡 raise `RETRY_EXHAUSTED` |
| 其他 5xx（501、505 等） | 不 retry，回 response | 否 |

### 4. Per-hop Redirect Policy（critical SSRF fix）

httpx `follow_redirects=False`，自行迴圈，每跳重跑完整 policy + DNS resolve。詳見前一版 §4，以下是修訂：

- `_validate_redirect_target` 失敗時：
  - **先** populate `self._last_result = _partial_result(...)` 帶上目前累積的 `redirect_hops` 與 `attempt_evidences`（codex iter-2 important#5）
  - **再** raise `NetworkAdapterError`
- `egress_allowlist` 從 `self._config` 讀（factory 注入；見 §7）
- redirect target 自身的 attempt_evidence 也記入（一個 hop 對應 ≥ 1 個 attempt）

### 5. Retry / Backoff — 顯式迴圈（**移除 tenacity**）

```python
def _retry_loop(self, http_request) -> httpx.Response:
    last_failure_type: NetworkFailureType | None = None  # codex iter-2 important#6

    for attempt in range(1, self._config.max_attempts + 1):
        evidence = self._begin_attempt(attempt, http_request)
        try:
            response = self._client.send(http_request, follow_redirects=False)
        except httpx.HTTPError as exc:
            failure = _classify_transport_error(exc)        # §10 mapping
            self._end_attempt(evidence, failure_type=failure, exc_class=type(exc).__name__)
            if not _is_retryable_failure(failure):
                raise NetworkAdapterError(failure, f"{type(exc).__name__}: {exc}") from exc
            last_failure_type = failure
        else:
            self._end_attempt(evidence, response=response)
            if not _is_retryable_response(response):
                return response
            last_failure_type = _failure_for_status(response.status_code)

        if attempt >= self._config.max_attempts:
            break

        wait_s = self._compute_wait(
            response if 'response' in locals() else None,
            attempt,
        )
        self._sleep(wait_s)

    raise NetworkAdapterError(
        NetworkFailureType.RETRY_EXHAUSTED,
        f"max_attempts={self._config.max_attempts} last_failure={last_failure_type}",
    )


def _is_retryable_response(r: httpx.Response) -> bool:
    return r.status_code in {429, 500, 502, 503, 504}

def _is_retryable_failure(ft: NetworkFailureType) -> bool:
    return ft == NetworkFailureType.NETWORK_TIMEOUT

def _failure_for_status(status: int) -> NetworkFailureType:
    return NetworkFailureType.RATE_BUDGET_EXCEEDED if status == 429 else NetworkFailureType.RETRY_EXHAUSTED


def _compute_wait(self, response: httpx.Response | None, attempt: int) -> float:
    """Pure function（已 inject clock；不直接呼叫 time）。可在 unit test 直接驗。"""
    if response is not None:
        retry_after = _parse_retry_after(response.headers.get("retry-after"), self._clock)
        if retry_after is not None:
            return min(retry_after, self._config.retry_after_cap_s)
    base = min(2 ** (attempt - 1), 30.0)
    return base + random.uniform(0, 1)


def _parse_retry_after(value: str | None, clock_fn: Callable[[], float]) -> float | None:
    """clock_fn 用於測試決定論；prod 用 time.monotonic。HTTP-date 用 datetime.now(utc) 仍合理。"""
    ...
```

語意：
- `max_attempts = 3` ⇒ 1 原始 + 2 retry
- transport timeout 可重試；transport 其他錯誤（DNS / refused / TLS / proxy）**不可重試** → 立即 raise
- retryable 5xx / 429 retry 至 `max_attempts` 後 raise `RETRY_EXHAUSTED`
- `Retry-After` cap 由 config 控（預設 60s）
- `_compute_wait` 為 pure function，**測試直接驗**（codex iter-2 important#8 → 不需 sleep 2s 這種 flaky test）

### 6. Evidence — inline，**不需 artifact store 注入**（codex iter-2 important#4）

```python
# contracts/network.py — 新增
class NetworkAttemptEvidence(BaseModel):
    """單次 HTTP attempt 的詳細證據。inline 帶在 NetworkClientResult 內。"""
    attempt_number: int
    started_at: datetime
    elapsed_ms: int
    request_method: str
    request_url: str
    request_headers_redacted: dict[str, str]
    response_status: int | None
    response_headers_redacted: dict[str, str] | None
    failure_class: str | None         # exception class name（transport 錯誤時）
    failure_type: str | None          # NetworkFailureType.value
```

```python
# ports/network.py — 修改 dataclass
@dataclass(frozen=True)
class NetworkClientResult:
    response: NetworkResponse
    redirect_hops: list[RedirectHop]
    body_text: str
    artifact_refs: list[Ref]
    attempt_evidences: list[NetworkAttemptEvidence] = field(default_factory=list)
```

`artifact_refs[0]` 仍是 raw artifact（呼叫端假設不變）。`attempt_evidences` 為 inline list，後續 P1 可改為 ref-backed。

### 7. egress_allowlist 接線（codex iter-2 critical#2）

新增 factory：

```python
# fetch/network_acquisition.py
def build_http_adapter_for_acquisition(
    request: NetworkRequest,
    *,
    egress_allowlist: list[str],
    allow_private_network: bool,
    transport: httpx.BaseTransport | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
    clock_fn: Callable[[], float] = time.monotonic,
) -> StdlibHttpSourceAdapter:
    config = _default_config_from_request(request)
    config = replace(
        config,
        egress_allowlist=frozenset(egress_allowlist),
        allow_private_network=allow_private_network,
    )
    return StdlibHttpSourceAdapter(
        request,
        config=config,
        transport=transport,
        sleep_fn=sleep_fn,
        clock_fn=clock_fn,
    )
```

`execute_http_network_acquisition` 改用 factory（注入 allowlist），既有 13 call sites 不改（保留 default-empty allowlist；列 P1 遷移）。

### 8. Failure Mapping（codex iter-2 critical#1）

修改 `fetch/acquisition.py:execute_source_acquisition`，**不吞** `NetworkAdapterError`：

```python
# fetch/acquisition.py — 修改 try/except
try:
    result = adapter.execute(command)
except NetworkAdapterError:
    raise  # 穿透回上層
except ValueError as exc:
    # 維持當前 ADAPTER_FAILURE / mismatch 行為
    ...
```

`fetch/network_acquisition.py:execute_http_network_acquisition` 在 `execute_source_acquisition()` 外層加 try/except：

```python
try:
    source_outcome = execute_source_acquisition(...)
except NetworkAdapterError as exc:
    # 部分結果可從 adapter.last_result 取（partial failure evidence）
    return _failure_report(
        fixture_id=fixture_id,
        request=request,
        failure_type=exc.failure_type,
        policy_decision_refs=policy_refs,
    )
```

### 9. Size Budget Enforcement（codex iter-2 important#10）

httpx streaming：

```python
def _read_body(self, response: httpx.Response, *, max_bytes: int) -> bytes:
    chunks = []
    total = 0
    for chunk in response.iter_bytes(chunk_size=8192):
        total += len(chunk)
        if total > max_bytes:
            response.close()
            raise NetworkAdapterError(
                NetworkFailureType.SIZE_BUDGET_EXCEEDED,
                f"body > {max_bytes} bytes",
            )
        chunks.append(chunk)
    return b"".join(chunks)
```

`max_bytes = self.request.size_budget_bytes`。

### 10. Exception Mapping Table（codex iter-2 important#11）

```python
def _classify_transport_error(exc: httpx.HTTPError) -> NetworkFailureType:
    if isinstance(exc, (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout)):
        return NetworkFailureType.NETWORK_TIMEOUT
    if isinstance(exc, httpx.ProxyError):
        return NetworkFailureType.ADAPTER_FAILURE          # detail="proxy_error"
    if isinstance(exc, httpx.ConnectError):
        return NetworkFailureType.ADAPTER_FAILURE          # detail="connect_failed"（含 DNS / refused）
    if isinstance(exc, httpx.RemoteProtocolError):
        return NetworkFailureType.ADAPTER_FAILURE          # detail="remote_protocol"
    # ssl.SSLError 通常被 httpx 包成 ConnectError；fallback
    return NetworkFailureType.ADAPTER_FAILURE
```

設計取捨：DNS / refused / TLS 共享 `ADAPTER_FAILURE`，由 `detail` 字串區分（避免 enum 爆炸）。Acceptance test 驗 `e.detail` 含關鍵字。**未來** P1 視需要拆 enum。

### 11. httpx Client 構造

```python
def _build_client(self, transport: httpx.BaseTransport | None) -> httpx.Client:
    timeout = httpx.Timeout(
        connect=self._config.connect_timeout_s,
        read=self._config.read_timeout_s,
        write=self._config.read_timeout_s,
        pool=self._config.connect_timeout_s,
    )
    kwargs: dict[str, Any] = {
        "timeout": timeout,
        "verify": self._config.verify_tls,
        "follow_redirects": False,
        "headers": {"User-Agent": self._config.user_agent},
    }
    if self._config.proxy is not None:
        parsed = urlparse(self._config.proxy)
        if parsed.scheme not in {"http", "https"}:
            raise ValueError(f"unsupported proxy scheme: {parsed.scheme}")
        kwargs["proxy"] = self._config.proxy
    if transport is not None:
        kwargs["transport"] = transport
    return httpx.Client(**kwargs)
```

## Dependencies

| Package | Version | Status | Justification |
|---------|---------|--------|---------------|
| `httpx` | `>=0.27,<1.0` | NEW | 取代 `urllib`：connection pool / proper timeout 拆分 / `proxy=` API / streaming |
| `pytest-httpserver` | latest | NEW (test only) | deterministic 429→200 / redirect chain；取代 httpbin / 黑洞 IP |

**~~tenacity~~ 移除**（codex iter-2 minor#12）：retry 主迴圈自寫，jitter 用 stdlib `random.uniform`。

## Test Strategy

### 既有測試必須不破

```bash
pytest tests/ -k "stdlib_http or network_acquisition or live_http or source_coverage or contract"
```

### 新增 unit tests（`tests/adapters/network/test_httpx_source_adapter.py`）

全部用 `httpx.MockTransport`（注入點：constructor `transport=`），**或** `pytest-httpserver`，**全無外部網路依賴 / 無真實 sleep**。

#### Pure function tests（無 transport 需求）
1. **`_compute_wait` 表驗**：直接 call，驗 `Retry-After: 5` → 5.0；`Retry-After: 3600` → cap 至 60；無 header 時 attempt=1 → ∈ [1,2]，attempt=4 → ∈ [8,9]
2. **`_parse_retry_after` 表驗**：純秒、HTTP-date（用 `datetime.now(utc) + 2s`）、垃圾字串、None
3. **`_classify_transport_error`**：每個 httpx exception class 對應正確 NetworkFailureType
4. **`_is_retryable_response`** / **`_is_retryable_failure`**：boundary（429 yes、403 no、500 yes、501 no）
5. **`_failure_for_status`**：429 → RATE_BUDGET_EXCEEDED；503 → RETRY_EXHAUSTED

#### Behavior tests（用 MockTransport）

6. **timeout 拆分（mock）**：MockTransport raise `httpx.ConnectTimeout` → adapter retry → max_attempts 後 raise `NetworkAdapterError(NETWORK_TIMEOUT)`；assert `mock_sleep.call_count == max_attempts - 1`
7. **read timeout**：MockTransport raise `httpx.ReadTimeout` → 同上
8. **致命 transport**：MockTransport raise `httpx.ConnectError("connection refused")` → 立即 raise（無 retry），`failure_type == ADAPTER_FAILURE`，`detail` 含 "connect"
9. **TLS 錯誤**：raise `httpx.ConnectError` containing SSL → ADAPTER_FAILURE
10. **Proxy 錯誤**：raise `httpx.ProxyError` → ADAPTER_FAILURE，detail 含 "proxy"
11. **429 + Retry-After（純秒）**：
    - MockTransport 第一回 429 + `Retry-After: 2`；第二回 200
    - `mock_sleep` 收到 2.0；第二次 send 之後成功
    - `attempt_evidences` 共 2 筆
12. **429 + Retry-After（HTTP-date）**：動態算 `(datetime.now(utc) + 2s).strftime(...)` → mock_sleep ≈ 2.0
13. **Retry-After cap**：`Retry-After: 3600` → mock_sleep == 60.0
14. **致命 4xx 不 retry，回 response**（codex iter-2 critical#3）：MockTransport 第一回 403 → execute() 完成；`last_result.response.status_code == 403`；body 仍記錄；無 raise
15. **可重試 5xx 耗盡**：MockTransport 連續 3 次 500 → raise `NetworkAdapterError(RETRY_EXHAUSTED)`；attempt_evidences 共 3 筆
16. **Redirect loop**：pytest-httpserver `/a → /b → /a → /b → /a → /b → /a`；max_redirects=5 → raise `REDIRECT_DENIED`；`last_result.redirect_hops` 有 5 hops（partial result，codex iter-2 important#5）
17. **Protocol downgrade**：MockTransport `https` → `http` location → raise `REDIRECT_DENIED`，detail "protocol_downgrade"
18. **Per-hop egress allowlist**：config.egress_allowlist={`https://a.example`}；redirect 至 `https://b.example` → raise `EGRESS_DENIED`
19. **Per-hop private network**：redirect 至 `http://127.0.0.1` → raise `PRIVATE_NETWORK_DENIED`
20. **DNS rebinding**：mock `socket.gethostbyname` 回 `10.0.0.1`，目標 `https://attacker.example` → raise `PRIVATE_NETWORK_DENIED`
21. **Size budget**：MockTransport 回 200 + body 100KB；request.size_budget_bytes=8192 → raise `SIZE_BUDGET_EXCEEDED`；assert body 在第 ~9KB 處中斷（streaming）
22. **Evidence 脫敏**：request 帶 `Authorization: Bearer secret`、response `Set-Cookie: sid=x` → evidence headers 對應 key 為 `<redacted>`，其他不動
23. **UA 預設**：不傳 config → request `User-Agent` 通過 regex `^Mozilla/5\.0 .* Chrome/\d+\.\d+\.\d+\.\d+`、不以 `VeraCrawl-` 開頭
24. **UA 注入**：`config=HttpClientConfig(user_agent="MyBot/1")` → header `User-Agent == "MyBot/1"`
25. **Proxy scheme 拒絕**：`config.proxy="socks5://..."` → `__init__` raise `ValueError`
26. **Proxy http 通過**：`config.proxy="http://127.0.0.1:9999"` → 構造成功（用 transport 攔截，不真連）
27. **Backwards compat**：`StdlibHttpSourceAdapter(request)` 無 config → 預設 config，`config.egress_allowlist` 為空 frozenset（13 既有 call sites 行為不變）
28. **Timeout precedence**：注入 `config=HttpClientConfig(read_timeout_s=5.0)` + `request.timeout_ms=999999` → adapter 用 5.0；不傳 config + `request.timeout_ms=2000` → 預設 config 的 read_timeout_s = 2.0
29. **Partial result on raise**：發生 REDIRECT_DENIED 後 `adapter.last_result` 非 None，含已完成的 redirect_hops 與 attempt_evidences

#### Integration tests（fetch 層）

30. **Acquisition 路徑 SSRF 阻擋**（codex iter-2 critical#2 驗證）：
    - 模擬 redirect 至 `127.0.0.1`
    - 走 `execute_http_network_acquisition` + factory（allowlist 由 acquisition 提供）
    - 預期得 `_failure_report(failure_type=PRIVATE_NETWORK_DENIED)`
31. **Acquisition 路徑保留 NetworkAdapterError 失敗類型**：模擬 RETRY_EXHAUSTED → outcome.report.operator_status == "retry_exhausted"

### 新增 integration tests（`@pytest.mark.live`）

```python
@pytest.mark.live
def test_real_chrome_ua_against_httpbin():
    """真實 UA 不被當 bot；驗 httpbin.org/headers 回的 User-Agent 含 Chrome 不含 VeraCrawl。"""

@pytest.mark.live
def test_real_redirect_recording():
    """httpbin.org/redirect-to → 真實 redirect 路徑能 record。"""
```

**不**用 `httpbin.org/status/429`（codex iter-1 important#10）—— retry 行為已在 unit 完整驗證。

### Boundary test

```bash
pytest tests/contract/test_*_import_boundaries.py
```

## Acceptance Criteria

- [ ] `pyproject.toml` 含 `httpx>=0.27,<1.0`、`pytest-httpserver`；**不含 `tenacity`**
- [ ] `src/veracrawl/adapters/network/stdlib_http.py` 不再 `import urllib.request` / `urllib.error`
- [ ] `grep "VeraCrawl-local-fixture" src/veracrawl/adapters/network/` = 0
- [ ] `src/veracrawl/adapters/network/stdlib_http.py` 預設 UA 通過 regex `^Mozilla/5\.0 .* Chrome/\d+\.\d+\.\d+\.\d+`
- [ ] `contracts/network.py` 含 `NetworkAttemptEvidence` model
- [ ] `contracts/enums.py` `NetworkFailureType` 含 `RETRY_EXHAUSTED`
- [ ] `ports/network.py` `NetworkClientResult` 含 `attempt_evidences` field（default 空 list）
- [ ] `fetch/network_acquisition.py` 含 `build_http_adapter_for_acquisition` factory
- [ ] `fetch/acquisition.py` `execute_source_acquisition` 不吞 `NetworkAdapterError`（用 import-graph + AST 驗證或單元測試）
- [ ] 既有 13 call sites 不需變動（`grep -c "StdlibHttpSourceAdapter(request)" src/veracrawl/cli tests/` 數量不變）
- [ ] `live_http.py:79` / `network_acquisition.py:143` 預設 `timeout_ms` ≥ 30000
- [ ] 31 個新 unit + integration test 全綠
- [ ] 既有 contract test 全綠
- [ ] `pytest -m "not live"` 在 CI 5 分鐘內完成（無真實 sleep）
- [ ] `ruff check` / `mypy src/veracrawl/adapters/network/` 無新錯
- [ ] commit message 描述 why（含 codex 三輪 feedback 對應的設計決策）

## Rollback

- 若 httpx `proxy=` 行為不一致：pin `httpx==0.27.2`
- 若 `NetworkAttemptEvidence` 加在 `NetworkClientResult` 觸發 dataclass 欄位排序問題：改 ABC + Protocol 或 `kw_only=True`
- 若 streaming size budget 與既有 `body_text` 抓取衝突：先讀完整 body 再 abort（捨 streaming 防 abuse 性質）但仍以 `body_size > budget` raise
- 若改 `execute_source_acquisition` 影響其他 adapter（不只 HTTP）：把判斷收斂在新 helper `_unwrap_network_adapter_error`，其他 adapter 無 NetworkAdapterError 不受影響

## Open Questions

- **Q1**：13 call site 的 SSRF migration 何時做？
  - **決定**：列 P0-1 後續 PR 但仍 P0 等級；本 plan 限縮在 acquisition path

- **Q2**：是否要把 `egress_allowlist` 直接擴入 `NetworkRequest` 契約？
  - **決定**：不擴。keep contract minimal；fetch layer factory 注入 config

- **Q3**：DNS rebinding 完整防護
  - **決定**：transport-level 完整防護列 P1；P0 提供 resolve-time 檢查

- **Q4**：`NetworkAttemptEvidence` inline vs ref-based
  - **決定**：P0-1 inline（無 store 依賴）；P1 改 ref + persistent

- **Q5**：HTTP/2
  - **決定**：徹底移除自 motivation 與 scope；P1 評估
