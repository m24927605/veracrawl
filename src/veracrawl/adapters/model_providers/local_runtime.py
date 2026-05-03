"""Local deterministic model provider runtime adapter."""

from __future__ import annotations

from veracrawl.contracts.agent import ModelRequest, ModelResponse


class LocalModelProviderRuntimeAdapter:
    provider_name = "Local model runtime"
    model_id = "veracrawl-local-deterministic"
    model_version = "1"

    def complete(self, request: ModelRequest) -> ModelResponse:
        return ModelResponse(
            id=f"model-response:{request.id}",
            model_request_id=request.id,
            response_ref=f"model-response-payload:{request.id}",
            parsed_output_ref=f"model-parsed-output:{request.id}",
            tool_request_refs=[],
            safety_filter_result_ref=f"safety-filter:{request.id}:pass",
            status="completed",
        )


def build_model_provider() -> LocalModelProviderRuntimeAdapter:
    return LocalModelProviderRuntimeAdapter()
