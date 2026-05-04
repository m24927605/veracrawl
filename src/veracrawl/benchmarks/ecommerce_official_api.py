"""Official ecommerce API product evidence benchmark runtime."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import cast

from veracrawl.contracts.common import Ref
from veracrawl.contracts.ecommerce_official_api import (
    EcommerceOfficialApiBenchmarkManifest,
    EcommerceOfficialApiBenchmarkReport,
    EcommerceOfficialApiFieldEvidence,
    EcommerceOfficialApiRedactedArtifact,
    EcommerceOfficialApiSiteResult,
    EcommerceOfficialApiSourceFetch,
    EcommerceOfficialApiTargetSpec,
)
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.production_grade import AuthorizedSourceAccessRecord
from veracrawl.ports.ecommerce_official_api import (
    EcommerceOfficialApiAdapterPort,
    EcommerceOfficialApiFetchOutcome,
    EcommerceOfficialApiResponse,
)

OfficialApiAdapterFactory = Callable[
    [EcommerceOfficialApiTargetSpec],
    EcommerceOfficialApiAdapterPort,
]


@dataclass(frozen=True)
class EcommerceOfficialApiBenchmarkResult:
    report: EcommerceOfficialApiBenchmarkReport
    site_results: list[EcommerceOfficialApiSiteResult]
    field_evidence: list[EcommerceOfficialApiFieldEvidence]
    source_fetches: list[EcommerceOfficialApiSourceFetch]
    redacted_artifacts: list[EcommerceOfficialApiRedactedArtifact]
    authorized_sources: list[AuthorizedSourceAccessRecord]


@dataclass(frozen=True)
class _CommonRefs:
    policy_decision_refs: list[Ref]
    command_record_refs: list[Ref]
    event_cursor_refs: list[Ref]
    outbox_refs: list[Ref]
    replay_bundle_ref: Ref


@dataclass(frozen=True)
class _ExtractedFields:
    identity_raw_text: str | None
    identity_terms_matched: list[str]
    price_raw_text: str | None
    price_amount: float | None
    price_currency: str | None
    availability_raw_text: str | None
    availability_status: str | None


def run_ecommerce_official_api_benchmark(
    *,
    manifest: EcommerceOfficialApiBenchmarkManifest,
    profile: str,
    adapter_factory: OfficialApiAdapterFactory,
) -> EcommerceOfficialApiBenchmarkResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")

    site_results: list[EcommerceOfficialApiSiteResult] = []
    field_evidence: list[EcommerceOfficialApiFieldEvidence] = []
    source_fetches: list[EcommerceOfficialApiSourceFetch] = []
    redacted_artifacts: list[EcommerceOfficialApiRedactedArtifact] = []
    authorized_sources: list[AuthorizedSourceAccessRecord] = []

    for target in manifest.target_specs:
        adapter = adapter_factory(target)
        outcome = adapter.fetch_product(fixture_id=manifest.id, target=target)
        site_result, site_fields, fetch, artifact, source = _handle_outcome(
            manifest=manifest,
            target=target,
            outcome=outcome,
        )
        site_results.append(site_result)
        field_evidence.extend(site_fields)
        if fetch is not None:
            source_fetches.append(fetch)
        if artifact is not None:
            redacted_artifacts.append(artifact)
        if source is not None:
            authorized_sources.append(source)

    report = _build_report(
        manifest=manifest,
        site_results=site_results,
        field_evidence=field_evidence,
        source_fetches=source_fetches,
        redacted_artifacts=redacted_artifacts,
        authorized_sources=authorized_sources,
    )
    return EcommerceOfficialApiBenchmarkResult(
        report=report,
        site_results=site_results,
        field_evidence=field_evidence,
        source_fetches=source_fetches,
        redacted_artifacts=redacted_artifacts,
        authorized_sources=authorized_sources,
    )


def _handle_outcome(
    *,
    manifest: EcommerceOfficialApiBenchmarkManifest,
    target: EcommerceOfficialApiTargetSpec,
    outcome: EcommerceOfficialApiFetchOutcome,
) -> tuple[
    EcommerceOfficialApiSiteResult,
    list[EcommerceOfficialApiFieldEvidence],
    EcommerceOfficialApiSourceFetch | None,
    EcommerceOfficialApiRedactedArtifact | None,
    AuthorizedSourceAccessRecord | None,
]:
    base = f"{manifest.id}:{target.id}:official-api"
    common_refs = _common_refs(base)
    if outcome.failure_type is not None or outcome.response is None:
        return (
            _failure_site_result(
                manifest=manifest,
                target=target,
                failure_type=outcome.failure_type or "official_api_no_response",
                diagnostics=outcome.diagnostics
                or ["official ecommerce API adapter did not produce a response"],
                missing_ref_fields=[
                    "authorized_source_ref",
                    "redacted_artifact_refs",
                    "source_anchor_refs",
                    "content_hash_refs",
                    "field_evidence_refs",
                ],
                common_refs=common_refs,
            ),
            [],
            None,
            None,
            None,
        )

    response = outcome.response
    if len(response.body) > target.size_budget_bytes:
        return (
            _failure_site_result(
                manifest=manifest,
                target=target,
                failure_type="official_api_body_too_large",
                diagnostics=[
                    (
                        f"{target.site_name} official API body exceeded "
                        f"{target.size_budget_bytes} bytes"
                    )
                ],
                missing_ref_fields=["redacted_artifact_refs", "field_evidence_refs"],
                common_refs=common_refs,
            ),
            [],
            None,
            None,
            None,
        )
    if not 200 <= response.status_code < 300:
        return (
            _failure_site_result(
                manifest=manifest,
                target=target,
                failure_type="official_api_http_error",
                diagnostics=[
                    f"{target.site_name} official API returned HTTP {response.status_code}"
                ],
                missing_ref_fields=["field_evidence_refs"],
                common_refs=common_refs,
            ),
            [],
            None,
            None,
            None,
        )

    try:
        payload = json.loads(response.body.decode("utf-8", errors="replace"))
    except json.JSONDecodeError as exc:
        return (
            _failure_site_result(
                manifest=manifest,
                target=target,
                failure_type="official_api_invalid_json",
                diagnostics=[f"{target.site_name} official API returned invalid JSON: {exc}"],
                missing_ref_fields=["field_evidence_refs"],
                common_refs=common_refs,
            ),
            [],
            None,
            None,
            None,
        )

    extracted = _extract_fields(
        target=target,
        payload=payload,
        body_text=response.body.decode("utf-8", errors="replace"),
    )
    missing = _missing_fields(target, extracted)
    if missing:
        return (
            _failure_site_result(
                manifest=manifest,
                target=target,
                failure_type="official_api_missing_product_evidence",
                diagnostics=[
                    (
                        f"{target.site_name} official API response was source-backed "
                        f"but missing {missing}"
                    )
                ],
                missing_ref_fields=missing,
                common_refs=common_refs,
            ),
            [],
            None,
            None,
            None,
        )

    artifact, fetch, source = _build_source_records(
        manifest=manifest,
        target=target,
        response=response,
        outcome=outcome,
        common_refs=common_refs,
        extracted=extracted,
    )
    site_fields = _build_field_evidence(
        manifest=manifest,
        target=target,
        artifact=artifact,
        source_fetch=fetch,
        extracted=extracted,
        common_refs=common_refs,
    )
    site_result = _passing_site_result(
        manifest=manifest,
        target=target,
        source=source,
        fetch=fetch,
        artifact=artifact,
        field_evidence=site_fields,
        extracted=extracted,
        common_refs=common_refs,
    )
    return site_result, site_fields, fetch, artifact, source


def _build_source_records(
    *,
    manifest: EcommerceOfficialApiBenchmarkManifest,
    target: EcommerceOfficialApiTargetSpec,
    response: EcommerceOfficialApiResponse,
    outcome: EcommerceOfficialApiFetchOutcome,
    common_refs: _CommonRefs,
    extracted: _ExtractedFields,
) -> tuple[
    EcommerceOfficialApiRedactedArtifact,
    EcommerceOfficialApiSourceFetch,
    AuthorizedSourceAccessRecord,
]:
    base = f"{manifest.id}:{target.id}:official-api"
    body_text = response.body.decode("utf-8", errors="replace")
    content_hash_ref = f"sha256:{hashlib.sha256(response.body).hexdigest()}"
    content_type = _content_type(response.headers)
    source_anchor_refs = _source_anchor_refs(
        base=base,
        payload_text=body_text,
        extracted=extracted,
    )
    preview = _redact_text(body_text)[:4000]
    artifact = EcommerceOfficialApiRedactedArtifact(
        id=f"artifact:{base}:redacted-source",
        fixture_id=manifest.id,
        target_spec_ref=target.id,
        site_name=target.site_name,
        platform=target.platform,
        source_url=response.final_url,
        status_code=response.status_code,
        content_type=content_type,
        byte_count=len(response.body),
        content_hash_ref=content_hash_ref,
        redaction_policy_refs=[
            f"redaction-policy:{base}:secrets",
            f"redaction-policy:{base}:personal-data",
        ],
        body_preview=preview,
        body_preview_truncated=len(body_text) > len(preview),
    )
    fetch = EcommerceOfficialApiSourceFetch(
        id=f"official-api-fetch:{base}",
        fixture_id=manifest.id,
        target_spec_ref=target.id,
        site_name=target.site_name,
        platform=target.platform,
        request_url=response.request_url,
        final_url=response.final_url,
        status_code=response.status_code,
        content_type=content_type,
        byte_count=len(response.body),
        content_hash_ref=content_hash_ref,
        redacted_artifact_ref=artifact.id,
        source_anchor_refs=source_anchor_refs,
        credential_grant_ref=outcome.credential_grant_ref,
        credential_audit_ref=outcome.credential_audit_ref,
        policy_decision_refs=common_refs.policy_decision_refs,
        command_record_refs=common_refs.command_record_refs,
        event_cursor_refs=common_refs.event_cursor_refs,
        outbox_refs=common_refs.outbox_refs,
        replay_bundle_ref=common_refs.replay_bundle_ref,
    )
    source = AuthorizedSourceAccessRecord(
        id=f"authorized-source-result:{base}",
        fixture_id=manifest.id,
        source_profile_ref=target.id,
        access_kind="official_api",
        credential_grant_ref=outcome.credential_grant_ref,
        credential_audit_ref=outcome.credential_audit_ref,
        redacted_artifact_refs=[artifact.id],
        source_anchor_refs=source_anchor_refs,
        content_hash_refs=[content_hash_ref],
        policy_decision_refs=common_refs.policy_decision_refs,
        command_record_refs=common_refs.command_record_refs,
        event_cursor_refs=common_refs.event_cursor_refs,
        outbox_refs=common_refs.outbox_refs,
        replay_bundle_ref=common_refs.replay_bundle_ref,
    )
    return artifact, fetch, source


def _build_field_evidence(
    *,
    manifest: EcommerceOfficialApiBenchmarkManifest,
    target: EcommerceOfficialApiTargetSpec,
    artifact: EcommerceOfficialApiRedactedArtifact,
    source_fetch: EcommerceOfficialApiSourceFetch,
    extracted: _ExtractedFields,
    common_refs: _CommonRefs,
) -> list[EcommerceOfficialApiFieldEvidence]:
    base = f"{manifest.id}:{target.id}:official-api"
    fields = [
        EcommerceOfficialApiFieldEvidence(
            id=f"field-evidence:{base}:identity",
            fixture_id=manifest.id,
            target_spec_ref=target.id,
            site_name=target.site_name,
            field_name="identity",
            raw_text=cast(str, extracted.identity_raw_text),
            normalized_value=" ".join(extracted.identity_terms_matched),
            source_anchor_ref=f"source-anchor:{base}:field:identity",
            redacted_artifact_ref=artifact.id,
            content_hash_ref=artifact.content_hash_ref,
            credential_audit_ref=source_fetch.credential_audit_ref,
            policy_decision_refs=common_refs.policy_decision_refs,
            command_record_refs=common_refs.command_record_refs,
            event_cursor_refs=common_refs.event_cursor_refs,
            outbox_refs=common_refs.outbox_refs,
            replay_bundle_ref=common_refs.replay_bundle_ref,
        ),
        EcommerceOfficialApiFieldEvidence(
            id=f"field-evidence:{base}:price",
            fixture_id=manifest.id,
            target_spec_ref=target.id,
            site_name=target.site_name,
            field_name="price",
            raw_text=cast(str, extracted.price_raw_text),
            normalized_value=cast(str, extracted.price_raw_text),
            amount=cast(float, extracted.price_amount),
            currency=cast(str, extracted.price_currency),
            source_anchor_ref=f"source-anchor:{base}:field:price",
            redacted_artifact_ref=artifact.id,
            content_hash_ref=artifact.content_hash_ref,
            credential_audit_ref=source_fetch.credential_audit_ref,
            policy_decision_refs=common_refs.policy_decision_refs,
            command_record_refs=common_refs.command_record_refs,
            event_cursor_refs=common_refs.event_cursor_refs,
            outbox_refs=common_refs.outbox_refs,
            replay_bundle_ref=common_refs.replay_bundle_ref,
        ),
        EcommerceOfficialApiFieldEvidence(
            id=f"field-evidence:{base}:availability",
            fixture_id=manifest.id,
            target_spec_ref=target.id,
            site_name=target.site_name,
            field_name="availability",
            raw_text=cast(str, extracted.availability_raw_text),
            normalized_value=cast(str, extracted.availability_status),
            source_anchor_ref=f"source-anchor:{base}:field:availability",
            redacted_artifact_ref=artifact.id,
            content_hash_ref=artifact.content_hash_ref,
            credential_audit_ref=source_fetch.credential_audit_ref,
            policy_decision_refs=common_refs.policy_decision_refs,
            command_record_refs=common_refs.command_record_refs,
            event_cursor_refs=common_refs.event_cursor_refs,
            outbox_refs=common_refs.outbox_refs,
            replay_bundle_ref=common_refs.replay_bundle_ref,
        ),
    ]
    return fields


def _passing_site_result(
    *,
    manifest: EcommerceOfficialApiBenchmarkManifest,
    target: EcommerceOfficialApiTargetSpec,
    source: AuthorizedSourceAccessRecord,
    fetch: EcommerceOfficialApiSourceFetch,
    artifact: EcommerceOfficialApiRedactedArtifact,
    field_evidence: list[EcommerceOfficialApiFieldEvidence],
    extracted: _ExtractedFields,
    common_refs: _CommonRefs,
) -> EcommerceOfficialApiSiteResult:
    field_refs = [field.id for field in field_evidence]
    return EcommerceOfficialApiSiteResult(
        id=f"site-result:{manifest.id}:{target.id}:official-api",
        fixture_id=manifest.id,
        target_spec_ref=target.id,
        site_name=target.site_name,
        platform=target.platform,
        api_family=target.api_family,
        field_evidence_refs=field_refs,
        identity_evidence_ref=field_refs[0],
        price_evidence_ref=field_refs[1],
        availability_evidence_ref=field_refs[2],
        price_raw_text=extracted.price_raw_text,
        price_amount=extracted.price_amount,
        price_currency=extracted.price_currency,
        availability_raw_text=extracted.availability_raw_text,
        availability_status=extracted.availability_status,
        authorized_source_ref=source.id,
        redacted_artifact_refs=[artifact.id],
        source_anchor_refs=fetch.source_anchor_refs,
        content_hash_refs=[fetch.content_hash_ref],
        credential_audit_refs=[fetch.credential_audit_ref],
        policy_decision_refs=common_refs.policy_decision_refs,
        command_record_refs=common_refs.command_record_refs,
        event_cursor_refs=common_refs.event_cursor_refs,
        outbox_refs=common_refs.outbox_refs,
        replay_bundle_refs=[common_refs.replay_bundle_ref],
        completion_result=CompletenessResult.PASS,
    )


def _failure_site_result(
    *,
    manifest: EcommerceOfficialApiBenchmarkManifest,
    target: EcommerceOfficialApiTargetSpec,
    failure_type: str,
    diagnostics: list[str],
    missing_ref_fields: list[str],
    common_refs: _CommonRefs,
) -> EcommerceOfficialApiSiteResult:
    base = f"{manifest.id}:{target.id}:official-api"
    return EcommerceOfficialApiSiteResult(
        id=f"site-result:{base}",
        fixture_id=manifest.id,
        target_spec_ref=target.id,
        site_name=target.site_name,
        platform=target.platform,
        api_family=target.api_family,
        policy_decision_refs=common_refs.policy_decision_refs,
        command_record_refs=common_refs.command_record_refs,
        event_cursor_refs=common_refs.event_cursor_refs,
        outbox_refs=common_refs.outbox_refs,
        replay_bundle_refs=[common_refs.replay_bundle_ref],
        blocked_source_refs=[f"blocked-source:{base}:{failure_type}"],
        failure_type=failure_type,
        missing_ref_fields=missing_ref_fields,
        diagnostics=diagnostics,
        completion_result=CompletenessResult.NEEDS_REVIEW,
    )


def _build_report(
    *,
    manifest: EcommerceOfficialApiBenchmarkManifest,
    site_results: list[EcommerceOfficialApiSiteResult],
    field_evidence: list[EcommerceOfficialApiFieldEvidence],
    source_fetches: list[EcommerceOfficialApiSourceFetch],
    redacted_artifacts: list[EcommerceOfficialApiRedactedArtifact],
    authorized_sources: list[AuthorizedSourceAccessRecord],
) -> EcommerceOfficialApiBenchmarkReport:
    completion = (
        CompletenessResult.PASS
        if len(site_results) == len(manifest.target_specs)
        and all(site.completion_result == CompletenessResult.PASS for site in site_results)
        else CompletenessResult.NEEDS_REVIEW
    )
    diagnostics = [
        diagnostic
        for site in site_results
        if site.completion_result != CompletenessResult.PASS
        for diagnostic in site.diagnostics
    ]
    blocked = [
        site.id for site in site_results if site.completion_result != CompletenessResult.PASS
    ]
    blocked_source_refs = [
        source_ref for site in site_results for source_ref in site.blocked_source_refs
    ]
    source_anchor_refs = sorted(
        {source_anchor for fetch in source_fetches for source_anchor in fetch.source_anchor_refs}
    )
    content_hash_refs = sorted({fetch.content_hash_ref for fetch in source_fetches})
    credential_audit_refs = sorted({fetch.credential_audit_ref for fetch in source_fetches})
    common_policy_refs = sorted(
        {policy for site in site_results for policy in site.policy_decision_refs}
    )
    common_command_refs = sorted(
        {command for site in site_results for command in site.command_record_refs}
    )
    common_event_refs = sorted(
        {event for site in site_results for event in site.event_cursor_refs}
    )
    common_outbox_refs = sorted({outbox for site in site_results for outbox in site.outbox_refs})
    common_replay_refs = sorted(
        {replay for site in site_results for replay in site.replay_bundle_refs}
    )
    all_failures = [site.failure_type for site in site_results if site.failure_type]
    credentials_only = all_failures and all(
        failure == "official_api_credentials_unavailable" for failure in all_failures
    )
    base_fields = {
        "id": f"ecommerce-official-api-report:{manifest.id}",
        "fixture_id": manifest.id,
        "run_ref": f"run:{manifest.id}:ecommerce-official-api",
        "target_site_count": len(manifest.target_specs),
        "site_result_refs": [site.id for site in site_results],
        "passing_site_result_refs": [
            site.id
            for site in site_results
            if site.completion_result == CompletenessResult.PASS
        ],
        "blocked_site_result_refs": blocked,
        "field_evidence_refs": [field.id for field in field_evidence],
        "authorized_source_refs": [source.id for source in authorized_sources],
        "redacted_artifact_refs": [artifact.id for artifact in redacted_artifacts],
        "source_anchor_refs": source_anchor_refs,
        "content_hash_refs": content_hash_refs,
        "credential_audit_refs": credential_audit_refs,
        "policy_decision_refs": common_policy_refs,
        "command_record_refs": common_command_refs,
        "event_cursor_refs": common_event_refs,
        "outbox_refs": common_outbox_refs,
        "replay_bundle_refs": common_replay_refs,
        "source_fetch_refs": [fetch.id for fetch in source_fetches],
        "blocked_source_refs": blocked_source_refs,
        "operator_status": (
            "ecommerce_official_api_completed"
            if completion == CompletenessResult.PASS
            else (
                "ecommerce_official_api_credentials_required"
                if credentials_only
                else "ecommerce_official_api_source_review_required"
            )
        ),
        "completion_result": completion,
    }
    if completion == CompletenessResult.PASS:
        return EcommerceOfficialApiBenchmarkReport(**base_fields)
    return EcommerceOfficialApiBenchmarkReport(
        **base_fields,
        failure_type=(
            "official_api_credentials_unavailable"
            if credentials_only
            else "official_api_source_review_required"
        ),
        missing_ref_fields=sorted(
            {field for site in site_results for field in site.missing_ref_fields}
        ),
        diagnostics=diagnostics or ["official ecommerce API benchmark requires review"],
    )


def _extract_fields(
    *,
    target: EcommerceOfficialApiTargetSpec,
    payload: object,
    body_text: str,
) -> _ExtractedFields:
    item = _first_item(target.platform, payload)
    identity_raw = _identity_text(target.platform, item)
    combined_identity_text = f"{identity_raw or ''}\n{body_text}"
    matched = [
        term
        for term in target.required_identity_terms
        if term.lower() in combined_identity_text.lower()
    ]
    price_raw, amount, currency = _price(target.platform, item)
    availability_raw, availability_status = _availability(target.platform, item)
    return _ExtractedFields(
        identity_raw_text=identity_raw,
        identity_terms_matched=matched,
        price_raw_text=price_raw,
        price_amount=amount,
        price_currency=currency,
        availability_raw_text=availability_raw,
        availability_status=availability_status,
    )


def _missing_fields(
    target: EcommerceOfficialApiTargetSpec,
    extracted: _ExtractedFields,
) -> list[str]:
    missing: list[str] = []
    if extracted.identity_raw_text is None:
        missing.append("identity_evidence_ref")
    if set(extracted.identity_terms_matched) != set(target.required_identity_terms):
        missing.append("identity_terms_matched")
    if (
        extracted.price_raw_text is None
        or extracted.price_amount is None
        or not extracted.price_currency
    ):
        missing.append("price_evidence_ref")
    if extracted.availability_raw_text is None or extracted.availability_status is None:
        missing.append("availability_evidence_ref")
    return missing


def _first_item(platform: str, payload: object) -> Mapping[str, object] | None:
    paths: list[Sequence[str | int]]
    if platform == "ebay":
        paths = [
            ("itemSummaries", 0),
            ("itemSummary",),
            ("items", 0),
        ]
    else:
        paths = [
            ("ItemResults", "Items", 0),
            ("ItemsResult", "Items", 0),
            ("itemsResult", "items", 0),
            ("data", "items", 0),
            ("items", 0),
            ("item",),
        ]
    for path in paths:
        value = _lookup(payload, path)
        mapping = _as_mapping(value)
        if mapping is not None:
            return mapping
    return _as_mapping(payload)


def _identity_text(platform: str, item: Mapping[str, object] | None) -> str | None:
    if item is None:
        return None
    paths: list[Sequence[str | int]]
    if platform == "ebay":
        paths = [("title",), ("shortDescription",)]
    else:
        paths = [
            ("ItemInfo", "Title", "DisplayValue"),
            ("itemInfo", "title", "displayValue"),
            ("title",),
            ("product", "title"),
        ]
    return _first_str(item, paths)


def _price(
    platform: str,
    item: Mapping[str, object] | None,
) -> tuple[str | None, float | None, str | None]:
    if item is None:
        return None, None, None
    if platform == "ebay":
        price_obj = _first_mapping(
            item,
            [
                ("price",),
                ("currentBidPrice",),
                ("marketingPrice", "originalPrice"),
            ],
        )
    else:
        price_obj = _first_mapping(
            item,
            [
                ("OffersV2", "Listings", 0, "Price", "Money"),
                ("OffersV2", "Listings", 0, "Price"),
                ("offersV2", "listings", 0, "price"),
                ("Offers", "Listings", 0, "Price"),
                ("Offers", "Summaries", 0, "LowestPrice"),
                ("Offers", "Summaries", 0, "HighestPrice"),
                ("offers", "listings", 0, "price"),
            ],
        )
    if price_obj is None:
        return None, None, None
    amount = _first_number(price_obj, [("Amount",), ("amount",), ("value",), ("Value",)])
    currency = _first_str(
        price_obj,
        [("Currency",), ("CurrencyCode",), ("currency",), ("currencyCode",)],
    )
    display = _first_str(
        price_obj,
        [("DisplayAmount",), ("displayAmount",), ("displayValue",), ("value",)],
    )
    if display is None and amount is not None and currency is not None:
        display = f"{currency} {amount:.2f}"
    return display, amount, currency


def _availability(
    platform: str,
    item: Mapping[str, object] | None,
) -> tuple[str | None, str | None]:
    if item is None:
        return None, None
    if platform == "ebay":
        availability_obj = _first_mapping(
            item,
            [
                ("estimatedAvailabilities", 0),
                ("availability",),
            ],
        )
        if availability_obj is None:
            return "available_listing", "in_stock"
        raw = _first_str(
            availability_obj,
            [
                ("estimatedAvailabilityStatus",),
                ("availabilityStatus",),
                ("status",),
            ],
        )
    else:
        availability_obj = _first_mapping(
            item,
            [
                ("OffersV2", "Listings", 0, "Availability"),
                ("offersV2", "listings", 0, "availability"),
                ("Offers", "Listings", 0, "Availability"),
                ("offers", "listings", 0, "availability"),
                ("availability",),
            ],
        )
        raw = (
            _first_str(
                availability_obj,
                [("Message",), ("message",), ("Type",), ("type",), ("status",)],
            )
            if availability_obj is not None
            else None
        )
    if raw is None:
        return None, None
    return raw, _normalize_availability(raw)


def _lookup(value: object, path: Sequence[str | int]) -> object | None:
    current: object | None = value
    for part in path:
        if current is None:
            return None
        if isinstance(part, int):
            if isinstance(current, list) and 0 <= part < len(current):
                current = current[part]
            else:
                return None
        else:
            mapping = _as_mapping(current)
            if mapping is None:
                return None
            current = _mapping_get(mapping, part)
    return current


def _mapping_get(mapping: Mapping[str, object], key: str) -> object | None:
    if key in mapping:
        return mapping[key]
    key_lower = key.lower()
    for candidate, value in mapping.items():
        if candidate.lower() == key_lower:
            return value
    return None


def _as_mapping(value: object | None) -> Mapping[str, object] | None:
    if isinstance(value, dict):
        return cast(Mapping[str, object], value)
    return None


def _first_mapping(
    value: object,
    paths: Sequence[Sequence[str | int]],
) -> Mapping[str, object] | None:
    for path in paths:
        mapping = _as_mapping(_lookup(value, path))
        if mapping is not None:
            return mapping
    return None


def _first_str(value: object, paths: Sequence[Sequence[str | int]]) -> str | None:
    for path in paths:
        candidate = _lookup(value, path)
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
        if isinstance(candidate, int | float):
            return str(candidate)
    return None


def _first_number(value: object, paths: Sequence[Sequence[str | int]]) -> float | None:
    for path in paths:
        candidate = _lookup(value, path)
        if isinstance(candidate, int | float):
            return float(candidate)
        if isinstance(candidate, str):
            try:
                return float(candidate.replace(",", ""))
            except ValueError:
                continue
    return None


def _normalize_availability(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    if any(token in normalized for token in ("out_of_stock", "unavailable", "sold_out")):
        return "out_of_stock"
    if any(token in normalized for token in ("limited", "low_stock", "only")):
        return "limited"
    if any(token in normalized for token in ("in_stock", "available", "instock")):
        return "in_stock"
    return normalized or "unknown"


def _source_anchor_refs(
    *,
    base: str,
    payload_text: str,
    extracted: _ExtractedFields,
) -> list[Ref]:
    refs = [
        f"source-anchor:{base}:response-status",
        f"source-anchor:{base}:response-body",
    ]
    try:
        payload = json.loads(payload_text)
    except json.JSONDecodeError:
        refs.append(f"source-anchor:{base}:json-parse-failed")
    else:
        mapping = _as_mapping(payload)
        if mapping is not None:
            refs.extend(
                f"source-anchor:{base}:json-key:{_slug(key)}"
                for key in sorted(mapping)[:8]
            )
    if extracted.identity_raw_text:
        refs.append(f"source-anchor:{base}:field:identity")
    if extracted.price_raw_text:
        refs.append(f"source-anchor:{base}:field:price")
    if extracted.availability_raw_text:
        refs.append(f"source-anchor:{base}:field:availability")
    return sorted(set(refs))


def _content_type(headers: Mapping[str, str]) -> str:
    for key, value in headers.items():
        if key.lower() == "content-type":
            return value.split(";", 1)[0].strip() or "application/octet-stream"
    return "application/octet-stream"


def _common_refs(base: str) -> _CommonRefs:
    return _CommonRefs(
        policy_decision_refs=[
            f"policy:{base}:authorized-source",
            f"policy:{base}:credential-scope",
            f"policy:{base}:no-bypass",
        ],
        command_record_refs=[f"command:{base}:read-product-official-api"],
        event_cursor_refs=[f"event-cursor:{base}:official-api-product-read"],
        outbox_refs=[f"outbox:{base}:official-api-product-read"],
        replay_bundle_ref=f"replay-bundle:{base}:official-api-product",
    )


def _redact_text(text: str) -> str:
    redacted = re.sub(
        r"(?i)(authorization|api[_-]?key|access[_-]?token|refresh[_-]?token|token|"
        r"secret|password|cookie|set-cookie)([\"'\s:=]+)([^\"'\s,}]+)",
        r"\1\2[REDACTED]",
        text,
    )
    return re.sub(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        "[REDACTED_EMAIL]",
        redacted,
    )


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "field"
