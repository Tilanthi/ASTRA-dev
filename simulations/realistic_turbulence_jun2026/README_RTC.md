# Realistic Turbulence Campaign (RTC) - Execution Guide

## Overview

This campaign addresses the two critical referee concerns through 1200 simulations at physical turbulence amplitudes (Mturb = 2-4):

1. **Referee Concern #1 - Transient Beading Problem**: Does transient beading survive in realistic turbulent environment? Can density peaks grow to bound cores?

2. **Referee Concern #2 - Turbulence Amplitude Gap**: Does turbulence-independence extend to physical regime (Mturb ~ 2-4)?

## Quick Start

### Step 1: Generate Configurations
```bash
cd /Users/gjw255/astrodata/SWARM/ASTRA-dev-main/simulations/realistic_turbulence_jun2026
python rtc_config_generator.py
```
This generates 1200 Athena++ configuration files in `configs/` directory.

### Step 2: Update Athena++ Binary Path
Edit `rtc_ray_submit.py` line 23:
```python
ATHENA_BINARY = "/path/to/athena++/bin/athena"  # UPDATE THIS PATH
```
Set to your actual Athena++ binary location.

### Step 3: Start Ray Cluster (if not running)
On your cluster head node:
```bash
ray start --head --port=6379
```

### Step 4: Submit Campaign
```bash
python rtc_ray_submit.py
```
This will:
- Submit 1200 simulations to Ray cluster
- Run 6 concurrent simulations (192 vCPUs total)
- Monitor progress automatically
- Save results incrementally to `results/RTC_results_progress.csv`

### Step 5: Monitor Progress
Results are saved incrementally. Check progress with:
```bash
tail -f results/RTC_results_progress.csv
```

### Step 6: Run Analysis (after completion)
```bash
# Analysis 1: Transient peak survival (Referee Concern #1)
python analysis_transient_survival.py

# Analysis 2: Turbulence amplitude dependence (Referee Concern #2)
python analysis_turbulence_dependence.py

# Analysis 3: Perpendicular-field suppression
python analysis_perpendicular_turbulence.py
```

## Expected Resource Requirements

- **Compute**: 1200 simulations × 32 CPUs × 45 min average = 28,800 CPU-hours ≈ 144 hours on 200 vCPUs
- **Storage**: ~120 GB temporary (purged after each sim), ~1 GB final
- **Wall time**: 6-7 days

## Success Criteria

### Minimum Success (addresses Referee Concern #1)
- ≥20% of supercritical simulations show τ_peak ≥ 0.1 tJ at Mturb ≥ 3
- Demonstrates transient peaks can survive long enough to form bound cores

### Moderate Success (addresses Referee Concern #2)
- Clear statistical result: λ/W depends on Mturb (p < 0.05) OR independent (p > 0.05)
- Either outcome provides definitive answer

### Full Success
- Both concerns addressed simultaneously
- Clear physical interpretation of turbulence role

## Output Files

### Simulation Results
- `results/RTC_results_all1200.csv` - Complete results table
- `results/figures/RTC-1_transient_survival_vs_Mturb.pdf` - Transient survival analysis
- `results/figures/RTC-2_lW_vs_Mturb_physical.pdf` - Turbulence dependence analysis
- `results/figures/RTC-3_perpendicular_suppression_vs_Mturb.pdf` - Perpendicular field analysis

## Integration with Paper

After completion, update `filament_spacing_streamlined_mnras.tex`:

1. **If transient peaks survive**: Add Section 4.X "Realistic-Turbulence Validation of THEO-1"
2. **If turbulence-independence breaks**: Reframe Section 4.10 to state independence is linear-regime only
3. **If turbulence overcomes perpendicular suppression**: Add to Section 5.2 discussion

## Troubleshooting

### Ray connection fails
- Ensure Ray cluster is running: `ray status`
- Check firewall allows port 6379
- Verify IP address in `rtc_ray_submit.py` line 16

### Athena++ crashes
- Check `ATHENA_BINARY` path is correct
- Verify MPI is available: `mpirun --version`
- Check output logs in individual simulation directories

### Out of memory
- Reduce concurrency from 6 to 4 simulations
- Increase memory per task in `@ray.remote` decorator

## Contact

For issues or questions, check:
- GitHub: https://github.com/Tilanthi/ASTRA-dev
- Campaign specification: `REALISTIC_TURBULENCE_CAMPAIGN_SPECIFICATION.md`

---

**Created**: 2026-06-30  
**Author**: ASTRA-PA  
**PI**: Glenn J. White (Open University)
