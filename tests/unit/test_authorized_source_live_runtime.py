from __future__ import annotations

import hashlib
import json
from pathlib import Path

from veracrawl.benchmarks.authorized_source_live import (
    LiveOfficialApiResponse,
    run_live_authorized_source_gate,
)
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.production_grade import (
    ProductionGradeClosureManifest,
    ProductionSourceProfile,
)


def _manifest() -> ProductionGradeClosureManifest:
    path = Path("tests/fixtures/production-authorized-source-live-official-api/manifest.yaml")
    return ProductionGradeClosureManifest.model_validate(
        json.loads(path.read_text(encoding="utf-8"))
    )


def test_live_authorized_source_uses_real_response_hash_and_redacted_artifact() -> None:
    bodies = {
        "source:pypi-requests-json": (
            b'{"info":{"name":"requests","author_email":"owner@example.com"},'
            b'"token":"secret-token"}'
        ),
        "source:npm-react-registry-json": b'{"name":"react","dist-tags":{"latest":"19.0.0"}}',
    }

    def fetcher(
        source_profile: ProductionSourceProfile,
        timeout_ms: int,
    ) -> LiveOfficialApiResponse:
        assert timeout_ms > 0
        body = bodies[source_profile.id]
        return LiveOfficialApiResponse(
            status_code=200,
            final_url=source_profile.entry_point_url,
            headers={"Content-Type": "application/json; charset=utf-8"},
            body=body,
        )

    result = run_live_authorized_source_gate(
        manifest=_manifest(),
        profile="production",
        fetcher=fetcher,
    )

    report = result.gate_result.report
    assert report.completion_result == CompletenessResult.PASS
    assert len(result.gate_result.authorized_sources) == 2
    first_record = result.gate_result.authorized_sources[0]
    expected_hash = f"sha256:{hashlib.sha256(bodies[first_record.source_profile_ref]).hexdigest()}"
    assert first_record.content_hash_refs == [expected_hash]
    assert report.artifact_refs == [artifact.id for artifact in result.redacted_artifacts]
    assert report.source_anchor_refs
    assert "owner@example.com" not in result.redacted_artifacts[0].body_preview
    assert "secret-token" not in result.redacted_artifacts[0].body_preview


def test_live_authorized_source_blocks_non_passing_live_api_response() -> None:
    def fetcher(
        source_profile: ProductionSourceProfile,
        timeout_ms: int,
    ) -> LiveOfficialApiResponse:
        return LiveOfficialApiResponse(
            status_code=403 if source_profile.id == "source:pypi-requests-json" else 200,
            final_url=source_profile.entry_point_url,
            headers={"Content-Type": "application/json"},
            body=b'{"name":"ok"}',
        )

    result = run_live_authorized_source_gate(
        manifest=_manifest(),
        profile="production",
        fetcher=fetcher,
    )

    report = result.gate_result.report
    assert report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert report.release_blocker_refs
    assert report.diagnostics
    assert len(result.gate_result.authorized_sources) == 1
