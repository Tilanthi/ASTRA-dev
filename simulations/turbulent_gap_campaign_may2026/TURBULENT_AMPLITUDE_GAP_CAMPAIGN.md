# Turbulent Amplitude Gap Campaign: Resolving HGBS Filament Fragmentation at Realistic Turbulence

## Executive Summary

**Critical Gap**: Current Athena++ simulations use laminar initial conditions (δv/cs ~ 10⁻⁴), while real HGBS filaments have δv/cs ~ 1-3 (four orders of magnitude larger). Campaign 5 tested only up to δv/cs = 1.0, leaving the non-linear regime at δv/cs ~ 2-3 completely untested.

**Objective**: Systematically map λ/W behavior across the full HGBS turbulence amplitude range (δv/cs = 1.0-3.0) for both longitudinal and perpendicular field geometries, testing whether qualitative dependencies (field geometry effects, β-dependence) survive at realistic amplitudes.

## Campaign Design

### Parameter Space Coverage

| Parameter | Range | Values | Rationale |
|-----------|-------|--------|-----------|
| Turbulent amplitude (δv/cs) | 1.0 - 3.0 | 1.0, 1.5, 2.0, 2.5, 3.0 | Full HGBS range |
| Line-mass fraction (f) | 1.0 - 2.0 | 1.0, 1.2, 1.5, 2.0 | Near-critical to supercritical |
| Plasma β (longitudinal) | 0.3 - 2.0 | 0.3, 0.5, 1.0, 2.0 | Weak to strong field |
| Field geometry (θ) | 0°, 90° | 0° (longitudinal), 90° (perpendicular) | Planck-relevant geometries |
| Random seeds | - | 5 per parameter point | Statistical robustness |

**Total simulations**: 5 amplitudes × 4 f values × 4 β values × 2 geometries × 5 seeds = **800 simulations**

### Critical Design Choices

1. **Temporal Resolution**: HDF5 snapshots every 0.01 tJ (not 0.05 tJ) to capture narrow beading window
2. **Domain Size**: 16λJ × 1λJ × 1λJ (extended longitudinal for higher turbulent modes)
3. **Spatial Resolution**: 512 × 64 × 64 cells (64 cells/λJ for adequate turbulent mode resolution)
4. **Turbulence Spectrum**: Kolmogorov driving with 8 longitudinal modes, v_x2 = v_x3 = 0 (filament-axis coherent)

### Simulation Configuration

```python
# Athena++ configuration template
[film]
problem = filament_fragmentation

[parthenon]
tmax = 2.0  # Multiple tJ to ensure fragmentation captured
nghost = 2
ncycles_out = 1  # Every timestep

[mesh]
nx1 = 512
nx2 = 64
nx3 = 64
flevels = 1  # Mesh refinement: 32³ blocks

[coordinates]
x1min = 0.0
x1max = 16.0  # 16 λJ longitudinal
x2min = -1.0
x2max = 1.0   # 2 λJ transverse
x3min = -0.5
x3max = 0.5   # 1 λJ transverse

[hydro]
eos = isothermal
c_s = 1.0  # Sound speed (code units)
gamma = 1.001  # Effectively isothermal

[field]
f = 0.0  # Initial field strength set by β below
B0 = calculated_from_beta  # B = sqrt(8πρc_s²/β)

[filament]
rho0 = 1.0  # Central density
W = 0.3  # Core half-width (0.3 λJ)
profile = gaussian  # ρ(r) = ρc * exp(-r²/2W²)
f_line_mass = <variable>  # 1.0, 1.2, 1.5, 2.0
beta = <variable>  # 0.3, 0.5, 1.0, 2.0
theta_B = <variable>  # 0° (longitudinal), 90° (perpendicular)

[turbulence]
amplitude = <variable>  # δv/cs = 1.0, 1.5, 2.0, 2.5, 3.0
spectrum = kolmogorov
n_modes = 8  # Longitudinal modes
seed = <variable>  # 1-5 per parameter point
coherent = true  # v_x2 = v_x3 = 0

[output]
fntype = hst  # History files every 0.001 tJ
fntype = hdf5  # Snapshots every 0.01 tJ
dt = 0.01  # HDF5 output interval

[gravity]
four_pi_G = 4π²  # λJ = 1 by construction
solver = fft  # Poisson solver
```

## Analysis Pipeline

### Primary Measurements

1. **Fragmentation Detection**:
   - Longitudinal density variance: σ(ρ_x1)/⟨ρ_x1⟩ > 2×10⁻⁴
   - Peak-finding algorithm: local maxima with ρ/ρ_ambient > 1.5
   - Beading window: Δt = t_last_peak - t_first_peak

2. **Spacing Measurement**:
   - Nearest-neighbor distance between detected peaks along x1 axis
   - λ/W = (mean spacing) / (0.3 λJ)
   - Bootstrap uncertainty (10,000 resamples) for confidence intervals

3. **Timescale Measurement**:
   - t_frag: time when σ(ρ_x1)/⟨ρ_x1⟩ first exceeds threshold
   - t_collapse: time when radial CFL timestep drops below 10⁻⁸ tJ
   - Competition parameter: ξ = t_frag / t_collapse

4. **Morphology Classification**:
   - FULL: ≥ 3 well-defined peaks with consistent spacing
   - PARTIAL: 1-2 peaks or irregular spacing
   - RADIAL_ONLY: σ(ρ_x1)/⟨ρ_x1⟩ < 2×10⁻⁴ throughout
   - SUPPRESSED: No fragmentation by t = 2.0 tJ

### Analysis Scripts

```python
#!/usr/bin/env python3
"""
turbulent_gap_analysis.py
Analysis pipeline for Turbulent Amplitude Gap Campaign
"""

import numpy as np
import h5py
import pandas as pd
from scipy.signal import find_peaks
from scipy.stats import bootstrap

def detect_fragmentation(snapshot_data, threshold=2e-4):
    """
    Detect longitudinal fragmentation from HDF5 snapshot.

    Parameters:
    -----------
    snapshot_data : h5py.File
        Athena++ HDF5 snapshot output
    threshold : float
        Density variance threshold for fragmentation detection

    Returns:
    --------
    dict with keys:
        fragmented : bool
        n_peaks : int
        peak_positions : array
        spacing_mean : float
        spacing_std : float
        t_detect : float
    """
    # Extract longitudinal density profile
    rho = snapshot_data['prim']['rho'][:]

    # Compute axial average (x2, x3 dimensions)
    rho_axial = rho.mean(axis=(1, 2))

    # Compute longitudinal variance
    rho_var = rho_axial.var()
    rho_mean = rho_axial.mean()
    normalized_var = rho_var / (rho_mean**2)

    # Check for fragmentation
    fragmented = normalized_var > threshold

    if not fragmented:
        return {
            'fragmented': False,
            'n_peaks': 0,
            'peak_positions': [],
            'spacing_mean': np.nan,
            'spacing_std': np.nan,
            't_detect': snapshot_data['Attributes']['time'][()]
        }

    # Find peaks
    peaks, properties = find_peaks(
        rho_axial,
        height=1.5 * rho_mean,
        distance=int(0.5 * 512 / 16)  # Minimum 0.5 λJ separation
    )

    if len(peaks) < 2:
        return {
            'fragmented': True,
            'n_peaks': len(peaks),
            'peak_positions': peaks,
            'spacing_mean': np.nan,
            'spacing_std': np.nan,
            't_detect': snapshot_data['Attributes']['time'][()]
        }

    # Compute spacings
    positions = peaks * (16.0 / 512)  # Convert to λJ units
    spacings = np.diff(positions)

    return {
        'fragmented': True,
        'n_peaks': len(peaks),
        'peak_positions': positions,
        'spacing_mean': spacings.mean(),
        'spacing_std': spacings.std(),
        't_detect': snapshot_data['Attributes']['time'][()]
    }

def measure_lambda_W(spacings, W_core=0.3):
    """
    Convert spacings to λ/W ratio.

    Parameters:
    -----------
    spacings : array
        Peak-to-peak spacings in λJ units
    W_core : float
        Core half-width in λJ units

    Returns:
    --------
    lambda_W : float
        Mean λ/W ratio
    """
    if len(spacings) == 0:
        return np.nan
    return spacings.mean() / W_core

def bootstrap_uncertainty(spacings, n_bootstrap=10000):
    """
    Compute bootstrap confidence interval for λ/W.

    Parameters:
    -----------
    spacings : array
        Peak-to-peak spacings
    n_bootstrap : int
        Number of bootstrap iterations

    Returns:
    --------
    ci_lower : float
        Lower 95% confidence bound
    ci_upper : float
        Upper 95% confidence bound
    """
    if len(spacings) < 2:
        return np.nan, np.nan

    lambda_W_values = []
    for _ in range(n_bootstrap):
        sample = np.random.choice(spacings, size=len(spacings), replace=True)
        lambda_W_values.append(sample.mean() / 0.3)

    lambda_W_values = np.array(lambda_W_values)
    return np.percentile(lambda_W_values, 2.5), np.percentile(lambda_W_values, 97.5)

def analyze_simulation(simulation_dir):
    """
    Analyze complete time series for one simulation.

    Parameters:
    -----------
    simulation_dir : str
        Path to simulation output directory

    Returns:
    --------
    results : dict
        Complete analysis results
    """
    import glob
    import os

    # Find all HDF5 snapshots
    snapshot_files = sorted(glob.glob(os.path.join(simulation_dir, '*.hdf5')))

    results = {
        'parameter_point': os.path.basename(simulation_dir),
        'snapshots_analyzed': len(snapshot_files),
        'fragmented': False,
        't_first_detection': np.nan,
        't_last_detection': np.nan,
        'beading_window': np.nan,
        'n_peaks_at_max': 0,
        'lambda_W': np.nan,
        'lambda_W_ci_lower': np.nan,
        'lambda_W_ci_upper': np.nan,
        'morphology': 'SUPPRESSED'
    }

    peak_counts = []
    lambda_W_values = []

    for snapshot_file in snapshot_files:
        with h5py.File(snapshot_file, 'r') as f:
            analysis = detect_fragmentation(f)

            if analysis['fragmented']:
                if not results['fragmented']:
                    results['fragmented'] = True
                    results['t_first_detection'] = analysis['t_detect']

                results['t_last_detection'] = analysis['t_detect']
                peak_counts.append(analysis['n_peaks'])

                if analysis['n_peaks'] >= 2:
                    lambda_W = measure_lambda_W(
                        np.diff(analysis['peak_positions'])
                    )
                    lambda_W_values.append(lambda_W)

    # Compute final statistics
    if results['fragmented']:
        results['beading_window'] = results['t_last_detection'] - results['t_first_detection']
        results['n_peaks_at_max'] = max(peak_counts) if peak_counts else 0

        # Morphology classification
        if results['n_peaks_at_max'] >= 3 and lambda_W_values:
            results['morphology'] = 'FULL'
            results['lambda_W'] = np.mean(lambda_W_values)
            ci_low, ci_high = bootstrap_uncertainty(
                np.diff(analysis['peak_positions'])
            )
            results['lambda_W_ci_lower'] = ci_low
            results['lambda_W_ci_upper'] = ci_high
        elif results['n_peaks_at_max'] >= 1:
            results['morphology'] = 'PARTIAL'
            if lambda_W_values:
                results['lambda_W'] = np.mean(lambda_W_values)
        else:
            results['morphology'] = 'RADIAL_ONLY'

    return results

def compile_campaign_results(campaign_dir):
    """
    Compile results across all simulations in campaign.

    Parameters:
    -----------
    campaign_dir : str
        Path to campaign root directory

    Returns:
    --------
    results_df : pandas.DataFrame
        Compiled results
    """
    import glob
    import os
    from concurrent.futures import ProcessPoolExecutor

    sim_dirs = glob.glob(os.path.join(campaign_dir, 'f*_b*_t*_s*'))

    with ProcessPoolExecutor(max_workers=8) as executor:
        results = executor.map(analyze_simulation, sim_dirs)

    results_list = []
    for result in results:
        # Parse parameter point from directory name
        params = parse_parameter_name(result['parameter_point'])
        result.update(params)
        results_list.append(result)

    return pd.DataFrame(results_list)

def parse_parameter_name(dirname):
    """
    Parse parameter values from directory naming convention.

    Convention: f{f}_b{beta}_t{theta}_s{seed}
    Example: f1.5_b1.0_t90_s3
    """
    import re

    match = re.match(r'f([\d.]+)_b([\d.]+)_t(\d+)_s(\d+)', dirname)
    if match:
        return {
            'f': float(match.group(1)),
            'beta': float(match.group(2)),
            'theta_deg': float(match.group(3)),
            'seed': int(match.group(4))
        }
    return {}

# Visualization functions
def plot_lambda_W_vs_turbulence(results_df):
    """
    Plot λ/W vs turbulent amplitude for different field geometries.
    """
    import matplotlib.pyplot as plt
    import seaborn as sns

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    # Longitudinal field
    longitudinal = results_df[results_df['theta_deg'] == 0]
    for beta in [0.3, 0.5, 1.0, 2.0]:
        beta_data = longitudinal[longitudinal['beta'] == beta]
        axes[0].errorbar(
            beta_data['amplitude'],
            beta_data['lambda_W'],
            yerr=[
                beta_data['lambda_W'] - beta_data['lambda_W_ci_lower'],
                beta_data['lambda_W_ci_upper'] - beta_data['lambda_W']
            ],
            marker='o',
            label=f'β = {beta}',
            alpha=0.7
        )

    axes[0].set_xlabel('Turbulent Amplitude (δv/cs)')
    axes[0].set_ylabel('λ/W')
    axes[0].set_title('Longitudinal Field (θ = 0°)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)

    # Perpendicular field
    perpendicular = results_df[results_df['theta_deg'] == 90]
    for beta in [0.3, 0.5, 1.0, 2.0]:
        beta_data = perpendicular[perpendicular['beta'] == beta]
        axes[1].errorbar(
            beta_data['amplitude'],
            beta_data['lambda_W'],
            yerr=[
                beta_data['lambda_W'] - beta_data['lambda_W_ci_lower'],
                beta_data['lambda_W_ci_upper'] - beta_data['lambda_W']
            ],
            marker='s',
            label=f'β = {beta}',
            alpha=0.7
        )

    axes[1].set_xlabel('Turbulent Amplitude (δv/cs)')
    axes[1].set_ylabel('λ/W')
    axes[1].set_title('Perpendicular Field (θ = 90°)')
    axes[1].legend()
    axes[1].grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('lambda_W_vs_turbulence.png', dpi=300)
    return fig

def plot_fragmentation_rate(results_df):
    """
    Plot fragmentation rate vs turbulent amplitude.
    """
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for theta, ax in zip([0, 90], axes):
        theta_data = results_df[results_df['theta_deg'] == theta]

        # Group by amplitude and count fragmentation rate
        grouped = theta_data.groupby('amplitude').agg({
            'fragmented': 'mean',
            'morphology': lambda x: (x == 'FULL').mean()
        }).reset_index()

        ax.plot(
            grouped['amplitude'],
            grouped['fragmented'] * 100,
            marker='o',
            label='Any fragmentation',
            linewidth=2
        )
        ax.plot(
            grouped['amplitude'],
            grouped['morphology'] * 100,
            marker='s',
            label='FULL morphology',
            linewidth=2
        )

        ax.set_xlabel('Turbulent Amplitude (δv/cs)')
        ax.set_ylabel('Fragmentation Rate (%)')
        ax.set_title(f'{"Longitudinal" if theta == 0 else "Perpendicular"} Field')
        ax.legend()
        ax.grid(True, alpha=0.3)
        ax.set_ylim([0, 105])

    plt.tight_layout()
    plt.savefig('fragmentation_rate.png', dpi=300)
    return fig

def plot_beading_window(results_df):
    """
    Plot beading window duration vs turbulent amplitude.
    """
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))

    for theta, ax in zip([0, 90], axes):
        theta_data = results_df[
            (results_df['theta_deg'] == theta) &
            (results_df['fragmented'] == True)
        ]

        for beta in [0.3, 0.5, 1.0, 2.0]:
            beta_data = theta_data[theta_data['beta'] == beta]
            ax.scatter(
                beta_data['amplitude'],
                beta_data['beading_window'],
                label=f'β = {beta}',
                alpha=0.6,
                s=50
            )

        ax.axhline(y=0.1, color='r', linestyle='--', label='Core growth threshold')
        ax.set_xlabel('Turbulent Amplitude (δv/cs)')
        ax.set_ylabel('Beading Window Δt (tJ)')
        ax.set_title(f'{"Longitudinal" if theta == 0 else "Perpendicular"} Field')
        ax.legend()
        ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig('beading_window.png', dpi=300)
    return fig

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python turbulent_gap_analysis.py <campaign_directory>")
        sys.exit(1)

    campaign_dir = sys.argv[1]

    print(f"Analyzing Turbulent Amplitude Gap Campaign: {campaign_dir}")
    print("This may take several minutes...")

    results_df = compile_campaign_results(campaign_dir)

    # Save results
    results_df.to_csv(f'{campaign_dir}/compiled_results.csv', index=False)

    print(f"\nResults compiled: {len(results_df)} simulations analyzed")
    print(f"Fragmentation rate: {results_df['fragmented'].mean()*100:.1f}%")

    # Generate plots
    print("Generating plots...")
    plot_lambda_W_vs_turbulence(results_df)
    plot_fragmentation_rate(results_df)
    plot_beading_window(results_df)

    print(f"Analysis complete. Results saved to {campaign_dir}/")
```

## Expected Outcomes and Interpretation Framework

### Scenario 1: Turbulence-Independence Persists (Best Case)

If λ/W shows < 15% variation across δv/cs = 1.0-3.0 for both geometries:
- **Conclusion**: Laminar qualitative dependencies remain valid at realistic amplitudes
- **Implication**: Campaign 6 perpendicular-field result (λ/W ≈ 1.25) represents genuine observational tension
- **Action**: Frame as quantitative prediction validated across turbulence range

### Scenario 2: Turbulence-Dependence Emerges (Likely)

If λ/W shows systematic variation > 20% or geometry dependence weakens:
- **Conclusion**: Laminar results do not extrapolate to real ISM conditions
- **Implication**: Campaign 6 results are qualitative only, not quantitative predictions
- **Action**: Emphasize need for realistic-turbulence simulations in future work

### Scenario 3: Morphology Transition (Possible)

If fragmentation rate drops sharply above δv/cs > 2.0:
- **Conclusion**: Turbulent pressure suppresses longitudinal fragmentation at high amplitudes
- **Implication**: Different fragmentation mechanisms dominate in laminar vs. turbulent regimes
- **Action**: Fundamental reinterpretation of simulation-observation comparison

## Computational Requirements

### Resource Estimation

- **Single simulation runtime**: ~3-6 hours (16λJ domain, 512³ resolution)
- **Total wall-clock time**: 800 simulations × 4 hours = 3,200 hours
- **Parallel execution**: 20 concurrent jobs → ~160 hours (~1 week)

### Storage Requirements

- **Per simulation**: ~2 GB (HDF5 snapshots at 0.01 tJ intervals)
- **Total raw data**: 800 × 2 GB = 1.6 TB
- **Processed data**: ~50 MB (CSV summary tables, plots)

## Integration with Paper

### Section to Add: "Turbulent Amplitude Gap Campaign"

```latex
\subsection{Realistic-Turbulence Validation Campaign (800 simulations)}

To address the critical gap between idealised laminar simulations ($\delta v/c_s \sim 10^{-4}$) and real HGBS conditions ($\delta v/c_s \sim 1$--$3$), we conducted a comprehensive campaign spanning the full turbulence amplitude range. This campaign tests whether the qualitative dependencies established under laminar conditions (field geometry effects, $\beta$-dependence) survive at realistic turbulent amplitudes.

\subsubsection{Campaign Design}

We performed 800 Athena++ simulations across:
\begin{itemize}
    \item Turbulent amplitude: $\delta v/c_s = 1.0, 1.5, 2.0, 2.5, 3.0$
    \item Line-mass fraction: $f = 1.0, 1.2, 1.5, 2.0$
    \item Plasma $\beta$: $0.3, 0.5, 1.0, 2.0$
    \item Field geometry: $\theta = 0^\circ$ (longitudinal), $90^\circ$ (perpendicular)
    \item Random seeds: 5 per parameter point
\end{itemize}

All simulations used extended longitudinal domain ($16\,\lambda_J$) with fine temporal resolution (HDF5 snapshots every $0.01\,t_{\rm J}$) to capture the narrow beading window identified in the CTZM validation.

\subsubsection{Key Results}

[Results to be inserted after campaign completion]

\subsubsection{Implications for Simulation-Observation Comparison}

[Interpretation based on observed outcomes]
```

## Bibliography of Relevant Literature

1. **Larson (1981)**: Turbulent properties of molecular clouds - established δv/cs ~ 1-3 as typical
2. **Heyer & Brunt (2004)**: Velocity scaling in molecular clouds
3. **Klessen et al. (2000)**: Turbulent fragmentation simulations
4. **Girichidis et al. (2012)**: Filament formation from turbulent clouds
5. **Seifried & Walch (2016)**: Magnetic field evolution during filament formation

## Contact and Repository

**Campaign PI**: G. J. White
**Institution**: The Open University / Rutherford Appleton Laboratory
**Code Repository**: https://github.com/Tilanthi/ASTRA-dev
**Data Policy**: All simulation outputs will be made publicly available upon publication

---

**Document Version**: 1.0
**Date**: 2026-05-28
**Status**: Ready for implementation
