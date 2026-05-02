# Contract: Browser Observation

## Scope

This contract defines browser observation records and sandbox gates. It does not require a production browser engine in core.

## Required Contracts

- `BrowserSandboxPolicy`
- `BrowserInteractionStep`
- `BrowserObservationPort`

## Required Commands And Events

- `capture_browser_snapshot`
- `execute_browser_step`
- `browser_step_executed`
- `snapshot_written`

## Rules

- Browser adapters must be replaceable behind `BrowserObservationPort`.
- Core packages must not import Playwright or any browser framework.
- Read-only browser observation must record DOM, screenshot, network metadata, sandbox, policy, and replay refs.
- Unsafe side-effect classes must be blocked before artifacts are accepted.
- Browser-derived artifacts are not publication evidence until later evidence contracts anchor them.
