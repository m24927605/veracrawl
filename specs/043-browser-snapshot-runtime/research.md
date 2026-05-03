# Research: Browser Snapshot Runtime

## Decisions

### Browser capability stays behind existing ports

Use `BrowserSourceAdapterPort` and `BrowserObservationResult` as the runtime
boundary. The target slice adds a report aggregate around those existing refs
instead of coupling core to a browser engine.

**Rationale**: VeraCrawl core must stay low-coupled and framework-neutral.
Concrete browser engines and deterministic fixtures are adapter concerns.

### Canonical success is ref-complete, not browser-native-state-complete

Persist refs to DOM, screenshot, network trace, console log, timing, budget,
policy, command/event/outbox, upstream acquisition reports, and replay bundle.
Do not persist browser engine sessions, cookies, trace blobs, or adapter object
state as canonical models.

**Rationale**: Replay and evidence lineage need stable canonical refs, while
engine-native state is replaceable adapter detail.

### Negative fixture outcomes are typed failures

Treat egress denial, unsafe interaction, budget exhaustion, prompt-tainted
content, missing artifact, and replay mismatch as deterministic failure types.

**Rationale**: Operators need explicit failure categories for review and repair;
ambiguous missing data would weaken the target architecture.

### CLI composes deterministic fixture adapters only at the edge

The CLI may import the deterministic browser adapter and local benchmark server
to run fixtures. The runtime receives adapter instances and upstream refs.

**Rationale**: This proves the port boundary while keeping tests executable
without external browser dependencies.

## Alternatives Considered

- **Direct Playwright dependency in core**: rejected because it would couple
  canonical runtime to a specific browser engine.
- **Browser report without upstream 041/042 refs**: rejected because 043 depends
  on live HTTP and structured source coverage and must not become a bypass path.
- **Treat prompt-tainted rendered content as pass-with-warning**: rejected
  because rendered content can become model context later and must be gated
  before downstream normalization/extraction.
