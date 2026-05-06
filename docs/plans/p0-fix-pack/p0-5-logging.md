# P0-5: Structured Logging

## Status

| | |
|---|---|
| Iteration | v2 (after codex iteration 1 feedback) |
| Started | - |
| Completed | - |
| Commits | - |
| Codex plan review | iter 1 ❌ (6 important + 3 minor; no critical) |

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

### 1. logging.py 模組（idempotent + caplog 相容）

關鍵設計（codex iter-1 important#2 + #3 + #8）：使用 **stdlib `logging.LoggerFactory`** 讓 structlog 透過 stdlib `Logger` 發 record，pytest `caplog` 可截獲。

```python
# src/veracrawl/runtime_support/logging.py
from __future__ import annotations

import logging
import os
import sys
from contextvars import ContextVar
from typing import Any, Callable

import structlog
from structlog.stdlib import BoundLogger, LoggerFactory

from veracrawl.runtime_support._log_redaction import RedactSensitiveProcessor

_correlation_id_var: ContextVar[str | None] = ContextVar(
    "veracrawl_correlation_id", default=None,
)

_VALID_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
_VALID_FORMATS = {"json", "console"}

_configured: bool = False
_meta_logger = logging.getLogger("veracrawl._meta")  # 用於 fallback warnings


def _correlation_id_processor(_, __, event_dict: dict[str, Any]) -> dict[str, Any]:
    cid = _correlation_id_var.get()
    if cid is not None:
        event_dict.setdefault("correlation_id", cid)
    return event_dict


def configure_logging(
    *,
    level: str | None = None,
    log_format: str | None = None,
    force: bool = False,
) -> None:
    """設置 logger。可重複呼叫；後者覆蓋前者。

    - `force=True` 完全 reset 既有設置（測試使用）。
    - 其他情況下 idempotent：同樣 env 重複呼叫 == 一次。
    """
    global _configured
    if _configured and not force:
        return

    requested_level = (level or os.getenv("VERACRAWL_LOG_LEVEL", "INFO")).upper()
    if requested_level not in _VALID_LEVELS:
        _meta_logger.warning(
            "invalid VERACRAWL_LOG_LEVEL=%r; falling back to INFO", requested_level,
        )
        requested_level = "INFO"
    log_level = getattr(logging, requested_level)

    requested_format = (log_format or os.getenv("VERACRAWL_LOG_FORMAT", "json")).lower()
    if requested_format not in _VALID_FORMATS:
        _meta_logger.warning(
            "invalid VERACRAWL_LOG_FORMAT=%r; falling back to json", requested_format,
        )
        requested_format = "json"

    # Reset stdlib logger handlers（force 模式下）
    root = logging.getLogger()
    if force:
        for h in list(root.handlers):
            root.removeHandler(h)

    handler = logging.StreamHandler(sys.stderr)
    handler.setLevel(log_level)
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(handler)
    root.setLevel(log_level)

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
    if requested_format == "console":
        processors.append(structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()))
    else:
        processors.append(structlog.processors.JSONRenderer(sort_keys=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(log_level),
        logger_factory=LoggerFactory(),                 # stdlib-backed → caplog OK
        cache_logger_on_first_use=False,                # 避免 idempotency 問題
    )

    _configured = True


def reset_logging() -> None:
    """test fixture / lifecycle 用。"""
    global _configured
    _configured = False
    structlog.reset_defaults()
    root = logging.getLogger()
    for h in list(root.handlers):
        root.removeHandler(h)


def get_logger(name: str | None = None) -> BoundLogger:
    return structlog.get_logger(name)


class with_correlation_id:
    def __init__(self, cid: str):
        self._cid = cid
        self._token = None

    def __enter__(self):
        self._token = _correlation_id_var.set(self._cid)
        return self._cid

    def __exit__(self, *args):
        _correlation_id_var.reset(self._token)


def bootstrap_cli_logging(prog: str) -> None:
    """所有 cli/*.py main() 開頭呼叫。注入 prog name 至 contextvars。"""
    configure_logging()
    structlog.contextvars.bind_contextvars(cli=prog)
```

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

每個 CLI `main()` 開頭：

```python
def main() -> int:
    bootstrap_cli_logging(prog="veracrawl-runtime")
    cid = os.getenv("VERACRAWL_RUN_ID") or str(uuid.uuid4())
    with with_correlation_id(cid):
        return _run(...)
```

每個 `runtime_support/*` 與 `agents/*` runtime entry 也對應一個 `with with_correlation_id(...)` boundary。具體 entry point 列表（要在 plan 中明確）：

- `agents/runtime.py:run_agent(...)` → 進 `run_id` 為 cid
- `agents/orchestration.py:orchestrate(...)` → 進對應 run_id
- `runtime_support/disaster_recovery.py:run_dr_drill(...)` → 進 drill_id
- 其他 runtime entry：在 P0-5 實作時 grep 識別並加註

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

1. **JSON format 預設**
   - configure → log → `caplog.records` 含 record，message 是 valid JSON

2. **Console format**
   - `configure_logging(log_format="console")` → 輸出 ANSI（用 `capfd.readouterr()` 驗 stderr 含 ANSI escape）

3. **Log level 過濾**
   - `level="ERROR"` → `logger.info(...)` 不出現於 caplog；`logger.error(...)` 出現

4. **Idempotent**
   - 連續 3 次 `configure_logging()` 不重複加 handler（檢查 `logging.getLogger().handlers` 長度）

5. **`force=True` 重設**
   - configure → reset → re-configure(level="DEBUG") → 新 level 生效

6. **無效 env 值 fallback（codex iter-1 minor#9）**
   - `configure_logging(level="INVALID")` → fallback INFO + meta_logger.warning
   - `configure_logging(log_format="invalid")` → fallback json

7. **correlation_id contextvar**
   - `with with_correlation_id("abc"): logger.info("x")` → caplog record 含 `"correlation_id":"abc"`
   - 退出後 logger.info → 不含

8. **巢狀 with_correlation_id**

9. **async 同 context 跟隨**
   - `await asyncio.create_task(...)` 內 logger 帶外層 cid

10. **新 thread NOT 跟隨（明確規範）**
    - `Thread(target=...)` 內 cid 為 None；測試斷言此行為，避免未來誤改

11. **Redaction processor**
    - `logger.info(event="x", api_key="secret", token="abc", body="...")` → caplog record 中對應 keys 為 `"<redacted>"`
    - `logger.info(event="x", count=5)` → 不影響非敏感 keys

12. **Type sanity**
    - `get_logger("veracrawl.test")` 回 `structlog.stdlib.BoundLogger` 子類別實例

### CLI bootstrap test（`tests/cli/test_logging_bootstrap.py`）

13. **每個 entry point main() 第一行為 `bootstrap_cli_logging`** — AST scan：
    ```python
    import ast, tomllib
    from pathlib import Path

    def test_all_entrypoints_bootstrap_logging():
        toml = tomllib.loads(Path("pyproject.toml").read_text())
        scripts = toml["project"]["scripts"]
        offenders = []
        for name, target in scripts.items():
            module_path, func = target.split(":")
            module_file = Path("src") / module_path.replace(".", "/") / ".py"  # 修正
            module_file = Path("src/" + module_path.replace(".", "/") + ".py")
            tree = ast.parse(module_file.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func:
                    if not _first_call_is_bootstrap_logging(node):
                        offenders.append(f"{module_file}:{func}")
        assert not offenders, f"missing bootstrap_cli_logging: {offenders}"
    ```

### Boundary tests（`tests/contract/`）

14. **內部模組無 raw `import logging` / `import structlog`**（codex iter-1 minor#7）：
    - 規範：app code 用 `from veracrawl.runtime_support.logging import get_logger`，**不直接** import logging / structlog
    - 例外：`src/veracrawl/runtime_support/logging.py` 與 `_log_redaction.py` 自身

15. **CLI 內非合約 print 已遷移（針對 §3.3 列出的 3 個檔）**：
    - grep `print(` 在這 3 個檔，必須**只**是 `print(json.dumps(...))` 形式
    - 其他形式 = 違規

### 既有測試遷移

部分既有測試用 `capsys` 抓 stdout — 合約 print 仍走 stdout，不影響。
若有抓內部進度訊息的測試（CLI 中已遷移的 prints），改為 `caplog.records[*].msg` 或 `caplog.text` 驗證。

## Acceptance Criteria

- [ ] `pyproject.toml` 含 `structlog>=24,<26`
- [ ] `src/veracrawl/runtime_support/logging.py` 存在；export `configure_logging` / `reset_logging` / `get_logger` / `with_correlation_id` / `bootstrap_cli_logging`
- [ ] `src/veracrawl/runtime_support/_log_redaction.py` 存在含 `RedactSensitiveProcessor`
- [ ] §3.3 列出的 3 個 CLI（runtime / live_http / process）內非合約 print **= 0**（只剩 `print(json.dumps(...))` 形式）
- [ ] 30 個 CLI entry point 的 main() 第一行為 `bootstrap_cli_logging(prog=...)`（AST scan boundary test 全綠）
- [ ] §3.4 列出的 3 個內部模組（stdlib_http / tool_gateway / observability）至少有一處 `get_logger(...)` 使用
- [ ] 14 個新 unit + bootstrap + boundary test 全綠
- [ ] 既有測試全綠
- [ ] `caplog` 能截獲 `get_logger(...).info(...)` 訊息
- [ ] `grep -rn "import logging\|import structlog" src/veracrawl/` 命中**僅**在 `runtime_support/logging.py` + `runtime_support/_log_redaction.py`（其他模組透過 `from ... import get_logger`）
- [ ] commit message 描述 why（「logging 基礎建設 + 代表性遷移；29 處 CLI prints 列 P1」）

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
