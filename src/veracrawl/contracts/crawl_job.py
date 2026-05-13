"""External CrawlJobSpec contract.

This contract drives the external (non-fixture) crawl runtime added by
``docs/plans/general-purpose-crawler-goal.md``. It deliberately rejects
dangerous defaults — empty allowlists, private networks, robots
bypasses, browser sources — so a hand-edited YAML file cannot
accidentally unleash an unbounded crawler.
"""

from __future__ import annotations

from enum import StrEnum
from urllib.parse import urlsplit

from pydantic import Field, field_validator, model_validator

from veracrawl.contracts.common import VeraModel
from veracrawl.contracts.enums import AdapterType

# Hard caps. These are deliberate upper bounds the spec cannot exceed
# regardless of operator intent — they bound worst-case blast radius
# for a misconfigured job. Operators can lower these via the spec but
# cannot raise them without changing source.
MAX_PAGES_HARD_CAP = 100_000
MAX_DEPTH_HARD_CAP = 32
MAX_RUNTIME_SECONDS_HARD_CAP = 24 * 60 * 60
PER_ORIGIN_CONCURRENCY_HARD_CAP = 16
RATE_LIMIT_RPM_HARD_CAP = 600


class RobotsPolicy(StrEnum):
    OBEY = "obey"
    WARN = "warn"
    DENY_WITHOUT_ROBOTS = "deny_without_robots"


class PrivateNetworkPolicy(StrEnum):
    DENY = "deny"
    # Test-only opt-in: allow loopback (127.0.0.0/8, ::1, localhost)
    # so integration tests can exercise the runner against a local
    # fixture server. Production crawl jobs MUST use DENY.
    ALLOW_LOOPBACK_ONLY = "allow_loopback_only"


class ExtractionMode(StrEnum):
    NONE = "none"
    DETERMINISTIC = "deterministic"
    LLM_ASSISTED = "llm_assisted"


class OutputFormat(StrEnum):
    JSONL = "jsonl"
    JSON = "json"


class RateLimitSpec(VeraModel):
    requests_per_minute: int = Field(ge=1, le=RATE_LIMIT_RPM_HARD_CAP)
    crawl_delay_seconds: float | None = Field(default=None, ge=0.0, le=600.0)


class ArtifactPolicySpec(VeraModel):
    store_raw_html: bool
    store_headers: bool
    store_screenshots: bool
    store_documents: bool


class ExtractionSpec(VeraModel):
    mode: ExtractionMode
    schema_ref: str | None = None
    exploratory_schema_allowed: bool = False

    @model_validator(mode="after")
    def validate_extraction(self) -> ExtractionSpec:
        if self.mode == ExtractionMode.LLM_ASSISTED:
            if self.schema_ref is None and not self.exploratory_schema_allowed:
                raise ValueError(
                    "extraction: llm_assisted without schema_ref requires "
                    "exploratory_schema_allowed=true"
                )
        return self


class OutputSpec(VeraModel):
    format: OutputFormat
    include_raw_refs: bool
    include_evidence: bool


def _looks_like_domain(value: str) -> bool:
    if not value or "/" in value or "://" in value or " " in value:
        return False
    # require at least one dot or be 'localhost'
    return "." in value or value == "localhost"


class CrawlJobSpec(VeraModel):
    id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    seed_urls: list[str] = Field(min_length=1)
    allowed_domains: list[str] = Field(min_length=1)
    denied_domains: list[str] = Field(default_factory=list)
    max_depth: int = Field(ge=0, le=MAX_DEPTH_HARD_CAP)
    max_pages: int = Field(ge=1, le=MAX_PAGES_HARD_CAP)
    max_runtime_seconds: int = Field(ge=1, le=MAX_RUNTIME_SECONDS_HARD_CAP)
    per_origin_concurrency: int = Field(ge=1, le=PER_ORIGIN_CONCURRENCY_HARD_CAP)
    rate_limit: RateLimitSpec
    source_adapters: list[AdapterType] = Field(min_length=1)
    robots_policy: RobotsPolicy = RobotsPolicy.OBEY
    private_network_policy: PrivateNetworkPolicy = PrivateNetworkPolicy.DENY
    artifact_policy: ArtifactPolicySpec
    extraction: ExtractionSpec
    output: OutputSpec

    @field_validator("seed_urls")
    @classmethod
    def validate_seed_urls_scheme(cls, value: list[str]) -> list[str]:
        for url in value:
            parsed = urlsplit(url)
            if parsed.scheme not in {"http", "https"}:
                raise ValueError(f"seed_urls entry must be http(s): {url!r}")
            if not parsed.hostname:
                raise ValueError(f"seed_urls entry missing hostname: {url!r}")
        return value

    @field_validator("allowed_domains", "denied_domains")
    @classmethod
    def validate_domain_shape(cls, value: list[str]) -> list[str]:
        for domain in value:
            if not _looks_like_domain(domain):
                # Use the field name in the message so downstream
                # ValidationError matches on either field.
                raise ValueError(
                    f"allowed_domains/denied_domains entry must be a bare "
                    f"hostname, got: {domain!r}"
                )
        return value

    @model_validator(mode="after")
    def validate_cross_field_invariants(self) -> CrawlJobSpec:
        allowed = {d.lower() for d in self.allowed_domains}
        for url in self.seed_urls:
            host = (urlsplit(url).hostname or "").lower()
            if host not in allowed and not any(
                host == a or host.endswith("." + a) for a in allowed
            ):
                raise ValueError(
                    f"seed_urls entry {url!r} is outside allowed_domains "
                    f"{sorted(allowed)}"
                )
        if AdapterType.BROWSER_SNAPSHOT in self.source_adapters:
            if not self.artifact_policy.store_screenshots:
                raise ValueError(
                    "browser adapter requires artifact_policy.store_screenshots=true"
                )
        return self
