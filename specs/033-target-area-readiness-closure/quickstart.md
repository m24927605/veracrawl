# Quickstart: Target Area Readiness Impact Closure

Run focused registry tests:

```bash
uv run --python python3.12 --extra dev pytest tests/contract/test_contract_registry.py
```

Validate the registry:

```bash
uv run --python python3.12 --extra dev veracrawl-contracts validate --format json
```
