"""``ReplayingModelProviderV2`` — s2 step 3 in-product replay consumer.

See ``docs/plans/general-purpose-crawler-agentification/
s2-llm-crawl-planner-adapter.md``. Returns canned
``ProviderResponse`` instances looked up by ``ProviderRequest.id``;
raises ``ReplayLookupMissError`` when the bundle is incomplete.
``supports()`` is derived from the canned bundle so the adapter
advertises only the capabilities it can actually serve.
"""

from __future__ import annotations

from collections.abc import Mapping

from veracrawl.contracts.enums import ModelCapability
from veracrawl.contracts.errors import ReplayLookupMissError
from veracrawl.contracts.llm_input import ProviderRequest, ProviderResponse


class ReplayingModelProviderV2:
    """``ModelProviderPortV2`` impl that replays canned responses."""

    def __init__(self, canned: Mapping[str, ProviderResponse]) -> None:
        self._canned = dict(canned)

    def complete(self, request: ProviderRequest) -> ProviderResponse:
        try:
            return self._canned[request.id]
        except KeyError as exc:
            raise ReplayLookupMissError(provider_request_id=request.id) from exc

    def supports(self, capability: ModelCapability) -> bool:
        values = self._canned.values()
        if capability is ModelCapability.STRUCTURED_OUTPUT_JSON_SCHEMA:
            return any(r.parsed_output is not None for r in values)
        if capability is ModelCapability.TOOL_CALLS:
            return any(bool(r.tool_calls) for r in values)
        return False
