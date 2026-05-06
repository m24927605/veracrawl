# P0-5: Structured Logging

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

- `grep "import logging\|import structlog" src/` = **0 命中**
- CLI / 內部模組用 `print()` **129 處**
- 生產環境無 structured logs、無 correlation id、無 log level、無 sink 抽象
- 事故根本無法事後追查；一旦 prod 出問題只能盲改

## Scope

**In scope:**

- `pyproject.toml` — 新增 `structlog`
- 新增：`src/veracrawl/runtime_support/logging.py` — `configure_logging()` + `get_logger()` + `with_correlation_id()`
- 替換內部模組所有 `print()` → `logger.<level>(...)`
- 在 runtime / agent / adapter 入口注入 `correlation_id` 至 contextvar
- env var：`VERACRAWL_LOG_LEVEL`（預設 `INFO`）、`VERACRAWL_LOG_FORMAT`（預設 `json`，可 `console`）

**Out of scope:**

- OTel 整合（屬 P1-6）
- Log shipping / aggregator（Loki / Datadog）
- per-module log level config（先全域，列 P1）
- log redaction filter（與 P0-3 / P0-4 自帶 redaction 不重複；列 P1 集中）

## Design

### 替換範圍

**必改（內部模組）**：
```
src/veracrawl/adapters/
src/veracrawl/agents/
src/veracrawl/browser/
src/veracrawl/fetch/
src/veracrawl/extract/
src/veracrawl/optimization/
src/veracrawl/normalize/
src/veracrawl/evidence/
src/veracrawl/publish/
src/veracrawl/graph/
src/veracrawl/graph_memory/
src/veracrawl/memory/
src/veracrawl/scheduler/
src/veracrawl/runtime_support/
src/veracrawl/runtime_events/
src/veracrawl/target_runtime/
```

**保留 print()**（CLI 入口顯示給用戶）：
- `src/veracrawl/cli/*.py` 的 main() / handler 函式對「給 user 看」的 stdout 訊息可保留 print
- 但 internal 函式仍要用 logger

驗收用 `grep -r "print(" src/veracrawl/{adapters,agents,browser,fetch,extract,optimization,normalize,evidence,publish,graph,graph_memory,memory,scheduler,runtime_support,runtime_events,target_runtime}/` = 0

### Logger 模組

```python
# src/veracrawl/runtime_support/logging.py
import logging
import os
import sys
import structlog
from contextvars import ContextVar
from typing import Any

_correlation_id_var: ContextVar[str | None] = ContextVar("correlation_id", default=None)

def _add_correlation_id(_, __, event_dict: dict[str, Any]) -> dict[str, Any]:
    cid = _correlation_id_var.get()
    if cid is not None:
        event_dict["correlation_id"] = cid
    return event_dict

def configure_logging() -> None:
    level_name = os.getenv("VERACRAWL_LOG_LEVEL", "INFO").upper()
    log_format = os.getenv("VERACRAWL_LOG_FORMAT", "json").lower()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stderr,
        level=level,
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        _add_correlation_id,
    ]

    if log_format == "console":
        processors.append(structlog.dev.ConsoleRenderer(colors=sys.stderr.isatty()))
    else:
        processors.append(structlog.processors.format_exc_info)
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )

def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)

class with_correlation_id:
    """Context manager 設定當前 correlation_id 至 contextvar。"""
    def __init__(self, cid: str):
        self._cid = cid
        self._token = None
    def __enter__(self):
        self._token = _correlation_id_var.set(self._cid)
        return self._cid
    def __exit__(self, *args):
        _correlation_id_var.reset(self._token)
```

### 入口注入 correlation_id

每個 runtime entry / CLI command / agent run 開始時：

```python
import uuid
from veracrawl.runtime_support.logging import with_correlation_id, get_logger

logger = get_logger(__name__)

def run_something(...):
    cid = str(uuid.uuid4())
    with with_correlation_id(cid):
        logger.info("run_started", target=...)
        ...
```

呼叫鏈下游無需改動，contextvar 自動跟隨（含 thread / async task）。

### CLI bootstrap

每個 CLI entry 第一行呼叫 `configure_logging()`：

```python
# src/veracrawl/cli/<any>.py
from veracrawl.runtime_support.logging import configure_logging

def main():
    configure_logging()
    ...
```

可以在 `cli/__init__.py` 提供 `bootstrap()` 統一處理。

### print() 替換規則

按訊息語意分類：

| 原 print 內容 | 改成 |
|---|---|
| 進度 / debug 資訊 | `logger.info(event="...", **kv)` |
| 錯誤 / 警告 | `logger.warning(...)` / `logger.error(...)` |
| 成功訊息 | `logger.info(...)` |
| 對 user 直接輸出（CLI stdout） | 保留 print，但限縮在 `cli/` 入口 |
| 報表 dump（JSON / table） | 保留 print（給 user 看的）|

### 替換策略

不要一次全改。建議：

1. 先寫 `logging.py` + 1 個示範模組替換 + tests（一個 commit）
2. 然後分批替換各模組（每個資料夾一個 commit，方便 review）
3. 最後寫 boundary test 強制 grep = 0（一個 commit）

但全部完成後仍計為 P0-5 一個 P0 完成項。

## Dependencies

| Package | Status | Justification |
|---------|--------|---------------|
| `structlog` | NEW | structured + contextvar + JSON formatter；stdlib `logging` 自寫 contextvar processor 易錯 |

## Test Strategy

### 既有測試必須不破

```bash
pytest tests/
```

特別注意：如果有測試 `capsys`/`capfd` 抓 stdout 驗證 print 訊息，需更新為 `caplog`（pytest 內建）抓 log。

### 新增 unit tests（`tests/runtime_support/test_logging.py`）

1. **JSON format 預設**
   - `VERACRAWL_LOG_FORMAT` 不設
   - `configure_logging()` 後 logger.info("x", k=1) → stderr 收到 valid JSON 含 `"event": "x"`、`"k": 1`、`"timestamp": ...`

2. **Console format**
   - `VERACRAWL_LOG_FORMAT=console`
   - 輸出非 JSON（含 ANSI / human readable）

3. **Log level 過濾**
   - `VERACRAWL_LOG_LEVEL=ERROR`
   - logger.info("x") → 無輸出
   - logger.error("y") → 有輸出

4. **correlation_id contextvar**
   - `with with_correlation_id("abc"): logger.info("x")` → output 含 `"correlation_id": "abc"`
   - context 結束後 logger.info("y") → output 不含 correlation_id

5. **巢狀 with_correlation_id**
   - `with with_correlation_id("a"):` 內 `with with_correlation_id("b"):` → 內層為 "b"
   - 退出內層 → 回到 "a"
   - 退出外層 → 無

6. **Async correlation_id 跟隨**
   - 啟動 async task → task 內 logger.info → 帶外層 correlation_id

### Boundary test（新增）

`tests/contract/test_no_print_in_internal_modules.py`：

```python
from pathlib import Path
import re
INTERNAL = ["adapters", "agents", "browser", "fetch", "extract", "optimization",
            "normalize", "evidence", "publish", "graph", "graph_memory",
            "memory", "scheduler", "runtime_support", "runtime_events", "target_runtime"]

def test_no_print_in_internal_modules():
    src = Path("src/veracrawl")
    pattern = re.compile(r"^\s*print\(", re.MULTILINE)
    offenders = []
    for module in INTERNAL:
        for py_file in (src / module).rglob("*.py"):
            content = py_file.read_text()
            for m in pattern.finditer(content):
                line_no = content[:m.start()].count("\n") + 1
                offenders.append(f"{py_file}:{line_no}")
    assert not offenders, f"print() found in internal modules: {offenders}"
```

### Logger usage smoke test

新增 `tests/runtime_support/test_logging_smoke.py`：

```python
def test_get_logger_returns_bound_logger():
    log = get_logger("veracrawl.test")
    assert hasattr(log, "info")
    assert hasattr(log, "bind")
```

## Acceptance Criteria

- [ ] `structlog` 在 pyproject.toml dependencies
- [ ] `src/veracrawl/runtime_support/logging.py` 存在且 export `configure_logging` / `get_logger` / `with_correlation_id`
- [ ] `grep -r "import logging\|import structlog" src/` 命中數 > 0（合理數量，預期 ≥ 30）
- [ ] `grep -r "print(" src/veracrawl/{adapters,agents,browser,fetch,extract,optimization,normalize,evidence,publish,graph,graph_memory,memory,scheduler,runtime_support,runtime_events,target_runtime}/` = **0**
- [ ] 6 個新 unit test 全綠
- [ ] 新 boundary test 全綠
- [ ] 既有 test 全綠
- [ ] commit message 描述 why（特別 129 處 print → 0）

## Rollback

- 如果 structlog 在某些 async 場景與 contextvar 互動有問題：
  - 改用 stdlib `logging` + 自寫 `LoggerAdapter` 帶 contextvar
  - 缺點：失去 processor pipeline，要自己拼 JSON renderer
- 如果替換 print 破壞既有 capsys-based test：
  - 該測試改用 caplog
  - 不要倒退把 logger 改回 print

## Open Questions

- **Q1**：CLI 入口的 print（給 user 看）要不要也走 logger（用 special "user" level）？
  - 建議：**不要**。User-facing output 跟 internal log 是兩件事；混在一起反而難閱讀

- **Q2**：log 是否要寫檔（rotating file handler）？
  - 建議：**不要**。容器化環境 stdout/stderr 即是 log；寫檔屬於 deploy 層責任

- **Q3**：要不要支援 `VERACRAWL_LOG_PRETTY=1` 在 prod 也能切 console format？
  - 建議：用 `VERACRAWL_LOG_FORMAT=console` 即可，不需額外 flag

- **Q4**：分批 commit（每個資料夾一個）vs 一次 commit 全替換？
  - 建議：分批（5-7 個 commit），每個 commit 對應一個資料夾，方便 codex task review。但完成後標記同一個 P0-5 done
