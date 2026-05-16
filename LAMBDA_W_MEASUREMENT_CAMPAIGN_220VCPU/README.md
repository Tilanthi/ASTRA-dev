# λ/W Direct Measurement Campaign

**Athena++ MHD simulation campaign to CORRECTLY address theoretician peer review concerns.**

---

## Overview

This campaign is designed to measure **λ/W (fragmentation wavelength)**, not t_frag (fragmentation timescale), to properly address the theoretician referee's three major concerns:

### Concern 5: Calibration Extrapolation
**Issue**: λ_frag = 1.11 λ_MJ calibration derived from near-critical regime (f ≈ 1.0-1.2) and extrapolated to supercritical (f ≥ 1.5).

**Campaign**: `LW_DIRECT` - Direct λ/W measurements at f = 1.5, 2.0, 2.5, 3.0 with longitudinal B-field.

### Concern 6: Perpendicular-Field Reliability
**Issue**: λ/W = 1.25 for perpendicular fields from only 27/100 "GOOD" measurements. Selection criteria unclear.

**Campaign**: `PERP_TIMESERIES` - Time-series λ/W analysis for perpendicular fields to understand when/why axial beading appears.

### Concern 7: FLAT Entries in Campaign 8
**Issue**: Campaign 8 shows FLAT entries at (θ=0°, β=0.3) contradicting Phase 1 results (100% fragmentation).

**Campaign**: `DOMAIN_TEST` - Domain size/resolution investigation to explain why λ/W extraction failed.

---

## Critical Difference from Previous Campaign

| Aspect | Previous Campaign | This Campaign |
|--------|------------------|---------------|
| **Metric** | t_frag (time) | λ/W (wavelength) |
| **Outputs** | HST files only | HDF5 snapshots at multiple times |
| **Domain** | Standard (8λJ) | Extended (16-32λJ) |
| **Analysis** | Fragmentation timescale | Beading pattern extraction |

**Key Innovation**: HDF5 snapshots enable direct λ/W measurement from density profiles.

---

## Campaign Structure

```
LAMBDA_W_MEASUREMENT_CAMPAIGN_220VCPU/
├── configs/                    # Configuration files (66 total)
│   ├── LW_DIRECT/             # 36 configs for supercritical λ/W
│   ├── PERP_TIMESERIES/       # 27 configs for perpendicular fields
│   ├── DOMAIN_TEST/           # 3 configs for domain tests (extended12)
│   └── manifest.json          # Complete configuration manifest
├── scripts/                    # Execution and analysis scripts
│   ├── compile_athena.sh      # Athena++ compilation
│   ├── run_campaign.py        # Ray execution script (220 CPUs)
│   ├── extract_beading.py     # λ/W extraction from HDF5
│   ├── analyze_lw_direct.py   # LW_DIRECT analysis
│   ├── analyze_perp_timeseries.py  # PERP_TIMESERIES analysis
│   └── analyze_domain_test.py # DOMAIN_TEST analysis
├── outputs/                    # Created during run (not in package)
└── README.md                   # This file
```

---

## Quick Start

### 1. Compile Athena++

```bash
cd /path/to/LAMBDA_W_MEASUREMENT_CAMPAIGN_220VCPU
chmod +x scripts/compile_athena.sh
./scripts/compile_athena.sh
```

**Requirements**:
- Python 3.7+
- HDF5 library
- MPI library
- FFTW library

### 2. Run Simulations

```bash
# Run all campaigns (66 simulations)
python scripts/run_campaign.py --num-workers 220

# Run specific campaign
python scripts/run_campaign.py --campaign LW_DIRECT --num-workers 220

# Resume from previous run
python scripts/run_campaign.py --resume --num-workers 220
```

**Expected Runtime**:
- LW_DIRECT: ~2-3 hours (36 simulations)
- PERP_TIMESERIES: ~1.5-2 hours (27 simulations)
- DOMAIN_TEST: ~0.5-1 hours (3 simulations)
- **Total**: ~4-6 hours on 220 CPUs

### 3. Extract λ/W Measurements

```bash
# Extract beading patterns from HDF5 snapshots
python scripts/extract_beading.py outputs/LW_DIRECT/ --campaign LW_DIRECT
python scripts/extract_beading.py outputs/PERP_TIMESERIES/ --campaign PERP_TIMESERIES
python scripts/extract_beading.py outputs/DOMAIN_TEST/ --campaign DOMAIN_TEST
```

### 4. Analyze Results

```bash
# Analyze each campaign
python scripts/analyze_lw_direct.py
python scripts/analyze_perp_timeseries.py
python scripts/analyze_domain_test.py
```

**Output Files**:
- `*_results.json`: Raw results
- `*_summary.csv`: Statistical summary
- `*_SUMMARY.md`: Executive summary
- `figures/*.pdf`: Publication-quality figures

---

## Campaign Details

### LW_DIRECT: Supercritical λ/W Measurements

**Purpose**: Direct λ/W measurements at f ≥ 1.5 to test calibration extrapolation.

**Parameters**:
- f = 1.5, 2.0, 2.5, 3.0 (4 values)
- β = 0.3, 1.0, 3.0 (3 values)
- θ = 0° (longitudinal field)
- Seeds = 3 (statistical independence)
- Domain = 32λJ (extended for multiple wavelengths)
- Snapshots = 10 (t = 0.5 to 6.0 t_J)

**Total**: 36 simulations

**Success Criteria**:
1. Direct λ/W measurements at f ≥ 1.5 with quantified uncertainties
2. λ/W(f) curve across near-critical to supercritical transition
3. Statistical test of extrapolation validity

**Expected Output**: λ/W vs f curve showing whether λ_frag = 1.11 λ_MJ extrapolation holds.

---

### PERP_TIMESERIES: Perpendicular-Field Time-Series

**Purpose**: Understand why only 27/100 perpendicular-field simulations showed "GOOD" beading.

**Parameters**:
- f = 1.0, 1.5, 2.0 (3 values)
- β = 0.3, 1.0, 3.0 (3 values)
- θ = 90° (perpendicular field)
- Seeds = 3
- Domain = 24λJ (longitudinal for evolution)
- Snapshots = 20 (finer time resolution)

**Total**: 27 simulations

**Success Criteria**:
1. Clear definition of "GOOD" vs "FLAT" vs "RADIAL_COLLAPSE"
2. Time-evolution maps showing when beading appears/disappears
3. Assessment of whether λ/W = 1.25 is representative

**Expected Output**: Time-evolution phase diagram and λ/W representativeness analysis.

---

### DOMAIN_TEST: Domain Size/Resolution Investigation

**Purpose**: Explain FLAT entries in Campaign 8 at (f=1.5, β=0.3, θ=0°).

**Parameters**:
- f = 1.5 (the problematic point)
- β = 0.3 (the problematic β)
- θ = 0° (longitudinal)
- Domain = 12λJ (extended12)
- Resolution = 384×48×48
- Seeds = 3

**Note**: Due to resolution compatibility constraints, only extended12 (12λJ) domain was tested.

**Total**: 3 simulations

**Success Criteria**:
1. Identification of why f=1.5, β=0.3 shows FLAT in Campaign 8
2. Minimum domain/resolution requirements for reliable detection
3. Confirmation that Phase 1 results are robust

**Expected Output**: Domain/resolution requirements and Campaign 8 discrepancy explanation.

---

## Expected Outcomes

### For Concern 5 (Calibration Extrapolation)

**LW_DIRECT will provide**:
- Direct λ/W measurements at f = 1.5, 2.0, 2.5, 3.0
- Quantified uncertainties from seed-to-seed variation
- Statistical test of extrapolation validity
- Either: validation of λ_frag = 1.11 λ_MJ OR revised calibration

**Paper Integration**: Add section "Supercritical Fragmentation: Direct λ/W Measurements"

---

### For Concern 6 (Perpendicular-Field λ/W)

**PERP_TIMESERIES will provide**:
- Clear definition of "GOOD" measurement criteria
- Time-evolution maps of beading vs collapse
- Assessment of λ/W = 1.25 representativeness
- Phase diagram of perpendicular-field fragmentation

**Paper Integration**: Revise Section 4.4 on field geometry with clarified results

---

### For Concern 7 (FLAT Entries)

**DOMAIN_TEST will provide**:
- Explanation of why f=1.5, β=0.3 shows FLAT in Campaign 8
- Domain size and resolution requirements
- Confirmation that Phase 1 results are robust

**Paper Integration**: Add explanatory footnote on Campaign 8 FLAT entries

---

## Troubleshooting

### Compilation Fails

**Problem**: Missing HDF5 or MPI libraries.

**Solution**:
```bash
# Check for HDF5
h5cc --showconfig

# Check for MPI
mpirun --version

# Install missing libraries (macOS)
brew install hdf5 open-mpi

# Install missing libraries (Linux)
sudo apt-get install libhdf5-dev libmpich-dev
```

### Ray Initialization Fails

**Problem**: Ray not installed or port conflict.

**Solution**:
```bash
# Install Ray
pip install ray

# Use different port
ray init(num_cpus=220, dashboard_port=8266)
```

### Simulations Timeout

**Problem**: Timeout too short for extended domains.

**Solution**:
- Edit `generate_configs.py` timeout values
- Or reduce `--num-workers` to allow longer walltime per simulation

### λ/W Extraction Fails

**Problem**: No HDF5 files generated.

**Solution**:
- Check that problem generator outputs HDF5 snapshots
- Verify `snapshots` in config output section
- Check Athena++ compilation with HDF5 support

---

## Verification Checklist

Before submitting to referee:

- [ ] All 81 simulations completed successfully
- [ ] λ/W extracted from all successful simulations
- [ ] All three analysis scripts run without errors
- [ ] Figures generated and checked
- [ ] Summary documents reviewed
- [ ] Results integrated into paper (if approved)

---

## Key Differences from Previous Campaign

1. **Measures λ/W, not t_frag**: Correctly addresses referee's concerns
2. **HDF5 snapshots**: Multiple time outputs for beading pattern extraction
3. **Extended domains**: 16-32λJ to ensure beading develops before collapse
4. **Time-series analysis**: Track beading evolution in perpendicular fields
5. **Domain tests**: Systematic investigation of finite-size effects

---

## Contact & Support

**Campaign Designer**: ASTRA system (Autonomous Scientific Discovery in Astrophysics)
**Date**: 2026-05-01
**Version**: 1.0

**For issues or questions**, refer to:
- Plan document: `/Users/gjw255/.claude/plans/shimmering-gliding-breeze.md`
- Theoretician assessment: `THEORETICIAN_RESULTS_ASSESSMENT.md`

---

## License

This campaign package is part of the ASTRA project for peer review response.
All simulation outputs and analysis results will be made publicly available upon acceptance.
