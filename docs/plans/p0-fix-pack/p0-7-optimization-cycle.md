# P0-7: 打破 optimization 循環依賴

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

`src/veracrawl/optimization/objective_evidence.py:16-49` 從多個下游模組 import 函式：
- `extract/optimization_integration.py`
- `normalize/optimization_integration.py`
- `graph/optimization_integration.py`
- `publish/optimization_integration.py`
- `scheduler/optimization_integration.py`
- `ops/optimization_integration.py`

而這些下游模組的 `optimization_integration.py` **反向 import** `veracrawl.optimization.runtime`：

```python
# src/veracrawl/extract/optimization_integration.py:6
from veracrawl.optimization.runtime import RuntimeDomExtractionResult
```

形成 `optimization → extract → optimization` 的循環。Python 因為函式級 import 暫時還能跑，但這破壞了 hexagonal 的層級單向流向 — `optimization/` 應該是 high-level orchestrator，不該被低階模組參照其 runtime types。

## Scope

**In scope:**

- 新增：`src/veracrawl/contracts/optimization_runtime.py` — 抽出共用 type
- 修改：`src/veracrawl/optimization/runtime.py` — 改 import contracts；可保留 re-export 為 backward compat
- 修改：6 個下游 `*/optimization_integration.py` — 改 import contracts，不再 import optimization
- 新增：`tests/contract/test_optimization_no_downstream_import.py` — boundary test

**Out of scope:**

- `optimization/runtime.py` (818 行) 拆檔（屬架構面，列 P1）
- `objective_evidence.py` 從 src/ 移到 tests/fixtures/（屬 P1-7）
- 統一 ReleaseGate Protocol（屬 P1-8）

## Design

### Step 1：盤點需要抽出的 types

開工第一步：

```bash
grep -h "from veracrawl.optimization.runtime import" \
    src/veracrawl/{extract,graph,normalize,publish,scheduler,ops}/optimization_integration.py
```

預期會看到一組 type names，例如：
- `RuntimeDomExtractionResult`
- `RuntimeDedupeRankingResult`
- `RuntimeFrontierScoreResult`
- `RuntimeCanonicalizationResult`
- ...

把這些 type 都抽到 `contracts/optimization_runtime.py`。

### Step 2：建立 `contracts/optimization_runtime.py`

```python
# src/veracrawl/contracts/optimization_runtime.py
"""
Optimization runtime 跨模組 type 定義。

這些 type 被 optimization 模組產出，並被下游（extract / normalize / graph / publish /
scheduler / ops）的 optimization_integration.py 消費。把 type 放在 contracts 是為了：
1. 打破 optimization → 下游 → optimization 的循環依賴
2. 維持 hexagonal 紀律：types 是 contract，不是 implementation
"""

from pydantic import BaseModel
# 從原 optimization/runtime.py 搬過來的 type 定義
class RuntimeDomExtractionResult(BaseModel):
    ...

class RuntimeDedupeRankingResult(BaseModel):
    ...

# ... 其他被下游 import 的 type
```

### Step 3：`optimization/runtime.py` 改 import + 保留 re-export

```python
# src/veracrawl/optimization/runtime.py
from veracrawl.contracts.optimization_runtime import (
    RuntimeDomExtractionResult,
    RuntimeDedupeRankingResult,
    # ...
)

# 為了不破壞當前內部呼叫端，re-export
__all__ = [
    "RuntimeDomExtractionResult",
    "RuntimeDedupeRankingResult",
    # ...
]

# 其他 optimization runtime 邏輯保留
def run_optimization(...):
    ...
```

不刪 `optimization/runtime.py` 內的 type 別名，因為仍有同模組內函式 reference。但 source of truth 已遷至 contracts。

### Step 4：下游 `*/optimization_integration.py` 改 import

`src/veracrawl/extract/optimization_integration.py`：

```python
# Before:
# from veracrawl.optimization.runtime import RuntimeDomExtractionResult

# After:
from veracrawl.contracts.optimization_runtime import RuntimeDomExtractionResult
```

對 6 個 integration 檔案重複此修改。

### Step 5：Boundary test

新增 `tests/contract/test_optimization_no_downstream_import.py`：

```python
import re
from pathlib import Path

DOWNSTREAM_MODULES = ["extract", "graph", "normalize", "publish", "scheduler", "ops"]

def test_downstream_modules_do_not_import_optimization():
    """Downstream modules must depend on contracts/, not optimization/, to avoid circular deps."""
    src = Path("src/veracrawl")
    pattern = re.compile(r"^\s*from\s+veracrawl\.optimization\.|^\s*import\s+veracrawl\.optimization\.", re.MULTILINE)

    offenders = []
    for module in DOWNSTREAM_MODULES:
        module_dir = src / module
        for py_file in module_dir.rglob("*.py"):
            content = py_file.read_text()
            for m in pattern.finditer(content):
                line_no = content[:m.start()].count("\n") + 1
                offenders.append(f"{py_file}:{line_no}: {m.group(0).strip()}")

    assert not offenders, (
        "Downstream modules must not import veracrawl.optimization.* "
        "(use veracrawl.contracts.optimization_runtime instead). "
        f"Offenders:\n{chr(10).join(offenders)}"
    )
```

### Step 6：保留 re-export 的合理性

不刪 `optimization/runtime.py` 內的 import-from-contracts re-export，因為：
- 該模組內的其他函式 reference 這些 types（不想全檔大改）
- 漸進遷移：未來 P1 可以一併把 `optimization/runtime.py` 拆檔時再清理

## Dependencies

無新依賴。

## Test Strategy

### 既有測試必須不破

```bash
pytest tests/optimization/ tests/extract/ tests/graph/ tests/normalize/ \
       tests/publish/ tests/scheduler/ tests/ops/ tests/contract/
```

特別是 `tests/contract/test_*_import_boundaries.py` 中現有 097-feature 的 boundary test 必須仍綠（這是好的紀律）。

### 新增 boundary test

如 Step 5 所述：`test_downstream_modules_do_not_import_optimization`。

### 新增 integration smoke test

確認 re-export 沒漏：

```python
# tests/contract/test_optimization_runtime_reexport.py
def test_optimization_runtime_reexports_contract_types():
    from veracrawl.optimization.runtime import RuntimeDomExtractionResult as ReExported
    from veracrawl.contracts.optimization_runtime import RuntimeDomExtractionResult as Source
    assert ReExported is Source
```

對所有抽出的 type 都做一次 identity check（防止抄漏）。

### Mypy 應該也能抓到循環

跑：
```bash
mypy src/veracrawl/optimization/ src/veracrawl/extract/optimization_integration.py
```

理論上 mypy 對循環 import 有報告（雖然 Python 函式級 import 能 work）。

## Acceptance Criteria

- [ ] `src/veracrawl/contracts/optimization_runtime.py` 存在，包含所有跨模組共用 type
- [ ] `grep "from veracrawl.optimization" src/veracrawl/{extract,graph,normalize,publish,scheduler,ops}/` = 0
- [ ] `grep "from veracrawl.contracts.optimization_runtime" src/veracrawl/{extract,graph,normalize,publish,scheduler,ops}/optimization_integration.py` 在 6 個檔都命中
- [ ] 新 boundary test `test_downstream_modules_do_not_import_optimization` 全綠
- [ ] 新 reexport identity test 全綠
- [ ] 既有測試全綠
- [ ] `pytest tests/contract/test_*_import_boundaries.py` 全綠
- [ ] commit message 描述 why（特別循環依賴）

## Rollback

- 如果發現抽出的 type 有 method 牽動其他 implementation（不只 data class）：
  - 該 type 拆成 `contracts/...Spec`（pure data） + `optimization/...Result`（含行為），下游只 import Spec
- 如果 boundary test 太嚴卡到既有測試：
  - 不放寬 test，而是修被卡的程式碼
  - 連續 3 次 fix 都卡住 → 在 STATUS.md 記 BLOCKED 原因，停手通知用戶

## Open Questions

- **Q1**：`contracts/optimization_runtime.py` 命名 vs `contracts/optimization.py`？
  - 既有 `contracts/crawler_optimization.py` 已存在 → 為避免混淆，用 `optimization_runtime.py`
  - 建議：保持 `optimization_runtime.py`

- **Q2**：要不要趁這個 P0 把 `optimization/runtime.py` 818 行也拆？
  - **不要**。屬於架構面 refactor，scope creep
  - 列 P1：`optimization/{frontier,dom,dedupe,canonicalization}.py`

- **Q3**：抽出的 type 是否要連同函式 helpers 一起抽？
  - 只抽 type（data class）。helpers 留在 `optimization/runtime.py`
  - 下游需要 helper 時，從 `optimization/` 透過某個 port 介面取，不要直接 import
  - 但這個改動超出 scope，列 P1

- **Q4**：boundary test 是否應該禁止 `tests/` 內 import optimization？
  - 不應該。tests 可以自由 import，只規範 src 內的層級流向
