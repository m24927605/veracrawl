"""Contract tests for the external CrawlJobSpec.

CrawlJobSpec is the contract that drives the external (non-fixture)
crawl runtime introduced by ``docs/plans/general-purpose-crawler-goal.md``.
Defaults must be safe: empty allowlists, private networks, and
browser sources are forbidden unless the job spec explicitly opts in.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from veracrawl.contracts.crawl_job import (
    ArtifactPolicySpec,
    CrawlJobSpec,
    ExtractionMode,
    ExtractionSpec,
    OutputFormat,
    OutputSpec,
    PrivateNetworkPolicy,
    RateLimitSpec,
    RobotsPolicy,
)
from veracrawl.contracts.enums import AdapterType


def _valid_kwargs(**overrides: object) -> dict[str, object]:
    base: dict[str, object] = {
        "id": "job:demo",
        "project_id": "project:demo",
        "objective": "Discover product pages on demo.example",
        "seed_urls": ["https://demo.example/", "https://demo.example/catalog"],
        "allowed_domains": ["demo.example"],
        "denied_domains": [],
        "max_depth": 2,
        "max_pages": 50,
        "max_runtime_seconds": 600,
        "per_origin_concurrency": 2,
        "rate_limit": RateLimitSpec(requests_per_minute=30, crawl_delay_seconds=1.0),
        "source_adapters": [AdapterType.HTTP, AdapterType.SITEMAP],
        "robots_policy": RobotsPolicy.OBEY,
        "private_network_policy": PrivateNetworkPolicy.DENY,
        "artifact_policy": ArtifactPolicySpec(
            store_raw_html=True,
            store_headers=True,
            store_screenshots=False,
            store_documents=True,
        ),
        "extraction": ExtractionSpec(
            mode=ExtractionMode.DETERMINISTIC,
            schema_ref=None,
            exploratory_schema_allowed=False,
        ),
        "output": OutputSpec(
            format=OutputFormat.JSONL,
            include_raw_refs=True,
            include_evidence=True,
        ),
    }
    base.update(overrides)
    return base


def test_valid_job_spec_round_trips() -> None:
    spec = CrawlJobSpec(**_valid_kwargs())  # type: ignore[arg-type]
    dumped = spec.model_dump(mode="json")
    restored = CrawlJobSpec.model_validate(dumped)
    assert restored.content_hash() == spec.content_hash()


def test_empty_allowed_domains_rejected() -> None:
    with pytest.raises(ValidationError, match="allowed_domains"):
        CrawlJobSpec(**_valid_kwargs(allowed_domains=[]))  # type: ignore[arg-type]


def test_empty_seed_urls_rejected() -> None:
    with pytest.raises(ValidationError, match="seed_urls"):
        CrawlJobSpec(**_valid_kwargs(seed_urls=[]))  # type: ignore[arg-type]


def test_non_http_seed_url_rejected() -> None:
    with pytest.raises(ValidationError, match="seed_urls"):
        CrawlJobSpec(**_valid_kwargs(seed_urls=["ftp://demo.example/"]))  # type: ignore[arg-type]


def test_seed_url_outside_allowed_domain_rejected() -> None:
    # Seed URLs must be inside allowed_domains; otherwise the very
    # first frontier item would be skipped, which is almost certainly
    # a job-spec mistake we should surface early.
    with pytest.raises(ValidationError, match="seed_urls"):
        CrawlJobSpec(
            **_valid_kwargs(  # type: ignore[arg-type]
                seed_urls=["https://other.example/"],
                allowed_domains=["demo.example"],
            )
        )


def test_max_pages_must_be_positive() -> None:
    with pytest.raises(ValidationError, match="max_pages"):
        CrawlJobSpec(**_valid_kwargs(max_pages=0))  # type: ignore[arg-type]


def test_max_pages_must_be_within_hard_cap() -> None:
    with pytest.raises(ValidationError, match="max_pages"):
        CrawlJobSpec(**_valid_kwargs(max_pages=10_000_000))  # type: ignore[arg-type]


def test_max_depth_must_be_non_negative_and_within_cap() -> None:
    with pytest.raises(ValidationError, match="max_depth"):
        CrawlJobSpec(**_valid_kwargs(max_depth=-1))  # type: ignore[arg-type]
    with pytest.raises(ValidationError, match="max_depth"):
        CrawlJobSpec(**_valid_kwargs(max_depth=1000))  # type: ignore[arg-type]


def test_max_runtime_seconds_bounds() -> None:
    with pytest.raises(ValidationError, match="max_runtime_seconds"):
        CrawlJobSpec(**_valid_kwargs(max_runtime_seconds=0))  # type: ignore[arg-type]
    with pytest.raises(ValidationError, match="max_runtime_seconds"):
        CrawlJobSpec(**_valid_kwargs(max_runtime_seconds=10**9))  # type: ignore[arg-type]


def test_source_adapters_must_be_non_empty() -> None:
    with pytest.raises(ValidationError, match="source_adapters"):
        CrawlJobSpec(**_valid_kwargs(source_adapters=[]))  # type: ignore[arg-type]


def test_browser_adapter_requires_explicit_opt_in() -> None:
    # Browser is off by default. It is only allowed when the job spec
    # explicitly lists BROWSER_SNAPSHOT in source_adapters AND sets
    # artifact_policy.store_screenshots=True (so the job has chosen
    # to retain the heavyweight side-effect artifacts).
    with pytest.raises(ValidationError, match="browser"):
        CrawlJobSpec(
            **_valid_kwargs(  # type: ignore[arg-type]
                source_adapters=[AdapterType.HTTP, AdapterType.BROWSER_SNAPSHOT],
                artifact_policy=ArtifactPolicySpec(
                    store_raw_html=True,
                    store_headers=True,
                    store_screenshots=False,
                    store_documents=False,
                ),
            )
        )


def test_browser_adapter_with_screenshots_allowed() -> None:
    spec = CrawlJobSpec(
        **_valid_kwargs(  # type: ignore[arg-type]
            source_adapters=[AdapterType.HTTP, AdapterType.BROWSER_SNAPSHOT],
            artifact_policy=ArtifactPolicySpec(
                store_raw_html=True,
                store_headers=True,
                store_screenshots=True,
                store_documents=False,
            ),
        )
    )
    assert AdapterType.BROWSER_SNAPSHOT in spec.source_adapters


def test_per_origin_concurrency_bounds() -> None:
    with pytest.raises(ValidationError, match="per_origin_concurrency"):
        CrawlJobSpec(**_valid_kwargs(per_origin_concurrency=0))  # type: ignore[arg-type]
    with pytest.raises(ValidationError, match="per_origin_concurrency"):
        CrawlJobSpec(**_valid_kwargs(per_origin_concurrency=1000))  # type: ignore[arg-type]


def test_rate_limit_requests_per_minute_bounds() -> None:
    with pytest.raises(ValidationError, match="requests_per_minute"):
        RateLimitSpec(requests_per_minute=0, crawl_delay_seconds=None)
    with pytest.raises(ValidationError, match="requests_per_minute"):
        RateLimitSpec(requests_per_minute=10_000, crawl_delay_seconds=None)


def test_rate_limit_crawl_delay_seconds_non_negative() -> None:
    with pytest.raises(ValidationError, match="crawl_delay_seconds"):
        RateLimitSpec(requests_per_minute=30, crawl_delay_seconds=-1.0)


def test_allowed_domain_shape_rejects_url() -> None:
    # allowed_domains should hold bare hostnames, not URLs.
    with pytest.raises(ValidationError, match="allowed_domains"):
        CrawlJobSpec(**_valid_kwargs(allowed_domains=["https://demo.example/"]))  # type: ignore[arg-type]


def test_denied_domains_can_be_empty() -> None:
    spec = CrawlJobSpec(**_valid_kwargs(denied_domains=[]))  # type: ignore[arg-type]
    assert spec.denied_domains == []


def test_robots_policy_defaults_to_obey() -> None:
    kwargs = _valid_kwargs()
    kwargs.pop("robots_policy")
    spec = CrawlJobSpec(**kwargs)  # type: ignore[arg-type]
    assert spec.robots_policy == RobotsPolicy.OBEY


def test_private_network_policy_defaults_to_deny() -> None:
    kwargs = _valid_kwargs()
    kwargs.pop("private_network_policy")
    spec = CrawlJobSpec(**kwargs)  # type: ignore[arg-type]
    assert spec.private_network_policy == PrivateNetworkPolicy.DENY


def test_extra_fields_rejected() -> None:
    with pytest.raises(ValidationError):
        CrawlJobSpec(**_valid_kwargs(unknown_field="boom"))  # type: ignore[arg-type]


def test_llm_assisted_extraction_requires_explicit_opt_in_for_exploratory_schema() -> None:
    # llm_assisted mode without a schema_ref is exploratory; that requires
    # exploratory_schema_allowed=True so callers can't silently bypass schema
    # discipline.
    with pytest.raises(ValidationError, match="exploratory"):
        CrawlJobSpec(
            **_valid_kwargs(  # type: ignore[arg-type]
                extraction=ExtractionSpec(
                    mode=ExtractionMode.LLM_ASSISTED,
                    schema_ref=None,
                    exploratory_schema_allowed=False,
                ),
            )
        )


def test_content_hash_stable() -> None:
    spec_a = CrawlJobSpec(**_valid_kwargs())  # type: ignore[arg-type]
    spec_b = CrawlJobSpec(**_valid_kwargs())  # type: ignore[arg-type]
    assert spec_a.content_hash() == spec_b.content_hash()
