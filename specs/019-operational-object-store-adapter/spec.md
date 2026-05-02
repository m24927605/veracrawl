# Feature Specification: VeraCrawl Operational Object Store Adapter

**Feature Branch**: `019-operational-object-store-adapter`
**Created**: 2026-05-03
**Status**: Implemented
**Input**: User description: "建立 VeraCrawl Operational Object Store Adapter：在 adapters 層實作 object-store-neutral artifact storage abstraction 與 S3-compatible/MinIO operational adapter、object store conformance harness、put/get/head/list/delete/content digest/idempotency/lifecycle/retention/privacy/policy/replay refs、live Docker MinIO integration gate 與 no-object-store runtime needs_review guard。Core 不得直接耦合 boto3/botocore/S3 SDK/物件儲存 SDK，不得把 deterministic fixture artifact store 假裝成 live object store pass，必須遵守 docs/07、09、10、11 與 constitution。"

## Constitution Alignment

- **General-purpose crawler impact**: Object store conformance applies to raw source snapshots, normalized documents, anchor maps, evidence bundles, output manifests, replay bundles, redaction maps, and future artifact families across all sites and source adapters.
- **Target/V1 boundary**: This is target artifact infrastructure work after operational Postgres and Redis broker adapters. It turns artifact bytes into a live object-store capability rather than deterministic fixture storage only.
- **Evidence and replay impact**: Operational pass requires artifact refs, object operation refs, content digest refs, read-after-write refs, head/list/delete refs, lifecycle refs, retention/privacy refs, policy refs, and replay refs.
- **Safety and policy impact**: Missing S3-compatible endpoint/runtime must not be reported as operational pass. Artifact storage must preserve digest, privacy, retention, lifecycle, and no-deleted-content rules.
- **Required reference docs**: `docs/07-data-contracts.md`, `docs/09-target-capability-model.md`, `docs/10-target-implementation-design.md`, `docs/11-target-testing-and-acceptance.md`, `.specify/memory/constitution.md`, and `AGENTS.md`.

## Requirements

- **FR-001**: System MUST define object store adapter specs, operation records, conformance reports, and fixture manifests.
- **FR-002**: System MUST implement an object-store-neutral core conformance harness that depends on contracts/ports only.
- **FR-003**: System MUST implement `veracrawl.adapters.object_stores.s3.S3ObjectStoreAdapter` behind the object-store boundary.
- **FR-004**: Core packages MUST NOT statically import `boto3`, `botocore`, S3 clients, `veracrawl.adapters`, concrete queue clients, or cloud SDKs.
- **FR-005**: S3-compatible conformance MUST prove put, duplicate put, get, head, list, delete, digest verification, lifecycle, retention, privacy, policy, and replay refs.
- **FR-006**: Duplicate write after adapter reopen MUST create zero duplicate objects and return a duplicate operation record.
- **FR-007**: CLI fixture execution MUST require explicit endpoint, bucket, access key, and secret for operational pass fixtures and MUST report `needs_review` for no-runtime fixtures instead of faking pass.
- **FR-008**: System MUST expose live integration tests that can run against provided S3-compatible credentials or Docker-provisioned MinIO.
- **FR-009**: System MUST register object store fixtures, target area coverage, docs, quickstart, and non-deceptive completion notes.

## Non-Goals

- This feature does not implement managed S3 operations, cloud IAM provisioning, CDN delivery, production retention jobs, encryption key management, metrics/tracing backend, deployment automation, or production artifact lifecycle workers.
- This feature does not remove deterministic fixture artifact storage; live object store execution complements it.
- This feature does not make deterministic fixture artifact refs an operational object store pass.
- VeraCrawl core must not import concrete DB/queue/cloud/object-store SDKs, browser libraries, model SDKs, or agent frameworks.

## Success Criteria

- **SC-001**: S3-compatible operational fixtures pass against a live endpoint or Docker-provisioned MinIO.
- **SC-002**: No-object-store runtime fixture returns `needs_review`, not pass.
- **SC-003**: Contract registry validation returns `ok: true`.
- **SC-004**: Core import-boundary tests prove `boto3`, `botocore`, and `veracrawl.adapters` stay outside core.
- **SC-005**: `ruff`, `mypy`, full pytest, and explicit MinIO live integration gate pass in this workspace.
