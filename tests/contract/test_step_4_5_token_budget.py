"""Phase 4 step 4.5 — TokenBudgetPort + OutboxBackedBudget contract tests."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from veracrawl.adapters.budget.outbox_backed_budget import (
    OutboxBackedBudget,
    ProviderPriceTable,
)
from veracrawl.contracts.agent import (
    Message,
    ResponseFormat,
    TokenBudget,
    TokenUsage,
)
from veracrawl.contracts.common import Ref
from veracrawl.contracts.durable import OutboxRecord
from veracrawl.contracts.enums import MessageRole, ResponseFormatKind
from veracrawl.contracts.errors import TokenBudgetExceeded
from veracrawl.contracts.llm_input import ProviderRequest
from veracrawl.contracts.token_budget import TokenUsageEvent
from veracrawl.ports.token_budget import TokenBudgetPort
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
)

_FROZEN_NOW = datetime(2026, 5, 9, 12, 0, 0, tzinfo=UTC)


class _InMemoryOutboxRepo:
    def __init__(self) -> None:
        self.appended: list[OutboxRecord] = []

    def append_outbox(self, record: OutboxRecord) -> Ref:
        self.appended.append(record)
        return f"outbox-ref:{record.id}"

    def list_pending_outbox(self, run_ref: Ref) -> list[OutboxRecord]:
        del run_ref
        return list(self.appended)

    def mark_outbox_dispatched(
        self, outbox_ref: Ref, *, dispatched_at_ref: Ref
    ) -> OutboxRecord:
        del outbox_ref, dispatched_at_ref
        raise NotImplementedError

    def mark_outbox_failed(self, outbox_ref: Ref, *, error_ref: Ref) -> OutboxRecord:
        del outbox_ref, error_ref
        raise NotImplementedError


def _make_request(model_name: str = "gpt-4o-mini", text: str = "extract") -> ProviderRequest:
    return ProviderRequest(
        id=f"provider-request:{model_name}:1",
        run_ref="run:phase-4-5:1",
        model_name=model_name,
        messages=[Message(role=MessageRole.USER, content=text)],
        response_format=ResponseFormat(kind=ResponseFormatKind.TEXT),
        max_output_tokens=128,
    )


def _make_budget(
    *,
    max_total_tokens: int | None = None,
    max_cost_usd: float | None = None,
    max_input_tokens: int | None = None,
    max_output_tokens: int | None = None,
) -> TokenBudget:
    if all(
        cap is None
        for cap in (max_total_tokens, max_cost_usd, max_input_tokens, max_output_tokens)
    ):
        max_total_tokens = 10_000
    return TokenBudget(
        id="token-budget:phase-4-5:1",
        run_ref="run:phase-4-5:1",
        max_input_tokens=max_input_tokens,
        max_output_tokens=max_output_tokens,
        max_total_tokens=max_total_tokens,
        max_cost_usd=max_cost_usd,
    )


def _build_price_table() -> ProviderPriceTable:
    return ProviderPriceTable(
        version="v1",
        prices={
            "gpt-4o-mini": {"input_per_1k": 0.00015, "output_per_1k": 0.0006},
            "claude-sonnet-4-6": {"input_per_1k": 0.003, "output_per_1k": 0.015},
        },
    )


def _build_budget_adapter(
    *,
    budget: TokenBudget | None = None,
    price_table: ProviderPriceTable | None = None,
    persisted: list[TokenUsageEvent] | None = None,
    outbox: _InMemoryOutboxRepo | None = None,
) -> OutboxBackedBudget:
    persisted_events = persisted if persisted is not None else []

    def persister(event: TokenUsageEvent) -> Ref:
        persisted_events.append(event)
        return f"payload:{event.id}"

    return OutboxBackedBudget(
        budget=budget or _make_budget(),
        price_table=price_table or _build_price_table(),
        outbox_repo=outbox or _InMemoryOutboxRepo(),
        record_persister=persister,
        run_ref="run:phase-4-5:1",
        command_result_ref="cmd-result:phase-4-5:1",
        event_ref="event:phase-4-5:1",
        clock=lambda: _FROZEN_NOW,
        runtime_mode=RuntimeMode.FIXTURE,
    )


# --- ProviderPriceTable -----------------------------------------------------


def test_price_table_round_trip() -> None:
    table = _build_price_table()
    cost = table.cost_for(
        model_name="gpt-4o-mini",
        prompt_tokens=1000,
        completion_tokens=500,
    )
    # 1000 * 0.00015/1000 + 500 * 0.0006/1000 = 0.00015 + 0.0003 = 0.00045
    assert cost == pytest.approx(0.00045)


def test_price_table_rejects_unknown_model() -> None:
    table = _build_price_table()
    with pytest.raises(ValueError, match="no price entry"):
        table.cost_for(
            model_name="unknown-model",
            prompt_tokens=100,
            completion_tokens=50,
        )


def test_price_table_rejects_negative_price() -> None:
    with pytest.raises(ValueError, match="must be non-negative"):
        ProviderPriceTable(
            version="v1",
            prices={
                "model": {"input_per_1k": -0.01, "output_per_1k": 0.001},
            },
        )


def test_price_table_rejects_non_finite_price() -> None:
    with pytest.raises(ValueError, match="must be finite"):
        ProviderPriceTable(
            version="v1",
            prices={
                "model": {"input_per_1k": float("nan"), "output_per_1k": 0.001},
            },
        )


def test_price_table_rejects_blank_version() -> None:
    with pytest.raises(ValueError, match="version"):
        ProviderPriceTable(
            version="   ",
            prices={
                "model": {"input_per_1k": 0.001, "output_per_1k": 0.002},
            },
        )


def test_price_table_loads_from_json_file(tmp_path: Path) -> None:
    path = tmp_path / "prices.v1.json"
    path.write_text(
        json.dumps(
            {
                "version": "v1",
                "prices": {
                    "gpt-4o-mini": {"input_per_1k": 0.00015, "output_per_1k": 0.0006},
                },
            }
        ),
        encoding="utf-8",
    )
    table = ProviderPriceTable.from_json_file(path)
    assert table.version == "v1"


def test_price_table_load_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("not valid json", encoding="utf-8")
    with pytest.raises(ValueError, match="JSON is invalid"):
        ProviderPriceTable.from_json_file(path)


# --- TokenUsageEvent --------------------------------------------------------


def test_token_usage_event_round_trip() -> None:
    event = TokenUsageEvent(
        id="token-usage:abcdef",
        run_ref="run:phase-4-5:1",
        request_ref="provider-request:1",
        model_name="gpt-4o-mini",
        usage=TokenUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        ),
        cost_usd=0.00045,
        price_table_version="v1",
    )
    assert event.cost_usd == 0.00045


def test_token_usage_event_rejects_non_finite_cost() -> None:
    with pytest.raises(ValueError, match="finite"):
        TokenUsageEvent(
            id="token-usage:abcdef",
            run_ref="run:phase-4-5:1",
            request_ref="provider-request:1",
            model_name="gpt-4o-mini",
            usage=TokenUsage(
                prompt_tokens=100,
                completion_tokens=50,
                total_tokens=150,
            ),
            cost_usd=float("inf"),
            price_table_version="v1",
        )


# --- OutboxBackedBudget -----------------------------------------------------


def test_construction_gates_blank_run_ref() -> None:
    with pytest.raises(ValueError, match="run_ref"):
        OutboxBackedBudget(
            budget=_make_budget(),
            price_table=_build_price_table(),
            outbox_repo=_InMemoryOutboxRepo(),
            record_persister=lambda _: "payload:x",
            run_ref="   ",
            command_result_ref="cmd-result:1",
            event_ref="event:1",
            runtime_mode=RuntimeMode.FIXTURE,
        )


def test_construction_rejects_budget_run_ref_mismatch() -> None:
    budget = TokenBudget(
        id="token-budget:1",
        run_ref="run:other",
        max_total_tokens=1000,
    )
    with pytest.raises(ValueError, match="bound run_ref"):
        OutboxBackedBudget(
            budget=budget,
            price_table=_build_price_table(),
            outbox_repo=_InMemoryOutboxRepo(),
            record_persister=lambda _: "payload:x",
            run_ref="run:phase-4-5:1",
            command_result_ref="cmd-result:1",
            event_ref="event:1",
            runtime_mode=RuntimeMode.FIXTURE,
        )


def test_construction_production_mode_raises() -> None:
    with pytest.raises(ProductionRuntimeNotImplemented):
        OutboxBackedBudget(
            budget=_make_budget(),
            price_table=_build_price_table(),
            outbox_repo=_InMemoryOutboxRepo(),
            record_persister=lambda _: "payload:x",
            run_ref="run:phase-4-5:1",
            command_result_ref="cmd-result:1",
            event_ref="event:1",
            runtime_mode=RuntimeMode.PRODUCTION,
        )


def test_construction_consults_current_mode_when_runtime_mode_omitted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("VERACRAWL_RUNTIME_MODE", "production")
    with pytest.raises(ProductionRuntimeNotImplemented):
        OutboxBackedBudget(
            budget=_make_budget(),
            price_table=_build_price_table(),
            outbox_repo=_InMemoryOutboxRepo(),
            record_persister=lambda _: "payload:x",
            run_ref="run:phase-4-5:1",
            command_result_ref="cmd-result:1",
            event_ref="event:1",
        )


def test_estimate_charge_under_cap_returns_estimate() -> None:
    adapter = _build_budget_adapter()
    estimate = adapter.estimate_charge(_make_request())
    assert estimate.prompt_tokens_estimate >= 1
    assert estimate.completion_tokens_estimate <= 256
    assert estimate.cost_usd_estimate >= 0


def test_estimate_charge_refuses_when_estimate_exceeds_cap() -> None:
    tiny_budget = _make_budget(max_total_tokens=2)
    adapter = _build_budget_adapter(budget=tiny_budget)
    # The default estimator produces at least 1 prompt + 128
    # completion ≫ 2, so estimate alone trips.
    with pytest.raises(TokenBudgetExceeded):
        adapter.estimate_charge(_make_request())


def test_charge_persists_durable_event_then_updates_total() -> None:
    persisted: list[TokenUsageEvent] = []
    outbox = _InMemoryOutboxRepo()
    adapter = _build_budget_adapter(persisted=persisted, outbox=outbox)
    usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
    adapter.charge(usage, request_ref="provider-request:gpt-4o-mini:1")
    assert len(persisted) == 1
    assert persisted[0].model_name == "gpt-4o-mini"
    assert persisted[0].usage.total_tokens == 150
    # 100 * 0.00015 / 1000 + 50 * 0.0006 / 1000
    # = 0.000015 + 0.00003 = 0.000045
    assert persisted[0].cost_usd == pytest.approx(0.000045)
    assert len(outbox.appended) == 1
    assert outbox.appended[0].dispatch_topic == "token-usage"
    assert adapter.charged_count == 1


def test_charge_raises_after_durable_persist_when_breaching_cap() -> None:
    persisted: list[TokenUsageEvent] = []
    outbox = _InMemoryOutboxRepo()
    # Cap below the first charge: total=150 > 100.
    budget = _make_budget(max_total_tokens=100)
    adapter = _build_budget_adapter(
        budget=budget, persisted=persisted, outbox=outbox
    )
    usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
    with pytest.raises(TokenBudgetExceeded):
        adapter.charge(usage, request_ref="provider-request:gpt-4o-mini:1")
    # Durable persist happened BEFORE the raise — replay can
    # reconstruct the breach moment.
    assert len(persisted) == 1
    assert len(outbox.appended) == 1


def test_charge_cap_breach_on_cost_usd() -> None:
    persisted: list[TokenUsageEvent] = []
    # 1M prompt + 1M completion at $0.00015 + $0.0006 / 1k =
    # $0.00015 + $0.0006 = $0.00075 / token-pair × 1M each:
    # actually 1_000_000 * 0.00015/1000 = 0.15, plus
    # 1_000_000 * 0.0006/1000 = 0.6 → total $0.75
    budget = _make_budget(max_cost_usd=0.10)
    adapter = _build_budget_adapter(budget=budget, persisted=persisted)
    usage = TokenUsage(
        prompt_tokens=1_000_000,
        completion_tokens=1_000_000,
        total_tokens=2_000_000,
    )
    with pytest.raises(TokenBudgetExceeded):
        adapter.charge(usage, request_ref="provider-request:gpt-4o-mini:1")
    assert len(persisted) == 1


def test_consecutive_charges_accumulate_advisory_total() -> None:
    persisted: list[TokenUsageEvent] = []
    adapter = _build_budget_adapter(persisted=persisted)
    usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    for _ in range(3):
        adapter.charge(usage, request_ref="provider-request:gpt-4o-mini:1")
    assert adapter.charged_count == 3
    assert len(persisted) == 3
    # Cost = 3 × (10 * 0.00015/1000 + 5 * 0.0006/1000)
    expected_per_call = 10 * 0.00015 / 1000 + 5 * 0.0006 / 1000
    assert adapter.total_cost_usd == pytest.approx(3 * expected_per_call)


def test_charge_request_ref_must_be_non_blank() -> None:
    adapter = _build_budget_adapter()
    usage = TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
    with pytest.raises(ValueError, match="request_ref"):
        adapter.charge(usage, request_ref="   ")


def test_runtime_checkable_protocol() -> None:
    adapter = _build_budget_adapter()
    assert isinstance(adapter, TokenBudgetPort)


def test_estimate_charge_then_charge_complete_flow() -> None:
    """End-to-end: estimate before call, charge after."""

    persisted: list[TokenUsageEvent] = []
    adapter = _build_budget_adapter(persisted=persisted)
    request = _make_request()
    estimate = adapter.estimate_charge(request)
    # Caller now issues the LLM call; assume actual usage
    # comes back close to the estimate.
    actual_usage = TokenUsage(
        prompt_tokens=estimate.prompt_tokens_estimate,
        completion_tokens=20,  # actual was less than estimate
        total_tokens=estimate.prompt_tokens_estimate + 20,
    )
    adapter.charge(actual_usage, request_ref=request.id)
    assert len(persisted) == 1
    assert persisted[0].usage.completion_tokens == 20
