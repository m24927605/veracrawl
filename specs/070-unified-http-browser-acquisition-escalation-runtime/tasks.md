# Tasks: Unified HTTP Browser Acquisition Escalation Runtime

## Implementation

- [x] T001 Define acquisition attempt contract requiring either source-backed
  artifacts/hash/anchors or an explicit source limitation ref.
- [x] T002 Register acquisition command/event coverage.
- [x] T003 Implement HTTP-to-browser escalation attempts in the shared runtime.
- [x] T004 Add positive and source-limited fixture/oracle corpora.
- [x] T005 Add tests proving source-limited cases are needs-review and not
  publication-ready.
- [x] T006 Add live acquisition evidence aggregator for AI/HTTP and Playwright
  browser evidence reports.
- [x] T007 Run live AI/HTTP and Playwright browser validation and feed the
  passing 070 report into 075.

## Validation Results

- Focused production-grade tests passed.
- Focused ruff passed.
- Full-suite validation is recorded in spec 075 after aggregate execution.

## Live Evidence Results: 2026-05-04

- Deterministic browser-quality corpus passed:
  `veracrawl-browser-quality-benchmark run tests/fixtures/browser-quality-corpus --profile quality --browser-adapter deterministic`.
  Result: 8 targets, 8 browser-required passes, 8 recovered fragments.
- Playwright browser-quality corpus passed:
  `uv run --python python3.12 --extra dev --extra browser-playwright veracrawl-browser-quality-benchmark run tests/fixtures/browser-quality-corpus --profile quality --browser-adapter playwright`.
  Result: 8 targets, 8 browser-required passes, 8 recovered fragments.
- Added `veracrawl-acquisition-escalation run-live`, which parses actual
  acquisition evidence reports from the AI/HTTP benchmark, underlying live HTTP
  report, and browser-quality report. It emits acquisition attempts,
  source-backed artifacts, content hashes, source anchors, policy refs,
  command/event/outbox refs, replay refs, and a lower `ProductionGateReport`.
- Passing live command:
  `uv run --python python3.12 --extra dev veracrawl-acquisition-escalation run-live tests/fixtures/production-acquisition-escalation-live-evidence --profile production --out .veracrawl-real-runs/production-grade-release-20260504-162133/production-gates/070-acquisition-live --input-report .veracrawl-real-runs/production-grade-release-20260504-162133/top-ecommerce-ai-agent-corpus-openai/run_report.json --input-report .veracrawl-real-runs/production-grade-release-20260504-162133/top-ecommerce-ai-agent-corpus-openai/real_world/run_report.json --input-report .veracrawl-real-runs/production-grade-release-20260504-162133/browser-quality-playwright/browser_quality_report.json`.
- Result:
  `completion_result=pass`,
  `operator_status=production_acquisition_escalation_completed`,
  `acquisition_input_report_count=3`, `release_blocker_count=0`.
- Source-limited ecommerce product availability cases remain recorded in specs
  066/067 and are not treated as crawlable by this gate.
- Focused live acquisition tests, focused ruff, focused mypy, registry
  validation, full ruff, full mypy, full pytest, and Docker-backed focused
  infrastructure pytest passed; exact aggregate validation is recorded in
  spec 075.
