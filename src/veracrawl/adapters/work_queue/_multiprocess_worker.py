"""Top-level worker entry point for ``MultiprocessWorkerPool``.

Lives in its own module so the subprocess can import it via
``multiprocessing.get_context('spawn')`` without inheriting the parent
process's state. The worker imports the caller-supplied execute
function by ``module:qualname`` reference so closures don't need to be
pickled (closures are not picklable across spawned processes).

Each worker pulls ``(work_item_ref,)`` tuples off ``input_q`` until it
sees the ``None`` sentinel, runs the resolved callable, and puts
``(worker_id, work_item_ref, outcome_json)`` tuples onto ``output_q``.
``outcome_json`` is the pydantic-serialized ``WorkOutcome``; the
parent reconstructs the model with strict validation.

Module is private (``_multiprocess_worker``); callers should use
``MultiprocessWorkerPool`` directly.
"""

from __future__ import annotations

import importlib
import multiprocessing
import multiprocessing.queues as mp_queues
import traceback
from typing import Any

_SENTINEL = None


def _resolve_callable(reference: str) -> Any:
    """Resolve ``module:qualname`` to a callable in this subprocess."""

    module_path, _, qualname = reference.partition(":")
    if not module_path or not qualname:
        raise ValueError(
            f"execute reference {reference!r} must be 'module:qualname'",
        )
    module = importlib.import_module(module_path)
    attr: Any = module
    for piece in qualname.split("."):
        attr = getattr(attr, piece)
    return attr


def _worker_loop(
    input_q: mp_queues.Queue[str | None],
    output_q: mp_queues.Queue[tuple[str, str, str]],
    worker_id: str,
    execute_reference: str,
) -> None:
    """Pull work items off ``input_q``, run them, put outcomes on ``output_q``.

    Uses pydantic v2's ``model_dump_json`` for cross-process transport;
    closures are not picklable, so the caller passes a string reference
    that this loop resolves locally.
    """

    execute_fn = _resolve_callable(execute_reference)
    while True:
        item = input_q.get()
        if item == _SENTINEL:
            break
        try:
            outcome = execute_fn(item)
            outcome_json = outcome.model_dump_json()
        except Exception as exc:
            # Fail-safe: caller-supplied callables shouldn't crash a
            # whole subprocess; convert raised exceptions into a
            # ``WorkOutcome(success=False)`` payload so the parent
            # still gets one outcome per dispatched item.
            from veracrawl.contracts.worker_lease import WorkOutcome
            outcome = WorkOutcome(
                success=False,
                error_kind=type(exc).__name__,
            )
            outcome_json = outcome.model_dump_json()
            traceback.print_exc()
        output_q.put((worker_id, item, outcome_json))


def spawn_worker(
    ctx: multiprocessing.context.BaseContext,
    *,
    input_q: mp_queues.Queue[str | None],
    output_q: mp_queues.Queue[tuple[str, str, str]],
    worker_id: str,
    execute_reference: str,
) -> multiprocessing.Process:
    p = ctx.Process(
        target=_worker_loop,
        args=(input_q, output_q, worker_id, execute_reference),
        name=f"veracrawl-worker-{worker_id}",
    )
    p.start()
    return p


__all__ = ["spawn_worker"]
