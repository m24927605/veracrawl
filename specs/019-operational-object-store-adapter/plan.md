# Implementation Plan: VeraCrawl Operational Object Store Adapter

**Branch**: `019-operational-object-store-adapter` | **Date**: 2026-05-03 | **Spec**: [spec.md](spec.md)

## Summary

Implement live artifact object storage without coupling VeraCrawl core to object-store SDKs. Add object store contracts, a core conformance harness, S3-compatible/MinIO adapter, live/no-runtime fixture CLI, registry/docs/test coverage, and Docker-backed MinIO integration.

## Technical Context

**Language/Version**: Python 3.11+ with Python 3.12 verification
**Primary Dependencies**: Pydantic contracts, optional `boto3`/`botocore` through `object-s3`
**Object Store**: S3-compatible adapter under `veracrawl.adapters.object_stores`
**Testing**: pytest, ruff, mypy, registry validation, CLI fixtures, Docker-backed MinIO integration gate
**Owner Services**: `artifact_lifecycle`, `ports`, `review_replay`, `tests`
**Canonical Contracts**: `ObjectStoreAdapterSpec`, `ObjectStoreOperationRecord`, `ObjectStoreConformanceReport`, `ObjectStoreFixtureManifest`
**Replay/Artifact Impact**: Operational object store pass requires artifact, object operation, digest, read/head/list/delete, lifecycle, retention, privacy, policy, and replay refs.

## Constitution Check

- [x] No single-site scraper assumptions.
- [x] Core remains free of boto3, botocore, object-store, storage, and cloud imports.
- [x] Concrete S3-compatible implementation lives in `adapters/`.
- [x] Deterministic fixture artifact store remains a fixture tool, not live object store proof.
- [x] Fixture/oracle, live integration, no-runtime report, and negative boundary tests are planned before implementation.
- [x] Target architecture is not weakened for schedule or staffing reasons.

## Project Structure

```text
src/veracrawl/contracts/artifact.py
src/veracrawl/artifact_lifecycle/object_store_conformance.py
src/veracrawl/adapters/object_stores/s3.py
src/veracrawl/cli/object_store.py
tests/contract/test_object_store_contracts.py
tests/contract/test_object_store_contract_registry.py
tests/contract/test_object_store_import_boundaries.py
tests/unit/test_s3_object_store_adapter.py
tests/integration/test_object_store_fixtures.py
tests/integration/test_s3_object_store_live.py
tests/fixtures/<object_store_fixture_id>/
```
