"""Pilot — same smoke test as ``pilot_smoke_test.py`` but
through the full v2 adapter framework (Phase 6 step 6.1).

After the Phase 6 step 6.1 unblock, ``OpenAIResponsesAdapterV2``
in ``RuntimeMode.PRODUCTION`` accepts a real
``httpx.BaseTransport`` (or defaults to a fresh
``httpx.HTTPTransport`` if ``transport=None``).

This pilot verifies the complete adapter framework path
end-to-end against real OpenAI:

* PRODUCTION construction succeeds with a real transport
* ``complete()`` issues a real call
* Response goes through ``_extract_output_text`` +
  ``_extract_usage`` + finish-reason mapping
* ``ProviderResponse`` lands with all validators passing

Out of scope:

* SchemaExtractionRuntime integration (next step — wire
  prompt registry + budget + calibration)
* Cost-budget enforcement
* Recovery loop

Total real-API cost: same ~$0.000015 for a 32-token
JSON_OBJECT call.

Usage:
    uv run --no-sync python scripts/pilot_via_adapter.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from veracrawl.adapters.model_providers.openai_responses_v2 import (
    OpenAIResponsesAdapterV2,
)
from veracrawl.contracts.agent import Message, ResponseFormat
from veracrawl.contracts.enums import (
    MessageRole,
    ResponseFormatKind,
)
from veracrawl.contracts.llm_input import ProviderRequest
from veracrawl.runtime_support.runtime_mode import RuntimeMode


def _load_env() -> tuple[str, str]:
    env_path = Path.home() / ".env"
    if not env_path.exists():
        sys.exit(f"~/.env not found at {env_path}")
    api_key: str | None = None
    model: str | None = None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()
        if key == "OPENAI_API_KEY":
            api_key = value
        elif key == "OPENAI_MODEL":
            model = value
    if not api_key:
        sys.exit("OPENAI_API_KEY missing in ~/.env")
    if not model:
        sys.exit("OPENAI_MODEL missing in ~/.env")
    return api_key, model


def main() -> int:
    api_key, model_name = _load_env()
    print(f"[pilot-adapter] model={model_name}")
    adapter = OpenAIResponsesAdapterV2(
        api_key=api_key,
        runtime_mode=RuntimeMode.PRODUCTION,
        # transport=None → defaults to real httpx.HTTPTransport
    )
    request = ProviderRequest(
        id="pilot:via-adapter:1",
        run_ref="run:pilot-adapter:1",
        model_name=model_name,
        messages=[
            Message(
                role=MessageRole.USER,
                content=(
                    "Reply with a single JSON object: "
                    '{"ack": true, "via": "adapter"}'
                ),
            ),
        ],
        response_format=ResponseFormat(kind=ResponseFormatKind.JSON_OBJECT),
        max_output_tokens=32,
        temperature=0.0,
    )
    print(f"[pilot-adapter] sending request id={request.id}")
    try:
        response = adapter.complete(request)
    except Exception as exc:
        print(
            f"[pilot-adapter] adapter.complete failed: "
            f"{type(exc).__name__}: {exc}",
            file=sys.stderr,
        )
        return 2
    print(
        f"[pilot-adapter] OK: text={response.text!r} "
        f"finish={response.finish_reason.value} "
        f"usage(prompt={response.usage.prompt_tokens}, "
        f"completion={response.usage.completion_tokens}, "
        f"total={response.usage.total_tokens})"
    )
    if response.parsed_output is not None:
        print(f"[pilot-adapter] parsed_output={response.parsed_output!r}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
