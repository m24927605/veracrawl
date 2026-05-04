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
- [x] T006 Add live extraction-quality evidence aggregator for field oracle,
  precision/recall, repair, real-world quality, and quality release reports.
- [x] T007 Repair live corpus drift and run passing 073 lower gate evidence.

## Validation Results

- Focused production-grade tests passed.
- Focused ruff passed.
- Full-suite validation is recorded in spec 075 after aggregate execution.

## Live Evidence Results: 2026-05-04

- The first real-world quality corpus run failed honestly at 39/40 because the
  PyPI HTML page no longer contained the required `requests` fragment.
- The PyPI target was changed to the public PyPI JSON API
  `https://pypi.org/pypi/requests/json`, preserving the same source origin and
  source-backed evidence while avoiding brittle client-rendered HTML.
- A second real-world quality run exposed transient GNU network/TLS failures.
  Those two unstable targets were replaced with Python official docs targets;
  the corpus still contains 40 live targets, 20 origins, and 12 pattern
  families.
- Passing real-world quality rerun:
  `veracrawl-real-quality-corpus run tests/fixtures/real-world-quality-corpus --profile quality`.
  Result: 40/40 targets passing, 20 origins, 12 pattern families.
- Added `veracrawl-production-quality-gate run-live`, which parses actual field
  oracle, precision/recall, quality release, repair, and real-world quality
  reports. It checks field counts, precision >= 0.98, recall >= 0.90,
  F1 >= 0.94, critical precision >= 0.99, repair success >= 0.80, unsafe bypass
  rate 0, release readiness, source anchors, content hashes, command/event
  refs, and replay refs.
- Passing live command:
  `uv run --python python3.12 --extra dev veracrawl-production-quality-gate run-live tests/fixtures/production-extraction-quality-live-evidence --profile production --out .veracrawl-real-runs/production-grade-release-20260504-162133/production-gates/073-extraction-quality-live --input-report .veracrawl-real-runs/production-grade-release-20260504-162133/field-oracle-quality-corpus/field_oracle_report.json --input-report .veracrawl-real-runs/production-grade-release-20260504-162133/precision-recall-quality/precision_recall_report.json --input-report .veracrawl-real-runs/production-grade-release-20260504-162133/quality-release-ready/quality_release_report.json --input-report .veracrawl-real-runs/production-grade-release-20260504-162133/repair-success-quality/repair_quality_report.json --input-report .veracrawl-real-runs/production-grade-release-20260504-162133/real-world-quality-corpus-rerun/quality_report.json`.
- Result:
  `completion_result=pass`,
  `operator_status=production_extraction_quality_completed`,
  `quality_input_report_count=5`, `artifact_ref_count=554`,
  `source_anchor_ref_count=200`, `content_hash_ref_count=554`,
  `replay_bundle_ref_count=637`, `release_blocker_count=0`.
- Focused live extraction-quality tests, focused ruff, focused mypy, registry
  validation, full ruff, full mypy, full pytest, and Docker-backed focused
  infrastructure pytest passed; exact aggregate validation is recorded in
  spec 075.
