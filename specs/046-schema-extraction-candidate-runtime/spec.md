# Feature Specification: Schema Extraction Candidate Runtime

**Feature Branch**: `046-schema-extraction-candidate-runtime`
**Status**: Planned - not implemented
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Generate schema-bound extraction strategies and candidates from normalized live
documents while keeping candidates separate from published outputs.

## Scope

- Declared schema and approved exploratory schema support.
- Extraction strategy records and candidate records.
- Model/tool trace refs behind framework-neutral ports.
- Schema validation, rejection, drift, and repair diagnostics.

## Dependencies

- Blocks: 047, 049, 054.
- Requires: 045.

## Completion Gate

Candidates carry strategy refs, schema validation refs, source anchors,
model/tool trace refs, rejection refs, and replay refs, and cannot be published
without evidence and verification.

## Non-Goals

- Does not publish candidate outputs directly.
- Does not allow model-generated content to replace source evidence.
