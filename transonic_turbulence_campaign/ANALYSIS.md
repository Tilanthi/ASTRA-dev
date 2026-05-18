# Analysis Procedures for Transonic Turbulence Campaign

## Overview

This document describes the analysis pipeline for extracting scientifically meaningful results from the transonic turbulence simulation campaign.

## Analysis Pipeline

### 1. Turbulence Characterization

#### 1.1 Mach Number Evolution
```python
# analyze_turbulence.py
import h5py
import numpy as np
import matplotlib.pyplot as plt

def compute_mach_number(h5_file):
    """
    Compute turbulent Mach number evolution from simulation outputs.
    
    Parameters
    ----------
    h5_file : str
        Path to HDF5 output file
    
    Returns
    -------
    t : array
        Time in units of t_J
    M_turb : array
        Turbulent Mach number
    """
    results = []
    
    with h5py.File(h5_file, 'r') as f:
        # Assume file has structure: /Level0/Step#/prim/vel
        n_steps = len(f['Level0'])
        
        for step_idx in range(0, n_steps, 10):  # Every 10th step
            try:
                grp = f[f'Level0/Step{step_idx:05d}/prim']
                
                # Get velocity field
                vel = grp['vel'][()]
                shape = vel.shape  # Expect (nx, ny, nz, 3)
                
                # Calculate rms velocity (mass-weighted)
                rho = grp['rho'][()]
                vel_rms = np.sqrt(np.mean(rho * vel**2) / np.mean(rho))
                
                # Normalize by sound speed (cs = 1 in normalized units)
                M_turb = vel_rms / 1.0
                time = grp.attrs.get('Time', 0.0)
                
                results.append((time, M_turb))
                
            except KeyError:
                continue
    
    results = np.array(results)
    t = results[:, 0]
    M_turb = results[:, 1]
    
    return t, M_turb

def plot_mach_evolution(t, M_turb, output_file='mach_evolution.pdf'):
    """Plot Mach number evolution."""
    plt.figure(figsize=(10, 6))
    plt.plot(t, M_turb, 'b-', linewidth=2)
    plt.axhline(y=1.0, color='r', linestyle='--', label='Transonic threshold')
    plt.xlabel('Time (t_J)')
    plt.ylabel('Turbulent Mach Number')
    plt.title('Turbulence Maintenance Check')
    plt.legend()
    plt.grid(True)
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"Mean M_turb: {np.mean(M_turb):.3f}")
    print(f"Min M_turb: {np.min(M_turb):.3f}")
    print(f"Max M_turb: {np.max(M_turb):.3f}")
```

#### 1.2 Power Spectrum Analysis
```python
def compute_velocity_spectrum(h5_file, time_snapshot=-1):
    """
    Compute velocity power spectrum to check turbulent cascade.
    
    Parameters
    ----------
    h5_file : str
        Path to HDF5 output file
    time_snapshot : int
        Which time snapshot to analyze (-1 for last)
    """
    with h5py.File(h5_file, 'r') as f:
        # Get velocity field
        if time_snapshot == -1:
            # Find last snapshot
            n_steps = len(f['Level0'])
            time_snapshot = n_steps - 1
        
        grp = f[f'Level0/Step{time_snapshot:05d}/prim']
        vel = grp['vel'][()]
        
        # Compute FFT along x-direction (filament axis)
        vel_x = vel[:, :, :, 0]
        
        # Average over transverse directions
        vel_x_mean = np.mean(vel_x, axis=(1, 2))
        
        # Compute power spectrum
        E_k = np.abs(np.fft.fft(vel_x_mean))**2
        k = np.fft.fftfreq(len(vel_x_mean))
        
        # Plot log-log
        plt.figure(figsize=(10, 6))
        plt.loglog(k[1:], E_k[1:], 'o-')
        plt.xlabel('Wavenumber k (λ_J⁻¹)')
        plt.ylabel('Power Spectral Density E(k)')
        plt.title('Velocity Power Spectrum')
        plt.grid(True, which='both', alpha=0.5)
        plt.savefig('velocity_spectrum.pdf', dpi=300, bbox_inches='tight')
        plt.close()
        
        return k, E_k
```

### 2. Fragmentation Spacing Measurement

#### 2.1 Core Detection
```python
from scipy.signal import find_peaks
from scipy.ndimage import gaussian_filter1d

def detect_cores(h5_file, threshold=3.0):
    """
    Detect dense cores in filament from density field.
    
    Parameters
    ----------
    h5_file : str
        Path to HDF5 output file
    threshold : float
        Detection threshold in units of background density
    """
    with h5py.File(h5_file, 'r') as f:
        # Get last snapshot (fully fragmented)
        rho = f['Level0'][-1]['prim']['rho'][()]
        
        # Extract midplane density (y-z plane at filament center)
        rho_midplane = rho[rho.shape[0]//2, :, :]
        
        # Average over y-direction (transverse to filament)
        rho_1d = np.mean(rho_midplane, axis=0)
        
        # Smooth slightly to reduce noise
        rho_smooth = gaussian_filter1d(rho_1d, sigma=2)
        
        # Find peaks
        peaks, properties = find_peaks(rho_smooth, height=threshold, distance=10)
        
        return peaks, properties

def extract_lambda_W(peaks, dx, W_core=0.3):
    """
    Extract fragmentation spacing from detected peaks.
    
    Parameters
    ----------
    peaks : array
        Peak positions (in grid units)
    dx : float
        Grid spacing (in λ_J units)
    W_core : float
        Filament core half-width (0.3 λ_J)
    
    Returns
    -------
    lambda_W : float
        Mean spacing normalized to core width
    lambda_W_std : float
        Standard deviation of spacing
    """
    if len(peaks) < 2:
        return np.nan, np.nan
    
    # Convert to physical units
    peak_positions = peaks * dx
    
    # Compute spacing between adjacent peaks
    spacings = np.diff(peak_positions)
    
    # Normalize to core width
    W_core_phys = W_core  # In λ_J units (0.3)
    lambda_W_values = spacings / W_core_phys
    
    # Return mean and std
    return np.mean(lambda_W_values), np.std(lambda_W_values)
```

#### 2.2 Fragmentation Classification
```python
def classify_fragmentation(h5_file):
    """
    Classify fragmentation outcome: BEADING vs RADIAL_COLLAPSE vs MIXED.
    
    Returns
    -------
    outcome : str
        'BEADING', 'RADIAL_COLLAPSE', or 'MIXED'
    confidence : float
        Confidence in classification (0-1)
    """
    with h5py.File(h5_file, 'r') as f:
        rho = f['Level0'][-1]['prim']['rho'][()]
        
        # Check for axial density variations
        rho_axis = rho[rho.shape[0]//2, :, rho.shape[2]//2]
        
        # Compute variance along axis
        var_axis = np.var(rho_axis)
        var_total = np.var(rho)
        
        # Beading criterion: significant axial variation
        beading_strength = var_axis / var_total
        
        if beading_strength > 0.1:
            return 'BEADING', beading_strength
        else:
            return 'RADIAL_COLLAPSE', 1.0 - beading_strength
```

### 3. Timescale Analysis

#### 3.1 Fragmentation Time
```python
def find_fragmentation_time(h5_file):
    """
    Determine when fragmentation occurred.
    
    Algorithm:
    1. Monitor axial density variance over time
    2. Fragmentation time: when variance exceeds threshold
    """
    variances = []
    times = []
    
    with h5py.File(h5_file, 'r') as f:
        n_steps = len(f['Level0'])
        
        for step_idx in range(0, n_steps, 5):  # Check every 5 steps
            try:
                grp = f[f'Level0/Step{step_idx:05d}/prim']
                rho = grp['rho'][()]
                
                # Axial density variance
                rho_axis = rho[rho.shape[0]//2, :, rho.shape[2]//2]
                var = np.var(rho_axis)
                
                variances.append(var)
                times.append(grp.attrs.get('Time', 0.0))
                
            except KeyError:
                continue
    
    variances = np.array(variances)
    times = np.array(times)
    
    # Find when variance exceeds threshold
    threshold = 0.1  # 10% background variation
    frag_indices = np.where(variances > threshold)[0]
    
    if len(frag_indices) > 0:
        return times[frag_indices[0]]
    else:
        return np.nan  # Never fragmented
```

### 4. Comparison with HGBS

#### 4.1 Projection Effects
```python
def apply_projection_correction(lambda_W_3d, inclination_deg):
    """
    Convert 3D spacing to 2D projected spacing.
    
    From Hacar et al. (2013): correction factor = 1/cos(inclination)
    """
    inclination_rad = np.radians(inclination_deg)
    correction = 1.0 / np.cos(inclination_rad)
    
    # For random orientation:
    # Mean correction ≈ 1.27 for isotropic orientations
    
    lambda_W_2d = lambda_W_3d / correction
    return lambda_W_2d
```

#### 4.2 HGBS Comparison Plot
```python
def plot_hgbs_comparison(results_df, output_file='hgbs_comparison.pdf'):
    """
    Plot simulation results vs HGBS observations.
    
    Parameters
    ----------
    results_df : DataFrame
        Columns: [f, beta, theta, M_drive, lambda_W, outcome]
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Plot 1: λ/W vs M_driver for longitudinal fields
    subset_long = results_df[results_df['theta'] == 0]
    for beta_val in [0.5, 1.0, 2.0]:
        beta_subset = subset_long[subset_long['beta'] == beta_val]
        axes[0,0].plot(beta_subset['M_drive'], beta_subset['lambda_W'], 
                        'o-', label=f'β={beta_val}')
    axes[0,0].axhline(y=2.79, color='k', linestyle='--', 
                       label='HGBS PM')
    axes[0,0].set_xlabel('Driving Mach Number')
    axes[0,0].set_ylabel('λ/W')
    axes[0,0].set_title('Longitudinal Field')
    axes[0,0].legend()
    axes[0,0].grid(True)
    
    # Plot 2: λ/W vs M_driver for perpendicular fields
    subset_perp = results_df[results_df['theta'] == 90]
    for beta_val in [0.5, 1.0, 2.0]:
        beta_subset = subset_perp[subset_perp['beta'] == beta_val]
        axes[0,1].plot(beta_subset['M_drive'], beta_subset['lambda_W'], 
                        's-', label=f'β={beta_val}')
    axes[0,1].axhline(y=2.79, color='k', linestyle='--', 
                       label='HGBS PM')
    axes[0,1].set_xlabel('Driving Mach Number')
    axes[0,1].set_ylabel('λ/W')
    axes[0,1].set_title('Perpendicular Field')
    axes[0,1].legend()
    axes[0,1].grid(True)
    
    # Plot 3: Outcome phase diagram
    # ... (add outcome classification visualization)
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    plt.close()
```

## Campaign-Wide Analysis

### Master Analysis Script
```python
# analyze_campaign.py
import pandas as pd
import os
import glob

def analyze_full_campaign(results_dir):
    """
    Analyze all 108 simulations in the campaign.
    
    Parameters
    ----------
    results_dir : str
        Directory containing all simulation outputs
    """
    results = []
    
    # Find all HDF5 files
    h5_files = sorted(glob.glob(os.path.join(results_dir, '*/turb.*.h5')))
    
    for h5_file in h5_files:
        # Extract run ID from filename
        run_id = os.path.basename(os.path.dirname(h5_file))
        
        # Extract parameters from run ID
        # Expected format: run_f{f}_beta{beta}_theta{theta}_M{M}_seed{seed}
        params = parse_run_id(run_id)
        
        # Analyze turbulence
        t, M_turb = compute_mach_number(h5_file)
        M_turb_mean = np.mean(M_turb)
        
        # Analyze fragmentation
        peaks, _ = detect_cores(h5_file)
        lambda_W, lambda_W_std = extract_lambda_W(peaks, dx=0.0078)  # 512³
        
        # Classify outcome
        outcome, confidence = classify_fragmentation(h5_file)
        
        # Get fragmentation time
        t_frag = find_fragmentation_time(h5_file)
        
        results.append({
            'run_id': run_id,
            **params,
            'M_turb_mean': M_turb_mean,
            'lambda_W': lambda_W,
            'lambda_W_std': lambda_W_std,
            'outcome': outcome,
            't_frag': t_frag
        })
    
    # Create DataFrame
    df = pd.DataFrame(results)
    
    # Save results
    df.to_csv('campaign_results.csv', index=False)
    
    # Generate summary plots
    generate_summary_plots(df)
    
    return df

def parse_run_id(run_id):
    """Extract parameters from run ID string."""
    # Example: run_f1.2_beta0.5_theta0_M1.0_seed42
    # Extract using regex
    import re
    
    match = re.match(r'run_f([\d\.]+)_beta([\d\.]+)_theta(\d+)_M([\d\.]+)_seed(\d+)', run_id)
    
    if match:
        f = float(match.group(1))
        beta = float(match.group(2))
        theta = int(match.group(3))
        M_driver = float(match.group(4))
        seed = int(match.group(5))
        
        return {
            'f': f,
            'beta': beta,
            'theta': theta,
            'M_driver': M_driver,
            'seed': seed
        }
    else:
        raise ValueError(f"Cannot parse run_id: {run_id}")
```

## Automated Analysis Workflow

### Master Pipeline
```bash
#!/bin/bash
# run_full_analysis.sh

RESULTS_DIR=$1
ATHENA_BIN=/path/to/athena/bin

echo "=== Transonic Turbulence Campaign Analysis ==="
echo "Results directory: $RESULTS_DIR"
echo ""

# Step 1: Check simulation completion
echo "Step 1: Checking simulation completion..."
python check_completion.py $RESULTS_DIR

# Step 2: Extract turbulence statistics
echo "Step 2: Extracting turbulence statistics..."
python extract_turbulence_stats.py $RESULTS_DIR

# Step 3: Measure fragmentation spacing
echo "Step 3: Measuring fragmentation spacing..."
python extract_lambda_W.py $RESULTS_DIR

# Step 4: Classify fragmentation outcomes
echo "Step 4: Classifying fragmentation outcomes..."
python classify_all_runs.py $RESULTS_DIR

# Step 5: Generate comparison plots
echo "Step 5: Generating comparison plots..."
python plot_hgbs_comparison.py $RESULTS_DIR

# Step 6: Create summary table
echo "Step 6: Creating summary table..."
python create_summary_table.py $RESULTS_DIR

echo ""
echo "=== Analysis Complete ==="
echo "Results saved to: analysis_results/"
echo ""
```

### Execution
```bash
chmod +x run_full_analysis.sh
./run_full_analysis.sh /scratch/username/turbulence_campaign/results/
```

## Output Format

### Results File Structure
```
analysis_results/
├── turbulence_stats/
│   ├── mach_evolution/
│   │   └── run_001_mach.pdf
│   ├── power_spectra/
│   │   └── run_001_spectrum.pdf
│   └── turbulence_summary.csv
├── fragmentation/
│   ├── core_detections/
│   │   └── run_001_cores.pdf
│   ├── lambda_W_measurements.csv
│   └── fragmentation_times.csv
├── classification/
│   ├── outcome_phase_diagram.pdf
│   └── outcome_summary.csv
└── hgbs_comparison/
    ├── lambda_W_vs_M.pdf
    ├── outcome_vs_M.pdf
    └── summary.pdf
```

### Summary Table Format
```csv
run_id,f,beta,theta,M_driver,seed,M_turb_mean,lambda_W,lambda_W_std,outcome,t_frag
run_001,1.2,0.5,0,1.0,0,1.15,0.12,2.3,0.45
run_002,1.2,0.5,0,1.0,1,1.18,0.10,2.4,0.47
...
```

## Quick Reference Scripts

### Single Simulation Analysis
```bash
# Quick analysis of one simulation
python analyze_single.py run_001/turb.0.0500.h5

# This outputs:
# - Turbulent Mach number: 1.2 ± 0.3
# - Fragmentation spacing: λ/W = 2.3 ± 0.1
# - Outcome: BEADING
# - Fragmentation time: t_frag = 0.45 t_J
```

### Campaign Summary
```bash
# Generate campaign summary
python generate_summary.py --results_dir results/ --output summary.pdf

# Outputs:
# - Overall success rate: 95/108 simulations completed
# - Turbulence maintenance: 92/108 achieved M ≥ 1.0
# - Fragmentation detected: 87/108 showed beading
# - Mean λ/W for M ≥ 1: 2.4 ± 0.6 (vs 2.79 ± 0.09 HGBS)
```

## Troubleshooting Analysis

### Common Issues

#### Issue 1: No HDF5 files produced
**Check**:
```bash
ls -lh /scratch/username/turb_*/turb.*.h5
```

**Solution**:
- Check if simulation ran long enough
- Verify HDF5 output was enabled in athena.input
- Check disk quota

#### Issue 2: Incomplete runs (t < tlim)
**Analysis**:
```python
# Check simulation duration
with h5py.File('turb.0.0100.h5', 'r') as f:
    t_final = f.attrs.get('Time', 0.0)
    print(f"Simulation ran to t = {t_final:.3f} t_J")
```

**Solution**:
- Extend tlim in input file
- Check for numerical instabilities
- Restart from checkpoint if available

#### Issue 3: No beading detected
**Analysis**:
```python
# Check if beading exists but was missed
python detect_cores.py turb.0.0500.h5 --threshold 2.0
python detect_cores.py turb.0.0500.h5 --threshold 1.5
python detect_cores.py turb.0.0500.h5 --threshold 1.0
```

**Solution**:
- Try different thresholds
- Check if radial collapse occurred instead
- Analyze earlier snapshots to see if beading was transient

## Integration with Paper

### Updating Paper Results
Once analysis is complete, update paper sections:

1. **Section 4.7.4**: Replace turbulence discussion with new results
2. **Section 5.3**: Update Heitsch formalism comparison
3. **Conclusions**: Replace turbulence bullet point with new findings
4. **Tables**: Update turbulence comparison tables

### LaTeX Table Format
```latex
\begin{table*}
\caption{Transonic Turbulence Campaign Results}
\label{tab:turbulence_transonic}
\begin{tabular}{lcccc}
\toprule
\textbf{Configuration} & \textbf{M\_turb} & \textbf{λ/W} & \textbf{Outcome} & \textbf{Notes} \\
\midrule
Longitudinal, β=0.5, M=2.0 & 2.1 ± 0.4 & 2.8 ± 0.3 & BEADING & Matches HGBS \\
Longitudinal, β=1.0, M=2.0 & 2.3 ± 0.5 & 3.1 ± 0.4 & BEADING & Matches HGBS \\
Perpendicular, β=0.5, M=2.0 & 2.1 ± 0.4 & 1.3 ± 0.2 & RADIAL\_COLLAPSE & Below HGBS \\
\bottomrule
\end{tabular}
\end{table*}
```

---
**Last updated**: 2026-05-18
**Based on**: HGBS paper Section 4.7.4, Heitsch (2009)
