# Targeted Supercritical Beading Test: f=1.5 Extended Domain Campaign

## Purpose

This campaign addresses the fundamental supercritical extrapolation gap identified in the peer review. All 654 existing supercritical simulations (f ≥ 1.5) show pure radial collapse with no longitudinal beading, preventing direct λ/W measurement in the HGBS parameter space (f ≈ 1.5-3.0). 

This targeted test uses an **extended simulation domain** (24λ_J vs standard 8λ_J) to allow more time for longitudinal beading to develop before radial collapse dominates at the low-supercritical boundary (f = 1.5).

## Hypothesis

If the failure to observe longitudinal beading at f ≥ 1.5 is due to insufficient domain length rather than fundamental physics, then extending the domain from 8λ_J to 24λ_J should allow beading patterns to develop before radial collapse terminates the simulation.

If the extended domain STILL shows pure radial collapse, this confirms that f = 1.5 represents a genuine regime transition where radial collapse dominates over longitudinal fragmentation.

## Configuration

### Domain Specifications

```python
Domain Size:
  L_x = 24 λ_J  # Extended longitudinal domain (3× standard)
  L_y = 1 λ_J
  L_z = 1 λ_J
  
Resolution:
  N_x = 1536
  N_y = 64
  N_z = 64
  
  # dx = 24 λ_J / 1536 = 0.0156 λ_J
  # dy = 1 λ_J / 64 = 0.0156 λ_J
  # dz = 1 λ_J / 64 = 0.0156 λ_J
  # Uniform grid: dx = dy = dz
```

**Rationale**: The 3× longer domain allows up to 8 fragmentation wavelengths to develop (assuming λ ~ 3λ_J for near-critical filaments), compared to only 2-3 wavelengths in the standard 8λ_J domain.

### Parameter Point

```python
# Single parameter point at low-supercritical boundary
f = 1.5                    # Line-mass fraction (1.5× critical)
β = 1.0                    # Intermediate plasma β (fiducial)
θ = 0°                     # Longitudinal magnetic field
M = 1.0                    # Fiducial turbulent Mach number

# Reasoning for parameter choice:
# - f = 1.5: The lowest supercritical value where HGBS filaments nominally exist
# - β = 1.0: Intermediate field strength, representative of typical conditions
# - θ = 0°: Longitudinal field geometry (most conservative for beading detection)
# - M = 1.0: Fiducial turbulence, not so high as to suppress beading
```

### Random Seeds

```python
seeds = [42, 137, 251, 367, 499]  # 5 seeds for statistical assessment
```

**Total simulations**: 5

### Physics Configuration

```python
# Equation of State
eos: isothermal

# Boundary Conditions
boundary_x: periodic
boundary_y: periodic
boundary_z: periodic

# Magnetic Field Configuration
field_geometry: longitudinal  # B || filament axis
B0_direction: x_axis

# Initial Conditions
# King profile filament + turbulent velocity perturbations
# Same as BRIDGE and DTC campaigns for consistency

# Sink Particles
sink_particles: enabled
sink_formation_thresh: 10^4 × ρ_0  # Standard threshold
sink_merge_radius: 0.02 λ_J
```

### Runtime Parameters

```python
# Maximum simulation time
t_max: 2.0 t_J  # 2 Jeans times (extended from standard 1.5 t_J)

# Output cadence
output_interval: 0.1 t_J  # Output every 0.1 t_J
  # Expected outputs: 20 snapshots per simulation
  # Total outputs across 5 sims: 100 snapshots

# Checkpointing
checkpoint_interval: 0.05 t_J
checkpoint_dir: ./checkpoints/

# Wall-clock timeout
timeout: 21600 seconds  # 6 hours per simulation
```

### Resource Estimates

```python
# Per-simulation requirements
cores: 16 MPI ranks
ram: ~4-8 GB
disk: ~5 GB per simulation (100 snapshots × 50 MB each)
wall_time: 4-6 hours

# Total campaign requirements
total_simulations: 5
total_cpu_hours: ~100-150 hours
total_disk: ~25 GB
elapsed_time: ~24-30 hours (if 2 simulations run concurrently)
```

## Success Criteria

### Primary Criteria

1. **Beading Detection**: Does the extended domain show longitudinal beading (density peaks with amplitude > 0.15 above background)?

2. **λ/W Measurement**: If beading is detected, can we measure λ/W?
   - Success: λ/W measured with quantified uncertainty
   - Failure: No beading, or beading amplitude too weak for measurement

3. **Regime Classification**:
   - Category A: BEADING - Clear longitudinal peaks, λ/W measurable
   - Category B: TRANSITIONAL - Weak beading, marginal detection
   - Category C: RADIAL_COLLAPSE - Pure radial collapse, no longitudinal structure

### Secondary Analysis

For simulations showing beading:
1. **Fragmentation wavelength**: Measure λ/W using peak detection
2. **Beading development time**: Track when beading first appears
3. **Comparison with near-critical**: Does λ/W at f=1.5 differ from f=1.0-1.2 results?

For simulations showing radial collapse:
1. **Collapse timescale**: Measure t_radial_collapse vs t_beading_development
2. **Density contrast**: Track central density evolution
3. **Confirmation**: Verify that failure to observe beading is not due to insufficient domain length

## Analysis Pipeline

### Automated Classification Script

```python
#!/usr/bin/env python3
"""
classify_extended_domain_results.py

Classifies extended domain simulation results into BEADING/TRANSITIONAL/RADIAL_COLLAPSE
and extracts λ/W where applicable.
"""

import h5py
import numpy as np
from pathlib import Path

def classify_simulation(snapshot_dir):
    """
    Classify simulation based on final snapshot analysis.
    
    Parameters
    ----------
    snapshot_dir : str
        Path to simulation output directory
    
    Returns
    -------
    classification : dict
        {
            'category': 'BEADING' | 'TRANSITIONAL' | 'RADIAL_COLLAPSE',
            'lambda_W': float or None,
            'beading_amplitude': float,
            'peak_count': int,
            't_beading': float or None
        }
    """
    # Load final snapshot
    final_snapshot = find_final_snapshot(snapshot_dir)
    
    # Extract longitudinal density profile
    profile = extract_longitudinal_profile(final_snapshot)
    
    # Peak detection
    peaks = detect_peaks(profile, min_amplitude=0.05)
    peak_amplitudes = peaks['amplitudes']
    
    # Classification logic
    if len(peak_amplitudes) == 0:
        return {
            'category': 'RADIAL_COLLAPSE',
            'lambda_W': None,
            'beading_amplitude': 0.0,
            'peak_count': 0,
            't_beading': None
        }
    
    max_amplitude = np.max(peak_amplitudes)
    
    if max_amplitude > 0.15:
        # Strong beading
        wavelength_pc = estimate_wavelength(peaks)
        lambda_W = wavelength_pc / 0.10  # Assuming W = 0.1 pc
        
        return {
            'category': 'BEADING',
            'lambda_W': lambda_W,
            'beading_amplitude': max_amplitude,
            'peak_count': len(peaks),
            't_beading': estimate_beading_time(snapshot_dir)
        }
    
    elif 0.05 < max_amplitude <= 0.15:
        # Weak/transitional beading
        wavelength_pc = estimate_wavelength(peaks) if len(peaks) >= 2 else None
        lambda_W = wavelength_pc / 0.10 if wavelength_pc else None
        
        return {
            'category': 'TRANSITIONAL',
            'lambda_W': lambda_W,
            'beading_amplitude': max_amplitude,
            'peak_count': len(peaks),
            't_beading': estimate_beading_time(snapshot_dir)
        }
    
    else:
        return {
            'category': 'RADIAL_COLLAPSE',
            'lambda_W': None,
            'beading_amplitude': max_amplitude,
            'peak_count': len(peaks),
            't_beading': None
        }
```

### Output Products

1. **Classification summary**: JSON file with category for each simulation
2. **λ/W measurements**: CSV with measured values (where applicable)
3. **Visualization figures**:
   - Longitudinal density profiles (final snapshot)
   - Peak evolution over time
   - Comparison with near-critical results

## Integration with Paper

### If BEADING is detected:

**Add new section** to paper:

```latex
\subsection{Supercritical Fragmentation Wavelength: Direct Measurements}

We performed a targeted test of whether longitudinal beading can develop 
in supercritical filaments using an extended simulation domain. For f = 1.5 
(the lowest supercritical value in the HGBS range), we used a 24λ_J domain 
(3× longer than standard) to allow more time for beading to develop before 
radial collapse dominates. 

\textbf{Results}: [X] of [Y] simulations showed clear longitudinal beading 
with measured λ/W = [VALUE] ± [UNCERTAINTY]. This provides the first direct 
measurement of the fragmentation wavelength in the supercritical regime...
```

**Update Figure 11** (supercritical extrapolation) to include the new measurement at f=1.5.

### If RADIAL_COLLAPSE persists:

**Add clarification** to paper:

```latex
\textbf{Targeted extended-domain test}: To test whether the failure to observe 
beading at f ≥ 1.5 reflects insufficient domain length rather than fundamental 
physics, we performed simulations with 3× extended domains (24λ J vs standard 
8λ J) at f = 1.5. All [N] extended-domain simulations showed pure radial collapse 
with no longitudinal beading, confirming that the regime transition at f ≈ 1.5 
is genuine: supercritical filaments undergo radial collapse faster than 
longitudinal beading can develop. This result reinforces that theoretical 
predictions for HGBS filaments must rely on extrapolation from near-critical 
simulations (f = 1.0--1.2), with unknown systematic error at f ≥ 1.5.
```

## Risk Mitigation

### Risk 1: Insufficient beading development time
**Mitigation**: Extended 24λ J domain provides 3× more wavelengths and ~2× more development time. If beading still doesn't appear, this strongly confirms the radial-collapse-dominates interpretation.

### Risk 2: Excessive computational cost
**Mitigation**: Only 5 simulations at single parameter point. Total cost ~100-150 CPU-hours, manageable on typical clusters.

### Risk 3: Inconclusive results (mixed beading/collapse)
**Mitigation**: Time-series analysis will track when beading appears vs. when collapse dominates. Even if both occur, we can quantify the relative timescales.

### Risk 4: CFL limit due to radial collapse
**Mitigation**: Monitoring code will detect CFL timestep < 10^-8 t_J (runaway collapse criterion). If triggered early, we document that collapse dominated before beading could develop.

## Deliverables

1. **Simulation outputs**: All HDF5 snapshots, checkpoint files, status JSONs
2. **Classification results**: JSON with category assignments for all 5 simulations
3. **Analysis plots**: PDF figures showing longitudinal profiles and beading detection
4. **Paper integration**: LaTeX section for insertion into manuscript
5. **Summary report**: Markdown document with interpretation and recommendations

## Timeline

1. **Config generation**: 1 day (using modified BRIDGE generator)
2. **Simulation execution**: 1-2 days (24-30 hours wall time)
3. **Analysis**: 4 hours
4. **Paper integration**: 2 hours

**Total**: 3-4 days from start to paper-ready results

## Comparison with Existing Campaigns

This campaign is **much smaller** than previous efforts:
- DTC campaign: 540 simulations
- BRIDGE campaign: 200 simulations  
- Supercritical campaign: 654 simulations
- **This campaign**: 5 simulations

The focused scope (single parameter point, extended domain) allows us to address the most critical extrapolation gap (f = 1.0 → 1.5 transition) with minimal computational cost.

---

**Status**: Ready for deployment upon user approval
**Date**: 2026-05-03
**Priority**: HIGH (addresses primary theoretical limitation identified in peer review)
