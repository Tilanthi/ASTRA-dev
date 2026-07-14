# Sub-project C — Astronomy Data Lake + Literature-Mined Action Space (Design Spec)

- **Date:** 2026-07-14
- **Status:** Implemented + validated (live fetches from SDSS CAS and Gaia DR3; full test suite green)
- **Scope:** Feature 1 (Biomni-style literature-mined action space + curated data lake), applied to the **Phase-2 claim search** as an opt-in data source.

## 1. Motivation

The 2026-07-14 failure-mode diagnostic found the autonomous search's binding
constraint is **data narrowness, not selection**: 148/157 Gate-2 "known"
rejections were foundational/textbook, 129/157 were colour–redshift — the only
strong relationships in the single sample (SDSS u,g,r,i,z + z_spec on ~4000
galaxies) ARE the textbook ones. Broadening the real data the search can mine is
the lever that targets that bottleneck. (Sub-project A, selection/UCB, was
dropped because it would optimise the wrong dial.)

## 2. Hard constraint (unchanged)

The discovery-store chokepoint (`discovery_store.append_verified`) is inviolable.
Sub-project C only changes **which real data** Gate-1 evaluates claims against;
survivors still flow through the unchanged `_emit()` → chokepoint path. The
sandbox network-denial profile (`astra_worker.sb`: `deny network*`) is
**unchanged** — the sandbox never fetches.

## 3. Design (pre-fetch-and-cache, opt-in)

- **Fetchers run OUTSIDE the sandbox** (network available) and write a cache CSV
  + JSON manifest to `~/.astra_persistent/evolved_programs/data_lake/`.
- **The sandboxed `claim_eval_worker` reads the cache FILE only** — exactly as it
  already reads `photoz_sdss_cache.csv`. `data_lake.load_split(name)` is a
  file-read; it never fetches.
- **Opt-in via `--data-source NAME`** on `run_claim_search`. Default `legacy`
  uses `real_data.py` (sdss_photoz) → **zero behaviour change** unless C is
  explicitly enabled. The proposer prompt is auto-templated with the dataset's
  columns/description (`data_lake.task_system_for`).

## 4. Components

- **`data_lake.py`** — `Dataset`/registry framework; `fetch_and_cache` (outside
  sandbox), `load_split` (sandbox file-read), `task_system_for` (prompt builder).
  Registered real datasets (all validated live): `sdss_stars`, `sdss_qso`,
  `sdss_galaxy_extended` (adds Petrosian concentration/morphology), `gaia_nearby`
  (astrometry — HR diagram, kinematics; genuinely outside the SDSS photometric
  space). Extensible: add a `Dataset` + fetcher to grow the lake.
- **`action_space_miner.py`** — Biomni `PaperTaskExtractor` analogue: reads
  recent astro-ph abstracts, extracts survey/analysis mentions (rule-based +
  optional LLM pass), suggests datasets to add. On-demand growth tool, not in
  the hot loop.
- **Integration** — `claim_eval_worker` accepts an optional `source` arg;
  `run_claim_search` adds `--data-source`/`--list-sources`, pre-fetches outside
  the sandbox, threads `source` through `gate1_run`/`two_gate_eval`, and
  templates the proposer prompt.

## 5. Testing & validation

- `test_data_lake.py` 7/7, `test_action_space_miner.py` 5/5 (no network).
- Regressions green: `test_discovery_chokepoint.py` 11/11, `test_claim_gates.py`
  17/17, `test_verdict_logging.py` 4/4 — default behaviour unchanged.
- **Live-validated:** `sdss_stars` (4000 real rows, SDSS CAS) and `gaia_nearby`
  (4000 real rows, Gaia DR3) fetched, cached, and manifested with real
  provenance. End-to-end claim search on `sdss_stars` ran and correctly found no
  spurious significance for the (galaxy) seed on star data.

## 6. How to use

```bash
# List available data sources
PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.run_claim_search --list-sources
# Populate a cache (real fetch; run outside the sandbox)
PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.data_lake fetch sdss_stars
# Mine a dataset for novel claims (opt-in; default is still legacy sdss_photoz)
PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.run_claim_search --data-source gaia_nearby --steps 5
# Let the literature suggest which datasets to add next
PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.action_space_miner
```

## 7. Out of scope / future

- More datasets (TESS/Kepler light curves, ZTF time-domain, SIMBAD/VizieR
  cross-matches) — the registry is extensible; each is a `Dataset` + fetcher.
- Wiring the supervisor to periodically rotate `--data-source` across the lake
  automatically (currently opt-in per run).
- Re-running the failure-mode analysis against `claim_verdicts.jsonl` once lake
  datasets have been mined, to confirm "known/textbook" rejections drop — the
  measure-before-committing check recommended in the diagnostic.
