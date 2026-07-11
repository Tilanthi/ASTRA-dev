# ASTRA Autonomous Discovery Re-architecture — Design Document

**Date:** 2026-07-11
**Status:** Approved (user direction, 2026-07-11) → **IMPLEMENTED & VERIFIED 2026-07-11**
**Author:** ASTRA engineering (Claude), grounded in code-level investigation

---

## 0. TL;DR

ASTRA's idle-time "autonomous discovery" service is **actively violating its own
prime directive**: it writes fictional discoveries — including the literal
hardcoded string `"STAN system initialized..."` as a discovery title — to the
genuine-discoveries store, ~1 per 60 s cycle. The machine-graded evolutionary
loop built after the AlphaEvolve work (real gains on real SDSS data) is verified
but **decoupled and offline**; the live service does not use it. Separately, the
ingestion consumer has a dedup bug that is silently duplicating records.

This design does three things:

1. **Makes "cannot emit fiction" a structural property** — no code path writes a
   discovery unless it passes two machine-checkable gates.
2. **Stands up an always-autostart, user-yielding supervisor** whose idle
   activity is the proven machine-graded loop (Phase 1), then generalises that
   loop to open-ended Eureka-level search with a literature-novelty gate
   (Phase 2).
3. **Fixes the store-hygiene bugs and sandboxes generated code** so the whole
   thing is trustworthy enough to run unattended.

The core idea, taken from AlphaEvolve: **no claim is promoted until it passes a
machine-checkable `EVALUATE`** — here, *two* gates (real-data verification +
literature novelty). Textbook restatements fail gate 2; fabricated claims fail
gate 1.

---

## 1. Problem statement (evidence-based)

All findings below were verified in code, not from the repo's own status notes.

### 1.1 The live service emits fictional discoveries (prime-directive violation)

- Entry chain actually running: installed `~/Library/LaunchAgents/com.astra.discovery.plist`
  → `astra_core/scientific_discovery/sleep_aware_watchdog.py` →
  `start_autonomous_discovery.py` → `astra_core/autonomous_startup_discovery_v2.py`
  → `FixedGenuineDiscoverySystem.start()` → `create_stan_system()` →
  `EnhancedUnifiedSTANSystem` → falls back to `UnifiedSTANSystem.process_query()`.
- `astra_core/core/unified.py` ~lines 558–569: `process_query()` returns a
  **hardcoded dict** whose `'answer'` is the literal string
  `"STAN system initialized. For full query processing, use EnhancedUnifiedSTANSystem."`
  `answer()` is an alias for `process_query()`.
- `autonomous_startup_discovery_v2.py` `_call_astra_with_timeout()` (~358–396)
  turns that `'answer'` string into a "discovery" (`_create_discovery_from_result`),
  so the canned init string becomes the **title and abstract verbatim**. This was
  read directly out of `~/.astra_persistent/genuine_discoveries.json`.
- Queries come from **15 fixed templates** in `_generate_simple_query()`
  (~474–488): 5 domains × 3 focuses. No real query understanding.
- The validation confidence **"60.0% / INCREMENTAL" is a hardcoded constant** in
  `astra_core/scientific_discovery/genuine_discovery_validator.py` (~148–158),
  not a computed value. Records are written **even with `is_genuine: false`**.
- Net: the service produces ~60 canned/fictional "discoveries" per hour and
  stores them alongside genuine ones. This is exactly what
  `CLAUDE.md` forbids ("NO FICTIONAL/SYNTHETIC DISCOVERIES … SYSTEM FAILURE IF
  MOCK DATA DETECTED").

### 1.2 Gap 2 — `answer()` bypass / hardcoded STAN output

- Root cause is the hardcoded return in `unified.py` (~558–569). A real
  `LLMInferenceEngine` exists (`astra_core/capabilities/llm_inference.py` ~198,
  `query()` ~367, with `AnthropicBackend`/`OpenAIBackend`/`MockBackend`) but
  **STAN is not wired to it**.
- The evolutionary proposer already uses a working direct-Anthropic client
  (`evolved_analysis/proposer.py` ~92–98, 180–183) via `ANTHROPIC_AUTH_TOKEN` +
  `ANTHROPIC_BASE_URL`. This is the de-facto correct LLM path.

### 1.3 Gap 3 — one discovery + a dedup bug that corrupts the store

- `evolved_discovery_consumer.py` `consume_evolved_discoveries()` (~29–89)
  dedups new records against `system.genuine_discoveries`. But
  `autonomous_startup_discovery_v2.py` (~47) sets `self.genuine_discoveries = []`
  and **never hydrates it from disk** on startup. So the dedup set is empty every
  cycle → the same record is re-appended every cycle.
- Evidence: `evolved_discoveries.json` holds **1** machine-verified record;
  `genuine_discoveries.json` has accumulated **duplicate** copies of it (same
  `program_hash`, same timestamp). The store is also polluted by the §1.1 fakes.
- The low *emission* count (1) is partly correct/conservative: the emitter only
  fires when a candidate beats the seed on held-out TEST data
  (`discovery_emit.py` ~57–95; `run_engine.py` ~99–115,
  `run_classify.py` ~83–100). That part is working as intended.

### 1.4 Gap 4 — no OS-level sandbox for generated code

- Current isolation = subprocess + timeout only
  (`evolved_analysis/evaluator.py` ~58–82; 60 s photo-z / 90 s classify).
  The worker `exec()`s the LLM-generated source in-process within that subprocess
  (`eval_worker.py` ~106–131).
- `validate_source()` only checks `f"def {entry_point}" in src`
  (`program.py` ~116–118). **No** AST import check, no `resource.setrlimit`, no
  filesystem/network restriction, no separate UID.
- Generated code only needs `numpy`/`pandas`/`sklearn` + reading cached CSVs. It
  does **not** need network, arbitrary file write, or subprocess.
- Platform: macOS. `/usr/bin/sandbox-exec` available (deprecated but functional);
  Python `resource` module available (`RLIMIT_CPU/AS/FSIZE/NOFILE/NPROC`…);
  Docker installed but daemon not running (too heavy for a LaunchAgent anyway).

### 1.5 Gap 1 — "live integration partial", reframed

The service is not stopped; it is running the **wrong path** (fiction). The
machine-graded evolutionary loop is verified but decoupled
(`evolved_analysis` deliberately imports leapcore by file path and avoids
`astra_core/__init__`, to dodge the heavy init / deadlock surface). The
consumer that would bridge them is wired into `_robust_discovery_loop()` (~67–79)
but, per §1.3, partly broken and starved of real output.

---

## 2. Goals and non-goals

**Goals**

- **G1 (invariant).** It is structurally impossible for any code path to write a
  discovery to the genuine store unless the claim passes two machine-checkable
  gates (real-data verification + literature novelty). Fiction cannot be emitted
  by construction.
- **G2 (autostart).** ASTRA starts on login and stays up; the supervisor
  self-heals (watchdog) without the old deadlock-prone pause/resume machinery.
- **G3 (assistant-first, autonomous-second).** When the user is actively using
  ASTRA, discovery yields cleanly and cheaply; when idle, discovery resumes.
- **G4 (real idle activity).** The idle-time loop performs machine-verified work
  (Phase 1: proven narrow-task evolution; Phase 2: open-ended Eureka search).
- **G5 (store integrity).** The store is hydrated from disk on startup, dedup is
  correct, and existing pollution is purged.
- **G6 (safe execution).** LLM-generated analysis code runs with bounded CPU /
  memory / filesystem / network.

**Non-goals**

- Repairing STAN into a general LLM brain. STAN stays a symbolic/template
  component; real LLM calls go through a shared gateway (§4.3).
- A 60 s discovery cadence. Genuine discovery is rare by nature; the loop runs
  on a cadence matched to the work (minutes), not a fixed fast tick.
- Full automation of the literature-novelty gate in Phase 1. Phase 1 ships the
  plumbing and the proven engine; the novelty gate lands in Phase 2 and is
  honestly labelled as best-effort retrieval, not oracle.

---

## 3. Architecture overview

```
                         ┌──────────────────────────────────────────┐
   login ──LaunchAgent──▶│            ASTRA Supervisor              │
                         │  (self-healing; replaces fiction emitter) │
                         └──────────────────────────────────────────┘
                              │                           │
              user-active?    │                           │ idle
            ┌─────────────────┘                           │
            ▼ (yield: finish current                       ▼
              candidate, don't start next)        ┌───────────────────┐
                                               │ Discovery Loop    │
                                               │ (cadence ~minutes)│
                                               └───────────────────┘
                                                       │
                                  proposes claim+test  │  (LLM via shared gateway)
                                                       ▼
        ┌──────────────────────────────────────────────────────────────┐
        │            Two-Gate EVALUATE (AlphaEvolve core)               │
        │                                                              │
        │  Gate 1: real-data verification                              │
        │     candidate test ──exec──▶ real archival data ──▶ metric   │
        │     (sandboxed: rlimit + AST allowlist + sandbox-exec)       │
        │                                                              │
        │  Gate 2: literature novelty                                  │
        │     claim ──retrieve──▶ arXiv/textbooks ──▶ not-already-known│
        │                                                              │
        │  promote ONLY if both pass                                   │
        └──────────────────────────────────────────────────────────────┘
                                                       │ pass
                                                       ▼
                                  genuine_discoveries.json (dedup-correct,
                                                           hydrated on start)
```

**Key invariants**

- *Write path is gated, not generator-based.* There is no "generate a discovery"
  call; there is only "submit a candidate to EVALUATE; if it passes, record it."
- *Assistant-first.* A single user-active signal gates starting the next
  candidate. No mutexes/event-waits on the loop thread (the v5.0 deadlock cause).
- *Decoupling preserved.* The evolutionary engine stays import-light (leapcore
  by file path, no `astra_core/__init__`), so it cannot re-trigger the heavy
  init / deadlock surface.

---

## 4. Phase 1 — stop the bleeding + trustworthy plumbing

Phase 1 deliverable: ASTRA autostarts, runs **only** machine-verified work when
idle, yields to the user, and cannot emit fiction. Phase 2 (§5) builds on it.

### 4.1 Kill the fiction path (G1)

- **Disable canned emission.** In `autonomous_startup_discovery_v2.py`,
  `_call_astra_with_timeout()` / `_create_discovery_from_result()` must **not**
  create a discovery from a canned/template `answer`. Concretely: if the ASTRA
  system response is the hardcoded init string (or any response lacking a
  machine `verification` block), return `None` — write nothing.
- **Remove the template query generator** `_generate_simple_query()` from the
  discovery path. (It may be retained only as an *assistant* prompt helper, never
  as an autonomous discovery source.)
- **Validator must be real or silent.** `genuine_discovery_validator.py`'s
  hardcoded 0.6/INCREMENTAL fallback (~148–158) must not mark anything genuine.
  A record without a machine `verification` block is rejected, not defaulted.
- **Single chokepoint for writes.** All writes to the genuine store go through
  one function that requires a non-empty `verification` block with a real
  metric. The consumer and any future emitter both use it. This makes "cannot
  emit fiction" structural rather than convention-based.

### 4.2 Fix store hygiene (G5)

- **Hydrate on startup.** `FixedGenuineDiscoverySystem` (or its replacement
  supervisor) loads `genuine_discoveries.json` into `self.genuine_discoveries`
  at init, so dedup has real prior state.
- **Correct dedup key.** Dedup on `verification.program_hash` (already the
  intended key in `evolved_discovery_consumer.py`), now against a hydrated set.
- **Purge pollution.** A one-time migration script removes (a) records with no
  `verification` block (the §1.1 fakes) and (b) duplicate `program_hash` records
  beyond the first. Runs once, logged, dry-run-first.

### 4.3 Shared LLM gateway (closes Gap 2 cleanly)

- Promote the proposer's working direct-Anthropic client into a canonical
  `astra_core` gateway, e.g. `astra_core/intelligence/llm_gateway.py`:
  `complete(system, messages, model="claude-haiku-4-5…"|"claude-sonnet-5…", ...)`,
  reading `ANTHROPIC_AUTH_TOKEN` + `ANTHROPIC_BASE_URL`.
- The proposer, the Phase 2 claim-generator, and (optionally) narration all use
  it. STAN is left as-is (symbolic/template); we do **not** rewire the large STAN
  class. This dissolves Gap 2 without the risk of repairing `answer()`.

### 4.4 Sandbox generated code (G6, closes Gap 4)

Defence-in-depth, all macOS-native, no Docker:

1. **AST import allowlist** (new `evolved_analysis/safety.py`, used by
   `evaluator.py` before exec): parse the candidate with `ast`, reject unless
   every `Import`/`ImportFrom` is in `{numpy, pandas, sklearn, scipy, math,
   statistics}` and there are no `Call` nodes to builtins that touch the OS
   (`open`, `exec`, `eval`, `compile`, `__import__`, attribute access to
   `__builtins__`, `os`, `sys`, `subprocess`, `socket`, `shutil`, `pty`).
   Existing repo AST tooling (`tool_integration.py` `PythonExecutor`) is a
   reference but is **not** used here; we add a focused checker.
2. **Resource limits** in `eval_worker.py` before exec: `resource.setrlimit`
   `RLIMIT_CPU` (e.g. 60 s), `RLIMIT_AS` (e.g. 2 GiB), `RLIMIT_FSIZE` (small),
   `RLIMIT_NPROC` (prevent forks).
3. **`sandbox-exec` profile** wrapping the worker subprocess: read-only access
   to the repo + data cache, write only to a temp dir for the result JSON, **no
   network** (`deny network*`), no access to `$HOME` outside the cache. The
   profile is a small `.sb` file invoked via `sandbox-exec`.
4. Timeout remains (already present).

### 4.5 Supervisor + safe yield + autostart (G2, G3)

- **New supervisor** `astra_core/autonomous_discovery_supervisor.py`:
  - Loads the genuine store from disk (§4.2).
  - Runs the discovery loop on a cadence matched to the work (default ~5 min,
    configurable), **not** 60 s.
  - **Yield mechanism:** before starting each candidate, checks a user-active
    signal. If active, it sleeps and re-checks; it never blocks on a lock. The
    signal is a simple mtime heartbeat file (e.g.
    `~/.astra_persistent/user_active`) touched by the assistant/CLI when in use,
    considered stale after N minutes. This is intentionally the *opposite* of the
    old `pause_event.wait()` threading that deadlocked (v5.0).
  - Default idle activity (Phase 1): run the **proven** evolutionary engine on a
    rotating set of defined tasks (photo-z, star/gal/qso), ingesting any new
    machine-verified results via the (now-fixed) consumer.
- **Repoint the LaunchAgent.** The installed
  `~/Library/LaunchAgents/com.astra.discovery.plist` currently points at
  `sleep_aware_watchdog.py`; it (and the repo copy) are updated to launch the
  new supervisor. Watchdog keeps the DEVNULL fix (it is correct and applied).
  Stuck threshold stays generous (init is slow; 60 min is fine).
- **Never fall back to fiction.** If the supervisor cannot initialise the real
  engine, it logs and waits — it does **not** degrade to `FixedGenuineDiscoverySystem`
  canned emission.

### 4.6 Phase 1 verification

- Unit: safety.py rejects `import os`, `open()`, bare `__builtins__`; allows
  numpy/sklearn. rlimit actually caps a fork-bomb candidate. sandbox-exec blocks
  a network attempt.
- Unit: the write chokepoint rejects a record with no `verification` block
  (fiction is impossible).
- Unit: consumer dedup is correct after hydration (no duplicates on re-run).
- Integration: start the supervisor, confirm zero non-verified records are
  written over a 15-min idle window; confirm a real evolved PASS still ingests.
- The "fiction impossible" invariant is asserted by a test that feeds the
  canned init string through the path and asserts nothing is written.

---

## 5. Phase 2 — open-ended Eureka search (builds on Phase 1)

Phase 1's idle activity evolves **fixed** tasks. Phase 2 generalises the engine
so the idle loop searches for genuinely **new** claims.

### 5.1 Generalise the evolved artifact: claim + executable test

- Today the artifact is a single function (`estimate_redshift`) for a fixed
  task. Phase 2's artifact is a **(claim, test)** pair:
  - `claim`: a short natural-language scientific statement with a quantitative
    prediction (e.g. "In SDSS DR16, galaxies with W1−W2 > 0.5 show a
    mid-infrared excess consistent with >30% AGN fraction at z < 0.8").
  - `test`: executable code that loads **real archival data** (via the same
    real-data fetcher + provenance manifest already used) and returns an
    objective metric + a significance/false-alarm estimate.
- The LLM (via the §4.3 gateway) proposes `(claim, test)` diffs; the existing
  task-agnostic `EvolutionEngine` evolves them. Generality was already proven by
  adding a second task type (classification) — this is the next generalisation.

### 5.2 Gate 1 — real-data verification (generalised)

- Reuses the Phase 1 sandbox + evaluator. Fitness component 1 = "test runs on
  real data and the claimed effect is significant" (p-value / σ / false-alarm
  probability below a threshold). A claim that does not reproduce on real data
  fails here. This is the anti-fiction gate.

### 5.3 Gate 2 — literature novelty (new)

- For a claim passing gate 1, retrieve the top-k most similar papers
  (arXiv API + Semantic Scholar; cached, with a manifest, same "no fake data"
  discipline).
- The candidate's **specific quantitative claim** must not already be reported
  in retrieved abstracts/papers. Implementation: a retrieval + entailment check
  (grounded in retrieved text, not free LLM judgement) — if the claim is
  entailed by existing literature, it is marked **known** and rejected (or
  downgraded to "confirmation", never "Eureka").
- Honestly best-effort: this gate reduces textbook/literature restatement (the
  user's explicit requirement) but is not a perfect novelty oracle. It is
  logged as a retrieval result so a human can audit.

### 5.4 Fitness and promotion

- `fitness = passes_gate1 AND passes_gate2` (with secondary parsimony from the
  existing multi-objective selector). Only both-gate survivors are written via
  the Phase 1 chokepoint, with `verification` recording both the real-data
  metric and the novelty-retrieval result.

### 5.5 Phase 2 verification

- A deliberately-known claim (e.g. a textbook CMB fact) is fed through and must
  be **rejected by gate 2**.
- A deliberately-fabricated claim (effect that does not exist in the data) must
  be **rejected by gate 1**.
- End-to-end: one full idle cycle produces at most both-gate survivors; none are
  fiction; none are textbook restatements.

---

## 6. Risks and honest limitations

- **Phase 2 is research-grade.** Open-ended claim generation + automated novelty
  is genuinely hard. Phase 1 is engineered and verifiable; Phase 2 may need
  iteration and its novelty gate is best-effort, not oracle. The design refuses
  to over-claim: better to emit *fewer*, auditable, both-gate survivors than to
  resume high-cadence plausible text.
- **Init/deadlock surface.** ASTRA's heavy `__init__` (77 domains, ~44 s
  instantiate, recursion fallback) is a pre-existing hazard. The supervisor
  keeps the evolutionary engine decoupled from it and never falls back to
  fiction on init failure.
- **LLM cost.** Phase 2's claim generation consumes budget; the cadence and
  per-cycle LLM call cap must be configurable (default conservative).
- **macOS `sandbox-exec` is deprecated.** It works today and is the lightest
  native option; if it is removed in a future macOS release, the rlimit + AST
  layers still provide defence-in-depth and a Docker path can be added later.
- **Store migration is one-way.** The purge removes fakes/dupes; it is run
  dry-run-first and logged so it is auditable and reversible from the log.

---

## 7. File-level change manifest

**Phase 1**

- *Modify* `astra_core/autonomous_startup_discovery_v2.py` — remove fiction
  emission; remove `_generate_simple_query` from discovery path; add store
  hydration; route writes through the chokepoint.
- *Modify* `astra_core/scientific_discovery/genuine_discovery_validator.py` — no
  hardcoded-genuine fallback; require machine verification.
- *Modify* `astra_core/scientific_discovery/evolved_discovery_consumer.py` —
  dedup against hydrated set (already correct once hydration lands).
- *Create* `astra_core/scientific_discovery/discovery_store.py` — single write
  chokepoint (`append_verified(discovery)` requiring a `verification` block) +
  load/dedup helpers. Used by consumer and any emitter.
- *Create* `astra_core/intelligence/llm_gateway.py` — canonical LLM client.
- *Modify* `evolved_analysis/proposer.py` — use the gateway (thin refactor).
- *Create* `evolved_analysis/safety.py` — AST import allowlist + os-call check.
- *Modify* `evolved_analysis/eval_worker.py` — apply rlimit before exec; run
  under sandbox-exec.
- *Modify* `evolved_analysis/evaluator.py` — call safety check; wrap worker in
  `sandbox-exec`.
- *Create* `evolved_analysis/astra_worker.sb` — sandbox-exec profile.
- *Create* `astra_core/autonomous_discovery_supervisor.py` — supervisor with
  cadence loop + user-active yield + Phase 1 idle activity.
- *Create* `astra_core/tools/purge_genuine_store.py` — one-time purge
  (dry-run-first, logged).
- *Modify* `~/Library/LaunchAgents/com.astra.discovery.plist` and repo
  `com.astra.discovery.plist` — launch the supervisor.
- *Create* tests under `astra_core/tests/` for: chokepoint rejection, safety
  allowlist, rlimit cap, sandbox network block, dedup-after-hydration,
  fiction-impossible invariant.

**Phase 2**

- *Create* `evolved_analysis/claim_task.py` — `(claim, test)` artifact +
  evaluator generalisation.
- *Create* `evolved_analysis/novelty_gate.py` — arXiv/Semantic-Scholar
  retrieval + entailment check, cached with manifest.
- *Modify* `astra_core/autonomous_discovery_supervisor.py` — add open-ended
  Eureka mode as an idle activity alongside the Phase 1 tasks.
- *Create* Phase 2 tests (known-claim rejected by gate 2; fabricated claim
  rejected by gate 1).

---

## 8. Rollout

1. **Triage (immediately):** stop the live fiction emitter so pollution ceases
   while implementing.
2. Phase 1 implement → verify each component → run the store purge (dry-run,
   then real) → repoint LaunchAgent → start supervisor → observe a 15-min idle
   window with zero non-verified writes.
3. Phase 2 implement → verify gates with the known/fabricated claim probes →
   enable as an idle activity with a conservative cadence/budget.
4. Update `CLAUDE.md` / system-status docs to reflect the new architecture
   (honestly, including that Phase 2 novelty is best-effort).

---

## 9. Success criteria

- **No fiction, ever:** over an unattended 24 h window, zero records appear in
  the genuine store without a machine `verification` block. (Testable invariant.)
- **Autostart + self-heal:** after reboot/login the supervisor is up within the
  watchdog window and recovers from a killed child without emitting fiction.
- **Yields to the user:** when the assistant is active, the loop stops starting
  new candidates within one candidate's duration; resumes when idle.
- **Real output:** Phase 1 ingests machine-verified results from the proven
  engine; Phase 2 additionally produces both-gate survivors that are neither
  fabricated nor textbook restatements.

---

## 10. Implementation status (2026-07-11) — what was built and verified

Both phases implemented and verified by execution (not assertion). 11 regression
tests pass (`astra_core/tests/test_discovery_chokepoint.py`).

**Phase 1 — stop the bleeding + trustworthy plumbing: DONE**
- `astra_core/scientific_discovery/discovery_store.py` (NEW) — the single write
  chokepoint. `append_verified` rejects any record without a machine
  `verification` block; load/dedup/purge helpers. Verified: 209 fictional +
  8 duplicate records purged (218 → 1 verified).
- `astra_core/autonomous_startup_discovery_v2.py` (MODIFIED) — fiction path
  disabled (`_call_astra_with_timeout` returns None: STAN `answer()` cannot
  produce verification); store hydrated + deduped on startup; `_save_discovery_store`
  writes only verified records. Fixes the per-cycle duplication bug.
- `astra_core/intelligence/llm_gateway.py` (NEW) — canonical Anthropic gateway;
  `evolved_analysis/proposer.py` refactored to use it (via `evolved_analysis/_llm.py`,
  a decoupled file-path loader that avoids triggering the heavy `astra_core/__init__`).
- `evolved_analysis/safety.py` (NEW) + `eval_worker.py` rlimits + `evaluator.py`
  sandbox-exec wrap + `astra_worker.sb` (NEW) — defence-in-depth for generated
  code. Verified: legit candidate grades correctly (σ_NMAD=0.0213) through the
  full sandbox; malicious `import os` blocked before exec.
- `astra_core/autonomous_discovery_supervisor.py` (NEW) — the always-on,
  user-yielding supervisor. Cadence loop, lock-free heartbeat yield
  (`~/.astra_persistent/user_active`), ingests verified records, optionally runs
  evolution episodes (auto-disabled with no LLM token — safe launchd default).
  Sources LLM creds from `~/.astra_persistent/llm_env` so no secret sits in the
  plist. Running under the `com.astra.discovery` LaunchAgent (plist repointed).
- Verified live: supervisor cycles cleanly under launchd; store holds 1 verified
  record, 0 fiction, across an idle window.

**Phase 2 — open-ended Eureka search (two-gate EVALUATE): DONE (research-grade)**
- `evolved_analysis/claim_task.py` (NEW) — the (CLAIM, `run_claim`) artifact +
  Gate-1 significance check.
- `evolved_analysis/claim_eval_worker.py` (NEW) — sandboxed Gate-1 worker.
- `evolved_analysis/novelty_gate.py` (NEW) — Gate 2: arXiv/S2 retrieval +
  grounded LLM judge; a claim is "known" if explicitly entailed OR a foundational
  textbook result. Cached with a provenance manifest.
- `evolved_analysis/run_claim_search.py` (NEW) — orchestrates both gates; emits
  ONLY both-gate survivors via a chokepoint-compatible verification block.
  Enabled as the supervisor's idle activity by setting
  `ASTRA_EVOLUTION_MODULE=evolved_analysis.run_claim_search`.
- Verified live: Gate 1 rejects fabricated/non-significant claims (effect≈0);
  Gate 2 catches known/foundational claims (Tully–Fisher, g-r↔redshift,
  concentration–colour). A 3-claim LLM search correctly emitted nothing (two
  non-real, one known).

**Honest limitations (unchanged from §6)**
- The novelty gate is best-effort, not an oracle. It catches explicit literature
  restatements and foundational textbook results; a genuinely novel result that
  happens to resemble a known one could be wrongly marked "known" (conservative).
- No genuinely-novel Eureka claim was emitted in testing — expected, since real
  novelty is rare and the SDSS colour space is well-trodden. The plumbing is
  trustworthy; finding a real Eureka result is a matter of running the search at
  scale over richer data (more features, more surveys) and auditing survivors.
- The legacy `CLAUDE.md`/status docs still describe the old fiction emitter as
  "FULLY OPERATIONAL"; they are stale and should be updated separately.

