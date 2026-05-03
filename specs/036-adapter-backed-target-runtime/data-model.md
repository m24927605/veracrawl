# Data Model: VeraCrawl Adapter-Backed Target Runtime

## TargetAdapterBackedSourceEntry

Fields:

- `id`: stable entry id
- `corpus_entry_ref`: source corpus entry id
- `adapter_type`: canonical VeraCrawl adapter type
- `adapter_spec_ref`: source adapter spec ref
- `adapter_source_ref`: adapter source ref
- `policy_decision_ref`: adapter policy decision ref
- `expected_output_ref`: optional expected adapter output ref
- `expected_content_hash_ref`: optional replay hash oracle
- `require_source_adapter_result`: true by default
- `allow_direct_source_fallback`: false by default
- `policy_denied`: negative fixture flag

Validation:

- Adapter-backed entries require adapter spec, adapter source, and policy refs.
- Passing entries must require source adapter result refs.
- Direct source fallback is invalid unless explicitly declared for a negative fixture.

## TargetAdapterBackedSourceManifest

Fields:

- `id`
- `fixture_id`
- `entries`
- `required_adapter_types`
- `expected_adapter_result_count`
- `policy_decision_refs`
- `replay_oracle_ref`
- `allow_direct_source_fallback`

Validation:

- Corpus entry refs must be unique.
- Passing manifests require at least one adapter type and expected adapter result count.
- Direct source fallback defaults to blocked.

## TargetAdapterBackedSourceRecord

Fields:

- `id`
- `run_ref`
- `corpus_entry_ref`
- `adapter_type`
- `source_adapter_result_ref`
- `adapter_output_refs`
- `adapter_policy_decision_refs`
- `adapter_replay_refs`
- `source_observation_ref`
- `content_hash_ref`
- `direct_source_bypass_refs`
- `missing_adapter_result_refs`
- `adapter_output_mismatch_refs`
- `policy_denied_refs`
- `replay_mismatch_refs`
- `result`

Validation:

- Passing records require source adapter result, adapter output, policy, replay, source observation, and content hash refs.
- Passing records cannot include bypass, missing adapter, mismatch, policy denied, or replay mismatch diagnostics.
- Failing records require at least one typed diagnostic ref.

## TargetRuntimeReport Extensions

New aggregate fields:

- `adapter_backed_source_refs`
- `source_adapter_result_refs`
- `adapter_output_refs`

Validation:

- Generic target completion does not require these fields.
- Adapter-backed fixtures require them through fixture manifest expectations and CLI checks.
