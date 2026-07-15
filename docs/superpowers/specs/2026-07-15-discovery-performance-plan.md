# ASTRA Discovery-Performance Improvement Plan

- **Date:** 2026-07-15  ·  **Status:** Phase 0 done (bottleneck confirmed); Phase 1a in progress
- **Restartable:** a fresh session can read this + CLAUDE.md (v14.8) and continue. Last commit before this spec: `a7d0cf9`.

## Context (current pipeline, v14.8)
ASTRA's autonomous Phase-2 claim search is mechanically healthy: fiction-free
chokepoint + two-gate EVALUATE (Gate-1 real-data significance, Gate-2 arXiv novelty),
a 7-dataset data lake (SDSS optical ×3, Gaia astrometry, Gaia variables, WISE mid-IR,
+ legacy sdss_photoz), an always-on supervisor rotating the productive niches, and a
self-improvement layer (predict/surprise, measured RSI loop, Brier-scored capability
index). It produces genuine discoveries (40 both-gate survivors). The question now is
**throughput + quality of genuine novelty**, not plumbing.

## Confirmed diagnosis (Phase 0, 2026-07-15) — the binding constraint
Per-candidate funnel from `claim_verdicts.jsonl` (745 non-seed candidates):

| Terminal outcome | Count | % | Meaning |
|---|---|---|---|
| **gate1_fail** | **557** | **74%** | proposed relation is NOT statistically significant |
| gate2_known | 105 | 14% | significant but textbook (Gate-2 rejects) |
| novel_emit | 40 | 5% | **success** (both-gate survivor) |
| triviality_block | 19 | 2% | near-deterministic/few-band identity |
| holdout_block | 13 | 1% | df_eval-only code (fix mostly holding) |
| gate2_retrieval_failed | 10 | 1% | transient arXiv (fix mostly holding) |

Gate-1 pass = 188/745 (**25%**). Novel fraction of Gate-1 passers = 40/188 = **21%**.

**Binding constraint = candidate-generation quality (gate1_fail, 74%).** The proposer
guesses which column-combinations correlate and is wrong 3× in 4. The novelty gate is
NOT the bottleneck (21% of passers are novel). **Lever: seed the proposer with the
data's real correlation structure** so it extrapolates from genuine signals.

## Goal + metrics
Raise the rate of genuine novel discoveries. **Metrics:** Gate-1 pass rate ↑ (from 25%);
novel-emit yield ↑ (from 5%); and (once Phase 3a) human-confirmed discovery rate; CI
Discovery sub-score trend. Measure each phase against the pre-phase funnel before
committing to the next (measure-before-build).

## Phases

## Status (2026-07-15, second pass)
- **Phase 0** ✅ — gate1_fail 74% confirmed.
- **Phase 1a** ✅ — `correlation_seeds` (data-driven seeding) + `task_system_for` injection.
- **Phase 1b/1c** ✅ — `explored_themes` injection (novelty-steering + coverage awareness).
- **Phase 3a** ✅ — `discovery_review` (rank novel claims for human review).
- **Phase 3b** ✅ — `confirmed_discoveries.jsonl` + `confirmation_rate` field in the CI.
- **Phase 2a** DEFERRED — multi-source Gate-2 (ADS/CrossRef). Phase 0 showed novelty
  is NOT the binding constraint (gate2_known 14%; 21% of Gate-1 passers already novel),
  so improving the novelty gate is the wrong lever until the Phase-1 measurement shows
  novelty became binding. Revisit only if the after-funnel's gate2_known rises.
- **Phase 2b** DEFERRED — embedding-based novelty pre-filter. Trims Gate-2 *cost*, but
  Gate-2 cost isn't the bottleneck either (the 74% that die at Gate-1 are cheap sandboxed
  evals). Low ROI until Gate-2 call volume is the binding cost.
- **Phase 4a** DEFERRED — SDSS×WISE cross-match. The plan's own "What NOT to do" says
  more data before the proposer is fixed = efficient textbook rediscovery. Build only
  AFTER the Phase-1 measurement proves 1a/1b/1c moved Gate-1 pass rate, so the new
  cross-modal space can actually be exploited. (4b stays deferred: `galSpecLine` is not
  accessible via public SDSS CAS — needs MPA-JHU direct download or `emissionLinesPort`.)

**Phase-1 measurement (2026-07-15):** before-funnel baseline (pre-1a, N=745) reproduces
Phase 0 exactly — gate1_fail 74.8%, **gate1-pass 25.2%**, novel-emit 5.4%, gate2_known
14.1%. A controlled `mine_rotation` burst (all 4 productive niches × 15 steps, new code,
supervisor paused to avoid LLM-rate contamination) generated a clean N=60 after-sample
(ts ≥ burst-start 19:24; the 13 gaia_variables verdicts at 19:00–19:12 were excluded as
possibly-old-code). Result (2026-07-15):

| metric | BEFORE (N=745) | AFTER (N=60) | read |
|---|---|---|---|
| **gate1-pass** | **25.2%** | **21.7%** (95% CI 13.1–33.6%) | **NO change** — CI spans the baseline |
| gate1_fail | 74.8% | 78.3% | binding constraint **unchanged** |
| gate2_known | 14.1% | 10.0% | improved (novelty-steering working) |
| novel_emit | 5.4% | 11.7% | **doubled** |
| novel / gate1-pass | 21% | 54% | 2.5× — passers far more likely novel |

**Verdict: Phase 1 did NOT meet its primary goal.** The #1 bottleneck (gate1_fail,
proposer generating insignificant relations) is unchanged — correlation seeds did not
raise gate1-pass above noise. **But 1b/1c (novelty-steering) clearly worked on the
secondary axis:** among claims that *do* pass significance, ~2.5× more are now genuinely
novel and fewer are textbook. Net: ~2× more novel discoveries per unit candidate effort,
but the significant-candidate pool did not grow.

Per-dataset (N=15 each — too small to separate, directional only): galaxy_extended
40%, qso 27%, gaia_variables 13%, wise_midir 7%. The galaxy-vs-qso split (helps where
data has exploitable structure; flat where the proposer already did OK) is a *hint*, not
a conclusion.

**Implications:** (1) Phase 2/4a deferral is vindicated — the proposer isn't fixed, so
Phase 4a is still premature and Phase 2 (novelty) is now even less needed since novelty-
steering already improved that axis. (2) The real next lever is a *different* attack on
gate1_fail: investigate whether correlation seeds actually reach/influence the proposer
(they may be appended as prose and ignored), or seed it with code templates derived from
the real correlations rather than "extrapolate" hints. N=60 is directional — the
supervisor's ongoing runs will sharpen the gate1-pass number.

### Seed-fix investigation + fix (2026-07-15, commit 64faa17)
Investigated the two options above. **Option 1 (do the seeds reach the proposer?)
= YES** — `task_system_for` appends `correlation_seeds`/`explored_themes` into the
prompt and `LLMProposer` uses it verbatim as the system prompt; nothing was dropped.
**The real root cause:** `correlation_seeds` returned each dataset's *strongest* pairwise
correlations, which by definition are the textbook/dominant ones (band↔redshift for QSOs,
mag↔size for galaxies, the HR diagram for stars) — exactly what the prompt tells the
proposer to avoid. Plus a bug: dash-less pre-computed colours like WISE `w1w2` were
misclassified as science columns, leaking trivial colour↔colour pairs (WISE's 6.7%
gate1-pass, worst-in-class).

Fix (TDD, `test_data_lake` 14/14): (1) `_is_science` now excludes concatenated-band
tokens (`w1w2`, `ugriz`); (2) `correlation_seeds` now **leads with RESIDUAL seeds** —
for each science column it removes the dominant predictor and surfaces mid-strength
partial signals (`resid(s~p)` vs `q`) that are genuinely non-obvious. Real-data check:
galaxy_extended now seeds `resid(petror90_r~g)↔petror50_r` (0.64) and
`↔concentration_r` (−0.53); WISE correctly returns `[]` (no science columns) instead of
garbage.

**Measurement now three-way** (`measure_phase1_funnel.py`, run by the `a685ee3d` /loop):
baseline (pre-1a) → ORIG (1a/1b/1c, old seeds) → FIX (1a/1b/1c + seed fix, ts ≥
20:14:48). The FIX partition starts empty and fills as the supervisor runs; the loop
stops + posts a conclusion when FIX N≥150 or the CI rules out a >~7pp gain.

**Next steps:** land the Phase-1 before/after result above; then re-evaluate Phase 4a
(only if the proposer is now fixed) — Phase 2 stays deferred.

### Phase 0 — re-confirm bottleneck ✅ DONE (2026-07-15)
Read `claim_verdicts.jsonl` (NOT the discovery stores — `failure_class` expects the
verdict-log shape: top-level `gate1`/`gate2`/`both_pass`). Result above: gate1_fail 74%.

### Phase 1 — candidate-generation quality (the binding constraint)
- **1a. Data-driven seeding** *(implement now)* — `data_lake.correlation_seeds(name)`:
  load the cached dataframe, subsample ~2000 rows, derive color indices for band-like
  columns (`u,g,r,i,z,w1..w4,phot_*_mean_mag`), compute the Spearman matrix over
  (numeric columns ∪ colors), return the top-K off-diagonal pairs with 0.3 ≤ |r| ≤ 0.95
  (significant but not near-deterministic). `task_system_for` appends them as
  "strong relations already present — extrapolate toward non-obvious higher-order forms
  (residuals, interactions, conditionals), do not restate." Defensive: returns [] on any
  error/missing cache. **Targets gate1_fail.**
- **1b. Novelty-steering (active avoidance)** — feed the dataset's recent
  `gate2_known` relation families to the proposer as "known — go adjacent." Targets
  gate2_known (14%).
- **1c. Coverage map (IdeaGraph-lite, dropped Sub-project B)** — track explored
  (dataset × relation-family) cells; bias the proposer toward under-explored space.

### Phase 2 — novelty-verification quality
- **2a.** Multi-source Gate-2 (ADS + arXiv + Semantic Scholar) + ensemble judge.
- **2b.** Cheap embedding-based "likely-known?" pre-filter before expensive Gate-2.

### Phase 3 — discovery confirmation (converts best-effort → genuine)
- **3a.** `discovery_review` tool: rank novel claims by (|effect|, novelty-reasoning
  quality, dataset diversity) for human confirmation.
- **3b.** Confirmed-discoveries store; its rate replaces the both-gate proxy in the CI
  Discovery sub-score (a real outcome metric).

### Phase 4 — cross-modal data (the science lever; after Phase 1)
- **4a.** Cross-matched SDSS×WISE positions → optical–IR relations (new space).
- **4b.** SDSS emission-line spectroscopy → ionization/AGN/SFR relations.

## Sequencing
**0 → 1a → 3a → 1b/1c → 2 → 4.** 1a first (cheapest, attacks the #1 failure); 3a early
(a human-confirmed outcome metric beats another process proxy).

## What NOT to do
- More surveys before Phase 1 (Phase 4 first = more efficient textbook rediscovery).
- Selection optimization (Sub-project A UCB) — not the bottleneck.
- Relaxing any gate — that reintroduces fiction.

## Restart instructions
1. `cd /Users/gjw255/astrodata/SWARM/ASTRA-dev-main`; `git log --oneline -3` to see state.
2. Re-confirm Phase 0: `PYTHONPATH=astra_core/scientific_discovery python -c "from evolved_analysis.predictions import load_verdicts; from evolved_analysis.improvement_loop import failure_class; import collections; r=[x for x in load_verdicts() if (x.get('label') or '')!='seed']; print(collections.Counter(failure_class(x) for x in r).most_common(3))"`.
3. Pick up at the first phase not marked ✅ DONE. Phase 1a lives in `data_lake.py`
   (`correlation_seeds` + `task_system_for` injection) + a test in `test_data_lake.py`.
4. Measure each phase against the funnel above before building the next.
