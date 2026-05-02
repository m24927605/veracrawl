# Quickstart: VeraCrawl Target Architecture Foundation

This quickstart describes the expected developer flow once implementation tasks are generated and executed. The commands are acceptance targets for `$speckit-tasks` and implementation; they are not yet proof that the runtime exists.

## 1. Create Development Environment

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## 2. Validate Contract Registry

```bash
veracrawl-contracts validate --format json
pytest tests/contract/test_contract_registry.py
```

Expected:

- every foundation contract has owner service, Python model, schema ref, source doc ref, replay flag, and tests
- command payload refs resolve
- event payload refs resolve
- source adapter and agent adapter fixture registrations resolve

## 3. Check Import Boundaries

```bash
pytest tests/contract/test_import_boundaries.py
```

Expected:

- `veracrawl.contracts`, `veracrawl.policy`, `veracrawl.runtime_events`, `veracrawl.ports`, and domain packages do not import `veracrawl.adapters`
- core packages do not import OpenAI Agent SDK, LangChain, LangGraph, CrewAI, AutoGen, Semantic Kernel, browser libraries, storage clients, or queue clients
- adapters import inward through VeraCrawl ports and contracts

## 4. Run Command/Event/Replay Contract Tests

```bash
pytest tests/contract/test_command_event_replay_contracts.py
pytest tests/unit/test_replay_validation.py
```

Expected:

- command results link to emitted event refs
- event sequence is contiguous per run
- replay manifest fails or returns needs-review when required refs are missing
- replay-critical refs survive redaction as stable refs

## 5. Run Source Adapter Conformance

```bash
pytest tests/contract/test_source_adapter_conformance.py
veracrawl-fixture run tests/fixtures/foundation-fetch-like --profile target --out .veracrawl-test-runs/foundation-fetch-like
veracrawl-fixture run tests/fixtures/foundation-non-fetch --profile target --out .veracrawl-test-runs/foundation-non-fetch
veracrawl-fixture run tests/fixtures/foundation-policy-blocked-source --profile target --out .veracrawl-test-runs/foundation-policy-blocked-source
veracrawl-fixture run tests/fixtures/foundation-replay-missing-ref --profile target --out .veracrawl-test-runs/foundation-replay-missing-ref
veracrawl-fixture run tests/fixtures/foundation-missing-evidence --profile target --out .veracrawl-test-runs/foundation-missing-evidence
veracrawl-fixture run tests/fixtures/foundation-adapter-mismatch --profile target --out .veracrawl-test-runs/foundation-adapter-mismatch
```

Expected:

- fetch-like adapters emit natural fetch-like results
- non-fetch adapters emit adapter-native refs and do not fake fetch/page snapshot semantics
- policy-blocked sources record blocked results and do not execute the denied source
- replay-missing-ref and missing-evidence fixtures fail or return needs-review instead of pass
- adapter-mismatch fixtures emit adapter mismatch diagnostics instead of canonicalizing invalid state

## 6. Run Agent Framework Conformance

```bash
pytest tests/contract/test_agent_framework_conformance.py
```

Expected:

- OpenAI Agent SDK fixture maps to VeraCrawl canonical request/result/trace contracts
- LangGraph fixture maps workflow-style state to VeraCrawl canonical request/result/trace contracts
- core remains free of direct framework imports
- mutating tool calls route through `ToolGatewayPort`, `CommandEnvelope`, and `CommandResult`

## 7. Run Full Foundation Gate

```bash
ruff check src tests
mypy src
pytest tests/contract tests/unit tests/integration
```

The local foundation gate should complete within 30 seconds on a normal developer machine. If a slower environment exceeds that target, the run must record timing output and the reason it is not a foundation performance regression.

Foundation work is complete only when all checks pass and the implementation still satisfies the constitution, spec, plan, data model, and contracts in this directory.
