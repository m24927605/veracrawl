"""``AgentCredentialLifecycle`` — Phase 2 step 2.5a.

Manages the lifecycle of credential refs an agent run is
authorized to use:

1. **Start**: resolve every ``credential_scope_refs`` entry on the
   :class:`AgentRunRequest` via :class:`CredentialScopeRegistryPort`.
   Hold the resolved :class:`CredentialScope` records (not credential
   values — those are fetched lazily by
   :class:`AuthorizedSessionAdapter` on each request). Emit a
   structured-log ``agent_credential_session_started`` event so the
   audit pipeline can correlate the run with the resolved scopes.

2. **End**: emit ``agent_credential_session_ended`` event with
   total credential-use count for the run. Invoke an injectable
   ``on_session_end`` callback (Phase 6 wires this to a vault
   cache-invalidation hook so any cached tokens are dropped at
   run completion).

Used as a context manager:

    with AgentCredentialLifecycle.start(
        request=agent_run_request,
        registry=scope_registry,
        run_ref=run_ref,
    ) as session:
        # session.scopes is a tuple[CredentialScope, ...]
        adapter = AuthorizedSessionAdapter(
            ...,
            credential_scope=session.scope_for("cred-scope:ebay"),
            ...,
        )

The session itself does not fetch credentials — that's the
:class:`AuthorizedSessionAdapter`'s job. The session just
bookkeeps the resolved scopes and the lifecycle audit events.

**Reservation (Phase 5 integration)**: this lifecycle is the
*building block*. The agent runtime in ``agents/runtime.py`` /
``agents/orchestration.py`` does NOT yet open a lifecycle context
for every ``AgentRunRequest``. Phase 5 step 5.1 (recovery /
agent runtime upgrade) wires the lifecycle into the orchestrator
so every credentialed run automatically resolves and invalidates.
Until then, callers that need credential lifecycle bookkeeping
(typically Phase 2 step 2.5b live test, the Phase 6 production
adapter) construct the lifecycle explicitly per the
``with`` form above. STATUS.md tracks this reservation.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from types import TracebackType

from veracrawl.contracts.agent import AgentRunRequest
from veracrawl.contracts.common import Ref
from veracrawl.contracts.security_privacy import CredentialScope
from veracrawl.ports.credential_scope_registry import (
    CredentialScopeRegistryPort,
)
from veracrawl.runtime_support.logging import get_logger

_logger = get_logger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _noop_on_session_end(scopes: Iterable[CredentialScope]) -> None:
    del scopes


class LifecycleEndCallbackError(RuntimeError):
    """Raised when ``on_session_end`` raises and no original exception
    is in flight. Wrapping ensures a failed cache-invalidation hook
    surfaces to the orchestrator instead of silently completing the
    run with possibly-stale credential state.
    """


class AgentCredentialLifecycle:
    """Per-run credential-scope holder and lifecycle audit.

    The class is a context manager:

    * ``__enter__`` resolves every scope_ref via the registry,
      records the resolved scopes, and emits the start audit event.
    * ``__exit__`` emits the end audit event and invokes the
      ``on_session_end`` callback (defaults to a no-op).

    The session is stateless beyond its resolved scopes and the
    lifecycle session id (a UUID). It is NOT designed to be
    reused — construct one per agent run.
    """

    def __init__(
        self,
        *,
        request: AgentRunRequest,
        registry: CredentialScopeRegistryPort,
        run_ref: Ref,
        on_session_end: Callable[[Iterable[CredentialScope]], None] = _noop_on_session_end,
        clock: Callable[[], datetime] = _utc_now,
    ) -> None:
        self._request = request
        self._registry = registry
        self._run_ref = run_ref
        self._on_session_end = on_session_end
        self._clock = clock
        self._session_id = f"agent-credential-session:{uuid.uuid4().hex}"
        # ``_scopes`` is populated by ``__enter__``; tuple keeps
        # the surface immutable post-resolution.
        self._scopes: tuple[CredentialScope, ...] = ()
        self._scope_by_ref: dict[Ref, CredentialScope] = {}
        # Per-run credential-use counter. The
        # ``AuthorizedSessionAdapter`` (Phase 2 step 2.4b) calls
        # :meth:`record_use` on each successful credential-bearing
        # request; the count lands on the
        # ``agent_credential_session_ended`` event so the audit
        # pipeline can correlate with the count of
        # CredentialUseRecord rows for the same run_ref.
        self._credential_use_count = 0

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def scopes(self) -> tuple[CredentialScope, ...]:
        return self._scopes

    @property
    def credential_use_count(self) -> int:
        return self._credential_use_count

    def record_use(self) -> None:
        """Increment the per-run credential-use counter. The
        ``AuthorizedSessionAdapter`` (Phase 2 step 2.4b) calls
        this on each successful credential-bearing request so the
        end event can report the total.
        """

        self._credential_use_count += 1

    def scope_for(self, scope_ref: Ref) -> CredentialScope:
        """Return the resolved :class:`CredentialScope` for the
        given scope_ref. Raises :class:`KeyError` for unknown
        refs (the registry resolution at __enter__ is the
        canonical lookup; this is the per-request accessor)."""

        if scope_ref not in self._scope_by_ref:
            raise KeyError(f"scope_ref not resolved by this session (length={len(scope_ref)})")
        return self._scope_by_ref[scope_ref]

    def _now(self) -> datetime:
        """Defense-in-depth tz-aware guard symmetric with
        ``OutboxVaultClient`` and ``AuthorizedSessionAdapter`` —
        replay determinism requires every audit timestamp to be
        tz-aware."""

        ts = self._clock()
        if ts.tzinfo is None or ts.utcoffset() is None:
            raise RuntimeError(
                "AgentCredentialLifecycle.clock returned a tz-naive "
                "datetime; replay determinism requires tz-aware timestamps"
            )
        return ts

    def __enter__(self) -> AgentCredentialLifecycle:
        # Resolve into locals first; assign onto the lifecycle
        # only after every ref has resolved. A partial-failure
        # scenario therefore leaves the lifecycle in its initial
        # state (no resolved scopes, no end event), which the
        # ``with`` form correctly treats as "session never
        # entered" — no __exit__ runs, no stale audit row.
        resolved: list[CredentialScope] = []
        scope_by_ref: dict[Ref, CredentialScope] = {}
        for scope_ref in self._request.credential_scope_refs:
            scope = self._registry.resolve(scope_ref)
            resolved.append(scope)
            scope_by_ref[scope_ref] = scope
        self._scopes = tuple(resolved)
        self._scope_by_ref = scope_by_ref
        timestamp = self._now()
        _logger.info(
            "agent_credential_session_started",
            session_id=self._session_id,
            run_ref=self._run_ref,
            agent_run_request_id=self._request.id,
            scope_count=len(self._scopes),
            scope_ids=tuple(scope.id for scope in self._scopes),
            timestamp_iso=timestamp.isoformat(),
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        del exc_val, exc_tb
        timestamp = self._now()
        # Run cleanup BEFORE emitting the end event so the audit
        # row's ``cleanup_succeeded`` field reflects the cleanup
        # outcome (rather than always claiming success and forcing
        # the operator to check a separate fallback log to detect
        # cleanup failure). When an original exception is in
        # flight, log + swallow the callback failure so the
        # original error reaches the caller; otherwise raise
        # ``LifecycleEndCallbackError`` after the end event.
        callback_failed = False
        try:
            self._on_session_end(self._scopes)
        except Exception:
            callback_failed = True
        cleanup_succeeded = not callback_failed
        _logger.info(
            "agent_credential_session_ended",
            session_id=self._session_id,
            run_ref=self._run_ref,
            agent_run_request_id=self._request.id,
            scope_count=len(self._scopes),
            credential_use_count=self._credential_use_count,
            ended_with_exception=exc_type is not None,
            cleanup_succeeded=cleanup_succeeded,
            timestamp_iso=timestamp.isoformat(),
        )
        if callback_failed:
            _logger.error(  # noqa: TRY400
                "agent_credential_session_end_callback_failed",
                session_id=self._session_id,
                run_ref=self._run_ref,
                timestamp_iso=timestamp.isoformat(),
                masked_by_original_exception=exc_type is not None,
            )
            if exc_type is None:
                raise LifecycleEndCallbackError(
                    "agent credential session end callback failed; "
                    "see structured-log fallback "
                    "``agent_credential_session_end_callback_failed``"
                ) from None


__all__ = ["AgentCredentialLifecycle", "LifecycleEndCallbackError"]
