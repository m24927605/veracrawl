# Agent System Design

## Purpose

VeraCrawl is an AI-native crawler. Agents are not an optional assistant layer; they are the mechanism that turns high-level crawl objectives into adaptive, observable crawl execution.

Agents should help with objective interpretation, site understanding, crawl planning, frontier control, extraction assistance, evidence requests, drift repair, memory use, and operational reasoning. Agents should not be allowed to directly mutate core data stores without controlled tools and audit events.

## Agent Team

V1 should not require every agent below to operate as an independent autonomous service.

V1 agents:

- Planner Agent in a constrained objective-to-plan loop.
- Site Understanding Agent for first-pass page type and template analysis.
- Extractor Agent for candidate creation and evidence anchor proposals.
- Verifier Agent only as a recommendation helper behind the verification service.

V1 memory rule:

- V1 agents may read current run context, approved objective, approved plan, snapshots, normalized documents, and previous run reports.
- Long-term site/page/extraction memory is disabled until the Memory Kernel phase provides scoped retrieval, freshness, invalidation, and trust metadata.
- V1 may emit run diary events for replay, but those diary events are not planning priors until promoted by the Memory Kernel.

Later agents:

- Frontier Agent for adaptive graph-driven scheduling.
- Fetch Analysis Agent for production failure clustering.
- Drift Agent for automated repair loops.
- Memory Agent for long-term site learning beyond simple run diaries.
- Ops Agent for production health recommendations.

### Planner Agent

Responsibilities:

- interpret natural-language crawl objectives
- read job spec
- inspect prior site memory after Memory Kernel is enabled
- inspect graph summaries
- propose crawl strategy
- select source adapters
- define initial frontier seeds
- request schema-specific extraction plans
- define expected evidence requirements

Inputs:

- user objective
- JobSpec
- previous run report
- graph summary
- schema registry

Outputs:

- crawl strategy
- crawl plan
- frontier seed plan
- expected page types
- expected evidence requirements
- risk notes

### Site Understanding Agent

Responsibilities:

- infer website navigation structure
- identify listing, detail, search, document, pagination, and API-like pages
- group page templates
- propose crawl path expansions
- identify low-value or duplicate zones
- summarize site-specific crawl constraints

Inputs:

- seed snapshots
- normalized documents
- URL graph
- page structure graph
- prior site memory after Memory Kernel is enabled
- crawl objective

Outputs:

- site model
- page type hypotheses
- crawl path recommendations
- template cluster notes
- uncertainty notes

### Frontier Agent

Responsibilities:

- review frontier health
- adjust priority rules
- identify high-value graph zones
- recommend recrawl targets
- detect duplicate or low-value URL zones

Inputs:

- frontier state
- URL graph
- freshness lag
- quality targets
- run budget

Outputs:

- priority adjustments
- retirement recommendations
- discovery expansion recommendations

### Fetch Analysis Agent

Responsibilities:

- inspect fetch failure clusters
- identify whether failures are transient, configuration-related, or source-related
- recommend adapter changes
- summarize HTTP and rendering issues

Inputs:

- fetch metrics
- response metadata
- worker logs
- adapter config

Outputs:

- failure classification
- retry recommendations
- operator review items

### Extractor Agent

Responsibilities:

- classify page type
- propose extraction candidates
- map content to schema fields
- propose schema fields when the objective is exploratory
- identify uncertain fields
- request additional evidence where needed

Inputs:

- normalized document
- page type memory after Memory Kernel is enabled
- schema definition
- evidence anchors

Outputs:

- extraction candidates
- field confidence
- evidence anchor candidates
- schema mapping notes

### Verifier Agent

Responsibilities:

- evaluate evidence packets
- compare candidates against schema constraints
- compare against current run evidence and allowed prior verified output refs
- compare against temporal KG only after Phase 4 projection is enabled, never as a V1 acceptance dependency
- identify contradictions
- recommend accept/reject/review decisions with reasons

Inputs:

- evidence packet
- schema rules
- current run context
- prior verified output refs allowed by publication policy
- temporal KG after Phase 4 only

Outputs:

- verification recommendation
- rejection reason
- contradiction record
- review queue item

### Drift Agent

Responsibilities:

- detect page template changes
- detect selector decay
- detect field distribution changes
- detect entity graph changes
- recommend schema or adapter updates
- propose repair plans for failed extraction paths

Inputs:

- prior snapshots
- current snapshots
- extraction success metrics
- graph deltas

Outputs:

- drift event
- severity
- affected schemas
- proposed remediation
- repair recommendation

### Memory Agent

Responsibilities:

- write important events to memory
- update site essential story
- maintain closets
- propose temporal KG updates from verified outputs
- invalidate stale memories
- create cross-site tunnels

Inputs:

- run events
- verified outputs
- drift events
- agent diaries
- graph deltas

Outputs:

- memory events
- KG update recommendations
- diary entries
- tunnel updates

### Ops Agent

Responsibilities:

- watch production metrics
- detect abnormal cost or failure rate
- summarize run health
- recommend pause, retry, or review
- generate operator reports

Inputs:

- metrics
- traces
- queue state
- cost state
- quality reports

Outputs:

- health summary
- alerts
- action recommendations

## Agent Runtime Abstraction

VeraCrawl agents are product roles and runtime contracts, not bindings to a specific agent framework.

Implementation requirements:

- The implementation language is Python.
- The core agent runtime must be a VeraCrawl-owned abstraction.
- Agent roles, tools, permissions, context refs, policy checks, event logging, and replay behavior must be represented by VeraCrawl contracts.
- External agent frameworks or model SDKs may only appear behind adapters.
- Agent framework objects must not be persisted, emitted as canonical events, or passed into worker internals.
- Tool calls must use VeraCrawl `CommandEnvelope`, `AgentToolSpec`, policy decisions, and typed results rather than framework-native tool state.
- The V1 agent loop should be directly understandable and testable without starting an external agent framework runtime.

Adapter boundary:

```text
VeraCrawl Agent Runtime
  -> AgentRuntimePort
  -> ModelProviderAdapter or optional AgentFrameworkAdapter
  -> provider/framework-specific SDK
```

Only `AgentRuntimePort` is visible to core planning, extraction, verification, policy, and replay code. Provider-specific and framework-specific packages live at the outer edge and can be replaced without changing data contracts or persisted event semantics.

## Tooling Rule

Agents should operate through explicit tools:

- interpret objective
- propose crawl plan
- search memory
- read drawer
- read snapshot
- query graph
- query KG
- classify page type
- create candidate
- build evidence packet
- recommend verification decision
- propose extraction repair
- write diary entry
- request frontier update
- create review item

Agents should not receive direct database credentials or unrestricted execution access.

## Permission Matrix

Agent permissions should be role and tool specific:

```text
Planner Agent: propose plans, read policy snapshots, read approved memory, create review items.
Site Understanding Agent: read snapshots, query graph, propose site model updates.
Frontier Agent: recommend priority changes; scheduler applies approved transitions.
Extractor Agent: create candidates and evidence anchor candidates.
Verifier Agent: create verification recommendations, not final accept decisions.
Drift Agent: propose repair plans and review items.
Memory Agent: write memory events and retrieval indexes, not authoritative facts.
Ops Agent: recommend pause/retry/review; control plane applies approved actions.
```

Agents may initiate processing work through tools, but durable mutations must be applied by the owning service after policy checks. Agents must not own publication tasks, credential use, or direct fact/output writes.

## Prompt Injection Boundary

All web-derived text, DOM, scripts, metadata, and linked documents are untrusted input.

Rules:

- web-derived instructions must not override system, policy, or user instructions
- untrusted content must be labeled before entering prompts
- prompts should use sanitized context refs instead of raw secrets or credentials
- mutating tools must reject requests caused only by untrusted page content
- tool gateway decisions must emit policy events
- agent output must be validated against tool output schemas before persistence

## V1 Coordination Flow

```text
User Objective
  -> Planner Agent interprets objective and creates crawl strategy
  -> Site Understanding Agent models site structure
  -> Scheduler service schedules approved frontier work
  -> Fetch workers observe sources
  -> Extractor Agent creates candidates
  -> Verifier Agent recommends verification outcomes
  -> Verification service or reviewer accepts/rejects candidates
  -> Run diary records durable learning
  -> Minimal review/replay surface reports health and decisions
```

Full target coordination after advanced orchestration:

```text
Planner / Site Understanding / Frontier / Fetch Analysis / Extractor / Verifier / Drift / Memory / Ops agents
  -> coordinate through approved tools, policy decisions, and replayable events
```

## Memory Usage

This section applies after the Memory Kernel phase is enabled.

Agents should use memory progressively:

- L0 always loaded
- L1 loaded per project/site
- L2 retrieved per current task
- L3 only for deep cross-run or cross-site search

This prevents context bloat while preserving deep recall.

## Replay Requirement

Every agent action should produce a replayable event:

- input context IDs
- objective ID
- crawl plan ID
- tool call
- output
- decision
- confidence
- model and prompt version when applicable
- related memory IDs
- related evidence IDs

This makes agent-assisted crawling debuggable.
