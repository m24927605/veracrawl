# Sacie Research Notes

Local repository studied: `~/products/verabase/sacie`

## Core Takeaway

Sacie is valuable for VeraCrawl because it treats analysis as an evidence pipeline, not as a direct model answer. This is essential for an AI agent crawler: agents may explore, classify, infer, and extract aggressively, but publication still requires evidence and verification.

The most important transferable rule is:

```text
candidate != fact
```

In VeraCrawl, extraction output is only a candidate until it passes evidence construction and verification.

## Sacie-style Pipeline For Crawling

```text
source snapshot
  -> deterministic extraction
  -> candidate generation
  -> evidence packet build
  -> verification
  -> fusion
  -> canonical report
  -> scenario projection
```

Crawler adaptation:

```text
page snapshot
  -> DOM/text extraction
  -> extraction candidate
  -> evidence packet
  -> verifier decision
  -> verified fact
  -> temporal KG write
  -> crawl report
```

## What To Borrow

### 1. Evidence Packets

Each candidate should be supported by an evidence packet containing:

- candidate value
- source URL
- crawl timestamp
- snapshot ID
- normalized document ID
- text or DOM anchor
- extraction method
- extractor version
- supporting evidence
- counter evidence
- confidence signals
- verifier decision

Evidence packets should be stored even when rejected. Rejections are useful for debugging and drift detection.

### 2. Source Anchors

A verified fact must point to exact source anchors.

Anchor types:

- text character offsets
- DOM selector path
- table cell coordinates
- JSON path
- screenshot region
- HTTP header
- linked source page
- prior verified fact

VeraCrawl should prefer stable anchors:

- canonicalized DOM paths
- semantic labels
- text quote windows
- content hashes
- neighboring heading context

### 3. Verification Before Fusion

Multiple candidates for the same fact should not be merged until they are individually verified.

Fusion should consider:

- source recency
- source authority within project
- directness of evidence
- consistency with nearby fields
- consistency with temporal KG after the Phase 4 projection exists
- extractor reliability
- contradiction records

### 4. Precision Controls

Sacie's precision mindset maps directly to crawler data quality.

VeraCrawl should define per-schema quality thresholds:

- required fields
- allowed value ranges
- type validators
- format validators
- cross-field constraints
- source count requirements
- freshness requirements
- confidence thresholds

Example:

```text
Product.price:
  requires numeric value
  requires currency evidence
  requires source anchor near product identity
  rejects stale snapshot beyond configured TTL
  flags conflict with current KG value
```

### 5. Trace And Replay

Every crawl run should preserve trace events:

- frontier decision
- fetch request and response metadata
- parser decision
- extraction prompt or rule version
- candidate emitted
- evidence packet built
- verification accepted or rejected
- memory written
- output exported

This makes production debugging possible.

## VeraCrawl Evidence States

Suggested candidate lifecycle:

- `observed`: raw source was captured.
- `candidate`: extraction produced a structured value.
- `evidence_built`: candidate has source anchors.
- `rejected`: failed verification.
- `conflicted`: conflicts with current or recent published outputs.
- `superseded`: replaced by newer published output.
- `published`: accepted through verification and publication policy.
- `expired`: no longer fresh enough for publication.

## How Sacie Complements Graphify

Graphify tells VeraCrawl where relationships may exist. Sacie-style evidence decides whether a relationship is publishable.

Example:

```text
Graph edge candidate:
  Product A -> price -> $99

Evidence packet:
  URL, snapshot, text anchor, DOM anchor, currency context, timestamp

Verifier:
  confirms product identity, price context, freshness, and schema validity

Verified fact:
  Product A -> price -> $99 [valid_from, source_evidence]
```

## How Sacie Complements MemPalace

MemPalace memory can remind agents that a selector or page type worked before. Sacie-style verification ensures the current run proves the fact again before publication.

Memory is a prior. Evidence is proof.

## Production Recommendation

Build VeraCrawl around the Sacie evidence funnel:

```text
Fast AI exploration is allowed.
Fast AI extraction is allowed.
Fast publication is not.
```

The platform should optimize for AI-assisted crawl throughput while keeping the publication boundary strict.
