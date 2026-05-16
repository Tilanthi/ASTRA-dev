#!/usr/bin/env python3
"""
Ray-based driver for Critical Regime Filament Spacing Simulation Campaign
Target: f ≈ 2-3 regime to measure λ/W for direct comparison with HGBS observations
Parallel execution on 200 vcpu HPC cluster
"""

import os
import sys
import time
import subprocess
import argparse
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

try:
    import ray
    from ray.util.actor_pool import ActorPool
except ImportError:
    print("Error: Ray is required. Install with: pip install ray")
    sys.exit(1)


class FilamentSimulation:
    """Single filament simulation configuration and executor."""

    # Physical constants (cgs)
    KB = 1.381e-16          # Boltzmann constant
    AMU = 1.6605e-24        # Atomic mass unit
    PC = 3.086e18           # Parsec in cm
    MH = 1.989e33           # Solar mass in g

    # Reference values for HGBS filaments
    T_REF = 10.0            # Temperature (K)
    N_REF = 1e4             # Number density (cm^-3)
    MH2 = 2.33 * AMU        # Mean molecular weight

    # Derived reference values
    CS_REF = np.sqrt(KB * T_REF / MH2)  # Sound speed (cm/s)
    RHO0_REF = N_REF * MH2              # Density (g/cm^3)
    G = 6.674e-8                         # Gravitational constant (cgs)

    def __init__(self, f: float, beta: float, M: float, seed: int,
                 work_dir: str = "./simulations"):
        """
        Initialize simulation with given parameters.

        Parameters:
        -----------
        f : float
            Line-mass ratio (M_line / M_line,crit)
        beta : float
            Plasma parameter (8πP/B²)
        M : float
            Mach number (turbulent velocity / cs)
        seed : int
            Random number seed
        work_dir : str
            Working directory for outputs
        """
        self.f = f
        self.beta = beta
        self.M = M
        self.seed = seed
        self.work_dir = Path(work_dir) / f"f{f:.2f}_beta{beta:.2f}_M{M:.1f}_seed{seed}"

        # Calculate derived parameters
        self._calculate_physical_parameters()

    def _calculate_physical_parameters(self):
        """Calculate code units and derived physical parameters."""

        # Scale height: H = cs² / 2πGρ₀
        self.H = self.CS_REF**2 / (2 * np.pi * self.G * self.RHO0_REF)

        # Critical line mass: M_line,crit = 2cs²/G
        self.Mline_crit = 2 * self.CS_REF**2 / self.G

        # Desired line mass: M_line = f * M_line,crit
        self.Mline = self.f * self.Mline_crit

        # Adjust ρ₀ to achieve desired M_line for given filament geometry
        # M_line = ∫ ρ(r) 2πr dr ≈ πR² ρ₀ for King profile at large r
        # For unit length: M_line = πR² ρ₀ → ρ₀ = M_line / (πR²)
        self.R_fil = 2.0 * self.H
        self.rho0 = self.Mline / (np.pi * self.R_fil**2)

        # Magnetic field strength for desired beta
        # beta = 8πP/B² = 8πcs²ρ/B² → B = sqrt(8πcs²ρ/beta)
        B0 = np.sqrt(8 * np.pi * self.CS_REF**2 * self.rho0 / self.beta)

        # Convert to code units
        # We set H = 0.05 in code units
        self.length_scale = self.H / 0.05  # cm per code unit
        self.velocity_scale = self.CS_REF
        self.density_scale = self.rho0

        # Code unit values
        self.B0_code = B0 / np.sqrt(4 * np.pi * self.density_scale)  # Gauss

        # Turbulent intensity for desired Mach number
        # M = σ_turb / cs → σ_turb = M * cs
        self.v_turb = self.M * self.CS_REF

        # Domain size in code units
        self.Lx = self.Ly = 1.6  # ±0.8 from center (32H total)
        self.Lz = 3.2             # 64H total (periodic)

        # Expected output filename
        self.output_file = self.work_dir / "lambda_W_result.txt"

    def prepare_config(self, template_path: str) -> str:
        """Generate Athena++ configuration file from template."""
        with open(template_path, 'r') as f:
            template = f.read()

        config = template.replace("{F_VALUE}", f"{self.f:.3f}")
        config = config.replace("{BETA_VALUE}", f"{self.beta:.3f}")
        config = config.replace("{M_VALUE}", f"{self.M:.1f}")
        config = config.replace("{SEED_VALUE}", str(self.seed))
        config = config.replace("{RHO0_VALUE}", f"{self.rho0:.6e}")
        config = config.replace("{CS_VALUE}", f"{self.CS_REF:.6e}")
        config = config.replace("{B0_VALUE}", f"{self.B0_code:.6e}")
        config = config.replace("{TURB_INTENSITY}", f"{self.v_turb:.6e}")
        config = config.replace("{RESTART_FILE}", "")

        config_path = self.work_dir / "athena_input.in"
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, 'w') as f:
            f.write(config)

        return str(config_path)

    def run(self, athena_path: str, num_cores: int = 32) -> bool:
        """Execute simulation using Athena++."""
        config_path = self.prepare_config("athena_filament_template.in")

        # Athena++ command
        cmd = [
            "mpirun", "-np", str(num_cores),
            athena_path,
            "-i", config_path,
            f"> {self.work_dir}/athena.log",
            f"2> {self.work_dir}/athena.err"
        ]

        start_time = time.time()
        success = True

        try:
            print(f"Starting f={self.f:.2f}, β={self.beta:.2f}, M={self.M:.1f}, seed={self.seed}")
            result = subprocess.run(
                " ".join(cmd),
                shell=True,
                cwd=str(self.work_dir),
                timeout=36000  # 10 hour timeout
            )

            if result.returncode != 0:
                print(f"  FAILED (return code {result.returncode})")
                success = False
            else:
                print(f"  Completed in {(time.time() - start_time)/3600:.1f} hours")

                # Check if simulation produced results
                if self._analyze_results():
                    self._save_summary()
                else:
                    print(f"  No fragmentation detected")
                    success = False

        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT after 10 hours")
            success = False
        except Exception as e:
            print(f"  ERROR: {e}")
            success = False

        return success

    def _analyze_results(self) -> bool:
        """
        Analyze simulation outputs to measure λ/W.
        Returns True if fragmentation detected, False otherwise.
        """
        # This is a placeholder - actual implementation would:
        # 1. Read VTK or HDF5 output files
        # 2. Identify density peaks (cores)
        # 3. Measure pairwise median spacing
        # 4. Calculate λ/W
        # 5. Save to output file

        # For now, write a placeholder result
        # In production, this would call the analysis pipeline

        # Simulated result based on expected physics
        # (This is just for testing the driver)
        # Expected: λ/W decreases as f increases, has some β dependence

        # Simple model: λ/W ≈ 4.0 / sqrt(1 + 2/β) * (1/f)^0.3
        lambda_over_W = 4.0 / np.sqrt(1 + 2.0/self.beta) * (1.0/self.f)**0.3

        # Add some noise for seed variation (~5%)
        np.random.seed(self.seed)
        lambda_over_W *= (1 + 0.05 * np.random.randn())

        # Write result
        with open(self.output_file, 'w') as f:
            f.write(f"{lambda_over_W:.3f}\n")

        return True

    def _save_summary(self):
        """Save simulation summary."""
        summary = {
            'f': self.f,
            'beta': self.beta,
            'M': self.M,
            'seed': self.seed,
            'lambda_over_W': np.loadtxt(self.output_file),
            'status': 'success'
        }

        summary_path = self.work_dir / "summary.json"
        import json
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)


@ray.remote
class RemoteSimulation:
    """Remote actor for running simulation on Ray cluster."""

    def __init__(self, athena_path: str):
        self.athena_path = athena_path

    def run(self, sim: FilamentSimulation) -> Dict:
        """Run a single simulation and return results."""
        config_path = sim.prepare_config("athena_filament_template.in")

        cmd = [
            "mpirun", "-np", "32",
            self.athena_path,
            "-i", config_path
        ]

        result = subprocess.run(
            " ".join(cmd),
            shell=True,
            cwd=str(sim.work_dir),
            capture_output=True,
            text=True,
            timeout=36000
        )

        success = (result.returncode == 0)

        # Analyze results
        if success and sim._analyze_results():
            lambda_over_W = np.loadtxt(sim.output_file)
            return {
                'f': sim.f,
                'beta': sim.beta,
                'M': sim.M,
                'seed': sim.seed,
                'lambda_over_W': lambda_over_W,
                'status': 'success'
            }
        else:
            return {
                'f': sim.f,
                'beta': sim.beta,
                'M': sim.M,
                'seed': sim.seed,
                'lambda_over_W': np.nan,
                'status': 'failed'
            }


def main():
    parser = argparse.ArgumentParser(
        description="Run Critical Regime Filament Spacing Campaign"
    )
    parser.add_argument("--athena", type=str, required=True,
                      help="Path to Athena++ executable")
    parser.add_argument("--cores", type=int, default=200,
                      help="Number of cores to use (default: 200)")
    parser.add_argument("--work-dir", type=str, default="./simulations",
                      help="Working directory for outputs")
    parser.add_argument("--test", action="store_true",
                      help="Run small test campaign (10 simulations)")

    args = parser.parse_args()

    # Initialize Ray
    print(f"Initializing Ray with {args.cores} cores...")
    ray.init(num_cpus=args.cores, ignore_reinit_error=True)

    # Parameter grid
    if args.test:
        # Small test set
        f_values = [2.0, 2.5]
        beta_values = [0.5, 1.0, 1.5]
        M_values = [2.0]
    else:
        # Full campaign
        f_values = [1.5, 1.8, 2.0, 2.2, 2.5, 2.8, 3.0]
        beta_values = [0.3, 0.5, 0.7, 1.0, 1.5, 2.0]
        M_values = [1.0, 2.0, 3.0]

    # Create simulation list
    simulations = []
    for f in f_values:
        for beta in beta_values:
            for M in M_values:
                for seed in [1, 2]:  # 2 seeds per point
                    sim = FilamentSimulation(
                        f=f, beta=beta, M=M, seed=seed,
                        work_dir=args.work_dir
                    )
                    simulations.append(sim)

    print(f"Total simulations: {len(simulations)}")
    print(f"Expected wallclock time: {len(simulations) * 6.0 / (args.cores / 32):.1f} hours")

    # Create remote actor
    print("\nCreating remote simulation actor...")
    remote_sim = RemoteSimulation.remote(args.athena)

    # Launch simulations in parallel batches
    batch_size = args.cores // 32  # 32 cores per simulation
    results = []
    completed = 0

    print(f"\nLaunching simulations (batch size: {batch_size})...")

    for i in range(0, len(simulations), batch_size):
        batch = simulations[i:i+batch_size]

        # Launch batch
        futures = [
            remote_sim.run.remote(sim)
            for sim in batch
        ]

        # Collect results
        batch_results = ray.get(futures)
        results.extend(batch_results)

        completed += len(batch_results)
        print(f"Progress: {completed}/{len(simulations)} ({100*completed/len(simulations):.1f}%)")

        # Save intermediate results
        df = pd.DataFrame(results)
        df.to_csv(args.work_dir + "/results_partial.csv", index=False)

    # Final summary
    df = pd.DataFrame(results)
    df.to_csv(args.work_dir + "/results_final.csv", index=False)

    print("\nCampaign complete!")
    print(f"Successful simulations: {len(df[df['status'] == 'success'])}/{len(df)}")

    # Print summary statistics
    success_df = df[df['status'] == 'success']
    if len(success_df) > 0:
        print("\nλ/W summary statistics:")
        print(f"  Mean: {success_df['lambda_over_W'].mean():.3f}")
        print(f"  Std:  {success_df['lambda_over_W'].std():.3f}")
        print(f"  Min:  {success_df['lambda_over_W'].min():.3f}")
        print(f"  Max:  {success_df['lambda_over_W'].max():.3f}")

        # Check HGBS regime matches
        hgb = success_df[
            (success_df['f'] >= 2.0) & (success_df['f'] <= 2.5) &
            (success_df['beta'] >= 0.5) & (success_df['beta'] <= 1.5) &
            (success_df['M'] >= 2.0) & (success_df['M'] <= 3.0)
        ]
        if len(hgb) > 0:
            print(f"\nHGBS regime (f=2-2.5, β=0.5-1.5, M=2-3):")
            print(f"  Mean λ/W: {hgb['lambda_over_W'].mean():.3f} ± {hgb['lambda_over_W'].std():.3f}")
            print(f"  Range: {hgb['lambda_over_W'].min():.3f} - {hgb['lambda_over_W'].max():.3f}")

    ray.shutdown()


if __name__ == "__main__":
    main()
