#!/usr/bin/env python3
"""
Batch Analysis Script for Sub-Isothermal Perpendicular Field Campaign

Processes all 72 simulations and aggregates results into a single database.
Generates summary plots and mixture calculations.

Usage:
    python batch_analysis.py --sim_root <simulation_root_directory> --output_dir <analysis_output_directory>
"""

import os
import sys
import argparse
import numpy as np
import pandas as pd
from pathlib import Path
import logging
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

# Import the filament analyzer
from analyze_filament import FilamentAnalyzer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class BatchAnalyzer:
    """Analyze multiple simulations and aggregate results"""

    def __init__(self, sim_root, output_dir):
        self.sim_root = Path(sim_root)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.results_database = []
        self.simulation_params = self._load_simulation_parameters()

    def _load_simulation_parameters(self):
        """Load simulation parameters from CSV"""

        param_file = self.sim_root / "simulation_parameters.csv"

        if param_file.exists():
            df = pd.read_csv(param_file)
            logger.info(f"Loaded {len(df)} simulation parameter sets")
            return df
        else:
            logger.warning(f"Parameter file not found: {param_file}")
            return None

    def find_simulations(self):
        """Find all completed simulation directories"""

        # Look for directories containing simulation outputs
        sim_dirs = []

        for item in self.sim_root.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                # Check if directory contains output files
                output_files = list(item.glob("*.hst")) + list(item.glob("*.vtk")) + list(item.glob("*.rst"))
                if output_files:
                    sim_dirs.append(item)

        logger.info(f"Found {len(sim_dirs)} completed simulations")
        return sim_dirs

    def analyze_simulation(self, sim_dir):
        """Analyze a single simulation"""

        analyzer = FilamentAnalyzer(sim_dir, self.output_dir / sim_dir.name)
        success = analyzer.run_analysis()

        if success:
            # Merge with simulation parameters
            result_row = analyzer.results.copy()

            if self.simulation_params is not None:
                sim_id = sim_dir.name
                param_row = self.simulation_params[self.simulation_params['sim_id'] == sim_id]

                if not param_row.empty:
                    for col in param_row.columns:
                        if col != 'sim_id':
                            result_row[col] = param_row[col].values[0]

            return result_row
        else:
            logger.warning(f"Analysis failed for {sim_dir.name}")
            return None

    def run_batch_analysis(self):
        """Analyze all simulations"""

        logger.info("Starting batch analysis")

        sim_dirs = self.find_simulations()

        for i, sim_dir in enumerate(sim_dirs):
            logger.info(f"Processing simulation {i+1}/{len(sim_dirs)}: {sim_dir.name}")

            result = self.analyze_simulation(sim_dir)

            if result is not None:
                self.results_database.append(result)

        logger.info(f"Batch analysis complete: {len(self.results_database)} simulations analyzed")

        # Save results database
        self.save_database()

        # Generate summary plots
        self.generate_summary_plots()

        # Compute mixture calculation
        self.compute_mixture_calculation()

    def save_database(self):
        """Save results database to CSV"""

        if not self.results_database:
            logger.warning("No results to save")
            return

        df = pd.DataFrame(self.results_database)

        # Save full database
        db_file = self.output_dir / "campaign_results_database.csv"
        df.to_csv(db_file, index=False)
        logger.info(f"Results database saved to {db_file}")

        # Save summary statistics
        summary_file = self.output_dir / "campaign_summary.txt"
        with open(summary_file, 'w') as f:
            f.write("Sub-Isothermal Perpendicular Field Campaign - Summary\n")
            f.write("="*60 + "\n\n")
            f.write(f"Analysis timestamp: {datetime.now().isoformat()}\n")
            f.write(f"Total simulations analyzed: {len(df)}\n\n")

            # Classification breakdown
            f.write("Classification Breakdown:\n")
            for cls in ['FRAG', 'STABLE_PARTIAL', 'FLAT_PROFILE']:
                count = len(df[df['classification'] == cls]) if 'classification' in df.columns else 0
                f.write(f"  {cls}: {count}\n")

            f.write("\nλ/W Statistics:\n")
            if 'lambda_W' in df.columns:
                lambda_W = df['lambda_W'].dropna()
                f.write(f"  Mean: {lambda_W.mean():.3f}\n")
                f.write(f"  Median: {lambda_W.median():.3f}\n")
                f.write(f"  Std: {lambda_W.std():.3f}\n")
                f.write(f"  Range: [{lambda_W.min():.3f}, {lambda_W.max():.3f}]\n")

        logger.info(f"Summary saved to {summary_file}")

    def generate_summary_plots(self):
        """Generate summary analysis plots"""

        if not self.results_database:
            logger.warning("No results for plotting")
            return

        df = pd.DataFrame(self.results_database)

        # Set up plotting style
        sns.set_style("whitegrid")
        plt.rcParams['figure.figsize'] = (12, 8)

        # Plot 1: λ/W vs f for different γ values
        if 'lambda_W' in df.columns and 'f' in df.columns and 'gamma' in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))

            for gamma_val in sorted(df['gamma'].unique()):
                gamma_df = df[df['gamma'] == gamma_val]
                ax.scatter(gamma_df['f'], gamma_df['lambda_W'],
                          label=f'γ = {gamma_val}', alpha=0.7, s=100)

            ax.set_xlabel('Line mass fraction (f)')
            ax.set_ylabel('Fragmentation wavelength (λ/W)')
            ax.set_title('λ/W vs f for Different γ Values (Perpendicular Field)')
            ax.legend()
            ax.grid(True, alpha=0.3)

            plot_file = self.output_dir / "lambda_W_vs_f_by_gamma.png"
            plt.savefig(plot_file, dpi=150, bbox_inches='tight')
            plt.close()
            logger.info(f"Plot saved to {plot_file}")

        # Plot 2: λ/W vs β for different γ values
        if 'lambda_W' in df.columns and 'beta' in df.columns and 'gamma' in df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))

            for gamma_val in sorted(df['gamma'].unique()):
                gamma_df = df[df['gamma'] == gamma_val]
                ax.scatter(gamma_df['beta'], gamma_df['lambda_W'],
                          label=f'γ = {gamma_val}', alpha=0.7, s=100)

            ax.set_xlabel('Plasma beta (β)')
            ax.set_ylabel('Fragmentation wavelength (λ/W)')
            ax.set_title('λ/W vs β for Different γ Values (Perpendicular Field)')
            ax.legend()
            ax.grid(True, alpha=0.3)

            plot_file = self.output_dir / "lambda_W_vs_beta_by_gamma.png"
            plt.savefig(plot_file, dpi=150, bbox_inches='tight')
            plt.close()
            logger.info(f"Plot saved to {plot_file}")

        # Plot 3: Classification heatmap in (f, β) plane for each γ
        if 'classification' in df.columns and 'f' in df.columns and 'beta' in df.columns:
            for gamma_val in sorted(df['gamma'].unique()):
                gamma_df = df[df['gamma'] == gamma_val]

                # Create classification map
                f_values = sorted(gamma_df['f'].unique())
                beta_values = sorted(gamma_df['beta'].unique())

                class_map = np.zeros((len(beta_values), len(f_values)))

                for i, f_val in enumerate(f_values):
                    for j, beta_val in enumerate(beta_values):
                        subset = gamma_df[(gamma_df['f'] == f_val) & (gamma_df['beta'] == beta_val)]

                        if not subset.empty:
                            # Use first classification found
                            cls = subset['classification'].values[0]

                            # Encode: FRAG=2, STABLE_PARTIAL=1, FLAT_PROFILE=0
                            if cls == 'FRAG':
                                class_map[j, i] = 2
                            elif cls == 'STABLE_PARTIAL':
                                class_map[j, i] = 1
                            else:
                                class_map[j, i] = 0

                fig, ax = plt.subplots(figsize=(10, 8))

                im = ax.imshow(class_map, cmap='RdYlGn', origin='lower',
                              extent=[min(f_values)-0.25, max(f_values)+0.25,
                                     min(beta_values)-0.25, max(beta_values)+0.25])

                ax.set_xlabel('Line mass fraction (f)')
                ax.set_ylabel('Plasma beta (β)')
                ax.set_title(f'Classification Map for γ = {gamma_val} (Perpendicular Field)')

                # Add colorbar
                cbar = plt.colorbar(im, ax=ax)
                cbar.set_label('Classification')
                cbar.set_ticks([0, 1, 2])
                cbar.set_ticklabels(['FLAT_PROFILE', 'STABLE_PARTIAL', 'FRAG'])

                plot_file = self.output_dir / f"classification_map_gamma{gamma_val}.png"
                plt.savefig(plot_file, dpi=150, bbox_inches='tight')
                plt.close()
                logger.info(f"Plot saved to {plot_file}")

    def compute_mixture_calculation(self):
        """
        Compute Planck-weighted mixture calculation.

        This uses the Planck field geometry distribution (90% perpendicular, 10% longitudinal)
        combined with the simulation results to predict ⟨λ/W⟩_Planck.
        """

        if not self.results_database:
            logger.warning("No results for mixture calculation")
            return

        df = pd.DataFrame(self.results_database)

        # For perpendicular field, use results from this campaign
        perp_df = df[df['classification'] == 'FRAG'].copy()

        if perp_df.empty:
            logger.warning("No fragmented simulations for mixture calculation")
            return

        # Compute mean λ/W for perpendicular field
        # Could also compute weighted by f distribution or other parameters
        perp_mean = perp_df['lambda_W'].mean()
        perp_std = perp_df['lambda_W'].std()

        # For longitudinal field, use reference values from isothermal campaign
        # (These would come from previous simulation results)
        long_mean = 3.7  # Reference value from isothermal longitudinal simulations
        long_std = 0.8

        # Planck-weighted mixture: 90% perpendicular, 10% longitudinal
        planck_weighted = 0.9 * perp_mean + 0.1 * long_mean

        # Estimate uncertainty (propagation of error)
        planck_uncertainty = np.sqrt((0.9 * perp_std)**2 + (0.1 * long_std)**2)

        logger.info(f"Planck-weighted prediction: ⟨λ/W⟩_Planck = {planck_weighted:.2f} ± {planck_uncertainty:.2f}")

        # Save mixture calculation
        mixture_file = self.output_dir / "mixture_calculation.txt"
        with open(mixture_file, 'w') as f:
            f.write("Planck-Weighted Mixture Calculation\n")
            f.write("="*60 + "\n\n")
            f.write(f"Analysis timestamp: {datetime.now().isoformat()}\n\n")

            f.write("Field Geometry Distribution (Planck Collaboration 2016):\n")
            f.write("  Perpendicular: 90%\n")
            f.write("  Longitudinal: 10%\n\n")

            f.write("Perpendicular Field (This Campaign, γ < 1):\n")
            f.write(f"  Mean λ/W: {perp_mean:.3f}\n")
            f.write(f"  Std λ/W: {perp_std:.3f}\n")
            f.write(f"  N: {len(perp_df)}\n\n")

            f.write("Longitudinal Field (Reference, Isothermal):\n")
            f.write(f"  Mean λ/W: {long_mean:.3f}\n")
            f.write(f"  Std λ/W: {long_std:.3f}\n\n")

            f.write("Planck-Weighted Prediction:\n")
            f.write(f"  ⟨λ/W⟩_Planck = {planck_weighted:.3f} ± {planck_uncertainty:.3f}\n\n")

            f.write("HGBS Measurements (Arzoumanian et al. 2019):\n")
            f.write("  Range: 2.0 - 3.0\n")
            f.write("  Mean: ~2.5\n\n")

            if planck_weighted < 2.0:
                f.write("Conclusion: Planck-weighted prediction is BELOW HGBS range\n")
            elif planck_weighted > 3.0:
                f.write("Conclusion: Planck-weighted prediction is ABOVE HGBS range\n")
            else:
                f.write("Conclusion: Planck-weighted prediction is WITHIN HGBS range\n")

        logger.info(f"Mixture calculation saved to {mixture_file}")


def main():
    parser = argparse.ArgumentParser(description='Batch analysis for sub-isothermal perpendicular campaign')
    parser.add_argument('--sim_root', type=str, required=True, help='Root directory containing all simulations')
    parser.add_argument('--output_dir', type=str, default='./analysis_results', help='Analysis output directory')

    args = parser.parse_args()

    # Run batch analysis
    analyzer = BatchAnalyzer(args.sim_root, args.output_dir)
    analyzer.run_batch_analysis()

    logger.info("Batch analysis completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
