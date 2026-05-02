"""Postgres persistence adapter contract descriptor.

This module intentionally declares the adapter boundary without importing a
Postgres client. Operational Postgres support must pass the same conformance
harness before it can report an executable pass.
"""

from __future__ import annotations

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import PersistenceAdapterKind, PersistenceCapability
from veracrawl.contracts.persistence import PersistenceAdapterSpec


def postgres_adapter_spec(fixture_id: str, policy_refs: list[Ref]) -> PersistenceAdapterSpec:
    return PersistenceAdapterSpec(
        id=f"persistence-adapter:{fixture_id}:postgres-contract",
        adapter_kind=PersistenceAdapterKind.POSTGRES_CONTRACT,
        capability_refs=list(PersistenceCapability),
        port_refs=[
            "port:metadata-persistence:postgres",
            "port:event-log-persistence:postgres",
            "port:outbox-persistence:postgres",
            "port:artifact-index-persistence:postgres",
            "port:queue-persistence:postgres",
        ],
        transaction_supported=True,
        idempotency_supported=True,
        lease_supported=True,
        policy_decision_refs=policy_refs,
    )
