# P0-3: OpenAI Adapter 修復

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

`adapters/model_providers/openai_responses.py` 是全 codebase 唯一真實對外打 LLM API 的程式，但問題嚴重：

- **L14**：寫死 `_DEFAULT_MODEL = "gpt-5.4-mini"` — 截至 2026-05 不存在的 model ID，會直接 401/404
- **L73-91**：request body 無 `tools` / `tool_choice` / `response_format` / `temperature` / `max_output_tokens=256`（小到無法做結構化輸出）
- **整體**：contract 寫了 `tool_schema_refs` / `response_schema_ref` / `prompt_template_ref` 但 adapter 全丟掉；response 只取 `output_text` 純字串就 hash，沒 JSON parse、沒 schema validate
- **L101-106**：error path 把整段 `error_body`（可能含 echo 回的 prompt）放進 `RuntimeError` — 違反 repo 自家定義的 `RAW_RESPONSE_LEAK` failure type
- **無 retry / backoff / circuit breaker / token budget cap**
- **L33** `_token_usage` 只在記憶體 dict 累計 → 多 process 失準、無 cost tracking 寫到 outbox

## Scope

**In scope:**

- `src/veracrawl/adapters/model_providers/openai_responses.py` — 全檔重整（保留 class 名 / port 介面）
- 修改 `ModelRequest` — 將 model name 從 default 改為必填欄位（**注意**：這會影響呼叫端，需同步更新；若會擴大 scope 太多則只在 adapter 內 require）
- 新增 `_redact.py` — error body 脫敏 helper
- `pyproject.toml` — 新增 `tenacity`（若 P0-1 已加則共用）

**Out of scope（P1）:**

- 重設計 `ModelProviderPort` 介面（這是 P1-1，會修 messages list / streaming / tools 介面層）
- Anthropic / Bedrock provider 實作
- 真正的 prompt cache 機制（OpenAI prefix cache 需 prompt 開頭穩定，跟 P1 prompt registry 一起做）
- 寫 outbox event 的 schema（沿用既有 outbox 機制即可）

## Design

### Model name 必填

**最小動法**：

1. 在 `ModelRequest`（或其建構器）保留 `model: str | None`，但 adapter 入口檢查 `if request.model is None: raise ValueError(...)`
2. 移除 `_DEFAULT_MODEL` 常數
3. 呼叫端遷移：grep 所有建 `ModelRequest` 的地方，補上 `model=...`

**Mode 候選清單**（截至 2026-05 OpenAI 可用模型，使用 Responses API）：
- `gpt-4.1` / `gpt-4.1-mini` / `gpt-4.1-nano`
- `gpt-5` / `gpt-5-mini`
- `o4-mini`

不在 adapter 寫死任何 model；fixture / benchmark 處明確指定。

### Tools / Structured Output 路徑

新增可選欄位至 `ModelRequest`（若 port 介面允許）：

```python
@dataclass(frozen=True)
class ModelRequest:
    model: str
    prompt: str                              # 後續 P1 會改 messages list
    max_output_tokens: int = 4096            # 預設 4096
    tools: list[dict] | None = None          # JSON Schema tool defs
    tool_choice: str | dict | None = None    # "auto" | "required" | {"type":"function","function":{"name":"x"}}
    response_format: dict | None = None      # {"type":"json_schema","json_schema":{...}}
    temperature: float | None = None
    metadata: dict[str, str] | None = None
```

若不能擴 `ModelRequest`（會破現有契約），則用 `request.context_payload` 帶 dict（仍是 side-channel，但有 schema 約束）。**優先嘗試擴欄位**；若失敗在 plan 註明改走 context_payload。

### Response 解析 + Pydantic validation

```python
def _parse_response(raw: dict, response_schema: type[BaseModel] | None) -> ModelResponse:
    output_text = _extract_text(raw)
    parsed = None
    if response_schema is not None:
        try:
            parsed = response_schema.model_validate_json(output_text)
        except ValidationError as e:
            raise StructuredOutputViolation(
                schema=response_schema.__name__,
                error_summary=_summarize_validation_error(e),  # 不含 raw response
            )
    return ModelResponse(
        output_text=output_text,
        parsed=parsed,
        token_usage=raw.get("usage", {}),
        ...
    )
```

`response_schema` 從 `request.response_format` 對應的 Pydantic class 取得（呼叫端需傳 class，不只 dict — 透過 contract 對齊）。

### Retry / Backoff

用 `tenacity`（與 P0-1 共用）：

- Retry on：`httpx.ConnectError` / `ConnectTimeout` / `ReadTimeout` / 429 / 500 / 502 / 503 / 504
- Don't retry：4xx 非 429（含 401 / 403 / 404 / 422）
- 等待：`wait_exponential(multiplier=2, min=2, max=60)` + jitter
- 最大嘗試：`max_attempts=4`（共 1 次原始 + 3 次 retry）

429 解析 `Retry-After`（如同 P0-1）。

### Token / Cost Tracking 寫進 outbox

```python
def _emit_token_usage_event(self, request: ModelRequest, response: ModelResponse) -> None:
    event = TokenUsageEvent(
        request_id=request.request_id,
        model=request.model,
        input_tokens=response.token_usage["input_tokens"],
        output_tokens=response.token_usage["output_tokens"],
        cached_tokens=response.token_usage.get("cached_tokens", 0),
        timestamp=datetime.now(timezone.utc),
    )
    self._outbox.publish(event)
```

仍保留 `_token_usage` in-memory dict 作為當前 session 加總（用於 budget cap 即時檢查），但**source of truth 是 outbox event**，由 P1 的 cost aggregator 消費。

### Token Budget Cap

```python
def __init__(self, *, max_tokens_per_run: int | None = None, ...):
    self._max_tokens_per_run = max_tokens_per_run
    self._tokens_used_this_run = 0

def complete(self, request):
    if self._max_tokens_per_run and self._tokens_used_this_run + request.max_output_tokens > self._max_tokens_per_run:
        raise TokenBudgetExceeded(used=..., cap=...)
    ...
```

預設 `None`（不限制）；fixture / benchmark 注入 cap。

### Error Path 不洩漏

```python
def _on_http_error(self, response: httpx.Response, request: ModelRequest) -> None:
    # 完全不讀 response.text / response.json
    error_code = _classify(response.status_code)
    raise ModelProviderError(
        code=error_code,                          # AUTH_FAILED / RATE_LIMITED / SERVER_ERROR / ...
        status=response.status_code,
        request_id_header=response.headers.get("x-request-id"),
        # 不放任何 body / prompt 內容
    )
```

新增 helper：

```python
# src/veracrawl/adapters/model_providers/_redact.py
def safe_error_summary(status: int, request_id: str | None) -> str:
    """供 logging 使用，保證不含 PII / prompt / response body。"""
    return f"openai_responses error status={status} request_id={request_id or '<none>'}"
```

呼叫端在 logger（P0-5）只能用 `safe_error_summary`，**不能直接 stringify exception**。

## Dependencies

| Package | Status | Justification |
|---------|--------|---------------|
| `tenacity` | NEW（或共用 P0-1 已加） | retry / backoff |
| `httpx` | NEW（或共用 P0-1 已加） | 取代當前的（疑似）requests / urllib，與 P0-1 對齊 |

`pydantic` 已在 contracts 用，無需新增。

## Test Strategy

### 既有測試必須不破

```bash
pytest tests/adapters/model_providers/ tests/agents/
```

### 新增 unit tests（`tests/adapters/model_providers/test_openai_responses.py`）

1. **Model name 必填**
   - `ModelRequest(model=None, ...)` → adapter 入口 raise
   - `ModelRequest(model="gpt-4.1", ...)` → 正常呼叫

2. **無寫死模型名**
   - grep `_DEFAULT_MODEL` / `gpt-5.4-mini` 在 src/ 命中數 = 0（在 acceptance section 機械驗證）

3. **Error path 無洩漏（核心 test）**
   - mock httpx 回 401 + body `"prompt: secret_key=abc123"` + `x-request-id: req_xyz`
   - 預期：raise `ModelProviderError(code="AUTH_FAILED", status=401, request_id_header="req_xyz")`
   - assert `"secret_key" not in str(error)`
   - assert `"prompt" not in str(error)`
   - assert `"abc123" not in str(error)`

4. **429 + Retry-After retry**
   - mock 第一次回 429 + `Retry-After: 2`，第二次回 200
   - assert 第二次 request 之間隔 ≥ 2.0s
   - assert response 成功

5. **致命 4xx 不重試**
   - mock 第一次回 422 → 立即 raise，無 retry

6. **Structured output validation 成功**
   - 定義 Pydantic schema `class Out(BaseModel): name: str; age: int`
   - mock 回 `{"name": "x", "age": 30}` JSON 字串
   - assert `response.parsed == Out(name="x", age=30)`

7. **Structured output validation 失敗**
   - 定義同上 schema
   - mock 回 `{"name": "x", "age": "thirty"}`
   - assert raise `StructuredOutputViolation`
   - assert `"thirty" not in str(error)`（不洩漏 raw response）

8. **Tools 路徑帶上 request body**
   - 給 `request.tools=[{"type": "function", ...}]`
   - intercept httpx request → assert request body json 包含 `tools` 欄位

9. **Token budget cap**
   - `max_tokens_per_run=100`
   - 第一次呼叫帶 `max_output_tokens=80` → 成功
   - 第二次呼叫帶 `max_output_tokens=80` → raise `TokenBudgetExceeded`

10. **Outbox emit**
    - mock outbox.publish
    - 完成一次成功 complete → assert outbox.publish 被呼叫一次，event 為 `TokenUsageEvent` 且欄位正確

### 新增 integration tests（`@pytest.mark.live`，預設 skip）

`tests/adapters/model_providers/test_openai_responses_live.py`：

```python
@pytest.mark.live
def test_real_completion(openai_api_key):
    adapter = OpenAIResponsesAdapter(api_key=openai_api_key)
    response = adapter.complete(ModelRequest(
        model="gpt-4.1-mini",
        prompt="reply with the single word: pong",
        max_output_tokens=10,
    ))
    assert "pong" in response.output_text.lower()

@pytest.mark.live
def test_real_structured_output(openai_api_key):
    class Sentiment(BaseModel):
        polarity: Literal["positive", "negative", "neutral"]
        confidence: float

    adapter = OpenAIResponsesAdapter(api_key=openai_api_key)
    response = adapter.complete(ModelRequest(
        model="gpt-4.1-mini",
        prompt="classify: 'I love this'",
        response_format={"type": "json_schema", "json_schema": Sentiment.model_json_schema()},
        max_output_tokens=100,
    ))
    assert response.parsed.polarity == "positive"
```

`openai_api_key` fixture 從 `OPENAI_API_KEY` env var 注入；缺則 skip。

## Acceptance Criteria

- [ ] `grep "_DEFAULT_MODEL" src/veracrawl/adapters/model_providers/` = 0
- [ ] `grep "gpt-5.4-mini" src/` = 0
- [ ] `grep "max_output_tokens=256" src/veracrawl/adapters/model_providers/` = 0
- [ ] adapter 入口對 `request.model is None` 有顯式驗證
- [ ] error path 不 stringify response body（grep `response.text` / `error_body` 在 raise 路徑 = 0）
- [ ] 10 個新 unit test 全綠
- [ ] 既有 contract test 全綠
- [ ] outbox event `TokenUsageEvent` 在每次成功 complete 後被 publish
- [ ] commit message 描述 why（特別 RAW_RESPONSE_LEAK 修正）

## Rollback

- 若擴 `ModelRequest` 欄位破壞太多 contract test：
  - 改走 `context_payload: dict` 路徑（保留 side-channel 但 schema 約束）
  - 在本檔加 `## Lessons` 註明
- 若 `tools` / `response_format` 在 OpenAI Responses API（非 Chat Completions）的格式有別：
  - 對齊 [OpenAI Responses API 文件](https://platform.openai.com/docs/api-reference/responses) 規範
  - 必要時 split 兩種 API path 的 helper
- 若 outbox 介面不存在 / 無法用：
  - 寫一個 `_FileOutbox`（append JSONL），列入 P1 統一替換為真正的 outbox

## Open Questions

- **Q1**：擴 `ModelRequest` 欄位 vs 走 `context_payload`，哪個 contract test 變更較少？
  - 開工前先 grep `ModelRequest(` 數量決定

- **Q2**：error code 列舉要不要在 contracts 定義（公開）還是 adapter 內部（私有）？
  - 建議：放 `contracts/model_provider_errors.py`，呼叫端可 `match` 處理

- **Q3**：是否在這個 P0 處理 prompt-injection 防護？
  - 建議：**不處理**。Prompt injection 屬 P1（prompt registry + sanitization layer），這個 P0 只專注 adapter level 安全（不洩漏 + retry + structured output）

- **Q4**：`StructuredOutputViolation` 是否要把 first 50 chars of raw output 放進 error？方便 debug？
  - 建議：**不放**。寧願 debug 麻煩也不要冒洩漏風險。可以提供 `raw_output_hash` 便於跟 outbox event 對應
