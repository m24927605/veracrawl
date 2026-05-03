# Research: Cost Latency Stability Release Gate

## Decisions

- Aggregate prior quality gate report refs rather than rerunning rows 058-063.
  The release gate is responsible for release-readiness composition and SLO
  checks, not for duplicating lower benchmark behavior.
- Require six prior gate refs: expanded real-world quality corpus, browser
  quality, deep crawl frontier, field-level oracle, precision/recall, and
  repair success.
- Require at least three stability runs to avoid claiming release readiness from
  a single lucky run.
- Block release on missing replay, missing command/event/outbox refs, and
  false-ready status even if numeric metrics appear acceptable.

## Alternatives Considered

- Treating 054 production release gate as sufficient: rejected because 054
  predates the post-056 quality roadmap and does not aggregate rows 058-063.
- Storing only summary booleans: rejected because release replay needs stable
  refs to prior gates, SLO metrics, audit, commands, events, outbox, and replay.
- Allowing best-effort release with warnings: rejected because the user required
  no weakened or fake completion.
