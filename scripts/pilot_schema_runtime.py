"""Pilot — real OpenAI call through SchemaExtractionRuntime.

This is the Phase 6 follow-up to ``pilot_via_adapter.py``:
instead of stopping at ``OpenAIResponsesAdapterV2.complete()``,
it runs the full Phase 4 extraction integrator:

* temporary JSON prompt registry
* ``OpenAIResponsesAdapterV2(runtime_mode=PRODUCTION)``
* ``OutboxBackedBudget`` with an in-memory outbox and a $0.01 cap
* ``IdentityCalibrator``
* ``SchemaExtractionRuntime.extract()``

The budget adapter is intentionally fixture-backed here because
the durable production outbox remains a Phase 6 operational
deferral. The provider call is real.

Usage:
    uv run --no-sync python scripts/pilot_schema_runtime.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from veracrawl.adapters.budget.outbox_backed_budget import (
    OutboxBackedBudget,
    ProviderPriceTable,
)
from veracrawl.adapters.calibration.identity import IdentityCalibrator
from veracrawl.adapters.model_providers.openai_responses_v2 import (
    OpenAIResponsesAdapterV2,
)
from veracrawl.adapters.prompt_registry.json_prompt_registry import (
    JsonPromptRegistry,
)
from veracrawl.contracts.agent import TokenBudget
from veracrawl.contracts.common import Ref
from veracrawl.contracts.durable import OutboxRecord
from veracrawl.contracts.llm_input import Anchor
from veracrawl.contracts.token_budget import TokenUsageEvent
from veracrawl.processing.schema_extraction_runtime import (
    SchemaExtractionRuntime,
)
from veracrawl.runtime_support.runtime_mode import RuntimeMode

_EXPECTED_FIELDS = {"sku": "PILOT-001", "title": "Pilot Widget Pro", "price": 19.99}
_EXPECTED_ANCHORS = {
    "sku": ["anchor:pilot:sku"],
    "title": ["anchor:pilot:title"],
    "price": ["anchor:pilot:price"],
}

# Official standard processing price on 2026-05-10:
# GPT-5.4 mini input $0.75 / 1M tokens, output $4.50 / 1M tokens.
# This pilot applies a 20% safety multiplier so the local $0.01
# cap is conservative without reaching out to the pricing page at runtime.
_ALLOWLISTED_PRICE_PER_1K = {
    "gpt-5.4-mini": {
        "input_per_1k": 0.0009,
        "output_per_1k": 0.0054,
    },
}


class PilotProductOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    sku: str
    title: str
    price: float


class _InMemoryOutboxRepo:
    def __init__(self) -> None:
        self.appended: list[OutboxRecord] = []

    def append_outbox(self, record: OutboxRecord) -> Ref:
        self.appended.append(record)
        return f"outbox-ref:{record.id}"


def _load_env() -> tuple[str, str]:
    env_path = Path.home() / ".env"
    if not env_path.exists():
        sys.exit(f"~/.env not found at {env_path}")
    api_key: str | None = None
    model: str | None = None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        if stripped.startswith("export "):
            stripped = stripped.removeprefix("export ").strip()
        key, _, value = stripped.partition("=")
        normalized_value = _normalize_env_value(value.strip())
        if key.strip() == "OPENAI_API_KEY":
            api_key = normalized_value
        elif key.strip() == "OPENAI_MODEL":
            model = normalized_value
    if not api_key:
        sys.exit("OPENAI_API_KEY missing in ~/.env")
    if not model:
        sys.exit("OPENAI_MODEL missing in ~/.env")
    return api_key, model


def _normalize_env_value(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _write_prompt_template(root: Path) -> str:
    role_dir = root / "extractor"
    role_dir.mkdir(parents=True, exist_ok=True)
    ref = "extractor/product-pilot.v1"
    payload = {
        "ref": ref,
        "role": "extractor",
        "name": "product-pilot",
        "version": "v1",
        "template": (
            "Extract product fields from this source. Return only a JSON object "
            'with exactly these keys: "sku", "title", "price". The price must '
            "be a number, not a string.\n"
            "Source URL: {url}\n"
            "Evidence anchors:\n{anchor_text}"
        ),
        "variables": ["url", "anchor_text"],
    }
    (role_dir / "product-pilot.v1.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )
    return ref


def _build_budget(
    *,
    model_name: str,
    outbox_repo: _InMemoryOutboxRepo,
    persisted_events: list[TokenUsageEvent],
) -> OutboxBackedBudget:
    def persist(event: TokenUsageEvent) -> Ref:
        persisted_events.append(event)
        return f"payload:{event.id}"

    return OutboxBackedBudget(
        budget=TokenBudget(
            id="token-budget:pilot-schema-runtime:1",
            run_ref="run:pilot-schema-runtime:1",
            max_cost_usd=0.01,
            max_total_tokens=2_000,
        ),
        price_table=ProviderPriceTable(
            version="pilot-v1",
            prices={model_name: _ALLOWLISTED_PRICE_PER_1K[model_name]},
        ),
        outbox_repo=outbox_repo,
        record_persister=persist,
        run_ref="run:pilot-schema-runtime:1",
        command_result_ref="cmd-result:pilot-schema-runtime:1",
        event_ref="event:pilot-schema-runtime:1",
        runtime_mode=RuntimeMode.FIXTURE,
    )


def _parse_artifact_path(argv: list[str]) -> Path | None:
    if not argv:
        return None
    if len(argv) == 2 and argv[0] == "--artifact-path":
        return Path(argv[1])
    print(
        "Usage: uv run --no-sync python scripts/pilot_schema_runtime.py "
        "[--artifact-path <path>]",
        file=sys.stderr,
    )
    raise SystemExit(64)


def main() -> int:
    artifact_path = _parse_artifact_path(sys.argv[1:])
    api_key, model_name = _load_env()
    if model_name not in _ALLOWLISTED_PRICE_PER_1K:
        print(
            "[pilot-schema-runtime] OPENAI_MODEL must be one of "
            f"{sorted(_ALLOWLISTED_PRICE_PER_1K)} so the $0.01 pilot cap "
            "uses an explicit conservative price table",
            file=sys.stderr,
        )
        return 1
    print(f"[pilot-schema-runtime] model={model_name}")
    outbox_repo = _InMemoryOutboxRepo()
    persisted_events: list[TokenUsageEvent] = []
    anchors = [
        Anchor(
            id="anchor:pilot:title",
            selector="h1",
            excerpt="Pilot Widget Pro",
        ),
        Anchor(
            id="anchor:pilot:sku",
            selector="[data-sku]",
            excerpt="SKU: PILOT-001",
        ),
        Anchor(
            id="anchor:pilot:price",
            selector=".price",
            excerpt="Price: $19.99",
        ),
    ]
    with tempfile.TemporaryDirectory(prefix="veracrawl-prompt-pilot-") as tmp:
        prompt_root = Path(tmp)
        prompt_ref = _write_prompt_template(prompt_root)
        runtime = SchemaExtractionRuntime(
            provider=OpenAIResponsesAdapterV2(
                api_key=api_key,
                runtime_mode=RuntimeMode.PRODUCTION,
            ),
            prompt_registry=JsonPromptRegistry(root=prompt_root),
            token_budget=_build_budget(
                model_name=model_name,
                outbox_repo=outbox_repo,
                persisted_events=persisted_events,
            ),
            calibrator=IdentityCalibrator(),
            run_ref="run:pilot-schema-runtime:1",
        )
        print(f"[pilot-schema-runtime] sending prompt_ref={prompt_ref}")
        try:
            candidate, citations, confidences = runtime.extract(
                source_url="https://example.com/products/pilot-widget-pro",
                prompt_ref=prompt_ref,
                prompt_context={
                    "url": "https://example.com/products/pilot-widget-pro",
                    "anchor_text": "\n".join(
                        f"- {anchor.id}: {anchor.excerpt}" for anchor in anchors
                    ),
                },
                output_class=PilotProductOutput,
                anchors=anchors,
                per_field_anchor_refs=_EXPECTED_ANCHORS,
                per_field_excerpts={
                    "sku": "SKU: PILOT-001",
                    "title": "Pilot Widget Pro",
                    "price": "Price: $19.99",
                },
                per_field_raw_scores={"sku": 0.95, "title": 0.93, "price": 0.9},
                model_name=model_name,
                max_output_tokens=128,
                schema_ref="schema:pilot-product:v1",
                model_call_trace_ref="model-call-trace:pilot-schema-runtime:1",
            )
        except Exception as exc:
            print(
                "[pilot-schema-runtime] extract failed: "
                f"{type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            return 2
    if candidate.field_values != _EXPECTED_FIELDS:
        print(
            "[pilot-schema-runtime] unexpected fields: "
            f"{candidate.field_values!r}",
            file=sys.stderr,
        )
        return 3
    if len(citations) != 3 or len(confidences) != 3:
        print(
            "[pilot-schema-runtime] expected 3 citations and 3 confidences; "
            f"got {len(citations)} citations / {len(confidences)} confidences",
            file=sys.stderr,
        )
        return 4
    citations_by_ref = {citation.id: citation for citation in citations}
    for field_name, expected_anchor_refs in _EXPECTED_ANCHORS.items():
        citation_ref = candidate.field_citation_refs[field_name]
        citation = citations_by_ref[citation_ref]
        if citation.anchor_refs != expected_anchor_refs:
            print(
                "[pilot-schema-runtime] unexpected citation anchors for "
                f"{field_name}: {citation.anchor_refs!r}",
                file=sys.stderr,
            )
            return 5
    if len(persisted_events) != 1 or len(outbox_repo.appended) != 1:
        print(
            "[pilot-schema-runtime] token usage was not durably recorded once",
            file=sys.stderr,
        )
        return 6
    usage = persisted_events[0].usage
    if artifact_path is not None:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        artifact = {
            "pilot": "schema-runtime-openai-smoke",
            "pilot_date": "2026-05-10",
            "scope": (
                "smoke-only: provider path is real OpenAI PRODUCTION; "
                "budget persistence is fixture-backed and does not satisfy "
                "Phase 6 production outbox acceptance"
            ),
            "model_name": model_name,
            "field_values": candidate.field_values,
            "field_citation_refs": candidate.field_citation_refs,
            "citation_anchor_refs": {
                citation.field_name: citation.anchor_refs for citation in citations
            },
            "confidence_count": len(confidences),
            "usage": {
                "prompt_tokens": usage.prompt_tokens,
                "completion_tokens": usage.completion_tokens,
                "total_tokens": usage.total_tokens,
            },
            "charged_cost_usd": persisted_events[0].cost_usd,
            "price_table": {
                "version": "pilot-openai-gpt-5.4-mini-2026-05-10-conservative",
                "prices_per_1k": _ALLOWLISTED_PRICE_PER_1K[model_name],
            },
        }
        artifact_path.write_text(
            json.dumps(artifact, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    print(
        "[pilot-schema-runtime] OK: "
        f"fields={candidate.field_values!r} "
        f"citations={len(citations)} confidences={len(confidences)} "
        f"usage(prompt={usage.prompt_tokens}, completion={usage.completion_tokens}, "
        f"total={usage.total_tokens}) "
        f"charged_cost=${persisted_events[0].cost_usd:.8f}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
