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


class UnitOfWorkStatus(StrEnum):
    OPEN = "open"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class DurableCommandRecordStatus(StrEnum):
    RECORDED = "recorded"
    COMMITTED = "committed"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"
    FAILED = "failed"


class OutboxStatus(StrEnum):
    PENDING = "pending"
    DISPATCHED = "dispatched"
    FAILED = "failed"


class FrontierItemStatus(StrEnum):
    QUEUED = "queued"
    LEASED = "leased"
    COMPLETED = "completed"
    RELEASED = "released"
    RETRYING = "retrying"
    DEAD_LETTERED = "dead_lettered"


class QueueLeaseStatus(StrEnum):
    ACTIVE = "active"
    HEARTBEAT_RECORDED = "heartbeat_recorded"
    COMPLETED = "completed"
    RELEASED = "released"
    EXPIRED = "expired"
    INVALID = "invalid"


class DurableRecoveryStatus(StrEnum):
    DURABLE_RECOVERED = "durable_recovered"
    DUPLICATE_COMMAND_DEDUPED = "duplicate_command_deduped"
    EVENT_GAP = "event_gap"
    PENDING_OUTBOX = "pending_outbox"
    STALE_LEASE = "stale_lease"
    INVALID_LEASE = "invalid_lease"
    MISSING_ARTIFACT = "missing_artifact"
    DEAD_LETTER = "dead_letter"


class FetchAttemptStatus(StrEnum):
    PLANNED = "planned"
    SUCCEEDED = "succeeded"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    MALFORMED = "malformed"
    RETRY_EXHAUSTED = "retry_exhausted"
    FAILED = "failed"


class FetchResultStatus(StrEnum):
    SUCCEEDED = "succeeded"
    BLOCKED = "blocked"
    RATE_LIMITED = "rate_limited"
    MALFORMED = "malformed"
    FAILED = "failed"


class RateLimitDecisionValue(StrEnum):
    ALLOW = "allow"
    RATE_LIMIT = "rate_limit"


class SourceFailureType(StrEnum):
    SOURCE_BLOCKED = "source_blocked"
    SOURCE_RATE_LIMITED = "source_rate_limited"
    ADAPTER_MISMATCH = "adapter_mismatch"
    MALFORMED_RESPONSE = "malformed_response"
    RETRY_EXHAUSTED = "retry_exhausted"
    MISSING_RAW_ARTIFACT = "missing_raw_artifact"


class SourceAcquisitionStatus(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    NEEDS_REVIEW = "needs_review"


class NetworkFailureType(StrEnum):
    EGRESS_DENIED = "egress_denied"
    PRIVATE_NETWORK_DENIED = "private_network_denied"
    ROBOTS_BLOCKED = "robots_blocked"
    RATE_BUDGET_EXCEEDED = "rate_budget_exceeded"
    SIZE_BUDGET_EXCEEDED = "size_budget_exceeded"
    REDIRECT_DENIED = "redirect_denied"
    NETWORK_TIMEOUT = "network_timeout"
    UNSAFE_BROWSER_SIDE_EFFECT = "unsafe_browser_side_effect"
    ADAPTER_FAILURE = "adapter_failure"
    MISSING_NETWORK_ARTIFACT = "missing_network_artifact"


class BrowserStepStatus(StrEnum):
    PLANNED = "planned"
    EXECUTED = "executed"
    BLOCKED = "blocked"
    FAILED = "failed"


class BrowserSideEffectClass(StrEnum):
    READ_ONLY = "read_only"
    ACCOUNT_CHANGING = "account_changing"
    PURCHASE_CART = "purchase_cart"
    DELETE = "delete"
    MESSAGE_SEND = "message_send"
    UNKNOWN = "unknown"


class PageType(StrEnum):
    STATIC = "static"
    LISTING = "listing"
    DETAIL = "detail"
    SEARCH = "search"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


class LinkProvenanceStatus(StrEnum):
    DISCOVERED = "discovered"
    BLOCKED = "blocked"
    DUPLICATE = "duplicate"


class ProcessFailureType(StrEnum):
    MISSING_RAW_ARTIFACT = "missing_raw_artifact"
    EMPTY_NORMALIZED_CONTENT = "empty_normalized_content"
    CANDIDATE_ANCHOR_GAP = "candidate_anchor_gap"
    NORMALIZATION_FAILED = "normalization_failed"
