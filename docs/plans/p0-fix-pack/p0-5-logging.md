# P0-5: Structured Logging

## Status

| | |
|---|---|
| Iteration | v3 (after codex iterations 1, 2 feedback) |
| Started | - |
| Completed | - |
| Commits | - |
| Codex plan review | iter 1 ❌ (6 important + 3 minor), iter 2 ❌ (8 important + 3 minor; **no critical in either**) |

## Why

- `grep -rn "import logging\|import structlog" src/` = **0 命中**
- `print()` 在 `src/veracrawl/` 共 **129 處，全部在 `cli/`**（其他 16 個內部子模組已是 0）
- 大多數 CLI print 是 `print(json.dumps(report.model_dump(mode="json"), sort_keys=True))` — 這是 **CLI 的合約輸出**（user 透過 stdout 拿結構化 JSON），不應移除
- 真正缺的：
  - **logging 基礎建設**（無 logger module / 無 correlation_id / 無 log level / 無 sink）
  - **CLI 內非合約輸出**（exception 處理、進度訊息）混在 print 裡，但無法與合約 JSON 區分
  - **runtime / agent / adapter 進入點無 correlation_id 注入**
- 一旦未來這些子模組需要記錄事件（事故 / debug / audit），目前無基礎可用

對齊 docs：
- `docs/02-production-architecture.md`（observability 章）
- `docs/12-target-readiness-review-log.md`（observability 成熟度）

## Scope

**In scope:**

- `pyproject.toml` — 新增 `structlog`
- 新增 `src/veracrawl/runtime_support/logging.py`：
  - `configure_logging()`（idempotent；可重設）
  - `get_logger(name)`（回 stdlib-backed `BoundLogger`）
  - `with_correlation_id(cid)` context manager
  - `bind_runtime_context(**kwargs)` helper
- 新增 `src/veracrawl/runtime_support/_log_redaction.py`：
  - 安全欄位 policy processor（防止意外記錄 prompt / body / payload）
- 在 **代表性** 內部模組增加 `get_logger` 使用（**證明基礎建設可用**，不嘗試全 codebase 遷移）：
  - `src/veracrawl/adapters/network/stdlib_http.py`（與 P0-1 配合，記錄 attempt 行為 — 但不依賴 P0-1 完成）
  - `src/veracrawl/agents/tool_gateway.py`（與 P0-4 配合，audit 路徑記 logger）
  - `src/veracrawl/runtime_support/observability.py`（與 P0-8 配合）
- CLI bootstrap：所有 `cli/*.py` 的 `main()` 第一行呼叫 `configure_logging()`；30+ entry point 用單一 helper `bootstrap_cli_logging(prog: str)` 統一處理
- CLI 中 **非合約 print** 移到 logger（明確列出，下方 §3.4）
- 測試 + boundary test（grep + AST）

**Out of scope:**

- 全 codebase 129 print 遷移 — 過大；本 P0 僅遷移 **明確的非合約 print**（exception status、progress 訊息等），合約 JSON 輸出保留
- Log redaction filter 完整化（基本 unsafe-key policy 在本 P0；複雜 PII regex 屬 P1）
- OTel 整合（屬 P1-6）
- Log shipping / aggregator（Loki / Datadog）
- per-module log level config（先全域）
- 跨 thread 的 contextvar 傳播（**移除舊 plan 錯誤聲明**；async 同 context 才會 follow）

## Design

### 1. logging.py 模組（idempotent + caplog 相容 + scoped handler）

關鍵設計（codex iter-2 important#1, #2, #3, #5）：

- 使用 **scoped logger `logging.getLogger("veracrawl")`**，**不動 root logger** → 不影響 pytest caplog（caplog 對 root 加自己的 handler）
- 使用 **`structlog.stdlib.BoundLogger` 為 wrapper_class**（搭配 stdlib `LoggerFactory`），`get_logger` 回傳真正的 `structlog.stdlib.BoundLogger`，type 與測試對齊
- `configure_logging()` 真實 idempotent：每次呼叫都 **重設 level + formatter**；早返機制改為「config 內容相同則跳過」（compare config dataclass）
- `bootstrap_cli_logging` 用 **token-returning** 模式，呼叫端 `with` block 自動 reset cli context
- `with_correlation_id` 與 `bootstrap_cli_logging` 都接受顯式 close → 可巢狀 / 重入

```python
# src/veracrawl/runtime_support/logging.py
from __future__ import annotations

import logging
import os
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Callable, Iterator

import structlog
from structlog.stdlib import BoundLogger, LoggerFactory

from veracrawl.runtime_support._log_redaction import RedactSensitiveProcessor

_VERACRAWL_LOGGER_NAME = "veracrawl"
_VERACRAWL_HANDLER_TAG = "veracrawl-stream-handler"

_VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
_VALID_FORMATS = {"json", "console"}

_correlation_id_var: ContextVar[str | None] = ContextVar(
    "veracrawl_correlation_id", default=None,
)

_meta_logger = logging.getLogger("veracrawl._meta")


@dataclass(frozen=True)
class _LoggingState:
    level: int
    log_format: str


_current_state: _LoggingState | None = None


def _correlation_id_processor(_, __, event_dict: dict[str, Any]) -> dict[str, Any]:
    cid = _correlation_id_var.get()
    if cid is not None:
        event_dict.setdefault("correlation_id", cid)
    return event_dict


def _resolve_level(value: str | None) -> int:
    requested = (value or os.getenv("VERACRAWL_LOG_LEVEL", "INFO")).upper()
    if requested not in _VALID_LEVELS:
        _meta_logger.warning("invalid VERACRAWL_LOG_LEVEL=%r; falling back to INFO", requested)
        requested = "INFO"
    return getattr(logging, requested)


def _resolve_format(value: str | None) -> str:
    requested = (value or os.getenv("VERACRAWL_LOG_FORMAT", "json")).lower()
    if requested not in _VALID_FORMATS:
        _meta_logger.warning("invalid VERACRAWL_LOG_FORMAT=%r; falling back to json", requested)
        requested = "json"
    return requested


def _build_processors(log_format: str) -> list[Callable]:
    processors: list[Callable] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        _correlation_id_processor,
        RedactSensitiveProcessor(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if log_format == "console":
        # 強制 colors=False（pytest 環境 isatty=False 也會明確；prod tty 由 PY_COLORS 控制）
        processors.append(structlog.dev.ConsoleRenderer(colors=False))
    else:
        processors.append(structlog.processors.JSONRenderer(sort_keys=True))
    return processors


def configure_logging(
    *,
    level: str | None = None,
    log_format: str | None = None,
) -> None:
    """配置 veracrawl scoped logger。每次呼叫都重設 level / formatter（true idempotent）。

    不動 root logger → 不影響 pytest caplog 等外部 handler。
    """
    global _current_state

    log_level = _resolve_level(level)
    fmt = _resolve_format(log_format)

    new_state = _LoggingState(level=log_level, log_format=fmt)
    if new_state == _current_state:
        return  # 完全相同 → no-op

    veracrawl_logger = logging.getLogger(_VERACRAWL_LOGGER_NAME)
    veracrawl_logger.setLevel(log_level)
    # 移除既有 veracrawl-tagged handler，避免重複
    for h in list(veracrawl_logger.handlers):
        if getattr(h, "_veracrawl_tag", None) == _VERACRAWL_HANDLER_TAG:
            veracrawl_logger.removeHandler(h)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(log_level)
    handler._veracrawl_tag = _VERACRAWL_HANDLER_TAG  # type: ignore[attr-defined]
    veracrawl_logger.addHandler(handler)
    veracrawl_logger.propagate = False

    structlog.configure(
        processors=_build_processors(fmt),
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=LoggerFactory(),
        cache_logger_on_first_use=False,
    )

    _current_state = new_state


def reset_logging() -> None:
    """test fixture 用：清除 veracrawl logger handler、重設 structlog defaults。

    **不動** root logger handlers，pytest caplog 不受影響。
    """
    global _current_state
    veracrawl_logger = logging.getLogger(_VERACRAWL_LOGGER_NAME)
    for h in list(veracrawl_logger.handlers):
        if getattr(h, "_veracrawl_tag", None) == _VERACRAWL_HANDLER_TAG:
            veracrawl_logger.removeHandler(h)
    structlog.reset_defaults()
    _current_state = None


def get_logger(name: str | None = None) -> BoundLogger:
    """`name` 必須以 `veracrawl` 開頭或為 None；強制掛在 scoped logger 樹下。"""
    actual = name or _VERACRAWL_LOGGER_NAME
    if not actual.startswith(_VERACRAWL_LOGGER_NAME):
        actual = f"{_VERACRAWL_LOGGER_NAME}.{actual}"
    return structlog.get_logger(actual)


@contextmanager
def with_correlation_id(cid: str) -> Iterator[str]:
    token = _correlation_id_var.set(cid)
    try:
        yield cid
    finally:
        _correlation_id_var.reset(token)


@contextmanager
def bootstrap_cli_logging(prog: str) -> Iterator[None]:
    """所有 cli/*.py main() 用 `with bootstrap_cli_logging("..."):` 包覆。

    - 配置 logger（idempotent；重複呼叫 no-op）
    - 注入 cli=prog 至 contextvars，**離開區塊時自動 unbind**
    - 每次 main() 進場都產生新 correlation_id（env VERACRAWL_RUN_ID 優先）
    """
    configure_logging()
    cid = os.getenv("VERACRAWL_RUN_ID") or _generate_run_id()
    cli_token = structlog.contextvars.bind_contextvars(cli=prog).get("cli")
    cid_token = _correlation_id_var.set(cid)
    try:
        yield
    finally:
        _correlation_id_var.reset(cid_token)
        structlog.contextvars.unbind_contextvars("cli")


def _generate_run_id() -> str:
    import uuid
    return str(uuid.uuid4())
```

每個 CLI `main()` 改為 `with bootstrap_cli_logging("veracrawl-runtime"): ...` 包覆 — 解決 codex iter-2 important#5 的 leakage 問題：context 在 `with` 退出自動 unbind。

**重要**（codex iter-1 important#4 / iter-2）：移除「contextvar 自動跨 thread 傳播」聲明。**規範**：

> contextvar 跟隨**同 context** 的 async task。新 thread / `concurrent.futures.ThreadPoolExecutor` **不會**自動傳播；如需要，明確 capture 與 set。

**重要**（codex iter-1 important#4）：移除「contextvar 自動跨 thread 傳播」聲明。**規範**：

> contextvar 跟隨**同 context** 的 async task。新 thread / `concurrent.futures.ThreadPoolExecutor` **不會**自動傳播；如需要，明確 capture 與 set。

### 2. 安全欄位 Policy（codex iter-1 important#6）

```python
# src/veracrawl/runtime_support/_log_redaction.py
import re
from typing import Any

# 禁止意外記錄 prompt / response body / artifact payload / token / cookie 等
_SENSITIVE_KEY_PATTERNS = (
    re.compile(r"_?(prompt|response_text|response_body|body|payload|token|secret|api_?key|cookie|authorization)$", re.IGNORECASE),
)

class RedactSensitiveProcessor:
    """structlog processor：偵測常見敏感 key 並標記 <redacted>。"""

    def __call__(self, _, __, event_dict: dict[str, Any]) -> dict[str, Any]:
        for key in list(event_dict.keys()):
            if any(p.search(key) for p in _SENSITIVE_KEY_PATTERNS):
                event_dict[key] = "<redacted>"
        return event_dict
```

注意：這只擋 **key 名稱匹配** 的明顯敏感欄位。完整 PII regex / value-based 檢查屬 P1。

### 3. CLI 遷移範圍（codex iter-1 important#1）

#### 3.1 合約輸出 — **保留 print**

```bash
grep -nE "print\(json\." src/veracrawl/cli/*.py
```

這些 `print(json.dumps(report.model_dump(...)))` 是 CLI 的「主要輸出」，user 透過 stdout 拿結構化 JSON 餵給 `jq` / pipeline。**不動**。

#### 3.2 非合約 print — **移到 logger**

明確類型（v2 第一版 P0-5 範圍）：

| Pattern | 處置 |
|---------|------|
| `print(f"...")` 含進度 / 狀態 / debug | → `logger.info(event="...", **kw)` |
| `print(f"failed: {e}")` exception 訊息 | → `logger.error(event="...", error=str(e))` |
| `print(json.dumps(...))` user-facing 結構化輸出 | **保留** |
| `print("Done!")` / `print("OK")` 純成功訊息 | → `logger.info(event="run_complete")` |

#### 3.3 範圍說明 — 證明 + 代表性遷移

P0-5 不嘗試一次清完所有 CLI 內非合約 print。**目標**：

- 建立 logging 基礎建設（§1, §2）
- **3 個代表性 CLI 完整遷移**（覆蓋 fixture / live / runtime 三類）：
  - `src/veracrawl/cli/runtime.py`
  - `src/veracrawl/cli/live_http.py`
  - `src/veracrawl/cli/process.py`
- 其他 27 個 CLI 在 `main()` 開頭加 `bootstrap_cli_logging(prog="...")`，**但不立刻清 print**（列 P1 follow-up）

#### 3.4 內部模組代表性使用

至少在以下三個檔案展示 `get_logger` 用法：

- `src/veracrawl/adapters/network/stdlib_http.py`（為 P0-1 鋪路）
- `src/veracrawl/agents/tool_gateway.py`（為 P0-4 鋪路）
- `src/veracrawl/runtime_support/observability.py`（為 P0-8 鋪路）

證明基礎建設可被 import / 使用。

### 4. Entry-point Inventory（codex iter-1 important#5）

從 `pyproject.toml [project.scripts]` 提取的 30 個 CLI entry point（每個都需 `bootstrap_cli_logging` 注入）：

`veracrawl-contracts` / `veracrawl-fixture` / `veracrawl-runtime` / `veracrawl-run-control` / `veracrawl-production-persistence` / `veracrawl-durable` / `veracrawl-source` / `veracrawl-source-runtime` / `veracrawl-network` / `veracrawl-live-http` / `veracrawl-structured-source` / `veracrawl-browser-snapshot` / `veracrawl-credentialed-session` / `veracrawl-live-normalization` / `veracrawl-schema-extraction` / `veracrawl-live-evidence` / `veracrawl-result-publication` / `veracrawl-agent-model-runtime` / `veracrawl-process` / `veracrawl-evidence` / `veracrawl-output-coverage` / `veracrawl-website-patterns` / `veracrawl-product-acceptance` / `veracrawl-target-runtime` / `veracrawl-graph` / `veracrawl-projection` / `veracrawl-graph-frontier-review` / `veracrawl-temporal-kg` / `veracrawl-memory` / `veracrawl-graph-memory-runtime` …

實作完整列表用 `python -c "import tomllib; print(list(tomllib.load(open('pyproject.toml','rb'))['project']['scripts']))"` 取得，**不在 plan 寫死**（避免 plan 與 toml drift）。

acceptance 用 AST scan 檢查每個對應的 main() 第一行為 `bootstrap_cli_logging(...)`。

### 5. Correlation ID

`bootstrap_cli_logging`（§1）已內建 cid 注入（env `VERACRAWL_RUN_ID` 優先，否則 uuid4）。

CLI main():

```python
def main() -> int:
    with bootstrap_cli_logging(prog="veracrawl-runtime"):
        return _run(...)
```

#### Runtime / Agent Entry-point 完整 Inventory（codex iter-2 important#6）

每個 runtime entry 在進場以 `with with_correlation_id(...)` 包覆。明確列表：

| 模組 / 函式 | Correlation source | 說明 |
|---|---|---|
| `agents/runtime.py:run_agent_run` | `agent_run.id` | agent 執行邊界 |
| `agents/orchestration.py:orchestrate_step` | `orchestration_command.id` | step 級 |
| `agents/real_adapter_runtime.py:execute_real_adapter_run` | `run.id` | live 路徑 |
| `runtime_support/disaster_recovery.py:run_dr_drill_*` | drill_id（fixture / scenario）| 各 drill entry |
| `runtime_support/observability.py:run_observability_*` | scenario fixture id | 觀測 gate |
| `runtime_support/security_privacy.py:enforce_*` | request_id | security gate |
| `runtime_support/infrastructure_gate.py:run_infrastructure_*` | scenario fixture id | infra gate |
| `scheduler/*runtime*.py:run_scheduler_*` | run_id | scheduler 邊界 |
| `target_runtime/runner.py:run_*` | run_id | target runner |

注意：本 P0-5 在 plan 列出 **全部** entry point，但**只在 §3.4 三個代表性檔內**真正加 `with with_correlation_id(...)`（與其他內部模組遷移範圍對齊；其餘列 P1-LOG-CORRELATION-EXPANSION）。Acceptance 不要求所有 runtime entry 都遷移。

## Dependencies

| Package | Version | Status | Justification |
|---------|---------|--------|---------------|
| `structlog` | `>=24,<26` | NEW | structured + contextvar + stdlib bridge；自寫 stdlib processor 易錯且需 ≥ 200 行；版本 pin 對齊 `LoggerFactory` 介面 |

## Test Strategy

### 既有測試必須不破

```bash
pytest tests/
```

特別注意 `capsys` / `capfd` 抓 stdout 的測試 → 不變（合約 print 保留）。

### 新增 unit tests（`tests/runtime_support/test_logging.py`）

每個 test 開頭呼叫 `reset_logging()`（fixture），確保隔離。

1. **JSON format 預設**
   - configure → `get_logger("veracrawl.test").info(event="x", k=1)` → `caplog.records` 含 record，message 是 valid JSON 含 `"event":"x"`、`"k":1`

2. **Console format**（codex iter-2 minor#9）
   - `configure_logging(log_format="console")` → log → 輸出**非 JSON 形態**（不以 `{` 開頭、含 event 字面值）
   - 不斷言 ANSI（pytest capture 環境會關 colors）

3. **Log level 過濾**
   - `level="ERROR"` → `logger.info(...)` 不出現於 caplog；`logger.error(...)` 出現

4. **Idempotent — 重複 configure 不疊 handler**
   - 連續 3 次 `configure_logging(level="INFO")` → veracrawl logger handler 數量 = 1

5. **Idempotent — 改 level 真生效**（codex iter-2 important#2）
   - `configure_logging(level="INFO")` → log info → 出現
   - 同一程序內 `configure_logging(level="ERROR")` → log info → 不出現
   - assert veracrawl logger.level 已更新至 ERROR

6. **`reset_logging()` 不破 caplog**（codex iter-2 important#3）
   - configure → log → caplog 收到
   - reset_logging() → caplog handler 仍在 root（assert `any(isinstance(h, _pytest.logging.LogCaptureHandler) for h in logging.getLogger().handlers)`）
   - re-configure → 仍能 log，仍被 caplog 抓到

7. **無效 env 值 fallback**
   - `configure_logging(level="INVALID")` → fallback INFO + `_meta_logger.warning` 出現於 caplog（找 record name="veracrawl._meta"）
   - `configure_logging(log_format="invalid")` → fallback json

8. **correlation_id contextvar**
   - `with with_correlation_id("abc"): logger.info("x")` → record extra 含 `correlation_id="abc"`
   - 退出後 logger.info → record 不含 correlation_id

9. **巢狀 with_correlation_id**：外 a、內 b、退內回 a、退外清空

10. **async 同 context 跟隨**
    - `await asyncio.create_task(...)` 內 logger 帶外層 cid

11. **新 thread NOT 跟隨（明確規範；codex iter-1 important#4）**
    - `with with_correlation_id("X"): t = Thread(target=worker); t.start(); t.join()` → worker 內 cid 為 None
    - 註解：若需要跨 thread，要明確 capture（測試不斷言任何「自動」行為）

12. **Redaction processor**
    - `logger.info(event="x", api_key="secret", token="abc", body="raw")` → record 對應 keys 為 `"<redacted>"`
    - `logger.info(event="x", count=5)` → 不影響非敏感 keys

13. **Type sanity**
    - `get_logger("veracrawl.test")` 回 `structlog.stdlib.BoundLogger` 實例（直接 isinstance 檢查；現在 `wrapper_class` 已對齊）

### CLI bootstrap test（`tests/cli/test_logging_bootstrap.py`）

13. **每個 entry point main() 用 `with bootstrap_cli_logging(...)` 包覆 body** — AST scan：
    ```python
    import ast, tomllib
    from pathlib import Path

    def test_all_entrypoints_bootstrap_logging():
        toml = tomllib.loads(Path("pyproject.toml").read_text())
        scripts = toml["project"]["scripts"]
        offenders = []
        for name, target in scripts.items():
            module_path, func = target.split(":")
            module_file = Path("src/" + module_path.replace(".", "/") + ".py")
            tree = ast.parse(module_file.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func:
                    if not _has_bootstrap_with(node):
                        offenders.append(f"{module_file}:{func}")
        assert not offenders, f"missing bootstrap_cli_logging: {offenders}"

    def _has_bootstrap_with(func: ast.FunctionDef) -> bool:
        for stmt in func.body:
            if isinstance(stmt, ast.With):
                for item in stmt.items:
                    call = item.context_expr
                    if isinstance(call, ast.Call) and (
                        (isinstance(call.func, ast.Name) and call.func.id == "bootstrap_cli_logging")
                        or (isinstance(call.func, ast.Attribute) and call.func.attr == "bootstrap_cli_logging")
                    ):
                        return True
        return False
    ```

14. **CLI logs 帶 cli + correlation_id**（caplog）：
    - mock argv 跑 `cli/runtime.py:main()`
    - 內部 `get_logger("veracrawl.cli.runtime").info(event="run_started")`
    - assert caplog record 中 `cli == "veracrawl-runtime"` 且 `correlation_id` 為 valid uuid（或 env 注入值）

15. **`VERACRAWL_RUN_ID` env 覆蓋**：
    - `monkeypatch.setenv("VERACRAWL_RUN_ID", "explicit-id")`
    - 進 `bootstrap_cli_logging` → cid == "explicit-id"

16. **重複進場 leakage 防護**：
    - `with bootstrap_cli_logging("a"): logger.info("x")` → record cli=a
    - 退出後 `with bootstrap_cli_logging("b"): logger.info("y")` → record cli=b（不是 "a,b"）
    - 兩 with 中間 `logger.info("z")` → record 不含 cli

### Boundary tests（`tests/contract/`）

17. **限制範圍的 logging import boundary**（codex iter-2 important#8）：

    | 路徑 | 規則 |
    |---|---|
    | `src/veracrawl/runtime_support/logging.py` / `_log_redaction.py` | 允許 `import logging` / `import structlog`（基礎建設自身） |
    | `src/veracrawl/{adapters,agents,browser,fetch,extract,optimization,normalize,evidence,publish,graph,graph_memory,memory,scheduler,runtime_events,target_runtime}/*` | **禁止** raw import；必須走 `from veracrawl.runtime_support.logging import get_logger` |
    | `src/veracrawl/cli/*` | **允許** `import logging`（stdlib 整合 / unittest 相容）；但禁止 `import structlog`（必須 get_logger） |
    | `src/veracrawl/runtime_support/{observability,disaster_recovery,security_privacy,infrastructure_gate,...}` | **允許** raw `import logging`（rollback path） |
    | `tests/` | 無限制 |

18. **CLI 內非合約 print 已遷移（針對 §3.3 列出的 3 個檔）**：
    - grep `print(` 在這 3 個檔，必須**只**是 `print(json.dumps(...))` 形式
    - 其他形式 = 違規

### 既有測試遷移

部分既有測試用 `capsys` 抓 stdout — 合約 print 仍走 stdout，不影響。
若有抓內部進度訊息的測試（CLI 中已遷移的 prints），改為 `caplog.records[*].msg` 或 `caplog.text` 驗證。

## Acceptance Criteria

- [ ] `pyproject.toml` 含 `structlog>=24,<26`
- [ ] `src/veracrawl/runtime_support/logging.py` 存在；export `configure_logging` / `reset_logging` / `get_logger` / `with_correlation_id` / `bootstrap_cli_logging`（context manager 形態）
- [ ] `src/veracrawl/runtime_support/_log_redaction.py` 存在含 `RedactSensitiveProcessor`
- [ ] §3.3 列出的 3 個 CLI（runtime / live_http / process）內非合約 print **= 0**（grep 後只剩 `print(json.dumps(...))` 形式）
- [ ] 30 個 CLI entry point 的 main() body 為 `with bootstrap_cli_logging(...)` 包覆（AST scan boundary test 全綠）
- [ ] §3.4 列出的 3 個內部模組（stdlib_http / tool_gateway / observability）至少有一處 `get_logger(...)` 使用
- [ ] 18 個新 unit + bootstrap + boundary test 全綠
- [ ] 既有測試全綠（特別是 caplog 沒被破壞）
- [ ] `caplog` 能截獲 `get_logger(...).info(...)` 訊息（unit test 6 / bootstrap test 14 證明）
- [ ] **限制範圍的** import boundary（§Boundary test 17）全綠：
  - `runtime_support/logging.py` + `_log_redaction.py`：允許
  - 16 個內部模組：禁止 raw import
  - `cli/`：允許 stdlib `import logging`，禁止 raw `import structlog`
  - `runtime_support/{observability,...}`：允許（rollback path）
  - `tests/`：無限制
- [ ] commit message 寫明：「P0-5 ships logging infrastructure + 3 representative CLI migrations + 3 internal-module usage demos. Remaining 27 CLIs only get bootstrap injection; full non-contract print migration is P1-LOG-CLI-EXPANSION (estimate: <count from implementation grep> pending prints).」

## Rollback

- 若 structlog `LoggerFactory` 與某些 pytest 版本互動有 bug：
  - fallback `structlog.PrintLoggerFactory(file=sys.stderr)` + 改測試走 `capfd`，但**仍規範** redaction processor / correlation_id（這些不依賴 logger factory）
- 若 idempotent `configure_logging` 在 multi-CLI chain 場景出狀況：
  - 改用 module-level cache + per-call diff 比對
- 若 redaction key regex 誤匹某合法欄位（如 `request_token_count`）：
  - allowlist 機制：`RedactSensitiveProcessor(extra_safe_keys=...)`

## Open Questions

- **Q1**：30 個 CLI 都加 `bootstrap_cli_logging` 是否一次完成？或者只做 §3.3 三個 + 列 P1？
  - **決定**：30 個都加（單行注入，低成本，不破壞合約 print）；只是 print → logger 遷移限縮於 3 個

- **Q2**：correlation_id 來源
  - 預設：env `VERACRAWL_RUN_ID` 或自動 uuid4
  - **決定**：保留兩者；env 優先

- **Q3**：safe-field policy 是否觸發既有測試失敗？
  - 若有測試斷言 log message 含 `body` 等字串，需更新測試
  - **決定**：實作時 grep 確認，必要時用 `extra_safe_keys` 開放

- **Q4**：將 30 個 CLI 的 boilerplate `bootstrap_cli_logging` 集中寫法
  - 可考慮 decorator `@cli_main(prog="...")`
  - **決定**：P0-5 走顯式 helper，不引入 decorator（保持簡單）；decorator 列 P1
