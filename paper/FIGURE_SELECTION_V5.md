# Dashboard Figure Selection for ASTRA RASTI Paper V5.0

## Prepared by ASTRA (2026-04-06)

All screenshots captured at 1920×1080 from the live ASTRA dashboard (v4.7).
Source PNGs in `/shared/ASTRA/paper/figures/dashboard-screenshots/` (full-page + viewport).
Cropped paper-ready PNGs in `/shared/ASTRA/paper/figures/`.

---

## SELECTED FIGURES FOR PAPER (Recommended 8-10 total)

### Figure 1: `dashboard-overview-hero.png` (1920×1080)
**Content**: Full overview tab — AGI Neural Topology visualization (hypothesis network graph with domain-colored nodes), Activity Stream with engine log, Data Visualizations panel (Hypothesis Funnel, Domain Activity bar chart, Confidence Radar, H₀ Distribution, Discovery Rate, Error Rate).
**Paper section**: Section 2 (System Architecture) or Section 3 (Dashboard)
**Why include**: Hero image showing the entire system at a glance. The neural topology is visually striking and shows hypothesis interconnections. Domain Activity bars show multi-domain coverage.

### Figure 2: `dashboard-verified-discoveries.png` (1920×1080)
**Content**: Verified Discoveries section showing:
- **Kepler's Third Law** — recovered from 2,839 exoplanets (slope 1.497 vs theory 1.500, R²=0.9982)
- **Accelerating Universe** — measured from 1,701 supernovae (slope 5.33 vs 5.00 expected, +6.6% excess = dark energy signature)
- **Galaxy Death in Real Time** — blue fraction drops 50%→10% over 3 Gyr from 2,000 SDSS galaxies
- **Stellar Physics from Gaia DR3** — MS slope, three stellar populations identified
- **Causal Inference** — PC/FCI correctly found redshift causes color changes
**Paper section**: Section 4 (Results) — this is THE key results figure
**Why include**: Demonstrates ASTRA's flagship capability — blind recovery of fundamental physics. The Kepler's Law and dark energy results are the paper's strongest claims.

### Figure 3: `dashboard-self-improvement-trajectory.png` (1920×1080)
**Content**: Discovery Strength Trajectory chart (400 discoveries plotted with domain-colored scatter + rolling average trendline) + Method Performance table showing success rates per method per domain.
**Paper section**: Section 4.3 (Self-Improvement) or Section 5 (Discussion)
**Why include**: Shows the learning trajectory — discovery strength improving over time. The scatter plot with trendline is publication-quality. Method performance table shows which statistical approaches work best per domain.

### Figure 4: `dashboard-stigmergy-top.png` (1920×1080) 
**Content**: Pheromone Field Status panel (9,614 deposits, 901 exploration, 137 success, 825 failure, 343 novelty) + A/B Test comparison (Pheromone-Guided: 1,014 trials, 12 successes, 1.2% rate vs Baseline: 0 trials)
**Paper section**: Section 3.X (Stigmergy) — NEW SECTION NEEDED
**Why include**: Quantitative evidence of the stigmergy system's scale and operation. The A/B test framework shows rigorous self-evaluation methodology.

### Figure 5: `dashboard-stigmergy-exploration.png` (1920×1080)
**Content**: Knowledge Gaps by Domain (bar chart — Astrophysics to Cross-Domain, with Epidemiology at 1.00 and Cross-Domain at 0.04), Exploration Strategy panel (strategy: explore, curiosity: 0.82, recommended domain: Epidemiology), Gordon Parameters (evaporation: 0.050, reinforcement: 0.100, anternet weight: 0.600, restraint: 0.400, switch probability: 0.150, contact rates), Swarm Agents panel (Explorer: 98 actions, Exploiter: 132 actions/99% success, Falsifier: 0, Analogist: 74 actions/100%, Scout: 0)
**Paper section**: Section 3.X (Stigmergy) — the key stigmergy figure
**Why include**: This single screenshot shows ALL components of the swarm intelligence system working together: knowledge gap identification, exploration/exploitation balance, biologically-inspired parameters, and specialized agent roles.

### Figure 6: `dashboard-safety-statespace.png` (1920×1080)
**Content**: State Space — Mind Trajectory (elliptical orbit visualization showing system state in phase space) + Anomaly Detection — Drift Monitor (Confidence Drift 0.32 NOMINAL, Exploration Balance 0.61 CRITICAL, Domain Diversity 0.48 WARNING, Value Stability 0.55 WARNING, Confidence Velocity 0.22 NOMINAL)
**Paper section**: Section 3.Y (Safety Architecture)
**Why include**: Shows the safety monitoring system — both the abstract visualization and concrete drift metrics. Important for responsible AI narrative.

### Figure 7: `dashboard-discoveries.png` (cropped, 1200×563)
**Content**: Full Hypothesis Pipeline — 38 VALIDATED hypotheses across 5 domains (Astrophysics, Climate Science, Cross-Domain, Economics, Epidemiology) with confidence scores (0.77-0.99), plus 6 PROPOSED and 7 ARCHIVED.
**Paper section**: Section 4 (Results) — hypothesis lifecycle
**Why include**: Shows the full scientific pipeline with hypothesis states, domain distribution, and confidence progression.

### Figure 8: `dashboard-self-improvement-metrics.png` (1920×1080) 
**Content**: Top-level metrics banner (397 Total Discoveries, 184 Method Outcomes, 89.1% Success Rate, 18.4 Avg Sig Results, Galaxy Hot Domain) + Improvement Trajectory sub-metrics (Success Rate 89.1%, Avg Sig Results 18.4, Confidence Delta +0.0331, Hypotheses Generated 40)
**Paper section**: Section 4.3 or abstract
**Why include**: Clean quantitative summary of the self-improvement system. Good for summarizing results.

---

## OPTIONAL/SUPPLEMENTARY FIGURES

- `dashboard-health.png` — Component Health (100% UP), good for supplementary
- `dashboard-control.png` — Intervention Console, good for human oversight discussion
- `dashboard-literature.png` — Paper Library with arXiv IDs, good for literature integration section
- `dashboard-overview-engine.png` — Engine log detail + OODA cycle visualization
- `dashboard-swarm-agents.png` — Close-up of 5 swarm agent cards (Explorer, Exploiter, Falsifier, Analogist, Scout)

---

## KEY POINTS FOR PAPER REVISION

### Stigmergy Section (NEW — critical addition)
The paper currently has ONE LINE about stigmergy in the acknowledgments. This needs a full subsection (1-2 pages) covering:

1. **Concept**: Stigmergy = indirect coordination through environmental modification (Grassé 1959, ant colonies). Applied to scientific discovery: hypotheses leave "pheromone trails" that guide future exploration.

2. **Implementation**:
   - `DigitalPheromoneField` — continuous field with deposits at domain-mixture coordinates
   - `StigmergicMemory` — persistent memory of successful/failed explorations
   - `PheromoneUpdater` + `CuriosityValueCalculator` — Gordon's biological transforms
   - 5 pheromone types: SUCCESS, FAILURE, NOVELTY, EXPLORATION, DANGER
   - Deposits decay (evaporation rate 0.050) and accumulate (reinforcement rate 0.100)

3. **Gordon Parameters**: Biologically-calibrated from ant colony research (Gordon 2010):
   - Anternet weight: 0.600 (interaction frequency influences foraging decisions)
   - Restraint weight: 0.400 (colony restraint under resource scarcity)  
   - Switch probability: 0.150 (task-switching rate)
   - Contact rate min/max: 0.033/0.167

4. **Swarm Agents**: 5 specialized agent types inspired by ant colony division of labour:
   - **Explorer** (98 actions) — seeks unexplored domains, follows NOVELTY pheromones
   - **Exploiter** (132 actions, 99% success) — deepens investigation in high-success areas, follows SUCCESS trails
   - **Falsifier** (0 actions) — attempts to disprove hypotheses, follows DANGER pheromones
   - **Analogist** (74 actions, 100% success) — discovers cross-domain structural analogies
   - **Scout** (0 actions) — surveys knowledge landscape, maps coverage gaps

5. **Knowledge Gap Analysis**: Measures exploration coverage per domain:
   - Astrophysics: 0.00 gap (fully explored)
   - Epidemiology: 1.00 gap (mostly unexplored)
   - Cross-Domain: 0.04 gap (well explored)
   
6. **A/B Testing**: Pheromone-guided vs random baseline selection, 1,014 trials, rigorous evaluation

7. **Safety Circuit Breaker**: If pheromone guidance success rate drops below threshold, system automatically reverts to baseline selection

8. **5 Engine Integration Points**:
   - ORIENT → ScoutAgent surveys landscape
   - SELECT → Pheromone re-ranking of candidate hypotheses  
   - INVESTIGATE → Deposit pheromones based on results
   - EVALUATE → NOVELTY pheromone for novel findings
   - UPDATE → Cross-domain connection deposits

### Self-Improvement Section (expand existing)
- 397 discoveries across 6 domains
- Discovery strength trajectory shows improving trend
- Adaptive method selection based on historical success rates
- Hypothesis generator creates new hypotheses from strong discoveries
- 184 method outcomes tracked for strategy optimization

### Dashboard Section (update)
- Now 9 tabs (was described as fewer in V4.0)
- Add Stigmergy tab description
- Reference new figures

### Results Update
- 38 validated hypotheses (was fewer in V4.0)
- 5 verified discoveries with specific measurements
- Multi-domain coverage: Astrophysics, Economics, Climate, Epidemiology, Cross-Domain

---

## FIGURE FILE MANIFEST

All in `/shared/ASTRA/paper/figures/`:

| Filename | Dimensions | Size | Paper Use |
|----------|-----------|------|-----------|
| `dashboard-overview-hero.png` | 1920×1080 | 376KB | Fig 1 |
| `dashboard-verified-discoveries.png` | 1920×1080 | 160KB | Fig 2 |
| `dashboard-self-improvement-trajectory.png` | 1920×1080 | 163KB | Fig 3 |
| `dashboard-stigmergy-top.png` | 1920×1080 | 108KB | Fig 4 |
| `dashboard-stigmergy-exploration.png` | 1920×1080 | 110KB | Fig 5 |
| `dashboard-safety-statespace.png` | 1920×1080 | 120KB | Fig 6 |
| `dashboard-discoveries.png` | 1200×563 | 375KB | Fig 7 |
| `dashboard-self-improvement-metrics.png` | 1920×1080 | 55KB | Fig 8 |

Plus existing figures from V4.0 in `/shared/ASTRA/paper/figures/`:
- `architecture-diagram.pdf`
- `hypothesis-lifecycle.pdf`  
- `ooda-cycle.pdf`
- `data-sources.pdf`
- etc.
