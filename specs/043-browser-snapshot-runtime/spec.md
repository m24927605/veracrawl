# Feature Specification: Browser Snapshot Runtime

**Feature Branch**: `043-browser-snapshot-runtime`
**Status**: Planned - not implemented
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Add a policy-gated browser snapshot adapter for JavaScript-required pages while
preserving sandbox, budget, network, artifact, prompt-taint, and replay
boundaries.

## Scope

- Browser snapshot adapter behind ports.
- DOM, screenshot, network trace, console, and timing artifacts.
- Browser minute and resource budget refs.
- Sandbox and network egress enforcement.
- Prompt-taint boundary for rendered content.

## Dependencies

- Blocks: 044, 045, 054.
- Requires: 041, 042.

## Completion Gate

Browser-required fixtures pass only with browser artifacts, policy/budget refs,
and replay refs; unsafe interactions, excessive cost, prompt-tainted content, or
blocked network access fail deterministically.

## Non-Goals

- Does not solve CAPTCHA, bypass paywalls, evade WAFs, or automate unauthorized
  login walls.
