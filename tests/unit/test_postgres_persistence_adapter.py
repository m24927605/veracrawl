from __future__ import annotations

import pytest

from veracrawl.adapters.persistence.postgres import (
    POSTGRES_DOCUMENT_TABLE,
    POSTGRES_DOCUMENT_TABLE_SQL,
    POSTGRES_DOCUMENT_UPSERT_SQL,
    PostgresPersistenceAdapter,
    PostgresRuntimeUnavailableError,
    postgres_adapter_spec,
)
from veracrawl.contracts.enums import PersistenceAdapterKind, PersistenceCapability


def test_postgres_adapter_spec_declares_operational_kind() -> None:
    spec = postgres_adapter_spec("unit", ["policy:unit:persistence-adapter"])
    assert spec.adapter_kind == PersistenceAdapterKind.POSTGRES
    assert set(spec.capability_refs) == set(PersistenceCapability)
    assert spec.transaction_supported is True
    assert spec.idempotency_supported is True
    assert spec.lease_supported is True


def test_postgres_sql_uses_jsonb_and_idempotent_upsert() -> None:
    assert POSTGRES_DOCUMENT_TABLE == "veracrawl_documents"
    assert "JSONB" in POSTGRES_DOCUMENT_TABLE_SQL
    assert "PRIMARY KEY (collection, key)" in POSTGRES_DOCUMENT_TABLE_SQL
    assert "ON CONFLICT (collection, key)" in POSTGRES_DOCUMENT_UPSERT_SQL
    assert "%s::jsonb" in POSTGRES_DOCUMENT_UPSERT_SQL


def test_postgres_adapter_requires_dsn() -> None:
    with pytest.raises(PostgresRuntimeUnavailableError):
        PostgresPersistenceAdapter("")


def test_postgres_adapter_rejects_unsafe_table_identifier() -> None:
    with pytest.raises(ValueError):
        PostgresPersistenceAdapter(
            "postgresql://example.invalid/veracrawl",
            table_name="veracrawl_documents;drop table x",
            connect=lambda *_args, **_kwargs: None,
        )
