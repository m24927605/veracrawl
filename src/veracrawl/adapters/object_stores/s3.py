"""Operational S3-compatible object store adapter."""

from __future__ import annotations

import importlib
import re
from typing import Any, cast

from veracrawl.contracts.artifact import (
    ObjectStoreAdapterSpec,
    ObjectStoreOperationRecord,
    RuntimeArtifactRef,
)
from veracrawl.contracts.common import Ref, stable_hash
from veracrawl.contracts.enums import (
    ArtifactType,
    ObjectStoreAdapterKind,
    ObjectStoreCapability,
    ObjectStoreOperation,
    OwnerService,
    PrivacyClassification,
)

_SAFE_SEGMENT_PATTERN = re.compile(r"^[A-Za-z0-9_.:-]+$")


class S3RuntimeUnavailableError(RuntimeError):
    """Raised when the optional S3 runtime dependency or endpoint is unavailable."""


class S3ObjectStoreAdapter:
    """S3-compatible object store adapter for executable artifact conformance."""

    def __init__(
        self,
        endpoint_url: str,
        *,
        bucket: str,
        access_key_id: str,
        secret_access_key: str,
        region_name: str = "us-east-1",
        namespace: str = "veracrawl",
        client: Any | None = None,
    ) -> None:
        if not endpoint_url and client is None:
            raise S3RuntimeUnavailableError("S3-compatible endpoint URL is required")
        for label, value in {"bucket": bucket, "namespace": namespace}.items():
            if not value or not _SAFE_SEGMENT_PATTERN.match(value):
                raise ValueError(f"unsafe S3 {label}: {value}")
        self.endpoint_url = endpoint_url
        self.bucket = bucket
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.region_name = region_name
        self.namespace = namespace
        self._client_provided = client is not None
        self._client = client if client is not None else _make_s3_client(
            endpoint_url=endpoint_url,
            access_key_id=access_key_id,
            secret_access_key=secret_access_key,
            region_name=region_name,
        )
        self._ensure_bucket()

    def reopen(self) -> S3ObjectStoreAdapter:
        return S3ObjectStoreAdapter(
            self.endpoint_url,
            bucket=self.bucket,
            access_key_id=self.access_key_id,
            secret_access_key=self.secret_access_key,
            region_name=self.region_name,
            namespace=self.namespace,
            client=self._client if self._client_provided else None,
        )

    def write(
        self,
        *,
        artifact_id: str,
        artifact_type: ArtifactType,
        producer_service: OwnerService,
        source_ref: Ref,
        content: str,
        privacy_classification: PrivacyClassification,
        adapter_ref: Ref,
        retention_policy_ref: Ref,
        privacy_policy_ref: Ref,
        policy_decision_refs: list[Ref],
    ) -> tuple[RuntimeArtifactRef, ObjectStoreOperationRecord]:
        artifact = _artifact_ref(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            producer_service=producer_service,
            source_ref=source_ref,
            content=content,
            privacy_classification=privacy_classification,
            retention_policy_ref=retention_policy_ref,
        )
        key = self._object_key(artifact.id)
        existing = self._head_object(key)
        if existing is not None and _metadata_digest(existing) == artifact.content_digest:
            operation = self._operation(
                adapter_ref=adapter_ref,
                operation=ObjectStoreOperation.DUPLICATE_PUT,
                artifact=artifact,
                object_key_ref=key,
                etag_ref=_etag(existing),
                duplicate_of_ref=artifact.id,
                retention_policy_ref=retention_policy_ref,
                privacy_policy_ref=privacy_policy_ref,
                policy_decision_refs=policy_decision_refs,
            )
            return artifact, operation
        self._client.put_object(
            Bucket=self.bucket,
            Key=key,
            Body=content.encode("utf-8"),
            ContentType="text/plain; charset=utf-8",
            Metadata={
                "artifact-id": artifact.id,
                "artifact-type": artifact.artifact_type.value,
                "producer-service": artifact.producer_service.value,
                "source-ref": artifact.source_ref,
                "content-digest": artifact.content_digest,
                "privacy-classification": artifact.privacy_classification.value,
                "lifecycle-state-ref": artifact.lifecycle_state_ref,
                "retention-policy-ref": artifact.retention_policy_ref,
            },
        )
        head = self._head_object(key)
        operation = self._operation(
            adapter_ref=adapter_ref,
            operation=ObjectStoreOperation.PUT,
            artifact=artifact,
            object_key_ref=key,
            etag_ref=_etag(head),
            retention_policy_ref=retention_policy_ref,
            privacy_policy_ref=privacy_policy_ref,
            policy_decision_refs=policy_decision_refs,
        )
        return artifact, operation

    def read(
        self,
        artifact: RuntimeArtifactRef,
        *,
        adapter_ref: Ref,
        retention_policy_ref: Ref,
        privacy_policy_ref: Ref,
        policy_decision_refs: list[Ref],
    ) -> tuple[str, ObjectStoreOperationRecord]:
        key = self._object_key(artifact.id)
        response = self._client.get_object(Bucket=self.bucket, Key=key)
        body = response["Body"].read().decode("utf-8")
        if stable_hash(body) != artifact.content_digest:
            raise ValueError(f"object digest mismatch for {artifact.id}")
        operation = self._operation(
            adapter_ref=adapter_ref,
            operation=ObjectStoreOperation.GET,
            artifact=artifact,
            object_key_ref=key,
            etag_ref=_etag(response),
            read_result_ref=f"read-result:{artifact.id}",
            retention_policy_ref=retention_policy_ref,
            privacy_policy_ref=privacy_policy_ref,
            policy_decision_refs=policy_decision_refs,
        )
        return body, operation

    def head(
        self,
        artifact: RuntimeArtifactRef,
        *,
        adapter_ref: Ref,
        retention_policy_ref: Ref,
        privacy_policy_ref: Ref,
        policy_decision_refs: list[Ref],
    ) -> ObjectStoreOperationRecord:
        key = self._object_key(artifact.id)
        response = self._head_object(key)
        if response is None:
            raise ValueError(f"object missing for {artifact.id}")
        if _metadata_digest(response) != artifact.content_digest:
            raise ValueError(f"object metadata digest mismatch for {artifact.id}")
        return self._operation(
            adapter_ref=adapter_ref,
            operation=ObjectStoreOperation.HEAD,
            artifact=artifact,
            object_key_ref=key,
            etag_ref=_etag(response),
            retention_policy_ref=retention_policy_ref,
            privacy_policy_ref=privacy_policy_ref,
            policy_decision_refs=policy_decision_refs,
        )

    def list_artifacts(
        self,
        *,
        adapter_ref: Ref,
        retention_policy_ref: Ref,
        privacy_policy_ref: Ref,
        policy_decision_refs: list[Ref],
    ) -> tuple[list[RuntimeArtifactRef], ObjectStoreOperationRecord]:
        prefix = f"{self.namespace}/"
        response = self._client.list_objects_v2(Bucket=self.bucket, Prefix=prefix)
        artifacts: list[RuntimeArtifactRef] = []
        for item in response.get("Contents", []):
            key = item["Key"]
            head = self._head_object(key)
            if head is not None:
                artifacts.append(_artifact_from_metadata(head["Metadata"]))
        operation = ObjectStoreOperationRecord(
            id=f"object-store-operation:{self.namespace}:list:{self._next_count()}",
            adapter_ref=adapter_ref,
            operation=ObjectStoreOperation.LIST,
            object_key_ref=prefix,
            lifecycle_state_ref=f"lifecycle:{self.namespace}:listed",
            retention_policy_ref=retention_policy_ref,
            privacy_policy_ref=privacy_policy_ref,
            policy_decision_refs=policy_decision_refs,
        )
        return artifacts, operation

    def delete(
        self,
        artifact: RuntimeArtifactRef,
        *,
        adapter_ref: Ref,
        retention_policy_ref: Ref,
        privacy_policy_ref: Ref,
        policy_decision_refs: list[Ref],
    ) -> ObjectStoreOperationRecord:
        key = self._object_key(artifact.id)
        self._client.delete_object(Bucket=self.bucket, Key=key)
        return ObjectStoreOperationRecord(
            id=f"object-store-operation:{artifact.id}:delete:{self._next_count()}",
            adapter_ref=adapter_ref,
            operation=ObjectStoreOperation.DELETE,
            artifact_ref=artifact.id,
            object_key_ref=key,
            deletion_marker_ref=f"deletion-marker:{artifact.id}",
            lifecycle_state_ref=f"lifecycle:{artifact.id}:deleted",
            retention_policy_ref=retention_policy_ref,
            privacy_policy_ref=privacy_policy_ref,
            policy_decision_refs=policy_decision_refs,
        )

    def object_count(self) -> int:
        response = self._client.list_objects_v2(Bucket=self.bucket, Prefix=f"{self.namespace}/")
        return int(response.get("KeyCount", 0))

    def _ensure_bucket(self) -> None:
        try:
            self._client.head_bucket(Bucket=self.bucket)
        except Exception:
            self._client.create_bucket(Bucket=self.bucket)

    def _head_object(self, key: str) -> dict[str, Any] | None:
        try:
            response = self._client.head_object(Bucket=self.bucket, Key=key)
        except Exception:
            return None
        return cast(dict[str, Any], response)

    def _operation(
        self,
        *,
        adapter_ref: Ref,
        operation: ObjectStoreOperation,
        artifact: RuntimeArtifactRef,
        object_key_ref: Ref,
        etag_ref: Ref | None,
        retention_policy_ref: Ref,
        privacy_policy_ref: Ref,
        policy_decision_refs: list[Ref],
        read_result_ref: Ref | None = None,
        duplicate_of_ref: Ref | None = None,
    ) -> ObjectStoreOperationRecord:
        return ObjectStoreOperationRecord(
            id=f"object-store-operation:{artifact.id}:{operation.value}:{self._next_count()}",
            adapter_ref=adapter_ref,
            operation=operation,
            artifact_ref=artifact.id,
            object_key_ref=object_key_ref,
            content_digest_ref=artifact.content_digest,
            size_bytes=artifact.size_bytes,
            etag_ref=etag_ref or f"etag:{artifact.id}:unavailable",
            read_result_ref=read_result_ref,
            duplicate_of_ref=duplicate_of_ref,
            lifecycle_state_ref=artifact.lifecycle_state_ref,
            retention_policy_ref=retention_policy_ref,
            privacy_policy_ref=privacy_policy_ref,
            policy_decision_refs=policy_decision_refs,
        )

    def _object_key(self, artifact_ref: Ref) -> str:
        return f"{self.namespace}/{artifact_ref}"

    def _next_count(self) -> int:
        if not hasattr(self, "_counter"):
            self._counter = 0
        self._counter += 1
        return int(self._counter)


def s3_object_store_adapter_spec(
    fixture_id: str,
    policy_refs: list[Ref],
    *,
    retention_refs: list[Ref] | None = None,
    privacy_refs: list[Ref] | None = None,
) -> ObjectStoreAdapterSpec:
    return ObjectStoreAdapterSpec(
        id=f"object-store-adapter:{fixture_id}:s3-compatible",
        adapter_kind=ObjectStoreAdapterKind.S3_COMPATIBLE,
        capability_refs=list(ObjectStoreCapability),
        bucket_ref=f"object-bucket:{fixture_id}:artifacts",
        namespace_ref=f"object-prefix:{fixture_id}",
        content_addressing_supported=True,
        digest_verification_supported=True,
        lifecycle_supported=True,
        retention_policy_refs=retention_refs or [f"retention-policy:{fixture_id}:artifacts"],
        privacy_policy_refs=privacy_refs or [f"privacy-policy:{fixture_id}:artifacts"],
        policy_decision_refs=policy_refs,
    )


def _artifact_ref(
    *,
    artifact_id: str,
    artifact_type: ArtifactType,
    producer_service: OwnerService,
    source_ref: Ref,
    content: str,
    privacy_classification: PrivacyClassification,
    retention_policy_ref: Ref,
) -> RuntimeArtifactRef:
    return RuntimeArtifactRef(
        id=artifact_id,
        artifact_type=artifact_type,
        producer_service=producer_service,
        source_ref=source_ref,
        content_digest=stable_hash(content),
        size_bytes=len(content.encode("utf-8")),
        privacy_classification=privacy_classification,
        lifecycle_state_ref=f"lifecycle:{artifact_id}:active",
        retention_policy_ref=retention_policy_ref,
    )


def _artifact_from_metadata(metadata: dict[str, str]) -> RuntimeArtifactRef:
    return RuntimeArtifactRef(
        id=metadata["artifact-id"],
        artifact_type=ArtifactType(metadata["artifact-type"]),
        producer_service=OwnerService(metadata["producer-service"]),
        source_ref=metadata["source-ref"],
        content_digest=metadata["content-digest"],
        size_bytes=0,
        privacy_classification=PrivacyClassification(metadata["privacy-classification"]),
        lifecycle_state_ref=metadata["lifecycle-state-ref"],
        retention_policy_ref=metadata["retention-policy-ref"],
    )


def _make_s3_client(
    *,
    endpoint_url: str,
    access_key_id: str,
    secret_access_key: str,
    region_name: str,
) -> Any:
    try:
        boto3 = importlib.import_module("boto3")
        config_module = importlib.import_module("botocore.config")
    except ImportError as exc:
        raise S3RuntimeUnavailableError(
            "boto3 and botocore are required for operational object store conformance; "
            "install with the object-s3 extra"
        ) from exc
    config_factory = config_module.__dict__.get("Config")
    if not callable(config_factory):
        raise S3RuntimeUnavailableError("botocore.config.Config is unavailable")
    return boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name=region_name,
        config=config_factory(s3={"addressing_style": "path"}),
    )


def _etag(response: dict[str, Any] | None) -> Ref | None:
    if response is None:
        return None
    raw = response.get("ETag")
    if not raw:
        return None
    value = str(raw).strip('"')
    return f"etag:{value}"


def _metadata_digest(response: dict[str, Any]) -> str | None:
    metadata = response.get("Metadata", {})
    if not isinstance(metadata, dict):
        return None
    raw = metadata.get("content-digest")
    return str(raw) if raw is not None else None
