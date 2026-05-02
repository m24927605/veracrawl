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


class ObjectStoreAdapterKind(StrEnum):
    S3_COMPATIBLE = "s3_compatible"
    S3_CONTRACT = "s3_contract"
    EXTERNAL_OBJECT_STORE = "external_object_store"


class ObjectStoreCapability(StrEnum):
    PUT = "put"
    DUPLICATE_PUT = "duplicate_put"
    GET = "get"
    HEAD = "head"
    LIST = "list"
    DELETE = "delete"
    CONTENT_DIGEST = "content_digest"
    IDEMPOTENCY = "idempotency"
    LIFECYCLE = "lifecycle"
    RETENTION = "retention"
    PRIVACY = "privacy"


class ObjectStoreOperation(StrEnum):
    PUT = "put"
    DUPLICATE_PUT = "duplicate_put"
    GET = "get"
    HEAD = "head"
    LIST = "list"
    DELETE = "delete"


class ObjectStoreConformanceFailureType(StrEnum):
    OBJECT_STORE_MISSING_DIGEST = "object_store_missing_digest"
    OBJECT_STORE_MISSING_READ_AFTER_WRITE = "object_store_missing_read_after_write"
    OBJECT_STORE_MISSING_DELETE_MARKER = "object_store_missing_delete_marker"


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


class MultiAgentWorkflowStatus(StrEnum):
    PROPOSED = "proposed"
    RUNNING = "running"
    COMPLETED = "completed"
    ESCALATED = "escalated"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentHandoffStatus(StrEnum):
    PROPOSED = "proposed"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    COMPLETED = "completed"


class CoordinationDecisionType(StrEnum):
    CHOOSE_PLAN = "choose_plan"
    RESOLVE_RECOMMENDATION_CONFLICT = "resolve_recommendation_conflict"
    TERMINATE_LOOP = "terminate_loop"
    ESCALATE_TO_REVIEW = "escalate_to_review"
    APPROVE_REPAIR_PROPOSAL = "approve_repair_proposal"


class CoordinationDecisionStatus(StrEnum):
    RECORDED = "recorded"
    APPLIED = "applied"
    REJECTED = "rejected"


class RepairSignalStatus(StrEnum):
    OBSERVED = "observed"
    REVIEWED = "reviewed"
    REPAIRED = "repaired"
    IGNORED = "ignored"


class MultiAgentFailureType(StrEnum):
    LOOP_BUDGET_EXHAUSTED = "loop_budget_exhausted"
    OWNER_SERVICE_BYPASS = "owner_service_bypass"
    MISSING_REPAIR_EVIDENCE = "missing_repair_evidence"
    UNRESOLVED_COORDINATION_CONFLICT = "unresolved_coordination_conflict"
    AGENT_REASONING_AS_EVIDENCE = "agent_reasoning_as_evidence"


class ReviewItemType(StrEnum):
    CRAWL_PLAN = "crawl_plan"
    SCHEMA = "schema"
    PUBLICATION_POLICY = "publication_policy"
    SOURCE_ADAPTER = "source_adapter"
    BROWSER_INTERACTION = "browser_interaction"
    AUTHORIZED_SESSION = "authorized_session"
    CREDENTIAL_USE = "credential_use"
    EXTRACTION_CANDIDATE = "extraction_candidate"
    EVIDENCE_PACKET = "evidence_packet"
    VERIFICATION_RECOMMENDATION = "verification_recommendation"
    PUBLICATION = "publication"
    EXPORT_DISPATCH = "export_dispatch"
    EXPORT_WITHDRAWAL = "export_withdrawal"
    ARTIFACT_LIFECYCLE = "artifact_lifecycle"
    RETENTION = "retention"
    MEMORY_RETRIEVAL = "memory_retrieval"
    CROSS_SCOPE_MEMORY_TUNNEL = "cross_scope_memory_tunnel"
    GRAPH_SIGNAL_USE = "graph_signal_use"
    RECOVERY_ACTION = "recovery_action"
    MULTI_AGENT_WORKFLOW = "multi_agent_workflow"
    CONFLICT = "conflict"
    DRIFT = "drift"
    SAFETY_POLICY = "safety_policy"


class ReviewPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class ReviewItemStatus(StrEnum):
    OPEN = "open"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    NEEDS_MORE_EVIDENCE = "needs_more_evidence"
    RESOLVED = "resolved"


class OpsSeverity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OpsFailureType(StrEnum):
    FETCH = "fetch"
    BROWSER = "browser"
    SESSION = "session"
    CREDENTIAL = "credential"
    MODEL = "model"
    AGENT = "agent"
    TOOL = "tool"
    QUEUE = "queue"
    LEASE = "lease"
    DEAD_LETTER = "dead_letter"
    PROCESSING = "processing"
    VERIFICATION = "verification"
    PUBLICATION = "publication"
    EXPORT = "export"
    PROJECTION = "projection"
    PROJECTION_MISMATCH = "projection_mismatch"
    MEMORY = "memory"
    MIGRATION = "migration"
    BACKFILL = "backfill"
    ARTIFACT_LIFECYCLE = "artifact_lifecycle"
    RETENTION = "retention"
    POLICY = "policy"
    AUTOSCALING = "autoscaling"
    BACKPRESSURE = "backpressure"
    DISASTER_RECOVERY = "disaster_recovery"
    MISSING_REVIEW_EVIDENCE = "missing_review_evidence"
    UNRESOLVED_FAILURE_WITHOUT_RECOVERY = "unresolved_failure_without_recovery"
    STALE_DASHBOARD_PROJECTION = "stale_dashboard_projection"
    UNSAFE_RECOVERY_WITHOUT_REVIEW = "unsafe_recovery_without_review"


class RecoveryActionType(StrEnum):
    RETRY_COMMAND = "retry_command"
    RETRY_QUEUE_ITEM = "retry_queue_item"
    RENEW_LEASE = "renew_lease"
    REPLAY_EVENTS = "replay_events"
    TOMBSTONE_ARTIFACT = "tombstone_artifact"
    REDACT_ARTIFACT = "redact_artifact"
    DELETE_ARTIFACT = "delete_artifact"
    RELEASE_LEGAL_HOLD = "release_legal_hold"
    WITHDRAW_OUTPUT = "withdraw_output"
    RECONCILE_EXPORT = "reconcile_export"
    REBUILD_PROJECTION = "rebuild_projection"
    RERUN_MIGRATION = "rerun_migration"
    RERUN_BACKFILL = "rerun_backfill"
    INVALIDATE_MEMORY = "invalidate_memory"
    QUARANTINE_TAINTED_CONTEXT = "quarantine_tainted_context"
    PAUSE_SITE = "pause_site"
    SCALE_WORKER_POOL = "scale_worker_pool"
    RESTORE_FROM_BACKUP = "restore_from_backup"
    REQUEST_REVIEW = "request_review"
    IGNORE = "ignore"


class OpsRecoveryStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class OpsDashboardType(StrEnum):
    RUN = "run"
    FRONTIER = "frontier"
    REVIEW = "review"
    REPLAY = "replay"
    QUALITY = "quality"
    COST = "cost"


class ExportTargetType(StrEnum):
    DATABASE = "database"
    WAREHOUSE = "warehouse"
    FILE = "file"
    API = "api"
    OBJECT_STORE = "object_store"
    QUEUE = "queue"


class ExportDeliveryMode(StrEnum):
    BATCH = "batch"
    STREAMING = "streaming"
    MANUAL = "manual"


class ExportJobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportAttemptStatus(StrEnum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportRetryClassification(StrEnum):
    TRANSIENT = "transient"
    PERMANENT = "permanent"
    DESTINATION_REJECTED = "destination_rejected"


class ExportWithdrawalReason(StrEnum):
    SUPERSEDED = "superseded"
    DISPUTED = "disputed"
    RETENTION_DELETE = "retention_delete"
    SCHEMA_MIGRATION = "schema_migration"
    OPERATOR_WITHDRAWAL = "operator_withdrawal"


class ExportWithdrawalStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportPropagationStatus(StrEnum):
    PENDING = "pending"
    PROPAGATED = "propagated"
    FAILED = "failed"
    DESTINATION_UNSUPPORTED = "destination_unsupported"


class ExportCorrectionStatus(StrEnum):
    PROPOSED = "proposed"
    PROPAGATED = "propagated"
    FAILED = "failed"


class ExportFailureType(StrEnum):
    MISSING_DELIVERY_RECEIPT = "missing_delivery_receipt"
    DUPLICATE_IDEMPOTENCY = "duplicate_idempotency"
    WITHDRAWAL_MAPPING_MISSING = "withdrawal_mapping_missing"
    DESTINATION_UNSUPPORTED = "destination_unsupported"
    CORRECTION_WITHOUT_WITHDRAWAL = "correction_without_withdrawal"


class ScaleQueueName(StrEnum):
    FRONTIER = "frontier"
    PROCESSING = "processing"
    VERIFICATION_REVIEW = "verification_review"
    EXPORT_OUTBOX = "export_outbox"
    PROJECTION = "projection"
    RECOVERY = "recovery"


class ScaleRetryClass(StrEnum):
    TRANSIENT = "transient"
    RATE_LIMITED = "rate_limited"
    POLICY_BLOCKED = "policy_blocked"
    PERMANENT_SOURCE_FAILURE = "permanent_source_failure"
    ADAPTER_BUG = "adapter_bug"
    WORKER_CRASH = "worker_crash"
    PROJECTION_MISMATCH = "projection_mismatch"
    DESTINATION_REJECTED = "destination_rejected"


class ScaleQueueItemStatus(StrEnum):
    QUEUED = "queued"
    LEASED = "leased"
    ACKED = "acked"
    NACKED = "nacked"
    DEAD_LETTERED = "dead_lettered"


class ScaleShardLeaseStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    RELEASED = "released"
    REVOKED = "revoked"


class BackpressureSignalType(StrEnum):
    QUEUE_LAG = "queue_lag"
    RETRY_RATE = "retry_rate"
    BROWSER_MINUTES = "browser_minutes"
    TOKEN_SPEND = "token_spend"
    OBJECT_STORE_GROWTH = "object_store_growth"
    PROJECTION_LAG = "projection_lag"
    EXPORT_LAG = "export_lag"
    ERROR_RATE = "error_rate"


class WorkerPool(StrEnum):
    FETCH = "fetch"
    BROWSER = "browser"
    PROCESSING = "processing"
    EXPORT = "export"
    PROJECTION = "projection"


class ScaleFailureType(StrEnum):
    STALE_LEASE_WITHOUT_RECOVERY = "stale_lease_without_recovery"
    UNFAIR_SITE_STARVATION = "unfair_site_starvation"
    AUTOSCALE_WITHOUT_POLICY = "autoscale_without_policy"
    DEAD_LETTER_MISSING_FAILURE_RECORD = "dead_letter_missing_failure_record"
    REPLAY_MISSING_SCALE_REFS = "replay_missing_scale_refs"


class QueueBrokerAdapterKind(StrEnum):
    REDIS = "redis"
    REDIS_CONTRACT = "redis_contract"
    EXTERNAL_BROKER = "external_broker"


class QueueBrokerCapability(StrEnum):
    ENQUEUE = "enqueue"
    LEASE = "lease"
    HEARTBEAT = "heartbeat"
    ACK = "ack"
    NACK = "nack"
    DEAD_LETTER = "dead_letter"
    FENCING_TOKEN = "fencing_token"
    VISIBILITY_TIMEOUT = "visibility_timeout"
    IDEMPOTENCY = "idempotency"
    FAIRNESS = "fairness"
    BACKPRESSURE = "backpressure"


class QueueBrokerOperation(StrEnum):
    ENQUEUE = "enqueue"
    DUPLICATE_ENQUEUE = "duplicate_enqueue"
    LEASE = "lease"
    HEARTBEAT = "heartbeat"
    ACK = "ack"
    NACK = "nack"
    DEAD_LETTER = "dead_letter"


class QueueBrokerConformanceFailureType(StrEnum):
    BROKER_MISSING_FENCING_TOKEN = "broker_missing_fencing_token"
    BROKER_MISSING_HEARTBEAT = "broker_missing_heartbeat"
    BROKER_MISSING_DEAD_LETTER = "broker_missing_dead_letter"


class PersistenceAdapterKind(StrEnum):
    REFERENCE_FILESYSTEM = "reference_filesystem"
    EXTERNAL_ADAPTER = "external_adapter"
    SQLITE = "sqlite"
    POSTGRES = "postgres"
    POSTGRES_CONTRACT = "postgres_contract"


class PersistenceCapability(StrEnum):
    METADATA_STORE = "metadata_store"
    EVENT_LOG = "event_log"
    OUTBOX = "outbox"
    ARTIFACT_INDEX = "artifact_index"
    QUEUE = "queue"


class PersistentQueueOperation(StrEnum):
    ENQUEUE = "enqueue"
    LEASE = "lease"
    HEARTBEAT = "heartbeat"
    ACK = "ack"
    NACK = "nack"
    DEAD_LETTER = "dead_letter"


class PersistenceFailureType(StrEnum):
    NON_ATOMIC_COMMIT = "non_atomic_commit"
    IDEMPOTENCY_NOT_PERSISTED = "idempotency_not_persisted"
    EVENT_LOG_GAP = "event_log_gap"
    OUTBOX_DISPATCH_MISSING = "outbox_dispatch_missing"
    ARTIFACT_INDEX_MISSING = "artifact_index_missing"
    LEASE_HEARTBEAT_MISSING = "lease_heartbeat_missing"


class PersistenceMigrationStatus(StrEnum):
    APPLIED = "applied"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


class PersistenceAdapterConformanceFailureType(StrEnum):
    ADAPTER_MISSING_CAPABILITY = "adapter_missing_capability"
    SQLITE_IDEMPOTENCY_GAP = "sqlite_idempotency_gap"
    SQLITE_EVENT_CURSOR_GAP = "sqlite_event_cursor_gap"
    SQLITE_OUTBOX_GAP = "sqlite_outbox_gap"
    SQLITE_MIGRATION_MISSING = "sqlite_migration_missing"


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


class PublicationFailureType(StrEnum):
    MISSING_EVIDENCE_ANCHOR = "missing_evidence_anchor"
    VERIFICATION_CONFLICT = "verification_conflict"
    PUBLICATION_POLICY_DENIED = "publication_policy_denied"
    REPLAY_GAP = "replay_gap"
    CANDIDATE_DIRECT_PUBLICATION = "candidate_direct_publication"
    REVIEW_NOT_ACCEPTED = "review_not_accepted"


class GraphNodeType(StrEnum):
    URL = "url"
    PAGE_TYPE = "page_type"
    TEMPLATE = "template"
    CANONICAL = "canonical"
    SOURCE_EVIDENCE = "source_evidence"
    ENTITY = "entity"
    TASK = "task"
    TEMPORAL_FACT = "temporal_fact"


class GraphEdgeType(StrEnum):
    HYPERLINK = "hyperlink"
    REDIRECT = "redirect"
    CANONICAL = "canonical"
    PAGE_STRUCTURE = "page_structure"
    SOURCE_EVIDENCE = "source_evidence"
    ENTITY_EVIDENCE = "entity_evidence"
    TASK_DEPENDENCY = "task_dependency"
    TEMPORAL_VALIDITY = "temporal_validity"


class GraphSignalType(StrEnum):
    FRONTIER_PRIORITY = "frontier_priority"
    REVIEW_ROUTE = "review_route"
    DEDUP_HINT = "dedup_hint"
    DRIFT_RISK = "drift_risk"
    QUALITY_WARNING = "quality_warning"


class ProjectionJobStatus(StrEnum):
    PLANNED = "planned"
    REBUILT = "rebuilt"
    MISMATCH = "mismatch"
    FAILED = "failed"


class GraphFailureType(StrEnum):
    MISSING_GRAPH_INPUT = "missing_graph_input"
    REBUILD_MISMATCH = "rebuild_mismatch"
    GRAPH_AS_EVIDENCE = "graph_as_evidence"
    MISSING_PROJECTION_WATERMARK = "missing_projection_watermark"
    PROJECTION_MISMATCH = "projection_mismatch"
    GRAPH_SIGNAL_AS_EVIDENCE = "graph_signal_as_evidence"


class MemoryType(StrEnum):
    SITE_BEHAVIOR = "site_behavior"
    PAGE_TYPE = "page_type"
    EXTRACTION_STRATEGY = "extraction_strategy"
    FAILURE_REPAIR = "failure_repair"
    TASK_CONTEXT = "task_context"
    AGENT_DIARY = "agent_diary"


class MemoryTrustLevel(StrEnum):
    TRUSTED = "trusted"
    UNTRUSTED = "untrusted"
    MIXED = "mixed"
    DERIVED = "derived"


class MemoryPromptUse(StrEnum):
    FORBIDDEN = "forbidden"
    SANITIZED_SUMMARY = "sanitized_summary"
    SCOPED_CONTEXT_REF = "scoped_context_ref"


class MemoryEventStatus(StrEnum):
    ACTIVE = "active"
    STALE = "stale"
    INVALIDATED = "invalidated"
    SUPERSEDED = "superseded"


class CrossScopeTunnelStatus(StrEnum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REVOKED = "revoked"
    EXPIRED = "expired"


class MemoryFailureType(StrEnum):
    MISSING_MEMORY_INPUT = "missing_memory_input"
    TAINTED_MEMORY_FOR_PROMPT = "tainted_memory_for_prompt"
    INVALIDATED_MEMORY_RETRIEVED = "invalidated_memory_retrieved"
    UNAUTHORIZED_CROSS_SCOPE_TUNNEL = "unauthorized_cross_scope_tunnel"
    MEMORY_AS_EVIDENCE = "memory_as_evidence"
    MISSING_REANCHOR_EVIDENCE = "missing_reanchor_evidence"
