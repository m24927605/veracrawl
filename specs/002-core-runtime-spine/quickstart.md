# Quickstart: VeraCrawl Target Core Runtime Spine

This quickstart defines the expected developer validation flow after `$speckit-tasks` and implementation. It does not claim full target crawler completion.

## 1. Install Development Environment

```bash
uv sync --python python3.12 --extra dev
```

## 2. Validate Runtime Contract Registry

```bash
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
pytest tests/contract/test_runtime_contract_registry.py
pytest tests/contract/test_runtime_command_event_contracts.py
```

Expected:

- every runtime contract has owner service, schema ref, replay behavior, and tests
- every runtime command resolves to an owner service and event path
- wrong-owner mutation is rejected and evented

## 3. Check Import Boundaries

```bash
uv run --python python3.12 --extra dev pytest tests/contract/test_runtime_import_boundaries.py
```

Expected:

- runtime core does not import concrete agent frameworks, browser libraries, storage clients, queue clients, model SDKs, or site-specific scraper modules
- adapters and fixtures depend inward through VeraCrawl ports and contracts

## 4. Run Objective-To-Output Success Fixture

```bash
uv run --python python3.12 --extra dev veracrawl-runtime run \
  tests/fixtures/runtime-record-success \
  --profile target \
  --out .veracrawl-test-runs/runtime-record-success
```

Expected:

- approved objective, plan, run, source adapter result, artifact refs, normalized document, extraction candidate, evidence packet, verification decision, published output, output manifest, and replay bundle are created
- every required record field has source-backed evidence refs
- replay reports zero missing required refs

## 5. Run Negative Runtime Fixtures

```bash
for fixture in \
  runtime-blocked-source \
  runtime-missing-evidence \
  runtime-verification-conflict \
  runtime-adapter-mismatch \
  runtime-replay-gap \
  runtime-boundary-violation
do
  uv run --python python3.12 --extra dev veracrawl-runtime run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```

Expected:

- no negative fixture produces successful publication
- each negative fixture emits typed failure, blocked, conflict, needs-review, boundary-violation, or replay-incomplete status
- operator-visible diagnostics identify the blocking gate

## 6. Run Agent Recommendation Conformance

```bash
uv run --python python3.12 --extra dev pytest tests/contract/test_agent_recommendation_contracts.py
```

Expected:

- recommendations enter through VeraCrawl contracts and traces
- accepted recommendations become owner-service commands
- framework adapter swaps do not change canonical runtime state

## 7. Run Full Runtime-Spine Gate

```bash
uv run --python python3.12 --extra dev ruff check src tests
uv run --python python3.12 --extra dev mypy src
uv run --python python3.12 --extra dev pytest tests/contract tests/unit tests/integration
```

The local runtime-spine gate should complete within 30 seconds or emit a timing report explaining why fixture complexity, not architectural drift, caused the slower run.

Runtime-spine work is complete only when all checks pass and the implementation still satisfies the constitution, spec, plan, data model, contracts, and quickstart in this directory.
