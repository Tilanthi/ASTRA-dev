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
- **Phase 2a** PENDING — multi-source Gate-2 (ADS/CrossRef — new APIs).
- **Phase 2b** PENDING — embedding-based novelty pre-filter.
- **Phase 4a** PENDING — SDSS×WISE cross-match (position matching, complex).
- **Phase 4b** DEFERRED — `galSpecLine` (MPA-JHU emission lines) is NOT accessible via
  the public SDSS CAS query (returned an HTML error page). Needs an alternative path:
  MPA-JHU catalog direct download, or `emissionLinesPort` long-format pivot. The broken
  fetcher was removed.

**Next steps:** measure 1a's effect on gate1-pass rate (funnel script); then Phase 2
(verification quality) or 4a (cross-modal).

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
