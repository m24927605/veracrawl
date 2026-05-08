"""HTTP source adapter (httpx-backed).

Replaces the historical ``urllib`` shell with an httpx implementation
that adds:

- per-hop redirect SSRF policy (each redirect target is re-validated for
  cross-origin protocol downgrade, optional egress allowlist membership,
  and private-network/loopback exclusion);
- retry on 429 and 5xx with ``Retry-After`` parsing (delta-seconds and
  HTTP-date forms), capped at 60s, with exponential backoff + jitter
  fallback;
- transport / sleep / jitter injection so unit tests never touch the
  network or wall clock;
- a real Chrome User-Agent by default (the previous
  ``VeraCrawl-local-fixture/1`` UA tripped Cloudflare-class blockers
  immediately).

The class name :class:`StdlibHttpSourceAdapter` is intentionally
preserved for backwards compatibility — 13 call sites construct it as
``StdlibHttpSourceAdapter(request)`` and the new behavior is enabled
through optional keyword arguments. A new :class:`NetworkAdapterError`
inherits :class:`ValueError` so existing
``except ValueError`` handlers in the acquisition layer keep matching;
the new exception carries a structured ``failure_type`` field for
callers that want to dispatch on category.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from ipaddress import ip_address
from typing import Any, Final
from urllib.parse import urljoin, urlparse

import httpx

from veracrawl.contracts.common import stable_hash
from veracrawl.contracts.enums import (
    AdapterResultStatus,
    AdapterType,
    NetworkFailureType,
    RouteClass,
    SourceAdapterResultType,
)
from veracrawl.contracts.errors import FatalError, PolicyViolation, RetryableError
from veracrawl.contracts.network import (
    NetworkAttemptEvidence,
    NetworkRequest,
    NetworkResponse,
    RedirectHop,
)
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult
from veracrawl.ports.conditional_cache import (
    CachedConditional,
    ConditionalCachePort,
    NoopConditionalCache,
)
from veracrawl.ports.cookie_jar import CookieJarPort, NoopCookieJar
from veracrawl.ports.network import NetworkClientResult
from veracrawl.ports.rate_limiter import (
    NoopRateLimiter,
    RateLimiterPort,
    RateLimitFloor,
    RateLimitProhibited,
)
from veracrawl.ports.robots import NoopRobotsPort, RobotsAdvice, RobotsPort
from veracrawl.runtime_support.runtime_mode import (
    ProductionRuntimeNotImplemented,
    RuntimeMode,
    current_mode,
)

_DEFAULT_CHROME_UA: Final[str] = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)
_DEFAULT_MAX_REDIRECTS: Final[int] = 5
_DEFAULT_MAX_ATTEMPTS: Final[int] = 3
_RETRY_AFTER_CAP_S: Final[float] = 60.0
_RETRYABLE_STATUSES: Final[frozenset[int]] = frozenset({429, 500, 502, 503, 504})
_RETRY_AFTER_HEADER: Final[str] = "retry-after"


class NetworkAdapterError(ValueError):
    """Adapter-level failure with a structured ``failure_type``.

    Inherits :class:`ValueError` so the existing
    ``except ValueError`` handler in
    ``fetch.network_acquisition.execute_http_network_acquisition`` continues
    to match without modification. Category-specific subclasses below
    additionally mix in one of the markers from
    :mod:`veracrawl.contracts.errors` (``RetryableError`` /
    ``FatalError`` / ``PolicyViolation``) so callers can dispatch on
    category without inspecting ``failure_type``.
    """

    def __init__(self, failure_type: NetworkFailureType, detail: str) -> None:
        self.failure_type = failure_type
        self.detail = detail
        super().__init__(f"{failure_type.value}: {detail}")


class NetworkTimeoutError(NetworkAdapterError, RetryableError):
    """Transport-level timeout. Caller may retry under same policy."""

    def __init__(self, detail: str = "network request timed out") -> None:
        super().__init__(NetworkFailureType.NETWORK_TIMEOUT, detail)


# Backwards-compat alias: existing imports of ``NetworkAdapterTimeoutError``
# continue to resolve. The ``Timeout`` form was the original name shipped
# by the urllib adapter; ``NetworkTimeoutError`` is the unified name.
NetworkAdapterTimeoutError = NetworkTimeoutError


class RetryExhaustedError(NetworkAdapterError, FatalError):
    """All retry attempts consumed without success."""

    def __init__(self, detail: str) -> None:
        super().__init__(NetworkFailureType.RETRY_EXHAUSTED, detail)


class RedirectDeniedError(NetworkAdapterError, PolicyViolation):
    """Redirect target violated egress / SSRF / scheme policy."""

    def __init__(self, detail: str) -> None:
        super().__init__(NetworkFailureType.REDIRECT_DENIED, detail)


class EgressDeniedError(NetworkAdapterError, PolicyViolation):
    """Target origin not in the configured egress allowlist."""

    def __init__(self, detail: str) -> None:
        super().__init__(NetworkFailureType.EGRESS_DENIED, detail)


class PrivateNetworkDeniedError(NetworkAdapterError, PolicyViolation):
    """Target host resolves to a private / loopback / link-local address."""

    def __init__(self, detail: str) -> None:
        super().__init__(NetworkFailureType.PRIVATE_NETWORK_DENIED, detail)


class AdapterFailureError(NetworkAdapterError, FatalError):
    """Generic non-retryable adapter failure (DNS, refused, TLS, etc.)."""

    def __init__(self, detail: str) -> None:
        super().__init__(NetworkFailureType.ADAPTER_FAILURE, detail)


class SizeBudgetExceededError(NetworkAdapterError, FatalError):
    """Response body grew past the configured size budget mid-stream.

    Marker is ``FatalError``: re-issuing the same request would just
    hit the same limit. Phase 5 ``RecoveryPort`` is expected to map
    this to ``RecoveryDecisionKind.ABANDON`` or to switch adapter.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(NetworkFailureType.SIZE_BUDGET_EXCEEDED, detail)


class RobotsBlockedError(NetworkAdapterError, PolicyViolation):
    """``robots.txt`` (or per-target ToS) refused the URL.

    Marker is ``PolicyViolation`` — the charter (``docs/09:116``)
    requires honoring robots; bypass is forbidden. The orchestrator
    must record-and-terminate, never retry.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(NetworkFailureType.ROBOTS_BLOCKED, detail)


class RateBudgetExceededError(NetworkAdapterError, FatalError):
    """Per-(origin, route, adapter) rate budget exhausted for the run.

    Marker is ``FatalError``: budget refusal is per-run and a retry
    will hit the same cap; recovery must restructure (e.g., escalate
    or abandon), not retry.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(NetworkFailureType.RATE_BUDGET_EXCEEDED, detail)


class UnsafeBrowserSideEffectError(NetworkAdapterError, PolicyViolation):
    """Browser observation triggered a side-effect the policy forbids.

    Marker is ``PolicyViolation`` — the design forbids browser writes
    / form submissions / pointer events outside the authorized
    interaction surface; the orchestrator must record and terminate.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(NetworkFailureType.UNSAFE_BROWSER_SIDE_EFFECT, detail)


class MissingNetworkArtifactError(NetworkAdapterError, FatalError):
    """Expected network artifact (response body / HAR / etc.) is missing.

    Marker is ``FatalError`` — a missing artifact is a contract
    violation by the upstream layer; retrying the same request will
    not produce the missing data.
    """

    def __init__(self, detail: str) -> None:
        super().__init__(NetworkFailureType.MISSING_NETWORK_ARTIFACT, detail)


_NETWORK_FAILURE_TYPE_TO_CLASS: dict[NetworkFailureType, type[NetworkAdapterError]] = {
    NetworkFailureType.NETWORK_TIMEOUT: NetworkTimeoutError,
    NetworkFailureType.RETRY_EXHAUSTED: RetryExhaustedError,
    NetworkFailureType.REDIRECT_DENIED: RedirectDeniedError,
    NetworkFailureType.EGRESS_DENIED: EgressDeniedError,
    NetworkFailureType.PRIVATE_NETWORK_DENIED: PrivateNetworkDeniedError,
    NetworkFailureType.ADAPTER_FAILURE: AdapterFailureError,
    NetworkFailureType.SIZE_BUDGET_EXCEEDED: SizeBudgetExceededError,
    NetworkFailureType.ROBOTS_BLOCKED: RobotsBlockedError,
    NetworkFailureType.RATE_BUDGET_EXCEEDED: RateBudgetExceededError,
    NetworkFailureType.UNSAFE_BROWSER_SIDE_EFFECT: UnsafeBrowserSideEffectError,
    NetworkFailureType.MISSING_NETWORK_ARTIFACT: MissingNetworkArtifactError,
}


def classify_network_failure(failure_type: NetworkFailureType, detail: str) -> NetworkAdapterError:
    """Pick the marker-bearing subclass for ``failure_type``.

    Every value of :class:`NetworkFailureType` now has a dedicated
    marker-bearing subclass (codex iter-4 important: an unmapped
    value used to fall back to bare ``NetworkAdapterError`` without a
    marker, breaking ``except FatalError:`` / ``except PolicyViolation:``
    dispatch). The fallback for an unrecognised enum (added in some
    future commit before its subclass lands) is
    :class:`AdapterFailureError`, which carries the ``FatalError``
    marker; that keeps the dispatch contract intact while the new
    enum value waits for a dedicated class.
    """
    cls = _NETWORK_FAILURE_TYPE_TO_CLASS.get(failure_type, AdapterFailureError)
    # Every subclass takes only ``detail`` (failure_type is implied by
    # the class). The dispatch table is keyed so cls is one of the
    # known subclasses; mypy's view is the broader base type, so the
    # call-arg / arg-type signatures of the parent are reported
    # despite this being correct against every entry in the dict.
    return cls(detail)  # type: ignore[call-arg,arg-type]


@dataclass(frozen=True)
class HttpClientConfig:
    """Per-adapter HTTP client policy.

    All fields have defaults sized for a real e-commerce / general-web
    target. Tests typically inject only the fields they care about.
    """

    connect_timeout_s: float = 10.0
    read_timeout_s: float = 30.0
    max_attempts: int = _DEFAULT_MAX_ATTEMPTS
    max_redirects: int = _DEFAULT_MAX_REDIRECTS
    user_agent: str = _DEFAULT_CHROME_UA
    # Per-hop SSRF policy on redirects is OPT-IN via these two fields.
    # Defaults stay permissive so the 13 legacy single-arg call sites and
    # localhost-based fixture tests do not start failing. Production callers
    # should set ``egress_allowlist`` and ``allow_private_network=False``
    # (see the acquisition factory pattern in
    # docs/plans/p0-fix-pack/p0-1-http-client.md).
    egress_allowlist: frozenset[str] = field(default_factory=frozenset)
    allow_private_network: bool = True
    retry_after_cap_s: float = _RETRY_AFTER_CAP_S
    # ``RobotsPort`` evaluation (design.md §4 Phase 1 step 1.2). The
    # default is :class:`NoopRobotsPort` so existing fixture tests
    # without robots wiring continue to pass; production callers must
    # inject :class:`UrllibRobotsParser` (or another real impl). The
    # adapter consults this port for the initial URL **and** every
    # cross-redirect target with the same single-source-of-truth user
    # agent (``user_agent``).
    robots_port: RobotsPort = field(default_factory=NoopRobotsPort)
    # ``RateLimiterPort`` cooperative pacing (design.md §4 Phase 1
    # step 1.3). The default is :class:`NoopRateLimiter` so existing
    # fixture tests without rate-limit wiring continue to pass;
    # production callers must inject :class:`InMemoryAimdLimiter` (or
    # another real impl). The adapter acquires a permit per HTTP
    # attempt — initial URL plus every redirect target — with the
    # ``RateLimitFloor`` derived from the live ``RobotsAdvice`` so
    # ``Crawl-delay`` / ``Request-rate`` flow into the AIMD floor.
    # Successful (non-retryable) responses report success; retry
    # exhaustion on ``429`` reports throttle so multiplicative
    # decrease + cooldown apply for the next caller.
    rate_limiter: RateLimiterPort = field(default_factory=NoopRateLimiter)
    # Bucket key route class. Default :class:`RouteClass.LISTING`
    # because most cooperative crawls start from listing pages;
    # callers fetching detail / search / api / file should override
    # so AIMD state stays separated per route class.
    route_class: RouteClass = RouteClass.LISTING
    # ``ConditionalCachePort`` (design.md §4 Phase 1 step 1.5). The
    # default is :class:`NoopConditionalCache` so existing fixture
    # tests without cache wiring continue to pass; production
    # callers inject :class:`InMemoryConditionalCache` (or another
    # real impl). The adapter consults the cache before each
    # outgoing fetch to add ``If-None-Match`` / ``If-Modified-Since``
    # and short-circuits on ``304`` to the cached body.
    conditional_cache: ConditionalCachePort = field(default_factory=NoopConditionalCache)
    # ``CookieJarPort`` (design.md §4 Phase 1 step 1.5). The default
    # is :class:`NoopCookieJar` (no cookies stored or sent) — safe
    # default for existing fixture tests. Production callers inject
    # :class:`InMemoryCookieJar`. Scope: per-run + per-origin,
    # cleared at run boundary.
    cookie_jar: CookieJarPort = field(default_factory=NoopCookieJar)
    # Run scope for the conditional cache + cookie jar. ``None``
    # means "derive from ``NetworkRequest.run_ref`` at adapter
    # construction" (codex iter-4 important: hardcoded fixture
    # default leaked cache + cookies across runs when callers
    # forgot to set this). An explicit string overrides the
    # derivation — production callers can set this to a different
    # run scope if needed (e.g., re-using cookies across two
    # logical runs).
    run_ref: str | None = None
    # Extra request headers (Authorization / X-Api-Key / etc.) the
    # adapter sends with every request. ``Authorization`` and
    # related credential-bearing names are STRIPPED on cross-origin
    # redirect (RFC 7235 best practice + cooperative-crawler
    # hygiene). Default empty so existing tests are unchanged.
    extra_headers: dict[str, str] = field(default_factory=dict)


def _is_private_network_url(url: str) -> bool:
    host = urlparse(url).hostname
    if host is None:
        return True
    if host == "localhost":
        return True
    try:
        address = ip_address(host)
    except ValueError:
        return False
    return (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_unspecified
    )


def _origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _canonical_origin(url: str) -> tuple[str, str, int | None]:
    """Return ``(scheme, host, port_or_default_None)`` for cross-origin
    comparison per RFC 6454. Default port (80 for http, 443 for https)
    normalizes to ``None`` so ``http://example.com`` and
    ``http://example.com:80`` compare equal.
    """

    parsed = urlparse(url)
    scheme = (parsed.scheme or "").lower()
    host = (parsed.hostname or "").lower()
    try:
        port = parsed.port
    except ValueError:
        port = None
    if port is not None:
        if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
            port = None
    return scheme, host, port


def _is_cross_origin(from_url: str, to_url: str) -> bool:
    """``True`` when ``to_url`` is a different origin than ``from_url``.

    RFC 6454: scheme + host + port must all match; a different
    scheme (``http`` vs ``https``) is cross-origin even on the same
    host. We use the canonical (default-port-normalized,
    case-insensitive) form so cosmetic URL differences don't trick
    the comparison.
    """

    return _canonical_origin(from_url) != _canonical_origin(to_url)


# Header names to strip on a cross-origin redirect. Codex iter-4
# critical: aligned with the contract-layer ``_SENSITIVE_HEADER_NAMES``
# set in ``contracts/network.py``. Custom credential headers
# (``X-Api-Key`` / ``X-Auth-Token`` / ``X-Session-Token`` /
# ``X-CSRF-Token``) are credential-bearing in the project's threat
# model — letting them ride a cross-origin redirect leaks the
# token. Lowercased; the actual strip is case-insensitive.
_CROSS_ORIGIN_STRIP_HEADERS: Final[frozenset[str]] = frozenset(
    {
        "authorization",
        "proxy-authorization",
        "cookie",
        "x-api-key",
        "x-auth-token",
        "x-session-token",
        "x-csrf-token",
    }
)


def _strip_cross_origin_headers(headers: dict[str, str]) -> dict[str, str]:
    """Return a copy of ``headers`` with cross-origin-sensitive
    headers removed (case-insensitive)."""

    return {
        name: value
        for name, value in headers.items()
        if name.lower() not in _CROSS_ORIGIN_STRIP_HEADERS
    }


# Header names whose values must be redacted when stored on
# :class:`NetworkAttemptEvidence` (the contract validator enforces
# the redaction marker; this list mirrors what the contract treats
# as sensitive).
_REDACTED_EVIDENCE_HEADER_MARKER: Final[str] = "[REDACTED]"
_EVIDENCE_REDACT_HEADERS: Final[frozenset[str]] = frozenset(
    {
        "authorization",
        "cookie",
        "set-cookie",
        "proxy-authorization",
        "x-api-key",
        "x-auth-token",
        "x-session-token",
        "x-csrf-token",
    }
)


def _redact_headers_for_evidence(headers: dict[str, str]) -> dict[str, str]:
    """Return ``headers`` with credential-bearing values replaced
    by the ``[REDACTED]`` marker the contract validator expects."""

    out: dict[str, str] = {}
    for name, value in headers.items():
        if name.lower() in _EVIDENCE_REDACT_HEADERS:
            out[name] = _REDACTED_EVIDENCE_HEADER_MARKER
        else:
            out[name] = value
    return out


def _parse_retry_after(value: str | None) -> float | None:
    if not value:
        return None
    raw = value.strip()
    if raw.isdigit():
        return float(raw)
    try:
        when = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        return None
    if when.tzinfo is None:
        when = when.replace(tzinfo=UTC)
    delta = (when - datetime.now(UTC)).total_seconds()
    return max(delta, 0.0)


def _backoff_seconds(attempt: int, *, jitter: Callable[[], float]) -> float:
    base: float = min(2 ** (attempt - 1), 30.0)
    return base + float(jitter())


def _classify_transport(exc: httpx.HTTPError) -> NetworkFailureType:
    if isinstance(
        exc, httpx.ConnectTimeout | httpx.ReadTimeout | httpx.WriteTimeout | httpx.PoolTimeout
    ):
        return NetworkFailureType.NETWORK_TIMEOUT
    return NetworkFailureType.ADAPTER_FAILURE


class StdlibHttpSourceAdapter:
    def __init__(
        self,
        request: NetworkRequest,
        *,
        config: HttpClientConfig | None = None,
        transport: httpx.BaseTransport | None = None,
        sleep_fn: Callable[[float], None] = time.sleep,
        jitter_fn: Callable[[], float] | None = None,
    ) -> None:
        self.request = request
        self._config = config or _default_config_from_request(request)
        # Codex iter-2 important #5: ``extra_headers`` is a mutable
        # ``dict`` field on a frozen dataclass. A caller that
        # mutates the dict after passing it in would leak credentials
        # across adapter instances / executions. Snapshot now into
        # an internal frozen copy that ``execute`` re-uses; the
        # adapter never reads ``self._config.extra_headers``
        # directly after this.
        self._frozen_extra_headers: dict[str, str] = dict(self._config.extra_headers)
        # Codex iter-4 important: derive run scope from
        # ``request.run_ref`` when ``HttpClientConfig.run_ref`` is
        # not set. Hardcoded fixture default leaked cache + cookies
        # across runs when callers forgot to override.
        config_run_ref = self._config.run_ref
        self._run_ref: str = config_run_ref if config_run_ref is not None else self.request.run_ref
        # Production-mode robots gate: the default
        # ``HttpClientConfig.robots_port`` is ``NoopRobotsPort`` so
        # existing fixture tests keep passing. In production the
        # no-op would silently bypass robots enforcement, which the
        # cooperative-crawler charter (``docs/09:116``) forbids; raise
        # so an unwired production deployment fails closed instead of
        # quietly fetching robots-blocked URLs.
        if current_mode() == RuntimeMode.PRODUCTION and isinstance(
            self._config.robots_port, NoopRobotsPort
        ):
            raise ProductionRuntimeNotImplemented(
                backend="robots",
                gate="StdlibHttpSourceAdapter",
            )
        # Production-mode rate-limiter gate (design.md §4 Phase 1
        # step 1.3): same pattern as the robots gate. In production
        # the no-op would skip cooperative pacing entirely, so a
        # mis-configured deployment cannot silently hammer an origin
        # — fail closed instead.
        if current_mode() == RuntimeMode.PRODUCTION and isinstance(
            self._config.rate_limiter, NoopRateLimiter
        ):
            raise ProductionRuntimeNotImplemented(
                backend="rate_limiter",
                gate="StdlibHttpSourceAdapter",
            )
        self._sleep = sleep_fn
        self._jitter: Callable[[], float] = (
            jitter_fn if jitter_fn is not None else lambda: random.uniform(0, 1)
        )
        timeout = httpx.Timeout(
            connect=self._config.connect_timeout_s,
            read=self._config.read_timeout_s,
            write=self._config.read_timeout_s,
            pool=self._config.connect_timeout_s,
        )
        client_kwargs: dict[str, Any] = {
            "timeout": timeout,
            "follow_redirects": False,
            "headers": {"User-Agent": self._config.user_agent},
        }
        if transport is not None:
            client_kwargs["transport"] = transport
        self._client = httpx.Client(**client_kwargs)
        self._last_result: NetworkClientResult | None = None
        self._redirect_hops: list[RedirectHop] = []
        self._attempt_evidences: list[NetworkAttemptEvidence] = []
        # When a 304 short-circuit produces a synthesized response,
        # we stash the cached entry's ``body_artifact_ref`` here so
        # ``execute`` can re-use it instead of fabricating a fresh
        # artifact ref. ``None`` means the response was a live fetch
        # and a new ref should be computed (codex iter-1 important
        # #1: replay traceability requires the cached ref to flow
        # through to ``NetworkClientResult.artifact_refs``).
        self._cached_artifact_ref_for_response: str | None = None
        # Working copy of the outgoing extra headers for this fetch.
        # Reset at the start of each ``execute`` call from
        # ``self._config.extra_headers``; mutated by
        # ``_fetch_with_redirects`` on cross-origin redirect to strip
        # Authorization / Cookie / Proxy-Authorization for the next
        # hop.
        self._current_extra_headers: dict[str, str] = {}
        # Codex iter-2 important #3: when a cross-origin redirect
        # strips the caller's credentials, also suppress the cookie
        # jar's emission for the **next** request. Otherwise a
        # caller who set ``Cookie`` in ``extra_headers`` (intended
        # for origin A) sees that cookie stripped on the redirect
        # to origin B, but the jar's cookies for B replace it —
        # which is a different credential boundary the caller did
        # not authorize. Treat cross-origin as a credentials-reset
        # for the next hop; subsequent hops can re-establish.
        self._suppress_jar_cookies_for_next_request: bool = False
        # Counter for unique attempt IDs across retries / hops.
        self._attempt_counter: int = 0
        # Retry-After observed during the most recent ``_send_with_retry``.
        # Reset at the start of each per-permit attempt so a stale hint
        # from a previous hop does not bleed into the next bucket's
        # cooldown (the limiter applies cooldown per (origin, route,
        # adapter) bucket; hop-to-hop mixing would over-extend an
        # unrelated bucket).
        self._last_retry_after_seconds: float | None = None

    @property
    def last_result(self) -> NetworkClientResult | None:
        return self._last_result

    def execute(self, command: SourceAdapterCommand) -> SourceAdapterResult:
        policy_decision_refs = (
            command.policy_snapshot_ref.split(",")
            if "," in command.policy_snapshot_ref
            else self.request.policy_decision_refs
        )
        self._redirect_hops = []
        self._attempt_evidences = []
        self._cached_artifact_ref_for_response = None
        self._suppress_jar_cookies_for_next_request = False
        # Snapshot the extra-headers config for this fetch so a
        # cross-origin strip on this fetch does not mutate the
        # adapter's persistent state across calls. Read from the
        # frozen copy taken at __init__ (codex iter-2 important #5)
        # so a caller mutating their own ``HttpClientConfig.extra_headers``
        # dict mid-flight cannot affect us.
        self._current_extra_headers = dict(self._frozen_extra_headers)
        self._attempt_counter = 0
        response = self._fetch_with_redirects(
            self.request.url, policy_decision_refs=policy_decision_refs
        )
        body = response.read()
        try:
            content_type_header = response.headers.get("content-type", "")
        except AttributeError:
            content_type_header = ""
        content_type = (
            content_type_header.split(";", 1)[0]
            if content_type_header
            else "application/octet-stream"
        )

        body_text = body.decode("utf-8", errors="replace")
        final_url = str(response.url)
        digest = stable_hash({"url": final_url, "body": body_text})
        # Codex iter-1 important #1: when a 304 short-circuit served
        # the response, reuse the cached body's artifact_ref so
        # replay records point at the original artifact instead of
        # fabricating a fresh one each time. Live (non-cached)
        # responses keep fabricating a new ref.
        if self._cached_artifact_ref_for_response is not None:
            artifact_ref = self._cached_artifact_ref_for_response
        else:
            artifact_ref = f"artifact:{self.request.id}:raw-html:{digest[:12]}"
        response_contract = NetworkResponse(
            id=f"network-response:{self.request.id}",
            request_ref=self.request.id,
            status_code=int(response.status_code),
            final_url=final_url,
            headers_ref=f"headers:{self.request.id}:response",
            raw_artifact_ref=artifact_ref,
            content_digest=digest,
            content_type=content_type,
            body_size_bytes=len(body),
            redirect_hop_refs=[hop.id for hop in self._redirect_hops],
            timing_ref=f"timing:{self.request.id}:response",
        )
        self._last_result = NetworkClientResult(
            response=response_contract,
            redirect_hops=list(self._redirect_hops),
            body_text=body_text,
            artifact_refs=[artifact_ref],
            attempt_evidences=list(self._attempt_evidences),
        )
        return SourceAdapterResult(
            id=f"source-result:{command.command_envelope_id}",
            run_id="run:network-fixture",
            adapter_spec_id=command.adapter_spec.id,
            adapter_type=AdapterType.HTTP,
            result_type=SourceAdapterResultType.FETCH_RESULT,
            output_refs=[artifact_ref],
            policy_decision_refs=self.request.policy_decision_refs,
            replay_event_refs=[f"event:{command.command_envelope_id}:network_response_recorded"],
            idempotency_key=f"{command.adapter_spec.id}:{self.request.id}",
            status=AdapterResultStatus.SUCCEEDED,
        )

    def _fetch_with_redirects(self, url: str, *, policy_decision_refs: list[str]) -> httpx.Response:
        current_url = url
        # Initial URL robots check (design.md §4 Phase 1 step 1.2).
        advice = self._check_robots(current_url, policy_decision_refs=policy_decision_refs)
        for hop in range(self._config.max_redirects + 1):
            response = self._send_with_rate_limit(current_url, advice=advice)
            if not _is_redirect_status(response.status_code):
                return response
            location = response.headers.get("location")
            if not location:
                raise RedirectDeniedError("redirect missing Location header")
            next_url = urljoin(current_url, location)
            self._validate_redirect_target(from_url=current_url, to_url=next_url)
            # Phase 1 step 1.5: cross-redirect Authorization /
            # Cookie / Proxy-Authorization strip (RFC 7235 best
            # practice + cooperative-crawler hygiene). When the
            # redirect crosses origins, drop credential-bearing
            # headers from the working copy so they are not echoed
            # to the new origin. Same-origin redirects keep the
            # headers because the credential was scoped to that
            # origin by the caller.
            if _is_cross_origin(current_url, next_url):
                self._current_extra_headers = _strip_cross_origin_headers(
                    self._current_extra_headers
                )
                # Suppress jar cookies on the next request too —
                # codex iter-2 important #3.
                self._suppress_jar_cookies_for_next_request = True
            # Cross-redirect robots re-check: design.md §4 Phase 1
            # explicitly requires "enforce on initial URL **and** every
            # redirect target". The check runs on every hop, not only
            # on cross-origin hops, because path-based ``Disallow``
            # rules can refuse a same-host redirect target.
            advice = self._check_robots(next_url, policy_decision_refs=policy_decision_refs)
            self._redirect_hops.append(
                RedirectHop(
                    id=f"redirect-hop:{self.request.id}:{hop + 1}",
                    request_ref=self.request.id,
                    sequence=hop + 1,
                    from_url=current_url,
                    to_url=next_url,
                    status_code=int(response.status_code),
                    policy_decision_refs=list(policy_decision_refs),
                )
            )
            current_url = next_url
        raise RedirectDeniedError(f"redirect loop > max_redirects={self._config.max_redirects}")

    def _send_with_rate_limit(
        self,
        url: str,
        *,
        advice: RobotsAdvice,
    ) -> httpx.Response:
        """Acquire a rate-limit permit, send + retry, and report outcome.

        The permit is scoped to one logical HTTP attempt (which may
        retry internally on 429 / 5xx via :meth:`_send_with_retry`).
        Floor inputs come from the live :class:`RobotsAdvice` so
        ``Crawl-delay`` / ``Request-rate`` flow into the AIMD floor
        for the bucket. AIMD outcomes:

        * Successful (non-retryable, returned by ``_send_with_retry``)
          → ``report_success`` → drives additive-increase phase.
        * :class:`RetryExhaustedError` after a 429 retry burst →
          ``report_throttled(retry_after_seconds=…)`` → multiplicative
          decrease + cooldown that honors the server's Retry-After
          hint when present (design.md §4 Phase 1: floor is the
          strictest of ``Retry-After`` / ``Crawl-delay`` /
          ``Request-rate``; the cooldown extension preserves that
          contract for the *next* caller of the bucket).
        * :class:`RateLimitProhibited` (raised by the limiter when
          the floor signals ``Request-rate: 0/N`` → infinite
          interval) → translate to :class:`RobotsBlockedError` so the
          cooperative-crawler refusal path is uniform with what
          :meth:`_check_robots` raises for explicit ``Disallow``
          rules.
        * Other failures (network / SSRF / etc.) → no report so
          AIMD state is not biased by infrastructure issues.
        """

        floor = RateLimitFloor(
            crawl_delay_seconds=advice.crawl_delay,
            request_rate=advice.request_rate,
        )
        # Reset the per-attempt Retry-After cache so a hint observed
        # on a previous hop does not extend the cooldown for the
        # *current* bucket (each acquire is its own logical attempt).
        self._last_retry_after_seconds = None
        # ``InMemoryAimdLimiter.acquire`` is a ``@contextmanager``
        # whose generator body runs on ``__enter__`` — so
        # :class:`RateLimitProhibited` (raised inside that body when
        # the floor is infinite, i.e. ``Request-rate: 0/N``) surfaces
        # at the ``with`` statement, not at the bare ``acquire(...)``
        # call. The translation to :class:`RobotsBlockedError` must
        # therefore wrap the ``with`` block, otherwise the exception
        # escapes uncaught and breaks the cooperative-refusal contract.
        try:
            with self._config.rate_limiter.acquire(
                origin=_origin(url),
                route_class=self._config.route_class,
                adapter_type=AdapterType.HTTP,
                floor=floor,
            ) as permit:
                try:
                    response = self._send_with_retry(url)
                except RetryExhaustedError:
                    self._config.rate_limiter.report_throttled(
                        permit=permit,
                        retry_after_seconds=self._last_retry_after_seconds,
                    )
                    raise
                self._config.rate_limiter.report_success(permit=permit)
                return response
        except RateLimitProhibited as exc:
            raise RobotsBlockedError(
                f"{url}: rate-limiter refused (full prohibition): {exc}"
            ) from exc

    def _check_robots(self, url: str, *, policy_decision_refs: list[str]) -> RobotsAdvice:
        advice = self._config.robots_port.evaluate(url, user_agent=self._config.user_agent)
        if advice.is_allowed:
            return advice
        reason = advice.disallow_reason or "robots.txt disallowed"
        # Embed the active policy decision refs in the error detail so
        # replay / audit diagnostics keep traceability for blocked
        # decisions (codex iter-4 minor: previously
        # ``policy_decision_refs`` was carried by the redirect path
        # but ignored when robots blocked the URL).
        if policy_decision_refs:
            policy_part = ",".join(policy_decision_refs)
            detail = f"{url}: {reason} (policy_decision_refs={policy_part})"
        else:
            detail = f"{url}: {reason}"
        raise RobotsBlockedError(detail)

    def _send_with_retry(self, url: str) -> httpx.Response:
        last_response: httpx.Response | None = None
        last_failure: NetworkFailureType = NetworkFailureType.NETWORK_TIMEOUT
        for attempt in range(1, self._config.max_attempts + 1):
            request_headers = self._build_request_headers(url)
            request_started_monotonic = time.monotonic()
            try:
                response = self._client.request(
                    self.request.method,
                    url,
                    headers=request_headers,
                )
            except httpx.HTTPError as exc:
                failure = _classify_transport(exc)
                last_failure = failure
                self._record_attempt_evidence(
                    url=url,
                    request_headers=request_headers,
                    response=None,
                    failure_class=failure.value,
                    started_monotonic=request_started_monotonic,
                )
                if (
                    failure is not NetworkFailureType.NETWORK_TIMEOUT
                    or attempt >= self._config.max_attempts
                ):
                    raise classify_network_failure(failure, f"{type(exc).__name__}: {exc}") from exc
                self._sleep(_backoff_seconds(attempt, jitter=self._jitter))
                continue

            self._record_attempt_evidence(
                url=url,
                request_headers=request_headers,
                response=response,
                failure_class=None,
                started_monotonic=request_started_monotonic,
            )
            self._absorb_set_cookies(url=url, response=response)

            if response.status_code in _RETRYABLE_STATUSES:
                last_response = response
                # Track the last observed Retry-After so
                # ``_send_with_rate_limit`` can pass it into
                # ``report_throttled`` on retry exhaustion. Only
                # 429 + 503 carry meaningful Retry-After per RFC
                # 7231; we record any retryable status though,
                # because the server may include the header on
                # 502 / 504 too.
                retry_after_hint = _parse_retry_after(response.headers.get(_RETRY_AFTER_HEADER))
                if retry_after_hint is not None:
                    self._last_retry_after_seconds = retry_after_hint
                if attempt >= self._config.max_attempts:
                    break
                wait = retry_after_hint
                if wait is None:
                    wait = _backoff_seconds(attempt, jitter=self._jitter)
                wait = min(wait, self._config.retry_after_cap_s)
                response.read()
                self._sleep(wait)
                continue

            # 304 Not Modified: synthesize a 200 response from the
            # cached body so the rest of the pipeline doesn't have
            # to special-case 304. This implements the design.md §4
            # Phase 1 acceptance ("304 short-circuits to cached
            # body") at the adapter boundary.
            if response.status_code == 304:
                cached = self._config.conditional_cache.get(run_ref=self._run_ref, url=url)
                if cached is not None:
                    response.read()  # drain the empty 304 body
                    self._cached_artifact_ref_for_response = cached.body_artifact_ref
                    return self._synthesize_from_cached(cached_url=url, cached=cached)
                # Server responded 304 but we have nothing cached
                # — fail closed: treat as a network adapter error
                # since we cannot produce a usable body.
                raise AdapterFailureError(f"server returned 304 but no cached body for url={url!r}")

            # 2xx: store ETag / Last-Modified for next time.
            if 200 <= response.status_code < 300:
                self._maybe_cache_conditional(url=url, response=response)

            return response

        if last_response is not None:
            raise RetryExhaustedError(
                f"max_attempts={self._config.max_attempts} last_status={last_response.status_code}"
            )
        raise classify_network_failure(last_failure, f"max_attempts={self._config.max_attempts}")

    def _build_request_headers(self, url: str) -> dict[str, str]:
        """Combine UA + extra_headers + cookies + conditional-fetch
        hints into the per-attempt outgoing header set.

        Order:
        1. Base ``User-Agent`` (from config)
        2. ``self._current_extra_headers`` — Authorization etc.,
           already stripped by ``_fetch_with_redirects`` if the
           previous hop crossed origins.
        3. ``Cookie`` from the cookie jar (per-run / per-origin /
           per-path scope).
        4. ``If-None-Match`` / ``If-Modified-Since`` from the
           conditional cache.
        """

        headers: dict[str, str] = {"User-Agent": self._config.user_agent}
        for name, value in self._current_extra_headers.items():
            headers[name] = value
        if self._suppress_jar_cookies_for_next_request:
            # Cross-origin redirect just stripped credentials. Don't
            # re-introduce them via jar cookies for the redirect
            # target on this very next hop. Reset the flag so
            # subsequent hops use the jar normally (codex iter-2
            # important #3).
            self._suppress_jar_cookies_for_next_request = False
        else:
            cookies = self._config.cookie_jar.cookies_for(run_ref=self._run_ref, url=url)
            if cookies:
                headers["Cookie"] = "; ".join(f"{n}={v}" for n, v in cookies.items())
        cached = self._config.conditional_cache.get(run_ref=self._run_ref, url=url)
        if cached is not None:
            if cached.etag:
                headers["If-None-Match"] = cached.etag
            if cached.last_modified and "If-None-Match" not in headers:
                headers["If-Modified-Since"] = cached.last_modified
        return headers

    def _record_attempt_evidence(
        self,
        *,
        url: str,
        request_headers: dict[str, str],
        response: httpx.Response | None,
        failure_class: str | None,
        started_monotonic: float,
    ) -> None:
        elapsed_ms = max(0, int((time.monotonic() - started_monotonic) * 1000))
        self._attempt_counter += 1
        attempt_id = f"attempt-evidence:{self.request.id}:{self._attempt_counter}"
        response_status: int | None = None
        response_headers_redacted: dict[str, str] | None = None
        if response is not None:
            response_status = int(response.status_code)
            try:
                resp_headers_dict = dict(response.headers)
            except Exception:  # noqa: BLE001
                resp_headers_dict = {}
            response_headers_redacted = _redact_headers_for_evidence(resp_headers_dict)
        evidence = NetworkAttemptEvidence(
            id=attempt_id,
            run_ref=self._run_ref,
            request_ref=self.request.id,
            attempt_number=self._attempt_counter,
            request_method=self.request.method,
            request_url=url,
            request_headers_redacted=_redact_headers_for_evidence(request_headers),
            response_status=response_status,
            response_headers_redacted=response_headers_redacted,
            elapsed_ms=elapsed_ms,
            failure_class=failure_class,
            redirect_hop_count=len(self._redirect_hops),
        )
        self._attempt_evidences.append(evidence)

    def _absorb_set_cookies(self, *, url: str, response: httpx.Response) -> None:
        """Walk every ``Set-Cookie`` response header and store it.

        ``httpx.Headers.get_list`` returns each ``Set-Cookie`` as a
        separate value (multi-valued header). The cookie jar parses
        each one; malformed values log + skip rather than raise.
        """

        try:
            set_cookies = response.headers.get_list("set-cookie")
        except AttributeError:
            set_cookies = []
        for raw in set_cookies:
            self._config.cookie_jar.accept_set_cookie(
                run_ref=self._run_ref,
                url=url,
                set_cookie_value=raw,
            )

    def _maybe_cache_conditional(self, *, url: str, response: httpx.Response) -> None:
        etag = response.headers.get("etag")
        last_modified = response.headers.get("last-modified")
        if not etag and not last_modified:
            return
        # Read body before caching — httpx Response body is
        # streamed and ``response.content`` materializes it.
        body_bytes = response.content
        body_text = body_bytes.decode("utf-8", errors="replace")
        # Codex iter-2 important #2: store the SAME artifact_ref
        # shape that ``execute()`` will emit for this body so a
        # later 304 short-circuit can reuse it. Earlier we stored
        # ``cached:`` while ``execute()`` emitted ``raw-html:``,
        # creating a ref that never appeared in any prior result.
        # ``execute()`` keys the digest on
        # ``{"url": final_url, "body": body_text}`` — we mirror that
        # so the digest matches.
        digest = stable_hash({"url": url, "body": body_text})
        body_artifact_ref = f"artifact:{self.request.id}:raw-html:{digest[:12]}"
        content_type_header = response.headers.get("content-type", "")
        content_type = (
            content_type_header.split(";", 1)[0]
            if content_type_header
            else "application/octet-stream"
        )
        self._config.conditional_cache.put(
            run_ref=self._run_ref,
            url=url,
            entry=CachedConditional(
                etag=etag,
                last_modified=last_modified,
                body_bytes=body_bytes,
                body_artifact_ref=body_artifact_ref,
                content_type=content_type,
                status_code=int(response.status_code),
            ),
        )

    def _synthesize_from_cached(
        self, *, cached_url: str, cached: CachedConditional
    ) -> httpx.Response:
        """Build an ``httpx.Response`` from a cached entry (304 short-circuit).

        The caller treats this exactly like a 2xx response from the
        wire — the rest of the pipeline (DOM artifact, redirect-hop
        bookkeeping, evidence) reads body / status / headers off
        this synthesized object the same way it would for a live
        response.

        ``httpx.Response.read()`` requires an attached ``request``;
        we synthesize a matching ``httpx.Request`` so the caller can
        ``response.read()`` without `RuntimeError`.
        """

        request = httpx.Request(self.request.method, cached_url)
        return httpx.Response(
            status_code=cached.status_code,
            headers={"content-type": cached.content_type},
            content=cached.body_bytes,
            request=request,
        )

    def _validate_redirect_target(self, *, from_url: str, to_url: str) -> None:
        from_scheme = urlparse(from_url).scheme
        to_parsed = urlparse(to_url)
        if to_parsed.scheme not in {"http", "https"}:
            raise RedirectDeniedError(f"unsupported redirect scheme: {to_parsed.scheme!r}")
        if from_scheme == "https" and to_parsed.scheme == "http":
            raise RedirectDeniedError("protocol_downgrade_https_to_http")
        if self._config.egress_allowlist:
            target_origin = _origin(to_url)
            if target_origin not in self._config.egress_allowlist:
                raise EgressDeniedError(f"redirect off allowlist: {target_origin}")
        if not self._config.allow_private_network and _is_private_network_url(to_url):
            raise PrivateNetworkDeniedError(f"redirect to private host: {to_parsed.hostname}")


def _is_redirect_status(status: int) -> bool:
    return status in {301, 302, 303, 307, 308}


def _default_config_from_request(request: NetworkRequest) -> HttpClientConfig:
    """Build a default HttpClientConfig from the legacy
    ``request.timeout_ms`` value so the 13 single-arg call sites
    continue to honor the timeout the request was constructed with."""
    timeout_s = max(min(request.timeout_ms / 1000.0, 60.0), 1.0)
    return HttpClientConfig(read_timeout_s=timeout_s)
