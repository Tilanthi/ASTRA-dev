# ASTRA: Autonomous Scientific Discovery in Astrophysics

> A unified framework for autonomous hypothesis generation and validation
> in astronomy and astrophysics, integrating causal reasoning, Bayesian inference,
> dimensional analysis, and multi-wavelength data fusion.

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com)

**Author**: Glenn J. White (The Open University & RAL Space)  
**Paper**: White, G.J. (2026). *ASTRA: Autonomous Scientific Discovery in Astrophysics.* RASTI, in press.  
**Repository**: [github.com/Tilanthi/ASTRA](https://github.com/Tilanthi/ASTRA)

---

## Highlights

- **89-endpoint FastAPI backend** for real-time scientific discovery orchestration
- **Autonomous OODA research cycle** — Orient → Select → Investigate → Evaluate → Update
- **9 real data sources** (27,430+ data points): Pantheon+ SNe Ia, NASA Exoplanet Archive, Gaia DR3, SDSS DR18, LIGO gravitational waves, Planck CMB, ZTF transients, TESS, SDSS galaxy clusters
- **40+ validated hypotheses** across 5 scientific domains
- **Self-improving discovery memory** — SQLite-backed with 780+ discoveries and 3,500+ method outcomes
- **Safety architecture** — 5-state controller, arbiter, circuit breakers, phased autonomy, ethics reasoning
- **Live dashboard** with 8 interactive tabs (glassmorphism UI, 95/100 design critic score)
- **RASTI paper** with 6 reproducible worked examples and publication-quality figures
- **75 astrophysics domain modules** covering cosmology, stellar physics, galaxy evolution, ISM, and more
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
│   ├── safety/                     Safety subsystem (13 modules)
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
├── astra_core/                  ← Core cognitive framework (~614 modules)
│   ├── domains/                    75 astrophysics domain modules
│   ├── reasoning/                  98 reasoning engines
│   ├── capabilities/               Analysis capabilities
│   ├── memory/                     Persistent memory system
│   ├── autonomous_research/        V7 Autonomous Scientist
│   ├── causal/                     Causal inference subsystem
│   ├── metacognitive/              Meta-cognitive monitoring
│   ├── simulation/                 Physics & market simulations
│   ├── swarm/                      Swarm intelligence
│   └── tests/                      Core test suites
│
├── paper/                       ← RASTI paper
│   ├── astra-rasti-v2.3.tex        Main manuscript (RASTI class, ~1,375 lines)
│   ├── RASTI_paper_V1.12.tex       Reference version
│   ├── supplement.tex              Supplementary material (~420 lines)
│   ├── references-v2.bib           Bibliography (57 entries)
│   ├── RASTI.cls                   RASTI document class
│   ├── mnras.cls / mnras.bst       MNRAS class (alternative)
│   ├── figures/                    Publication figures (6 PDFs + generation script)
│   ├── Example1/                   Scaling relations (Herschel filaments)
│   ├── Example2/                   Multi-wavelength fusion (Chandra CDFS)
│   ├── Example3/                   Pattern recognition (SDSS galaxies)
│   ├── Example4/                   Causal inference (Gaia stellar + Phillips)
│   ├── Example5/                   Bayesian model selection (virial scaling)
│   └── Example6/                   Discovery mode (galaxy survey, 3,000 objects)
│
├── filaments/                   ← Filament width research
│   ├── filament_width_analysis.py  Analysis of the 0.1 pc mystery
│   ├── mhd_simulation_suite.py     MHD simulations (Mach number, plasma beta)
│   ├── sonic_scale_theory_deep_dive.py  Sonic scale theory investigation
│   └── simulation_results/         Simulation output data
│
├── RASTI_AI/                    ← Jupyter notebook demonstrations
│   ├── test02_scaling_relations_figure.ipynb
│   ├── test04_multiwavelength_fusion.ipynb
│   ├── test06_genuine_discovery.ipynb
│   ├── test11_causal_inference.ipynb
│   └── test12_bayesian_model_selection.ipynb
│
├── User_Manual/                 ← User documentation
│   └── User_Manual.md
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
git clone https://github.com/Tilanthi/ASTRA.git
cd ASTRA

pip install fastapi uvicorn scipy numpy pandas requests beautifulsoup4 \
            scikit-learn aiofiles
```

### Running the Server

```bash
python3 -m astra_live_backend.server
# → Server running at http://localhost:8787/
```

### Using the Core Framework

```python
from astra_core import create_stan_system

# Create system with auto-optimized capabilities
system = create_stan_system()

# Answer queries with automatic capability selection
result = system.answer("What causes supernovae?")
print(result['answer'])
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

### Live Dashboard

ASTRA includes a real-time mission control dashboard with 8 interactive tabs:

- **Overview** — Neural topology, activity log, hypothesis funnel, domain activity
- **Safety** — State-space visualization, anomaly detection, drift monitor
- **Control** — Engine controls (pause/safe/e-stop), supervisor, approvals
- **Health** — System metrics, persistence stats, method success rates
- **Phase 4** — Operational readiness protocol, ceremonies, rollback procedures
- **Discoveries** — Hypothesis pipeline, 6 verified discoveries with full statistics
- **Self-Improve** — Discovery timeline, method performance table, learning metrics
- **Literature** — Citation metrics, arXiv paper integration, novelty scores

Dashboard score: **95/100** (professional design critic audit).

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

## RASTI Paper

**"ASTRA: Autonomous Scientific Discovery in Astrophysics"**

- **Author**: Glenn J. White (The Open University & RAL Space)
- **Target**: RASTI (Royal Astronomical Society Techniques and Instruments)
- **Format**: RASTI LaTeX class, 22 pages, 6 figures, 57 references
- **Location**: `paper/` directory

### Six Worked Examples

The paper includes six fully reproducible test cases, each with data generation, analysis, and figure scripts:

| Example | Topic | Data | Key Results |
|---------|-------|------|-------------|
| 1 | Scaling relations | Herschel filaments | Dimensional analysis, physical validation |
| 2 | Multi-wavelength fusion | Chandra CDFS | Probabilistic cross-matching, Bayesian uncertainty |
| 3 | Pattern recognition | SDSS galaxies | Galaxy property correlations, bimodality |
| 4 | Causal inference | Gaia stellar + SNe Ia | Structural causal models, Phillips relation |
| 5 | Bayesian model selection | Virial scaling | Evidence computation, prior specification |
| 6 | Discovery mode | Galaxy survey (3,000) | Main sequence recovery, outlier detection |

### Building the Paper

```bash
cd paper

# Generate figures
python3 figures/generate_figures.py

# Compile PDF (RASTI class)
pdflatex astra-rasti-v2.3.tex
bibtex astra-rasti-v2.3
pdflatex astra-rasti-v2.3.tex
pdflatex astra-rasti-v2.3.tex

# Compile supplement
pdflatex supplement.tex

# Run a worked example
cd Example1
python3 01_generate_data.py
python3 02_v5_discovery_test.py
python3 03_generate_figures.py
```

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

## Filaments Research

ASTRA includes an investigation into the long-standing mystery of why interstellar filament widths cluster at ~0.1 pc across three orders of magnitude in density:

- **Finding**: The sonic scale of the turbulent cascade (λ_sonic ≈ 0.1 pc) sets the minimum filament width
- **Evidence**: 5,476 filaments measured across 10+ regions (Herschel, Planck, ALMA)
- **Simulations**: 7 MHD simulations varying Mach number (1–20) and plasma beta (0.1–10)
- **Location**: `filaments/` directory

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

## Self-Improvement

ASTRA includes a self-improvement loop that learns from its own research history:

1. **Discovery Memory** — Every investigation outcome (success or failure) is stored in SQLite with method, domain, effect size, and p-value
2. **Hypothesis Generation** — New hypotheses are auto-generated from patterns in the discovery memory
3. **Adaptive Strategy** — Method selection adapts based on historical success rates per domain
4. **Sprint Success Rate** — Currently ~89–90% across all domains
5. **Exploration Balance** — Epsilon-greedy strategy ensures novel hypothesis spaces are explored

Current statistics:
- 780+ discoveries recorded
- 3,500+ method outcomes tracked
- 5 active scientific domains

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
# Regenerate with latest data snapshot
python3 astra_live_backend/generate_dashboard.py
# Output: /shared/public/astra-live/index.html
```

### Generating Figures

```bash
python3 paper/figures/generate_figures.py
# Output: paper/figures/fig{1-6}-*.{pdf,png}
```

---

## Scope and Limitations

ASTRA is not presented as achieving artificial general intelligence (AGI) or AGI-like performance. The system operates within defined astrophysical domains using established algorithms (PC algorithm, Bayesian inference, dimensional analysis, FCI causal discovery) combined through an integrated architecture.

We should not expect to give ASTRA one of the big contemporary problems like "What is the nature of Dark Matter and Dark Energy" and expect a computational Eureka moment. ASTRA's role in science is to work alongside the experienced astronomer to analyze data and facilitate genuine discovery. ASTRA is therefore a tool to assist the astronomer, rather than a replacement for domain expertise.

Results are validated against known physical theory and observational constraints. The system does not claim general reasoning beyond its training domains or autonomous operation without human oversight.

---

## License

| Component | License |
|-----------|---------|
| ASTRA codebase (Python, backend, engine) | [Apache License 2.0](LICENSE) |
| Paper & documentation | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |
| Data outputs (discoveries, datasets) | [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) |

See [LICENSE](LICENSE) and [NOTICE](NOTICE) for full terms and attribution.

---

## Acknowledgments

**Research Partner**: [OpenHub](https://openhub.co.th/), Thailand  
**Research Platform**: [Taurus](https://taurus.cloud) multi-agent orchestration platform

The development of ASTRA builds upon foundational work on stigmergic intelligence and autonomous navigation by Dey, R. (2025) — [STAN: Stigmergic A* Navigation](https://github.com/vbrltech/STAN) — at OpenHub, Thailand.

Built on data from:
- [Pantheon+](https://pantheonplussh0es.github.io/) (Scolnic et al. 2022)
- [NASA Exoplanet Archive](https://exoplanetarchive.ipac.caltech.edu/)
- [Gaia DR3](https://www.cosmos.esa.int/web/gaia/dr3) (ESA/Gaia)
- [SDSS DR18](https://www.sdss.org/dr18/)
- [GWTC](https://gwosc.org/) (LIGO/Virgo/KAGRA)
- [Planck 2018](https://www.cosmos.esa.int/web/planck) (ESA)
- [ZTF](https://www.ztf.caltech.edu/) (Zwicky Transient Facility)
- [TESS](https://tess.mit.edu/) (NASA)
- [World Bank Open Data](https://data.worldbank.org/)
- [NASA GISS](https://data.giss.nasa.gov/) Surface Temperature Analysis
- [NOAA Global Monitoring Laboratory](https://gml.noaa.gov/) (Mauna Loa CO₂)
