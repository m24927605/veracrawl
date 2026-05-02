"""Canonical enum values used by foundation contracts."""

from __future__ import annotations

from enum import StrEnum


class OwnerService(StrEnum):
    CONTROL = "control"
    SCHEDULER = "scheduler"
    FETCH = "fetch"
    BROWSER = "browser"
    NORMALIZE = "normalize"
    EXTRACT = "extract"
    EVIDENCE = "evidence"
    VERIFY = "verify"
    PUBLISH = "publish"
    PROJECTION = "projection"
    GRAPH = "graph"
    MEMORY = "memory"
    AGENTS = "agents"
    REVIEW_REPLAY = "review_replay"
    EXPORT = "export"
    OPS = "ops"
    ARTIFACT_LIFECYCLE = "artifact_lifecycle"
    CONTRACTS = "contracts"
    RUNTIME_EVENTS = "runtime_events"
    POLICY = "policy"
    PORTS = "ports"
    TESTS = "tests"


class CommandStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMMITTED = "committed"
    FAILED = "failed"


class CommandResultStatus(StrEnum):
    COMMITTED = "committed"
    REJECTED = "rejected"
    FAILED = "failed"
    DUPLICATE = "duplicate"


class PolicyDecisionValue(StrEnum):
    ALLOW = "allow"
    DENY = "deny"
    REQUIRE_REVIEW = "require_review"


class AdapterType(StrEnum):
    HTTP = "http"
    SITEMAP = "sitemap"
    RSS = "rss"
    BROWSER_SNAPSHOT = "browser_snapshot"
    AUTHORIZED_SESSION = "authorized_session"
    API_SOURCE = "api_source"
    DOCUMENT_SOURCE = "document_source"
    FILE_IMPORT = "file_import"
    MANUAL_SEED = "manual_seed"
    PRIOR_SNAPSHOT = "prior_snapshot"


class SourceAdapterResultType(StrEnum):
    FETCH_RESULT = "fetch_result"
    BROWSER_SNAPSHOT = "browser_snapshot"
    DISCOVERED_LINKS = "discovered_links"
    SESSION_STATE = "session_state"
    API_PAYLOAD = "api_payload"
    DOCUMENT_ARTIFACT = "document_artifact"
    FILE_ARTIFACT = "file_artifact"
    SEED_PLAN = "seed_plan"
    PRIOR_SNAPSHOT_REF = "prior_snapshot_ref"
    BLOCKED_SOURCE = "blocked_source"


class AdapterResultStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    BLOCKED = "blocked"
    FAILED = "failed"
    PARTIAL = "partial"


class AgentRole(StrEnum):
    PLANNER = "planner"
    SITE_UNDERSTANDING = "site_understanding"
    FRONTIER = "frontier"
    FETCH_ANALYSIS = "fetch_analysis"
    EXTRACTOR = "extractor"
    VERIFIER = "verifier"
    DRIFT = "drift"
    MEMORY = "memory"
    OPS = "ops"


class AgentRunStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"
    ESCALATED = "escalated"
    CANCELLED = "cancelled"


class RuntimeType(StrEnum):
    NATIVE_VERACRAWL = "native_veracrawl"
    MODEL_PROVIDER_ADAPTER = "model_provider_adapter"
    AGENT_FRAMEWORK_ADAPTER = "agent_framework_adapter"


class FrameworkStatePersistence(StrEnum):
    FORBIDDEN = "forbidden"
    DIAGNOSTIC_ONLY = "diagnostic_only"


class ToolType(StrEnum):
    READ = "read"
    PROPOSE = "propose"
    MUTATE_WITH_POLICY = "mutate_with_policy"
    REVIEW_ONLY = "review_only"


class ToolCallStatus(StrEnum):
    PROPOSED = "proposed"
    REJECTED = "rejected"
    APPROVED = "approved"
    EXECUTED = "executed"
    FAILED = "failed"


class ReplayMissingRefBehavior(StrEnum):
    FAIL_REPLAY = "fail_replay"
    ALLOW_WITH_GAP_REPORT = "allow_with_gap_report"


class ReplayMode(StrEnum):
    FULL = "full"
    REDACTED = "redacted"
    STRUCTURAL = "structural"


class CompletenessResult(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"


class ComparisonMode(StrEnum):
    EXACT = "exact"
    NORMALIZED = "normalized"
    TOLERANCE = "tolerance"


class ObjectiveStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    ACTIVE = "active"
    PAUSED = "paused"
    ARCHIVED = "archived"


class PlanStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RuntimeCompletionGateType(StrEnum):
    OBJECTIVE = "objective"
    PLAN = "plan"
    SOURCE = "source"
    NORMALIZATION = "normalization"
    EXTRACTION = "extraction"
    EVIDENCE = "evidence"
    VERIFICATION = "verification"
    PUBLICATION = "publication"
    REPLAY = "replay"


class RuntimeGateStatus(StrEnum):
    PENDING = "pending"
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"
    CONFLICT = "conflict"


class ArtifactType(StrEnum):
    RAW_SOURCE = "raw_source"
    NORMALIZED_DOCUMENT = "normalized_document"
    ANCHOR_MAP = "anchor_map"
    CANDIDATE_PAYLOAD = "candidate_payload"
    EVIDENCE_BUNDLE = "evidence_bundle"
    OUTPUT_MANIFEST = "output_manifest"
    REPLAY_BUNDLE = "replay_bundle"
    REDACTION_MAP = "redaction_map"


class PrivacyClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    RESTRICTED = "restricted"


class ExtractionCandidateStatus(StrEnum):
    CANDIDATE = "candidate"
    EVIDENCE_BUILT = "evidence_built"
    REJECTED = "rejected"
    CONFLICTED = "conflicted"
    SUPERSEDED = "superseded"
    PUBLISHED = "published"


class EvidencePacketStatus(StrEnum):
    BUILT = "built"
    ACCEPTED_FOR_VERIFICATION = "accepted_for_verification"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class VerificationDecisionValue(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"
    REVIEW = "review"
    CONFLICT = "conflict"


class PublishedOutputStatus(StrEnum):
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


class AgentRecommendationSubject(StrEnum):
    CRAWL_PLAN = "crawl_plan"
    EXTRACTION_STRATEGY = "extraction_strategy"
    EVIDENCE_ANCHOR = "evidence_anchor"
    VERIFICATION = "verification"
    REPAIR = "repair"


class AgentRecommendationStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
