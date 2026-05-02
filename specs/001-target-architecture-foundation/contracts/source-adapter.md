# Contract: Source Adapter Port

Source adapters produce canonical `SourceAdapterResult` records. They do not decide durable state mutations directly and they do not force every source into HTTP fetch semantics.

## Core Port

`veracrawl.ports.source_adapter.SourceAdapterPort`:

```python
class SourceAdapterPort(Protocol):
    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult: ...
```

`SourceAdapterCommand` is a typed command wrapper around:

- `CommandEnvelope`
- `SourceAdapterSpec`
- source ref or seed ref
- policy snapshot ref
- deterministic clock/randomness refs for tests
- optional credential/session scoped refs

## Adapter Types And Natural Results

| Adapter type | Natural result types | Required owner |
| --- | --- | --- |
| `http` | fetch_result, blocked_source | fetch |
| `sitemap` | discovered_links, blocked_source | fetch |
| `rss` | discovered_links, blocked_source | fetch |
| `browser_snapshot` | browser_snapshot, blocked_source | browser |
| `authorized_session` | session_state, blocked_source | control |
| `api_source` | api_payload, blocked_source | fetch |
| `document_source` | document_artifact, blocked_source | normalize |
| `file_import` | file_artifact | artifact_lifecycle |
| `manual_seed` | seed_plan | control |
| `prior_snapshot` | prior_snapshot_ref | control |

Validation:

- `adapter_type` and `result_type` must match the table.
- `status=blocked` requires a policy decision ref with `decision=deny` or `require_review`.
- Fetch-like adapters may reference `FetchAttempt`, `FetchResult`, or `PageSnapshot` only when their natural output supports it.
- Non-fetch adapters must emit adapter-native output refs and must not fake fetch/page snapshot contracts.

## Policy Gate Requirements

Every adapter execution must evaluate:

- source scope
- robots/terms/customer authorization where applicable
- rate and budget
- credential/session policy where applicable
- egress and private network restrictions where applicable
- browser side-effect policy for browser adapters
- artifact privacy classification for document/file adapters

Policy-denied behavior:

- return `SourceAdapterResult.status=blocked`
- set `result_type=blocked_source`
- include policy decision refs
- emit `source_adapter_result_recorded`
- do not attempt the blocked source

## Foundation Fixtures

### Fetch-Like Fixture

Fixture ID: `foundation-fetch-like`

Required behavior:

- uses an `http` or `api_source` adapter stub
- returns `SourceAdapterResult.status=succeeded`
- uses `result_type=fetch_result` or `api_payload`
- includes output refs and replay event refs
- validates idempotency key stability

### Non-Fetch Fixture

Fixture ID: `foundation-non-fetch`

Required behavior:

- uses `manual_seed`, `prior_snapshot`, `document_source`, or `file_import`
- returns the matching natural result type
- does not create fake `FetchResult` or `PageSnapshot`
- includes adapter-native output refs

### Policy-Blocked Fixture

Fixture ID: `foundation-policy-blocked-source`

Required behavior:

- evaluates a deny or require-review policy
- records blocked result and policy decision refs
- proves no source attempt, browser action, credential use, or downstream mutation occurs

## Event Requirements

Every completed adapter invocation must be linked to:

- `command_received`
- `policy_evaluated`
- `source_adapter_result_recorded`
- `command_committed` or `command_rejected`

Failure paths may also emit `error_recorded` or create review/failure refs.

## Negative Tests

Tests must fail when:

- an unknown adapter type is registered
- adapter type and result type are incompatible
- a denied policy still produces a successful result
- a non-fetch adapter emits fetch-only refs
- replay refs omit the source adapter result
- idempotency key is missing or unstable
