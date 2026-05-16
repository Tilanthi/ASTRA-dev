# Peer Review Response Campaign
## Complete MHD Simulation Package for External 200-CPU Computer

**Version**: 1.0
**Date**: 23 April 2026
**Purpose**: Address critical peer review concerns for MNRAS filament spacing paper

---

## QUICK START

```bash
# 1. Extract package
tar -xzf peer_review_response_APR2026.tar.gz
cd peer_review_response_APR2026

# 2. Compile Athena++
bash scripts/compile_athena.sh

# 3. Launch campaign
bash run_campaign.sh
```

---

## CAMPAIGN OVERVIEW

This campaign comprises **320 new Athena++ MHD simulations** designed to address four critical gaps identified in peer review:

| Gap | Description | Simulations | Phase |
|-----|-------------|-------------|-------|
| **T3** | No perpendicular field simulations | 96 | 2 |
| **T1/T2** | Limited near-critical regime (f<1.4) | 80 | 1 |
| **T9** | No oblique field calibration | 90 | 3 |
| **EOS** | Isothermal vs adiabatic comparison | 54 | 4 |

---

## PARAMETER SPACE

### Phase 1: Near-Critical Campaign (80 simulations)
- **Objective**: Detect longitudinal beading in f≈1 regime
- **Parameters**: f = 1.0-1.2, β = 0.3-1.0, M = 1.0-2.0, seeds = {1,2}
- **Field geometry**: Longitudinal (θ = 0°)
- **EOS**: Isothermal

### Phase 2: Perpendicular Field Campaign (96 simulations)
- **Objective**: Test realistic field geometry (90% of filaments)
- **Parameters**: f = 1.5-3.0, β = 0.3-2.0, M = 1.0-2.0, seeds = {1,2}
- **Field geometry**: Perpendicular (θ = 90°)
- **EOS**: Isothermal

### Phase 3: Oblique Field Calibration (90 simulations)
- **Objective**: Validate λ_frag = 1.11 λ_MJ across field geometries
- **Parameters**: θ = 30°, 45°, 60°; f = 1.5-2.5; β = 0.5-2.0; M = 1.0-2.0
- **Field geometry**: Oblique (specified angle)
- **EOS**: Isothermal

### Phase 4: Adiabatic Extension (54 simulations)
- **Objective**: Test if adiabatic EOS allows beading by slowing radial collapse
- **Parameters**: f = 1.0-1.2, β = 0.5-1.0, M = 1.0, seeds = {1,2,3}
- **Field geometry**: Longitudinal (θ = 0°)
- **EOS**: Adiabatic (γ = 5/3)

---

## COMPUTATIONAL REQUIREMENTS

### Hardware
- **CPUs**: 200 (AMD EPYC 7B13 or similar)
- **RAM**: ~2 GB per simulation (16 MPI ranks)
- **Disk**: ~320 GB for all HDF5 outputs

### Software
- **MPI**: OpenMPI or MPICH
- **Python**: 3.8+ with Ray, NumPy, Pandas, Matplotlib
- **Athena++**: v21.0 (compiled from source)

### Execution Configuration
```python
# Ray configuration
ray.init(num_cpus=200)

# Parallel execution
max_concurrent = 12  # 12 simultaneous simulations
mpi_ranks_per_sim = 16  # 16 MPI ranks per simulation
```

---

## OUTPUT REQUIREMENTS

### Per-Simulation Data
Each simulation produces:
- **Status JSON**: Classification, t_frag, n_peaks, lambda_frag, quality
- **HDF5 snapshots**: Minimum 15 snapshots at Δt = 0.05 tJ
- **History file**: Full time evolution (HST format)

### Critical Deliverables
1. **simulation_catalog.csv** - Master catalog of all 320 simulations
2. **fig1_beading_threshold.pdf** - Where longitudinal beading emerges
3. **fig2_lambda_W_comparison.pdf** - λ/W vs field geometry
4. **fig3_oblique_calibration.pdf** - Validation of λ_frag = 1.11 λ_MJ
5. **fig4_adia_comparison.pdf** - Isothermal vs adiabatic comparison
6. **SUMMARY_REPORT.md** - Response to each peer review concern

---

## SUCCESS CRITERIA

The campaign will be successful if it demonstrates:

1. **Longitudinal beading detection**: At least one regime shows ≥2 longitudinal peaks
2. **Perpendicular field λ_frag**: Direct measurement of λ/W for perpendicular fields
3. **Oblique calibration validation**: Confirmation of λ_frag = 1.11 λ_MJ
4. **Near-critical characterization**: Identification of beading threshold f
5. **EOS comparison**: Assessment of isothermal vs adiabatic fragmentation

---

## EXECUTION FLOW

### Preparation (First time only)
```bash
# Extract package
tar -xzf peer_review_response_APR2026.tar.gz
cd peer_review_response_APR2026

# Compile Athena++
bash scripts/compile_athena.sh

# Verify Ray installation
python3 -c "import ray; print(ray.__version__)"
```

### Execution (Choose mode)
```bash
# Interactive mode (recommended)
bash run_campaign.sh

# Direct Python
python3 scripts/launch_campaign.py --phase 1      # Phase 1 only
python3 scripts/launch_campaign.py --phase 1-2    # Phases 1+2
python3 scripts/launch_campaign.py --all          # Full campaign

# Resume after interruption
python3 scripts/launch_campaign.py --all --resume
```

### Analysis (After simulations complete)
```bash
python3 scripts/analyze_campaign.py
```

---

## INTEGRATION WITH PAPER

After successful campaign completion:

### 1. Copy analysis outputs
```bash
cp analysis_output/fig*.pdf /path/to/paper/figures/
cp analysis_output/SUMMARY_REPORT.md /path/to/paper/
cp analysis_output/simulation_catalog.csv /path/to/paper/
```

### 2. Update paper sections
- **Abstract**: Mention new simulations addressing concerns
- **Section 4**: Add perpendicular field and oblique calibration results
- **Section 5**: Update discussion with new evidence
- **Conclusions**: Revise with new findings

### 3. Generate response to reviewer
- Document how each concern was addressed
- Cite specific simulations showing beading
- Include figures demonstrating perpendicular field fragmentation

---

## TROUBLESHOOTING

### Ray initialization fails
```bash
ray stop
ray start --head
```

### Simulations timeout frequently
```python
# Edit scripts/launch_campaign.py
TIMEOUT_SECONDS = 21600  # Increase from 14400 to 21600 (6 hours)
```

### Memory issues
```python
# Edit scripts/launch_campaign.py
MAX_CONCURRENT = 8  # Reduce from 12 to 8
```

### Athena++ compilation fails
- Check HDF5, FFTW3, MPI are installed
- Verify problem generator is in src/prob/
- Review compile_athena.sh output for errors

---

## PACKAGE STRUCTURE

```
peer_review_response_APR2026/
├── INDEX.md                           # This file
├── run_campaign.sh                    # Master launch script
│
├── config/
│   ├── campaign_specification.json    # Campaign metadata
│   └── simulation_manifest.json       # Complete simulation list (320 sims)
│
├── scripts/
│   ├── launch_campaign.py             # Ray-based parallel execution
│   ├── analyze_campaign.py            # Analysis and figure generation
│   ├── compile_athena.sh              # Athena++ compilation script
│   └── extract_lambda.py              # Longitudinal peak detection
│
├── templates/
│   ├── athena_input_template.dat      # Athena++ input file template
│   └── filament_spacing_pr.cpp        # Problem generator source code
│
└── docs/
    ├── README.md                       # Complete documentation
    ├── QUICKSTART.md                   # Quick start guide
    └── DATA_RETURN_SPEC.md            # Required outputs for paper
```

---

## SUPPORT

For technical issues:
1. Check docs/README.md for detailed documentation
2. Review docs/QUICKSTART.md for common problems
3. Examine logs in status/ directory for simulation details

For scientific questions:
- Consult campaign_specification.json for scientific rationale
- Review INDEX.md for peer review concern mapping
- Refer to original filament spacing paper for context

---

**Campaign prepared by**: ASTRA autonomous system
**Date**: 23 April 2026
**Purpose**: Peer review response for MNRAS filament spacing paper
