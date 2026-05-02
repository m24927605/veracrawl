"""Public foundation contract exports."""

from veracrawl.contracts.agent import (
    AgentActionTrace,
    AgentRecommendation,
    AgentRunRequest,
    AgentRunResult,
    AgentRuntimeSpec,
    AgentToolSpec,
    ContextBundle,
    ContextBundleTrace,
    ContextRef,
    ModelCallTrace,
    ModelRequest,
    ModelResponse,
    ToolCallTrace,
)
from veracrawl.contracts.artifact import RuntimeArtifactRef
from veracrawl.contracts.command import (
    BaseCommandPayload,
    CommandEnvelope,
    CommandResult,
    CommandTypeSpec,
)
from veracrawl.contracts.event import CrawlRunEvent, EventCursor, EventTypeSpec
from veracrawl.contracts.evidence import EvidenceCoverageResult, EvidencePacket
from veracrawl.contracts.fixture import (
    BenchmarkFixtureManifest,
    DRRestoreOracle,
    ExpectedEventSequenceOracle,
    ExpectedEvidenceCoverageOracle,
    ExpectedGraphOracle,
    ExpectedOutputOracle,
    FailureInjectionPlan,
    ReplayBundleOracle,
    ThresholdSpec,
)
from veracrawl.contracts.objective import (
    CrawlObjective,
    CrawlPlan,
    CrawlRun,
    RunPlanSnapshot,
    RuntimeCompletionGate,
)
from veracrawl.contracts.policy import BlockedActionReport, PolicyDecision
from veracrawl.contracts.processing import ExtractionCandidate, NormalizedDocument
from veracrawl.contracts.publication import OutputManifest, PublishedOutput
from veracrawl.contracts.registry import registry_json, validate_registry
from veracrawl.contracts.replay import ReplayBundleManifest, ReplayValidationReport
from veracrawl.contracts.source_adapter import (
    SourceAdapterCommand,
    SourceAdapterResult,
    SourceAdapterSpec,
)
from veracrawl.contracts.verification import VerificationDecision

__all__ = [
    "AgentActionTrace",
    "AgentRecommendation",
    "AgentRunRequest",
    "AgentRunResult",
    "AgentRuntimeSpec",
    "AgentToolSpec",
    "BaseCommandPayload",
    "BenchmarkFixtureManifest",
    "BlockedActionReport",
    "CommandEnvelope",
    "CommandResult",
    "CommandTypeSpec",
    "ContextBundle",
    "ContextBundleTrace",
    "ContextRef",
    "CrawlObjective",
    "CrawlPlan",
    "CrawlRun",
    "CrawlRunEvent",
    "DRRestoreOracle",
    "EventCursor",
    "EventTypeSpec",
    "ExpectedEventSequenceOracle",
    "ExpectedEvidenceCoverageOracle",
    "ExpectedGraphOracle",
    "ExpectedOutputOracle",
    "EvidenceCoverageResult",
    "EvidencePacket",
    "ExtractionCandidate",
    "FailureInjectionPlan",
    "ModelCallTrace",
    "ModelRequest",
    "ModelResponse",
    "NormalizedDocument",
    "OutputManifest",
    "PolicyDecision",
    "PublishedOutput",
    "ReplayBundleManifest",
    "ReplayBundleOracle",
    "ReplayValidationReport",
    "RunPlanSnapshot",
    "RuntimeArtifactRef",
    "RuntimeCompletionGate",
    "SourceAdapterCommand",
    "SourceAdapterResult",
    "SourceAdapterSpec",
    "ThresholdSpec",
    "ToolCallTrace",
    "VerificationDecision",
    "registry_json",
    "validate_registry",
]
