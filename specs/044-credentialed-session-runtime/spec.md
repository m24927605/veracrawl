# Feature Specification: Credentialed Session Runtime

**Feature Branch**: `044-credentialed-session-runtime`
**Status**: Planned - not implemented
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Support authorized credentialed sessions without leaking secrets, exceeding
scope, or allowing credentials to become canonical crawler state.

## Scope

- Credential use requests, policy decisions, and audit refs.
- Session adapter boundary and redacted replay refs.
- Credential scope enforcement for HTTP and browser paths.
- Secret redaction in artifacts, logs, traces, and replay bundles.

## Dependencies

- Blocks: 054.
- Requires: 039, 041, 043.

## Completion Gate

Credentialed fixtures prove vault boundary, credential audit, redacted replay,
and denial for out-of-scope, missing-authorization, leakage, or unsafe
credential use.

## Non-Goals

- Does not steal credentials or bypass login walls.
- Does not persist raw secrets as canonical state.
