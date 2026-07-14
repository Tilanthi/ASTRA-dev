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
- **Version**: 14.1 (2026-07-14) — opt-in **data lake + literature-mined action space** (Sub-project C) plus a verdict-logging / legacy-system cleanup, on top of the v14.0 fiction-free, two-gate EVALUATE re-architecture.
- **GitHub**: https://github.com/Tilanthi/ASTRA-dev

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
