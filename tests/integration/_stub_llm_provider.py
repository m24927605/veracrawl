"""Stub ModelProviderPortV2 factory for CLI integration tests.

Importable via ``--llm-provider tests.integration._stub_llm_provider:make_provider``.
"""

from __future__ import annotations

from typing import Any

from veracrawl.contracts.agent import TokenUsage
from veracrawl.contracts.enums import ModelCapability, ProviderFinishReason
from veracrawl.contracts.llm_input import ProviderRequest, ProviderResponse


class _StubProvider:
    def complete(self, request: ProviderRequest) -> ProviderResponse:
        # Always emit a single canned guess that quotes the
        # "Page A" heading present in the static-site fixture.
        parsed: dict[str, Any] = {
            "field_guesses": [
                {
                    "field_name": "headline",
                    "value": "Page A",
                    "evidence_quote": "Page A",
                }
            ]
        }
        return ProviderResponse(
            id="stub-resp-1",
            request_ref=request.id,
            text="{}",
            usage=TokenUsage(
                prompt_tokens=10,
                completion_tokens=5,
                total_tokens=15,
            ),
            finish_reason=ProviderFinishReason.STOP,
            parsed_output=parsed,
        )

    def supports(self, capability: ModelCapability) -> bool:
        return True


def make_provider() -> _StubProvider:
    return _StubProvider()
