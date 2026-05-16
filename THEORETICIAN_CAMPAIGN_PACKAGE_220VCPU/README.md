# THEORETICIAN_CAMPAIGN_PACKAGE_220VCPU

**Purpose**: Address major concerns from theoretician peer reviewer about MHD simulation campaign

**Created**: 2026-05-01
**Total simulations**: 225 (75 STV + 60 PFS + 90 NCRI)
**Estimated wall time**: ~4 days on 220 vCPU cluster

---

## The Three Major Concerns Addressed

### Concern 5: Calibration Extrapolation
> "The calibration λ_frag = 1.11 λ_MJ is derived outside the physically relevant regime. The paper explicitly states that this calibration comes from near-critical simulations (f ≈ 1.0–1.2) and is then extrapolated to the supercritical regime (f ≈ 1.5–3.0) where HGBS filaments are observed."

**STV Campaign**: Direct λ/W measurements at f = 1.5, 1.8, 2.0, 2.5, 3.0 with 5 seeds each for statistical validation.

---

### Concern 6: Perpendicular-Field Reliability
> "The λ/W = 1.25 for perpendicular fields is of uncertain reliability. Campaign 6 reports that only 27 'GOOD' measurements of axial fragmentation were obtained from 100 simulations of perpendicular-field filaments... If perpendicular-field filaments primarily undergo radial collapse, then the 27 cases showing λ/W ≈ 1.25 may represent a minority regime."

**PFS Campaign**: Systematic investigation of perpendicular-field fragmentation with time-series analysis to understand when and why beading occurs.

---

### Concern 7: FLAT Entries in Campaign 8
> "The Campaign 8 λ/W Calibration Matrix (Figure 18) contains multiple FLAT entries that are not discussed. At θ = 0°, β = 0.3, the result is FLAT despite the paper repeatedly stating that longitudinal near-critical filaments show robust axial beading (100% fragmentation in Phase 1)."

**NCRI Campaign**: Domain size and resolution investigation to explain FLAT entries and confirm Phase 1 results.

---

## Quick Start

```bash
# 1. Extract package
tar -xzf THEORETICIAN_CAMPAIGN_PACKAGE_220VCPU.tar.gz
cd THEORETICIAN_CAMPAIGN_PACKAGE_220VCPU

# 2. Compile Athena++
bash compile_athena.sh

# 3. Install dependencies
pip3 install ray h5py numpy scipy pandas matplotlib

# 4. Run campaign
python3 run_campaign.py

# 5. Monitor progress (in another terminal)
python3 monitor_progress.py

# 6. Analyze results (after completion)
python3 analyze_stv.py
python3 analyze_pfs.py
python3 analyze_ncri.py
python3 analyze_integrated.py
```

---

## Computational Requirements

### Hardware
- **CPUs**: 220 vCPU (AMD EPYC or similar)
- **RAM**: ~400 GB total
- **Disk**: ~500 GB for outputs

### Ray Configuration
```python
ray.init(num_cpus=220)
max_concurrent = 12  # 12 simulations × 16 cores = 192 cores
cores_per_sim = 16
```

### Per-Simulation Resources
- **Cores**: 16 MPI ranks
- **RAM**: 2-4 GB
- **Wall time**: 1-3 hours (depending on domain size)
- **Disk**: 1-2 GB

---

## Campaign Specifications

### STV (Supercritical Transition Validation)
- **Purpose**: Direct λ/W measurements in supercritical regime
- **Parameters**: f = [1.5, 1.8, 2.0, 2.5, 3.0], β = [0.3, 1.0, 3.0], θ = 0°, 5 seeds
- **Domain**: L = 24λJ (extended to capture beading before collapse)
- **Resolution**: 768 × 64 × 64
- **Simulations**: 75

### PFS (Perpendicular-Field Systematics)
- **Purpose**: Understand why only 27/100 perpendicular sims show "GOOD" beading
- **Parameters**: f = [1.0, 1.2, 1.5, 2.0], β = [0.3, 1.0, 3.0], θ = 90°, 5 seeds
- **Domain**: L = 16λJ (longitudinal for time evolution)
- **Resolution**: 512 × 64 × 64
- **Special**: Time-series outputs (every 0.1 tJ) for evolution analysis
- **Simulations**: 60

### NCRI (Near-Critical Resolution Investigation)
- **Purpose**: Resolve FLAT entries in Campaign 8
- **Parameters**: f = [1.0, 1.2, 1.3, 1.4, 1.5], β = 0.3, θ = 0°, 3 seeds
- **Domains**: Standard (8λJ), Bridge (12λJ), Long (16λJ)
- **Resolutions**: 128³, 256³, 512×64×64
- **Simulations**: 90

---

## Expected Outputs

### After Simulation
1. **outputs/STV/**: 75 simulation directories with HDF5, HST, status files
2. **outputs/PFS/**: 60 simulation directories with time-series outputs
3. **outputs/NCRI/**: 90 simulation directories across domain/res combinations

### After Analysis
1. **STV_SUMMARY.md**: Direct λ/W measurements, extrapolation test
2. **PFS_SUMMARY.md**: Perpendicular-field phase diagram, classification criteria
3. **NCRI_SUMMARY.md**: Domain/resolution requirements, FLAT entry explanation
4. **INTEGRATED_ANALYSIS.md**: Cross-campaign synthesis
5. **figures/**: Publication-ready PDF figures
6. **data/**: CSV files with all measurements

---

## File Structure

```
THEORETICIAN_CAMPAIGN_PACKAGE_220VCPU/
├── README.md                    # This file
├── MANIFEST.md                  # Package manifest
├── run_campaign.py              # Main Ray execution script
├── monitor_progress.py          # Progress monitoring
├── compile_athena.sh            # Athena++ compilation
├── generate_configs.py          # Config generation (already run)
├── analyze_stv.py               # STV analysis
├── analyze_pfs.py               # PFS analysis
├── analyze_ncri.py              # NCRI analysis
├── analyze_integrated.py        # Integrated analysis
├── configs/                     # All 225 config files
│   ├── STV/                     # 75 configs
│   ├── PFS/                     # 60 configs
│   └── NCRI/                    # 90 configs
├── analysis_utils/
│   ├── extract_beading.py       # Peak detection
│   ├── time_series_analysis.py  # Time evolution (PFS)
│   ├── classification.py        # GOOD/FLAT criteria
│   └── statistical_tests.py     # χ², bootstrap, Bayesian
└── outputs/                     # Created during run
    ├── STV/
    ├── PFS/
    └── NCRI/
```

---

## Scientific Background

### Why These Campaigns Matter

**For HGBS Comparison**: The observed filament-constrained spacing is λ/W = 2.05 ± 0.05. This value is compared against MHD simulation predictions to infer physics. The reliability of those simulation predictions directly affects our conclusions.

**The Core Issue**: Most HGBS filaments are supercritical (f > 1.5), but our λ/W measurements come from near-critical simulations (f ≈ 1.0-1.2). The 1.11× calibration factor is extrapolated, not measured.

**What These Campaigns Will Deliver**:
1. Direct measurements at supercritical f values
2. Assessment of whether perpendicular-field λ/W = 1.25 is robust
3. Resolution for Campaign 8 discrepancies
4. Minimum requirements for reliable λ/W measurements

---

## Integration with Paper

### New Sections to Add
1. **"Supercritical Fragmentation: Direct Measurements"** - STV results
2. **"Perpendicular-Field Fragmentation: Time Evolution"** - PFS results
3. **"Minimum Requirements for λ/W Measurements"** - NCRI results

### Figures to Generate
1. λ/W vs f curve with direct measurements (STV)
2. Perpendicular-field phase diagram (PFS)
3. Domain/resolution convergence plot (NCRI)
4. Integrated comparison with HGBS observations

### Response to Referee
After campaign completion, we can respond:
> "To address the theoretician's concerns, we performed 225 new MHD simulations in three targeted campaigns. The STV campaign provides direct λ/W measurements at f = 1.5-3.0, finding [result]. The PFS campaign explains the perpendicular-field fragmentation behavior, showing [result]. The NCRI campaign resolves the Campaign 8 discrepancies, identifying [explanation]."

---

## Timeline

1. **Setup**: 2 hours (already done - configs generated)
2. **Transfer to cluster**: 1 hour
3. **Athena++ compilation**: 1 hour
4. **Simulation execution**: ~90 hours (4 days)
5. **Analysis**: 4 hours
6. **Paper integration**: 4 hours

**Total**: ~5 days from start to paper-ready results

---

## Troubleshooting

### Issue: Ray won't start
```bash
# Stop existing Ray
ray stop

# Clean start
ray start --head --num-cpus=220 --port=6379
```

### Issue: Out of memory
```bash
# Reduce concurrent jobs in run_campaign.py
# Change max_concurrent from 12 to 8
```

### Issue: Simulations failing
```bash
# Check individual logs
cat outputs/STV/*/sim.log

# Common fixes:
# - Increase timeout in config files
# - Reduce resolution for problematic (f, β) combinations
```

---

## Validation

### Pre-Run Checklist
- [ ] Configs generated: 225 total (75 STV + 60 PFS + 90 NCRI)
- [ ] Athena++ executable exists
- [ ] Ray can initialize with 220 CPUs
- [ ] Disk space > 500 GB available

### Post-Run Verification
```bash
# Check completion
python3 -c "
import json, glob
results = []
for f in glob.glob('outputs/*/status.json'):
    with open(f) as fp:
        results.append(json.load(fp))
print(f'Total: {len(results)}')
for status in ['FRAG', 'STABLE', 'TIMEOUT', 'ERROR']:
    count = sum(1 for r in results if r.get('status') == status)
    print(f'{status}: {count}')
"
```

---

## Contact and Support

**Package created**: 2026-05-01
**Campaign**: Theoretician Peer Review Response
**Total simulations**: 225
**Estimated completion**: ~4 days on 220 vCPU

For questions, refer to:
- Main simulation plan: `/Users/gjw255/.claude/plans/shimmering-gliding-breeze.md`
- Athena++ documentation: https://princetonuniversity.github.io/athena-public-version/
- Ray documentation: https://docs.ray.io/

---

**END OF README**
