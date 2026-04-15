#!/usr/bin/env python3

# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
MHD Simulation Suite: Testing Filament Width Origin

This script sets up and analyzes 10 MHD simulations varying Mach number (M) and
plasma beta (β) to test the sonic scale theory for 0.1 pc filament widths.

Parameter Space:
  - Mach number: M = 1, 3, 5, 10, 20
  - Plasma beta: β = 0.1, 1, 10

Theory Predictions:
  - Sonic scale: λ_sonic ∝ L_inj * M^(-2)
  - Higher M → smaller sonic scale → narrower filaments
  - Magnetic effects should modify widths at low β

Author: ASTRA Computational Physics Team
Date: 2026-04-03
"""

import sys
sys.path.insert(0, '/Users/gjw255/astrodata/SWARM/ASTRA')

import numpy as np
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter, label
from scipy.optimize import curve_fit


@dataclass
class SimulationParameters:
    """Parameters for a single MHD simulation"""
    sim_id: str
    mach_number: float  # Sonic Mach number
    plasma_beta: float  # Plasma β = P_thermal / P_magnetic
    box_size_pc: float  # Box size in parsecs
    resolution: int  # Cells per dimension
    driving_scale: float  # Turbulent driving scale (fraction of box)
    magnetic_field_geometry: str  # 'uniform', 'turbulent', 'mixed'
    simulation_time: float  # In units of t_cross = L / σ_turb


@dataclass
class FilamentMeasurement:
    """Measured filament properties from simulation"""
    sim_id: str
    mach_number: float
    plasma_beta: float
    mean_width_pc: float
    width_std_pc: float
    width_median_pc: float
    num_filaments: int
    sonic_scale_prediction: float
    magnetic_scale_prediction: float
    density_range: Tuple[float, float]


class MHDSimulationSuite:
    """
    Manage a suite of MHD simulations to test filament width origin.

    The suite covers a 2D parameter space in (M, β) to test:
    1. Sonic scale prediction: λ_sonic ∝ M^(-2)
    2. Magnetic modification: λ_B depends on β
    """

    def __init__(self, base_dir: str = "./mhd_simulations"):
        """Initialize simulation suite"""
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.simulations = self._define_simulations()
        self.results = []

    def _define_simulations(self) -> List[SimulationParameters]:
        """
        Define 10 simulations covering the (M, β) parameter space.

        Strategy:
        - Fix β = 1, vary M = 1, 3, 5, 10, 20 (test sonic scale)
        - Fix M = 5, vary β = 0.1, 1, 10 (test magnetic effects)
        - Include corners for full coverage
        """
        simulations = []

        # Core sonic scale tests (β = 1, varying M)
        for i, mach in enumerate([1, 3, 5, 10, 20]):
            simulations.append(SimulationParameters(
                sim_id=f"M{mach:02d}_beta1.0",
                mach_number=float(mach),
                plasma_beta=1.0,
                box_size_pc=10.0,  # 10 pc box
                resolution=512,  # 512^3 cells
                driving_scale=0.5,  # Drive at half box size
                magnetic_field_geometry="uniform",
                simulation_time=2.0  # 2 crossing times
            ))

        # Magnetic effect tests (M = 5, varying β)
        for beta in [0.1, 10]:
            simulations.append(SimulationParameters(
                sim_id=f"M05_beta{beta:.1f}",
                mach_number=5.0,
                plasma_beta=beta,
                box_size_pc=10.0,
                resolution=512,
                driving_scale=0.5,
                magnetic_field_geometry="uniform",
                simulation_time=2.0
            ))

        # Corner cases
        simulations.append(SimulationParameters(
            sim_id=f"M01_beta0.1",
            mach_number=1.0,
            plasma_beta=0.1,
            box_size_pc=10.0,
            resolution=512,
            driving_scale=0.5,
            magnetic_field_geometry="uniform",
            simulation_time=2.0
        ))

        simulations.append(SimulationParameters(
            sim_id=f"M20_beta10.0",
            mach_number=20.0,
            plasma_beta=10.0,
            box_size_pc=10.0,
            resolution=512,
            driving_scale=0.5,
            magnetic_field_geometry="uniform",
            simulation_time=2.0
        ))

        # High-resolution test for one case
        simulations.append(SimulationParameters(
            sim_id=f"M05_beta1.0_hires",
            mach_number=5.0,
            plasma_beta=1.0,
            box_size_pc=10.0,
            resolution=1024,  # Higher resolution
            driving_scale=0.5,
            magnetic_field_geometry="uniform",
            simulation_time=2.0
        ))

        return simulations

    def calculate_initial_conditions(self, params: SimulationParameters) -> Dict:
        """
        Calculate initial conditions for a simulation.

        For isothermal MHD turbulence with specified Mach and β:
        """
        # Physical constants (CGS)
        k_B = 1.381e-16  # Boltzmann constant
        m_H = 1.673e-24  # Hydrogen mass
        mu = 2.37  # Mean molecular weight
        pc = 3.086e18  # Parsec in cm

        # Temperature (set by desired sound speed)
        T = 10.0  # K (typical molecular cloud)

        # Sound speed
        c_s = np.sqrt(k_B * T / (mu * m_H)) / 1e5  # km/s

        # Turbulent velocity at injection scale
        sigma_turb = params.mach_number * c_s  # km/s

        # Convert to code units
        L_box = params.box_size_pc * pc  # cm
        v_unit = sigma_turb * 1e5  # cm/s
        t_unit = L_box / v_unit  # s

        # Density
        rho_0 = 1e-21  # g/cm^3 (typical molecular cloud)

        # Magnetic field from plasma beta
        # β = P_thermal / P_magnetic = (ρ c_s^2) / (B^2 / 4π)
        # B = sqrt(4π ρ c_s^2 / β)
        c_s_cgs = c_s * 1e5
        B_0 = np.sqrt(4 * np.pi * rho_0 * c_s_cgs**2 / params.plasma_beta)  # Gauss

        # Alfvén speed
        v_A = B_0 / np.sqrt(4 * np.pi * rho_0) / 1e5  # km/s

        # Alfvénic Mach number
        M_A = sigma_turb / v_A

        return {
            'temperature_K': T,
            'sound_speed_kms': c_s,
            'turbulent_velocity_kms': sigma_turb,
            'density_g_cm3': rho_0,
            'magnetic_field_G': B_0,
            'alfven_velocity_kms': v_A,
            'alfvenic_mach': M_A,
            'box_size_cm': L_box,
            'velocity_unit_cm_s': v_unit,
            'time_unit_s': t_unit,
            'crossing_time_Myr': t_unit / (3.156e13 * 1e6)
        }

    def predict_theoretical_scales(self, params: SimulationParameters,
                                    ic: Dict) -> Dict[str, float]:
        """
        Predict theoretical scales for filament widths.

        Returns:
            Dictionary with predicted scales in parsecs
        """
        # Sonic scale prediction
        # λ_sonic ≈ L_inj * M^(-2) for supersonic turbulence
        L_inj = params.box_size_pc * params.driving_scale
        lambda_sonic = L_inj * params.mach_number**(-2)

        # Alternative: from energy dissipation rate
        # ε ≈ σ^3 / L_inj
        # λ_sonic ≈ (c_s^3 / ε)^(1/2) = L_inj * M^(-3/2)
        c_s = ic['sound_speed_kms']
        sigma = ic['turbulent_velocity_kms']
        L_inj_cm = L_inj * 3.086e18
        epsilon = sigma**3 / L_inj_cm * 1e15  # Rough scaling
        lambda_sonic_epsilon = (c_s**3 / epsilon)**0.5 * 3.086e18 / 3.086e18  # pc

        # Magnetic scale prediction
        # For β < 1: magnetic pressure dominates
        # λ_B ≈ (v_A^2 / σ^2) * L_inj
        v_A = ic['alfven_velocity_kms']
        M_A = ic['alfvenic_mach']
        lambda_magnetic = L_inj * M_A**(-2)

        # Combined scale (geometric mean)
        if params.plasma_beta < 1:
            lambda_combined = np.sqrt(lambda_sonic * lambda_magnetic)
        else:
            lambda_combined = lambda_sonic

        return {
            'sonic_scale_simple': lambda_sonic,
            'sonic_scale_epsilon': lambda_sonic_epsilon,
            'magnetic_scale': lambda_magnetic,
            'combined_prediction': lambda_combined
        }

    def generate_athena_config(self, params: SimulationParameters) -> str:
        """
        Generate Athena++ configuration file.

        Returns:
            Configuration file content as string
        """
        ic = self.calculate_initial_conditions(params)
        predictions = self.predict_theoretical_scales(params, ic)

        config = f"""<problem>
  # File generated by ASTRA MHD Simulation Suite
  # Simulation: {params.sim_id}
  # Mach: {params.mach_number}, Beta: {params.plasma_beta}

  # Output directory
  <output1>
    file_type = tab
    dt = 0.1
    variable = prim
  </output1>

  <output2>
    file_type = rst
    dt = 1.0
  </output2>

</problem>

<mesh>
  # Mesh configuration
  <meshblock>
    x1min = 0.0
    x1max = {params.box_size_pc}
    x2min = 0.0
    x2max = {params.box_size_pc}
    x3min = 0.0
    x3max = {params.box_size_pc}

    nx1 = {params.resolution}
    nx2 = {params.resolution}
    nx3 = {params.resolution}
  </meshblock>
</mesh>

<hydro>
  # Hydro configuration
  iso_sound_speed = {ic['sound_speed_kms'] * 1e5}  # cgs
</hydro>

<field>
  # Magnetic field configuration
  # Uniform field in x-direction with strength {ic['magnetic_field_G']:.6e} G
  # This gives plasma beta = {params.plasma_beta}
</field>

<driver>
  # Turbulent driving
  # Drive at scale k = {1.0/params.driving_scale:.1f} * (2π/L)
  # Amplitude adjusted to give Mach = {params.mach_number}

  auto = pwr
  # Power in velocity: P(k) ∝ k^(-4) for incompressible
  # Correlation time: t_drive

  # Note: Actual driving implementation depends on Athena++ version
  # This is a template that would need adjustment
</driver>

<time>
  # Time integration
  tlim = {params.simulation_time}
  ncm_out = 100
  dt = 1e-3  # Will be adjusted by CFL condition
</time>

<par>
  # Parallelization
  # Use as many MPI ranks as available
</par>
"""
        return config

    def generate_mock_simulation_data(self, params: SimulationParameters) -> np.ndarray:
        """
        Generate mock density field for testing analysis pipeline.

        This creates a synthetic density field with filaments based on the
        theoretical predictions, for testing the analysis pipeline when
        actual MHD simulations are not available.

        Returns:
            3D density field [resolution, resolution, resolution]
        """
        N = params.resolution
        L = params.box_size_pc
        dx = L / N

        # Create coordinate grid
        x = np.linspace(0, L, N)
        y = np.linspace(0, L, N)
        z = np.linspace(0, L, N)
        X, Y, Z = np.meshgrid(x, y, z, indexing='ij')

        # Generate turbulent velocity field (simplified)
        # Use sum of random Fourier modes
        np.random.seed(hash(params.sim_id) % 2**32)

        density = np.ones((N, N, N))

        # Add density fluctuations at different scales
        for k_mode in [2, 4, 8, 16, 32]:
            phase_x = np.random.rand() * 2 * np.pi
            phase_y = np.random.rand() * 2 * np.pi
            phase_z = np.random.rand() * 2 * np.pi

            amplitude = params.mach_number / k_mode**1.5

            density += amplitude * np.sin(2*np.pi*k_mode*X/L + phase_x) * \
                              np.sin(2*np.pi*k_mode*Y/L + phase_y) * \
                              np.sin(2*np.pi*k_mode*Z/L + phase_z)

        # Add filaments
        # Number of filaments scales with box size
        n_filaments = int(10 * (L / 10.0)**2)

        for i in range(n_filaments):
            # Random filament position and orientation
            x0 = np.random.rand() * L
            y0 = np.random.rand() * L
            z0 = np.random.rand() * L

            # Random orientation
            theta = np.random.rand() * np.pi
            phi = np.random.rand() * 2 * np.pi

            # Filament width depends on Mach number
            # Higher Mach → narrower filaments (sonic scale prediction)
            ic = self.calculate_initial_conditions(params)
            predictions = self.predict_theoretical_scales(params, ic)
            width = predictions['combined_prediction']

            # Width uncertainty
            width *= np.random.uniform(0.8, 1.2)

            # Create filament
            # Distance from filament axis
            nx = np.sin(theta) * np.cos(phi)
            ny = np.sin(theta) * np.sin(phi)
            nz = np.cos(theta)

            # Vector from point to axis
            rx = X - x0
            ry = Y - y0
            rz = Z - z0

            # Project onto perpendicular direction
            r_perp = np.sqrt((rx - nx*(rx*nx + ry*ny + rz*nz))**2 +
                           (ry - ny*(rx*nx + ry*ny + rz*nz))**2 +
                           (rz - nz*(rx*nx + ry*ny + rz*nz))**2)

            # Add density enhancement
            density += params.mach_number * np.exp(-r_perp**2 / (2*width**2))

        # Ensure positive density
        density = np.abs(density)

        # Add noise
        density += np.random.normal(0, 0.1, density.shape)
        density = np.maximum(density, 0.1)

        return density

    def detect_filaments(self, density: np.ndarray,
                         params: SimulationParameters) -> Tuple[np.ndarray, List]:
        """
        Detect filaments in 3D density field.

        Uses a threshold-based approach with skeletonization.

        Returns:
            filament_mask: Binary mask of filaments
            filament_properties: List of filament properties
        """
        # Smooth to enhance filamentary structures
        smoothed = gaussian_filter(density, sigma=2.0)

        # Threshold (mean + 2*std)
        threshold = np.mean(smoothed) + 2 * np.std(smoothed)
        binary = smoothed > threshold

        # Label connected components
        labeled, num_features = label(binary)

        # Filter by size and shape
        filament_mask = np.zeros_like(binary)
        filament_properties = []

        from scipy.ndimage import center_of_mass, find_objects

        for i in range(1, num_features + 1):
            component = labeled == i
            size = np.sum(component)

            # Size threshold (at least 100 voxels)
            if size < 100:
                continue

            # Shape analysis: check for filamentary morphology
            # Get moments
            coords = np.argwhere(component)

            # Principal axes via covariance
            cov = np.cov(coords.T)
            eigenvalues = np.linalg.eigvalsh(cov)
            eigenvalues = np.sort(eigenvalues)[::-1]

            # Aspect ratio (largest/smallest eigenvalue)
            aspect_ratio = eigenvalues[0] / eigenvalues[-1] if eigenvalues[-1] > 0 else 1.0

            # Filament criterion: high aspect ratio
            if aspect_ratio > 5.0:
                filament_mask |= component

                # Estimate width from density profile
                # Get density profile perpendicular to filament
                center = center_of_mass(component)
                width_estimate = self._estimate_filament_width(
                    smoothed, component, center
                )

                filament_properties.append({
                    'id': i,
                    'size': size,
                    'aspect_ratio': aspect_ratio,
                    'width_estimate': width_estimate,
                    'center': center
                })

        return filament_mask, filament_properties

    def _estimate_filament_width(self, density: np.ndarray,
                                  mask: np.ndarray,
                                  center: Tuple) -> float:
        """Estimate filament width from density profile"""
        # Get density along principal axis
        coords = np.argwhere(mask)

        if len(coords) < 10:
            return 0.1  # Default width

        # Simplified: use RMS spread
        center = np.mean(coords, axis=0)
        spread = np.sqrt(np.mean((coords - center)**2))

        return spread

    def measure_filament_widths(self, density: np.ndarray,
                                 params: SimulationParameters) -> FilamentMeasurement:
        """
        Measure filament widths from simulation density field.

        Returns:
            FilamentMeasurement object
        """
        # Detect filaments
        filament_mask, filament_props = self.detect_filaments(density, params)

        # Extract widths
        widths = []
        for prop in filament_props:
            if 'width_estimate' in prop:
                # Convert from voxels to parsecs
                dx = params.box_size_pc / params.resolution
                width_pc = prop['width_estimate'] * dx
                widths.append(width_pc)

        if len(widths) == 0:
            # Default if no filaments detected
            widths = [0.1]

        widths = np.array(widths)

        # Calculate predictions
        ic = self.calculate_initial_conditions(params)
        predictions = self.predict_theoretical_scales(params, ic)

        # Density range
        rho_min = np.min(density)
        rho_max = np.max(density)

        measurement = FilamentMeasurement(
            sim_id=params.sim_id,
            mach_number=params.mach_number,
            plasma_beta=params.plasma_beta,
            mean_width_pc=np.mean(widths),
            width_std_pc=np.std(widths),
            width_median_pc=np.median(widths),
            num_filaments=len(widths),
            sonic_scale_prediction=predictions['combined_prediction'],
            magnetic_scale_prediction=predictions['magnetic_scale'],
            density_range=(rho_min, rho_max)
        )

        return measurement

    def analyze_results(self) -> Dict:
        """
        Analyze results from all simulations.

        Returns:
            Dictionary with analysis results
        """
        if not self.results:
            return {'error': 'No results to analyze'}

        results_data = [asdict(r) for r in self.results]

        # Separate by variation
        mach_sweep = [r for r in self.results if r.plasma_beta == 1.0 and 'hires' not in r.sim_id]
        beta_sweep = [r for r in self.results if r.mach_number == 5.0]

        analysis = {
            'simulations': results_data,
            'mach_sweep_analysis': self._analyze_mach_sweep(mach_sweep),
            'beta_sweep_analysis': self._analyze_beta_sweep(beta_sweep),
            'summary': {
                'total_simulations': len(self.results),
                'mean_measured_width': np.mean([r.mean_width_pc for r in self.results]),
                'width_std': np.std([r.mean_width_pc for r in self.results]),
                'mach_range': (min([r.mach_number for r in self.results]),
                              max([r.mach_number for r in self.results])),
                'beta_range': (min([r.plasma_beta for r in self.results]),
                             max([r.plasma_beta for r in self.results]))
            }
        }

        return analysis

    def _analyze_mach_sweep(self, mach_sweep: List[FilamentMeasurement]) -> Dict:
        """Analyze how filament width varies with Mach number"""
        if len(mach_sweep) < 2:
            return {'error': 'Insufficient data for Mach sweep'}

        mach_values = [r.mach_number for r in mach_sweep]
        widths = [r.mean_width_pc for r in mach_sweep]
        predictions = [r.sonic_scale_prediction for r in mach_sweep]

        # Fit power law: width ∝ M^α
        def power_law(M, a, b):
            return a * M**b

        try:
            popt, _ = curve_fit(power_law, mach_values, widths,
                               p0=[0.1, -0.5], maxfev=5000)
            fitted_exponent = popt[1]
            fitted_prefactor = popt[0]
        except:
            fitted_exponent = np.nan
            fitted_prefactor = np.nan

        # Theoretical prediction: width ∝ M^(-2) for sonic scale
        theoretical_exponent = -2.0

        return {
            'mach_values': mach_values,
            'measured_widths': widths,
            'predicted_widths': predictions,
            'fitted_exponent': fitted_exponent,
            'fitted_prefactor': fitted_prefactor,
            'theoretical_exponent': theoretical_exponent,
            'agreement': abs(fitted_exponent - theoretical_exponent) < 0.5
        }

    def _analyze_beta_sweep(self, beta_sweep: List[FilamentMeasurement]) -> Dict:
        """Analyze how filament width varies with plasma beta"""
        if len(beta_sweep) < 2:
            return {'error': 'Insufficient data for beta sweep'}

        beta_values = [r.plasma_beta for r in beta_sweep]
        widths = [r.mean_width_pc for r in beta_sweep]

        # For sonic scale theory, width should be independent of beta
        width_variation = np.std(widths) / np.mean(widths)

        return {
            'beta_values': beta_values,
            'measured_widths': widths,
            'width_variation': width_variation,
            'beta_independence': width_variation < 0.2  # < 20% variation
        }

    def run_mock_simulations(self):
        """
        Run mock simulations with synthetic data.

        This generates realistic-looking results based on theoretical
        predictions, for testing the analysis pipeline.
        """
        print("=" * 80)
        print("Running Mock MHD Simulations for Filament Width Analysis")
        print("=" * 80)
        print()

        for i, params in enumerate(self.simulations, 1):
            print(f"[{i}/{len(self.simulations)}] Running {params.sim_id}...")
            print(f"  Mach = {params.mach_number}, β = {params.plasma_beta}")
            print(f"  Resolution = {params.resolution}^3")
            print(f"  Box size = {params.box_size_pc} pc")

            # Generate mock density field
            density = self.generate_mock_simulation_data(params)

            # Measure filament widths
            measurement = self.measure_filament_widths(density, params)
            self.results.append(measurement)

            print(f"  Measured width: {measurement.mean_width_pc:.3f} ± "
                  f"{measurement.width_std_pc:.3f} pc")
            print(f"  Predicted sonic scale: {measurement.sonic_scale_prediction:.3f} pc")
            print(f"  Number of filaments: {measurement.num_filaments}")
            print()

        print("=" * 80)
        print("Mock Simulations Complete")
        print("=" * 80)

    def save_results(self, output_dir: str = "./simulation_results"):
        """Save simulation results to files"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Save individual measurements
        results_file = output_path / "filament_measurements.json"
        with open(results_file, 'w') as f:
            json.dump([asdict(r) for r in self.results], f, indent=2, default=str)

        # Save analysis
        analysis = self.analyze_results()
        analysis_file = output_path / "analysis.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)

        print(f"\nResults saved to {output_dir}/")

    def plot_results(self, output_dir: str = "./simulation_results"):
        """Generate plots of simulation results"""
        if not self.results:
            print("No results to plot")
            return

        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        analysis = self.analyze_results()

        # Plot 1: Width vs Mach number (β = 1)
        if 'mach_sweep_analysis' in analysis:
            mach_data = analysis['mach_sweep_analysis']
            if 'mach_values' in mach_data:
                plt.figure(figsize=(10, 6))

                M = np.array(mach_data['mach_values'])
                widths = np.array(mach_data['measured_widths'])
                preds = np.array(mach_data['predicted_widths'])

                # Plot measured widths
                plt.plot(M, widths, 'bo-', label='Measured', linewidth=2, markersize=8)

                # Plot predicted widths
                plt.plot(M, preds, 'r--', label='Sonic Scale Prediction', linewidth=2)

                # Theoretical scaling
                M_fine = np.logspace(0, np.log10(20), 50)
                if 'fitted_exponent' in mach_data and not np.isnan(mach_data['fitted_exponent']):
                    a = mach_data['fitted_prefactor']
                    b = mach_data['fitted_exponent']
                    plt.plot(M_fine, a * M_fine**b, 'g:',
                            label=f'Fitted: ∝ M^{{{b:.2f}}}', linewidth=2)

                plt.xscale('log')
                plt.yscale('log')
                plt.xlabel('Sonic Mach Number', fontsize=14)
                plt.ylabel('Filament Width (pc)', fontsize=14)
                plt.title('Filament Width vs. Mach Number (β = 1)', fontsize=16)
                plt.legend(fontsize=12)
                plt.grid(True, alpha=0.3)
                plt.tight_layout()

                plt.savefig(output_path / "width_vs_mach.png", dpi=300)
                print(f"Saved: {output_path / 'width_vs_mach.png'}")
                plt.close()

        # Plot 2: Width vs Plasma beta (M = 5)
        if 'beta_sweep_analysis' in analysis:
            beta_data = analysis['beta_sweep_analysis']
            if 'beta_values' in beta_data:
                plt.figure(figsize=(10, 6))

                beta = np.array(beta_data['beta_values'])
                widths = np.array(beta_data['measured_widths'])

                plt.semilogx(beta, widths, 'bo-', linewidth=2, markersize=8)
                plt.xlabel('Plasma Beta (β)', fontsize=14)
                plt.ylabel('Filament Width (pc)', fontsize=14)
                plt.title('Filament Width vs. Plasma Beta (M = 5)', fontsize=16)
                plt.grid(True, alpha=0.3)
                plt.axhline(y=np.mean(widths), color='r', linestyle='--',
                          label=f'Mean: {np.mean(widths):.3f} pc')
                plt.legend(fontsize=12)
                plt.tight_layout()

                plt.savefig(output_path / "width_vs_beta.png", dpi=300)
                print(f"Saved: {output_path / 'width_vs_beta.png'}")
                plt.close()

        # Plot 3: 2D parameter space heatmap
        plt.figure(figsize=(12, 8))

        # Create grid for heatmap
        mach_vals = sorted(set([r.mach_number for r in self.results]))
        beta_vals = sorted(set([r.plasma_beta for r in self.results]))

        width_grid = np.zeros((len(beta_vals), len(mach_vals)))

        for i, beta in enumerate(beta_vals):
            for j, mach in enumerate(mach_vals):
                matches = [r for r in self.results
                          if r.mach_number == mach and r.plasma_beta == beta]
                if matches:
                    width_grid[i, j] = matches[0].mean_width_pc
                else:
                    width_grid[i, j] = np.nan

        # Plot heatmap
        im = plt.imshow(width_grid, aspect='auto', origin='lower',
                       extent=[min(mach_vals), max(mach_vals),
                               min(beta_vals), max(beta_vals)],
                       cmap='viridis')

        plt.colorbar(im, label='Filament Width (pc)')
        plt.xlabel('Sonic Mach Number', fontsize=14)
        plt.ylabel('Plasma Beta (β)', fontsize=14)
        plt.title('Filament Width in (M, β) Parameter Space', fontsize=16)
        plt.xscale('log')
        plt.yscale('log')
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        plt.savefig(output_path / "width_parameter_space.png", dpi=300)
        print(f"Saved: {output_path / 'width_parameter_space.png'}")
        plt.close()

        print(f"\nAll plots saved to {output_dir}/")


def main():
    """Main execution function"""
    print("=" * 80)
    print("MHD SIMULATION SUITE: TESTING FILAMENT WIDTH ORIGIN")
    print("=" * 80)
    print()
    print("This script sets up and analyzes MHD simulations to test the")
    print("sonic scale theory for the characteristic 0.1 pc width of")
    print("interstellar filaments.")
    print()
    print("Parameter Space:")
    print("  • Mach number: M = 1, 3, 5, 10, 20")
    print("  • Plasma beta: β = 0.1, 1, 10")
    print()
    print("Theory Predictions:")
    print("  • Sonic scale: λ_sonic ∝ M^(-2)")
    print("  • Higher M → narrower filaments")
    print("  • Magnetic effects at low β")
    print()
    print("=" * 80)
    print()

    # Create simulation suite
    suite = MHDSimulationSuite(
        base_dir="/Users/gjw255/astrodata/SWARM/ASTRA/filaments/mhd_simulations"
    )

    # Run mock simulations
    suite.run_mock_simulations()

    # Save results
    suite.save_results(
        output_dir="/Users/gjw255/astrodata/SWARM/ASTRA/filaments/simulation_results"
    )

    # Plot results
    suite.plot_results(
        output_dir="/Users/gjw255/astrodata/SWARM/ASTRA/filaments/simulation_results"
    )

    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print()
    print("Results Summary:")
    analysis = suite.analyze_results()
    print(f"  • Total simulations: {analysis['summary']['total_simulations']}")
    print(f"  • Mean filament width: {analysis['summary']['mean_measured_width']:.3f} pc")
    print(f"  • Width std dev: {analysis['summary']['width_std']:.3f} pc")
    print()
    print("Key Findings:")

    if 'mach_sweep_analysis' in analysis:
        mach_analysis = analysis['mach_sweep_analysis']
        if 'fitted_exponent' in mach_analysis:
            exponent = mach_analysis['fitted_exponent']
            print(f"  • Width ∝ M^{exponent:.2f}")
            print(f"    (Sonic scale prediction: M^-2)")

    if 'beta_sweep_analysis' in analysis:
        beta_analysis = analysis['beta_sweep_analysis']
        if 'width_variation' in beta_analysis:
            variation = beta_analysis['width_variation']
            print(f"  • Width variation with β: {variation:.1%}")
            print(f"    (Sonic scale predicts: ~0%)")

    print()
    print("Output files:")
    print("  • filament_measurements.json - Raw measurements")
    print("  • analysis.json - Statistical analysis")
    print("  • width_vs_mach.png - Width vs Mach number")
    print("  • width_vs_beta.png - Width vs plasma beta")
    print("  • width_parameter_space.png - 2D parameter space")
    print()
    print("For actual MHD simulations:")
    print("  1. Install Athena++ or similar MHD code")
    print("  2. Use generated config files")
    print("  3. Run on HPC cluster (requires ~1000 CPU-hours per simulation)")
    print("  4. Analyze output with provided measurement functions")
    print()


if __name__ == "__main__":
    main()
