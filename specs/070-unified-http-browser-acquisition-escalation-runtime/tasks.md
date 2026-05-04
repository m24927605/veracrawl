# Tasks: Unified HTTP Browser Acquisition Escalation Runtime

## Implementation

- [x] T001 Define acquisition attempt contract requiring either source-backed
  artifacts/hash/anchors or an explicit source limitation ref.
- [x] T002 Register acquisition command/event coverage.
- [x] T003 Implement HTTP-to-browser escalation attempts in the shared runtime.
- [x] T004 Add positive and source-limited fixture/oracle corpora.
- [x] T005 Add tests proving source-limited cases are needs-review and not
  publication-ready.

## Validation Results

- Focused production-grade tests passed.
- Focused ruff passed.
- Full-suite validation is recorded in spec 075 after aggregate execution.
