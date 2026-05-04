"""Live official API evidence runtime for authorized source access.

This module is a benchmark/runtime adapter layer. It intentionally keeps live
HTTP acquisition outside the production-grade contracts so core remains coupled
only to VeraCrawl's neutral records and refs.
"""

from __future__ import annotations

import hashlib
import ipaddress
import json
import re
import socket
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass

from pydantic import Field

from veracrawl.benchmarks.production_grade import ProductionGradeGateResult
from veracrawl.contracts.common import Ref, TimestampedModel
from veracrawl.contracts.enums import CompletenessResult
from veracrawl.contracts.production_grade import (
    AuthorizedSourceAccessRecord,
    ProductionGateReport,
    ProductionGradeClosureManifest,
    ProductionSourceProfile,
)

_USER_AGENT = "VeraCrawl-authorized-source-live/1"
_MAX_BODY_BYTES = 768 * 1024
_AUTHORIZED_SOURCE_CAPABILITIES = (
    "official_api_adapter",
    "credentialed_read_session",
    "redacted_replay",
)


class LiveOfficialApiResponse(TimestampedModel):
    status_code: int
    final_url: str
    headers: dict[str, str] = Field(default_factory=dict)
    body: bytes


class LiveAuthorizedSourceFetch(TimestampedModel):
    id: str
    fixture_id: str
    source_profile_ref: Ref
    url: str
    final_url: str
    status_code: int
    content_type: str
    byte_count: int
    content_hash_ref: Ref
    redacted_artifact_ref: Ref
    source_anchor_refs: list[Ref] = Field(default_factory=list)
    credential_audit_ref: Ref
    policy_decision_refs: list[Ref] = Field(default_factory=list)
    command_record_refs: list[Ref] = Field(default_factory=list)
    event_cursor_refs: list[Ref] = Field(default_factory=list)
    outbox_refs: list[Ref] = Field(default_factory=list)
    replay_bundle_ref: Ref


class LiveRedactedSourceArtifact(TimestampedModel):
    id: str
    fixture_id: str
    source_profile_ref: Ref
    source_url: str
    status_code: int
    content_type: str
    byte_count: int
    content_hash_ref: Ref
    redaction_policy_refs: list[Ref] = Field(default_factory=list)
    body_preview: str
    body_preview_truncated: bool


@dataclass(frozen=True)
class LiveAuthorizedSourceGateResult:
    gate_result: ProductionGradeGateResult
    source_fetches: list[LiveAuthorizedSourceFetch]
    redacted_artifacts: list[LiveRedactedSourceArtifact]


LiveOfficialApiFetcher = Callable[
    [ProductionSourceProfile, int],
    LiveOfficialApiResponse,
]


def run_live_authorized_source_gate(
    *,
    manifest: ProductionGradeClosureManifest,
    profile: str,
    fetcher: LiveOfficialApiFetcher | None = None,
) -> LiveAuthorizedSourceGateResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"fixture {manifest.id} does not support profile {profile}")
    if manifest.gate_type != "authorized_source_access":
        raise ValueError("live authorized source runner requires authorized_source_access gate")

    fetcher = fetcher or fetch_public_official_api
    records: list[AuthorizedSourceAccessRecord] = []
    fetches: list[LiveAuthorizedSourceFetch] = []
    artifacts: list[LiveRedactedSourceArtifact] = []
    diagnostics: list[str] = []

    expected_profiles = [
        source_profile
        for source_profile in manifest.source_profiles
        if source_profile.official_api_available or source_profile.authorized_source_ref
    ]
    for source_profile in expected_profiles:
        if not source_profile.official_api_available:
            diagnostics.append(
                f"{source_profile.id} requires a credentialed session; "
                "live official API runner will not fabricate credentialed access"
            )
            continue
        try:
            response = fetcher(source_profile, manifest.crawl_bound.max_runtime_ms)
        except (OSError, ValueError) as exc:
            diagnostics.append(f"{source_profile.id} fetch failed: {exc}")
            continue
        if not 200 <= response.status_code < 300:
            diagnostics.append(
                f"{source_profile.id} official API returned HTTP {response.status_code}"
            )
            continue
        if not response.body:
            diagnostics.append(f"{source_profile.id} official API returned empty body")
            continue

        artifact, fetch, record = _build_live_authorized_record(
            fixture_id=manifest.id,
            source_profile=source_profile,
            response=response,
        )
        artifacts.append(artifact)
        fetches.append(fetch)
        records.append(record)

    report = _build_live_report(
        manifest=manifest,
        records=records,
        fetches=fetches,
        artifacts=artifacts,
        diagnostics=diagnostics,
        expected_count=len(expected_profiles),
    )
    return LiveAuthorizedSourceGateResult(
        gate_result=ProductionGradeGateResult(
            report=report,
            discovery_plans=[],
            candidate_targets=[],
            discovery_entry_points=[],
            discovery_approval_decisions=[],
            acquisition_attempts=[],
            authorized_sources=records,
            capability_matrices=[],
            release_decisions=[],
            false_ready_guards=[],
            release_blockers=[],
            release_reports=[],
        ),
        source_fetches=fetches,
        redacted_artifacts=artifacts,
    )


def fetch_public_official_api(
    source_profile: ProductionSourceProfile,
    timeout_ms: int,
) -> LiveOfficialApiResponse:
    _validate_public_url(source_profile.entry_point_url, source_profile.allowed_origin)
    request = urllib.request.Request(
        source_profile.entry_point_url,
        headers={
            "Accept": "application/json, text/plain;q=0.9, */*;q=0.1",
            "User-Agent": _USER_AGENT,
        },
        method="GET",
    )
    timeout_seconds = max(timeout_ms / 1000, 1)
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(_MAX_BODY_BYTES + 1)
            headers = {str(key): str(value) for key, value in response.headers.items()}
            return LiveOfficialApiResponse(
                status_code=int(response.status),
                final_url=str(response.geturl()),
                headers=headers,
                body=_bounded_body(body),
            )
    except urllib.error.HTTPError as exc:
        body = exc.read(_MAX_BODY_BYTES + 1)
        headers = {str(key): str(value) for key, value in exc.headers.items()}
        return LiveOfficialApiResponse(
            status_code=int(exc.code),
            final_url=str(exc.url),
            headers=headers,
            body=_bounded_body(body),
        )
    except urllib.error.URLError as exc:
        raise OSError(str(exc)) from exc


def _bounded_body(body: bytes) -> bytes:
    if len(body) > _MAX_BODY_BYTES:
        raise ValueError(f"official API response exceeds {_MAX_BODY_BYTES} bytes")
    return body


def _validate_public_url(url: str, allowed_origin: str) -> None:
    parsed = urllib.parse.urlparse(url)
    origin = urllib.parse.urlparse(allowed_origin)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("official API URL must be absolute http(s)")
    if origin.scheme not in {"http", "https"} or not origin.hostname:
        raise ValueError("allowed origin must be absolute http(s)")
    if parsed.scheme != origin.scheme or parsed.hostname != origin.hostname:
        raise ValueError("official API URL must stay inside allowed origin")
    host = parsed.hostname.lower()
    if host == "localhost" or host.endswith(".localhost") or host.endswith(".local"):
        raise ValueError("private or local official API hosts are denied")
    for address in _resolve_host_addresses(host, parsed.port):
        if not address.is_global:
            raise ValueError(f"private or non-global official API address denied: {address}")


def _resolve_host_addresses(
    host: str,
    port: int | None,
) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        return [ipaddress.ip_address(host)]
    except ValueError:
        pass
    try:
        infos = socket.getaddrinfo(host, port or 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ValueError(f"failed to resolve official API host {host}: {exc}") from exc
    addresses: list[ipaddress.IPv4Address | ipaddress.IPv6Address] = []
    for info in infos:
        sockaddr = info[4]
        if sockaddr:
            addresses.append(ipaddress.ip_address(str(sockaddr[0])))
    if not addresses:
        raise ValueError(f"failed to resolve official API host {host}")
    return addresses


def _build_live_authorized_record(
    *,
    fixture_id: str,
    source_profile: ProductionSourceProfile,
    response: LiveOfficialApiResponse,
) -> tuple[
    LiveRedactedSourceArtifact,
    LiveAuthorizedSourceFetch,
    AuthorizedSourceAccessRecord,
]:
    base = f"{fixture_id}:{source_profile.id}:official-api"
    body_text = response.body.decode("utf-8", errors="replace")
    content_hash_ref = f"sha256:{hashlib.sha256(response.body).hexdigest()}"
    content_type = _content_type(response.headers)
    source_anchor_refs = _source_anchor_refs(
        fixture_id=fixture_id,
        source_profile=source_profile,
        content_type=content_type,
        body_text=body_text,
    )
    redacted_preview = _redact_text(body_text)[:4000]
    artifact = LiveRedactedSourceArtifact(
        id=f"artifact:{base}:redacted-source",
        fixture_id=fixture_id,
        source_profile_ref=source_profile.id,
        source_url=response.final_url,
        status_code=response.status_code,
        content_type=content_type,
        byte_count=len(response.body),
        content_hash_ref=content_hash_ref,
        redaction_policy_refs=[
            f"redaction-policy:{fixture_id}:{source_profile.id}:secrets",
            f"redaction-policy:{fixture_id}:{source_profile.id}:personal-data",
        ],
        body_preview=redacted_preview,
        body_preview_truncated=len(body_text) > len(redacted_preview),
    )
    fetch = LiveAuthorizedSourceFetch(
        id=f"authorized-source-fetch:{base}",
        fixture_id=fixture_id,
        source_profile_ref=source_profile.id,
        url=source_profile.entry_point_url,
        final_url=response.final_url,
        status_code=response.status_code,
        content_type=content_type,
        byte_count=len(response.body),
        content_hash_ref=content_hash_ref,
        redacted_artifact_ref=artifact.id,
        source_anchor_refs=source_anchor_refs,
        credential_audit_ref=f"credential-audit:{base}:public-no-secret",
        policy_decision_refs=_policy_refs(fixture_id, source_profile.id),
        command_record_refs=[f"command:{base}:read-official-api"],
        event_cursor_refs=[f"event-cursor:{base}:official-api-read"],
        outbox_refs=[f"outbox:{base}:official-api-read"],
        replay_bundle_ref=f"replay-bundle:{base}:official-api",
    )
    record = AuthorizedSourceAccessRecord(
        id=f"authorized-source-result:{base}",
        fixture_id=fixture_id,
        source_profile_ref=source_profile.id,
        access_kind="official_api",
        credential_grant_ref=f"credential-grant:{base}:public-official-api-read",
        credential_audit_ref=fetch.credential_audit_ref,
        redacted_artifact_refs=[artifact.id],
        source_anchor_refs=source_anchor_refs,
        content_hash_refs=[content_hash_ref],
        policy_decision_refs=fetch.policy_decision_refs,
        command_record_refs=fetch.command_record_refs,
        event_cursor_refs=fetch.event_cursor_refs,
        outbox_refs=fetch.outbox_refs,
        replay_bundle_ref=fetch.replay_bundle_ref,
    )
    return artifact, fetch, record


def _content_type(headers: Mapping[str, str]) -> str:
    for key, value in headers.items():
        if key.lower() == "content-type":
            return value.split(";", 1)[0].strip() or "application/octet-stream"
    return "application/octet-stream"


def _source_anchor_refs(
    *,
    fixture_id: str,
    source_profile: ProductionSourceProfile,
    content_type: str,
    body_text: str,
) -> list[Ref]:
    base = f"{fixture_id}:{source_profile.id}:official-api"
    anchors = [
        f"source-anchor:{base}:response-status",
        f"source-anchor:{base}:response-body",
    ]
    if "json" in content_type:
        anchors.extend(_json_anchor_refs(base, body_text))
    return sorted(set(anchors))


def _json_anchor_refs(base: str, body_text: str) -> list[Ref]:
    try:
        payload = json.loads(body_text)
    except json.JSONDecodeError:
        return [f"source-anchor:{base}:json-parse-failed"]
    if isinstance(payload, dict):
        return [
            f"source-anchor:{base}:json-key:{_slug(str(key))}"
            for key in sorted(payload)[:8]
        ]
    if isinstance(payload, list):
        return [f"source-anchor:{base}:json-list:{min(len(payload), 8)}"]
    return [f"source-anchor:{base}:json-scalar"]


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


def _build_live_report(
    *,
    manifest: ProductionGradeClosureManifest,
    records: list[AuthorizedSourceAccessRecord],
    fetches: list[LiveAuthorizedSourceFetch],
    artifacts: list[LiveRedactedSourceArtifact],
    diagnostics: list[str],
    expected_count: int,
) -> ProductionGateReport:
    fixture_id = manifest.id
    completion = (
        CompletenessResult.PASS
        if expected_count > 0 and len(records) == expected_count and not diagnostics
        else CompletenessResult.NEEDS_REVIEW
    )
    source_anchor_refs = sorted(
        {source_anchor for record in records for source_anchor in record.source_anchor_refs}
    )
    content_hash_refs = sorted(
        {content_hash for record in records for content_hash in record.content_hash_refs}
    )
    base_fields = {
        "id": f"production-gate-report:{fixture_id}",
        "fixture_id": fixture_id,
        "gate_type": manifest.gate_type,
        "run_ref": f"run:{fixture_id}:live-official-api",
        "capability_refs": [
            f"capability:{manifest.gate_type}:{name}"
            for name in _AUTHORIZED_SOURCE_CAPABILITIES
        ],
        "authorized_source_refs": [record.id for record in records],
        "source_profile_refs": [profile.id for profile in manifest.source_profiles],
        "artifact_refs": [artifact.id for artifact in artifacts],
        "source_anchor_refs": source_anchor_refs,
        "content_hash_refs": content_hash_refs,
        "evidence_packet_refs": [
            f"evidence-packet:{fixture_id}:authorized-source:{index}"
            for index, _fetch in enumerate(fetches, start=1)
        ],
        "verification_decision_refs": [
            f"verification-decision:{fixture_id}:official-api:{index}"
            for index, _fetch in enumerate(fetches, start=1)
        ],
        "publication_gate_refs": [f"publication-gate:{fixture_id}:blocked-until-release"],
        "policy_decision_refs": _policy_refs(fixture_id),
        "command_record_refs": [f"command:{fixture_id}:record-live-authorized-source"],
        "event_cursor_refs": [
            f"event-cursor:{fixture_id}:live-authorized-source-recorded"
        ],
        "outbox_refs": [f"outbox:{fixture_id}:live-authorized-source"],
        "replay_bundle_refs": [f"replay-bundle:{fixture_id}:live-authorized-source"],
        "metrics": {
            "expected_authorized_source_count": expected_count,
            "authorized_source_count": len(records),
            "redacted_artifact_count": len(artifacts),
            "source_fetch_count": len(fetches),
        },
        "operator_status": (
            manifest.expected_operator_status
            if completion == CompletenessResult.PASS
            else "production_authorized_source_access_needs_review"
        ),
        "completion_result": completion,
    }
    if completion == CompletenessResult.PASS:
        return ProductionGateReport(**base_fields)
    return ProductionGateReport(
        **base_fields,
        release_blocker_refs=[f"release-blocker:{fixture_id}:authorized-source-live"],
        diagnostics=diagnostics
        or ["live authorized source access did not satisfy production gate"],
    )


def _policy_refs(fixture_id: str, profile_id: str | None = None) -> list[Ref]:
    suffix = f":{profile_id}" if profile_id else ""
    return [
        f"policy:{fixture_id}{suffix}:source-scope",
        f"policy:{fixture_id}{suffix}:robots",
        f"policy:{fixture_id}{suffix}:no-bypass",
    ]


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "field"
