# Resume Prompt — VeraCrawl V2 Production Spine (2026-05-10)

> Paste the body below into a fresh agent session (codex / claude code / any
> capable LLM agent) after `/clear`. Self-contained — assumes no prior
> conversation context. State as of master `a821e698be2449b8167969bf36dad0be0aea3063`
> ("Phase 6 step 6.1 unblock: PRODUCTION mode wires real HTTPTransport").

---

You are picking up work on the VeraCrawl v2 production-authorized-source-crawler.
This is a multi-phase build (Phases 0–6) for a compliant LLM-agent web crawling
system. The previous session landed ~95 commits across 7 phases of design +
implementation; the contract surface has been validated against real OpenAI.
Your job is to continue from where we stopped.

## Where you are

- Working directory:
  `/Users/sin-chengchen/products/veracrawler/veracrawl/.ait/workspaces/attempt-0001-01kr1pya87180smrvxj4h6mm6v`
  (an AIT worktree; detached HEAD pattern is normal)
- Parent repo: `/Users/sin-chengchen/products/veracrawler/veracrawl` (master at
  `a821e698be2449b8167969bf36dad0be0aea3063`)
- Branch preserving the work: `v2-prodspine-attempt-0001` (same SHA)
- AIT worktree has its own copy of the tree; commits here, then
  `git update-ref refs/heads/master <sha>` to fast-forward parent master
  (no remote configured, no GitHub PR path)

## Read these first (in order)

1. `docs/plans/p0-fix-pack/STATUS.md` — authoritative phase progress + per-step
   reservations + codex-review log
2. `docs/plans/production-authorized-source-crawler/design.md` — V2 spec
3. `docs/plans/production-authorized-source-crawler/phase-{3,4,5,6}-design.md`
   — JIT design supplements (already shipped)
4. `~/.claude/projects/-Users-sin-chengchen-products-veracrawler-veracrawl/memory/MEMORY.md`
   — user feedback persisted across sessions; especially:
   - `feedback_no_spec_kit.md` (DO NOT use `specs/NNN-*/` directory pattern)
   - `feedback_efficiency_directives.md` (front-load design; reduce ceremony)
   - `feedback_codex_recurring_concerns.md` (16-item pattern checklist; scan
     before writing first draft)

## What's done (every fixture-mode-buildable sub-step across Phases 0–6)

- **Phase 0**: contracts + exception hierarchy (DONE pre-attempt)
- **Phase 1**: cooperative HTTP + browser baseline 1.1→1.6c
  (DONE_WITH_RESERVATIONS)
- **Phase 2**: authorized session subsystem 2.1→2.5b (DONE_WITH_RESERVATIONS)
- **Phase 3**: 7/7 sub-steps including `AccessControlClassifier` /
  `PolicyDrivenEscalator` / `EbayTokenCachePort` / `CursorPaginatedAdapter` /
  `AmazonSpApiLwaTransport` (fixture-mode) / `EbayBrowseAdapter` (fixture-mode
  with pagination + 401 refresh)
- **Phase 4**: 7/7 sub-steps. `ModelProviderPortV2` +
  `OpenAIResponsesAdapterV2` + `AnthropicMessagesAdapter` + `JsonPromptRegistry`
  + `OutboxBackedBudget` + `SchemaExtractionRuntime` + `IdentityCalibrator` /
  `PlattCalibrator`. **Both v2 adapters now accept real `httpx.HTTPTransport`
  in `RuntimeMode.PRODUCTION`** (Phase 6 step 6.1 unblock landed).
- **Phase 5**: 4/4 sub-steps. `RecoveryPort` + `LLMBackedRecovery` +
  `HeuristicCheapClassifier` + `CostGatePort` + `InMemoryCostGate` +
  `AgentRunController` + cheap-classifier corpus
- **Phase 6**: design supplement + step 6.2 charter regression test DONE; 6.1
  partially landed (PRODUCTION mode wiring); 6.3/6.4/6.5 are operational
  deferrals (real Postgres/S3/OTel, gold corpus, three nightly green runs)
- `ProviderResponse.tool_calls: list[ToolCall]` field added with invariants
  (populated → finish=TOOL_CALL; unique IDs)

## Validated against real OpenAI

- `OPENAI_API_KEY` + `OPENAI_MODEL=gpt-5.4-mini` are in `~/.env`
- `scripts/pilot_smoke_test.py` — raw httpx call, ProviderRequest /
  ProviderResponse round-trip works
- `scripts/pilot_via_adapter.py` — full v2 adapter framework end-to-end,
  returned `{"ack": true, "via": "adapter"}` for ~$0.000015
- Real wire shape (`text.format` for JSON_OBJECT) + usage block
  (`input_tokens` / `output_tokens` / `total_tokens`) + finish_reason mapping
  all match contract assumptions

## Constraints (HARD)

1. **Charter (`docs/09:116`)**: NO mechanisms for CAPTCHA solving, paywall
   bypass, credential theft, login-wall circumvention, WAF evasion, stealth
   automation, ban-avoidance proxy tactics, or bypassing robots / terms /
   customer authorization policy. Test
   `tests/contract/test_phase_6_charter_regression.py` enforces this on
   `src/`.
2. **No spec-kit**: never create `specs/NNN-*/` directories or three-file
   `spec.md` / `plan.md` / `tasks.md` pattern.
3. **No `pyyaml` / new heavy deps without explicit approval** (codex
   recurring concern #10).
4. **PRODUCTION mode** raises `ProductionRuntimeNotImplemented` for paths
   still gated. FIXTURE mode is `MockTransport`-only on adapters.
5. **Codex review at every stage transition** via
   `~/.claude/hooks/codex-review.sh task <baseline-sha> --project-dir $PWD`
   with `CODEX_REVIEW_ITERATION=N`. 5-iter cap; post-iter-5 fix-up if
   rejected.
6. **YAGNI**: no speculative abstractions, no future-proofing.
7. **Type checks must pass**: `uv run --no-sync mypy --strict src tests`
   baseline = **68 pre-existing errors**; new commits must keep this at 68
   (any increase = regression).
8. **`uv run --no-sync ruff check .` must be clean**.
9. **`uv run --no-sync pytest -q` must exit 0** before committing.
10. **All commits** end with
    `Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>`
    (or whatever attribution your harness uses).

## Codex recurring concerns checklist (apply BEFORE writing first draft)

Before writing any new module, scan for these 16 patterns that codex review
consistently flags:

1. Sensitive-marker tuple completeness (credentials, OAuth, JWT, PII)
2. PRODUCTION-mode gate via `ProductionRuntimeNotImplemented`
3. `_private` slot discoverability via `dir()` / `__dict__` walk
4. Recursion bounds + cycle detection
5. `from None` AND `__context__` leak via re-raise inside `except` (use
   capture-flag pattern: capture exception, raise OUTSIDE the except block)
6. Identifier-shape validation (whitespace-only refused; regex for opaque IDs)
7. Unbounded loops (cap with explicit budget)
8. `getattr` safety (custom `__getattribute__` triggering side effects)
9. URL handling: scheme allowlist + netloc + userinfo refusal + path
   canonicalization
10. Dependency upper bounds (`<MAJOR.MINOR+1`)
11. Private modules (`_string`, `re._parser`) — refuse, use stdlib API
12. Path canonicalization (`Path.resolve()` + `relative_to()` to confine to
    root)
13. Free-form `reason: str` strings — replace with enum
14. Exception `__dict__` leak via `vars()` / `logging.exception`
15. Real-engine timing in tests (use deterministic time / regex)
16. Doc / spec / docstring divergence from implementation

## Recommended next steps (priority order)

### Immediate (1 attempt each)

**A. `SchemaExtractionRuntime` end-to-end pilot via real OpenAI**

Build `scripts/pilot_schema_runtime.py` that:

- Loads OPENAI_API_KEY from ~/.env
- Builds `JsonPromptRegistry` pointing at a tmp prompts dir with one extractor
  template
- Builds `OpenAIResponsesAdapterV2(runtime_mode=PRODUCTION)`
- Builds `OutboxBackedBudget` with a tiny cap ($0.01)
- Builds `IdentityCalibrator`
- Calls `SchemaExtractionRuntime.extract()` against a real OpenAI call
- Verifies `LLMExtractionCandidate` + citations + confidences land cleanly

This is the proof-of-concept that the integrator works against reality.

**B. Wire real LLM dispatcher into `LLMBackedRecovery`**

Currently `LLMBackedRecovery._llm_decision_fn` is a stub callable. Replace
with a `SchemaExtractionRuntime`-backed dispatcher that asks the model to
choose `{DIFFERENT_URL, ESCALATE_ADAPTER, REQUEST_REVIEW, ABANDON}` via
JSON_OBJECT prompt. This unblocks Phase 5 actually doing recovery instead of
always returning ABANDON.

**C. `AgentRunController.cost_gate.charge()` integration**

Currently the controller calls `cost_gate.check()` but never
`cost_gate.charge()`. Reason: `SchemaExtractionRuntime.extract()` returns
3-tuple without usage. Change extract() to return 4-tuple including the
`ProviderResponse` (or add `last_usage` attribute to runtime), then have
controller charge after success. Update existing tests.

### Short-term (next batch)

**D. `ToolCall` parsing on response side** for both v2 adapters. Wire shapes:

- OpenAI Responses API: `output[].type == "function_call"` items have
  `name`, `arguments` (JSON string), `call_id`
- Anthropic Messages: `content[].type == "tool_use"` blocks have `name`,
  `input` (JSON dict), `id`

Currently both adapters refuse `tools` at `complete()`. Lift the refusal
once parsing lands.

**E. Codex review backfill** on the unreviewed batch (Phase 3 step
3.1 / 3.2 / 3.4 / 3.5b / 3.6, Phase 4 step 4.4–4.7, Phase 5 step
5.1–5.4, Phase 6 step 6.2). Pattern: pick a step's commit chain, set
`BASELINE=<parent of first commit in chain>`, run
`CODEX_REVIEW_ITERATION=1 ~/.claude/hooks/codex-review.sh task $BASELINE --project-dir $PWD`.
Apply important findings.

### Operational (multi-day, not single-attempt)

- **F.** Phase 6 step 6.5 — gold corpus authoring (200 entries), Platt fit,
  nightly Brier / ECE pipeline
- **G.** Phase 6 step 6.4 — live regression suite against eBay / SP-API /
  Cloudflare-protected URLs (needs developer-account approvals)
- **H.** Phase 6 step 6.3 — DR drill on real Postgres / Redis / S3
- **I.** Persistent Postgres outbox + S3 evidence store (replaces in-memory
  implementations)

## Common pitfalls (avoid these)

- **Don't** build features speculatively. The codebase already has 95+
  commits of fixture-mode building blocks; the gap is operational not
  architectural.
- **Don't** add `pyyaml` / `jsonschema` / heavy deps without checking why
  they're absent (codex recurring concern #10 + already-deferred reservations
  in design supplements).
- **Don't** treat AIT worktree as a fresh repo — it shares git objects with
  the parent. `git status` in the parent worktree may show "uncommitted
  changes" that are actually older user state, not your work. Use
  `git update-ref refs/heads/master <sha>` to fast-forward parent master from
  this worktree's commits.
- **Don't** lift PRODUCTION gates without a real validation pilot. The
  Phase 6.1 unblock for OpenAI / Anthropic landed because we ran
  `scripts/pilot_via_adapter.py` against real OpenAI first.
- **Don't** trust codex iter-N findings as gospel — codex sometimes
  flip-flops (e.g., JSON_SCHEMA handling across iter-2 / 3 / 4 / 5 of step
  4.3). Apply Staff-team judgment: if a finding contradicts a prior settled
  decision, hold the line and document.
- **Don't** create more design supplements (Phases 3–6 already have them).
  For new sub-steps inside an existing phase, just write tight implementation
  + tests.
- **Don't** spawn the AIT system to run `claude` — you ARE the agent. Just
  edit and run tests directly.

## Workflow

For each implementation step:

1. Scan codex-recurring-concerns checklist
2. Write tight implementation (port + adapter + tests)
3. `uv run --no-sync pytest tests/path/to/focused_test.py -x -q`
   (focused green)
4. `uv run --no-sync ruff check .` (must be clean — apply `--fix` if safe)
5. `uv run --no-sync mypy --strict src tests | grep -cE "error:"` (must stay
   at 68)
6. `uv run --no-sync pytest -q` (full suite green, exit 0)
7. `git add <files> && git commit -m "..."` (full commit message with
   Co-Authored-By)
8. Codex review:
   `CODEX_REVIEW_ITERATION=1 ~/.claude/hooks/codex-review.sh task <baseline> --project-dir $PWD > /tmp/codex.log; tail -50 /tmp/codex.log`
   — apply important findings, iterate up to 5 times, post-iter-5 fix-up if
   needed
9. Update `docs/plans/p0-fix-pack/STATUS.md` with the step row +
   reservations + codex-log rows
10. `git update-ref refs/heads/master <new-sha>` to fast-forward parent
    master
11. `git branch -f v2-prodspine-attempt-0001 HEAD` to update the preserved
    branch

## First action

Run `git log --oneline | head -10` to confirm you're at `a821e69`
("Phase 6 step 6.1 unblock"). Then run
`uv run --no-sync python scripts/pilot_via_adapter.py` to verify the
real-OpenAI pilot still works (cost ~$0.000015). If both confirm, proceed
with task **A** above.

Reply in 繁體中文 unless the user switches to English. Match the existing
commit-message style (subject line in plain English with optional emoji-free
prefix; body wrapped to ~72 chars with explicit codex-iter / Phase-X-step
references; trailer with Co-Authored-By).
