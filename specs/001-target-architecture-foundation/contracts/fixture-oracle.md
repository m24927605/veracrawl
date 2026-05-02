# Contract: Fixture And Oracle Foundation

The foundation fixture runner validates deterministic local fixtures against explicit oracles. External websites may supplement later testing, but foundation acceptance must not depend on network availability.

## CLI Contract

The implementation must expose:

```text
veracrawl-contracts validate --format json
veracrawl-fixture run tests/fixtures/<fixture_id> --profile target --out .veracrawl-test-runs/<fixture_id>
```

`veracrawl-contracts validate` exits non-zero when registry consistency fails.

`veracrawl-fixture run` exits non-zero when a required fixture manifest, oracle, artifact hash, event sequence, policy decision, or replay ref is missing or invalid.

## Fixture Layout

```text
tests/fixtures/<fixture_id>/
  manifest.yaml
  source/
    server.yaml
    public/
    auth/
    documents/
    api/
  oracles/
    expected_outputs.yaml
    expected_events.yaml
    expected_graph.yaml
    expected_evidence.yaml
    expected_replay.yaml
    expected_dr_restore.yaml
    thresholds.yaml
    failure_injection.yaml
  artifacts/
    expected_hashes.yaml
  README.md
```

Foundation fixtures may leave unused source folders empty, but manifest refs must be explicit and the runner must verify required oracle files exist.

## Required Foundation Fixtures

| Fixture | Purpose | Required pass/fail behavior |
| --- | --- | --- |
| `foundation-fetch-like` | proves fetch-like source adapter result semantics | pass when result, events, artifact hashes, and replay refs match |
| `foundation-non-fetch` | proves non-fetch adapters do not fake fetch artifacts | pass when adapter-native refs match and fetch-only refs are absent |
| `foundation-policy-blocked-source` | proves blocked sources are reported, not bypassed | pass only when blocked result and deny/review policy refs exist |
| `foundation-replay-missing-ref` | proves replay cannot falsely pass with missing refs | must fail or return needs-review, never pass |
| `foundation-missing-evidence` | proves outputs cannot pass without required evidence anchors | must fail or return needs-review, never pass |
| `foundation-adapter-mismatch` | proves incompatible adapter outputs cannot become canonical state | must fail with adapter mismatch diagnostics |

## Required Oracle Contracts

### ExpectedOutputOracle

Required fields:

- `id`
- `fixture_id`
- `expected_output_type`
- `expected_items`
- `required_field_coverage`
- `required_evidence_level`
- `allowed_optional_misses`
- `forbidden_outputs`
- `comparison_mode`

Validation:

- expected items must compare by exact, normalized, or explicitly thresholded tolerance mode
- required evidence levels must resolve to evidence coverage oracle refs
- forbidden outputs must be absent

### ExpectedEvidenceCoverageOracle

Required fields:

- `id`
- `fixture_id`
- `required_anchor_refs`
- `required_artifact_refs`
- `privacy_classification_expectations`
- `required_verification_refs`
- `missing_evidence_behavior`

Validation:

- missing required anchors must fail or return needs-review
- missing evidence must never allow publication or pass status
- redacted evidence must preserve stable refs and privacy classification expectations

### ExpectedEventSequenceOracle

Required fields:

- `id`
- `fixture_id`
- `required_event_types`
- `forbidden_event_types`
- `ordering_constraints`
- `required_payloads`
- `event_cursor_refs`
- `replay_required_event_types`

Validation:

- required event types must be present in order
- forbidden events must be absent
- required payload refs must resolve to registered schemas
- replay-required event types must appear in replay manifest refs

### ExpectedGraphOracle

Required fields:

- `id`
- `fixture_id`
- `expected_nodes`
- `expected_edges`
- `forbidden_edges`
- `expected_projection_watermarks`
- `false_merge_cases`
- `false_split_cases`

Validation:

- expected graph refs must be treated as fixture expectations, not source evidence
- forbidden graph edges must be absent
- graph expectations must not satisfy publication evidence requirements

### FailureInjectionPlan

Required fields:

- `id`
- `fixture_id`
- `injected_failures`
- `expected_failure_records`
- `expected_recovery_actions`
- `expected_dead_letters`
- `expected_events`
- `expected_operator_visible_status`

Validation:

- every injected failure must map to an expected visible failure, recovery, review, or blocked result
- adapter mismatch must identify the adapter type, result type, and canonical contract it failed to satisfy

### DRRestoreOracle

Required fields:

- `id`
- `fixture_id`
- `required_restore_phase_refs`
- `required_backup_manifest_refs`
- `required_validation_gate_refs`
- `expected_report_status`
- `unresolved_ref_behavior`

Validation:

- missing restore phases, backup manifests, or validation gates fail or return needs-review
- this foundation validates oracle shape only and does not implement production DR restore

### ReplayBundleOracle

Required fields:

- `id`
- `fixture_id`
- `required_event_cursor_refs`
- `required_artifact_hash_refs`
- `required_source_adapter_result_refs`
- `required_command_result_refs`
- `required_agent_action_trace_refs`
- `required_model_call_trace_refs`
- `required_tool_call_trace_refs`
- `required_context_bundle_trace_refs`
- `required_policy_decision_refs`
- `expected_missing_ref_behavior`
- `expected_completeness_result`

Validation:

- missing required refs with `fail_replay` must produce `fail`
- missing required refs with `allow_with_gap_report` must produce `needs_review`
- missing required refs must never produce `pass`

### Thresholds

Threshold fields must be explicit when `comparison_mode=tolerance`:

- numeric absolute tolerance
- numeric percent tolerance
- timestamp seconds tolerance
- text normalization rules

Undeclared tolerance is invalid.

## Artifact Hash Rules

All generated artifacts must be compared by stable hash when the fixture declares expected hashes. Redacted artifacts must be compared against redacted stable refs or redacted artifact hashes, not raw secret text.

## Negative Tests

Tests must fail when:

- fixture manifest is missing
- oracle file is missing
- output, evidence, event, graph, failure, DR restore, or replay oracle refs are declared but unresolved
- tolerance mode lacks explicit thresholds
- required event is missing or out of order
- forbidden event appears
- replay manifest passes with missing required refs
- missing evidence still permits publication or pass status
- adapter mismatch is accepted as a canonical VeraCrawl result
- blocked-source fixture attempts the source anyway
- raw credential material appears in generated artifacts, logs, model requests, replay bundles, or fixture output
