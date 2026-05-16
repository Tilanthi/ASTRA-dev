# Peer Review Response Simulation Campaigns: Summary Document
## MNRAS Major Revision - 2026-04-30

### Executive Summary

This document summarizes six comprehensive ATHENA++ MHD simulation campaigns designed to address all major concerns raised during peer review of the filament spacing paper. The campaigns total **1,023 simulations** requiring approximately **61 hours** on a 200-CPU ray cluster (~2.5 days of cluster time).

### Campaign Overview

| Campaign | ID | Simulations | Runtime (hrs) | Priority | Status |
|----------|----|-------------|---------------|----------|--------|
| Mixed Field Geometry λ/W Calibration | C8 | 175 | 15 | CRITICAL | SPECIFIED |
| Staged Fragmentation in Supercritical Regime | C9 | 240 | 20 | CRITICAL | SPECIFIED |
| Filament Length L/3 Convergence Test | C10 | 48 | 6 | HIGH | SPECIFIED |
| Temporal Evolution Scenario Test | C11 | 60 | 8 | MEDIUM | SPECIFIED |
| Refined DTC with Extended Coverage | C12 | 300 | 12 | MEDIUM | SPECIFIED |
| Literature β Compilation and Validation | C13 | 0* | 1 week** | HIGH | SPECIFIED |

*Research campaign (literature review)
**Estimated time for literature search and analysis

### Scientific Objectives

#### Campaign 8: Mixed Field Geometry λ/W Calibration (CRITICAL)

**Resolves**: Central tension between perpendicular-field theory (λ/W ≈ 1.25) and observations (λ/W = 2.79 for mostly perpendicular filaments)

**Key Question**: What mixing fraction of longitudinal-field filaments is needed to reproduce observed λ/W values?

**Parameters**:
- f = 1.5 (representative supercritical)
- β = [0.3, 0.5, 1.0, 1.5, 2.0]
- θ = [0°, 15°, 30°, 45°, 60°, 75°, 90°] (B-field angles)
- Seeds: 5 per parameter point

**Domain**: 16λ_J × 1λ_J × 1λ_J at 512 × 64 × 64

**Output**: λ/W(θ) calibration for each β, mixing fraction analysis

---

#### Campaign 9: Staged Fragmentation in Supercritical Regime (CRITICAL)

**Resolves**: Supercritical extrapolation gap and radial vs longitudinal fragmentation

**Key Innovation**: Time-dependent line mass ramping to test whether early-time fragmentation at near-critical f survives supercritical accretion

**Parameters**:
- f_initial = [0.9, 1.0, 1.1, 1.2]
- f_final = [1.5, 2.0, 2.5, 3.0]
- β = [0.5, 1.0, 2.0]
- Seeds: 5 per parameter point

**Staged Evolution**:
- Phase 1: Evolve at f_initial until t = 1.2 t_J
- Phase 2: Linear ramp to f_final over 0.3 t_J
- Phase 3: Evolve at f_final until t = 2.0 t_J

**Output**: Beading persistence classification, λ/W measurements

---

#### Campaign 10: Filament Length L/3 Convergence Test (HIGH)

**Resolves**: Pairwise median convergence problem with proper NN spacing validation

**Test Scenarios**:
- Test A: Periodic beading at known spacing (d = 0.3 pc)
- Test B: Random uniform core distribution

**Regions**: All 8 HGBS regions (Taurus, Orion B, Aquila, Perseus, Ophiuchus, Serpens, TMC1, CRA)

**Plus**: Full HGBS re-analysis with proper NN spacing computation

**Output**: Bias quantification, region-by-region NN spacing results

---

#### Campaign 11: Temporal Evolution Scenario Test (MEDIUM)

**Resolves**: Were HGBS filaments near-critical at fragmentation time?

**Accretion Scenarios**:
- Scenario A: No accretion (control) - f = 1.0
- Scenario B: Slow accretion - f(t) = 1.0 → 1.5 over 5 t_J
- Scenario C: Rapid accretion - f(t) = 1.0 → 2.0 over 2 t_J
- Scenario D: Very rapid accretion - f(t) = 1.0 → 3.0 over 1 t_J

**Parameters**: β = [0.5, 1.0, 2.0], Seeds: 5

**Output**: λ/W at fragmentation, beading persistence tracking

---

#### Campaign 12: Refined DTC with Extended Coverage (MEDIUM)

**Resolves**: Do corrected DTC results shift the three-regime framework?

**Focus**: β = 0.3 region where artifacts occurred

**Parameters**:
- M = [0.5, 0.8, 1.0, 1.2, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0] (extended range)
- f = [1.2, 1.4, 1.6, 1.8, 2.0, 2.2]
- Seeds: 5

**CRITICAL FIX**: Wall-clock timeout = 6 hours (corrected from 600s)

**Output**: Updated stability boundary, boundary shift analysis

---

#### Campaign 13: Literature β Compilation and Validation (HIGH)

**Resolves**: Independent validation of β-constraints from λ/W

**Approach**: Compile Zeeman, polarimetry, and other B-field measurements from literature

**Comparison**: Use Campaign 7 calibration to predict β from λ/W, compare with measurements

**Output**: β comparison table, scatter plot, consistency assessment

---

### Execution Instructions

#### Prerequisites

```bash
# Load modules
module load astra/athena++
module load ray

# Activate conda environment
conda activate astra
```

#### Run All Campaigns

```bash
cd /data/peer_response_runs/specification
bash run_all_campaigns.sh
```

#### Run Individual Campaigns

```bash
# Campaign 8 only
bash run_all_campaigns.sh C8

# Campaigns 8 and 9
bash run_all_campaigns.sh C8 C9

# Direct ray execution
cd C8_Mixed_Geometry
python -m ray.execute --num-cpus 200 run_campaign_8.py
```

### Output Format

All campaigns produce:

1. **results.json** - Machine-readable summary
2. **analysis_summary.pdf** - Visual summary figures
3. **README.md** - Campaign-specific documentation
4. **HDF5 snapshots** - Selected simulations (validation)

### Data Return Format

After completion, package results as:

```
peer_review_response_results_<date>.tar.gz
├── C8_Mixed_Geometry/
├── C9_Staged_Fragmentation/
├── C10_L3_Convergence/
├── C11_Temporal_Evolution/
├── C12_Refined_DTC/
└── C13_Beta_Validation/
```

### Expected Timeline

| Phase | Duration | Description |
|-------|----------|-------------|
| Specification | Complete | All 6 campaigns specified |
| Execution | ~3 days | 61 hours on 200 CPUs |
| Analysis | ~1 week | Process results, generate figures |
| Validation | ~1 week | Cross-check with observations |
| Paper revision | ~1 week | Incorporate results |

### Contact

For questions about campaign specifications or execution:
- ASTRA Peer Review Response Team
- Date: 2026-04-30
- Repository: github.com/Tilanthi/ASTRA-dev

### Version History

- v1.0 (2026-04-30): Initial specification complete
  - All 6 campaigns specified
  - Runner scripts created
  - Documentation complete
