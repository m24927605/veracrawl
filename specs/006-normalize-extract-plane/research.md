# Research: VeraCrawl Normalize and Extract Plane

## Decision 1: Use Standard-Library HTML Parsing

Use `html.parser.HTMLParser` for deterministic fixture normalization.

Rationale:

- It avoids third-party parser dependencies while proving raw-to-normalized lineage.
- It is generic and does not require site selectors.
- It can extract text and links for deterministic local fixtures.

## Decision 2: Anchors Are Required Before Candidates

Every extracted candidate field must point to a text anchor.

Rationale:

- Later evidence packets need source-backed anchors.
- Candidate records cannot become trusted outputs without anchor lineage.

## Decision 3: Link Provenance Is Separate From Graph Projection

This slice emits `LinkProvenance` and page classification records, but does not build graph projections.

Rationale:

- Graph intelligence depends on canonical link provenance and normalized documents.
- Avoids claiming graph capability before graph rebuild and watermark tests exist.

## Decision 4: Candidates Cannot Publish

Extraction candidates remain intermediate records and cannot create `PublishedOutput` or `OutputManifest`.

Rationale:

- VeraCrawl's product rule separates extracted candidates from published outputs.
- Publication requires later evidence and verification acceptance.
