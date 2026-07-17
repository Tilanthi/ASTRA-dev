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
- **Version**: 14.14 (2026-07-17). Recent work: full `astra_core` audit + physics rebuild — revived `astro_physics` (import failures 43→0, `AstroSwarmSystem` live) via 11 new verified PhD-level physics modules (RADEX CO non-LTE radiative transfer, SMC inference, Salpeter/Kroupa IMF + Kennicutt-Schmidt, Högbom CLEAN, populated astronomy knowledge-graph, agents framework, …) + guard widening across the symbolic/swarm chains; removed the unused ARC-AGI puzzle subsystem (`arc_agi/`, `arc_reasoning/`); confirmed `swarm/` (MORK stigmergic-reasoning engine) is a core capability — **not** superseded by `intelligence/` (which is the complementary evolutionary/LEAP-core optimizer) — and is imported by `AstroSwarmSystem`. Importable modules 476→555; baseline 43→28; 74 tests pass. **Full version history + status detail → `CLAUDE_ASTRA_SYSTEM_STATUS.md`.**
- **GitHub**: https://github.com/Tilanthi/ASTRA-dev


### Current Status
All `System Status — v14.x` sections (v14.0→v14.14: fiction-free two-gate EVALUATE → data lake → niche rotation → dedup → non-optical datasets → self-improvement → residual-seed fix → cross-modal `sdss_wise_xmatch` → anti-circularity gate → repo-health audit → codebase audit + astro_physics physics rebuild) now live in **`CLAUDE_ASTRA_SYSTEM_STATUS.md`** to keep this entry file lean.

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
