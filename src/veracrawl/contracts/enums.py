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


class RunLifecycleAction(StrEnum):
    CREATE_OBJECTIVE = "create_objective"
    APPROVE_PLAN = "approve_plan"
    START_RUN = "start_run"
    PAUSE_RUN = "pause_run"
    RESUME_RUN = "resume_run"
    CANCEL_RUN = "cancel_run"
    FAIL_RUN = "fail_run"
    COMPLETE_RUN = "complete_run"


class ProductionRunControlFailureType(StrEnum):
    POLICY_DENIED = "production_run_control_policy_denied"
    MISSING_APPROVAL = "production_run_control_missing_approval"
    MISSING_BUDGET = "production_run_control_missing_budget"
    INVALID_TRANSITION = "production_run_control_invalid_transition"
    MISSING_REPLAY = "production_run_control_missing_replay"


class ProductionPersistenceFailureType(StrEnum):
    NON_ATOMIC_COMMIT = "production_persistence_non_atomic_commit"
    CANONICAL_STATE_MISSING = "production_persistence_canonical_state_missing"
    IDEMPOTENCY_MISSING = "production_persistence_idempotency_missing"
    EVENT_GAP = "production_persistence_event_gap"
    OUTBOX_MISSING = "production_persistence_outbox_missing"
    ARTIFACT_INDEX_MISSING = "production_persistence_artifact_index_missing"
    LEASE_HEARTBEAT_MISSING = "production_persistence_lease_heartbeat_missing"
    POLICY_MISSING = "production_persistence_policy_missing"
    REPLAY_MISSING = "production_persistence_replay_missing"


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


class RuntimeInfrastructureAdapterFamily(StrEnum):
    POSTGRES_PERSISTENCE = "postgres_persistence"
    REDIS_QUEUE_BROKER = "redis_queue_broker"
    S3_OBJECT_STORE = "s3_object_store"


class RuntimeInfrastructureFailureType(StrEnum):
    INFRASTRUCTURE_MISSING_PERSISTENCE_REFS = "infrastructure_missing_persistence_refs"
    INFRASTRUCTURE_MISSING_QUEUE_REFS = "infrastructure_missing_queue_refs"
    INFRASTRUCTURE_MISSING_OBJECT_REFS = "infrastructure_missing_object_refs"
    INFRASTRUCTURE_MISSING_REPLAY_REFS = "infrastructure_missing_replay_refs"


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
    MISSING_AGENT_MODEL_RUNTIME = "missing_agent_model_runtime"
    MISSING_LIVE_EVIDENCE = "missing_live_evidence"
    MISSING_TOOL_GATE = "missing_tool_gate"
    MISSING_OWNER_COMMAND = "missing_owner_command"
    MISSING_REPLAY_REFS = "missing_replay_refs"


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
    OBSERVABILITY_GAP = "observability_gap"
    REDACTION_VIOLATION = "redaction_violation"
    MISSING_REVIEW_EVIDENCE = "missing_review_evidence"
    UNRESOLVED_FAILURE_WITHOUT_RECOVERY = "unresolved_failure_without_recovery"
    STALE_DASHBOARD_PROJECTION = "stale_dashboard_projection"
    UNSAFE_RECOVERY_WITHOUT_REVIEW = "unsafe_recovery_without_review"


class DRRestorePhase(StrEnum):
    RESTORE_METADATA = "restore_metadata"
    RESTORE_ARTIFACTS = "restore_artifacts"
    REPLAY_EVENTS = "replay_events"
    REBUILD_PROJECTIONS = "rebuild_projections"
    RECONCILE_EXPORTS = "reconcile_exports"
    VALIDATE_REFERENCES = "validate_references"
    PUBLISH_REPORT = "publish_report"


class DRRestorePhaseStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DRRestoreRunStatus(StrEnum):
    PLANNED = "planned"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class DRRestoreFailureType(StrEnum):
    MISSING_METADATA_RESTORE_REFS = "dr_restore_missing_metadata_restore_refs"
    MISSING_ARTIFACT_REACHABILITY_REFS = "dr_restore_missing_artifact_reachability_refs"
    MISSING_EVENT_REPLAY_REFS = "dr_restore_missing_event_replay_refs"
    MISSING_PROJECTION_REBUILD_REFS = "dr_restore_missing_projection_rebuild_refs"
    MISSING_EXPORT_RECONCILIATION_REFS = "dr_restore_missing_export_reconciliation_refs"
    UNRESOLVED_REFS = "dr_restore_unresolved_refs"
    DATA_LOSS_DETECTED = "dr_restore_data_loss_detected"
    UNSAFE_RECOVERY_WITHOUT_APPROVAL = "dr_restore_unsafe_recovery_without_approval"


class ObservabilitySignalType(StrEnum):
    HEALTH = "health"
    SLO = "slo"
    COST = "cost"
    QUALITY = "quality"
    FAILURE = "failure"
    RECOVERY = "recovery"
    DR = "dr"


class ObservabilityMetricKind(StrEnum):
    GAUGE = "gauge"
    COUNTER = "counter"
    HISTOGRAM = "histogram"
    SLO = "slo"
    COST = "cost"
    QUALITY = "quality"


class TraceSpanKind(StrEnum):
    COMMAND = "command"
    EVENT = "event"
    ADAPTER = "adapter"
    AGENT = "agent"
    TOOL = "tool"
    QUEUE = "queue"
    ARTIFACT = "artifact"
    PROJECTION = "projection"
    EXPORT = "export"
    RECOVERY = "recovery"
    OBSERVABILITY = "observability"


class TraceSpanStatus(StrEnum):
    OK = "ok"
    ERROR = "error"
    NEEDS_REVIEW = "needs_review"


class AlertStatus(StrEnum):
    FIRING = "firing"
    RESOLVED = "resolved"
    NEEDS_REVIEW = "needs_review"


class RunbookActionStatus(StrEnum):
    RECOMMENDED = "recommended"
    APPROVED = "approved"
    EXECUTED = "executed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class ObservabilityFailureType(StrEnum):
    MISSING_METRIC_REFS = "observability_missing_metric_refs"
    MISSING_TRACE_REFS = "observability_missing_trace_refs"
    MISSING_ALERT_REFS = "observability_missing_alert_refs"
    MISSING_RUNBOOK_REFS = "observability_missing_runbook_refs"
    STALE_DASHBOARD_WATERMARK = "observability_stale_dashboard_watermark"
    MISSING_DR_REFS = "observability_missing_dr_refs"
    MISSING_REDACTION_REFS = "observability_missing_redaction_refs"
    MISSING_REPLAY_REFS = "observability_missing_replay_refs"
    SECRET_LEAK_DETECTED = "observability_secret_leak_detected"
    UNSAFE_RUNBOOK_WITHOUT_APPROVAL = "observability_unsafe_runbook_without_approval"


class SecurityActionSurface(StrEnum):
    NETWORK = "network"
    PROMPT = "prompt"
    CREDENTIAL = "credential"
    BROWSER = "browser"
    MEMORY = "memory"
    GRAPH = "graph"
    EXPORT = "export"
    RECOVERY = "recovery"
    ARTIFACT_LIFECYCLE = "artifact_lifecycle"


class SecurityCheckResult(StrEnum):
    ALLOW = "allow"
    BLOCK = "block"
    NEEDS_REVIEW = "needs_review"


class CredentialDeliveryMode(StrEnum):
    SCOPED_HEADER = "scoped_header"
    SCOPED_COOKIE = "scoped_cookie"
    REQUEST_SIGNING = "request_signing"
    VAULT_BROKERED_FORM_FILL = "vault_brokered_form_fill"


class ArtifactLifecycleOperation(StrEnum):
    CLASSIFY = "classify"
    REDACT = "redact"
    TOMBSTONE = "tombstone"
    DELETE = "delete"
    LEGAL_HOLD = "legal_hold"
    RETENTION = "retention"
    RELEASE_LEGAL_HOLD = "release_legal_hold"


class SecurityPrivacyFailureType(StrEnum):
    UNSAFE_NETWORK = "security_privacy_unsafe_network"
    PROMPT_INJECTION_TOOL_MISUSE = "security_privacy_prompt_injection_tool_misuse"
    CREDENTIAL_LEAKAGE = "security_privacy_credential_leakage"
    MISSING_LIFECYCLE_PROPAGATION = "security_privacy_missing_lifecycle_propagation"
    LEGAL_HOLD_DELETE = "security_privacy_legal_hold_delete"
    MISSING_PROJECTION_CLEANUP = "security_privacy_missing_projection_cleanup"
    MISSING_REDACTED_REPLAY = "security_privacy_missing_redacted_replay"
    MISSING_OBSERVABILITY_REFS = "security_privacy_missing_observability_refs"


class AgentAdapterFailureType(StrEnum):
    MISSING_RUNTIME_REFS = "agent_adapter_missing_runtime_refs"
    RAW_PROMPT_LEAK = "agent_adapter_raw_prompt_leak"
    RAW_RESPONSE_LEAK = "agent_adapter_raw_response_leak"
    FRAMEWORK_STATE_CANONICAL = "agent_adapter_framework_state_canonical"
    MISSING_MODEL_TRACE = "agent_adapter_missing_model_trace"
    MISSING_TOOL_TRACE = "agent_adapter_missing_tool_trace"
    MISSING_REPLAY_REFS = "agent_adapter_missing_replay_refs"
    MISSING_SECURITY_PRIVACY_REFS = "agent_adapter_missing_security_privacy_refs"
    UNSUPPORTED_FRAMEWORK = "agent_adapter_unsupported_framework"


class ModelProviderAdapterFailureType(StrEnum):
    MISSING_RUNTIME_REFS = "model_provider_adapter_missing_runtime_refs"
    RAW_PROMPT_LEAK = "model_provider_adapter_raw_prompt_leak"
    RAW_RESPONSE_LEAK = "model_provider_adapter_raw_response_leak"
    RAW_CREDENTIAL_LEAK = "model_provider_adapter_raw_credential_leak"
    PROVIDER_TRANSCRIPT_CANONICAL = "model_provider_adapter_provider_transcript_canonical"
    MISSING_CONTEXT_TRACE = "model_provider_adapter_missing_context_trace"
    MISSING_REPLAY_REFS = "model_provider_adapter_missing_replay_refs"
    MISSING_SECURITY_PRIVACY_REFS = "model_provider_adapter_missing_security_privacy_refs"
    UNSAFE_TOOL_SUGGESTION = "model_provider_adapter_unsafe_tool_suggestion"
    UNSUPPORTED_PROVIDER = "model_provider_adapter_unsupported_provider"


class AgentModelAdapterRuntimeFailureType(StrEnum):
    MISSING_RUN_CONTROL = "agent_model_adapter_missing_run_control"
    MISSING_LIVE_NORMALIZATION = "agent_model_adapter_missing_live_normalization"
    MISSING_SCHEMA_EXTRACTION = "agent_model_adapter_missing_schema_extraction"
    ADAPTER_RUNTIME_UNAVAILABLE = "agent_model_adapter_runtime_unavailable"
    UNSUPPORTED_PROVIDER = "agent_model_adapter_unsupported_provider"
    UNSUPPORTED_FRAMEWORK = "agent_model_adapter_unsupported_framework"
    RAW_PROMPT_LEAK = "agent_model_adapter_raw_prompt_leak"
    RAW_RESPONSE_LEAK = "agent_model_adapter_raw_response_leak"
    RAW_CREDENTIAL_LEAK = "agent_model_adapter_raw_credential_leak"
    FRAMEWORK_STATE_CANONICAL = "agent_model_adapter_framework_state_canonical"
    PROVIDER_TRANSCRIPT_CANONICAL = "agent_model_adapter_provider_transcript_canonical"
    MISSING_MODEL_TRACE = "agent_model_adapter_missing_model_trace"
    MISSING_TOOL_TRACE = "agent_model_adapter_missing_tool_trace"
    MISSING_CONTEXT_TRACE = "agent_model_adapter_missing_context_trace"
    MISSING_REPLAY_REFS = "agent_model_adapter_missing_replay_refs"
    CORE_IMPORT_BOUNDARY = "agent_model_adapter_core_import_boundary"


class SourceCoverageFailureType(StrEnum):
    MISSING_RUNTIME_REFS = "source_coverage_missing_runtime_refs"
    ADAPTER_NATIVE_STATE_CANONICAL = "source_coverage_adapter_native_state_canonical"
    RAW_SECRET_LEAK = "source_coverage_raw_secret_leak"
    MISSING_BROWSER_REFS = "source_coverage_missing_browser_refs"
    MISSING_CREDENTIAL_AUDIT = "source_coverage_missing_credential_audit"
    MISSING_DOCUMENT_ARTIFACT = "source_coverage_missing_document_artifact"
    MISSING_API_PAYLOAD = "source_coverage_missing_api_payload"
    MISSING_REPLAY_REFS = "source_coverage_missing_replay_refs"
    UNSAFE_BROWSER_SIDE_EFFECT = "source_coverage_unsafe_browser_side_effect"
    UNSUPPORTED_ADAPTER = "source_coverage_unsupported_adapter"


class DynamicSourceRuntimeFailureType(StrEnum):
    MISSING_RUNTIME_REFS = "dynamic_source_runtime_missing_runtime_refs"
    ADAPTER_NATIVE_STATE_CANONICAL = "dynamic_source_runtime_adapter_state_canonical"
    RAW_SECRET_LEAK = "dynamic_source_runtime_raw_secret_leak"
    MISSING_CREDENTIAL_AUDIT = "dynamic_source_runtime_missing_credential_audit"
    MISSING_DOCUMENT_ARTIFACT = "dynamic_source_runtime_missing_document_artifact"
    MISSING_API_PAYLOAD = "dynamic_source_runtime_missing_api_payload"
    MISSING_REPLAY_REFS = "dynamic_source_runtime_missing_replay_refs"
    UNSAFE_BROWSER_SIDE_EFFECT = "dynamic_source_runtime_unsafe_browser_side_effect"
    UNSUPPORTED_ADAPTER = "dynamic_source_runtime_unsupported_adapter"


class StructuredSourceAdapterFailureType(StrEnum):
    POLICY_DENIED = "structured_source_policy_denied"
    MALFORMED_SOURCE = "structured_source_malformed_source"
    UNSUPPORTED_ADAPTER = "structured_source_unsupported_adapter"
    REPLAY_MISMATCH = "structured_source_replay_mismatch"
    MISSING_ARTIFACT = "structured_source_missing_artifact"


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
    RESTORE_OBSERVABILITY_SIGNAL = "restore_observability_signal"
    REFRESH_DASHBOARD_PROJECTION = "refresh_dashboard_projection"
    REDACT_SENSITIVE_CONTEXT = "redact_sensitive_context"
    RUN_OBSERVABILITY_RUNBOOK = "run_observability_runbook"
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


class LiveHttpAcquisitionFailureType(StrEnum):
    POLICY_DENIED = "live_http_policy_denied"
    PRIVATE_NETWORK_DENIED = "live_http_private_network_denied"
    MALFORMED_RESPONSE = "live_http_malformed_response"
    MISSING_ARTIFACT = "live_http_missing_artifact"
    REPLAY_MISMATCH = "live_http_replay_mismatch"
    DIRECT_SOURCE_BYPASS = "live_http_direct_source_bypass"
    ADAPTER_UNAVAILABLE = "live_http_adapter_unavailable"
    NETWORK_FAILURE = "live_http_network_failure"


class BrowserSnapshotFailureType(StrEnum):
    POLICY_DENIED = "browser_snapshot_policy_denied"
    EGRESS_DENIED = "browser_snapshot_egress_denied"
    UNSAFE_INTERACTION = "browser_snapshot_unsafe_interaction"
    BUDGET_EXCEEDED = "browser_snapshot_budget_exceeded"
    PROMPT_TAINTED_CONTENT = "browser_snapshot_prompt_tainted_content"
    MISSING_ARTIFACT = "browser_snapshot_missing_artifact"
    REPLAY_MISMATCH = "browser_snapshot_replay_mismatch"
    ADAPTER_UNAVAILABLE = "browser_snapshot_adapter_unavailable"


class CredentialedSessionFailureType(StrEnum):
    POLICY_DENIED = "credentialed_session_policy_denied"
    MISSING_AUTHORIZATION = "credentialed_session_missing_authorization"
    OUT_OF_SCOPE = "credentialed_session_out_of_scope"
    RAW_SECRET_LEAK = "credentialed_session_raw_secret_leak"
    UNSAFE_CREDENTIAL_USE = "credentialed_session_unsafe_credential_use"
    MISSING_AUDIT = "credentialed_session_missing_audit"
    MISSING_REDACTED_REPLAY = "credentialed_session_missing_redacted_replay"
    REPLAY_MISMATCH = "credentialed_session_replay_mismatch"
    ADAPTER_UNAVAILABLE = "credentialed_session_adapter_unavailable"


class LiveNormalizationFailureType(StrEnum):
    MISSING_UPSTREAM = "live_normalization_missing_upstream"
    EMPTY_CONTENT = "live_normalization_empty_content"
    MISSING_ANCHOR_MAP = "live_normalization_missing_anchor_map"
    MISSING_SITE_MODEL = "live_normalization_missing_site_model"
    REPLAY_MISMATCH = "live_normalization_replay_mismatch"
    NORMALIZATION_FAILED = "live_normalization_failed"


class SchemaExtractionFailureType(StrEnum):
    MISSING_LIVE_NORMALIZATION = "schema_extraction_missing_live_normalization"
    SCHEMA_VALIDATION_FAILED = "schema_extraction_schema_validation_failed"
    MISSING_FIELD_ANCHOR = "schema_extraction_missing_field_anchor"
    MISSING_MODEL_TOOL_TRACE = "schema_extraction_missing_model_tool_trace"
    CANDIDATE_DIRECT_PUBLICATION = "schema_extraction_candidate_direct_publication"
    DRIFT_REPAIR_REQUIRED = "schema_extraction_drift_repair_required"
    REPLAY_MISMATCH = "schema_extraction_replay_mismatch"
    EXTRACTION_FAILED = "schema_extraction_failed"


class LiveEvidenceVerificationFailureType(StrEnum):
    MISSING_SCHEMA_EXTRACTION = "live_evidence_missing_schema_extraction"
    MISSING_SOURCE_ANCHOR = "live_evidence_missing_source_anchor"
    STALE_EVIDENCE = "live_evidence_stale_evidence"
    CONTRADICTORY_EVIDENCE = "live_evidence_contradictory_evidence"
    GRAPH_ONLY_EVIDENCE = "live_evidence_graph_only_evidence"
    MEMORY_ONLY_EVIDENCE = "live_evidence_memory_only_evidence"
    VERIFICATION_CONFLICT = "live_evidence_verification_conflict"
    PUBLICATION_GATE_BYPASS = "live_evidence_publication_gate_bypass"
    REPLAY_MISMATCH = "live_evidence_replay_mismatch"
    EVIDENCE_BUILD_FAILED = "live_evidence_build_failed"


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


class ResultPublicationExportFailureType(StrEnum):
    MISSING_LIVE_EVIDENCE = "result_publication_missing_live_evidence"
    PUBLICATION_POLICY_DENIED = "result_publication_policy_denied"
    VERIFICATION_NOT_ACCEPTED = "result_publication_verification_not_accepted"
    MISSING_OUTPUT_MANIFEST = "result_publication_missing_output_manifest"
    EXPORT_MISSING_RECEIPT = "result_publication_export_missing_receipt"
    WITHDRAWAL_MISSING_PROPAGATION = "result_publication_withdrawal_missing_propagation"
    CORRECTION_WITHOUT_WITHDRAWAL = "result_publication_correction_without_withdrawal"
    PRIVACY_MISSING = "result_publication_privacy_missing"
    DIRECT_EXPORT_BYPASS = "result_publication_direct_export_bypass"
    REPLAY_MISMATCH = "result_publication_replay_mismatch"


class TargetOutputType(StrEnum):
    RECORD = "record"
    TABLE = "table"
    DOCUMENT_METADATA = "document_metadata"
    DOCUMENT = "document"
    FILE = "file"
    DATASET = "dataset"
    FACT = "fact"


class TargetWebsitePattern(StrEnum):
    STATIC = "static"
    SITEMAP_RSS_FEED = "sitemap_rss_feed"
    LISTING_DETAIL = "listing_detail"
    SEARCH = "search"
    NON_DESTRUCTIVE_FORMS = "non_destructive_forms"
    JAVASCRIPT_PAGES = "javascript_pages"
    AUTHENTICATED_SOURCES = "authenticated_sources"
    API_LIKE_ENDPOINTS = "api_like_endpoints"
    DOCUMENTS = "documents"
    MULTI_LANGUAGE_PAGES = "multi_language_pages"
    DRIFTED_SITES = "drifted_sites"
    HIGH_VOLUME_SITES = "high_volume_sites"


class OutputTypeCoverageFailureType(StrEnum):
    MISSING_RUNTIME_REFS = "output_type_coverage_missing_runtime_refs"
    MISSING_OUTPUT_TYPE = "output_type_coverage_missing_output_type"
    UNSUPPORTED_OUTPUT_TYPE = "output_type_coverage_unsupported_output_type"
    DERIVED_CONTEXT_AS_EVIDENCE = "output_type_coverage_derived_context_as_evidence"
    CANDIDATE_AS_EVIDENCE = "output_type_coverage_candidate_as_evidence"
    GRAPH_AS_EVIDENCE = "output_type_coverage_graph_as_evidence"
    MEMORY_AS_EVIDENCE = "output_type_coverage_memory_as_evidence"
    AGENT_REASONING_AS_EVIDENCE = "output_type_coverage_agent_reasoning_as_evidence"
    TEMPORAL_KG_AS_EVIDENCE = "output_type_coverage_temporal_kg_as_evidence"
    MISSING_TABLE_CELL_EVIDENCE = (
        "output_type_coverage_missing_table_cell_evidence"
    )
    MISSING_FILE_LIFECYCLE = "output_type_coverage_missing_file_lifecycle"
    MISSING_DATASET_ITEM_EVIDENCE = (
        "output_type_coverage_missing_dataset_item_evidence"
    )
    MISSING_FACT_VERIFICATION = "output_type_coverage_missing_fact_verification"
    MISSING_REPLAY_REFS = "output_type_coverage_missing_replay_refs"


class WebsitePatternCoverageFailureType(StrEnum):
    MISSING_RUNTIME_REFS = "website_pattern_missing_runtime_refs"
    MISSING_PATTERN = "website_pattern_missing_pattern"
    UNSUPPORTED_PATTERN = "website_pattern_unsupported_pattern"
    SINGLE_SITE_ASSUMPTION = "website_pattern_single_site_assumption"
    SCAFFOLD_ONLY = "website_pattern_scaffold_only"
    MISSING_SOURCE_ADAPTER = "website_pattern_missing_source_adapter"
    MISSING_SITE_MODEL = "website_pattern_missing_site_model"
    MISSING_OUTPUT_EVIDENCE = "website_pattern_missing_output_evidence"
    MISSING_PATTERN_SPECIFIC_REFS = "website_pattern_missing_pattern_specific_refs"
    UNSAFE_INTERACTION = "website_pattern_unsafe_interaction"
    MISSING_REPLAY_REFS = "website_pattern_missing_replay_refs"


class TargetProductWorkflow(StrEnum):
    MULTI_SITE_ONBOARDING = "multi_site_onboarding"
    OBJECTIVE_TO_PLAN_APPROVAL = "objective_to_plan_approval"
    DYNAMIC_AUTH_DOCUMENT_API_CRAWL = "dynamic_auth_document_api_crawl"
    EVIDENCE_REVIEW = "evidence_review"
    CONFLICT_RESOLUTION = "conflict_resolution"
    DRIFT_REPAIR = "drift_repair"
    MEMORY_REUSE = "memory_reuse"
    EXPORT_AND_WITHDRAWAL = "export_and_withdrawal"
    REPLAY_AND_AUDIT = "replay_and_audit"
    OPERATOR_RECOVERY = "operator_recovery"


class MinimumProductGate(StrEnum):
    APPROVED_PLAN_CREATION = "approved_plan_creation"
    REVIEWER_TIME_PER_OUTPUT = "reviewer_time_per_output"
    DRIFT_REPAIR_SUCCESS = "drift_repair_success"
    OPERATOR_RECOVERY_COMPLETION = "operator_recovery_completion"
    EXPORT_WITHDRAWAL_RECONCILIATION = "export_withdrawal_reconciliation"
    USER_FACING_STATUS_ACCURACY = "user_facing_status_accuracy"
    BUYER_VALUE_WORKFLOW_PASS = "buyer_value_workflow_pass"


class ProductAcceptanceFailureType(StrEnum):
    MISSING_RUNTIME_REFS = "product_acceptance_missing_runtime_refs"
    MISSING_WORKFLOW = "product_acceptance_missing_workflow"
    MISSING_MINIMUM_GATE = "product_acceptance_missing_minimum_gate"
    MISSING_EVIDENCE = "product_acceptance_missing_evidence"
    MISSING_REPLAY = "product_acceptance_missing_replay"
    MISSING_OPERATOR_VISIBILITY = "product_acceptance_missing_operator_visibility"
    MISSING_POLICY = "product_acceptance_missing_policy"
    MISSING_WORKFLOW_SPECIFIC_REFS = (
        "product_acceptance_missing_workflow_specific_refs"
    )
    SCAFFOLD_ONLY = "product_acceptance_scaffold_only"
    CONTRACT_ONLY = "product_acceptance_contract_only"
    FALSE_COMPLETE_STATUS = "product_acceptance_false_complete_status"
    DEGRADED_OPERATIONAL = "product_acceptance_degraded_operational"
    MISSING_EXPORT_RECONCILIATION = (
        "product_acceptance_missing_export_reconciliation"
    )


class TargetRuntimeStatus(StrEnum):
    COMPLETE = "complete"
    NEEDS_REVIEW = "needs_review"
    BLOCKED = "blocked"
    FAILED = "failed"


class TargetRuntimeFailureType(StrEnum):
    POLICY_DENIED = "target_runtime_policy_denied"
    PROMPT_INJECTION = "target_runtime_prompt_injection"
    MISSING_EVIDENCE = "target_runtime_missing_evidence"
    REPLAY_MISMATCH = "target_runtime_replay_mismatch"
    PARTIAL_EXPORT = "target_runtime_partial_export"
    FALSE_COMPLETE = "target_runtime_false_complete"
    DRIFT_REPAIR_REQUIRED = "target_runtime_drift_repair_required"
    ORACLE_MISMATCH = "target_runtime_oracle_mismatch"
    ADAPTER_RESULT_MISSING = "target_runtime_adapter_result_missing"
    ADAPTER_OUTPUT_MISMATCH = "target_runtime_adapter_output_mismatch"
    DIRECT_SOURCE_BYPASS = "target_runtime_direct_source_bypass"
    PROCESSING_MISSING = "target_runtime_processing_missing"
    EVIDENCE_MISSING = "target_runtime_evidence_missing"
    PUBLICATION_BYPASS = "target_runtime_publication_bypass"
    DERIVED_CONTEXT_AS_EVIDENCE = "target_runtime_derived_context_as_evidence"


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


class GraphFrontierDecisionType(StrEnum):
    PRIORITIZE = "prioritize"
    RETRY = "retry"
    RETIRE = "retire"
    EXPAND = "expand"


class GraphReviewRouteType(StrEnum):
    ROUTE_TO_REVIEW = "route_to_review"
    ESCALATE = "escalate"
    REQUIRE_MORE_EVIDENCE = "require_more_evidence"


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


class GraphFrontierReviewFailureType(StrEnum):
    MISSING_RUNTIME_REFS = "graph_frontier_review_missing_runtime_refs"
    GRAPH_SIGNAL_AS_EVIDENCE = "graph_frontier_review_signal_as_evidence"
    MISSING_SOURCE_GRAPH_REFS = "graph_frontier_review_missing_source_graph_refs"
    MISSING_EXPLANATION_REF = "graph_frontier_review_missing_explanation_ref"
    UNAUTHORIZED_FRONTIER_MUTATION = "graph_frontier_review_unauthorized_frontier_mutation"
    MISSING_REVIEW_ROUTE = "graph_frontier_review_missing_review_route"
    MISSING_REPLAY_REFS = "graph_frontier_review_missing_replay_refs"
    UNSUPPORTED_SIGNAL = "graph_frontier_review_unsupported_signal"


class TemporalKGEntityType(StrEnum):
    PERSON = "person"
    ORGANIZATION = "organization"
    PRODUCT = "product"
    ARTICLE = "article"
    EVENT = "event"
    LOCATION = "location"
    DOCUMENT = "document"
    CLAIM = "claim"
    OTHER = "other"


class TemporalKGStatus(StrEnum):
    CURRENT = "current"
    SUPERSEDED = "superseded"
    EXPIRED = "expired"
    DISPUTED = "disputed"
    INVALIDATED = "invalidated"


class TemporalKGConflictType(StrEnum):
    FALSE_MERGE = "false_merge"
    FALSE_SPLIT = "false_split"
    CONTRADICTION = "contradiction"
    IDENTITY_DRIFT = "identity_drift"


class TemporalKGAdjudicationDecisionType(StrEnum):
    CONFIRM_IDENTITY = "confirm_identity"
    SPLIT_IDENTITY = "split_identity"
    MERGE_IDENTITY = "merge_identity"
    INVALIDATE_IDENTITY = "invalidate_identity"
    SUPERSEDE_PROJECTION = "supersede_projection"
    DISPUTE_PROJECTION = "dispute_projection"


class TemporalKGFailureType(StrEnum):
    MISSING_RUNTIME_REFS = "temporal_kg_missing_runtime_refs"
    PROVISIONAL_IDENTITY = "temporal_kg_provisional_identity"
    PROJECTION_AS_EVIDENCE = "temporal_kg_projection_as_evidence"
    MISSING_IDENTITY_EVIDENCE = "temporal_kg_missing_identity_evidence"
    MISSING_CANONICAL_SOURCES = "temporal_kg_missing_canonical_sources"
    MISSING_BITEMPORAL_REFS = "temporal_kg_missing_bitemporal_refs"
    FALSE_MERGE_WITHOUT_ADJUDICATION = (
        "temporal_kg_false_merge_without_adjudication"
    )
    FALSE_SPLIT_WITHOUT_SUPERSESSION = "temporal_kg_false_split_without_supersession"
    MISSING_REPLAY_REFS = "temporal_kg_missing_replay_refs"


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


class GraphMemoryProductionFailureType(StrEnum):
    MISSING_LIVE_NORMALIZATION = "graph_memory_missing_live_normalization"
    MISSING_LIVE_EVIDENCE = "graph_memory_missing_live_evidence"
    MISSING_MULTI_AGENT_REPAIR = "graph_memory_missing_multi_agent_repair"
    MISSING_GRAPH_PROJECTION = "graph_memory_missing_graph_projection"
    MISSING_TEMPORAL_KG = "graph_memory_missing_temporal_kg"
    MISSING_MEMORY_KERNEL = "graph_memory_missing_memory_kernel"
    MISSING_FRONTIER_EXPLANATION = "graph_memory_missing_frontier_explanation"
    MISSING_REPAIR_EXPLANATION = "graph_memory_missing_repair_explanation"
    MISSING_INVALIDATION_REF = "graph_memory_missing_invalidation_ref"
    GRAPH_AS_EVIDENCE = "graph_memory_graph_as_evidence"
    MEMORY_AS_EVIDENCE = "graph_memory_memory_as_evidence"
    STALE_MEMORY_USED = "graph_memory_stale_memory_used"
    REPLAY_MISMATCH = "graph_memory_replay_mismatch"
