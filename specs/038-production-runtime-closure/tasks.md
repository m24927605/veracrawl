# Tasks: VeraCrawl Production Runtime Spec Roadmap

**Input**: Design documents from `/specs/038-production-runtime-closure/`

## Phase 1: Roadmap Control Spec

- [x] T001 Replace generated placeholder with production runtime roadmap control spec in `specs/038-production-runtime-closure/spec.md`
- [x] T002 Add requirements checklist in `specs/038-production-runtime-closure/checklists/requirements.md`
- [x] T003 Add implementation plan for the roadmap control spec in `specs/038-production-runtime-closure/plan.md`

## Phase 2: Planned Spec Reservation

- [x] T004 Predeclare planned spec `039-production-run-control-api`
- [x] T005 Predeclare planned spec `040-production-persistence-runtime-wiring`
- [x] T006 Predeclare planned spec `041-live-http-acquisition-runtime`
- [x] T007 Predeclare planned spec `042-structured-source-adapters-runtime`
- [x] T008 Predeclare planned spec `043-browser-snapshot-runtime`
- [x] T009 Predeclare planned spec `044-credentialed-session-runtime`
- [x] T010 Predeclare planned spec `045-live-normalization-site-understanding`
- [x] T011 Predeclare planned spec `046-schema-extraction-candidate-runtime`
- [x] T012 Predeclare planned spec `047-live-evidence-verification-runtime`
- [x] T013 Predeclare planned spec `048-result-publication-export-runtime`
- [x] T014 Predeclare planned spec `049-real-agent-model-adapter-runtime`
- [x] T015 Predeclare planned spec `050-multi-agent-orchestration-repair-runtime`
- [x] T016 Predeclare planned spec `051-graph-memory-production-runtime`
- [x] T017 Predeclare planned spec `052-worker-orchestration-scale-runtime`
- [x] T018 Predeclare planned spec `053-ops-console-replay-observability`
- [x] T019 Predeclare planned spec `054-production-benchmark-release-gate`

## Phase 3: Repository Guidance

- [x] T020 Update `docs/08-build-roadmap.md` with the post-037 spec roadmap
- [x] T021 Update `AGENTS.md` active Spec Kit pointer and anti-ad-hoc-spec rule
- [x] T022 Update `.specify/feature.json` to point to spec 038

## Phase 4: Verification

- [x] T023 Verify planned specs 039-054 exist
- [x] T024 Verify no generated placeholder text remains in planned specs
- [x] T025 Run `git diff --check`

## Validation Results

- 2026-05-03: Planned specs 039-054 were created as `spec.md` files only; they are planned, not implemented.
- 2026-05-03: `docs/08-build-roadmap.md` and `specs/038-production-runtime-closure/spec.md` both define the post-037 roadmap.
- 2026-05-03: `.specify/feature.json` points to `specs/038-production-runtime-closure`.
- 2026-05-03: File presence check confirmed exactly one `spec.md` for each planned spec 039-054.
- 2026-05-03: Placeholder scan found no generated template placeholders in specs 038-054, `docs/08-build-roadmap.md`, `AGENTS.md`, or `.specify/feature.json`.
- 2026-05-03: `uv run --python python3.12 --extra dev veracrawl-contracts validate --format json` passed with `ok: true`.
- 2026-05-03: `git diff --check` passed.
