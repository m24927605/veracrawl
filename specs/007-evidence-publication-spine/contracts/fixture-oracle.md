# Contract: Evidence Publication Fixtures

Fixture command:

```text
veracrawl-evidence run tests/fixtures/<evidence_fixture_id> --profile target --out .veracrawl-test-runs/<evidence_fixture_id>
```

Required success fixtures:

| Fixture | Acceptance |
| --- | --- |
| evidence-field-coverage | field anchors cover all required fields and publication is not attempted |
| evidence-verification-review | accepted verification and review decisions are emitted |
| evidence-publication-success | output manifest and published output are emitted only after all gates pass |

Required negative fixtures:

| Fixture | Acceptance |
| --- | --- |
| evidence-missing-anchor | incomplete evidence coverage blocks publication |
| evidence-verification-conflict | conflict verification blocks publication |
| evidence-policy-denied | publication policy denial blocks publication |
| evidence-replay-gap | missing replay refs block publication |
| evidence-candidate-direct-publication | direct candidate publication is rejected |

Every fixture must include `manifest.yaml`, expected output, event, evidence,
replay, and threshold oracles. Negative fixtures must never emit output manifest
or published output refs.
