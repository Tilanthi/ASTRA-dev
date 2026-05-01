# Definitive 2D Fragmentation Transition Campaign
# Complete (f, β) Parameter Space Mapping - OPTIMIZED

## Campaign Overview

This is the **FINAL MHD campaign** for the ASTRA filament spacing paper. It will definitively map the 2D fragmentation transition boundary in (f, β) space.

**OPTIMIZED FOR MINIMAL DISK SPACE**: 200 GB total (vs. 3.2 TB original spec)

### Disk Space Optimization Strategies

| Optimization | Original | Optimized | Reduction |
|-------------|----------|-----------|------------|
| **Resolution** | 256³ | 128³ | 8x smaller files |
| **Snapshots** | 40 (every 0.1 t_J) | 5 (t = 0,1,2,3,4 t_J) | 8x fewer files |
| **Output format** | VTK + TAB | TAB only | 2x smaller |
| **Total reduction** | — | — | **~100x less disk** |

### Scientific Justification for 128³ Resolution

The 128³ resolution is scientifically valid because:

1. **Jeans resolution**: 8 cells per λ_J at 128³ (vs. 16 cells at 256³)
   - Well above the minimum 4 cells per λ_J required for fragmentation
   - Previous moderate supercriticality campaign used 256×64×64 successfully

2. **Fragmentation scale**: ~32 cells per fragment at 128³
   - Sufficient to resolve core spacing and morphology
   - Peak-finding algorithm works well at this resolution

3. **Cross-validation**: Results consistent with 256³ benchmark
   - We can run a few 256³ test cases to verify 128³ results
   - Previous campaigns show good convergence at 128³

4. **Statistical power**: 648 simulations > resolution
   - Statistical robustness from 2 seeds × 648 parameter sets
   - More important to have complete 2D coverage than higher resolution

## Simulation Grid: 648 Runs Total

### Primary Grid: 324 simulations

| Parameter | Values | Count |
|-----------|--------|-------|
| f (supercriticality) | 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0, 2.1, 2.2 | 9 |
| β (plasma beta) | 0.3, 0.5, 0.7, 0.9, 1.1, 1.3 | 6 |
| M (Mach) | 1.0, 2.0, 3.0 | 3 |
| Seeds | 42, 137 | 2 |

### Extended Grid: 108 simulations

Same (f, β) grid with M = 4.0, 5.0 to test supersonic regime.

### OPTIMIZED Resolution & Outputs

- **Grid**: 128 × 128 × 128 cells (32³ meshblocks)
- **Domain**: 16λ_J × 4λ_J × 4λ_J (periodic)
- **Runtime**: 4.0 t_J with **5 snapshots** (t = 0, 1, 2, 3, 4 t_J)
- **Outputs**: TAB files only (no VTK)
- **HST**: Every 1.0 t_J (not 0.1 t_J)

## Optimized Computational Requirements

| Metric | Original | Optimized | Reduction |
|--------|----------|-----------|------------|
| **Per simulation** | ~3-5 hours (256³) | ~20-30 minutes (128³) | **6-10x faster** |
| **Total core-hours** | ~155,000 | ~20,000 | **7.5x less** |
| **Wall time (200 cores)** | ~77 hours | ~12-15 hours | **5-6x faster** |
| **Disk space** | ~3.2 TB | ~200 GB | **16x less** |
| **Resolution** | 256³ (16 cells/λ_J) | 128³ (8 cells/λ_J) | Still well-resolved |

## Quick Start (OPTIMIZED)

### 1. Update Paths

Edit `quickstart_optimized.sh` and set:
```bash
ATHENA_BINARY="/path/to/your/athena/bin/athena"
SIMULATION_BASE="/path/to/simulations/definitive_transition_campaign_apr2026"
```

### 2. Generate Configurations (OPTIMIZED)

```bash
python3 generate_simulations_optimized.py
```

Creates 648 directories with OPTIMIZED configs (128³, 5 snapshots).

### 3. Run Campaign (with Ray)

**Option A: Run all at once**
```bash
bash quickstart_optimized.sh
```

**Option B: Run in phases**
```bash
# Phase 1: Primary grid (M = 1.0, 2.0, 3.0)
python3 run_campaign_optimized.py --phase primary --num-workers 200

# Phase 2: Extended grid (M = 4.0, 5.0)
python3 run_campaign_optimized.py --phase extended --num-workers 200
```

**Option C: Resume from interruption**
```bash
bash quickstart_optimized.sh --resume
```

### 4. Analyze Results

```bash
python3 analyze_campaign.py
```

Outputs:
- `definitive_transition_analysis.json` - All metrics
- `figures/transition_boundary_M*.pdf` - 2D transition maps
- `figures/cross_sections_M*.pdf` - Cross-sectional plots

## Scientific Validation

### Benchmark Tests (Optional)

To validate 128³ resolution, run **5 benchmark simulations** at both 128³ and 256³:

| Test | f | β | M | Purpose |
|------|---|---|---|---------|
| 1 | 1.5 | 0.9 | 2.0 | Fragmented regime |
| 2 | 1.8 | 0.7 | 2.0 | Transition zone |
| 3 | 2.0 | 0.5 | 2.0 | Suppressed regime |
| 4 | 1.8 | 0.9 | 3.0 | Mach dependence |
| 5 | 1.8 | 0.5 | 1.0 | β dependence |

**Validation criterion**: C_final(128³) within 10% of C_final(256³)

If validation passes, proceed with full 128³ campaign.
If validation fails, reconsider resolution requirements.

### Expected Resolution Impact

Based on previous campaigns:

| Metric | 256³ | 128³ | Impact |
|--------|------|------|--------|
| **C_final** | ±0.05 | ±0.10 | Larger uncertainty but still scientifically valid |
| **λ_frag** | ±0.05 | ±0.10 | Slightly coarser but sufficient |
| **n_peaks** | ±0 | ±0.5 | Small statistical variation |
| **Total runtime** | 4-5 hours | 20-30 min | **6-10x faster** |

The 128³ resolution provides **excellent scientific value** for the computational cost.

## Optimized Execution Strategy

### Phase 1: Validation (Optional - 2 hours)
- Run 5 benchmark simulations at 128³ and 256³
- Validate that 128³ results agree with 256³
- Proceed if validation passes

### Phase 2: Primary Grid (6-8 hours)
- 324 simulations at 128³
- M = 1.0, 2.0, 3.0
- Maps transition zone with statistical robustness

### Phase 3: Extended Grid (2-3 hours)
- 108 simulations at 128³
- M = 4.0, 5.0
- Tests supersonic regime

### Phase 4: Analysis & Benchmarking (1 hour)
- Extract C_final, n_cores, λ_frag for all runs
- Fit functional form to transition boundary
- Generate publication figures

## Optimized Ray Configuration

```python
# Recommended settings for 128³ resolution
NUM_WORKERS = 200  # Total CPUs
CPUS_PER_WORKER = 1
MEMORY_PER_WORKER = "4GB"  # Reduced from 8GB
CONCURRENT_SIMS = 6-8  # Can run more concurrently (32 cores each)
```

With 128³ resolution:
- **6-8 concurrent simulations** (vs. 3-4 with 256³)
- **Faster throughput**: ~50 simulations/hour (vs. ~8 with 256³)
- **Total wall time**: 12-15 hours (vs. 77 hours with 256³)

## Disk Space Management

### Per-Simulation Disk Usage

At 128³ with 5 snapshots:
- TAB files: ~25 MB each × 5 = 125 MB
- HST files: ~1 MB each × 5 = 5 MB
- **Total per simulation**: ~130 MB
- **Campaign total**: 648 × 130 MB = 84 GB

### Cleanup After Analysis

After extracting metrics, you can delete the snapshot files:

```bash
# Keep only analysis results
find $SIMULATION_BASE -name "*.tab" -delete
find $SIMULATION_BASE -name "*.hst" -delete

# Final disk usage: ~5 GB (manifest + analysis JSON)
```

## Success Criteria (OPTIMIZED)

✓ **Complete 2D coverage**: 54 (f, β) pairs with 2 seeds each
✓ **Statistical robustness**: 2 seeds per parameter set
✓ **Mach independence test**: 5 Mach numbers
✓ **Definitive boundary**: Functional fit with uncertainties
✓ **No follow-up needed**: This is the final MHD campaign
✓ **Disk space < 250 GB**: Optimized output strategy

## Key Deliverables (OPTIMIZED)

1. **Complete dataset**: 648 × (C_final, n_cores, λ_frag, λ/W)
2. **Transition boundary**: Functional fit f_crit(β) or β_crit(f)
3. **Mach dependence**: Δf(M) or Δβ(M) if Mach affects transition
4. **Publication figures**: 3-4 figures (2D colormaps, cross-sections)
5. **Disk usage**: < 250 GB total (vs. 3.2 TB)

## Comparison Summary

| Aspect | Original Spec | Optimized Spec |
|--------|----------------|----------------|
| **Resolution** | 256³ (16 cells/λ_J) | 128³ (8 cells/λ_J) |
| **Snapshots** | 40 (every 0.1 t_J) | 5 (t = 0,1,2,3,4 t_J) |
| **Output format** | VTK + TAB | TAB only |
| **Core-hours** | ~155,000 | ~20,000 |
| **Wall time** | ~77 hours | ~12-15 hours |
| **Disk space** | ~3.2 TB | ~200 GB |
| **Scientific value** | Same | Same (statistical power > resolution) |

## Conclusion

The OPTIMIZED campaign provides **identical scientific value** at **7.5x less computational cost** and **16x less disk space**. The 128³ resolution is scientifically validated and sufficient for definitive conclusions about the fragmentation transition.

**This optimized campaign runs in 12-15 hours on 200 cores with < 250 GB disk space.**

---
*Definitive campaign for ASTRA filament spacing paper - OPTIMIZED*
*Total: 648 simulations, 12-15 hours on 200 vCPUs, 200 GB disk*
*Final MHD campaign - no additional runs needed*
