# Contract: Memory Kernel

## Commands

- `write_memory_event`
- `retrieve_memory`
- `record_memory_kernel_report`

## Events

- `memory_written`
- `memory_retrieved`
- `memory_kernel_reported`

## Invariants

- Memory write requires scope, provenance, policy, poisoning, freshness, and prompt-use refs.
- Retrieved memory requires sanitized context refs.
- Invalidated memory must be excluded, not returned as retrieved.
- Memory reports require command, event cursor, outbox, and policy refs before pass.
