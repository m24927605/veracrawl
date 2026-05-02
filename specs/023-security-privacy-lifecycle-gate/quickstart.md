# Quickstart: Security Privacy Lifecycle Gate

```sh
uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 veracrawl-security-privacy run \
  tests/fixtures/security-privacy-success \
  --profile target \
  --out .veracrawl-test-runs/security-privacy-success
```

```sh
for fixture in \
  security-privacy-policy-only \
  security-privacy-unsafe-network \
  security-privacy-prompt-injection \
  security-privacy-credential-leakage \
  security-privacy-missing-lifecycle \
  security-privacy-legal-hold-delete \
  security-privacy-missing-projection-cleanup \
  security-privacy-missing-redacted-replay \
  security-privacy-missing-observability
do
  uv run --python python3.12 --extra dev --extra postgres --extra queue-redis --extra object-s3 veracrawl-security-privacy run \
    tests/fixtures/$fixture \
    --profile target \
    --out .veracrawl-test-runs/$fixture
done
```
