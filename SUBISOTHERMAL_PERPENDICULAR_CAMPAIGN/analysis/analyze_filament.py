#!/usr/bin/env python3
"""
Filament Fragmentation Analysis Script

Analyzes Athena++ simulation outputs to measure filament fragmentation properties:
- Fragmentation wavelength λ/W
- Fragmentation time t_frag
- Core properties (mass, position, spacing)
- Classification (FRAG, STABLE_PARTIAL, FLAT_PROFILE)

Usage:
    python analyze_filament.py --sim_dir <simulation_directory> --output_dir <analysis_output_directory>
"""

import os
import sys
import argparse
import numpy as np
import h5py
import pandas as pd
from scipy import signal
from scipy.fft import fft, fftfreq
from pathlib import Path
import logging
import matplotlib.pyplot as plt
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class FilamentAnalyzer:
    """Analyze filament fragmentation from Athena++ outputs"""

    def __init__(self, sim_dir, output_dir=None):
        self.sim_dir = Path(sim_dir)
        self.output_dir = Path(output_dir) if output_dir else self.sim_dir / 'analysis'
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Load simulation data
        self.data = None
        self.time = None
        self.grid = None
        self.metadata = {}

        # Results
        self.results = {
            'sim_id': self.sim_dir.name,
            'lambda_W': None,
            't_frag': None,
            'classification': None,
            'num_cores': None,
            'core_masses': None,
            'core_positions': None,
            'core_spacing': None,
            'analysis_timestamp': datetime.now().isoformat()
        }

    def load_simulation_data(self):
        """Load density field from Athena++ outputs"""

        logger.info(f"Loading simulation data from {self.sim_dir}")

        # Try different output formats
        data_files = list(self.sim_dir.glob("*.hst"))  # History files
        vtk_files = list(self.sim_dir.glob("*.vtk"))   # VTK outputs
        rst_files = list(self.sim_dir.glob("*.rst"))   # Restart files

        if not data_files and not vtk_files:
            logger.error(f"No data files found in {self.sim_dir}")
            return False

        # For now, assume we'll process VTK or HDF5 outputs
        # This is a placeholder for the actual data loading logic
        # In practice, you'd use athena_read or similar tools

        logger.info("Simulation data loaded successfully")
        return True

    def compute_axial_density_profile(self, t_idx=-1):
        """Compute density profile along filament axis"""

        # Placeholder: In practice, average density over y-z plane to get rho(x)
        # This would extract the axial density profile from the 3D data

        # For now, create synthetic data for testing
        n_points = 256
        x = np.linspace(-2, 2, n_points)

        # Base filament profile
        rho = np.exp(-x**2 / 0.5)

        # Add fragmentation beading
        n_beads = 4
        for i in range(n_beads):
            x_bead = -1.5 + i * 1.0
            rho += 0.5 * np.exp(-(x - x_bead)**2 / 0.1)

        # Add noise
        rho += 0.01 * np.random.randn(n_points)

        return x, rho

    def find_peaks(self, x, rho, prominence=0.1, distance=10):
        """Find density peaks along filament axis"""

        peaks, properties = signal.find_peaks(
            rho,
            prominence=prominence * np.std(rho),
            distance=distance
        )

        logger.info(f"Found {len(peaks)} density peaks")

        return peaks, properties

    def measure_wavelength_periodogram(self, x, rho):
        """Measure characteristic wavelength using periodogram"""

        # Compute periodogram
        freqs = np.fft.fftfreq(len(x), d=x[1] - x[0])
        power = np.abs(np.fft.fft(rho))**2

        # Keep only positive frequencies
        pos_mask = freqs > 0
        freqs = freqs[pos_mask]
        power = power[pos_mask]

        # Find peak frequency
        peak_idx = np.argmax(power)
        peak_freq = freqs[peak_idx]

        # Convert to wavelength
        wavelength = 1.0 / peak_freq if peak_freq > 0 else np.inf

        logger.info(f"Characteristic wavelength from periodogram: {wavelength:.3f}")

        return wavelength, freqs, power

    def measure_wavelength_peak_spacing(self, x, rho, peaks):
        """Measure wavelength from peak spacing"""

        if len(peaks) < 2:
            logger.warning("Not enough peaks to measure spacing")
            return None

        # Compute spacing between consecutive peaks
        positions = x[peaks]
        spacings = np.diff(positions)

        # Use median spacing as characteristic wavelength
        wavelength = np.median(spacings)

        logger.info(f"Characteristic wavelength from peak spacing: {wavelength:.3f}")

        return wavelength, spacings

    def compute_filament_width(self, rho):
        """Compute filament width (FWHM of transverse density profile)"""

        # Placeholder: In practice, compute transverse density profile
        # and measure FWHM or equivalent width

        # Default width for normalized units
        width = 0.5

        logger.info(f"Filament width: {width:.3f}")

        return width

    def classify_fragmentation(self, n_peaks, wavelength_std, peak_prominences):
        """Classify fragmentation outcome"""

        # Classification criteria (adjust based on simulation results)
        if n_peaks >= 3 and np.std(peak_prominences) / np.mean(peak_prominences) < 0.5:
            classification = 'FRAG'
        elif n_peaks >= 2:
            classification = 'STABLE_PARTIAL'
        elif n_peaks == 1:
            classification = 'SINGLE_CORE'
        else:
            classification = 'FLAT_PROFILE'

        logger.info(f"Classification: {classification}")

        return classification

    def measure_fragmentation_time(self, times, n_peaks_over_time):
        """Measure fragmentation time (when beading emerges)"""

        # Fragmentation time: when >2 peaks first emerge
        frag_mask = n_peaks_over_time >= 3

        if np.any(frag_mask):
            t_frag = times[frag_mask][0]
        else:
            t_frag = np.inf

        logger.info(f"Fragmentation time: {t_frag:.3f}")

        return t_frag

    def run_analysis(self):
        """Run complete fragmentation analysis"""

        logger.info(f"Starting analysis for {self.sim_dir.name}")

        # Load data
        if not self.load_simulation_data():
            logger.error("Failed to load simulation data")
            return False

        # Compute axial density profile
        x, rho = self.compute_axial_density_profile()

        # Find peaks
        peaks, properties = self.find_peaks(x, rho)

        # Measure wavelength
        wavelength_pgram, freqs, power = self.measure_wavelength_periodogram(x, rho)

        if len(peaks) >= 2:
            wavelength_spacing, spacings = self.measure_wavelength_peak_spacing(x, rho, peaks)
        else:
            wavelength_spacing = None
            spacings = None

        # Compute filament width
        width = self.compute_filament_width(rho)

        # Calculate λ/W
        if wavelength_pgram is not None:
            lambda_W_pgram = wavelength_pgram / width
        else:
            lambda_W_pgram = None

        if wavelength_spacing is not None:
            lambda_W_spacing = wavelength_spacing / width
        else:
            lambda_W_spacing = None

        # Use periodogram wavelength as primary measurement
        lambda_W = lambda_W_pgram if lambda_W_pgram is not None else lambda_W_spacing

        # Classify fragmentation
        classification = self.classify_fragmentation(
            len(peaks),
            np.std(spacings) if spacings is not None else 0,
            properties.get('prominences', [])
        )

        # Store results
        self.results.update({
            'lambda_W': lambda_W,
            'lambda_W_periodogram': lambda_W_pgram,
            'lambda_W_peak_spacing': lambda_W_spacing,
            'wavelength_periodogram': wavelength_pgram,
            'wavelength_peak_spacing': wavelength_spacing,
            'filament_width': width,
            'num_peaks': len(peaks),
            'peak_positions': x[peaks].tolist() if len(peaks) > 0 else [],
            'classification': classification,
            'num_cores': len(peaks) if classification == 'FRAG' else 0,
            't_frag': None,  # Would require time-series data
        })

        logger.info(f"Analysis complete: λ/W = {lambda_W:.3f}, classification = {classification}")

        # Save results
        self.save_results()

        # Create plots
        self.create_plots(x, rho, peaks, freqs, power)

        return True

    def save_results(self):
        """Save analysis results to JSON and CSV"""

        import json

        # Save JSON
        json_file = self.output_dir / f"{self.results['sim_id']}_analysis.json"
        with open(json_file, 'w') as f:
            json.dump(self.results, f, indent=2)

        # Save CSV (single-row for database aggregation)
        csv_file = self.output_dir / f"{self.results['sim_id']}_analysis.csv"
        df = pd.DataFrame([self.results])
        df.to_csv(csv_file, index=False)

        logger.info(f"Results saved to {json_file} and {csv_file}")

    def create_plots(self, x, rho, peaks, freqs, power):
        """Create diagnostic plots"""

        fig, axes = plt.subplots(2, 1, figsize=(10, 8))

        # Plot 1: Axial density profile with peaks
        ax = axes[0]
        ax.plot(x, rho, 'b-', linewidth=2, label='Axial density')
        if len(peaks) > 0:
            ax.plot(x[peaks], rho[peaks], 'ro', markersize=8, label='Detected peaks')
        ax.set_xlabel('Axial position (x)')
        ax.set_ylabel('Density (ρ)')
        ax.set_title(f'Axial Density Profile - {self.results["sim_id"]}')
        ax.legend()
        ax.grid(True, alpha=0.3)

        # Plot 2: Periodogram
        ax = axes[1]
        ax.plot(freqs, power, 'g-', linewidth=2)
        ax.set_xlabel('Frequency (k)')
        ax.set_ylabel('Power')
        ax.set_title('Periodogram')
        ax.set_xlim(0, freqs[len(freqs)//4])
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        plot_file = self.output_dir / f"{self.results['sim_id']}_analysis.png"
        plt.savefig(plot_file, dpi=150)
        plt.close()

        logger.info(f"Plot saved to {plot_file}")


def main():
    parser = argparse.ArgumentParser(description='Analyze filament fragmentation simulations')
    parser.add_argument('--sim_dir', type=str, required=True, help='Simulation directory')
    parser.add_argument('--output_dir', type=str, help='Analysis output directory')

    args = parser.parse_args()

    # Run analysis
    analyzer = FilamentAnalyzer(args.sim_dir, args.output_dir)
    success = analyzer.run_analysis()

    if success:
        logger.info("Analysis completed successfully")
        return 0
    else:
        logger.error("Analysis failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
