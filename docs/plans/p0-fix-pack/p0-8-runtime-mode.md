# P0-8: Runtime Mode（區分 prod vs fixture）

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

`src/veracrawl/runtime_support/{observability,disaster_recovery,security_privacy,infrastructure_gate}.py` 全部用 `if scenario in _FAILURES` 做 scenario 字串查表，回 hardcoded refs。這設計在 fixture-driven 測試環境合理，但：

- **生產環境下沒有 fixture scenario 名** → 整個 gate 默默走 `runtime_unavailable` 分支
- 用戶看到 ref report 以為 gate 通過，實際上 **所有 production runtime 路徑都是空殼**
- 這是 review 中第二大共識結論（僅次於 "fixture-in-src" 反 pattern）

舉例（`runtime_support/observability.py:103-128`）：

```python
def run_observability_gate(scenario: str) -> ObservabilityGateReport:
    if scenario in _KNOWN_FAILURES:
        return _FAILURES[scenario]
    return ObservabilityGateReport(...)  # 默默回 "通過" 但完全沒做事
```

## Scope

**In scope:**

- 新增：`src/veracrawl/runtime_support/runtime_mode.py` — `RuntimeMode` enum + `current_mode()` helper
- 修改：4 個 gate 檔案 — observability / disaster_recovery / security_privacy / infrastructure_gate
- 環境變數：`VERACRAWL_RUNTIME_MODE`（`fixture` | `production`，預設 `fixture` 維持向後相容）
- 對應的 boundary / integration tests

**Out of scope:**

- 真正接 OTel / Prometheus / 真實 DR backend（屬 P1-6 / 各自獨立 epic）
- 把所有 `*_runtime` 模組都加 mode（先聚焦 4 個 gate）
- Per-call mode override（先全域 env var）

## Design

### `runtime_mode.py`

```python
# src/veracrawl/runtime_support/runtime_mode.py
import os
from enum import StrEnum
from contextvars import ContextVar

class RuntimeMode(StrEnum):
    FIXTURE = "fixture"           # 測試 / contract demo / fixture replay
    PRODUCTION = "production"     # 真實生產；未實作的 path 必須顯式 raise

_DEFAULT_MODE = RuntimeMode.FIXTURE
_mode_var: ContextVar[RuntimeMode | None] = ContextVar("runtime_mode", default=None)

def current_mode() -> RuntimeMode:
    """讀取當前 runtime mode。優先順序：
    1. ContextVar（用 with_runtime_mode 注入）
    2. 環境變數 VERACRAWL_RUNTIME_MODE
    3. 預設 FIXTURE（向後相容）
    """
    cv = _mode_var.get()
    if cv is not None:
        return cv
    env = os.getenv("VERACRAWL_RUNTIME_MODE")
    if env:
        try:
            return RuntimeMode(env.lower())
        except ValueError:
            raise ValueError(
                f"VERACRAWL_RUNTIME_MODE={env!r} invalid; "
                f"expected one of: {[m.value for m in RuntimeMode]}"
            )
    return _DEFAULT_MODE

class with_runtime_mode:
    """Context manager 注入 runtime mode 至當前 contextvar。

    用於測試 / 細粒度控制；prod 應走環境變數。
    """
    def __init__(self, mode: RuntimeMode):
        self._mode = mode
        self._token = None

    def __enter__(self):
        self._token = _mode_var.set(self._mode)
        return self._mode

    def __exit__(self, *args):
        _mode_var.reset(self._token)


class ProductionRuntimeNotImplemented(NotImplementedError):
    """RuntimeMode.PRODUCTION 下，未實作的 backend path 必須拋此錯誤。"""

    def __init__(self, *, backend: str, gate: str):
        self.backend = backend
        self.gate = gate
        super().__init__(
            f"production backend {backend!r} not implemented for {gate!r}; "
            f"set VERACRAWL_RUNTIME_MODE=fixture for contract testing or "
            f"implement the production path"
        )
```

### Gate 檔案改造模板

對 4 個 gate 套用同一模板（以 observability 為例）：

```python
# src/veracrawl/runtime_support/observability.py
from veracrawl.runtime_support.runtime_mode import (
    RuntimeMode, current_mode, ProductionRuntimeNotImplemented,
)

def run_observability_gate(scenario: str | None = None) -> ObservabilityGateReport:
    mode = current_mode()

    if mode is RuntimeMode.FIXTURE:
        # 既有 fixture 行為原樣保留
        if scenario in _KNOWN_FAILURES:
            return _FAILURES[scenario]
        return ObservabilityGateReport(...)  # fixture pass

    # mode is PRODUCTION
    raise ProductionRuntimeNotImplemented(
        backend="observability",
        gate="run_observability_gate",
    )
```

對所有原本「scenario lookup → 回 hardcoded report」的入口同樣處理。

**列出需改的入口**（開工前 grep 確認完整清單）：

- `runtime_support/observability.py`：
  - `run_observability_gate`
  - `evaluate_telemetry_pipeline`
  - 其他入口
- `runtime_support/disaster_recovery.py`：
  - `dr_restore_plan`
  - `evaluate_dr_drill`
  - 其他
- `runtime_support/security_privacy.py`：
  - `enforce_pii_policy`
  - 其他
- `runtime_support/infrastructure_gate.py`：
  - `run_infrastructure_gate`
  - 其他

每個入口都加 mode check。

### `__init__.py` 補 export

`src/veracrawl/runtime_support/__init__.py`：

```python
from veracrawl.runtime_support.runtime_mode import (
    RuntimeMode,
    current_mode,
    with_runtime_mode,
    ProductionRuntimeNotImplemented,
)
```

### 為何不直接刪 fixture path

爬蟲 / LLM reviewer 都認為「fixture 走原路徑」是合理的，因為：

1. 既有 377 個測試檔仰賴 fixture mode 跑通
2. Codex review gate 自身也是 contract-based，需要 fixture 模式
3. 一次刪光 = 全 codebase 紅 → 卡住 P0 進度

mode 是漸進過渡：未來 P1 / P2 真實實作 backend 時，PRODUCTION 路徑逐步補上，FIXTURE 可保留作為 contract test 模式。

## Dependencies

無新依賴。

## Test Strategy

### 既有測試必須不破

預設 `VERACRAWL_RUNTIME_MODE` 不設 → `current_mode()` 回 `FIXTURE` → 既有行為完全一致。

```bash
pytest tests/runtime_support/ tests/contract/
```

### 新增 unit tests（`tests/runtime_support/test_runtime_mode.py`）

1. **預設 mode 為 FIXTURE**
   - 不設 env var、不用 with_runtime_mode → `current_mode() == RuntimeMode.FIXTURE`

2. **env var 覆蓋**
   - `monkeypatch.setenv("VERACRAWL_RUNTIME_MODE", "production")` → `RuntimeMode.PRODUCTION`
   - `"fixture"` / `"FIXTURE"` 都應接受（case-insensitive）
   - `"invalid"` → raise ValueError

3. **with_runtime_mode 覆蓋 env var**
   - 設 env=PRODUCTION
   - `with with_runtime_mode(RuntimeMode.FIXTURE):` → 內為 FIXTURE
   - 退出後 → 回 PRODUCTION

4. **巢狀 with_runtime_mode**
   - 外 PRODUCTION → 內 FIXTURE → 內 PRODUCTION → 退出三層回原始

### 新增 gate behavior tests（4 個 gate 各一個檔）

`tests/runtime_support/test_observability_gate_modes.py`：

5. **FIXTURE mode 行為（向後相容）**
   - `with with_runtime_mode(RuntimeMode.FIXTURE):` 跑既有 scenario lookup
   - 已知 failure scenario → 回對應 fixture report
   - 已知 success scenario → 回 fixture pass

6. **PRODUCTION mode raise NotImplementedError**
   - `with with_runtime_mode(RuntimeMode.PRODUCTION):` 呼叫 gate
   - 預期：raise `ProductionRuntimeNotImplemented`
   - assert error.backend == "observability"
   - assert error.gate == "run_observability_gate"
   - assert "fixture" in str(error) — 提示用戶可切回 fixture

7-10. 對 disaster_recovery / security_privacy / infrastructure_gate 各做 5 + 6 兩個 case。

### Boundary test

新增 `tests/contract/test_runtime_support_mode_check.py`：

確保 4 個 gate 檔案的每個 public function 都有 mode check（不要漏）。可以用 AST 解析：

```python
import ast
from pathlib import Path

GATE_FILES = [
    "src/veracrawl/runtime_support/observability.py",
    "src/veracrawl/runtime_support/disaster_recovery.py",
    "src/veracrawl/runtime_support/security_privacy.py",
    "src/veracrawl/runtime_support/infrastructure_gate.py",
]

def _has_current_mode_call(func: ast.FunctionDef) -> bool:
    for node in ast.walk(func):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "current_mode":
            return True
    return False

def test_all_gate_entrypoints_check_mode():
    offenders = []
    for path in GATE_FILES:
        tree = ast.parse(Path(path).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith("_"):
                if not _has_current_mode_call(node):
                    offenders.append(f"{path}:{node.name}")
    assert not offenders, f"public gate functions missing current_mode() check: {offenders}"
```

注意：上面 AST 檢查可能誤報（例如 helper public function 不需要 mode check）。可加 `# noqa: runtime-mode` 標記豁免。如過度誤報則改用 grep-based 檢查或人工審查。

## Acceptance Criteria

- [ ] `src/veracrawl/runtime_support/runtime_mode.py` 存在，export `RuntimeMode` / `current_mode` / `with_runtime_mode` / `ProductionRuntimeNotImplemented`
- [ ] 4 個 gate 檔案的所有 public 入口都呼叫 `current_mode()`
- [ ] env var `VERACRAWL_RUNTIME_MODE` 不設時，所有既有測試行為一致（fixture）
- [ ] env var 設 `production` 時，gate 入口 raise `ProductionRuntimeNotImplemented`
- [ ] 新 unit test（runtime_mode 4 個 + 4 個 gate × 2 case = 12 個）全綠
- [ ] 新 boundary test 全綠
- [ ] 既有測試全綠
- [ ] commit message 描述 why（特別「fixture path 默默通過 = 信任崩塌」）

## Rollback

- 如果 boundary test 對 helper public function 誤報太多：
  - 改成 list-based explicit allowlist（哪些函式必須有 mode check）
  - 或加 `# noqa: runtime-mode` 標記豁免
- 如果某些 fixture-mode 路徑因為改動而行為微變：
  - **檢查並修正**，不放寬 mode check
  - 預設應該完全等價

## Open Questions

- **Q1**：mode 是否要支援 `staging` / `canary` 等中間模式？
  - 建議：不要。`fixture` / `production` 二元已足；中間模式列 P1 評估

- **Q2**：是否要在 logger（P0-5）加 `runtime_mode` 至每個 log entry？
  - 建議：**加**。在 `logging.py` 的 processor 中讀 `current_mode()` 寫入。debug 體感大幅提升

- **Q3**：CLI 入口要不要強制讀 env var 並 fail-fast 印出 mode？
  - 建議：CLI bootstrap 開頭印 `mode=fixture/production` 一行，方便用戶確認。但不 fail-fast（fixture 是合法預設）

- **Q4**：是否要 ContextVar + env var 之外，再支援 config file（toml）？
  - 建議：**不要**。等 P1-2（pydantic-settings 集中 Settings）一起處理
