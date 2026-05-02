# Implementation Plan: VeraCrawl Multi-Agent Repair

**Branch**: `011-multi-agent-repair` | **Date**: 2026-05-02 | **Spec**: [spec.md](spec.md)

## Summary

Implement framework-neutral multi-agent workflow, handoff, coordination, drift repair signal, replay report, CLI fixture runner, and negative boundary fixtures.

## Constitution Check

- [x] No site-specific scraper assumptions.
- [x] Core remains framework-neutral and does not import agent frameworks or model SDKs.
- [x] Owner services remain responsible for durable mutations.
- [x] Memory, graph, and agent reasoning cannot replace evidence.
- [x] Replay refs and negative fixtures are defined before implementation.
