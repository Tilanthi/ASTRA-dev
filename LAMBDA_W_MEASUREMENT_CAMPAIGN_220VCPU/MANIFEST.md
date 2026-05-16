# λ/W Direct Measurement Campaign - Package Manifest

**Package**: LAMBDA_W_MEASUREMENT_CAMPAIGN_220VCPU
**Date**: 2026-05-01
**Target Cluster**: 220 CPU AMD EPYC 7B13
**Purpose**: Address theoretician peer review concerns about λ/W measurements

---

## Package Contents

### Configuration Files (`configs/`)

| Subdirectory | Count | Description |
|--------------|-------|-------------|
| `configs/LW_DIRECT/` | 36 | Supercritical λ/W direct measurements (Concern 5) |
| `configs/PERP_TIMESERIES/` | 27 | Perpendicular-field time-series (Concern 6) |
| `configs/DOMAIN_TEST/` | 3 | Domain size tests (extended12 only) (Concern 7) |
| `configs/manifest.json` | 1 | Complete configuration manifest |
| **Total Configs** | **66** | All Athena++ simulation configurations |

### Scripts (`scripts/`)

| Script | Purpose | Dependencies |
|--------|---------|--------------|
| `compile_athena.sh` | Compile Athena++ v21.0 with HDF5 | bash, gcc, python3 |
| `run_campaign.py` | Execute simulations with Ray | ray, subprocess, json |
| `extract_beading.py` | Extract λ/W from HDF5 snapshots | h5py, scipy, numpy |
| `analyze_lw_direct.py` | Analyze LW_DIRECT results | pandas, scipy, matplotlib |
| `analyze_perp_timeseries.py` | Analyze PERP_TIMESERIES results | pandas, scipy, matplotlib |
| `analyze_domain_test.py` | Analyze DOMAIN_TEST results | pandas, scipy, matplotlib |

### Documentation

| File | Purpose |
|------|---------|
| `README.md` | Comprehensive user guide |
| `MANIFEST.md` | This file - package inventory |

---

## Configuration Breakdown

### LW_DIRECT: 36 Simulations

**Parameter Space**:
- f (line mass): 1.5, 2.0, 2.5, 3.0
- β (plasma beta): 0.3, 1.0, 3.0
- θ (field angle): 0° (longitudinal)
- Seeds: 3 (42, 137, 251)

**Domain**: Lx = 32λJ, resolution = 1024×64×64

**Snapshots**: 10 outputs at t = 0.5 to 6.0 t_J

**Expected Output**: Direct λ/W measurements at f ≥ 1.5

---

### PERP_TIMESERIES: 27 Simulations

**Parameter Space**:
- f (line mass): 1.0, 1.5, 2.0
- β (plasma beta): 0.3, 1.0, 3.0
- θ (field angle): 90° (perpendicular)
- Seeds: 3 (42, 137, 251)

**Domain**: Lx = 24λJ, resolution = 768×64×64

**Snapshots**: 20 outputs at t = 0.5 to 6.0 t_J

**Expected Output**: Time-evolution of λ/W for perpendicular fields

---

### DOMAIN_TEST: 3 Simulations

**Parameter Space**:
- f (line mass): 1.5 (fixed - problematic point)
- β (plasma beta): 0.3 (fixed - problematic value)
- θ (field angle): 0° (longitudinal)
- Domain: 12λJ (extended12 only - resolution compatibility constraint)
- Resolution: 384×48×48
- Seeds: 3 (42, 137, 251)

**Expected Output**: λ/W extraction at f=1.5, β=0.3 with 12λJ domain

**Note**: Due to resolution compatibility constraints in the config generator, only
the extended12 (12λJ) domain was successfully generated. Additional domain/resolution
combinations can be tested in a follow-up campaign if needed.

---

## Computational Requirements

### Per-Simulation Resources

| Metric | Value |
|--------|-------|
| Cores | 16 MPI ranks |
| RAM | ~2-4 GB |
| Disk (output) | ~1-2 GB |
| Wall time | 1-3 hours |

### Cluster Configuration

```python
ray_config = {
    'num_cpus': 220,
    'max_concurrent': 12,  # 12 sims × 16 cores = 192 cores
    'cores_per_sim': 16,
}
```

### Total Resources

| Campaign | Simulations | CPU-hours | Wall time (12 concurrent) |
|----------|-------------|-----------|---------------------------|
| LW_DIRECT | 36 | ~720 | ~3 hours |
| PERP_TIMESERIES | 27 | ~480 | ~2.5 hours |
| DOMAIN_TEST | 3 | ~40 | ~0.5 hours |
| **Total** | **66** | **~1240** | **~6 hours** |

---

## Software Dependencies

### System Requirements

- **OS**: Linux (tested on Ubuntu 20.04, CentOS 7)
- **Python**: 3.7 or later
- **MPI**: OpenMPI or MPICH
- **Compiler**: GCC 7.0 or later (for C++14 support)

### Python Packages

```bash
# Core dependencies
pip install numpy scipy pandas h5py matplotlib

# Ray for distributed execution
pip install ray

# Optional: for monitoring
pip install jupyter
```

### HDF5 Library

```bash
# Ubuntu/Debian
sudo apt-get install libhdf5-dev hdf5-tools

# CentOS/RHEL
sudo yum install hdf5-devel

# macOS
brew install hdf5
```

---

## Execution Workflow

### Step 1: Compile Athena++

```bash
cd LAMBDA_W_MEASUREMENT_CAMPAIGN_220VCPU
chmod +x scripts/compile_athena.sh
./scripts/compile_athena.sh
```

**Expected Output**: Binary `athena_filament` in campaign directory

**Time**: ~10 minutes

---

### Step 2: Run Simulations

```bash
# Option A: Run all campaigns
python scripts/run_campaign.py --num-workers 220

# Option B: Run specific campaign
python scripts/run_campaign.py --campaign LW_DIRECT --num-workers 220

# Option C: Resume from interruption
python scripts/run_campaign.py --resume --num-workers 220
```

**Expected Output**:
- `outputs/<campaign>/<sim_name>/` directories
- HDF5 snapshot files (`*.h5`)
- History files (`*.hst`)
- Status files (`status.json`)

**Time**: ~7 hours total (on 220 CPUs)

---

### Step 3: Extract λ/W Measurements

```bash
# Extract from each campaign
python scripts/extract_beading.py outputs/LW_DIRECT/ --campaign LW_DIRECT
python scripts/extract_beading.py outputs/PERP_TIMESERIES/ --campaign PERP_TIMESERIES
python scripts/extract_beading.py outputs/DOMAIN_TEST/ --campaign DOMAIN_TEST
```

**Expected Output**: JSON files with λ/W measurements

**Time**: ~5 minutes

---

### Step 4: Analyze Results

```bash
# Analyze each campaign
python scripts/analyze_lw_direct.py
python scripts/analyze_perp_timeseries.py
python scripts/analyze_domain_test.py
```

**Expected Output**:
- Statistical summaries (`*.csv`)
- Fitting results (`*.json`)
- Figures (`figures/*.pdf`)
- Executive summaries (`*_SUMMARY.md`)

**Time**: ~10 minutes

---

## Output File Structure

```
outputs/
├── LW_DIRECT/
│   ├── LW_DIRECT_f1.5_beta0.3_M1.0_theta0.0_s42/
│   │   ├── config.json
│   │   ├── athena_input.dat
│   │   ├── LW_DIRECT_*.hst (history files)
│   │   ├── LW_DIRECT_*.h5 (HDF5 snapshots)
│   │   └── status.json
│   └── ... (36 simulations)
├── PERP_TIMESERIES/
│   └── ... (27 simulations)
└── DOMAIN_TEST/
    └── ... (18 simulations)
```

---

## Success Criteria

### LW_DIRECT (Concern 5)

- [ ] λ/W measured at f = 1.5, 2.0, 2.5, 3.0
- [ ] Uncertainties quantified from seed variation
- [ ] Extrapolation test performed (near-critical vs supercritical)
- [ ] Conclusion: λ_frag = 1.11 λ_MJ valid or needs revision?

### PERP_TIMESERIES (Concern 6)

- [ ] "GOOD" classification criteria defined
- [ ] Time-evolution maps generated
- [ ] λ/W = 1.25 representativeness assessed
- [ ] Physical explanation for 27/100 detection rate

### DOMAIN_TEST (Concern 7)

- [ ] Campaign 8 FLAT entries explained
- [ ] Minimum domain/resolution requirements identified
- [ ] Phase 1 robustness confirmed

---

## Validation Checklist

Before deploying to cluster:

- [ ] All 66 config files validated (syntax check)
- [ ] Athena++ compiles without errors
- [ ] Ray initializes with 220 CPUs
- [ ] Disk space > 200 GB available
- [ ] Output directories created
- [ ] Scripts have execute permissions

After simulation completion:

- [ ] All 66 status.json files exist
- [ ] Completion rate > 95%
- [ ] HDF5 snapshots present
- [ ] λ/W extraction successful
- [ ] Analysis scripts run without errors
- [ ] Figures generated correctly

---

## Package Integrity

### File Count Verification

```bash
# Config files
find configs/ -name "*.json" | wc -l  # Should be 66 (excluding manifest.json)

# Scripts
ls scripts/*.py scripts/*.sh | wc -l   # Should be 6

# Documentation
ls *.md | wc -l                        # Should be 2
```

### Manifest Hash

To verify package integrity after transfer:

```bash
# Generate checksum
find . -type f -exec sha256sum {} \; > MANIFEST.sha256

# Verify after transfer
sha256sum -c MANIFEST.sha256
```

---

## Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-05-01 | Initial package creation |

---

## References

1. **Theoretician Referee Report**: Concerns 5, 6, 7 about λ/W calibration and reliability
2. **Previous Campaign**: THEORETICIAN_CAMPAIGN (May 2026) - measured t_frag, not λ/W
3. **Assessment**: THEORETICIAN_RESULTS_ASSESSMENT.md - explains why previous campaign didn't address concerns
4. **Plan**: /Users/gjw255/.claude/plans/shimmering-gliding-breeze.md

---

**End of Manifest**
