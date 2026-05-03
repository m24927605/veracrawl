# Feature Specification: Live HTTP Acquisition Runtime

**Feature Branch**: `041-live-http-acquisition-runtime`
**Created**: 2026-05-03
**Status**: Active
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Constitution Alignment

- **General-purpose crawler impact**: Live HTTP acquisition applies to any
  authorized HTTP/HTTPS website source and does not encode a single site,
  selector set, domain, or output schema.
- **Target/V1 boundary**: This activates roadmap row 041. It depends on row 039
  run control and row 040 persistence wiring, then proves authorized HTTP
  acquisition can write request, response, source adapter, snapshot, source
  observation, artifact, policy, event/outbox, and replay refs.
- **Evidence and replay impact**: Raw HTTP observations must produce artifact
  refs, content hashes, canonical URL refs, source observation refs, command
  refs, event cursor refs, outbox refs, and replay bundle refs.
- **Safety and policy impact**: Scope denial, private-network denial,
  malformed responses, missing artifacts, replay gaps, and direct-source bypass
  must fail with typed diagnostics.
- **Required reference docs**: `docs/07-data-contracts.md`,
  `docs/08-build-roadmap.md`, `docs/09-target-capability-model.md`,
  `docs/10-target-implementation-design.md`, and
  `docs/11-target-testing-and-acceptance.md`.

## User Stories & Testing

### User Story 1 - Acquire Authorized HTTP Source (Priority: P1)

As a crawl runtime owner, I need an approved production run to fetch an
authorized HTTP page through the HTTP source adapter port and persist source
observation, snapshot, artifact, content hash, policy, and replay refs.

**Independent Test**: Run `veracrawl-live-http run tests/fixtures/live-http-success --profile target --out .veracrawl-test-runs/live-http-success`; the report passes only when row 039/040 refs and live HTTP request/response/source observation refs are present.

### User Story 2 - Preserve Redirect And Canonical URL Lineage (Priority: P2)

As a reviewer, I need redirects and final canonical URL refs to be visible in
the acquisition report rather than hidden inside adapter-native state.

**Independent Test**: `live-http-redirect` passes only when redirect hop refs,
final response refs, canonical URL refs, artifact refs, and replay refs exist.

### User Story 3 - Reject Unsafe Or Fake Acquisition (Priority: P3)

As a Staff reviewer, I need unsafe network access, malformed responses, missing
artifacts, replay gaps, and direct source bypass to fail explicitly.

**Independent Test**: Negative fixtures for scope denied, private denied,
malformed response, missing artifact, replay mismatch, and direct-source bypass
fail with typed `LiveHttpAcquisitionFailureType` values.

## Requirements

- **FR-001**: System MUST define live HTTP acquisition contracts and fixture manifests.
- **FR-002**: System MUST expose `veracrawl-live-http` CLI fixtures.
- **FR-003**: System MUST require row 039 run-control refs and row 040
  production persistence refs before a passing HTTP acquisition report.
- **FR-004**: System MUST execute HTTP acquisition through `NetworkSourceAdapterPort`
  and MUST NOT read fixture source files as a direct-source bypass.
- **FR-005**: System MUST record network request, network response, redirect,
  source acquisition report, source adapter result, fetch attempt, fetch result,
  page snapshot, source observation, artifact, content hash, canonical URL,
  policy, command, event cursor, outbox, and replay refs for pass.
- **FR-006**: System MUST block unsafe scope/private-network/malformed/missing
  artifact/replay/direct-bypass cases with typed diagnostics.
- **FR-007**: System MUST register contracts, commands, events, fixture oracles,
  and target area coverage for `live_http_acquisition_runtime`.
- **FR-008**: System MUST preserve core independence from concrete HTTP clients;
  standard-library HTTP remains adapter-owned.

## Key Entities

- **LiveHttpAcquisitionReport**: Operator-visible proof of live HTTP acquisition
  through production run-control/persistence and HTTP source adapter refs.
- **LiveHttpFixtureManifest**: Fixture expectation contract.
- **TargetSourceObservationRecord**: Source-backed observation record derived
  from the HTTP response and artifact refs.

## Non-Goals

- Does not implement browser rendering.
- Does not implement credentialed sessions.
- Does not implement structured sitemap/RSS/API/document adapters beyond HTTP.
- Does not implement worker autoscaling or production network fleet operations.

## Success Criteria

- **SC-001**: Success fixture fetches a local HTTP page through adapter ports and passes with row 039/040 refs.
- **SC-002**: Redirect fixture records redirect hop and canonical URL refs.
- **SC-003**: Negative fixtures fail with typed diagnostics and no false pass.
- **SC-004**: Registry validation passes and `live_http_acquisition_runtime` is materialized.
- **SC-005**: Focused tests, CLI loop, ruff, mypy, full non-Docker, and Docker-backed gates pass.
