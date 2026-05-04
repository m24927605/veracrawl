# Feature Specification: Unified HTTP Browser Acquisition Escalation Runtime

**Feature Branch**: `070-unified-http-browser-acquisition-escalation-runtime`  
**Created**: 2026-05-04  
**Status**: Planned  
**Roadmap Row**: 070  
**Input**: Production-grade closure requirement: JS/browser evidence recovery must be part of the crawler runtime, not a manual probe.

## Summary

Integrate HTTP, structured source, and browser snapshot acquisition into one
policy-gated acquisition escalation runtime. When HTTP/structured acquisition
does not expose required evidence, VeraCrawl may escalate to browser rendering
only when policy, sandbox, budget, side-effect, and prompt-taint gates allow it.

## User Scenarios

1. Given an HTTP product page that returns only an app shell, VeraCrawl attempts
   browser rendering under sandbox and budget. If rendered DOM exposes product
   evidence, the result can pass with DOM artifacts and content hashes.
2. Given a browser-rendered page that shows login-required or source-limited
   content, VeraCrawl records needs-review/source-limited without bypass.
3. Given browser rendering that triggers unsafe interactions, excessive cost, or
   prompt-tainted content, VeraCrawl blocks the path and records typed failure.

## Functional Requirements

- **FR-001**: System MUST define `AcquisitionEscalationPlan`,
  `AcquisitionAttempt`, `BrowserEscalationDecision`,
  `RenderedSourceObservation`, and `SourceLimitationRecord` contracts.
- **FR-002**: System MUST evaluate HTTP, structured source, and browser
  acquisition attempts through a single source acquisition state machine.
- **FR-003**: System MUST trigger browser escalation only when required evidence
  is missing and policy allows read-only rendering.
- **FR-004**: System MUST capture DOM, visible text, screenshot, network trace,
  console logs, timing, content hashes, source anchors, command/event/outbox
  refs, and replay refs for rendered evidence.
- **FR-005**: System MUST classify rendered login walls, app shell, challenge,
  source API denial, robots denial, budget exhaustion, and prompt-taint as typed
  source limitations or failures.
- **FR-006**: System MUST keep Playwright/browser-native state adapter-owned and
  outside core canonical state.
- **FR-007**: System MUST integrate with product availability and generic schema
  extraction flows.

## Safety Requirements

- No stealth automation, browser fingerprint evasion, CAPTCHA solving, proxy
  rotation, login-wall bypass, WAF bypass, cart/checkout, or mutation.
- Browser interactions are read-only unless a later explicit authorized spec
  allows a narrower credentialed read path.

## Required Tests

- Unit and contract tests for escalation decisions and source limitation
  records.
- Browser fixture tests where browser DOM recovers evidence that HTTP missed.
- Negative tests for login-required DOM, challenge DOM, unsafe interaction,
  budget exhaustion, prompt-taint, missing DOM artifact, missing replay, and
  source API denial.
- Live public JS corpus validation with deterministic and Playwright adapters.

## Completion Gate

`veracrawl-acquisition-escalation` can decide and execute HTTP-to-browser
evidence recovery for authorized targets, while source-limited sites such as the
recorded Shopee Taiwan case remain honest needs-review when browser render does
not expose source-backed evidence.
