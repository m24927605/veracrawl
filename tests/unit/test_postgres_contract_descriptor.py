from __future__ import annotations

from veracrawl.adapters.persistence.postgres_contract import postgres_adapter_spec
from veracrawl.contracts.enums import PersistenceAdapterKind, PersistenceCapability


def test_postgres_descriptor_declares_contract_without_client_dependency() -> None:
    spec = postgres_adapter_spec(
        "postgres-adapter-contract-harness",
        ["policy:postgres-adapter-contract-harness:persistence-adapter"],
    )
    assert spec.adapter_kind == PersistenceAdapterKind.POSTGRES_CONTRACT
    assert set(spec.capability_refs) == set(PersistenceCapability)
    assert any(ref.endswith(":postgres") for ref in spec.port_refs)
