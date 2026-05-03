# Feature Specification: Structured Source Adapters Runtime

**Feature Branch**: `042-structured-source-adapters-runtime`
**Status**: Planned - not implemented
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Add production source adapters for sitemap, RSS/feed, API-like sources,
documents, and file imports behind the existing source adapter boundary.

## Scope

- Sitemap and RSS/feed discovery.
- API-like JSON source acquisition.
- Document source acquisition and metadata capture.
- File-import source adapter for authorized local inputs.
- Adapter metadata schemas, source adapter result refs, artifacts, policy refs,
  and replay refs.

## Dependencies

- Blocks: 043, 045, 054.
- Requires: 041.

## Completion Gate

Each structured adapter produces source adapter results, artifacts, evidence
seeds, policy refs, and replay refs, with negative fixtures for malformed,
policy-denied, unsupported, and replay-mismatched sources.

## Non-Goals

- Does not implement browser rendering.
- Does not publish outputs.
