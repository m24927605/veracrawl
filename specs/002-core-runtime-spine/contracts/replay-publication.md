# Contract: Replay And Publication

## Purpose

Define the publication and replay requirements that prevent unverified or unreplayable outputs.

## Publication Preconditions

`PublishedOutput` and `OutputManifest` may be created only when all are true:

- objective gate is pass
- plan gate is pass
- source gate is pass or policy-accepted partial
- normalization gate is pass
- extraction gate is pass
- evidence gate is pass
- verification decision is accept
- publication policy decision is allow
- replay refs required for publication are present
- artifact lifecycle permits current use

## OutputManifest Requirements

The manifest must include:

- output ID and version
- schema refs
- required field/item refs
- evidence packet refs
- field-level evidence refs
- verification decision refs
- publication policy decision refs
- artifact refs and hashes
- privacy lifecycle refs
- export/withdrawal lifecycle placeholders
- replay bundle ref
- manifest hash

## ReplayBundleManifest Requirements

The replay bundle must include:

- command result refs
- event cursor refs
- source adapter result refs
- artifact hash refs
- normalized document refs
- extraction candidate refs
- evidence packet refs
- verification decision refs
- output manifest refs
- optional agent/model/tool/context trace refs
- policy decision refs
- deterministic clock/random seed refs
- redaction map ref
- completeness result

## Missing Ref Behavior

- Missing required publication refs block publication.
- Missing required replay refs produce fail or needs_review according to replay policy, never pass.
- Redacted content must preserve stable refs required for structural replay.

## Conflict Behavior

Verification conflict prevents publication until adjudicated or superseded. Conflict records must remain replay-visible and operator-visible.
