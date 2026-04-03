# ASTRA Autonomous Research System

## Overview

ASTRA has been transformed from a task-based analysis tool into a **fully autonomous, self-improving scientific discovery agent**. It operates in continuous research cycles: generating hypotheses, testing them rigorously, learning from results, and feeding discoveries back into itself.

## Architecture

```
/shared/ASTRA/
├── config/
│   └── autonomous_system_prompt.md    # Full system prompt (reference)
├── knowledge/
│   ├── STATE.md                       # Current understanding (updated every run)
│   ├── INSIGHTS.md                    # Accumulated lessons learned
│   └── FINDINGS.md                    # Confirmed significant findings
├── hypotheses/
│   ├── QUEUE.md                       # Prioritized hypothesis queue
│   └── GRAVEYARD.md                   # Refuted hypotheses + lessons
├── pipeline/
│   └── (analysis scripts generated here)
├── logs/
│   └── 2026-04.md                     # Monthly run log
├── data/
│   └── discovery_run/                 # All data, scripts, plots
├── AUTONOMOUS_README.md               # This file
└── SHARED.md                          # Shared drive documentation
```

## How It Works

### Research Cycle (Every Run)
1. **Orient** — Read knowledge base to understand current state
2. **Select** — Pick highest-priority hypothesis (or generate new one)
3. **Investigate** — Execute rigorous analysis with available data
4. **Evaluate** — Score result, extract lessons
5. **Update** — Feed everything back into knowledge base

### Hypothesis Lifecycle
```
[Generate] → [Queue] → [Select] → [Investigate] → [Evaluate]
                                                    ↓
                                    [Confirm] or [Refute → Graveyard]
                                                    ↓
                                            [Update Knowledge Base]
                                                    ↓
                                            [Generate New Hypotheses]
```

### Self-Improvement
- Every 5 runs: meta-analysis of hypothesis survival rate
- Identifies productive vs unproductive hypothesis types
- Adjusts approach based on accumulated insights

## Current State (as of 2026-04-03)

### Completed Cycles
| Run | Hypothesis | Result | Key Lesson |
|-----|-----------|--------|------------|
| 1 (Discovery) | Broad survey | Found acceleration coincidence | Need targeted follow-up |
| 2 (Follow-Up) | H001: Coincidence is special | REFUTED | Cosmologically expected |
| 3 (Green Valley) | H003: GV at RAR transition | REFUTED | Mass-size relation in disguise |
| 4 (Final Synthesis) | H004: Dimensional ratio is fundamental | REFUTED | Epoch-specific coincidence |

### Queue (6 Pending Hypotheses)
| ID | Priority | Hypothesis |
|----|----------|-----------|
| H009 | 2 | Cluster L-M slope excess correlates with environment |
| H010 | 3 | BH M-σ non-linearity is real |
| H011 | 3 | CMB low-ℓ deficit has constant suppression factor |
| H012 | 2 | SN Ia H₀ depends on redshift range |
| H013 | 4 | Causal discovery on H₀ compilation |
| H014 | 2 | RAR residuals correlate with galaxy properties |

### Key Metrics
- Hypotheses tested: 8
- Confirmed: 0 | Refuted: 6 | Inconclusive: 2
- Survival rate: 0% (expected for aggressive hypothesis testing)
- Insights accumulated: 12
- Data quality notes: 5

## Running the System

The orchestrator (`astra-orchestrator`) is configured with the autonomous system prompt. Each delegation triggers a full research cycle:

```
Parent agent → Delegate to astra-orchestrator → Orient → Select → Investigate → Evaluate → Update → Return
```

For continuous operation, the parent agent can schedule periodic runs or trigger on-demand.

## Data Sources

| Dataset | Size | Description |
|---------|------|-------------|
| SPARC RAR | 3,384 pts | Galaxy rotation curves |
| MCXC Clusters | 1,744 | Galaxy cluster properties |
| BH M-σ | 230 | Supermassive black holes |
| SDSS | 82,891 | Galaxy photometric/spectroscopic |
| Pantheon+ | 1,544 | Type Ia supernovae |
| H₀ Compilation | 53 | Hubble constant measurements |
| Planck CMB | 250 bins | CMB power spectrum |
| BAO | 8 | Baryon acoustic oscillations |

**Total**: ~89,000+ data points across 15 orders of magnitude in astrophysical scale.

## Design Philosophy

1. **Negative results are as valuable as positive ones** — knowing what ISN'T there is good science
2. **Three rounds of scrutiny minimum** — raw → subsample → confound disentangling
3. **The "interesting" signal usually has a boring explanation** — mass, selection effects, cosmological expectations
4. **Never stop asking "what's next?"** — every finding generates new questions
5. **Follow the data, not the narrative** — beautiful theories don't override ugly data

---

*System initialized: 2026-04-03T04:30:00Z*
*Agent: ASTRA v4.7*
*Platform: Taurus multi-agent orchestration*
