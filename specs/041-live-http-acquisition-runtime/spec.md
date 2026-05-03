# Feature Specification: Live HTTP Acquisition Runtime

**Feature Branch**: `041-live-http-acquisition-runtime`
**Status**: Planned - not implemented
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Implement authorized live HTTP acquisition behind source adapter ports, including
policy gates, redirects, canonical URLs, request/response metadata, snapshots,
content hashes, source observations, artifacts, and replay refs.

## Scope

- HTTP source adapter runtime behind ports.
- Network policy, private-network denial, timeout, retry, redirect, and content
  type handling.
- Snapshot artifact write with hash and source observation refs.
- Negative fixtures for denied scope, unsafe network, malformed responses,
  replay mismatch, and direct-source bypass.

## Dependencies

- Blocks: 042, 043, 045, 052, 054.
- Requires: 039, 040.

## Completion Gate

Authorized HTTP crawl fixtures write source observations and artifacts from real
local/network sources, and blocked or unsafe sources produce typed failures
without bypassing adapter or policy gates.

## Non-Goals

- Does not implement browser rendering.
- Does not implement credentialed sessions.
