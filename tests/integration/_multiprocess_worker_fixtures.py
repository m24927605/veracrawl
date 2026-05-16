"""Top-level execute callables used by ``test_multiprocess_worker_pool_live``.

The s17 ``MultiprocessWorkerPool`` requires importable callables (no
closures, since ``multiprocessing.get_context('spawn')`` workers
re-import everything in a fresh interpreter). These functions are
defined here so the test can pass ``module:qualname`` references.
"""

from __future__ import annotations

from veracrawl.contracts.worker_lease import WorkOutcome


def echo_success(work_item_ref: str) -> WorkOutcome:
    """Pretend to do work; always succeed."""

    del work_item_ref
    return WorkOutcome(success=True)


def echo_failure(work_item_ref: str) -> WorkOutcome:
    """Pretend to do work; always fail transiently."""

    del work_item_ref
    return WorkOutcome(success=False, error_kind="simulated_transient")
