# Implementation Plan: Delivery ETA Offer Sorting Projection

**Branch**: `078-delivery-eta-offer-sorting-projection`  
**Spec**: `specs/078-delivery-eta-offer-sorting-projection/spec.md`  
**Date**: 2026-05-04

## Technical Context

**Language**: Python  
**Architecture Constraints**: General-purpose AI agent crawler, low coupling,
high cohesion, framework-neutral core, no single-site scraper logic, no LLM
output as evidence.  
**Existing Surface**: Product availability benchmark, product availability
contracts, CLI JSON artifacts, fixture/oracle tests, contract registry.

## Constitution Check

- [x] General-purpose AI agent crawler behavior is preserved.
- [x] Core remains framework-neutral and does not import concrete agent
  frameworks or ecommerce SDKs.
- [x] Delivery and shipping values require source-backed evidence refs.
- [x] Missing field evidence is represented honestly as absent or non-pass.
- [x] Target architecture is not weakened due to staffing, schedule, sprint
  pressure, or delivery speed.

## Work Plan

1. Add offer projection contracts and register them.
2. Extend product availability contracts with optional delivery/shipping fields.
3. Implement general delivery ETA and shipping fee extraction from accepted
   source text, metadata, JSON-LD, or browser DOM text.
4. Implement offer projection sorting runtime.
5. Extend CLI output artifacts and summary.
6. Add contract, runtime, CLI fixture, replay, and registry tests.
7. Update docs/README and record validation results.

## Non-Goals

- No cart-only checkout automation.
- No site-specific ecommerce parser for Amazon, Walmart, momo, PChome, Shopee,
  eBay, or any other single platform.
- No claim that blocked sites expose delivery ETA.
- No use of LLM output as price, inventory, delivery, or shipping evidence.
