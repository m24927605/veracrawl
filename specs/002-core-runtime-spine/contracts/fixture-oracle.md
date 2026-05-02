# Contract: Runtime Fixture Oracle

## Purpose

Define deterministic success and negative fixture expectations for the runtime spine.

## Fixture Set

| Fixture | Expected outcome | Required proof |
| --- | --- | --- |
| runtime-record-success | pass | published output manifest and replay-complete bundle |
| runtime-blocked-source | blocked/fail | policy decision, blocked source result, no publication |
| runtime-missing-evidence | needs_review/fail | missing coverage report, no publication |
| runtime-verification-conflict | conflict | conflict decision, no publication |
| runtime-adapter-mismatch | fail | adapter diagnostics, no canonical invalid state |
| runtime-replay-gap | fail/needs_review | missing ref report, no replay pass |
| runtime-boundary-violation | fail | cross-owner mutation rejection and forbidden import detection |

## Required Oracles

Every runtime fixture must define:

- manifest
- expected command sequence
- expected event sequence
- expected policy decisions
- expected source adapter results
- expected artifact hashes
- expected normalized anchors where applicable
- expected extraction candidates where applicable
- expected evidence coverage
- expected verification decisions
- expected output manifest where applicable
- expected replay bundle
- expected completion gates

## Pass/Fail Rules

- Undeclared tolerance fails.
- Missing required oracle fails.
- Raw secret material in fixture outputs fails.
- Any negative fixture producing successful publication fails.
- Any successful fixture with missing replay refs fails.
- Any fixture relying on external network, framework-native state, or non-deterministic model output fails.
