#!/usr/bin/env python3
"""
Extract longitudinal beading pattern from simulation outputs.

This script detects density peaks and measures fragmentation wavelength
from Athena++ simulation snapshots for the peer review response campaigns.
"""

import numpy as np
import h5py
from scipy.signal import find_peaks
from scipy.interpolate import interp1d
from pathlib import Path
from typing import Dict, List, Any, Optional
import json


def load_density_field(snapshot_file: str) -> np.ndarray:
    """
    Load density field from HDF5 snapshot file.

    Parameters
    ----------
    snapshot_file : str
        Path to HDF5 snapshot file

    Returns
    -------
    np.ndarray
        Density field with shape (Nz, Ny, Nx, 1)
    """
    try:
        with h5py.File(snapshot_file, 'r') as f:
            # Try common field names
            for key in ['rho', 'density', 'dens']:
                if key in f:
                    rho = f[key][:]
                    return rho

            # If not found, list available datasets
            raise ValueError(f"No density field found. Available: {list(f.keys())}")

    except Exception as e:
        raise IOError(f"Failed to load {snapshot_file}: {e}")


def compute_longitudinal_profile(rho: np.ndarray) -> np.ndarray:
    """
    Compute longitudinal density profile by averaging over transverse directions.

    Parameters
    ----------
    rho : np.ndarray
        Density field with shape (Nz, Ny, Nx, 1)

    Returns
    -------
    np.ndarray
        Longitudinal profile with shape (Nx,)
    """
    # Average over transverse dimensions (z and y axes)
    rho_1D = rho.mean(axis=(0, 1))

    # Remove singleton dimension if present
    if rho_1D.ndim > 1:
        rho_1D = rho_1D.squeeze()

    return rho_1D


def normalize_profile(rho_1D: np.ndarray) -> np.ndarray:
    """
    Normalize density profile to mean zero, unit variance.

    Parameters
    ----------
    rho_1D : np.ndarray
        Longitudinal density profile

    Returns
    -------
    np.ndarray
        Normalized profile
    """
    rho_mean = rho_1D.mean()
    rho_std = rho_1D.std()

    if rho_std > 0:
        return (rho_1D - rho_mean) / rho_std
    else:
        return rho_1D - rho_mean


def extract_beading_pattern(
    snapshot_file: str,
    contrast_threshold: float = 0.1,
    min_peak_separation: int = 20,
    Lx_lambdaJ: float = 8.0
) -> Dict[str, Any]:
    """
    Extract beading pattern from a simulation snapshot.

    Parameters
    ----------
    snapshot_file : str
        Path to HDF5 snapshot file
    contrast_threshold : float
        Minimum peak contrast (as fraction of mean density)
    min_peak_separation : int
        Minimum separation between peaks in grid cells
    Lx_lambdaJ : float
        Domain length in units of λJ

    Returns
    -------
    dict
        Beading analysis results with keys:
        - n_peaks: Number of peaks detected
        - peak_positions: Array of peak positions (in λJ units)
        - lambda_measured: Mean spacing between peaks (in λJ units)
        - longitudinal_variance: Variance of normalized profile
        - peak_contrasts: Array of peak contrasts
        - status: 'beading_detected', 'no_beading', or 'error'
        - rho_normalized: Normalized density profile
    """
    try:
        # Load and process density field
        rho = load_density_field(snapshot_file)
        rho_1D = compute_longitudinal_profile(rho)

        # Get grid information
        Nx = len(rho_1D)
        dx = Lx_lambdaJ / Nx  # Grid spacing in λJ units

        # Normalize for peak detection
        rho_mean = rho_1D.mean()
        rho_normalized = (rho_1D - rho_mean) / rho_mean

        # Detect peaks
        peaks, properties = find_peaks(
            rho_normalized,
            height=contrast_threshold,
            distance=min_peak_separation
        )

        if len(peaks) == 0:
            return {
                'n_peaks': 0,
                'peak_positions': [],
                'lambda_measured': None,
                'longitudinal_variance': np.var(rho_normalized),
                'peak_contrasts': [],
                'status': 'no_beading',
                'rho_normalized': rho_normalized.tolist(),
                'Nx': Nx,
                'Lx_lambdaJ': Lx_lambdaJ
            }

        # Convert peak positions to physical units (λJ)
        peak_positions_lambdaJ = peaks * dx

        # Measure wavelength from peak spacing
        if len(peaks) >= 2:
            # Use mean spacing between adjacent peaks
            lambda_grid = np.diff(peaks).mean()
            lambda_measured = lambda_grid * dx  # Convert to λJ units
        else:
            # Only one peak - cannot measure wavelength
            lambda_measured = None

        # Extract peak contrasts
        peak_contrasts = rho_normalized[peaks].tolist()

        return {
            'n_peaks': len(peaks),
            'peak_positions': peak_positions_lambdaJ.tolist(),
            'lambda_measured': lambda_measured,
            'longitudinal_variance': np.var(rho_normalized),
            'peak_contrasts': peak_contrasts,
            'status': 'beading_detected',
            'rho_normalized': rho_normalized.tolist(),
            'Nx': Nx,
            'Lx_lambdaJ': Lx_lambdaJ
        }

    except Exception as e:
        return {
            'n_peaks': 0,
            'peak_positions': [],
            'lambda_measured': None,
            'longitudinal_variance': 0.0,
            'peak_contrasts': [],
            'status': f'error: {str(e)}',
            'error': str(e)
        }


def analyze_time_series(
    output_dir: str,
    Lx_lambdaJ: float = 8.0,
    snapshot_pattern: str = "*.h5"
) -> List[Dict[str, Any]]:
    """
    Analyze beading evolution through time from HST output files.

    Parameters
    ----------
    output_dir : str
        Directory containing simulation outputs
    Lx_lambdaJ : float
        Domain length in λJ units
    snapshot_pattern : str
        Glob pattern for snapshot files

    Returns
    -------
    list
        Time series of beading analysis results
    """
    output_path = Path(output_dir)
    snapshot_files = sorted(output_path.glob(snapshot_pattern))

    if len(snapshot_files) == 0:
        print(f"Warning: No snapshot files found matching {snapshot_pattern} in {output_dir}")
        return []

    results = []
    for snapshot_file in snapshot_files:
        result = extract_beading_pattern(str(snapshot_file), Lx_lambdaJ=Lx_lambdaJ)
        result['snapshot_file'] = str(snapshot_file)
        result['snapshot_index'] = int(snapshot_file.stem.split('.')[-1]) if '.' in snapshot_file.name else None
        results.append(result)

    return results


def compute_lambda_over_W(
    lambda_measured: float,
    W_core: float = 0.3
) -> float:
    """
    Compute λ/W ratio from measured wavelength.

    Parameters
    ----------
    lambda_measured : float
        Measured fragmentation wavelength (in λJ units)
    W_core : float
        Core half-width (in λJ units)

    Returns
    -------
    float
        λ/W ratio
    """
    return lambda_measured / (2 * W_core)  # Full width = 2 * half-width


def measure_density_contrast(
    snapshot_file: str,
    Lx_lambdaJ: float = 8.0
) -> Dict[str, float]:
    """
    Measure density contrast C = ρ_max/ρ_0 from snapshot.

    Parameters
    ----------
    snapshot_file : str
        Path to snapshot file
    Lx_lambdaJ : float
        Domain length in λJ units

    Returns
    -------
    dict
        Density contrast metrics
    """
    try:
        rho = load_density_field(snapshot_file)
        rho_1D = compute_longitudinal_profile(rho)

        rho_0 = rho_1D.mean()  # Background density
        rho_max = rho_1D.max()  # Peak density
        rho_min = rho_1D.min()  # Minimum density

        return {
            'C_max': rho_max / rho_0 if rho_0 > 0 else np.inf,
            'C_min': rho_min / rho_0 if rho_0 > 0 else 0.0,
            'rho_max': float(rho_max),
            'rho_0': float(rho_0),
            'rho_min': float(rho_min)
        }

    except Exception as e:
        return {
            'error': str(e)
        }


def batch_analyze_campaign(
    campaign_dir: str,
    campaign_name: str,
    output_json: Optional[str] = None
) -> Dict[str, Any]:
    """
    Batch analyze all simulations in a campaign.

    Parameters
    ----------
    campaign_dir : str
        Base directory containing campaign outputs
    campaign_name : str
        Campaign identifier
    output_json : str, optional
        Path to save results JSON

    Returns
    -------
    dict
        Campaign analysis results
    """
    campaign_path = Path(campaign_dir)
    output_base = campaign_path / 'outputs' / campaign_name

    if not output_base.exists():
        return {'error': f'Output directory not found: {output_base}'}

    # Find all simulation directories
    sim_dirs = [d for d in output_base.iterdir() if d.is_dir()]

    results = {}
    for sim_dir in sim_dirs:
        sim_name = sim_dir.name

        # Extract parameters from directory name
        # Expected format: {campaign}_f{f}_beta{beta}_M{M}_theta{theta}_s{seed}
        try:
            parts = sim_name.split('_')
            params = {}
            for part in parts:
                if part.startswith('f'):
                    params['f'] = float(part[1:])
                elif part.startswith('beta'):
                    params['beta'] = float(part[4:])
                elif part.startswith('M'):
                    params['M'] = float(part[1:])
                elif part.startswith('theta'):
                    params['theta'] = float(part[5:])
                elif part.startswith('s'):
                    params['seed'] = int(part[1:])

            # Analyze final snapshot
            h5_files = list(sim_dir.glob('*.h5'))
            if h5_files:
                # Use the last H5 file (final output)
                final_file = sorted(h5_files)[-1]

                # Determine domain length from parameters or use default
                Lx = params.get('Lx_lambdaJ', 8.0)  # Default to 8λJ

                beading_result = extract_beading_pattern(str(final_file), Lx_lambdaJ=Lx)
                contrast_result = measure_density_contrast(str(final_file), Lx_lambdaJ=Lx)

                results[sim_name] = {
                    'parameters': params,
                    'beading': beading_result,
                    'contrast': contrast_result,
                    'final_file': str(final_file)
                }
            else:
                results[sim_name] = {
                    'parameters': params,
                    'error': 'No output files found'
                }

        except Exception as e:
            results[sim_name] = {'error': str(e)}

    # Save to JSON if requested
    if output_json:
        with open(output_json, 'w') as f:
            json.dump(results, f, indent=2)

    return results


def generate_summary_statistics(campaign_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate summary statistics from campaign analysis results.

    Parameters
    ----------
    campaign_results : dict
        Results from batch_analyze_campaign

    Returns
    -------
    dict
        Summary statistics
    """
    beading_detected = []
    no_beading = []
    lambda_values = []
    contrast_values = []

    for sim_name, result in campaign_results.items():
        if 'error' in result:
            continue

        if result.get('beading', {}).get('status') == 'beading_detected':
            beading_detected.append(sim_name)
            lambda_val = result['beading'].get('lambda_measured')
            if lambda_val is not None:
                lambda_values.append(lambda_val)
        else:
            no_beading.append(sim_name)

        contrast = result.get('contrast', {}).get('C_max')
        if contrast is not None:
            contrast_values.append(contrast)

    summary = {
        'total_simulations': len(campaign_results),
        'beading_detected': len(beading_detected),
        'no_beading': len(no_beading),
        'detection_rate': len(beading_detected) / len(campaign_results) if campaign_results else 0.0,
        'beading_simulations': beading_detected
    }

    if lambda_values:
        summary['lambda_mean'] = float(np.mean(lambda_values))
        summary['lambda_std'] = float(np.std(lambda_values))
        summary['lambda_min'] = float(np.min(lambda_values))
        summary['lambda_max'] = float(np.max(lambda_values))
        summary['lambda_median'] = float(np.median(lambda_values))

    if contrast_values:
        summary['contrast_mean'] = float(np.mean(contrast_values))
        summary['contrast_std'] = float(np.std(contrast_values))
        summary['contrast_max'] = float(np.max(contrast_values))

    return summary


def main():
    """Command-line interface for beading extraction."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract beading pattern from Athena++ simulation outputs'
    )
    parser.add_argument(
        'input',
        help='Input snapshot file or campaign directory'
    )
    parser.add_argument(
        '--campaign',
        help='Campaign name (if analyzing full campaign)',
        default=None
    )
    parser.add_argument(
        '--output',
        help='Output JSON file',
        default=None
    )
    parser.add_argument(
        '--Lx',
        help='Domain length in λJ units',
        type=float,
        default=8.0
    )
    parser.add_argument(
        '--contrast',
        help='Peak contrast threshold',
        type=float,
        default=0.1
    )

    args = parser.parse_args()

    input_path = Path(args.input)

    if input_path.is_file():
        # Single file analysis
        result = extract_beading_pattern(
            str(input_path),
            contrast_threshold=args.contrast,
            Lx_lambdaJ=args.Lx
        )

        print(json.dumps(result, indent=2))

        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\nResults saved to {args.output}")

    elif input_path.is_dir() and args.campaign:
        # Campaign analysis
        results = batch_analyze_campaign(
            str(input_path),
            args.campaign,
            output_json=args.output
        )

        summary = generate_summary_statistics(results)

        print("\nCAMPAIGN SUMMARY")
        print("=" * 70)
        print(f"Total simulations: {summary['total_simulations']}")
        print(f"Beading detected: {summary['beading_detected']} ({summary['detection_rate']*100:.1f}%)")
        print(f"No beading: {summary['no_beading']}")

        if 'lambda_mean' in summary:
            print(f"\nλ statistics:")
            print(f"  Mean: {summary['lambda_mean']:.3f} ± {summary['lambda_std']:.3f} λJ")
            print(f"  Range: [{summary['lambda_min']:.3f}, {summary['lambda_max']:.3f}] λJ")

        if 'contrast_mean' in summary:
            print(f"\nDensity contrast:")
            print(f"  Mean: {summary['contrast_mean']:.2f} ± {summary['contrast_std']:.2f}")
            print(f"  Max: {summary['contrast_max']:.2f}")

        print("=" * 70)

        if args.output:
            print(f"\nFull results saved to {args.output}")


if __name__ == '__main__':
    main()
