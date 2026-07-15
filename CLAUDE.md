# ASTRA Project Guide (Streamlined for Context)

**Full detail lives in the dependent files** (this is the lean entry point):
- `CLAUDE_ASTRA_FULL.md` — complete system documentation
- `CLAUDE_ASTRA_ARCHITECTURE.md` — architecture, modules, and pipeline-validation gates
- `CLAUDE_ASTRA_TESTING.md` — testing procedures and benchmarks
- `CLAUDE_ASTRA_QUICKSTART.md` — quick start methods and examples
- `CLAUDE_ASTRA_SYSTEM_STATUS.md` — latest status + the v5–v7 historical fix record

---

## Critical Rules
- ❌ **NO FICTIONAL/SYNTHETIC DISCOVERIES** — only genuine, verified astronomical discoveries
- ❌ **NO MOCK DATA OR MOCKASTRA** — never use MockASTRA, test data, or mock discoveries under any circumstances
- ✅ **ALWAYS use the real ASTRA system** — only genuine EnhancedUnifiedSTANSystem with real astronomical queries
- ✅ **ALWAYS verify discovery authenticity** before presenting it to the user
- 🚨 **SYSTEM FAILURE IF MOCK DATA DETECTED** — a mock discovery means a critical bug requiring an immediate fix

## Project Detection
- **ASTRA**: `/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/`
  - **GitHub Target**: https://github.com/Tilanthi/ASTRA-dev (ONLY this repository)
  - **Purpose**: Autonomous Scientific Discovery in Astrophysics

---

## Quick Start
The only supported always-on path is the **`com.astra.discovery` macOS LaunchAgent**: it runs the fiction-free supervisor, starts at login, auto-restarts on crash, and yields to user activity. (`start_continuous_discovery.sh` — "Method 2" — is **DEPRECATED**: it launches the retired fiction emitter via the legacy watchdog and churns ~400 MB/day producing nothing.)

```bash
launchctl list com.astra.discovery                       # status
tail -f .astra_service.log                                # logs
launchctl kickstart -k gui/$(id -u)/com.astra.discovery   # restart
```

Programmatic: `from astra_core import create_stan_system; system = create_stan_system()`.

More methods: `CLAUDE_ASTRA_QUICKSTART.md`.

---

## Essential Information

### Project Overview
- **ASTRA**: Autonomous Scientific Discovery in Astrophysics
- **Version**: 14.10 (2026-07-15) — first **cross-matched** dataset: SDSS optical × AllWISE mid-IR per object (`sdss_wise_xmatch`), opening the optical–IR cross-modal axis (justified by the v14.9 residual-seeding fix that raised gate1-pass 25%→34%); on top of v14.9 (data-driven proposer seeding + explored-themes + discovery_review + confirmation-rate CI), v14.8 (Brier calibration + Discovery CI), v14.7 (self-improvement layer), v14.6 (non-optical datasets), v14.5 (near-dup reviewer), v14.4 (effect+p-value dedup), v14.3 (always-on niche rotation), v14.2 (rotation miner + niche hints), v14.1 (data lake + cleanup), v14.0 (fiction-free two-gate EVALUATE).
- **GitHub**: https://github.com/Tilanthi/ASTRA-dev

### System Status — v14.3 (2026-07-15): higher-novelty niches in the always-on path
The supervisor's `ASTRA_EVOLUTION_MODULE` is now `evolved_analysis.mine_rotation` with `ASTRA_MINE_ROUND_ROBIN=1` + `ASTRA_MINE_STEPS=12` (in `~/.astra_persistent/llm_env`), so each evolution episode mines **one productive data-lake niche, round-robin** (galaxy morphology → QSOs → …) instead of the textbook-dominated legacy sdss_photoz. Each episode stays short (one niche × 12 steps) and user-yielding. Confirmed end-to-end (a confirmation run emitted a QSO novel claim immediately).

### System Status — v14.10 (2026-07-15): first cross-matched (cross-modal) dataset
Phase 4a landed: `sdss_wise_xmatch` (in `evolved_analysis/data_lake.py`) — SDSS optical galaxies **cross-matched by position** to AllWISE mid-IR for the *same* objects (region-bounded SDSS-CAS query + IRSA AllWISE pull + astropy cone-match at 2″ via `_cone_match_merge`), giving per-galaxy u,g,r,i,z + Petrosian radii/concentration + z_spec **and** WISE W1–W4 + optical–IR colours (r-w1, r-w2, w1w2). TDD (`test_data_lake`, 16 green) + live-fetched/validated (116 matched galaxies). This is the first **cross-modal** axis — dust / stellar-mass / AGN colour space — built now because the v14.9 residual-seeding fix (commit `64faa17`) raised gate1-pass 25%→34% (CI excludes baseline), so the proposer can finally exploit richer structure. The productive rotation now spans **5 niches**; `productive_datasets()` picks the new one up automatically. Gap remaining: radio, X-ray, spectroscopy.

### Dedup (v14.4): effect + p-value fingerprint
The store dedups on a **(held-out effect, p-value)** fingerprint (`discovery_store.dedup_key`), not just `program_hash`. Regenerated duplicates of the same finding vary in wording and program hash but share an identical effect + p-value (the `run_claim` computation is identical), so this collapses them reliably — fixes the triplicate near-duplicates the rotation was emitting. Applied at both the chokepoint (`append_verified`/`dedup_verified`) and emit-time (`_emit`), with a `program_hash` fallback for records lacking effect/p-value.

**Near-duplicate review (v14.5):** `discovery_store.near_duplicate_groups` + `evolved_analysis.dup_review` surface distinct findings that share |effect| with p-values within an order of magnitude (they *might* be the same phenomenon) for **human review — not auto-merged**. Run: `PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.dup_review`.

**Breadth (v14.6): first non-optical datasets.** Registered `wise_midir` (AllWISE W1–W4 — a new **mid-IR** wavelength) and `gaia_variables` (Gaia DR3 variable stars — a **time-domain** modality), both live-fetched and validated (16,220 WISE rows; 4,000 variables). The productive rotation now cycles **5 niches: galaxy morphology, QSOs, mid-IR, variables, and (v14.10) the SDSS×WISE cross-match** — breaking out of optical galaxy photometry. Gap remaining: radio, X-ray, spectroscopy (cross-matches begun in v14.10; the registry is hand-curated; `action_space_miner` exists to grow it from the literature).

**Self-improvement layer (v14.7): predict/surprise, measured RSI loop, capability index.** Three additive stdlib-only instruments (no chokepoint/gate changes), inspired by *Unleashing the Beast* (Perni/Dey, 2026):
- **#1 predict-before-act + surprise ledger** (`predictions.py`): `mine_rotation` writes a statistical-baseline prediction before each episode and scores `surprise` after — turning the verdict log into a *calibration* instrument. **Upgraded (v14.8) to Brier-scored probabilistic calibration**: a Beta-posterior forecast P(≥1 novel emit) per episode, scored with the Brier score + a reliability curve — proper calibration (do predicted probabilities match observed frequencies?), not just stationarity. `~/.astra_persistent/evolved_programs/{predictions,surprise_ledger}.jsonl`.
- **#2 gated, measured self-improvement** (`improvement_loop.py`): mines verdicts into recurring failure classes → proposes gated fixes (propose only) → **measures whether an applied fix reduced its failure class**. Live result: split-discipline fix 100.0, Gate-2 retrieval fix 67.6 (rollup RSI effectiveness 83.8, "improving not solved"). `rsi_proposals.jsonl` / `rsi_applied.jsonl` / `rsi_effectiveness.txt`.
- **#3 capability index** (`capability_index.py`): dated CI (0–100) from existing artifacts; **ingests sub-100 RSI effectiveness that can LOWER it**. **Upgraded (v14.8)**: Calibration now Brier-based (real forecast calibration); added a **Discovery outcome sub-score** (novel-yield vs a 15% aspiration + trend) so the CI tracks discovery quality, not just pipeline health. Live CI **66.5** (calibration 35.8 from 2 episodes — noisy, will stabilize; discovery 66.5; learning 59.8; execution 93.4; breadth 100). Trend not level; 100 = formula saturation. `ci_history.jsonl`.
- Run: `python -m evolved_analysis.predictions|capability_index|improvement_loop [mine|measure]`.

### System Status — v14.2 (2026-07-14): scaling novel output
Pilots showed novelty is rare, roughly linear in candidate-evals, and object-type-dependent (stars → 0 novel; galaxies/QSOs → some). Two levers added:
- **Scale** — `evolved_analysis/mine_rotation.py` runs the Phase-2 search across datasets in one command: `PYTHONPATH=astra_core/scientific_discovery python -m evolved_analysis.mine_rotation --steps N`.
- **Focus** — datasets carry `textbook_risk` (`sdss_stars` + `gaia_nearby` = "high" — ~100% known, HR-diagram-dominated) and a `niche_hint` appended to the proposer prompt (galaxy concentration/morphology, QSO colour×redshift interactions). `productive_datasets()` returns the mineable ones; the rotation miner skips high-risk by default (`--include-high-risk` to opt in). `--list-sources` shows the risk flag.

---

### System Status — v14.1 (2026-07-14)
- **Data lake (Sub-project C).** Phase-2 claim search can mine real datasets beyond the single SDSS photo-z sample, via opt-in `--data-source NAME` (default `legacy` = unchanged). Modules `evolved_analysis/data_lake.py` (registry + fetch/cache; `sdss_stars`, `sdss_qso`, `sdss_galaxy_extended`, `gaia_nearby`) and `action_space_miner.py` (Biomni-style arXiv astro-ph miner). **Sandbox unchanged**: fetchers run outside the sandbox and write cache CSVs; the sandboxed worker reads cache files only (no-network profile intact). Live-validated vs SDSS CAS + Gaia DR3. Spec: `docs/superpowers/specs/2026-07-14-subproject-c-data-lake-design.md`.
- **Proposer split-discipline fix** — `claim_uses_train_split` guard + prompt rule + `--propose-retries` (the 2026-07-14 pilot found the proposer generated `df_eval`-only code the holdout gate rejected).
- **Gate-2 retrieval robustness** — `_http_get` retry/backoff + retry-on-empty; transient "retrieval-failed" is no longer cached.
- **Verdict logging** — `~/.astra_persistent/evolved_programs/claim_verdicts.jsonl` tags each per-candidate verdict with its dataset (the supervisor runs the subprocess with stdout→DEVNULL).
- **2026-07-14 finding:** the binding constraint is a *chain* (data → proposer split-discipline → Gate-2 retrieval), now all fixed on main. Broader data is necessary-but-not-sufficient because real data is textbook-dominated (Gaia → 100% known: HR diagram, reduced proper motion). Sub-project A (UCB selection) was designed but **not** built — selection isn't the bottleneck. Spec kept at `docs/superpowers/specs/2026-07-13-subproject-a-acquisition-multifidelity-design.md` (not recommended).

### System Status — v14.0 (2026-07-11, still current)
**Fiction is structurally impossible.** A single write chokepoint — `astra_core/scientific_discovery/discovery_store.py::append_verified` — rejects any record without a machine `verification` block. The always-on `astra_core/autonomous_discovery_supervisor.py` (launchd `com.astra.discovery`) ingests only machine-verified records and, when idle + an LLM token is present, runs the evolutionary engine. It never falls back to fiction.

**Two-gate EVALUATE (AlphaEvolve core):** Phase 1 = proven narrow-task evolution (photo-z σ_NMAD 0.049→0.021; star/gal/qso 0.33→0.91 on real SDSS). Phase 2 = open-ended (CLAIM, test) search: **Gate 1** real-data significance (sandboxed, no network) + **Gate 2** literature novelty vs arXiv. Only both-gate survivors are stored.

- Generated code sandboxed: AST import allowlist + `resource` rlimits + `sandbox-exec` (no network, temp-writes-only).
- Canonical LLM gateway (`astra_core/intelligence/llm_gateway.py`); STAN stays a symbolic component.
- Honest limitation: Gate-2 novelty is best-effort (not a perfect oracle); Eureka-class novelty is rare.

**Enabling autonomous evolution:** the supervisor runs ingest-only until `~/.astra_persistent/llm_env` (chmod 600) contains `ANTHROPIC_AUTH_TOKEN` (+ base URL) and `ASTRA_EVOLUTION_MODULE` (e.g. `evolved_analysis.run_claim_search`).

Full design: `docs/superpowers/specs/2026-07-11-astra-autonomous-discovery-rearchitecture-design.md`.

### Key Features
4-level discovery classification (Novel Observation → Theoretical Insight → Paradigm Shift → Eureka); 3-D scoring (Novelty + Validation + Impact); swarm intelligence + ontology + causal inference; auto-start, user-yielding operation.

### Pipeline Validation Gates (v6.0)
Paper-output rigor gates (citation resolution, derivation traces, non-trivial validation, explicit tolerances). Impl: `astra_core/pipeline_validation.py`. **Detail moved to `CLAUDE_ASTRA_ARCHITECTURE.md`.**

---

## Common Commands
```bash
launchctl list com.astra.discovery                        # service status
launchctl kickstart -k gui/$(id -u)/com.astra.discovery   # restart service
tail -f .astra_service.log                                 # logs
python3 astra_core/tests/test_discovery_chokepoint.py      # core regression test
python3 astra_core/tests/v4/run_tests.py                   # full test suite
```

## Persistent Memory & Key Files
- `~/.astra_persistent/genuine_discoveries.json`, `evolved_discoveries.json`, `discovery_memory.json` — discovery stores (chokepoint-gated)
- `~/.astra_persistent/llm_env` — LLM token + `ASTRA_EVOLUTION_MODULE` (chmod 600)
- `~/.astra_persistent/evolved_programs/claim_verdicts.jsonl` — per-candidate verdict log
- `~/.astra_persistent/conversation_context/` — conversation checkpoints

```python
from astra_core.memory.persistent import create_integrator
integrator = create_integrator(); integrator.initialize_session()
```

---

## GitHub Repository Targeting
**CRITICAL**: when pushing, **ALWAYS target only `https://github.com/Tilanthi/ASTRA-dev.git`** (ASTRA only — astronomical research, discovery system, astrophysics tools). Verify with `git remote -v` before pushing.

---

**Detail moved out of this file to keep it lean:** full docs → `CLAUDE_ASTRA_FULL.md`; architecture + pipeline gates → `CLAUDE_ASTRA_ARCHITECTURE.md`; testing → `CLAUDE_ASTRA_TESTING.md`; quick start → `CLAUDE_ASTRA_QUICKSTART.md`; status + v5–v7 historical fix record → `CLAUDE_ASTRA_SYSTEM_STATUS.md`.
