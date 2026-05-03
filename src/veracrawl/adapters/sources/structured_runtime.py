"""Adapter-owned structured source fixture parsing."""

from __future__ import annotations

import csv
import json
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    CompletenessResult,
    SourceAdapterResultType,
)
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult
from veracrawl.contracts.source_runtime import StructuredSourceAdapterRecord
from veracrawl.fetch.acquisition import SourceAcquisitionOutcome, execute_source_acquisition


@dataclass(frozen=True)
class StructuredSourceMaterialization:
    artifact_ref: Ref
    natural_result_refs: list[Ref]
    metadata_refs: list[Ref]
    evidence_seed_refs: list[Ref]
    discovered_url_refs: list[Ref]
    api_payload_refs: list[Ref]
    document_artifact_refs: list[Ref]
    file_artifact_refs: list[Ref]
    content_hash_refs: list[Ref]
    replay_refs: list[Ref]


_SOURCE_FILE_BY_ADAPTER = {
    AdapterType.SITEMAP: "sitemap.xml",
    AdapterType.RSS: "feed.xml",
    AdapterType.API_SOURCE: "api.json",
    AdapterType.DOCUMENT_SOURCE: "document.txt",
    AdapterType.FILE_IMPORT: "import.csv",
}

_RESULT_TYPE_BY_ADAPTER = {
    AdapterType.SITEMAP: SourceAdapterResultType.DISCOVERED_LINKS,
    AdapterType.RSS: SourceAdapterResultType.DISCOVERED_LINKS,
    AdapterType.API_SOURCE: SourceAdapterResultType.API_PAYLOAD,
    AdapterType.DOCUMENT_SOURCE: SourceAdapterResultType.DOCUMENT_ARTIFACT,
    AdapterType.FILE_IMPORT: SourceAdapterResultType.FILE_ARTIFACT,
}


class StructuredFixtureSourceAdapter:
    def __init__(self, *, adapter_type: AdapterType, source_path: Path) -> None:
        if adapter_type not in _SOURCE_FILE_BY_ADAPTER:
            raise ValueError(f"unsupported structured source adapter: {adapter_type.value}")
        self.adapter_type = adapter_type
        self.source_path = source_path
        self.last_materialization: StructuredSourceMaterialization | None = None

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        content = self.source_path.read_text(encoding="utf-8")
        fixture_key = _fixture_key(command.command_envelope_id)
        parsed = _parse_source(self.adapter_type, content)
        digest = stable_hash(
            {
                "adapter_type": self.adapter_type.value,
                "source_path": str(self.source_path),
                "parsed": parsed,
            }
        )
        artifact_ref = (
            f"artifact:{command.command_envelope_id}:{self.adapter_type.value}:raw:{digest[:12]}"
        )
        materialization = _materialization(
            fixture_key=fixture_key,
            adapter_type=self.adapter_type,
            artifact_ref=artifact_ref,
            parsed=parsed,
            digest=digest,
        )
        self.last_materialization = materialization
        return SourceAdapterResult(
            id=f"source-result:{command.command_envelope_id}",
            run_id=f"run:{fixture_key}",
            adapter_spec_id=command.adapter_spec.id,
            adapter_type=command.adapter_spec.adapter_type,
            result_type=_RESULT_TYPE_BY_ADAPTER[self.adapter_type],
            output_refs=[artifact_ref],
            policy_decision_refs=[f"policy:{fixture_key}:structured-source"],
            replay_event_refs=materialization.replay_refs,
            idempotency_key=f"{command.adapter_spec.id}:{self.source_path}:{digest}",
            status=AdapterResultStatus.SUCCEEDED,
        )


def build_structured_source_adapter_records(
    fixture_id: str,
    *,
    sources_root: Path,
    policy_decision_refs: list[Ref] | None = None,
) -> list[StructuredSourceAdapterRecord]:
    policy_refs = policy_decision_refs or [f"policy:{fixture_id}:structured-source"]
    records: list[StructuredSourceAdapterRecord] = []
    for adapter_type, filename in _SOURCE_FILE_BY_ADAPTER.items():
        slug = _adapter_slug(adapter_type)
        adapter = StructuredFixtureSourceAdapter(
            adapter_type=adapter_type,
            source_path=sources_root / filename,
        )
        outcome = execute_source_acquisition(
            fixture_id=f"{fixture_id}-{slug}",
            adapter_type=adapter_type,
            scenario="structured-source-success",
            adapter=adapter,
        )
        records.append(
            _record_from_outcome(
                fixture_id=fixture_id,
                adapter_type=adapter_type,
                outcome=outcome,
                materialization=_required_materialization(adapter),
                policy_decision_refs=policy_refs,
            )
        )
    return records


def _record_from_outcome(
    *,
    fixture_id: str,
    adapter_type: AdapterType,
    outcome: SourceAcquisitionOutcome,
    materialization: StructuredSourceMaterialization,
    policy_decision_refs: list[Ref],
) -> StructuredSourceAdapterRecord:
    if outcome.source_result is None:
        raise ValueError(f"{adapter_type.value} structured source missing adapter result")
    slug = _adapter_slug(adapter_type)
    document_refs = list(materialization.document_artifact_refs)
    if outcome.document_artifact is not None:
        document_refs.append(outcome.document_artifact.id)
    return StructuredSourceAdapterRecord(
        id=f"structured-source-adapter-record:{fixture_id}:{slug}",
        adapter_type=adapter_type,
        source_adapter_result_ref=outcome.source_result.id,
        natural_result_refs=materialization.natural_result_refs,
        artifact_refs=sorted(set(outcome.report.artifact_refs + [materialization.artifact_ref])),
        metadata_refs=materialization.metadata_refs,
        evidence_seed_refs=materialization.evidence_seed_refs,
        discovered_url_refs=materialization.discovered_url_refs,
        api_payload_refs=materialization.api_payload_refs,
        document_artifact_refs=sorted(set(document_refs)),
        file_artifact_refs=materialization.file_artifact_refs,
        fetch_attempt_refs=outcome.report.fetch_attempt_refs,
        fetch_result_refs=outcome.report.fetch_result_refs,
        page_snapshot_refs=[outcome.page_snapshot.id] if outcome.page_snapshot else [],
        policy_decision_refs=sorted(
            set(policy_decision_refs + outcome.report.policy_decision_refs)
        ),
        command_record_refs=outcome.report.command_record_refs,
        event_cursor_refs=outcome.report.event_cursor_refs,
        outbox_refs=outcome.report.outbox_refs,
        replay_refs=materialization.replay_refs,
        content_hash_refs=materialization.content_hash_refs,
        result=CompletenessResult.PASS,
    )


def _parse_source(adapter_type: AdapterType, content: str) -> dict[str, Any]:
    if adapter_type == AdapterType.SITEMAP:
        urls = [_text(node) for node in ET.fromstring(content).iter() if _local_name(node) == "loc"]
        return {"urls": [url for url in urls if url]}
    if adapter_type == AdapterType.RSS:
        root = ET.fromstring(content)
        links = [
            _text(child)
            for item in root.iter()
            if _local_name(item) == "item"
            for child in item
            if _local_name(child) == "link"
        ]
        return {"urls": [link for link in links if link]}
    if adapter_type == AdapterType.API_SOURCE:
        data = json.loads(content)
        if not isinstance(data, dict):
            raise ValueError("api source fixture must contain a JSON object")
        records = data.get("records")
        if not isinstance(records, list) or not records:
            raise ValueError("api source fixture must contain records")
        return {"records": records}
    if adapter_type == AdapterType.DOCUMENT_SOURCE:
        lines = [line.strip() for line in content.splitlines() if line.strip()]
        if not lines:
            raise ValueError("document source fixture must not be empty")
        return {"title": lines[0], "line_count": len(lines)}
    if adapter_type == AdapterType.FILE_IMPORT:
        rows = list(csv.DictReader(content.splitlines()))
        if not rows:
            raise ValueError("file import fixture must contain rows")
        return {"rows": rows}
    raise ValueError(f"unsupported structured source adapter: {adapter_type.value}")


def _materialization(
    *,
    fixture_key: str,
    adapter_type: AdapterType,
    artifact_ref: Ref,
    parsed: dict[str, Any],
    digest: str,
) -> StructuredSourceMaterialization:
    slug = _adapter_slug(adapter_type)
    base = f"{fixture_key}:{slug}"
    discovered = [
        f"url-ref:{base}:{index}:{stable_hash(url)[:12]}"
        for index, url in enumerate(parsed.get("urls", []), start=1)
    ]
    api_payloads = (
        [f"api-payload:{base}:{digest[:12]}"] if adapter_type == AdapterType.API_SOURCE else []
    )
    document_refs = (
        [f"document-artifact:{base}:{digest[:12]}"]
        if adapter_type == AdapterType.DOCUMENT_SOURCE
        else []
    )
    file_refs = (
        [f"file-artifact:{base}:{digest[:12]}"]
        if adapter_type == AdapterType.FILE_IMPORT
        else []
    )
    natural_refs = discovered + api_payloads + document_refs + file_refs
    return StructuredSourceMaterialization(
        artifact_ref=artifact_ref,
        natural_result_refs=natural_refs,
        metadata_refs=[f"metadata:{base}:{digest[:12]}"],
        evidence_seed_refs=[f"evidence-seed:{base}:{digest[:12]}"],
        discovered_url_refs=discovered,
        api_payload_refs=api_payloads,
        document_artifact_refs=document_refs,
        file_artifact_refs=file_refs,
        content_hash_refs=[f"content-hash:{base}:{digest}"],
        replay_refs=[f"replay:{base}:{digest[:12]}"],
    )


def _required_materialization(
    adapter: StructuredFixtureSourceAdapter,
) -> StructuredSourceMaterialization:
    if adapter.last_materialization is None:
        raise ValueError("structured source adapter did not materialize refs")
    return adapter.last_materialization


def _fixture_key(command_envelope_id: Ref) -> str:
    return command_envelope_id.removeprefix("cmd:").removesuffix(":source")


def _adapter_slug(adapter_type: AdapterType) -> str:
    return adapter_type.value.replace("_", "-")


def _local_name(node: ET.Element[str]) -> str:
    return node.tag.rsplit("}", 1)[-1]


def _text(node: ET.Element[str]) -> str:
    return (node.text or "").strip()
