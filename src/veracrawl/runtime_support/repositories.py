"""Deterministic in-memory repositories behind runtime repository ports."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Generic, TypeVar

from veracrawl.contracts.common import Ref, TimestampedModel

T = TypeVar("T", bound=TimestampedModel)


class InMemoryRuntimeRepository(Generic[T]):
    def __init__(self) -> None:
        self._items: dict[Ref, T] = {}

    def save(self, item: T) -> Ref:
        item_id = item.model_dump().get("id")
        if not isinstance(item_id, str) or not item_id:
            raise ValueError("runtime repository items require string id")
        self._items[item_id] = item
        return item_id

    def get(self, ref: Ref) -> T | None:
        return self._items.get(ref)

    def list(self) -> list[T]:
        return list(self._items.values())


@dataclass
class RuntimeRepositories:
    objectives: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    plans: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    runs: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    gates: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    source_results: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    artifacts: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    normalized_documents: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    candidates: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    evidence_packets: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    evidence_coverage: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    verification_decisions: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    published_outputs: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    output_manifests: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    replay_bundles: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    command_results: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    policy_decisions: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
    agent_recommendations: InMemoryRuntimeRepository[TimestampedModel] = field(
        default_factory=InMemoryRuntimeRepository
    )
