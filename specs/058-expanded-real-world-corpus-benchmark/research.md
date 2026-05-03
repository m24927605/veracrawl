# Research: Expanded Real-World Public Corpus Benchmark

## Decision: Compose Row 055 Instead Of Replacing It

**Decision**: The quality benchmark runtime calls `run_real_world_benchmark_corpus`
and evaluates its observations against quality thresholds.

**Rationale**: Row 055 already owns live HTTP acquisition, robots preflight,
origin allowlists, private-network denial, artifact refs, content hashes,
command/event/outbox refs, and replay refs. Reusing it preserves a single source
of acquisition truth and avoids a parallel HTTP path.

**Rejected Alternative**: Implement a new live HTTP runner for quality corpus
only. This would increase coupling, duplicate policy logic, and risk inconsistent
evidence semantics.

## Decision: Quality Pass Requires Passing Row 055 Observations

**Decision**: Quality targets count toward thresholds only when their underlying
row 055 observation passes. Policy-denied, network-unavailable, drift, and
replay-missing targets are reported but not counted as passing quality coverage.

**Rationale**: Production-quality claims cannot count drift or blocked targets as
success. The report should distinguish broad declaration from passing coverage.

**Rejected Alternative**: Allow partial pass when enough targets pass even if
other targets drift. That hides external drift and weakens operator trust.

## Decision: Pattern Coverage Is Declared And Verified From Passing Targets

**Decision**: Each target declares pattern refs. The runtime aggregates pattern
coverage from passing observations only and enforces minimum pattern count.

**Rationale**: Pattern coverage must be explicit and audit-friendly. Counting
patterns from failed observations would overstate capability.

**Rejected Alternative**: Infer pattern families from URLs or HTML heuristics.
This risks site-specific assumptions and brittle classification.

## Decision: Live Public Corpus And Deterministic Fixture Corpus Share The Same Manifest Shape

**Decision**: Tests may monkeypatch the network adapter for deterministic
validation, but the manifest shape remains identical to the live public corpus.

**Rationale**: This allows focused tests to be deterministic while the CLI can run
the same corpus against public sites for real validation.

## Decision: Use Stable Refs, Not Raw Page Bodies, In Quality Reports

**Decision**: Quality reports store refs and counts. Raw public page content
remains in artifact stores through existing row 055 behavior.

**Rationale**: This keeps privacy/retention and replay semantics consistent with
VeraCrawl contracts.
