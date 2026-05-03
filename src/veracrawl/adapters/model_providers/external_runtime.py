"""Generic external model provider runtime adapter wrapper."""

from __future__ import annotations

import importlib
from collections.abc import Callable
from typing import Any, cast

from veracrawl.contracts.agent import ModelRequest, ModelResponse


class ExternalModelProviderRuntimeAdapter:
    def __init__(
        self,
        *,
        provider_name: str,
        model_id: str,
        model_version: str,
        module_name: str,
        callable_name: str = "complete",
    ) -> None:
        self.provider_name = provider_name
        self.model_id = model_id
        self.model_version = model_version
        self.module_name = module_name
        self.callable_name = callable_name

    def complete(self, request: ModelRequest) -> ModelResponse:
        module = importlib.import_module(self.module_name)
        raw_callable = getattr(module, self.callable_name, None)
        if raw_callable is None:
            raise RuntimeError(
                f"{self.module_name}.{self.callable_name} is not configured"
            )
        complete = cast(Callable[[ModelRequest], ModelResponse | dict[str, Any]], raw_callable)
        result = complete(request)
        if isinstance(result, ModelResponse):
            return result
        return ModelResponse.model_validate(result)


def build_model_provider(
    *,
    provider_name: str,
    model_id: str,
    model_version: str,
    module_name: str,
    callable_name: str = "complete",
) -> ExternalModelProviderRuntimeAdapter:
    return ExternalModelProviderRuntimeAdapter(
        provider_name=provider_name,
        model_id=model_id,
        model_version=model_version,
        module_name=module_name,
        callable_name=callable_name,
    )
