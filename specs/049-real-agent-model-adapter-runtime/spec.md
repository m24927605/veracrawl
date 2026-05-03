# Feature Specification: Real Agent And Model Adapter Runtime

**Feature Branch**: `049-real-agent-model-adapter-runtime`
**Status**: Planned - not implemented
**Roadmap Source**: `specs/038-production-runtime-closure/spec.md`

## Purpose

Connect real model providers and agent frameworks through replaceable adapters
for planning, site understanding, extraction strategy, repair, and verification
support while preserving framework-neutral VeraCrawl core state.

## Scope

- Model provider adapter execution for approved providers.
- Agent framework adapters for OpenAI Agent SDK, LangChain, LangGraph, CrewAI,
  AutoGen, Semantic Kernel, and future frameworks where supported.
- Model/tool/agent trace refs.
- Adapter conformance tests and import-boundary tests.

## Dependencies

- Blocks: 050, 051, 054.
- Requires: 039, 045, 046.

## Completion Gate

Planning, extraction, and repair can use real adapters, but core packages do not
import concrete SDKs/frameworks and canonical state persists only VeraCrawl
contracts, commands, events, policy, traces, artifacts, and replay refs.

## Non-Goals

- Does not make any framework mandatory.
- Does not persist framework-native state as canonical state.
