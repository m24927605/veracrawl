# Quickstart: Multi-Agent Orchestration And Repair Runtime

Run one success fixture:

```bash
uv run --python python3.12 --extra dev veracrawl-agent-workflow run \
  tests/fixtures/crawl-repair-success \
  --profile target \
  --out .veracrawl-test-runs/crawl-repair-success
```

Run all row 050 fixtures:

```bash
tmpdir=$(mktemp -d)
for fixture in \
  multi-agent-repair-success \
  coordination-arbitration-success \
  repair-loop-evidence-success \
  crawl-repair-success \
  extraction-repair-success \
  owner-service-bypass \
  unresolved-coordination-conflict \
  agent-reasoning-as-evidence \
  multi-agent-missing-agent-model-runtime \
  multi-agent-missing-live-evidence \
  multi-agent-missing-tool-gate \
  multi-agent-missing-owner-command \
  multi-agent-replay-mismatch
do
  uv run --python python3.12 --extra dev veracrawl-agent-workflow run \
    "tests/fixtures/$fixture" \
    --profile target \
    --out "$tmpdir/$fixture"
done
```
