# P0-4: Tool Gateway 真實 Gating

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

`src/veracrawl/agents/tool_gateway.py` 全文 28 行，`execute()` 直接回 `CommandResult(status=COMMITTED, ...)`：

- 沒看 command type
- 沒看 args
- 沒 allowlist
- 沒 sandbox
- 沒輸入驗證
- 沒 rate limit / quota

所有「sandbox / 權限」都只是命名 convention（`allowed_tool_spec_refs` 是字串 ref，沒運行時對齊）。如果上 prod 讓 LLM agent 真用這個 gateway，等於 LLM 想做什麼都通過。

## Scope

**In scope:**

- `src/veracrawl/agents/tool_gateway.py` — 重寫核心 `execute()` 邏輯
- 新增：`src/veracrawl/agents/_tool_audit.py` — audit log helper（寫 outbox）
- 新增：`src/veracrawl/agents/_tool_quota.py` — quota tracker
- `src/veracrawl/contracts/tool_gateway.py`（若不存在則新增）— 定義 `ToolSpec`、`ToolPolicy`、`CommandResult`、`RejectionReason`
- 對應的 port（如 `ports/tool_gateway.py`）— 確保 hexagonal 邊界

**Out of scope:**

- 真實 sandbox（Docker / Firecracker）— 屬 deployment 層；先做 **policy gate**，sandbox 列 P1
- 跨 agent 共享 quota（distributed counter）— 列 P1，先做 in-process
- 細粒度 RBAC（per-user policy）— 列 P1

## Design

### 核心介面

```python
# src/veracrawl/contracts/tool_gateway.py

class ToolSpec(BaseModel):
    """單一 tool 的 schema 定義。"""
    name: str                                        # e.g. "fetch_url"
    args_schema: dict                                # JSON Schema for command args
    cost_per_call_tokens: int = 0                    # 用於 quota 計算
    description: str

class ToolPolicy(BaseModel):
    """gateway 的執行策略。"""
    allowed_tools: dict[str, ToolSpec]               # name → spec
    max_calls_per_run: int = 100
    max_cost_tokens_per_run: int = 100_000
    audit_redact_keys: frozenset[str] = frozenset()  # args 寫 audit 時要脫敏的 key

class CommandRequest(BaseModel):
    tool_name: str
    args: dict
    run_id: str                                       # 用於 quota 跟 correlation

class RejectionReason(StrEnum):
    UNKNOWN_TOOL = "unknown_tool"
    SCHEMA_VIOLATION = "schema_violation"
    QUOTA_EXCEEDED_CALLS = "quota_exceeded_calls"
    QUOTA_EXCEEDED_COST = "quota_exceeded_cost"
    POLICY_DENIED = "policy_denied"

class CommandResult(BaseModel):
    status: Literal["COMMITTED", "REJECTED"]
    rejection_reason: RejectionReason | None = None
    rejection_detail: str | None = None              # 例如哪個欄位 schema violate
    output: Any | None = None
    cost_tokens: int = 0
```

### Gateway 實作

```python
# src/veracrawl/agents/tool_gateway.py
from jsonschema import Draft202012Validator, ValidationError

class InProcessToolGateway:
    def __init__(
        self,
        *,
        policy: ToolPolicy,
        audit_outbox: Outbox,
        tool_executor: Callable[[str, dict], Any],   # 真正執行 tool 的 callable
    ):
        self._policy = policy
        self._audit = audit_outbox
        self._executor = tool_executor
        self._quota: dict[str, _RunQuota] = {}

    def execute(self, request: CommandRequest) -> CommandResult:
        # 1. allowlist
        spec = self._policy.allowed_tools.get(request.tool_name)
        if spec is None:
            return self._reject(
                request, RejectionReason.UNKNOWN_TOOL,
                detail=f"tool {request.tool_name!r} not in allowlist",
            )

        # 2. schema validation
        try:
            Draft202012Validator(spec.args_schema).validate(request.args)
        except ValidationError as e:
            return self._reject(
                request, RejectionReason.SCHEMA_VIOLATION,
                detail=f"path={list(e.absolute_path)} message={e.message}",
            )

        # 3. quota
        quota = self._quota.setdefault(request.run_id, _RunQuota())
        if quota.calls + 1 > self._policy.max_calls_per_run:
            return self._reject(
                request, RejectionReason.QUOTA_EXCEEDED_CALLS,
                detail=f"calls={quota.calls} cap={self._policy.max_calls_per_run}",
            )
        if quota.cost_tokens + spec.cost_per_call_tokens > self._policy.max_cost_tokens_per_run:
            return self._reject(
                request, RejectionReason.QUOTA_EXCEEDED_COST,
                detail=f"cost={quota.cost_tokens + spec.cost_per_call_tokens} cap=...",
            )

        # 4. execute
        try:
            output = self._executor(request.tool_name, request.args)
        except Exception as exc:
            self._audit_event(request, decision="ERROR", error=type(exc).__name__)
            raise

        quota.calls += 1
        quota.cost_tokens += spec.cost_per_call_tokens

        result = CommandResult(
            status="COMMITTED",
            output=output,
            cost_tokens=spec.cost_per_call_tokens,
        )
        self._audit_event(request, decision="COMMITTED")
        return result

    def _reject(self, request, reason, *, detail) -> CommandResult:
        result = CommandResult(status="REJECTED", rejection_reason=reason, rejection_detail=detail)
        self._audit_event(request, decision="REJECTED", reason=reason.value, detail=detail)
        return result

    def _audit_event(self, request, *, decision, **kw) -> None:
        args_hash = sha256(json.dumps(request.args, sort_keys=True).encode()).hexdigest()
        redacted_args = _redact(request.args, self._policy.audit_redact_keys)
        self._audit.publish(ToolGatewayAuditEvent(
            run_id=request.run_id,
            tool_name=request.tool_name,
            args_hash=args_hash,
            args_preview=redacted_args,
            decision=decision,
            timestamp=datetime.now(timezone.utc),
            **kw,
        ))
```

### Audit log

```python
class ToolGatewayAuditEvent(BaseModel):
    run_id: str
    tool_name: str
    args_hash: str
    args_preview: dict          # 已脫敏
    decision: Literal["COMMITTED", "REJECTED", "ERROR"]
    reason: str | None = None
    detail: str | None = None
    error: str | None = None
    timestamp: datetime
```

寫到既有 outbox（與 P0-3 共用）。如果還沒有真正的 outbox 抽象，先用 in-memory list + 列 P1 接 persistent。

### 脫敏

```python
def _redact(args: dict, redact_keys: frozenset[str]) -> dict:
    return {
        k: ("<redacted>" if k in redact_keys else v)
        for k, v in args.items()
    }
```

policy.audit_redact_keys 預設 `frozenset({"api_key", "token", "password", "secret"})`。

### Tool Executor 注入

`tool_executor: Callable[[str, dict], Any]` — 由呼叫端注入。不在 gateway 寫死任何 tool 實作（保持 hexagonal 邊界）。

## Dependencies

| Package | Status | Justification |
|---------|--------|---------------|
| `jsonschema` | 可能 NEW（先 grep `pyproject.toml`） | 真正執行 JSON Schema 驗證；自寫易錯 |

## Test Strategy

### 既有測試必須不破

```bash
pytest tests/agents/
```

特別注意：當前 `tool_gateway.py` 的 28 行回 `COMMITTED` 的行為，可能有測試假設這個寬鬆性。新行為下這些測試應該更新（變成「合法 tool + 合法 args → COMMITTED」的版本）。

### 新增 unit tests（`tests/agents/test_tool_gateway.py`）

1. **未在 allowlist → REJECTED**
   - policy.allowed_tools = `{"a": ToolSpec(...)}`
   - request.tool_name = `"b"`
   - assert `result.status == "REJECTED"`
   - assert `result.rejection_reason == RejectionReason.UNKNOWN_TOOL`

2. **Schema violation → REJECTED**
   - tool spec args_schema = `{"type": "object", "required": ["url"], "properties": {"url": {"type": "string"}}}`
   - request.args = `{}` → `SCHEMA_VIOLATION`
   - request.args = `{"url": 123}` → `SCHEMA_VIOLATION`
   - request.args = `{"url": "https://x"}` → `COMMITTED`

3. **Detail 包含具體欄位**
   - 上面 `{"url": 123}` case → `result.rejection_detail` 包含 `"url"`

4. **Quota: max_calls_per_run**
   - policy.max_calls_per_run = 2
   - 連續 3 次合法呼叫 → 第 3 次 `QUOTA_EXCEEDED_CALLS`

5. **Quota: max_cost_tokens_per_run**
   - tool spec cost_per_call_tokens = 50
   - max_cost_tokens_per_run = 100
   - 連續 3 次（共 150 tokens） → 第 3 次 `QUOTA_EXCEEDED_COST`
   - 但第 2 次（100 tokens）仍應通過

6. **Quota per run_id 獨立**
   - run_id="A" 用滿 quota
   - run_id="B" 仍可呼叫

7. **Audit COMMITTED**
   - mock outbox
   - 一次成功 → outbox 收到一個 event，decision="COMMITTED"

8. **Audit REJECTED 含 reason**
   - 一次失敗 → event.decision == "REJECTED"，reason 對應

9. **Audit args 脫敏**
   - policy.audit_redact_keys = `frozenset({"api_key"})`
   - request.args = `{"url": "https://x", "api_key": "sk-secret"}`
   - audit event.args_preview["api_key"] == "<redacted>"
   - audit event.args_preview["url"] == "https://x"
   - **但 args_hash 仍是原始 args 的 hash**（用於追溯）

10. **Executor 拋例外時也寫 audit**
    - executor raise → audit event decision="ERROR"
    - exception 仍向上 propagate

### Boundary test

新增 import boundary：`tests/contract/test_tool_gateway_import_boundaries.py`
- `tool_gateway.py` 不可 import 任何 `adapters.*`（gateway 是 application layer）
- 不可 import `httpx` / `playwright` 等具體 tool 實作

## Acceptance Criteria

- [ ] `src/veracrawl/agents/tool_gateway.py` 行數 > 28（必然，因為加入了真實邏輯）
- [ ] `grep "status=.COMMITTED" src/veracrawl/agents/tool_gateway.py` 不再 unconditional
- [ ] 10 個新 unit test 全綠
- [ ] 既有 contract test 全綠
- [ ] `jsonschema` 在 pyproject.toml dependencies
- [ ] audit event 寫 outbox（mock 驗證）
- [ ] commit message 描述 why（特別「之前是橡皮章」）

## Rollback

- 如果 `jsonschema` 與 Pydantic schema 互轉麻煩：
  - tool spec 直接定義 `args_pydantic_model: type[BaseModel]`，不走 jsonschema
  - 缺點：失去與外部 LLM tool spec（OpenAI / Anthropic）的對齊
- 如果 quota 邏輯影響既有 fixture-driven 測試：
  - 預設 policy 的 quota 設極大值（near-unlimited）
  - 測試明確注入小 quota policy

## Open Questions

- **Q1**：JSON Schema vs Pydantic model — tool spec 用哪個？
  - 建議：JSON Schema（與 LLM tool calling 標準對齊；contracts 內仍可用 Pydantic 驗證 schema 自身合法）

- **Q2**：quota 跨 run_id 共享一個全局 cap？
  - 建議：先 per-run，全局 cap 列 P1 distributed counter

- **Q3**：audit event 是否要記錄 result.output（截斷）？方便 debug
  - 建議：**不記錄 output** — 防止 LLM-generated 內容意外進 audit log（可能含敏感資料）。只記 args_hash + cost

- **Q4**：tool_executor 例外要 wrap 成 `ToolExecutionError` 還是裸 propagate？
  - 建議：裸 propagate 但 audit；caller 自決定處理。Wrap 列 P1（與全局 exception 階級一起做）
