# Quickstart: VeraCrawl Multi-Agent Repair

```sh
uv run --python python3.12 --extra dev pytest \
  tests/contract/test_multi_agent_contract_registry.py \
  tests/contract/test_multi_agent_contracts.py \
  tests/contract/test_multi_agent_import_boundaries.py \
  tests/unit/test_multi_agent_orchestration.py \
  tests/unit/test_multi_agent_repair_boundary.py \
  tests/unit/test_multi_agent_replay.py \
  tests/integration/test_multi_agent_fixtures.py
```

```sh
for fixture in \
  multi-agent-repair-success \
  coordination-arbitration-success \
  repair-loop-evidence-success \
  owner-service-bypass \
  unresolved-coordination-conflict \
  agent-reasoning-as-evidence
do
  uv run --python python3.12 --extra dev veracrawl-agent-workflow run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```
