# Contract: Evidence Coverage

`EvidenceAnchor` records field-level source evidence. It must point to the
candidate, field name, source artifact, normalized document, text anchor, text
hash, privacy classification, and policy refs.

`EvidencePacketManifest` records the replayable evidence bundle. It must point to
the evidence packet, coverage result, evidence anchors, normalized documents,
source artifacts, privacy lifecycle refs, policy refs, replay bundle, and manifest
hash.

Coverage pass requires:

- every required candidate field has an `EvidenceAnchor`
- every evidence anchor has a source artifact, normalized document, and text anchor
- graph, memory, and agent reasoning refs do not count as source evidence
- missing source evidence returns non-pass and no publication refs
