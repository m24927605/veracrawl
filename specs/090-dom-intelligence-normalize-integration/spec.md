# Feature Specification: DOM Intelligence Normalize Integration

**Feature Branch**: `088-optimization-owner-integration`
**Created**: 2026-05-06
**Status**: Implemented
**Input**: Spec 088 approved integration roadmap row 090.

## Purpose

Connect runtime DOM context bundles, page zones, and interactive element
rankings from specs 082 and 087 to normalize/browser-owned integration records.

## Constitution Alignment

- DOM integration remains page-pattern and schema agnostic.
- Normalize/browser own DOM artifacts, anchor preservation, and prompt-taint
  policy refs.
- Screenshot or browser output can supplement DOM evidence only when policy
  permits; DOM tree remains the primary machine context.

## Requirements

- **FR-090-001**: System MUST map normalized document refs to DOM context refs,
  retained node refs, page zone refs, and interactive element refs.
- **FR-090-002**: System MUST retain source anchors and artifact refs for every
  retained DOM node and element ranking.
- **FR-090-003**: System MUST record context-size reduction metrics and fail
  integration when required anchors are missing.
- **FR-090-004**: System MUST label prompt-tainted or browser-derived context
  through policy refs before downstream extraction.

## Completion Gate

Normalize integration tests prove DOM intelligence records retain anchors,
reduce context, rank expected elements, and fail missing-anchor or unsafe
browser-context cases.

## Non-Goals

- This spec does not implement a new browser renderer.
- This spec does not make screenshots the primary extraction substrate.
