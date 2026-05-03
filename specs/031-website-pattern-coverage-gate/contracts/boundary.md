# Contract: Website Pattern Coverage Boundary

Website pattern coverage records are target benchmark proofs. They are not source
evidence by themselves and cannot satisfy publication evidence requirements.

Allowed pass inputs:

- source adapter refs
- source evidence refs
- site model and page type refs
- expected output/evidence oracle refs
- policy and safety refs
- artifact/event/graph oracle refs
- pattern-specific refs
- command, event cursor, outbox, and replay refs

Forbidden pass shortcuts:

- a single site or selector set as proof of general pattern support
- manifest-only or scaffold-only fixture refs
- unsupported pattern names
- unsafe browser/form/auth side effects
- output refs without source evidence and replay refs
- concrete browser, HTTP, storage, queue, model, agent framework, export target,
  or site-specific scraper imports in core runtime
