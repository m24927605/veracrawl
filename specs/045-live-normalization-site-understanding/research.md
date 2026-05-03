# Research: Live Normalization And Site Understanding

## Decisions

### Reuse deterministic normalization pipeline

`normalize_html_document` already produces normalized document, manifest, anchor
map, anchors, link provenance, page type, and site model refs. The new runtime
wraps it with live acquisition prerequisites and completion gates.

### Upstream acquisition refs are mandatory

Passing reports require 041 live HTTP, 042 structured source, and 043 browser
snapshot refs so normalization cannot become a direct-source bypass.

### Site understanding is derived context

Page type and site model refs are useful for planning and future graph/memory
work, but they are not source evidence or published output.

## Alternatives Considered

- **Parse fixture files directly in core**: rejected because core must receive
  acquired content and refs through explicit inputs.
- **Use AI framework for page classification**: rejected for this slice; future
  AI assistance must remain framework-neutral and adapter-bound.
