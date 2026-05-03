"""Real-world benchmark corpus runtime."""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from html.parser import HTMLParser
from urllib import robotparser

from veracrawl.contracts.common import Ref
from veracrawl.contracts.enums import (
    CompletenessResult,
    RealWorldBenchmarkFailureType,
)
from veracrawl.contracts.network import NetworkResponse
from veracrawl.contracts.real_world_benchmark import (
    RealWorldBenchmarkCorpusManifest,
    RealWorldBenchmarkRunReport,
    RealWorldBenchmarkSiteObservation,
    RealWorldBenchmarkSiteSpec,
)
from veracrawl.control.production_persistence import ProductionPersistenceStore
from veracrawl.control.runtime import create_runtime_command
from veracrawl.fetch.live_http import (
    LiveHttpAcquisitionRuntimeResult,
    execute_live_http_acquisition,
)
from veracrawl.fetch.network_acquisition import is_private_network_url, url_origin
from veracrawl.ports.network import NetworkSourceAdapterPort


@dataclass(frozen=True)
class RobotsFetchResult:
    status_code: int
    body_text: str


@dataclass(frozen=True)
class RealWorldBenchmarkResult:
    report: RealWorldBenchmarkRunReport
    observations: list[RealWorldBenchmarkSiteObservation]
    live_http_results: list[LiveHttpAcquisitionRuntimeResult]


NetworkAdapterFactory = Callable[[str, RealWorldBenchmarkSiteSpec], NetworkSourceAdapterPort]
RobotsFetcher = Callable[[RealWorldBenchmarkSiteSpec], RobotsFetchResult]


class _TitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._in_title = False
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.lower() == "title":
            self._in_title = True

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() == "title":
            self._in_title = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._parts.append(data)

    @property
    def title(self) -> str:
        return " ".join(" ".join(self._parts).split())


def run_real_world_benchmark_corpus(
    *,
    manifest: RealWorldBenchmarkCorpusManifest,
    profile: str,
    store: ProductionPersistenceStore,
    adapter_factory: NetworkAdapterFactory,
    robots_fetcher: RobotsFetcher,
) -> RealWorldBenchmarkResult:
    if profile not in manifest.profile_refs:
        raise ValueError(f"real-world benchmark corpus {manifest.id} does not support {profile}")

    observations: list[RealWorldBenchmarkSiteObservation] = []
    live_results: list[LiveHttpAcquisitionRuntimeResult] = []
    allowed_origins = set(manifest.allowed_origin_refs)

    for site in manifest.site_specs:
        site_run_ref = f"{manifest.id}:{site.id}"
        if site.allowed_origin not in allowed_origins or url_origin(site.target_url) not in (
            allowed_origins
        ):
            observations.append(
                _failure_observation(
                    manifest_id=manifest.id,
                    site=site,
                    failure=RealWorldBenchmarkFailureType.SCOPE_DENIED,
                    missing_field="allowed_origin",
                    diagnostics=[f"{site.target_url} is outside the corpus allowlist"],
                )
            )
            continue
        if is_private_network_url(site.target_url) or is_private_network_url(site.robots_url):
            observations.append(
                _failure_observation(
                    manifest_id=manifest.id,
                    site=site,
                    failure=RealWorldBenchmarkFailureType.PRIVATE_NETWORK_DENIED,
                    missing_field="target_url",
                    diagnostics=["real-world benchmark denied private-network target"],
                )
            )
            continue

        robots = _check_robots(site=site, robots_fetcher=robots_fetcher)
        if robots.failure_type is not None:
            observations.append(
                _failure_observation(
                    manifest_id=manifest.id,
                    site=site,
                    failure=robots.failure_type,
                    missing_field=robots.missing_field,
                    diagnostics=robots.diagnostics or [],
                    robots_policy_ref=robots.policy_ref,
                )
            )
            continue

        live_result = execute_live_http_acquisition(
            fixture_id=site_run_ref,
            scenario="success",
            target_url=site.target_url,
            store=store,
            adapter=adapter_factory(site_run_ref, site),
            profile=profile,
            egress_allowlist=[site.allowed_origin],
            allow_private_network=False,
            size_budget_bytes=site.size_budget_bytes,
            timeout_ms=site.timeout_ms,
        )
        live_results.append(live_result)
        observation = _observation_from_live_result(
            manifest_id=manifest.id,
            site=site,
            robots_policy_ref=robots.policy_ref,
            live_result=live_result,
        )
        store.save_canonical_model(
            "real_world_benchmark_site_observations",
            observation.id,
            observation,
        )
        observation = _record_observation_event(
            manifest_id=manifest.id,
            site=site,
            observation=observation,
            live_result=live_result,
            store=store,
        )
        observations.append(observation)

    report = _build_run_report(manifest=manifest, observations=observations)
    store.save_canonical_model("real_world_benchmark_run_reports", report.id, report)
    if live_results:
        _record_run_report_event(
            manifest=manifest,
            report=report,
            live_result=live_results[0],
            store=store,
        )
        report = _build_run_report(manifest=manifest, observations=observations, store=store)
        store.save_canonical_model("real_world_benchmark_run_reports", report.id, report)
    return RealWorldBenchmarkResult(
        report=report,
        observations=observations,
        live_http_results=live_results,
    )


@dataclass(frozen=True)
class _RobotsCheck:
    policy_ref: Ref
    failure_type: RealWorldBenchmarkFailureType | None = None
    missing_field: str = ""
    diagnostics: list[str] | None = None


def _check_robots(
    *,
    site: RealWorldBenchmarkSiteSpec,
    robots_fetcher: RobotsFetcher,
) -> _RobotsCheck:
    policy_ref = f"policy:{site.id}:robots"
    try:
        robots = robots_fetcher(site)
    except OSError as exc:
        return _RobotsCheck(
            policy_ref=policy_ref,
            failure_type=RealWorldBenchmarkFailureType.NETWORK_UNAVAILABLE,
            missing_field="robots_url",
            diagnostics=[f"robots preflight failed: {exc}"],
        )
    if robots.status_code not in site.allowed_robots_status_codes:
        return _RobotsCheck(
            policy_ref=f"{policy_ref}:{robots.status_code}",
            failure_type=RealWorldBenchmarkFailureType.ROBOTS_DENIED,
            missing_field="robots_status_code",
            diagnostics=[f"robots status {robots.status_code} is not allowed"],
        )
    if robots.status_code == 200:
        parser = robotparser.RobotFileParser()
        parser.set_url(site.robots_url)
        parser.parse(robots.body_text.splitlines())
        if not parser.can_fetch("VeraCrawl-real-benchmark/1", site.target_url):
            return _RobotsCheck(
                policy_ref=f"{policy_ref}:deny",
                failure_type=RealWorldBenchmarkFailureType.ROBOTS_DENIED,
                missing_field="robots_policy",
                diagnostics=[f"robots policy disallows {site.target_url}"],
            )
    return _RobotsCheck(policy_ref=f"{policy_ref}:allow:{robots.status_code}")


def _observation_from_live_result(
    *,
    manifest_id: str,
    site: RealWorldBenchmarkSiteSpec,
    robots_policy_ref: Ref,
    live_result: LiveHttpAcquisitionRuntimeResult,
) -> RealWorldBenchmarkSiteObservation:
    report = live_result.report
    network = live_result.network_outcome.network_result if live_result.network_outcome else None
    if report.completion_result != CompletenessResult.PASS or network is None:
        return _failure_observation(
            manifest_id=manifest_id,
            site=site,
            failure=RealWorldBenchmarkFailureType.LIVE_HTTP_FAILED,
            missing_field=report.operator_status,
            diagnostics=report.diagnostics or [report.operator_status],
            robots_policy_ref=robots_policy_ref,
            live_http_report_ref=report.id,
            network_response_ref=report.network_response_ref,
            artifact_refs=report.artifact_refs,
            policy_decision_refs=report.policy_decision_refs,
            command_record_refs=report.command_record_refs,
            event_cursor_refs=report.event_cursor_refs,
            outbox_refs=report.outbox_refs,
        )

    missing_refs = _missing_live_evidence_refs(report)
    if missing_refs:
        return _failure_observation(
            manifest_id=manifest_id,
            site=site,
            failure=RealWorldBenchmarkFailureType.MISSING_EVIDENCE_REFS,
            missing_field=",".join(missing_refs),
            diagnostics=[f"live HTTP report missing refs: {', '.join(missing_refs)}"],
            robots_policy_ref=robots_policy_ref,
            live_http_report_ref=report.id,
            network_response_ref=report.network_response_ref,
            artifact_refs=report.artifact_refs,
            policy_decision_refs=report.policy_decision_refs,
            command_record_refs=report.command_record_refs,
            event_cursor_refs=report.event_cursor_refs,
            outbox_refs=report.outbox_refs,
        )

    matched, mismatches = _evaluate_observations(site, network.body_text, network.response)
    if mismatches:
        return _failure_observation(
            manifest_id=manifest_id,
            site=site,
            failure=RealWorldBenchmarkFailureType.OBSERVATION_MISMATCH,
            missing_field="observation_oracle",
            diagnostics=mismatches,
            robots_policy_ref=robots_policy_ref,
            live_http_report_ref=report.id,
            network_response_ref=report.network_response_ref,
            artifact_refs=report.artifact_refs,
            policy_decision_refs=report.policy_decision_refs,
            command_record_refs=report.command_record_refs,
            event_cursor_refs=report.event_cursor_refs,
            outbox_refs=report.outbox_refs,
        )

    return RealWorldBenchmarkSiteObservation(
        id=f"real-world-site-observation:{manifest_id}:{site.id}",
        site_spec_ref=site.id,
        target_url=site.target_url,
        robots_policy_ref=robots_policy_ref,
        live_http_report_ref=report.id,
        network_response_ref=report.network_response_ref,
        source_observation_refs=report.source_observation_refs,
        artifact_refs=report.artifact_refs,
        content_hash_refs=report.content_hash_refs,
        canonical_url_refs=report.canonical_url_refs,
        policy_decision_refs=sorted(set(report.policy_decision_refs + [robots_policy_ref])),
        command_record_refs=report.command_record_refs,
        event_cursor_refs=report.event_cursor_refs,
        outbox_refs=report.outbox_refs,
        replay_bundle_ref=report.replay_bundle_ref,
        status_code=network.response.status_code,
        content_type=network.response.content_type,
        body_size_bytes=network.response.body_size_bytes,
        content_digest=network.response.content_digest,
        matched_observation_refs=matched,
        completion_result=CompletenessResult.PASS,
    )


def _missing_live_evidence_refs(report: object) -> list[str]:
    required = {
        "network_response_ref": getattr(report, "network_response_ref", None),
        "source_observation_refs": getattr(report, "source_observation_refs", None),
        "artifact_refs": getattr(report, "artifact_refs", None),
        "content_hash_refs": getattr(report, "content_hash_refs", None),
        "canonical_url_refs": getattr(report, "canonical_url_refs", None),
        "command_record_refs": getattr(report, "command_record_refs", None),
        "event_cursor_refs": getattr(report, "event_cursor_refs", None),
        "outbox_refs": getattr(report, "outbox_refs", None),
        "replay_bundle_ref": getattr(report, "replay_bundle_ref", None),
    }
    return [name for name, value in required.items() if not value]


def _evaluate_observations(
    site: RealWorldBenchmarkSiteSpec,
    body: str,
    response: NetworkResponse,
) -> tuple[list[Ref], list[str]]:
    matched: list[Ref] = []
    mismatches: list[str] = []
    status_code = response.status_code
    content_type = response.content_type
    body_size_bytes = response.body_size_bytes
    if status_code == site.expected_status_code:
        matched.append(f"observation:{site.id}:status-code")
    else:
        mismatches.append(f"expected status {site.expected_status_code}, got {status_code}")
    if str(content_type).startswith(site.expected_content_type):
        matched.append(f"observation:{site.id}:content-type")
    else:
        mismatches.append(
            f"expected content type {site.expected_content_type}, got {content_type}"
        )
    if body_size_bytes >= site.min_body_size_bytes:
        matched.append(f"observation:{site.id}:body-size")
    else:
        mismatches.append(
            f"expected body size >= {site.min_body_size_bytes}, got {body_size_bytes}"
        )
    parser = _TitleParser()
    parser.feed(body)
    title = parser.title.casefold()
    body_folded = body.casefold()
    for index, fragment in enumerate(site.required_title_fragments, start=1):
        if fragment.casefold() in title:
            matched.append(f"observation:{site.id}:title:{index}")
        else:
            mismatches.append(f"title fragment not found: {fragment}")
    for index, fragment in enumerate(site.required_body_fragments, start=1):
        if fragment.casefold() in body_folded:
            matched.append(f"observation:{site.id}:body:{index}")
        else:
            mismatches.append(f"body fragment not found: {fragment}")
    for index, (pattern, minimum) in enumerate(site.required_regex_counts.items(), start=1):
        count = len(re.findall(pattern, body, flags=re.IGNORECASE | re.MULTILINE))
        if count >= minimum:
            matched.append(f"observation:{site.id}:regex:{index}")
        else:
            mismatches.append(f"regex {pattern!r} expected >= {minimum}, got {count}")
    return matched, mismatches


def _failure_observation(
    *,
    manifest_id: str,
    site: RealWorldBenchmarkSiteSpec,
    failure: RealWorldBenchmarkFailureType,
    missing_field: str,
    diagnostics: list[str],
    robots_policy_ref: Ref | None = None,
    live_http_report_ref: Ref | None = None,
    network_response_ref: Ref | None = None,
    artifact_refs: list[Ref] | None = None,
    policy_decision_refs: list[Ref] | None = None,
    command_record_refs: list[Ref] | None = None,
    event_cursor_refs: list[Ref] | None = None,
    outbox_refs: list[Ref] | None = None,
) -> RealWorldBenchmarkSiteObservation:
    return RealWorldBenchmarkSiteObservation(
        id=f"real-world-site-observation:{manifest_id}:{site.id}",
        site_spec_ref=site.id,
        target_url=site.target_url,
        robots_policy_ref=robots_policy_ref,
        live_http_report_ref=live_http_report_ref,
        network_response_ref=network_response_ref,
        artifact_refs=artifact_refs or [],
        policy_decision_refs=policy_decision_refs or [],
        command_record_refs=command_record_refs or [],
        event_cursor_refs=event_cursor_refs or [],
        outbox_refs=outbox_refs or [],
        failure_report_refs=[f"failure:{manifest_id}:{site.id}:{failure.value}"],
        missing_ref_fields=[missing_field],
        failure_type=failure,
        diagnostics=diagnostics,
        completion_result=CompletenessResult.FAIL,
    )


def _build_run_report(
    *,
    manifest: RealWorldBenchmarkCorpusManifest,
    observations: list[RealWorldBenchmarkSiteObservation],
    store: ProductionPersistenceStore | None = None,
) -> RealWorldBenchmarkRunReport:
    failures = [item for item in observations if item.completion_result != CompletenessResult.PASS]
    if failures:
        failure_type = failures[0].failure_type or RealWorldBenchmarkFailureType.LIVE_HTTP_FAILED
        return RealWorldBenchmarkRunReport(
            id=f"real-world-benchmark-run-report:{manifest.id}",
            fixture_id=manifest.id,
            run_ref=f"run:{manifest.id}",
            benchmark_corpus_ref=f"real-world-benchmark-corpus:{manifest.id}",
            site_observation_refs=[item.id for item in observations],
            failure_report_refs=sorted(
                {ref for item in failures for ref in item.failure_report_refs}
            ),
            missing_ref_fields=sorted(
                {field for item in failures for field in item.missing_ref_fields}
            ),
            failure_type=failure_type,
            diagnostics=[diagnostic for item in failures for diagnostic in item.diagnostics],
            operator_status=failure_type.value,
            completion_result=CompletenessResult.FAIL,
        )

    command_record_refs = _collect("command_record_refs", observations)
    event_cursor_refs = _collect("event_cursor_refs", observations)
    outbox_refs = _collect("outbox_refs", observations)
    if store is not None:
        command_record_refs = sorted(
            set(command_record_refs + [f"durable-command:cmd:{manifest.id}:real-world-report"])
        )
        outbox_refs = sorted(set(outbox_refs + [f"outbox:cmd:{manifest.id}:real-world-report"]))
        cursor = store.build_event_cursor(f"run:{manifest.id}")
        event_cursor_refs = sorted(set(event_cursor_refs + [cursor.id]))
    return RealWorldBenchmarkRunReport(
        id=f"real-world-benchmark-run-report:{manifest.id}",
        fixture_id=manifest.id,
        run_ref=f"run:{manifest.id}",
        benchmark_corpus_ref=f"real-world-benchmark-corpus:{manifest.id}",
        benchmark_run_refs=[
            f"benchmark-run:{manifest.id}:{item.site_spec_ref}" for item in observations
        ],
        site_observation_refs=[item.id for item in observations],
        live_http_report_refs=_collect_optional("live_http_report_ref", observations),
        network_response_refs=_collect_optional("network_response_ref", observations),
        source_observation_refs=_collect("source_observation_refs", observations),
        artifact_refs=_collect("artifact_refs", observations),
        content_hash_refs=_collect("content_hash_refs", observations),
        canonical_url_refs=_collect("canonical_url_refs", observations),
        policy_decision_refs=_collect("policy_decision_refs", observations),
        command_record_refs=command_record_refs,
        event_cursor_refs=event_cursor_refs,
        outbox_refs=outbox_refs,
        replay_bundle_refs=_collect_optional("replay_bundle_ref", observations),
        observation_summary_refs=[
            f"observation-summary:{manifest.id}:{item.site_spec_ref}" for item in observations
        ],
        operator_status="real_world_benchmark_completed",
        completion_result=CompletenessResult.PASS,
    )


def _collect(field_name: str, observations: list[RealWorldBenchmarkSiteObservation]) -> list[Ref]:
    refs: list[Ref] = []
    for observation in observations:
        refs.extend(getattr(observation, field_name))
    return sorted(set(refs))


def _collect_optional(
    field_name: str,
    observations: list[RealWorldBenchmarkSiteObservation],
) -> list[Ref]:
    return sorted({ref for ref in (getattr(item, field_name) for item in observations) if ref})


def _record_observation_event(
    *,
    manifest_id: str,
    site: RealWorldBenchmarkSiteSpec,
    observation: RealWorldBenchmarkSiteObservation,
    live_result: LiveHttpAcquisitionRuntimeResult,
    store: ProductionPersistenceStore,
) -> RealWorldBenchmarkSiteObservation:
    production_report = live_result.production_persistence.report
    command = create_runtime_command(
        command_id=f"cmd:{manifest_id}:{site.id}:real-world-observation",
        command_type="record_real_world_benchmark_site_observation",
        target_aggregate_type="RealWorldBenchmarkSiteObservation",
        target_aggregate_id=observation.id,
        actor_ref="actor:real-world-benchmark",
        payload_ref=f"payload:{manifest_id}:{site.id}:real-world-observation",
        policy_decision_refs=observation.policy_decision_refs,
    )
    record, _, outbox, _, _ = store.handle_command_once(
        command,
        run_ref=production_report.run_ref,
        objective_ref=production_report.objective_ref,
        plan_ref=production_report.plan_ref,
        event_type="real_world_benchmark_site_observed",
        output_refs=[observation.id],
    )
    store.mark_outbox_dispatched(
        outbox.id,
        dispatched_at_ref=f"clock:{manifest_id}:{site.id}:real-world-observation-dispatched",
    )
    cursor = store.build_event_cursor(production_report.run_ref)
    updated = observation.model_copy(
        update={
            "command_record_refs": sorted(
                set(observation.command_record_refs + [record.id])
            ),
            "event_cursor_refs": sorted(
                set(observation.event_cursor_refs + [cursor.id])
            ),
            "outbox_refs": sorted(set(observation.outbox_refs + [outbox.id])),
        }
    )
    store.save_canonical_model("real_world_benchmark_site_observations", updated.id, updated)
    return updated


def _record_run_report_event(
    *,
    manifest: RealWorldBenchmarkCorpusManifest,
    report: RealWorldBenchmarkRunReport,
    live_result: LiveHttpAcquisitionRuntimeResult,
    store: ProductionPersistenceStore,
) -> None:
    del live_result
    command = create_runtime_command(
        command_id=f"cmd:{manifest.id}:real-world-report",
        command_type="record_real_world_benchmark_run_report",
        target_aggregate_type="RealWorldBenchmarkRunReport",
        target_aggregate_id=report.id,
        actor_ref="actor:real-world-benchmark",
        payload_ref=f"payload:{manifest.id}:real-world-report",
        policy_decision_refs=report.policy_decision_refs,
    )
    _, _, outbox, _, _ = store.handle_command_once(
        command,
        run_ref=f"run:{manifest.id}",
        objective_ref=f"objective:{manifest.id}",
        plan_ref=f"plan:{manifest.id}",
        event_type="real_world_benchmark_run_reported",
        output_refs=[report.id],
    )
    store.mark_outbox_dispatched(
        outbox.id,
        dispatched_at_ref=f"clock:{manifest.id}:real-world-report-dispatched",
    )
