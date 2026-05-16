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

s2.1 plan iter-5 reservation R1 (closed): when the request.id
miss falls through to ``canned_by_raw_ref``, an explicit
``replay_request_overrides: Mapping[str, str]`` ctor arg maps
``ProviderRequest.id`` → ``raw_response_ref`` so multi-entry
bundles are deterministic. Insertion-order fallback is preserved
for single-entry bundles where overrides aren't supplied (kept
backward-compatible with the s2.1 step-4 single-entry round-trip
test).
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
        replay_request_overrides: Mapping[str, str] | None = None,
    ) -> None:
        self._canned = dict(canned)
        self._canned_by_raw_ref: dict[str, ProviderResponse] = (
            dict(canned_by_raw_ref) if canned_by_raw_ref else {}
        )
        self._artifact_store = artifact_store
        # s2.1 R1: deterministic request_id → raw_response_ref map for
        # multi-entry canned_by_raw_ref bundles. Empty mapping by
        # default; falls back to insertion-order pick.
        self._replay_request_overrides: dict[str, str] = (
            dict(replay_request_overrides) if replay_request_overrides else {}
        )

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        if request.id in self._canned:
            return self._canned[request.id]
        if self._canned_by_raw_ref and self._artifact_store is not None:
            override_ref = self._replay_request_overrides.get(request.id)
            if override_ref is not None:
                # s2.1 R1: deterministic resolution. The override maps
                # this request to a specific raw_response_ref; the
                # canned_by_raw_ref bundle MUST contain that entry.
                response = self._canned_by_raw_ref.get(override_ref)
                if response is None:
                    raise ReplayLookupMissError(
                        provider_request_id=request.id,
                    )
                try:
                    self._artifact_store.read(override_ref)
                except KeyError as exc:
                    raise ReplayLookupMissError(
                        provider_request_id=request.id,
                    ) from exc
                return response
            # No override: insertion-order fallback (single-entry case).
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
