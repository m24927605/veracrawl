"""Operational Postgres persistence adapter."""

from __future__ import annotations

import importlib
import json
import re
from collections.abc import Callable
from typing import Any, cast

from veracrawl.adapters.persistence.json_document import JsonDocumentPersistenceAdapterMixin
from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import PersistenceAdapterKind, PersistenceCapability
from veracrawl.contracts.persistence import PersistenceAdapterSpec

POSTGRES_DOCUMENT_TABLE = "veracrawl_documents"

POSTGRES_DOCUMENT_TABLE_SQL = f"""
CREATE TABLE IF NOT EXISTS {POSTGRES_DOCUMENT_TABLE} (
    collection TEXT NOT NULL,
    key TEXT NOT NULL,
    document JSONB NOT NULL,
    PRIMARY KEY (collection, key)
)
"""

POSTGRES_DOCUMENT_UPSERT_SQL = f"""
INSERT INTO {POSTGRES_DOCUMENT_TABLE} (collection, key, document)
VALUES (%s, %s, %s::jsonb)
ON CONFLICT (collection, key)
DO UPDATE SET document = EXCLUDED.document
"""

_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class PostgresRuntimeUnavailableError(RuntimeError):
    """Raised when the optional Postgres runtime dependency or DSN is unavailable."""


class PostgresPersistenceAdapter(JsonDocumentPersistenceAdapterMixin):
    """Postgres JSONB-backed adapter for executable persistence conformance."""

    def __init__(
        self,
        dsn: str,
        *,
        table_name: str = POSTGRES_DOCUMENT_TABLE,
        connect: Callable[..., Any] | None = None,
    ) -> None:
        if not dsn:
            raise PostgresRuntimeUnavailableError("Postgres DSN is required")
        if not _IDENTIFIER_PATTERN.match(table_name):
            raise ValueError(f"unsafe Postgres table identifier: {table_name}")
        self.dsn = dsn
        self.table_name = table_name
        self._connect_fn = connect or _load_psycopg_connect()
        self._initialize()

    def reopen(self) -> PostgresPersistenceAdapter:
        return PostgresPersistenceAdapter(
            self.dsn,
            table_name=self.table_name,
            connect=self._connect_fn,
        )

    def _connect(self) -> Any:
        return self._connect_fn(self.dsn, autocommit=True)

    def _initialize(self) -> None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(self._table_sql())

    def _table_sql(self) -> str:
        return f"""
        CREATE TABLE IF NOT EXISTS {self.table_name} (
            collection TEXT NOT NULL,
            key TEXT NOT NULL,
            document JSONB NOT NULL,
            PRIMARY KEY (collection, key)
        )
        """

    def _put_document(self, collection: str, key: Ref, document: dict[str, Any]) -> Ref:
        encoded = json.dumps(document, sort_keys=True, separators=(",", ":"))
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    INSERT INTO {self.table_name} (collection, key, document)
                    VALUES (%s, %s, %s::jsonb)
                    ON CONFLICT (collection, key)
                    DO UPDATE SET document = EXCLUDED.document
                    """,
                    (collection, key, encoded),
                )
        return key

    def _get_document(self, collection: str, key: Ref) -> dict[str, Any] | None:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT document
                    FROM {self.table_name}
                    WHERE collection = %s AND key = %s
                    """,
                    (collection, key),
                )
                row = cursor.fetchone()
        if row is None:
            return None
        return _decode_document(row[0])

    def _list_documents(self, collection: str) -> list[dict[str, Any]]:
        with self._connect() as connection:
            with connection.cursor() as cursor:
                cursor.execute(
                    f"""
                    SELECT document
                    FROM {self.table_name}
                    WHERE collection = %s
                    ORDER BY key
                    """,
                    (collection,),
                )
                rows = cursor.fetchall()
        return [_decode_document(row[0]) for row in rows]


def postgres_adapter_spec(fixture_id: str, policy_refs: list[Ref]) -> PersistenceAdapterSpec:
    return PersistenceAdapterSpec(
        id=f"persistence-adapter:{fixture_id}:postgres",
        adapter_kind=PersistenceAdapterKind.POSTGRES,
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


def _load_psycopg_connect() -> Callable[..., Any]:
    try:
        module = importlib.import_module("psycopg")
    except ImportError as exc:
        raise PostgresRuntimeUnavailableError(
            "psycopg is required for operational Postgres persistence; "
            "install with the postgres extra"
        ) from exc
    connect = module.__dict__.get("connect")
    if not callable(connect):
        raise PostgresRuntimeUnavailableError("psycopg.connect is unavailable")
    return cast(Callable[..., Any], connect)


def _decode_document(raw: object) -> dict[str, Any]:
    if isinstance(raw, dict):
        return cast(dict[str, Any], raw)
    if isinstance(raw, str):
        loaded = json.loads(raw)
        if isinstance(loaded, dict):
            return cast(dict[str, Any], loaded)
    raise ValueError("stored Postgres document must be a JSON object")
