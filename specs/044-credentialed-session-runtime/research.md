# Research: Credentialed Session Runtime

## Decisions

### Session use is adapter-owned and canonical state is redacted refs

The core runtime accepts a `CredentialedSessionAdapterPort` and records only
VeraCrawl refs: credential audit, session adapter result, redacted artifact,
redacted replay, command/event/outbox, policy, and upstream acquisition refs.

**Rationale**: Raw credentials, cookies, browser sessions, and vault-native
objects must remain outside canonical state.

### Credential use audit is mandatory for pass

Use the existing `CredentialUseAudit` contract for scope, origin, delivery mode,
policy, approval, redaction, command/event, and replay proof.

**Rationale**: This avoids a parallel credential audit model and keeps security
semantics high-cohesion in the security/privacy contract area.

### Negative outcomes are typed

Missing authorization, out-of-scope origins, unsafe credential use, raw secret
leakage, missing audit, missing redacted replay, and replay mismatch fail
deterministically.

**Rationale**: Credential workflows need explicit operator-visible failures; a
partial pass would be deceptive.

## Alternatives Considered

- **Persist session cookies as canonical state**: rejected because adapter-native
  state and raw secret derivatives cannot become VeraCrawl state.
- **Reuse dynamic source runtime only**: rejected because row 044 needs an
  explicit credentialed session aggregate tied to 041 and 043 prerequisites.
- **Treat missing redacted replay as needs-review**: rejected because redacted
  replay is mandatory for credentialed session pass.
