# ASTRA — Autonomous Scientific & Technological Research Agent

> An AI-driven framework for autonomous cross-domain scientific discovery,
> hypothesis generation, and validation using real astronomical and socioeconomic data.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)

## Highlights

- **89-endpoint FastAPI backend** for real-time scientific discovery orchestration
- **Autonomous OODA research cycle** — Orient → Select → Investigate → Evaluate → Update
- **9 real data sources** (27,430+ data points): Pantheon+ SNe Ia, NASA Exoplanet Archive, Gaia DR3, SDSS DR18, LIGO gravitational waves, Planck CMB, ZTF transients, TESS, SDSS galaxy clusters
- **40+ validated hypotheses** across 5 scientific domains
- **Self-improving discovery memory** — SQLite-backed with 726+ discoveries and 3,600+ method outcomes
- **Safety architecture** — 5-state controller, arbiter, circuit breakers, phased autonomy, ethics reasoning
- **Live dashboard** with 8 interactive tabs (glassmorphism UI, 95/100 design critic score)
- **RASTI paper** in MNRAS format (22 pages, 6 publication-quality figures)
- **Causal inference** — PC/FCI algorithms, do-calculus interventions, confounder detection
- **Bayesian framework** — BIC model comparison, Bayes factors, Laplace posteriors
- **Full reproducibility** — every discovery can be independently re-verified from source data

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        ASTRA Engine                             │
│                                                                 │
│   ┌─────────┐    ┌──────────┐    ┌─────────────┐              │
│   │ ORIENT  │───▶│  SELECT  │───▶│ INVESTIGATE │              │
│   │ Scan    │    │ Prioritize│   │ Fetch Data  │              │
│   │ State   │    │ Hypothesis│   │ Run Tests   │              │
│   └─────────┘    └──────────┘    └──────┬──────┘              │
│        ▲                                │                      │
│        │         ┌──────────┐    ┌──────▼──────┐              │
│        └─────────│  UPDATE  │◀───│  EVALUATE   │              │
│                  │ Confidence│   │ Significance │              │
│                  │ Knowledge │   │ Effect Size  │              │
│                  └──────────┘    └─────────────┘              │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │  Safety Layer: Controller │ Arbiter │ Circuit Breakers  │  │
│   └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
    ┌────▼────┐         ┌────▼────┐         ┌────▼────┐
    │ 9 Data  │         │ SQLite  │         │  Live   │
    │ Sources │         │ Memory  │         │Dashboard│
    └─────────┘         └─────────┘         └─────────┘
```

---

## Repository Structure

```
ASTRA/
├── README.md                    ← You are here
├── CLAUDE.md                    ← AI assistant guidance
├── .gitignore
│
├── astra_live_backend/          ← Active system (89 endpoints, 33 modules)
│   ├── server.py                   FastAPI application & route definitions
│   ├── engine.py                   OODA discovery cycle orchestrator
│   ├── hypotheses.py               Hypothesis state machine & phase gates
│   ├── statistics.py               Statistical tests, FDR, effect sizes
│   ├── cosmology.py                ΛCDM fitting, H₀ estimation, Laplace
│   ├── data_registry.py            Registry for 9 data sources
│   ├── data_fetcher.py             Fetch & cache real scientific data
│   ├── bayesian.py                 BIC, Bayes factors, model comparison
│   ├── causal.py                   PC/FCI causal algorithms, do-calculus
│   ├── literature.py               TF-IDF similarity, arXiv integration
│   ├── paper_generator.py          Auto-draft LaTeX from hypotheses
│   ├── discovery_memory.py         SQLite memory & method outcomes
│   ├── hypothesis_generator.py     Auto-generate hypotheses from memory
│   ├── adaptive_strategist.py      Method selection & exploration balance
│   ├── degradation.py              Long-run health monitoring
│   ├── exporter.py                 JSON/CSV/LaTeX/report export
│   ├── provenance.py               Discovery lineage tracking
│   ├── generate_dashboard.py       Dashboard HTML + snapshot generator
│   ├── safety/                     Safety subsystem
│   │   ├── controller.py              5-state safety controller
│   │   ├── arbiter.py                 Verdicts & override system
│   │   ├── supervisor.py             Shift-based human oversight
│   │   ├── ceremony.py               State transition ceremonies
│   │   ├── circuit_breakers.py        Automatic fault isolation
│   │   ├── ethics.py                  Ethics reasoning engine
│   │   ├── phased_autonomy.py         Graduated autonomy levels
│   │   ├── orp.py                     Operational Readiness Protocol
│   │   ├── safety_case.py             Hazard/claim/risk registry
│   │   ├── health.py                  System health checks
│   │   └── audit.py                   Audit trail logging
│   ├── sprints/                    Domain-specific research sprints
│   │   ├── combined_sprint.py         Multi-domain orchestrator
│   │   ├── crossdomain_sprint.py      Cross-domain correlation analysis
│   │   └── econ_sprint.py             Economics-focused sprint
│   ├── state_space/                State-space analysis (PCA, attractors)
│   └── test_*.py                   Test suites (58+ tests)
│
├── paper/                       ← RASTI paper (MNRAS format)
│   ├── astra-rasti-v2.tex          Main manuscript (V2.2, ~1,340 lines)
│   ├── supplement.tex              Supplementary material (~420 lines)
│   ├── references-v2.bib           Bibliography (37 entries)
│   ├── mnras.cls                   MNRAS document class
│   ├── mnras.bst                   MNRAS bibliography style
│   ├── generate_supplement.py      Auto-generate supplement from API
│   ├── figures/                    Publication figures
│   │   ├── generate_figures.py        Figure generation script
│   │   ├── fig1-scaling-relations.*   Kepler's Third Law + HR diagram
│   │   ├── fig2-multiwavelength.*     Multi-source data integration
│   │   ├── fig3-pattern-recognition.* Galaxy bimodality + clustering
│   │   ├── fig4-causal-inference.*    Causal graph + confounders
│   │   ├── fig5-bayesian-model.*      Model comparison + posteriors
│   │   └── fig6-discovery-mode.*      Discovery cycle performance
│   └── *.pdf                       Compiled PDFs (not tracked)
│
├── stan_core/                   ← Legacy cognitive framework (~614 modules)
│   ├── capabilities/               Analysis capabilities
│   ├── reasoning/                   Reasoning engines
│   ├── memory/                      Persistent memory system
│   └── ...                          (retained for backward compatibility)
│
├── self_evolution/              ← Self-improvement & mutation engine
├── pipeline/                    ← Per-hypothesis analysis scripts
├── config/                      ← System prompts & configuration
├── knowledge/                   ← Accumulated findings & insights
├── hypotheses/                  ← Hypothesis queue, results, graveyard
├── logs/                        ← Run logs & scheduler logs
└── reproduce.py                 ← Reproducibility verification tool
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- System packages: `git`, `curl`

### Installation

```bash
git clone https://github.com/web3guru888/ASTRA.git
cd ASTRA

pip install fastapi uvicorn scipy numpy pandas requests beautifulsoup4 \
            scikit-learn aiofiles
```

### Running the Server

```bash
python3 -m astra_live_backend.server
# → Server running at http://localhost:8787/
```

### Verify It Works

```bash
# System status
curl http://localhost:8787/api/status | python3 -m json.tool

# List all hypotheses
curl http://localhost:8787/api/hypotheses | python3 -m json.tool

# Run one discovery cycle
curl -X POST http://localhost:8787/api/engine/cycle | python3 -m json.tool

# Check discovery memory
curl http://localhost:8787/api/discovery-memory | python3 -m json.tool
```

---

## Key API Endpoints

### Engine Control

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/engine/cycle` | Execute one OODA discovery cycle |
| `POST` | `/api/engine/start` | Start continuous discovery |
| `POST` | `/api/engine/stop` | Stop the engine |
| `POST` | `/api/engine/pause` | Pause the engine |
| `POST` | `/api/engine/resume` | Resume from pause |
| `POST` | `/api/engine/emergency-stop` | Emergency halt |
| `GET`  | `/api/engine/state-vector` | Current engine state vector |

### Hypotheses

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/hypotheses` | List all hypotheses with confidence scores |
| `GET`  | `/api/hypotheses/{id}` | Get hypothesis details |
| `POST` | `/api/hypotheses` | Create a new hypothesis |
| `POST` | `/api/hypothesis/{id}/approve` | Approve for publication |
| `POST` | `/api/hypothesis/{id}/reject` | Reject hypothesis |

### Safety & Alignment

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/engine/safety-status` | Current safety state |
| `GET`  | `/api/engine/alignment` | Alignment score & metrics |
| `GET`  | `/api/engine/anomalies` | Detected anomalies |
| `GET`  | `/api/engine/arbiter` | Arbiter status |
| `GET`  | `/api/engine/safety-case` | Full safety case (hazards, claims, risk) |
| `GET`  | `/api/engine/orp` | Operational Readiness Protocol status |
| `GET`  | `/api/engine/ceremony` | State transition ceremony status |

### Data & Science

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/data-sources` | List all 9 data sources |
| `GET`  | `/api/data-sources/{id}/fetch` | Fetch data from a source |
| `GET`  | `/api/cross-matches` | Cross-domain variable matches |
| `GET`  | `/api/variables` | All tracked variables (45+) |
| `POST` | `/api/science/causal-discovery` | Run causal inference (PC/FCI) |
| `POST` | `/api/science/model-comparison` | Bayesian model comparison |
| `POST` | `/api/statistics/confounder-analysis` | Confounder detection |

### Discovery Memory & Self-Improvement

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/discovery-memory` | Memory summary statistics |
| `GET`  | `/api/discovery-memory/discoveries` | All stored discoveries |
| `GET`  | `/api/discovery-memory/graph` | Discovery knowledge graph |
| `GET`  | `/api/discovery-memory/improvement` | Self-improvement metrics |
| `GET`  | `/api/strategy` | Current adaptive strategy |
| `POST` | `/api/discovery-memory/generate` | Auto-generate new hypotheses |

### Literature & Papers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/literature/search?q=...` | Search arXiv literature |
| `GET`  | `/api/literature/papers` | Cached paper library |
| `POST` | `/api/literature/search-similar` | TF-IDF similarity search |
| `GET`  | `/api/literature/novelty/{id}` | Novelty score for hypothesis |
| `GET`  | `/api/papers` | Auto-generated paper drafts |

### Export & Provenance

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/export/discoveries.json` | Export all discoveries (JSON) |
| `GET`  | `/api/export/discoveries.csv` | Export all discoveries (CSV) |
| `GET`  | `/api/export/hypothesis/{id}.tex` | Export hypothesis as LaTeX |
| `GET`  | `/api/export/full-report.json` | Complete system report |
| `GET`  | `/api/provenance` | All provenance records |
| `GET`  | `/api/provenance/{id}/lineage` | Full discovery lineage |

---

## Scientific Domains

ASTRA operates across five scientific domains simultaneously, generating and validating hypotheses using real data.

### Astrophysics (15 hypotheses)

Key findings validated with real data:
- **Kepler's Third Law**: log(P) = 1.497·log(a) − 0.474·log(M★), R² = 0.9982 (2,839 exoplanets)
- **Accelerating Universe**: μ = 5.33·log(z) + 24.42, χ²/dof = 0.64 (1,701 SNe Ia)
- **Galaxy Color Bimodality**: u−g peaks at 1.44 and 1.92 (2,000 SDSS galaxies)
- **HR Diagram Structure**: M_G = 3.66×(BP−RP), r = 0.90 (4,984 Gaia stars)
- Gravitational wave event rates, ZTF transient host correlations, CMB peak structure

### Economics (10 hypotheses)

- Okun's Law, Trade-GDP correlation, Gini coefficient dynamics
- PPP convergence, GDP mean-reversion, Reinhart-Rogoff threshold analysis
- Export diversification effects, inflation persistence

### Climate Science (5 hypotheses)

- CO₂–Temperature correlation: R² = 0.936
- Warming acceleration: 67% faster than baseline
- CO₂ growth rate trends, decadal warming patterns

### Epidemiology (5 hypotheses)

- Preston Curve: R² = 0.686 (GDP vs life expectancy)
- Infant mortality determinants, DPT vaccination coverage effects
- Maternal mortality correlates

### Cross-Domain (8 hypotheses)

- GDP–CO₂ nexus, Life expectancy–CO₂ relationship
- Wealth-Health correlation: R² = 0.700
- Urbanization–emissions patterns, renewables paradox

---

## Data Sources

| # | Source | Records | Domain | Variables |
|---|--------|---------|--------|-----------|
| 1 | Pantheon+ SNe Ia | 1,701 | Cosmology | Redshift, distance modulus, uncertainty |
| 2 | NASA Exoplanet Archive | 2,839 | Exoplanets | Period, semi-major axis, mass, radius |
| 3 | Gaia DR3 | 4,984 | Stellar | Parallax, magnitudes, color indices |
| 4 | SDSS DR18 | 2,000+ | Galaxies | u/g/r/i/z photometry, redshift, type |
| 5 | LIGO Gravitational Waves | 280 | GW events | Chirp mass, distance, SNR |
| 6 | Planck CMB | 2,507 | Cosmology | Power spectrum, multipole moments |
| 7 | ZTF Transients | 2,000 | Transients | Light curves, classifications |
| 8 | TESS (via VizieR) | varied | Exoplanets | Transit parameters, stellar properties |
| 9 | SDSS Galaxy Clusters | varied | Clusters | Richness, redshift, luminosity |

**Total**: 27,430+ data points across 45 variables and 29 cross-match pairs.

---

## Discovery Engine

### OODA Cycle

Each discovery cycle follows the OODA loop:

1. **Orient** — Scan the knowledge base, review past discoveries, assess current state
2. **Select** — Prioritize the most promising hypothesis for investigation (adaptive strategy balances exploitation vs. exploration)
3. **Investigate** — Fetch real data from source APIs, run statistical tests (KS, χ², t-test, Pearson, Granger), compute effect sizes
4. **Evaluate** — Assess statistical significance (p < 0.01 with FDR correction), compute Bayesian confidence updates
5. **Update** — Record the discovery, update hypothesis confidence, feed results back into the knowledge base for the next cycle

### Hypothesis Lifecycle

```
Generate → Queue → Select → Investigate → Evaluate
                                            ↓
                            Validate (confidence > 0.8)
                            or Refute → Graveyard (with lessons)
                                            ↓
                                    Record in Discovery Memory
                                            ↓
                                    Generate New Hypotheses
```

### Statistical Methods

- **Tests**: KS, χ², Student's t, Welch's t, Mann-Whitney U, Pearson/Spearman correlation, Granger causality
- **Corrections**: Benjamini-Hochberg FDR, Bonferroni
- **Effect sizes**: Cohen's d, η², Cramér's V, R²
- **Bayesian**: BIC model comparison, Bayes factors, Laplace approximation posteriors
- **Time series**: Autocorrelation, CUSUM change-point detection
- **Causal**: PC algorithm, FCI algorithm, do-calculus interventions, confounder detection

---

## Safety Architecture

ASTRA implements defense-in-depth safety with multiple independent layers:

### 5-State Safety Controller

```
BOOT → NOMINAL → DEGRADED → SAFE_MODE → EMERGENCY_STOP
```

State transitions require formal ceremonies with documented justification and rollback plans.

### Safety Components

| Component | Purpose |
|-----------|---------|
| **Controller** | 5-state FSM governing system behavior |
| **Arbiter** | Reviews engine decisions, issues verdicts, supports human overrides |
| **Circuit Breakers** | Automatic fault isolation (error rate, anomaly, resource limits) |
| **Supervisor** | Shift-based human oversight with action logging |
| **Ceremony** | Formal state transition protocol with audit trail |
| **Ethics Engine** | Evaluates research decisions against ethical guidelines |
| **Phased Autonomy** | Graduated autonomy levels based on demonstrated safety |
| **ORP** | Operational Readiness Protocol — pre-flight checklists |
| **Safety Case** | Structured argument: hazards → claims → evidence → risk |
| **Audit Trail** | Immutable log of all safety-relevant events |

---

## RASTI Paper

**"ASTRA: An Integrated Analysis Framework for Physics-Aware Astrophysical Discovery"**

- **Authors**: Glenn J. White (The Open University) & Robin Dey (VBRL Holdings Inc)
- **Target**: Monthly Notices of the Royal Astronomical Society (MNRAS) / Research Notes
- **Format**: MNRAS LaTeX class, 22 pages, 6 figures, 37 references
- **Location**: `paper/` directory

### Building the Paper

```bash
cd paper

# Generate figures
python3 figures/generate_figures.py

# Compile PDF
pdflatex astra-rasti-v2.tex
bibtex astra-rasti-v2
pdflatex astra-rasti-v2.tex
pdflatex astra-rasti-v2.tex

# Compile supplement
pdflatex supplement.tex
```

### Figures

| Figure | Content |
|--------|---------|
| Fig. 1 | Scaling relations — Kepler's Third Law + HR diagram |
| Fig. 2 | Multi-wavelength data integration across 9 sources |
| Fig. 3 | Pattern recognition — galaxy bimodality + clustering |
| Fig. 4 | Causal inference — causal graph + confounder analysis |
| Fig. 5 | Bayesian model comparison + posterior distributions |
| Fig. 6 | Discovery cycle — performance metrics + convergence |

---

## Reproducibility

Every discovery recorded by ASTRA can be independently reproduced:

```bash
# List all reproducible discoveries
python3 reproduce.py --list

# Reproduce a specific discovery
python3 reproduce.py <discovery_id>

# Reproduce all discoveries (takes a while)
python3 reproduce.py --all

# Use a custom database
python3 reproduce.py --db /path/to/astra_discoveries.db --list
```

The tool re-fetches original data from source APIs and re-runs the statistical test to verify the recorded result matches.

---

## Development

### Running Tests

```bash
# All tests
pytest astra_live_backend/ -v

# Specific test suites
pytest astra_live_backend/test_phase10.py -v    # Long-run stability
pytest astra_live_backend/test_phase11.py -v    # Publication & export
pytest astra_live_backend/test_literature.py -v  # Literature integration
```

### Dashboard

The live dashboard is a single-file HTML application with embedded CSS/JS.

```bash
# Edit the HTML template directly
vim astra_live_backend/generate_dashboard.py  # or the HTML source

# Regenerate with latest data snapshot
python3 astra_live_backend/generate_dashboard.py
# Output: /shared/public/astra-live/index.html
```

**Note**: The generator injects a `__SNAPSHOT__` JSON blob into the HTML. CSS and JS edits to the template persist through regeneration.

### Generating Figures

```bash
python3 paper/figures/generate_figures.py
# Output: paper/figures/fig{1-6}-*.{pdf,png}
```

---

## Self-Improvement

ASTRA includes a self-improvement loop that learns from its own research history:

1. **Discovery Memory** — Every investigation outcome (success or failure) is stored in SQLite with method, domain, effect size, and p-value
2. **Hypothesis Generation** — New hypotheses are auto-generated from patterns in the discovery memory
3. **Adaptive Strategy** — Method selection adapts based on historical success rates per domain
4. **Sprint Success Rate** — Currently ~89–90% across all domains
5. **Exploration Balance** — Epsilon-greedy strategy ensures novel hypothesis spaces are explored

Current statistics:
- 726+ discoveries recorded
- 3,600+ method outcomes tracked
- 5 active scientific domains

---

## License

TBD

---

## Acknowledgments

Built on data from:
- [Pantheon+](https://pantheonplussh0es.github.io/) (Scolnic et al. 2022)
- [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/)
- [Gaia DR3](https://www.cosmos.esa.int/web/gaia/dr3) (ESA/Gaia)
- [SDSS DR18](https://www.sdss.org/dr18/)
- [GWTC](https://gwosc.org/) (LIGO/Virgo/KAGRA)
- [Planck 2018](https://www.cosmos.esa.int/web/planck) (ESA)
- [ZTF](https://www.ztf.caltech.edu/) (Zwicky Transient Facility)
- [TESS](https://tess.mit.edu/) (NASA)
