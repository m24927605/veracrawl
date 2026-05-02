# Contract: Runtime Spine

## Purpose

Define the deterministic objective-to-output runtime contract for the first target core runtime spine.

## Runtime Profile

- Profile ID: `runtime-record-success`
- Source profile: fetch-like local deterministic source
- Output profile: record output with field-level evidence
- Store profile: in-memory canonical repositories behind ports
- Artifact profile: fixture-run artifact store with content hashes
- Agent profile: no external agent framework required for success path

## Required Flow

1. Create or load approved `CrawlObjective`.
2. Propose and approve `CrawlPlan`.
3. Start `CrawlRun` and create immutable `RunPlanSnapshot`.
4. Execute source adapter command through source adapter port.
5. Record `SourceAdapterResult` and raw `RuntimeArtifactRef`.
6. Normalize raw artifact into `NormalizedDocument` with anchor map refs.
7. Create `ExtractionCandidate` with schema-bound field anchors.
8. Build `EvidencePacket` and coverage result.
9. Create `VerificationDecision`.
10. Publish `PublishedOutput` and immutable `OutputManifest`.
11. Build `ReplayBundleManifest`.
12. Evaluate runtime completion gates.

## Required Results

The successful profile must emit:

- command results for every mutating action
- crawl run events for every state transition
- policy decisions for source, adapter, evidence, verification, and publication gates where applicable
- artifact refs with hashes
- evidence packet refs for every required output field
- verification decision refs
- output manifest hash
- replay bundle manifest with zero missing required refs

## Prohibited Behavior

- Direct mutation by source adapters, agents, framework adapters, or fixture harness code.
- Publication from extraction candidates without evidence and verification.
- Core imports of concrete agent frameworks, browser libraries, storage clients, queue clients, model SDKs, or site-specific scrapers.
- Treating graph, memory, or agent reasoning refs as source evidence.
