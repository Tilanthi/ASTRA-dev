# ASTRA ← AlphaEvolve Integration Plan

**Purpose.** A durable, self-contained plan for evolving ASTRA from a
single-shot, LLM-judged text generator into an AlphaEvolve-style evolutionary
discovery loop with **machine-checkable evaluation on real data**. Written so
work can resume after context loss — read this file top to bottom.

---

## 0. If you are resuming, read this first

**Goal of the whole effort:** give ASTRA the one component it is missing and
that AlphaEvolve proves is the whole game — an automated, machine-checkable
`EVALUATE` function on real data — then build the evolutionary loop, context
feedback, and ensemble around it.

**What is DONE:**
- **Recommendation 1 (gene-based POC)** — `astra_core/scientific_discovery/evolved_analysis/`
  (real_data.py, evolve_photoz.py): evolutionary loop on REAL SDSS data. Verified
  PASS: σ_NMAD 0.0491 → 0.0224 (+54%), η 0.036 → 0.005 on held-out data.
- **Recommendation 2 (evolve executable code via LLM diff-proposer)** —
  `astra_core/scientific_discovery/evolved_analysis/`. The evolved artifact is a Python function
  `estimate_redshift`; a live LLM proposes diffs/rewrites; graded by the REAL
  leapcore `FitnessEvaluator` (loaded by file path, decoupled from the auto-start
  service) running each candidate in an isolated subprocess. Verified PASS: σ_NMAD
  0.0491 → 0.0213 (+57%), η 0.036 → 0.005 on held-out data. LLM proposer: 17/17
  calls produced valid code, 13/17 beat their parent; best program was
  LLM-authored (raw mags + 4 colours → regularised GradientBoostingRegressor).
  Persisted to `~/.astra_persistent/evolved_programs/`.
- **Recommendation 3 (ablation: context / ensemble / meta-prompt)** —
  `astra_core/scientific_discovery/evolved_analysis/ablation.py` + `meta_prompt.py` + proposer/worker
  extensions. Fig-7-style ablation on real photo-z (equal budget/condition):
  every condition beat naive seed (TEST σ 0.0491 → ~0.020, ~58%); context→ensemble
  →meta lower the selection σ monotonically (0.0187→0.0183→0.0180) and ~double
  the strong-parent improvement rate (3–4/12→7/12). Held-out TEST deltas within
  noise at this budget → flagged as needing rec-4 k-fold/cascade.
- **Recommendation 4 (search quality: CV / cascade / MAP-Elites / multi-obj)** —
  `astra_core/scientific_discovery/evolved_analysis/selection.py` + `archive.py` + `run_quality.py`.
  Headline: 5-fold CV selection shrinks the selection→held-out-TEST gap ~33%
  (0.0021→0.0014), raises corr(·,TEST) (+0.758→+0.815), and exposes the rec-3
  single-EVAL "trend" as noise — i.e. trustworthy measurement. Plus cascade
  pruning, MAP-Elites multi-family diversity, multi-objective parsimony. (Async
  throughput pipeline deferred.)

**What is NEXT (all four core recommendations + most hardening DONE):** see
"Work-package status" below. Remaining: OS-level sandbox for untrusted code;
period-finding task (needs lightkurve install or Gaia DataLink auth — deferred,
see open question).

## Work-package status (hardening, WP2–6)

- **WP2 — Promote driver onto a clean engine ✅.** `leapcore_evolution.py`'s
  `LEAPCoreEvolution` now takes an injectable `rng` (backward-compatible; default
  = global `np.random`). New canonical `engine.py` `EvolutionEngine` reuses the
  real leapcore classes, is RNG-injected + proposer-driven, and supersedes the
  hand-rolled loops. Demo `run_engine.py`: seed 0.0491→0.0210, CV gap 0.0011.
- **WP3 — Production home ✅.** Package relocated (copied) to
  `astra_core/scientific_discovery/evolved_analysis/` (relative/absolute imports
  rewritten, deeper-nesting paths fixed). Verified it imports + runs **without**
  triggering `astra_core/__init__` (decoupled). Run as
  `PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.run_engine`.
  (Legacy `alphaevolve_poc/` has been deleted; this is the canonical home.)
- **WP4 — Multi-seed ablation ✅ (3 seeds, error bars).** `run_multiseed.py`;
  held-out TEST σ mean±std over seeds {42,7,123}:
  `floor_seed 0.0215±0.0033` · `no_context 0.0203±0.0013` · `context 0.0192±0.0003`
  · `ensemble 0.0193±0.0014` · `meta_prompt 0.0197±0.0002` · `full 0.0198±0.0015`.
  With error bars the signal sharpens: **floor is worst AND noisiest** (±0.0033);
  **rich context is the clearest win — best (0.0192) and most stable (±0.0003)**,
  separated from floor by ~7× its own std; ensemble/meta/full cluster within noise
  of context but push the beat-strong-parent rate back up (5.7–6.3 vs 4.3–4.7).
  Log: `~/.astra_persistent/evolved_programs/multiseed_ablation.json`.
- **WP5 — Second real task ✅ (generality).** SDSS STAR/GALAXY/QSO classification
  (different problem type + metric = balanced accuracy). `cls_*.py` +
  `run_classify.py` via the same engine. Seed bal-acc 0.333→**0.912** (STAR 0.90 /
  GALAXY 0.87 / QSO 0.96) on real balanced data. (Period finding **skipped** per
  user decision — generality already proven; reliable time-domain light curves
  need lightkurve [env change] or Gaia DataLink [auth]. The engine is task-agnostic
  and ready if either becomes available.)
- **WP6 — Async throughput pipeline ✅.** `parallel.py`
  `ParallelEvolutionEngine` (ThreadPoolExecutor; snapshot population → λ
  propose+eval concurrently → single-writer merge). Demo `run_parallel.py`:
  **1.86× wall-clock speedup** at 4 workers, quality comparable (σ≈0.020).

## Integration into astra_core (honest status)

Is `evolved_analysis` seamlessly built into ASTRA? **Partially — and now more so.**

**What IS integrated (verified):**
- **Lazy-registered & reachable as an ASTRA subpackage.** `astra_core/scientific_discovery/__init__.py` has a PEP 562 `__getattr__`; `import astra_core.scientific_discovery as s; s.evolved_analysis` and `from astra_core.scientific_discovery.evolved_analysis import engine` BOTH work, without paying the evolved_analysis load when scientific_discovery itself is imported. Internal imports are relative, so the package runs in two modes: ASTRA subpackage (`from astra_core.scientific_discovery.evolved_analysis import …`) and CLI (`PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.…`).
- **Reuses real ASTRA evolutionary classes** — subclasses the real `astra_core/intelligence/leapcore_evolution.py` `FitnessEvaluator`/`Chromosome` (loaded by file path); that file's `LEAPCoreEvolution` now accepts an injectable `rng` (backward-compatible).
- **Writes ASTRA-schema discoveries with machine verification.** `discovery_emit.py` emits `{title, abstract, discovery_type, timestamp}` records — ASTRA's format — **plus a `verification` field** with the machine-computed metric (σ_NMAD / balanced_accuracy, eval + held-out TEST, n, data source, program hash). This is the field ASTRA's current "genuine discoveries" lack (they are unverified textbook prose). Verified end-to-end: a PASS run wrote a real record to `~/.astra_persistent/evolved_discoveries.json`.

**What is NOT (yet) integrated (honest):**
- ~~Not called by ASTRA's discovery pipeline / auto-start.~~ **NOW WIRED (this pass).** `astra_core/scientific_discovery/evolved_discovery_consumer.py` `consume_evolved_discoveries(system)` runs once at the top of each discovery cycle in `autonomous_startup_discovery_v2.py` (guarded, lazy-imported). It folds new machine-verified records from `evolved_discoveries.json` into the loop's `genuine_discoveries` store as ASTRA discoveries (`validation.quality='GENUINE'`, `is_genuine=True`, verification preserved), idempotently (dedup by `verification.program_hash` — survives cycles + restarts). It NEVER raises and does one small non-blocking file read, so it cannot deadlock the loop. Verified in isolation (ingest / idempotent / new-record / missing-file / garbage all pass). The service was restarted to activate it; consumption is logged as "INGESTED machine-verified evolved discovery". **Live activation (honest):** the restarted discovery process hangs at 0% CPU during ASTRA's OWN init (stops mid domain-loading, before the loop is reached) — a PRE-EXISTING init hang (the v5–v7 deadlock surface), not caused by this change (the consume call is inside the loop body; the old process was already sick, cycle-225 spamming). So the consumer is **verified in isolation + correctly wired**, but cannot be exercised live until ASTRA's discovery-init hang is fixed (separate deep work, out of scope here).
- **Code generation uses the direct Claude gateway, NOT `system.answer()`.** Probe result: STAN's `system.answer()` is ~44s + recursion-fallback to instantiate, and returns a **canned "high-redshift universe" essay ignoring the prompt** for BOTH code-gen and narration requests. So STAN is unusable as a code proposer *or* narrator. The `--stan` narration path exists (subprocess, auto-start patched) but defaults OFF with this documented; template narration (factual) is the default.
- **Writes to a separate discoveries file** (`evolved_discoveries.json`, not the live `genuine_discoveries.json` the service writes) to avoid write races; a `merge_into_genuine()` helper (dry-run by default) folds them in when the service is stopped.
- **Does not use ASTRA's domain registry / `astro_databases` / persistent memory** — uses its own real-data fetchers.

**Net:** genuinely importable from ASTRA and writing verified records back in ASTRA's schema (the two highest-value integration points), but not yet a participant in the live discovery loop — blocked by ASTRA-side issues (auto-start deadlock surface, STAN returning canned content) outside the safe scope of this pass.

### Discovery-service init hang — root cause + fix (diagnosed via ultracode workflow)

**Root cause (adversarially verified, conf 0.96): subprocess pipe deadlock.** The
LaunchAgent runs `sleep_aware_watchdog.py`, whose `start_discovery()`
(`sleep_aware_watchdog.py:163-168`) spawns the discovery process with
`stdout=PIPE, stderr=PIPE` and **never drains them** (no communicate/read/readline/
drain thread anywhere). The child `start_autonomous_discovery.py:49-56` configures
logging with a `FileHandler('.astra_autonomous.log')` AND a `StreamHandler()`
(defaults to `sys.stderr` → the 64KB pipe), plus bare `print()`s → the 16KB stdout
pipe. Both pipes fill; the next flush blocks the main thread forever in
`_bufferedwriter_flush_unlocked` (2620/2620 `sample` frames), 0% CPU. The
`.astra_autonomous.log` froze at 860408639 bytes *because* the main thread wedged
on the pipe flush (file writes themselves are fine). Chronic: the watchdog
tolerates the corpse 3600s then `pkill -9` respawns into the identical config.

**Fix applied (minimal, safe):** `subprocess.PIPE` → `subprocess.DEVNULL` at both
spawn sites (`sleep_aware_watchdog.py:166-167` — the one the LaunchAgent runs — and
`astra_watchdog.py:128-129` for completeness). No threading/loop/child-code change;
the child still self-logs to `.astra_autonomous.log` via FileHandler, so no
diagnostic loss. Deploy order used: unload agent → kill hung child → edit →
truncate the 821 MB log → reload. Optional longer-term (not done): swap the child's
FileHandler for a RotatingFileHandler and/or point the StreamHandler at devnull.
Live verification (process reaches cycle 1 + consumes `evolved_discoveries.json`)
in progress.

**VERIFIED LIVE (after fix):** the discovery process no longer hangs — it reaches
`DISCOVERY CYCLE 1` and the consumer fired: `✅ INGESTED machine-verified evolved
discovery … sigma_NMAD=0.0199, TEST=0.0213 … consumed 1 new … into the genuine
store.` The machine-verified record is now in ASTRA's `genuine_discoveries.json`
(`source: evolved_analysis`, `verification` field present, `quality=GENUINE`).
Loop cycles advance normally (1→2→3, 60s cadence).

**Surfaced pre-existing ASTRA bugs (NOT caused by these changes, non-blocking for
the consume, but worth a follow-up):**
1. `maximum recursion depth exceeded` in the genuine-discovery init → caught, falls
   back to `FixedGenuineDiscoverySystem` (the loop + consume still run).
2. **Duplicate log emission (~7× per event)** — the root logger has ~7 handlers
   attached, so every log line is printed ~7×. This is what ballooned
   `.astra_autonomous.log` to 821 MB (disk was 97% full). Fix: dedup handlers at
   startup (`force=True` basicConfig or clear existing handlers) + a
   RotatingFileHandler.
3. `_save_discovery_store` re-appends the in-memory list to the file's existing
   list every cycle → duplicate records accumulate in the genuine store over time
   (affects ASTRA's own discoveries too).

**The four recommendations, one line each:**
1. **Evaluator first** — make discoveries machine-gradeable on real data. *(POC done.)*
2. **Wire the evolutionary loop** — connect the existing `leapcore_evolution.py`
   + an LLM code-diff proposer to a real evaluator.
3. **Cheap ablation wins** — feed past discoveries into prompts; add an LLM
   ensemble; co-evolve the prompt.
4. **Quality-of-search** — cascade evaluation, MAP-Elites/island diversity,
   multi-objective scoring.

---

## 1. The core insight (why)

AlphaEvolve (DeepMind) is an evolutionary LLM coding agent. It beat Strassen's
matrix-multiplication record after 45 years and optimized Google's Borg
scheduler, TPU circuits, and Gemini training kernels. Its recipe:

```
parent programs --LLM-diff--> child programs --EVALUATE--> real scalar
      ^                                                          |
      +------------- program database (elites + diversity) <-----+
```

**The decisive fact from the paper:** the loop's honesty comes entirely from
machine feedback. Their ablations show every component matters — but the
foundation is an automated evaluator. The paper's own stated limitation:

> "The main limitation of AlphaEvolve is that it handles problems for which it
> is possible to devise an automated evaluator … there are domains such as the
> natural sciences where only some experiments can be simulated or automated."

Two escape hatches the paper itself provides (both apply to astrophysics):
- **Instrumental-goal framing:** when the answer isn't an algorithm, *evolve an
  algorithm that finds it* — "a surprisingly effective strategy compared to
  searching for the solution directly."
- **Evolve the search heuristic, not the object:** their biggest math wins came
  from evolving *search programs* scored by fast objective functions.

Astrophysics is full of fast, objective, machine-grade-able functions: χ² fit
residuals, false-alarm probability, detection S/N, σ_NMAD, outlier fraction,
BIC/AIC, periodogram peak power, cross-validation error, completeness/purity.
**These are the `EVALUATE` functions AlphaEvolve needs.**

---

## 2. ASTRA's current architecture — the gaps (verified in code)

Recon findings (with file references):

| Aspect | ASTRA today | AlphaEvolve | Where |
|---|---|---|---|
| Discovery loop | single `system.answer(query)` call, 20s timeout | evolutionary loop over a program DB | `astra_core/autonomous_startup_discovery_v2.py` ~L359 |
| Query | `random.choice()` of 3 sentence templates | parent + inspirations + rendered results | `_generate_simple_query` ~L463 |
| Output | natural-language string truncated to 300 chars | executable code | `_create_discovery_from_result` ~L394 |
| Scoring | **LLM-as-judge + regex pattern match** | code execution → objective scalar | `scientific_discovery/genuine_discovery_validator.py` ~L161 |
| Feedback | past discoveries NOT fed back into prompts | parents+scores ARE the prompt | (absent) |
| Ground truth | none | required | — |
| Evolution | `leapcore_evolution.py` exists but **unused** | core engine | `astra_core/intelligence/leapcore_evolution.py` |

**The tell-tale failure:** a stored "genuine discovery" was textbook 1 M☉
stellar evolution (10 Gyr MS lifetime) that the validator missed — because the
validator pattern-matches text from the same model family that generated it.
That circularity is exactly the failure mode ASTRA's own v6.0 "Metric
Specification Gate" tried to retire, and exactly what machine feedback fixes.

**Mock-data trap (important):** folders named like real data contain
ASTRA-generated fakes — e.g. `W3_HGBS_filaments/HGBS_SOURCE_DATA/*/core_catalog_*.csv`
is header-stamped *"Generated by ASTRA Discovery System"*, and
`RASTI_paper/Example6/sdss_galaxies_realistic.csv` is simulated (unphysical
mags 27–29). **Always fetch real data from primary archives; never trust
in-tree "data".** (The POC fetches live from SDSS CAS and writes a manifest.)

---

## 3. Recommendation 1 — Evaluator first  ✅ POC DONE

**Principle:** before any evolutionary machinery helps, there must be one real
`EVALUATE(solution) → scalar` that runs on real data. Without it, selection
optimizes a hallucination.

**Reference implementation:** `astra_core/scientific_discovery/evolved_analysis/` (photo-z on real SDSS).
- `EVALUATE` = `evaluate()` in `evolve_photoz.py`: TRAIN/EVAL/TEST split of real
  galaxies; fitness = `-(σ_NMAD + 3·η)` on the EVAL split; TEST scored once at end.
- **Verified:** +54% σ_NMAD improvement, machine-graded, on held-out real data.

**How to pick the next real task (menu, each has an honest `EVALUATE`):**
- **Photo-z** (done) — SDSS ugriz → z_spec; metric σ_NMAD/η.
- **Period finding** — real variable-star light curves (TESS/VizieR) → published
  period; metric recovery fraction within tolerance. *Most iconic "evolve the
  search algorithm" task.*
- **Transient/vocal detection** — real light curves → injected/recovered signals;
  metric detection significance + false-alarm probability (injection-recovery on
  REAL survey noise is legitimate; fully synthetic datasets are not).
- **Spectral line fitting** — real spectra → known line parameters; metric χ²/dof
  + velocity accuracy vs independent measurement.
- **Filament/core analysis** — REAL Herschel/HGBS maps (re-download from the
  archive; do not use the in-tree ASTRA-generated catalogs); metric residual or
  recovery of published structures.

**Acceptance criterion:** a single `EVALUATE` that (a) runs on real archival
data with an auditable provenance manifest, (b) returns a scalar computable by
code (not an LLM), (c) shows the seed is beatable. ✅ met by the POC.

---

## 4. Recommendation 2 — Wire the evolutionary loop  ✅ DONE

**Goal:** connect ASTRA's existing-but-dormant evolutionary engine to a real
evaluator, and add an LLM code-diff proposer (AlphaEvolve's "creative generation").

**Implementation:** `astra_core/scientific_discovery/evolved_analysis/` (see its README). Subclasses
the REAL `astra_core/intelligence/leapcore_evolution.py` `FitnessEvaluator`
(loaded by file path → no `astra_core/__init__.py`, no auto-start); evolved
artifact = executable `estimate_redshift`; `LLMProposer` (live Claude) +
`GeneticProposer` (offline fallback); each candidate runs in an isolated
subprocess with hard timeout; μ+λ niche-diverse driver; persisted to
`~/.astra_persistent/evolved_programs/`.

**Verified PASS** (held-out TEST, real SDSS): σ_NMAD 0.0491 → 0.0213 (+57%),
η 0.036 → 0.005. LLM proposer: 17 calls, 17/17 valid code, 13/17 beat parent;
winner was an LLM-authored rewrite (raw mags + 4 colours → regularised
GradientBoostingRegressor). Run log: `~/.astra_persistent/evolved_programs/run_*.json`.

**Remaining for production hardening (not blocking rec 3/4):**
- OS-level sandbox for untrusted code (current = subprocess + timeout, fine for
  trusted-libs code locally).
- Promote the thin driver onto `leapcore_evolution.LEAPCoreEvolution`'s full
  engine once its global-`np.random` / V36 couplings are factored out.
- Move the package into `astra_core/scientific_discovery/evolved_analysis/`
  (intended final home) once decoupling is proven over time.

---

## 5. Recommendation 3 — The cheap ablation wins  ✅ DONE

**Implementation:** `astra_core/scientific_discovery/evolved_analysis/ablation.py` (+ extensions to
`proposer.py`, `eval_worker.py`, new `meta_prompt.py`). Implemented all three
features and ran an AlphaEvolve Fig-7-style ablation on the real photo-z task
(equal LLM budget per condition, fixed seed):

- **(a) Context feedback** — eval worker returns a binned residual *error
  profile*; proposer renders it into the prompt (AlphaEvolve's "rendered
  evaluation results"). Toggle `context_level="minimal"` vs `"rich"`.
- **(b) LLM ensemble** — `LLMProposer(model=…)` per instance; ablation routes
  ~⅓ of proposals to Sonnet 5 (breakthroughs) + rest to Haiku 4.5 (volume).
- **(c) Meta-prompt co-evolution** — `meta_prompt.py`: population of strategy
  hint-sets scored by downstream program fitness; epsilon-greedy + LLM-spawned
  variants + culling.

**Result (single run, steps=12/condition):**
- **Robust:** every condition beat the naive seed on held-out data (TEST σ
  0.0491 → ~0.020–0.021, ~58% reduction) — reproduces AlphaEvolve's
  "no-evolution is worst."
- **Per-feature (selection metric + improvement rate):** context → ensemble →
  meta lowers EVAL σ monotonically (0.0187 → 0.0183 → 0.0180) and ~doubles the
  rate of proposals beating a strong parent (3–4/12 → 7/12). Ensemble got wins
  from both tiers; meta learned to prefer the winning hints (`colors`, `biasfix`).
- **Honest caveat:** held-out TEST deltas are within noise at this budget, and
  TEST diverges from EVAL → single-split overfitting. Publication-grade Fig-7
  needs more steps + multi-seed + k-fold/cascade (rec 4). Log:
  `~/.astra_persistent/evolved_programs/ablation.json`.

**Core acceptance criterion met:** each feature measurably improves the real
selection metric and improvement rate (directionally matching AlphaEvolve),
while the held-out separation is correctly flagged as needing rec-4 rigor.

**Production integration (when promoting to astra_core):**
- (a) into `astra_core/autonomous_startup_discovery_v2.py` prompt construction
  (parent + inspirations + rendered metrics from `astra_discoveries.db`).
- (b) router into `astra_core/core/unified_enhanced.py`.
- (c) `astra_core/scientific_discovery/meta_prompt_evolution.py`.

---

## 6. Recommendation 4 — Quality-of-search  ✅ DONE (core); async pipeline deferred

**Implementation:** `astra_core/scientific_discovery/evolved_analysis/selection.py` (K-fold CV +
cascade + multi-objective `SelectionEvaluator`), `archive.py` (MAP-Elites +
diversity-aware parent sampling), `run_quality.py` (demos). `eval_worker.py` grew
`cv:K` / `cv:K:i` out-of-fold CV over the TRAIN+EVAL pool (TEST held out).

- **(a) Cascade** — `SelectionEvaluator(cascade=True)`: a one-fold stage-1 probe
  prunes clearly-bad programs (σ > `cascade_thresh`) before the full K-fold.
- **(b) MAP-Elites + islands** — `archive.py`: best program per behavioral cell
  `(model_family, complexity_bucket)`; parents sampled across cells (island
  diversity without needing crossover, since the LLM proposer edits code).
- **(c) Multi-objective** — `parsimony_weight>0` adds a simplicity term to the
  scalar fitness (σ_NMAD + 3η + λ·parsimony).
- **(d) Async throughput pipeline** — **deferred** (was always gated on 1–3 being
  honest, which they now are). Remaining work for scale-out.

**Result (the headline — CV fixes the rec-3 overfitting caveat).** Re-scoring the
six rec-3 condition-bests by 5-fold CV: mean |selection−TEST| gap 0.0021 → 0.0014
(~33% smaller); corr(metric, TEST) +0.758 → +0.815; the rec-3 single-EVAL
"per-feature trend" (spread 0.0013) collapses under CV (spread 0.0011 ≈ TEST
0.0010) → CV correctly refuses to declare a winner among the rich conditions.
Experiment A (coarse pool): when candidates differ clearly (σ spread ≫ split
noise), single-EVAL and CV agree — single-split is fine for coarse selection; CV
is the safety net for fine distinctions. Experiment B (all four features loop,
10 steps): best CV σ 0.0477→0.0194 (seed Linear→GradientBoosting), held-out TEST
σ 0.0203 with |CV−TEST| gap only **0.0009** (vs rec-3's noisy 0.002–0.006),
MAP-Elites kept 3 cells / 2 families, cascade pruned 0/11 (strong proposer),
beat_parent 7/10. Calibration finding: parsimony weight must be ≪ the primary
scale (0.3 let simplicity dominate; 0.002 is a tie-breaker). Log:
`~/.astra_persistent/evolved_programs/rec4_quality.json`.

**Core win:** rec 4 makes the *measurement* trustworthy (cross-validated,
smaller generalization gap) and keeps the search diverse (multi-family archive) —
exactly the rigor rec 3 flagged as missing. Log: `rec4_quality.json`.

**Production integration (when promoting to astra_core):**
- CV/cascade/multi-obj selection → wrap any real `FitnessEvaluator` the way
  `SelectionEvaluator` wraps `RealDataProgramEvaluator`.
- MAP-Elites → replace the simple population in the discovery driver.
- Async pipeline → only once a single-node loop is run at scale (rec 4(d)).

---

## 7. AlphaEvolve → ASTRA component map

| AlphaEvolve | ASTRA integration point | Status |
|---|---|---|
| Automated `EVALUATE` | `RealDataProgramEvaluator(FitnessEvaluator)` on real archives | ✅ rec 1+2 |
| Evolve code via LLM diffs | `astra_core/scientific_discovery/evolved_analysis/proposer.py` (`LLMProposer`) | ✅ rec 2 |
| Program database (persist + niches) | `~/.astra_persistent/evolved_programs/` + niche elites | ✅ rec 2 (MAP-Elites rec 4) |
| Rich context + rendered results in prompt | `code_evolve/eval_worker.py` (error profile) + `proposer.py` (`context_level`) | ✅ rec 3 |
| LLM ensemble (Flash+Pro) | `code_evolve/ablation.py` routing (Haiku+Sonnet); `LLMProposer(model=)` | ✅ rec 3 |
| Meta-prompt co-evolution | `code_evolve/meta_prompt.py` (`HintSetPopulation`) | ✅ rec 3 |
| K-fold CV selection (trustworthy measurement) | `code_evolve/selection.py` (`SelectionEvaluator`) + `eval_worker.py` `cv:K` | ✅ rec 4 |
| MAP-Elites + islands (diversity) | `code_evolve/archive.py` (`MAPElitesArchive`) | ✅ rec 4 |
| Cascade evaluation | `SelectionEvaluator(cascade=True)` (one-fold stage-1 gate) | ✅ rec 4 |
| Multi-objective scoring | `SelectionEvaluator(parsimony_weight=)` | ✅ rec 4 |
| Async throughput pipeline | (deferred; decouple from LaunchAgent) | ☐ rec 4d |

---

## 8. Guardrails (do not regress)

- **No mock data, ever.** Fetch real data from primary archives; write a
  provenance manifest (SQL + source + row count + timestamp) like the POC. Do
  not trust in-tree "data" folders — several are ASTRA-generated fakes (§2).
- **No LLM judging its own output as the *selection* signal.** LLM-as-judge is
  fine for *soft* auxiliary hints (paper §1.3), never as the primary fitness.
- **Keep the evolutionary process decoupled from the `com.astra.discovery`
  LaunchAgent** to avoid the deadlock history documented in CLAUDE.md v5.0–v7.0.
- **Sandbox + timeout every `EVALUATE`** (LLM-generated code is untrusted):
  reuse `astra_core/core/thread_safe_timeout.py`.
- **Hold out a TEST split** scored once at the end; selection must never see it.

---

## 9. Resume checklist

- [x] Rec 1 POC — `astra_core/scientific_discovery/evolved_analysis/` verified PASS.
- [x] Rec 2 — `astra_core/scientific_discovery/evolved_analysis/` verified PASS (LLM diff-proposer +
      real leapcore FitnessEvaluator + subprocess sandbox + program DB).
- [x] Rec 3 — `astra_core/scientific_discovery/evolved_analysis/ablation.py` + `meta_prompt.py`
      verified (Fig-7-style ablation; features help on selection metric +
      improvement rate; held-out needs rec-4 rigor).
- [x] Rec 4 — `selection.py` + `archive.py` + `run_quality.py` verified
      (CV selection shrinks gap to TEST ~33% + higher corr; cascade; MAP-Elites
      diversity; multi-objective parsimony). Async pipeline (4d) deferred.
- [x] WP2 — promoted `EvolutionEngine` + rng-injectable leapcore.
- [x] WP3 — production home `astra_core/scientific_discovery/evolved_analysis/`.
- [x] WP4 — 3-seed ablation (`run_multiseed.py`).
- [x] WP5 — second real task (SDSS classification) via the same engine.
- [x] WP6 — async/parallel pipeline (`parallel.py`, 1.86× speedup).
- [x] Delete legacy `alphaevolve_poc/` (done — relocated to evolved_analysis).
- [ ] Optional follow-ups: OS-level sandbox; period-finding task (**skipped per
      user decision** — needs lightkurve install or Gaia DataLink auth; re-open
      if either becomes available; engine is task-agnostic and ready).
- Each recommendation: A/B it against an ablated baseline on a fixed real task
  and report the real metric (mirror AlphaEvolve Fig 7).
