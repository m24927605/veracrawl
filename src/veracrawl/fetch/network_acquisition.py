"""Network acquisition runtime."""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
from urllib.parse import urlparse

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import AdapterType, CompletenessResult, NetworkFailureType
from veracrawl.contracts.network import NetworkAcquisitionReport, NetworkRequest
from veracrawl.contracts.source_adapter import SourceAdapterCommand
from veracrawl.fetch.acquisition import execute_source_acquisition, source_adapter_spec
from veracrawl.ports.network import NetworkClientResult, NetworkSourceAdapterPort


@dataclass(frozen=True)
class NetworkBrowserAcquisitionOutcome:
    report: NetworkAcquisitionReport
    network_result: NetworkClientResult | None = None


def url_origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def is_private_network_url(url: str) -> bool:
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


def build_network_request(
    *,
    fixture_id: str,
    target_url: str,
    policy_decision_refs: list[Ref],
    size_budget_bytes: int,
    timeout_ms: int,
) -> NetworkRequest:
    return NetworkRequest(
        id=f"network-request:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        source_ref=target_url,
        url=target_url,
        method="GET",
        headers_ref=f"headers:{fixture_id}:request",
        policy_decision_refs=policy_decision_refs,
        egress_policy_ref=f"policy:{fixture_id}:egress",
        private_network_policy_ref=f"policy:{fixture_id}:private-network",
        robots_policy_ref=f"policy:{fixture_id}:robots",
        rate_budget_ref=f"budget:{fixture_id}:rate",
        size_budget_bytes=size_budget_bytes,
        timeout_ms=timeout_ms,
        idempotency_key=f"network:{fixture_id}:{target_url}",
    )


def network_policy_failure(
    request: NetworkRequest,
    *,
    scenario: str,
    egress_allowlist: list[str],
    allow_private_network: bool,
    rate_budget_remaining: int = 1,
) -> NetworkFailureType | None:
    if url_origin(request.url) not in egress_allowlist:
        return NetworkFailureType.EGRESS_DENIED
    if is_private_network_url(request.url) and not allow_private_network:
        return NetworkFailureType.PRIVATE_NETWORK_DENIED
    if scenario == "robots-blocked":
        return NetworkFailureType.ROBOTS_BLOCKED
    if rate_budget_remaining < 1 or scenario == "rate-budget":
        return NetworkFailureType.RATE_BUDGET_EXCEEDED
    if scenario == "redirect-denied":
        return NetworkFailureType.REDIRECT_DENIED
    if scenario == "timeout":
        return NetworkFailureType.NETWORK_TIMEOUT
    return None


def _failure_report(
    *,
    fixture_id: str,
    request: NetworkRequest | None,
    failure_type: NetworkFailureType,
    policy_decision_refs: list[Ref],
    browser_step_ref: Ref | None = None,
) -> NetworkBrowserAcquisitionOutcome:
    completion = (
        CompletenessResult.NEEDS_REVIEW
        if failure_type == NetworkFailureType.RATE_BUDGET_EXCEEDED
        else CompletenessResult.FAIL
    )
    report = NetworkAcquisitionReport(
        id=f"network-acquisition:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        network_request_ref=request.id if request else None,
        browser_step_ref=browser_step_ref,
        policy_decision_refs=policy_decision_refs,
        failure_report_refs=[f"network-failure:{fixture_id}:{failure_type.value}"],
        missing_ref_fields=[failure_type.value],
        operator_status=failure_type.value,
        completion_result=completion,
    )
    return NetworkBrowserAcquisitionOutcome(report=report)


def _source_command_for_network(request: NetworkRequest) -> SourceAdapterCommand:
    return SourceAdapterCommand(
        command_envelope_id=f"cmd:{request.id}:source",
        adapter_spec=source_adapter_spec(AdapterType.HTTP),
        source_ref=request.url,
        policy_snapshot_ref=",".join(request.policy_decision_refs),
        deterministic_clock_ref=f"clock:{request.id}:fixed",
        randomness_seed_ref=f"random:{request.id}:fixed",
    )


def execute_http_network_acquisition(
    *,
    fixture_id: str,
    scenario: str,
    target_url: str,
    adapter: NetworkSourceAdapterPort,
    egress_allowlist: list[str],
    allow_private_network: bool,
    size_budget_bytes: int = 8192,
    timeout_ms: int = 1000,
) -> NetworkBrowserAcquisitionOutcome:
    policy_refs = [f"policy:{fixture_id}:network"]
    request = build_network_request(
        fixture_id=fixture_id,
        target_url=target_url,
        policy_decision_refs=policy_refs,
        size_budget_bytes=size_budget_bytes,
        timeout_ms=timeout_ms,
    )
    failure = network_policy_failure(
        request,
        scenario=scenario,
        egress_allowlist=egress_allowlist,
        allow_private_network=allow_private_network,
    )
    if failure is not None:
        return _failure_report(
            fixture_id=fixture_id,
            request=request,
            failure_type=failure,
            policy_decision_refs=policy_refs,
        )

    if scenario == "size-budget":
        try:
            adapter.execute(_source_command_for_network(request))
        except ValueError:
            return _failure_report(
                fixture_id=fixture_id,
                request=request,
                failure_type=NetworkFailureType.ADAPTER_FAILURE,
                policy_decision_refs=policy_refs,
            )
        result = adapter.last_result
        if result and result.response.body_size_bytes > request.size_budget_bytes:
            return _failure_report(
                fixture_id=fixture_id,
                request=request,
                failure_type=NetworkFailureType.SIZE_BUDGET_EXCEEDED,
                policy_decision_refs=policy_refs,
            )

    source_outcome = execute_source_acquisition(
        fixture_id=fixture_id,
        adapter_type=AdapterType.HTTP,
        scenario="network-success",
        adapter=adapter,
    )
    network_result = adapter.last_result
    if network_result is None:
        return _failure_report(
            fixture_id=fixture_id,
            request=request,
            failure_type=NetworkFailureType.MISSING_NETWORK_ARTIFACT,
            policy_decision_refs=policy_refs,
        )
    report = NetworkAcquisitionReport(
        id=f"network-acquisition:{fixture_id}",
        run_ref=f"run:{fixture_id}",
        network_request_ref=request.id,
        network_response_ref=network_result.response.id,
        redirect_hop_refs=[hop.id for hop in network_result.redirect_hops],
        source_acquisition_report_ref=source_outcome.report.id,
        artifact_refs=sorted(
            set(source_outcome.report.artifact_refs + network_result.artifact_refs)
        ),
        policy_decision_refs=sorted(set(policy_refs + source_outcome.report.policy_decision_refs)),
        command_record_refs=source_outcome.report.command_record_refs,
        event_cursor_refs=source_outcome.report.event_cursor_refs,
        outbox_refs=source_outcome.report.outbox_refs,
        recovery_report_refs=source_outcome.report.recovery_report_refs,
        operator_status="network_acquired",
        completion_result=CompletenessResult.PASS,
    )
    return NetworkBrowserAcquisitionOutcome(report=report, network_result=network_result)
