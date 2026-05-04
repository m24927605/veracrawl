from __future__ import annotations

import json
from pathlib import Path

from veracrawl.benchmarks.ecommerce_official_api import (
    run_ecommerce_official_api_benchmark,
)
from veracrawl.contracts.ecommerce_official_api import (
    EcommerceOfficialApiBenchmarkManifest,
    EcommerceOfficialApiTargetSpec,
)
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.ports.ecommerce_official_api import (
    EcommerceOfficialApiFetchOutcome,
    EcommerceOfficialApiResponse,
)


class _FakeAdapter:
    def __init__(self, body: bytes | None = None, failure_type: str | None = None) -> None:
        self.body = body
        self.failure_type = failure_type

    def fetch_product(
        self,
        *,
        fixture_id: str,
        target: EcommerceOfficialApiTargetSpec,
    ) -> EcommerceOfficialApiFetchOutcome:
        base = f"{fixture_id}:{target.id}:official-api"
        if self.failure_type is not None:
            return EcommerceOfficialApiFetchOutcome(
                credential_grant_ref=f"credential-grant:{base}:unavailable",
                credential_audit_ref=f"credential-audit:{base}:missing-env",
                failure_type=self.failure_type,
                diagnostics=[f"{target.site_name} credentials unavailable"],
            )
        assert self.body is not None
        return EcommerceOfficialApiFetchOutcome(
            credential_grant_ref=f"credential-grant:{base}:env",
            credential_audit_ref=f"credential-audit:{base}:env:redacted",
            response=EcommerceOfficialApiResponse(
                status_code=200,
                request_url=target.entry_point_url,
                final_url=target.entry_point_url,
                headers={"Content-Type": "application/json"},
                body=self.body,
            ),
        )


def _manifest() -> EcommerceOfficialApiBenchmarkManifest:
    path = Path("tests/fixtures/us-ecommerce-official-api-product-availability/manifest.yaml")
    return EcommerceOfficialApiBenchmarkManifest.model_validate(
        json.loads(path.read_text(encoding="utf-8"))
    )


def test_ecommerce_official_api_runtime_builds_source_backed_field_evidence() -> None:
    bodies = {
        "amazon-creators-api-sandisk-256gb": json.dumps(
            {
                "items": [
                    {
                        "ItemInfo": {
                            "Title": {
                                "DisplayValue": (
                                    "SanDisk 256GB Extreme microSDXC UHS-I Memory Card"
                                )
                            }
                        },
                        "OffersV2": {
                            "Listings": [
                                {
                                    "Price": {
                                        "Money": {
                                            "Amount": 24.99,
                                            "Currency": "USD",
                                            "DisplayAmount": "$24.99",
                                        }
                                    },
                                    "Availability": {"Message": "In Stock"},
                                }
                            ]
                        },
                    }
                ],
                "access_token": "must-redact",
            }
        ).encode(),
        "ebay-browse-api-sandisk-256gb": json.dumps(
            {
                "itemSummaries": [
                    {
                        "title": "SanDisk 256GB Extreme microSDXC Memory Card",
                        "price": {"value": "23.49", "currency": "USD"},
                        "estimatedAvailabilities": [
                            {"estimatedAvailabilityStatus": "IN_STOCK"}
                        ],
                    }
                ]
            }
        ).encode(),
    }
    manifest = _manifest()

    result = run_ecommerce_official_api_benchmark(
        manifest=manifest,
        profile="target",
        adapter_factory=lambda target: _FakeAdapter(body=bodies[target.id]),
    )

    assert result.report.completion_result == CompletenessResult.PASS
    assert result.report.operator_status == "ecommerce_official_api_completed"
    assert len(result.site_results) == 2
    assert len(result.field_evidence) == 6
    assert len(result.authorized_sources) == 2
    assert result.report.source_fetch_refs
    assert all(field.source_anchor_ref for field in result.field_evidence)
    assert all(not field.llm_output_evidence_refs for field in result.field_evidence)
    assert "must-redact" not in result.redacted_artifacts[0].body_preview


def test_ecommerce_official_api_runtime_records_missing_credentials_without_fake_pass() -> None:
    manifest = _manifest()

    result = run_ecommerce_official_api_benchmark(
        manifest=manifest,
        profile="target",
        adapter_factory=lambda _target: _FakeAdapter(
            failure_type="official_api_credentials_unavailable"
        ),
    )

    assert result.report.completion_result == CompletenessResult.NEEDS_REVIEW
    assert result.report.operator_status == "ecommerce_official_api_credentials_required"
    assert result.report.authorized_source_refs == []
    assert result.report.field_evidence_refs == []
    assert len(result.report.blocked_site_result_refs) == 2
    assert result.report.failure_type == "official_api_credentials_unavailable"

