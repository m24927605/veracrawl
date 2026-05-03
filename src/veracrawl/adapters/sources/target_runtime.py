"""Deterministic adapter-backed materialization for target runtime fixtures."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    CompletenessResult,
    SourceAdapterResultType,
)
from veracrawl.contracts.source_adapter import (
    SourceAdapterCommand,
    SourceAdapterResult,
    SourceAdapterSpec,
)
from veracrawl.contracts.target_runtime import (
    TargetAdapterBackedSourceEntry,
    TargetAdapterBackedSourceManifest,
    TargetAdapterBackedSourceRecord,
    TargetSourceCorpusEntry,
    TargetSourceCorpusManifest,
)

RESULT_TYPE_BY_ADAPTER: dict[AdapterType, SourceAdapterResultType] = {
    AdapterType.HTTP: SourceAdapterResultType.FETCH_RESULT,
    AdapterType.SITEMAP: SourceAdapterResultType.DISCOVERED_LINKS,
    AdapterType.RSS: SourceAdapterResultType.DISCOVERED_LINKS,
    AdapterType.BROWSER_SNAPSHOT: SourceAdapterResultType.BROWSER_SNAPSHOT,
    AdapterType.API_SOURCE: SourceAdapterResultType.API_PAYLOAD,
    AdapterType.DOCUMENT_SOURCE: SourceAdapterResultType.DOCUMENT_ARTIFACT,
}


@dataclass(frozen=True)
class AdapterMaterialization:
    source_result: SourceAdapterResult
    content_hash_ref: str
    output_ref: str


class LocalTargetRuntimeSourceAdapter:
    def __init__(
        self,
        *,
        fixture_dir: Path,
        corpus_entries: dict[str, TargetSourceCorpusEntry],
    ) -> None:
        self.fixture_dir = fixture_dir
        self.corpus_entries = corpus_entries
        self.last_materialization: AdapterMaterialization | None = None

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        corpus_entry = self.corpus_entries[command.source_ref]
        content = (self.fixture_dir / corpus_entry.source_path).read_text(encoding="utf-8")
        digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
        output_ref = f"adapter-output:{command.command_envelope_id}:{digest[:12]}"
        source_result = SourceAdapterResult(
            id=f"source-result:{command.command_envelope_id}",
            run_id=f"run:{command.command_envelope_id}",
            adapter_spec_id=command.adapter_spec.id,
            adapter_type=command.adapter_spec.adapter_type,
            result_type=RESULT_TYPE_BY_ADAPTER[command.adapter_spec.adapter_type],
            output_refs=[output_ref],
            policy_decision_refs=[command.policy_snapshot_ref],
            replay_event_refs=[f"event:{command.command_envelope_id}:adapter-output"],
            idempotency_key=f"{command.adapter_spec.id}:{command.source_ref}",
            status=AdapterResultStatus.SUCCEEDED,
        )
        self.last_materialization = AdapterMaterialization(
            source_result=source_result,
            content_hash_ref=f"sha256:{digest}",
            output_ref=output_ref,
        )
        return source_result


def build_adapter_backed_source_records(
    *,
    fixture_dir: Path,
    adapter_manifest: TargetAdapterBackedSourceManifest,
    source_corpus: TargetSourceCorpusManifest,
) -> list[TargetAdapterBackedSourceRecord]:
    corpus_entries = {entry.id: entry for entry in source_corpus.entries}
    adapter = LocalTargetRuntimeSourceAdapter(
        fixture_dir=fixture_dir,
        corpus_entries=corpus_entries,
    )
    records: list[TargetAdapterBackedSourceRecord] = []
    for entry in adapter_manifest.entries:
        corpus_entry = corpus_entries[entry.corpus_entry_ref]
        records.append(_materialize_entry(fixture_dir, adapter, entry, corpus_entry))
    return records


def _materialize_entry(
    fixture_dir: Path,
    adapter: LocalTargetRuntimeSourceAdapter,
    entry: TargetAdapterBackedSourceEntry,
    corpus_entry: TargetSourceCorpusEntry,
) -> TargetAdapterBackedSourceRecord:
    content = (fixture_dir / corpus_entry.source_path).read_text(encoding="utf-8")
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    content_hash_ref = f"sha256:{digest}"
    source_observation_ref = (
        f"source-observation:{entry.id.split(':', maxsplit=1)[0]}:"
        f"{entry.corpus_entry_ref}:{digest[:12]}"
    )
    direct_bypass_refs = (
        [f"direct-source-bypass:{entry.id}"] if entry.simulate_direct_source_bypass else []
    )
    missing_adapter_refs = (
        [f"missing-adapter-result:{entry.id}"] if entry.simulate_missing_adapter_result else []
    )
    if direct_bypass_refs or missing_adapter_refs:
        return _record(
            entry=entry,
            source_observation_ref=source_observation_ref,
            content_hash_ref=content_hash_ref,
            direct_bypass_refs=direct_bypass_refs,
            missing_adapter_refs=missing_adapter_refs,
        )
    command = SourceAdapterCommand(
        command_envelope_id=f"{entry.id}:source-adapter",
        adapter_spec=_adapter_spec(entry),
        source_ref=entry.corpus_entry_ref,
        policy_snapshot_ref=entry.policy_decision_ref,
    )
    source_result = adapter.execute(command)
    materialization = adapter.last_materialization
    if materialization is None:
        raise ValueError(f"{entry.id} did not materialize adapter output")
    output_mismatch_refs = (
        [f"adapter-output-mismatch:{entry.id}"]
        if entry.expected_output_ref and entry.expected_output_ref not in source_result.output_refs
        else []
    )
    replay_mismatch_refs = (
        [f"adapter-replay-mismatch:{entry.id}"]
        if entry.expected_content_hash_ref and entry.expected_content_hash_ref != content_hash_ref
        else []
    )
    policy_denied_refs = [entry.policy_decision_ref] if entry.policy_denied else []
    return _record(
        entry=entry,
        source_observation_ref=source_observation_ref,
        content_hash_ref=content_hash_ref,
        source_result=source_result,
        adapter_output_refs=source_result.output_refs,
        adapter_replay_refs=[
            *source_result.replay_event_refs,
            f"replay:{entry.id}:adapter:{digest[:12]}",
        ],
        output_mismatch_refs=output_mismatch_refs,
        policy_denied_refs=policy_denied_refs,
        replay_mismatch_refs=replay_mismatch_refs,
    )


def _adapter_spec(entry: TargetAdapterBackedSourceEntry) -> SourceAdapterSpec:
    return SourceAdapterSpec(
        id=entry.adapter_spec_ref,
        name=f"target-runtime-{entry.adapter_type.value}",
        version="1",
        adapter_type=entry.adapter_type,
        supported_source_types=[entry.adapter_type.value],
        metadata_schema_ref=f"schema:{entry.adapter_spec_ref}:metadata",
        transformation_schema_ref=f"schema:{entry.adapter_spec_ref}:transform",
        policy_refs=[entry.policy_decision_ref],
        idempotency_key_template="{adapter_spec_id}:{source_ref}",
    )


def _record(
    *,
    entry: TargetAdapterBackedSourceEntry,
    source_observation_ref: str,
    content_hash_ref: str,
    source_result: SourceAdapterResult | None = None,
    adapter_output_refs: list[str] | None = None,
    adapter_replay_refs: list[str] | None = None,
    direct_bypass_refs: list[str] | None = None,
    missing_adapter_refs: list[str] | None = None,
    output_mismatch_refs: list[str] | None = None,
    policy_denied_refs: list[str] | None = None,
    replay_mismatch_refs: list[str] | None = None,
) -> TargetAdapterBackedSourceRecord:
    diagnostics = (
        (direct_bypass_refs or [])
        + (missing_adapter_refs or [])
        + (output_mismatch_refs or [])
        + (policy_denied_refs or [])
        + (replay_mismatch_refs or [])
    )
    return TargetAdapterBackedSourceRecord(
        id=f"adapter-backed-source:{entry.id}",
        run_ref=f"run:{entry.id.split(':', maxsplit=1)[0]}",
        corpus_entry_ref=entry.corpus_entry_ref,
        adapter_type=entry.adapter_type,
        source_adapter_result_ref=source_result.id if source_result is not None else None,
        adapter_output_refs=adapter_output_refs or [],
        adapter_policy_decision_refs=[entry.policy_decision_ref],
        adapter_replay_refs=adapter_replay_refs or [],
        source_observation_ref=source_observation_ref,
        content_hash_ref=content_hash_ref,
        direct_source_bypass_refs=direct_bypass_refs or [],
        missing_adapter_result_refs=missing_adapter_refs or [],
        adapter_output_mismatch_refs=output_mismatch_refs or [],
        policy_denied_refs=policy_denied_refs or [],
        replay_mismatch_refs=replay_mismatch_refs or [],
        result=CompletenessResult.FAIL if diagnostics else CompletenessResult.PASS,
    )
