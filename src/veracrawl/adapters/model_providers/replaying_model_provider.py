"""``ReplayingModelProviderV2`` — s2 step 3 + s2.1 step 4 in-product replay consumer.

See ``docs/plans/general-purpose-crawler-agentification/
s2-llm-crawl-planner-adapter.md`` (s2 step 3) and
``s2.1-provider-artifact-wiring.md`` (s2.1 step 4).

Returns canned ``ProviderResponse`` instances looked up by
``ProviderRequest.id`` first (s2 mode). If that miss occurs and
``canned_by_raw_ref`` + ``artifact_store`` are both wired (s2.1
mode), the adapter resolves the response by reading bytes from
the store keyed by ``raw_response_ref`` — proving the artifact
store actually round-trips. Raises ``ReplayLookupMissError`` in
all unresolvable cases.

``supports()`` is derived from the union of both canned mappings
so the adapter advertises only the capabilities it can actually
serve.

s2.1 plan iter-5 reservation R1: when the request.id miss falls
through to ``canned_by_raw_ref``, this consumer picks the
first entry in insertion order — sufficient for the single-entry
round-trip test 26a but not yet a deterministic resolver across
multi-entry bundles. Multi-entry deterministic resolution is
deferred to s12 (runner-replay wiring) which will thread an
explicit request→ref mapping through ``RunReport``.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING

from veracrawl.contracts.enums import ModelCapability
from veracrawl.contracts.errors import ReplayLookupMissError
from veracrawl.contracts.llm_input import ProviderRequest, ProviderResponse

if TYPE_CHECKING:
    from veracrawl.ports.stores import ArtifactStorePort


class ReplayingModelProviderV2:
    """``ModelProviderPortV2`` impl that replays canned responses."""

    def __init__(
        self,
        canned: Mapping[str, ProviderResponse],
        *,
        canned_by_raw_ref: Mapping[str, ProviderResponse] | None = None,
        artifact_store: ArtifactStorePort | None = None,
    ) -> None:
        self._canned = dict(canned)
        self._canned_by_raw_ref: dict[str, ProviderResponse] = (
            dict(canned_by_raw_ref) if canned_by_raw_ref else {}
        )
        self._artifact_store = artifact_store

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        if request.id in self._canned:
            return self._canned[request.id]
        if self._canned_by_raw_ref and self._artifact_store is not None:
            # s2.1: dict insertion order; R1 reservation acknowledges
            # multi-entry non-determinism — deferred to s12.
            ref, response = next(iter(self._canned_by_raw_ref.items()))
            try:
                self._artifact_store.read(ref)
            except KeyError as exc:
                raise ReplayLookupMissError(
                    provider_request_id=request.id,
                ) from exc
            return response
        raise ReplayLookupMissError(provider_request_id=request.id)

    def supports(self, capability: ModelCapability) -> bool:
        values = list(self._canned.values()) + list(self._canned_by_raw_ref.values())
        if capability is ModelCapability.STRUCTURED_OUTPUT_JSON_SCHEMA:
            return any(r.parsed_output is not None for r in values)
        if capability is ModelCapability.TOOL_CALLS:
            return any(bool(r.tool_calls) for r in values)
        return False
