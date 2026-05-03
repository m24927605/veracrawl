# Research: Precision Recall Quality Benchmark

## Decision: Confusion Records Are The Metric Source Of Truth

Quality metrics consume `FieldConfusionRecord` inputs rather than rerunning
extraction. Each record carries field evaluation, evidence, publication gate,
command/event/outbox, policy, and replay refs.

## Decision: Thresholds Are Explicit Contracts

Default thresholds are precision >= 0.98, recall >= 0.90, F1 >= 0.94, and
critical-field precision >= 0.99. Runtime code cannot lower them silently.

## Decision: Slice Metrics Are First-Class

Reports include corpus, schema, website pattern, source type, rendering mode,
and confidence bucket slices so later release gates can block hidden weak areas.

## Decision: Unsafe Inputs Cannot Become True Positives

Publication bypass, LLM-as-evidence, missing evidence, missing replay, and hidden
false positives fail with typed diagnostics.
