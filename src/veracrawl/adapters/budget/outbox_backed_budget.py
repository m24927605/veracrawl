"""Phase 4 step 4.5 — durable token-budget adapter.

``OutboxBackedBudget`` enforces a per-run :class:`TokenBudget`
across multiple ``ModelProviderPortV2.complete`` calls. Every
call produces:

1. a pre-flight :class:`TokenUsageEstimate` — refused if the
   estimate alone would breach the cap (no provider call).
2. a post-call :class:`TokenUsageEvent` durably persisted to
   the outbox under ``dispatch_topic="token-usage"`` BEFORE
   the in-memory advisory total updates.
3. a :class:`TokenBudgetExceeded` raise AFTER the durable
   persist if the new total breaches the cap (replay can
   reconstruct the breach moment from the durable record).

This mirrors the durable-audit-authoritative policy settled
in Phase 2 step 2.5b: durable record is the source of truth;
the in-memory counter is best-effort. Phase 5 step 5.1 will
derive the counter from the durable outbox by construction
(removing the divergence-prone parallel state).

Estimator strategy (Phase 4 fixture-mode):
- ``DefaultUsageEstimator`` uses a deterministic heuristic
  (UTF-8 byte-length / 4 ≈ tokens for English text) with a
  conservative completion-tokens estimate
  (``min(max_output_tokens, 256)``). Real tokenizers
  (tiktoken / Anthropic) wired in Phase 6 step 6.1.

Pricing strategy:
- ``ProviderPriceTable`` is loaded from
  ``prompts/_meta/provider_prices.<vN>.json`` (JSON, not
  YAML — same dep-tightness rationale as the prompt
  registry). Cost = ``prompt_tokens * input_price_per_1k /
  1000 + completion_tokens * output_price_per_1k / 1000``.
"""

from __future__ import annotations

import json
import math
import threading
import uuid
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from veracrawl.contracts.agent import TokenBudget, TokenUsage
from veracrawl.contracts.common import Ref
from veracrawl.contracts.errors import TokenBudgetExceeded
from veracrawl.contracts.llm_input import ProviderRequest, TokenUsageEstimate
from veracrawl.contracts.token_budget import TokenUsageEvent
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    current_mode,
)


def _ensure_non_blank(name: str, value: str) -> None:
    if not value or not value.strip():
        raise ValueError(f"{name} must be a non-blank identifier")


class ProviderPriceTable:
    """Pinned per-1k-token cost table.

    JSON shape:

    .. code-block:: json

        {
          "version": "v1",
          "prices": {
            "gpt-4o-mini": {"input_per_1k": 0.00015, "output_per_1k": 0.0006},
            "claude-sonnet-4-6": {"input_per_1k": 0.003, "output_per_1k": 0.015}
          }
        }

    Boundary invariants: prices are non-negative finite
    numbers; missing model entries raise on lookup so a
    typo'd ``model_name`` never silently price-as-zero.
    """

    def __init__(self, *, version: str, prices: dict[str, dict[str, float]]) -> None:
        _ensure_non_blank("price table version", version)
        for model_name, entry in prices.items():
            _ensure_non_blank("price table model_name", model_name)
            for key in ("input_per_1k", "output_per_1k"):
                if key not in entry:
                    raise ValueError(
                        f"price table entry for {model_name!r} missing {key!r}"
                    )
                value = entry[key]
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    raise ValueError(
                        f"price table {key} for {model_name!r} must be a number"
                    )
                if not math.isfinite(value):
                    raise ValueError(
                        f"price table {key} for {model_name!r} must be finite"
                    )
                if value < 0:
                    raise ValueError(
                        f"price table {key} for {model_name!r} must be non-negative"
                    )
        self.version = version
        self._prices = prices

    @classmethod
    def from_json_file(cls, path: Path | str) -> ProviderPriceTable:
        resolved = Path(path).resolve(strict=False)
        if not resolved.exists():
            raise ValueError(
                f"price table file does not exist: {resolved!r}"
            )
        try:
            payload = json.loads(resolved.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError("price table JSON is invalid") from exc
        if not isinstance(payload, dict):
            raise ValueError("price table JSON must be an object")
        version = payload.get("version")
        prices = payload.get("prices")
        if not isinstance(version, str):
            raise ValueError("price table missing 'version' string")
        if not isinstance(prices, dict):
            raise ValueError("price table missing 'prices' object")
        return cls(version=version, prices=prices)

    def cost_for(
        self,
        *,
        model_name: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        if model_name not in self._prices:
            raise ValueError(
                f"no price entry for model {model_name!r} in price table "
                f"version {self.version!r}"
            )
        entry = self._prices[model_name]
        return (
            prompt_tokens * entry["input_per_1k"] / 1000.0
            + completion_tokens * entry["output_per_1k"] / 1000.0
        )


class DefaultUsageEstimator:
    """Heuristic prompt-token estimator (Phase 4 fixture mode).

    Counts UTF-8 bytes / 4 across all message contents — a
    conservative-but-deterministic stand-in for real
    tokenizers. The result is intentionally a slight
    over-estimate so the budget gate trips slightly earlier
    than the real call would. Real tokenizers wired in Phase
    6 step 6.1.
    """

    def estimate(self, request: ProviderRequest) -> tuple[int, int]:
        """Return ``(prompt_tokens_estimate, completion_tokens_estimate)``."""

        prompt_bytes = sum(
            len(message.content.encode("utf-8")) for message in request.messages
        )
        prompt_tokens = max(1, (prompt_bytes + 3) // 4)
        # Conservative completion estimate: assume the model
        # produces up to ``min(max_output_tokens, 256)``.
        completion_tokens = min(request.max_output_tokens, 256)
        return prompt_tokens, completion_tokens


class OutboxBackedBudget:
    """Durable token-budget enforcement via the outbox."""

    def __init__(
        self,
        *,
        budget: TokenBudget,
        price_table: ProviderPriceTable,
        outbox_repo: Any,  # OutboxRepositoryPort, kept Any to avoid circular
        record_persister: Callable[[TokenUsageEvent], Ref],
        run_ref: Ref,
        command_result_ref: Ref,
        event_ref: Ref,
        clock: Callable[[], datetime] | None = None,
        estimator: DefaultUsageEstimator | None = None,
        runtime_mode: RuntimeMode | None = None,
    ) -> None:
        effective_mode = runtime_mode if runtime_mode is not None else current_mode()
        if effective_mode is RuntimeMode.PRODUCTION:
            raise ProductionRuntimeNotImplemented(
                backend="outbox_backed_budget",
                gate="phase_4_step_4_5_production_persist",
            )
        _ensure_non_blank("run_ref", run_ref)
        _ensure_non_blank("command_result_ref", command_result_ref)
        _ensure_non_blank("event_ref", event_ref)
        if budget.run_ref != run_ref:
            raise ValueError(
                "budget.run_ref must equal the budget's bound run_ref"
            )
        self._budget = budget
        self._price_table = price_table
        self._outbox_repo = outbox_repo
        self._record_persister = record_persister
        self._run_ref = run_ref
        self._command_result_ref = command_result_ref
        self._event_ref = event_ref
        self._clock: Callable[[], datetime] = clock or (lambda: datetime.now(UTC))
        self._estimator = estimator or DefaultUsageEstimator()
        self._lock = threading.Lock()
        # Advisory in-memory totals.
        self._total_prompt = 0
        self._total_completion = 0
        self._total_cost_usd = 0.0
        self._charged_count = 0

    def estimate_charge(self, request: ProviderRequest) -> TokenUsageEstimate:
        prompt_estimate, completion_estimate = self._estimator.estimate(request)
        cost_estimate = self._price_table.cost_for(
            model_name=request.model_name,
            prompt_tokens=prompt_estimate,
            completion_tokens=completion_estimate,
        )
        with self._lock:
            projected_prompt = self._total_prompt + prompt_estimate
            projected_completion = self._total_completion + completion_estimate
            projected_cost = self._total_cost_usd + cost_estimate
            self._refuse_if_breaches_cap(
                prompt=projected_prompt,
                completion=projected_completion,
                cost=projected_cost,
                phase="estimate",
            )
        return TokenUsageEstimate(
            request_ref=request.id,
            model_name=request.model_name,
            prompt_tokens_estimate=prompt_estimate,
            completion_tokens_estimate=completion_estimate,
            cost_usd_estimate=cost_estimate,
        )

    def charge(self, usage: TokenUsage, *, request_ref: Ref) -> None:
        _ensure_non_blank("request_ref", request_ref)
        # Resolve model_name from the request_ref by relying on
        # the caller embedding it; the budget never needs to
        # call back into the request store. The model_name is
        # passed via the price table's keys at construction;
        # callers that need cross-model accounting hold separate
        # budgets.
        model_name = self._infer_model_name_for_request(request_ref)
        cost_usd = self._price_table.cost_for(
            model_name=model_name,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
        )
        event = TokenUsageEvent(
            id=f"token-usage:{uuid.uuid4().hex}",
            run_ref=self._run_ref,
            request_ref=request_ref,
            model_name=model_name,
            usage=usage,
            cost_usd=cost_usd,
            price_table_version=self._price_table.version,
        )
        # Durable persist FIRST (mirrors Phase 2 step 2.5b
        # durable-audit-authoritative policy).
        payload_ref = self._record_persister(event)
        outbox_record = self._build_outbox_record(event=event, payload_ref=payload_ref)
        self._outbox_repo.append_outbox(outbox_record)
        # Now update advisory totals + check cap.
        with self._lock:
            self._total_prompt += usage.prompt_tokens
            self._total_completion += usage.completion_tokens
            self._total_cost_usd += cost_usd
            self._charged_count += 1
            self._refuse_if_breaches_cap(
                prompt=self._total_prompt,
                completion=self._total_completion,
                cost=self._total_cost_usd,
                phase="charge",
            )

    @property
    def charged_count(self) -> int:
        with self._lock:
            return self._charged_count

    @property
    def total_cost_usd(self) -> float:
        with self._lock:
            return self._total_cost_usd

    def _refuse_if_breaches_cap(
        self,
        *,
        prompt: int,
        completion: int,
        cost: float,
        phase: str,
    ) -> None:
        b = self._budget
        if b.max_input_tokens is not None and prompt > b.max_input_tokens:
            raise TokenBudgetExceeded(
                status_code=0,
                error_code="TOKEN_BUDGET_EXCEEDED",
                request_id=None,
            )
        if b.max_output_tokens is not None and completion > b.max_output_tokens:
            raise TokenBudgetExceeded(
                status_code=0,
                error_code="TOKEN_BUDGET_EXCEEDED",
                request_id=None,
            )
        if (
            b.max_total_tokens is not None
            and prompt + completion > b.max_total_tokens
        ):
            raise TokenBudgetExceeded(
                status_code=0,
                error_code="TOKEN_BUDGET_EXCEEDED",
                request_id=None,
            )
        if b.max_cost_usd is not None and cost > b.max_cost_usd:
            raise TokenBudgetExceeded(
                status_code=0,
                error_code="TOKEN_BUDGET_EXCEEDED",
                request_id=None,
            )
        del phase  # arg kept for future telemetry

    def _build_outbox_record(
        self, *, event: TokenUsageEvent, payload_ref: Ref
    ) -> Any:
        from veracrawl.contracts.durable import OutboxRecord

        return OutboxRecord(
            id=f"outbox:{event.id}",
            run_ref=self._run_ref,
            command_result_ref=self._command_result_ref,
            event_ref=self._event_ref,
            dispatch_topic="token-usage",
            payload_ref=payload_ref,
            idempotency_key=event.id,
        )

    def _infer_model_name_for_request(self, request_ref: Ref) -> str:
        # The caller passes ``request_ref`` (string id of the
        # ``ProviderRequest`` that produced this usage). The
        # budget does not store a request-ref → model-name map
        # itself; callers either hold separate budget instances
        # per model or pass the model_name via the
        # ``ProviderRequest.id`` shape (e.g.,
        # ``provider-request:{model}:{seq}``). For Phase 4
        # fixture-mode tests, the price table holds a single
        # model and we treat that as the implicit binding.
        if len(self._price_table._prices) == 1:
            return next(iter(self._price_table._prices))
        # If the request_ref encodes the model under a known
        # convention, parse it; otherwise the caller must use
        # one model per budget.
        for candidate in self._price_table._prices:
            if candidate in request_ref:
                return candidate
        raise ValueError(
            "could not infer model_name from request_ref; "
            "use one OutboxBackedBudget per model or embed the "
            "model name in the ProviderRequest id"
        )


__all__ = ["OutboxBackedBudget", "ProviderPriceTable", "DefaultUsageEstimator"]
