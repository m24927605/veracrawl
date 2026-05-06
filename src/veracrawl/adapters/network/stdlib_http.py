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
    SourceAdapterResultType,
)
from veracrawl.contracts.errors import FatalError, PolicyViolation, RetryableError
from veracrawl.contracts.network import NetworkRequest, NetworkResponse, RedirectHop
from veracrawl.contracts.source_adapter import SourceAdapterCommand, SourceAdapterResult
from veracrawl.ports.network import NetworkClientResult

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


_NETWORK_FAILURE_TYPE_TO_CLASS: dict[NetworkFailureType, type[NetworkAdapterError]] = {
    NetworkFailureType.NETWORK_TIMEOUT: NetworkTimeoutError,
    NetworkFailureType.RETRY_EXHAUSTED: RetryExhaustedError,
    NetworkFailureType.REDIRECT_DENIED: RedirectDeniedError,
    NetworkFailureType.EGRESS_DENIED: EgressDeniedError,
    NetworkFailureType.PRIVATE_NETWORK_DENIED: PrivateNetworkDeniedError,
    NetworkFailureType.ADAPTER_FAILURE: AdapterFailureError,
}


def classify_network_failure(
    failure_type: NetworkFailureType, detail: str
) -> NetworkAdapterError:
    """Pick the marker-bearing subclass for ``failure_type``.

    Falls back to the generic :class:`NetworkAdapterError` for failure
    types that don't have a dedicated subclass yet (e.g.
    SIZE_BUDGET_EXCEEDED, ROBOTS_BLOCKED, RATE_BUDGET_EXCEEDED). Those
    subclasses can be added incrementally without disturbing existing
    callers — the helper continues to return a base
    ``NetworkAdapterError`` for unmapped values.
    """
    cls = _NETWORK_FAILURE_TYPE_TO_CLASS.get(failure_type)
    if cls is None:
        return NetworkAdapterError(failure_type, detail)
    # Specific subclasses take only ``detail`` (failure_type is implied
    # by the class). The dispatch table is keyed so cls is one of the
    # six known subclasses; mypy's view is the broader base type, so
    # the call-arg / arg-type signatures of the parent are reported
    # despite this being correct against every entry in the dict.
    return cls(detail)  # type: ignore[arg-type,call-arg]


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
        )
        return SourceAdapterResult(
            id=f"source-result:{command.command_envelope_id}",
            run_id="run:network-fixture",
            adapter_spec_id=command.adapter_spec.id,
            adapter_type=AdapterType.HTTP,
            result_type=SourceAdapterResultType.FETCH_RESULT,
            output_refs=[artifact_ref],
            policy_decision_refs=self.request.policy_decision_refs,
            replay_event_refs=[
                f"event:{command.command_envelope_id}:network_response_recorded"
            ],
            idempotency_key=f"{command.adapter_spec.id}:{self.request.id}",
            status=AdapterResultStatus.SUCCEEDED,
        )

    def _fetch_with_redirects(
        self, url: str, *, policy_decision_refs: list[str]
    ) -> httpx.Response:
        current_url = url
        for hop in range(self._config.max_redirects + 1):
            response = self._send_with_retry(current_url)
            if not _is_redirect_status(response.status_code):
                return response
            location = response.headers.get("location")
            if not location:
                raise RedirectDeniedError("redirect missing Location header")
            next_url = urljoin(current_url, location)
            self._validate_redirect_target(from_url=current_url, to_url=next_url)
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
        raise RedirectDeniedError(
            f"redirect loop > max_redirects={self._config.max_redirects}"
        )

    def _send_with_retry(self, url: str) -> httpx.Response:
        last_response: httpx.Response | None = None
        last_failure: NetworkFailureType = NetworkFailureType.NETWORK_TIMEOUT
        for attempt in range(1, self._config.max_attempts + 1):
            try:
                response = self._client.request(self.request.method, url)
            except httpx.HTTPError as exc:
                failure = _classify_transport(exc)
                last_failure = failure
                if (
                    failure is not NetworkFailureType.NETWORK_TIMEOUT
                    or attempt >= self._config.max_attempts
                ):
                    raise classify_network_failure(
                        failure, f"{type(exc).__name__}: {exc}"
                    ) from exc
                self._sleep(_backoff_seconds(attempt, jitter=self._jitter))
                continue

            if response.status_code in _RETRYABLE_STATUSES:
                last_response = response
                if attempt >= self._config.max_attempts:
                    break
                wait = _parse_retry_after(response.headers.get(_RETRY_AFTER_HEADER))
                if wait is None:
                    wait = _backoff_seconds(attempt, jitter=self._jitter)
                wait = min(wait, self._config.retry_after_cap_s)
                response.read()
                self._sleep(wait)
                continue

            return response

        if last_response is not None:
            raise RetryExhaustedError(
                f"max_attempts={self._config.max_attempts} "
                f"last_status={last_response.status_code}"
            )
        raise classify_network_failure(
            last_failure, f"max_attempts={self._config.max_attempts}"
        )

    def _validate_redirect_target(self, *, from_url: str, to_url: str) -> None:
        from_scheme = urlparse(from_url).scheme
        to_parsed = urlparse(to_url)
        if to_parsed.scheme not in {"http", "https"}:
            raise RedirectDeniedError(
                f"unsupported redirect scheme: {to_parsed.scheme!r}"
            )
        if from_scheme == "https" and to_parsed.scheme == "http":
            raise RedirectDeniedError("protocol_downgrade_https_to_http")
        if self._config.egress_allowlist:
            target_origin = _origin(to_url)
            if target_origin not in self._config.egress_allowlist:
                raise EgressDeniedError(f"redirect off allowlist: {target_origin}")
        if not self._config.allow_private_network and _is_private_network_url(to_url):
            raise PrivateNetworkDeniedError(
                f"redirect to private host: {to_parsed.hostname}"
            )


def _is_redirect_status(status: int) -> bool:
    return status in {301, 302, 303, 307, 308}


def _default_config_from_request(request: NetworkRequest) -> HttpClientConfig:
    """Build a default HttpClientConfig from the legacy
    ``request.timeout_ms`` value so the 13 single-arg call sites
    continue to honor the timeout the request was constructed with."""
    timeout_s = max(min(request.timeout_ms / 1000.0, 60.0), 1.0)
    return HttpClientConfig(read_timeout_s=timeout_s)
