# Tasks: Production Extraction Quality And Oracle Runtime

## Implementation

- [x] T001 Register production extraction quality capability in contracts and
  target area coverage.
- [x] T002 Implement `extraction_quality` gate with precision, recall, F1,
  critical precision, evidence packet refs, verification refs, publication gate
  refs, command/event/outbox refs, and replay refs.
- [x] T003 Expose `veracrawl-production-quality-gate`.
- [x] T004 Add extraction quality fixture/oracle corpus.
- [x] T005 Add tests for quality metrics and publication gating refs.

## Validation Results

- Focused production-grade tests passed.
- Focused ruff passed.
- Full-suite validation is recorded in spec 075 after aggregate execution.
