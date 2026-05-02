"""Runtime repository ports."""

from __future__ import annotations

from typing import Protocol, TypeVar

from veracrawl.contracts.common import Ref, TimestampedModel

T_co = TypeVar("T_co", bound=TimestampedModel, covariant=True)
T = TypeVar("T", bound=TimestampedModel)


class RuntimeRepositoryPort(Protocol[T]):
    def save(self, item: T) -> Ref: ...

    def get(self, ref: Ref) -> T | None: ...

    def list(self) -> list[T]: ...


class RuntimeRepositorySetPort(Protocol):
    objectives: RuntimeRepositoryPort[TimestampedModel]
    plans: RuntimeRepositoryPort[TimestampedModel]
    runs: RuntimeRepositoryPort[TimestampedModel]
    gates: RuntimeRepositoryPort[TimestampedModel]
    source_results: RuntimeRepositoryPort[TimestampedModel]
    artifacts: RuntimeRepositoryPort[TimestampedModel]
    normalized_documents: RuntimeRepositoryPort[TimestampedModel]
    candidates: RuntimeRepositoryPort[TimestampedModel]
    evidence_packets: RuntimeRepositoryPort[TimestampedModel]
    verification_decisions: RuntimeRepositoryPort[TimestampedModel]
    published_outputs: RuntimeRepositoryPort[TimestampedModel]
    output_manifests: RuntimeRepositoryPort[TimestampedModel]
    replay_bundles: RuntimeRepositoryPort[TimestampedModel]
    command_results: RuntimeRepositoryPort[TimestampedModel]
    policy_decisions: RuntimeRepositoryPort[TimestampedModel]
