# Dashboard Figures for ASTRA RASTI Paper

## Selected Figures for Inclusion

### Figure 7: ASTRA Live Dashboard — Four-Panel Composite
**File**: `fig-dashboard-composite-4panel.png` (1600×900, 496KB)
**Content**: 2×2 grid showing Overview (top-left), Safety (top-right), Discoveries (bottom-left), Health (bottom-right)
**Paper context**: Demonstrates the complete monitoring and control interface. Shows OODA decision engine, state space trajectory, hypothesis pipeline, component health, cycle performance, and audit trail — all in one figure.
**Caption suggestion**: "The ASTRA Live Dashboard provides real-time monitoring across four operational views: (a) Overview showing the OODA decision engine, neural topology visualization, and autonomous decision log; (b) Safety monitoring with state space trajectory, anomaly detection, and alignment stability metrics; (c) Discoveries tab displaying the hypothesis pipeline with validated, testing, and proposed hypotheses; (d) Health monitoring showing component status, cycle performance, domain distribution, and audit trail."

### Figure 8: Safety Dashboard — Full View
**File**: `fig8-dashboard-safety.png` (1800×1013, 231KB)
**Content**: State space mind trajectory (PCA), anomaly detection drift monitor, alignment stability (78.4% composite — Scientific Rigor 82%, Reproducibility 92%, Epistemic Humility 83%)
**Paper context**: Key for the safety architecture section. Shows the state space visualization, boundary detection, and the 6-dimensional alignment scoring.
**Caption suggestion**: "Safety monitoring dashboard showing the state space mind trajectory (left), anomaly detection with drift metrics (right), and composite alignment stability scoring across six dimensions (bottom)."

### Alternative: Individual Dashboard Overview
**File**: `fig7-dashboard-overview.png` (1800×1013, 517KB) 
**Content**: Full overview tab with Activity Stream, OODA Decision Engine, AGI Neural Topology, Data Visualizations (hypothesis funnel, confidence radar, H₀ distribution, discovery rate, error rate), Autonomous Decision Log
**Use if**: Space permits a dedicated overview figure separate from the composite

## Detail Crops Available (for inline or supplementary use)
- `fig-detail-ooda-cycle.png` — Decision Engine ORIENT→SELECT→INVESTIGATE→EVALUATE→UPDATE
- `fig-detail-state-space.png` — State space mind trajectory with concentric safety boundaries
- `fig-detail-neural-topology.png` — AGI neural topology / hypothesis network graph
- `fig-detail-hypothesis-funnel.png` — Pipeline: Proposed→Screening→Testing→Validated→Published
- `fig-detail-cycle-performance.png` — Performance over engine cycles
- `fig-detail-domain-distribution.png` — Domain coverage donut chart
- `fig-detail-novelty-scores.png` — Top 10 novelty scores bar chart
- `fig-detail-control-panel.png` — Intervention console (Pause/E-Stop/Safe/Resume)
- `fig-detail-validated-hypotheses.png` — Cards showing validated hypothesis summaries

## Technical Notes
- All screenshots taken from live ASTRA v4.7 dashboard running on localhost
- Dashboard is ~607KB single-page HTML with embedded snapshot data
- Dark theme (Deep Space Black #06080d background) — prints well on white with border
- Font: Orbitron (headings), Space Mono (data), Inter (body)
- Resolution: 1920×1080 desktop viewport for all main shots
- All PNG format, suitable for LaTeX \includegraphics
