# Feature Specification: Live Normalization And Site Understanding

**Feature Branch**: `045-live-normalization-site-understanding`
**Status**: Planned - not implemented
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Convert acquired live artifacts into normalized documents, anchor maps, page
type classifications, site models, link provenance, and transformation manifests.

## Scope

- HTML/text/document normalization.
- Raw-to-normalized anchor maps.
- Link extraction and provenance.
- Page type classification and site model records.
- AI-assisted site understanding through framework-neutral adapters.

## Dependencies

- Blocks: 046, 047, 049, 051, 052, 054.
- Requires: 041, 042, 043.

## Completion Gate

Real acquired artifacts produce replayable normalization manifests, source
anchors, site models, and link provenance across target website patterns.

## Non-Goals

- Does not publish outputs.
- Does not treat site model or graph context as source evidence.
