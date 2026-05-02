# Contract: Graph Fixtures

Fixture command:

```text
veracrawl-graph run tests/fixtures/<graph_fixture_id> --profile target --out .veracrawl-test-runs/<graph_fixture_id>
```

Required success fixtures:

| Fixture | Acceptance |
| --- | --- |
| graph-url-hyperlink | URL nodes and hyperlink edges with provenance and replay pass |
| graph-canonical-redirect | canonical and redirect edges with acquisition/canonical provenance |
| graph-page-structure | page type and page structure nodes/edges with site model refs |

Required negative fixtures:

| Fixture | Acceptance |
| --- | --- |
| graph-missing-input | missing input refs fail graph build |
| graph-rebuild-mismatch | rebuild hash mismatch fails graph replay |
| graph-as-evidence | graph evidence substitution is rejected |
