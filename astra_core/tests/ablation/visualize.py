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
Ablation Study Visualization Tools

Create visualizations and reports from ablation study results.
"""

import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from datetime import datetime


# Color scheme for visualizations
COLORS = {
    "baseline": "#2E7D32",  # Green
    "critical": "#C62828",  # Red
    "moderate": "#F57C00",  # Orange
    "minor": "#1976D2",     # Blue
    "background": "#F5F5F5"
}


class AblationVisualizer:
    """Create visualizations for ablation study results"""

    def __init__(self, results_dir: str = "astra_core/tests/ablation/results"):
        self.results_dir = results_dir
        Path(self.results_dir).mkdir(parents=True, exist_ok=True)

    def load_results(self, filename: str) -> Dict[str, Any]:
        """Load ablation results from JSON file"""
        filepath = os.path.join(self.results_dir, filename)

        with open(filepath, 'r') as f:
            return json.load(f)

    def create_component_importance_chart(self, results: Dict[str, Any],
                                         output_file: Optional[str] = None):
        """Create bar chart showing component importance"""
        # Extract data
        ablations = []
        degradations = []

        for name, data in results.items():
            ablations.append(name.replace("_", " ").title())
            degradations.append(data["percent_degradation"])

        # Sort by degradation
        sorted_indices = np.argsort(degradations)[::-1]
        ablations = [ablations[i] for i in sorted_indices]
        degradations = [degradations[i] for i in sorted_indices]

        # Create color mapping based on degradation
        colors = []
        for deg in degradations:
            if deg > 30:
                colors.append(COLORS["critical"])
            elif deg > 15:
                colors.append(COLORS["moderate"])
            else:
                colors.append(COLORS["minor"])

        # Create figure
        fig, ax = plt.subplots(figsize=(12, 8))

        bars = ax.barh(ablations, degradations, color=colors, edgecolor='black', linewidth=0.5)

        # Customize
        ax.set_xlabel('Performance Degradation (%)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Ablated Component', fontsize=12, fontweight='bold')
        ax.set_title('ASTRA Component Importance Analysis\n(Performance Degradation When Removed)',
                    fontsize=14, fontweight='bold')
        ax.set_xlim(0, max(degradations) * 1.1)
        ax.invert_yaxis()

        # Add value labels
        for i, (bar, deg) in enumerate(zip(bars, degradations)):
            ax.text(deg + 0.5, bar.get_y() + bar.get_height()/2,
                   f'{deg:.1f}%',
                   va='center', fontsize=10)

        # Add legend
        legend_elements = [
            mpatches.Patch(color=COLORS["critical"], label='Critical (>30%)'),
            mpatches.Patch(color=COLORS["moderate"], label='Moderate (15-30%)'),
            mpatches.Patch(color=COLORS["minor"], label='Minor (<15%)')
        ]
        ax.legend(handles=legend_elements, loc='lower right')

        plt.tight_layout()

        # Save
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"component_importance_{timestamp}.png"

        filepath = os.path.join(self.results_dir, output_file)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Component importance chart saved to: {filepath}")
        return filepath

    def create_performance_degradation_graph(self, results: Dict[str, Any],
                                            output_file: Optional[str] = None):
        """Create line graph showing performance degradation"""
        # Extract data
        ablations = []
        baseline_scores = []
        ablated_scores = []
        degradations = []

        for name, data in results.items():
            ablations.append(name.replace("_", " ").title())
            baseline_scores.append(data["full_system_score"])
            ablated_scores.append(data["ablated_system_score"])
            degradations.append(data["percent_degradation"])

        # Sort by degradation
        sorted_indices = np.argsort(degradations)
        ablations = [ablations[i] for i in sorted_indices]
        baseline_scores = [baseline_scores[i] for i in sorted_indices]
        ablated_scores = [ablated_scores[i] for i in sorted_indices]

        # Create figure
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

        # Top plot: Score comparison
        x = np.arange(len(ablations))
        width = 0.35

        ax1.bar(x - width/2, baseline_scores, width, label='Full System',
               color=COLORS["baseline"], edgecolor='black', linewidth=0.5)
        ax1.bar(x + width/2, ablated_scores, width, label='Ablated System',
               color=COLORS["critical"], edgecolor='black', linewidth=0.5)

        ax1.set_ylabel('Overall Score', fontsize=12, fontweight='bold')
        ax1.set_title('ASTRA Ablation Study: Performance Comparison',
                     fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(ablations, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)

        # Bottom plot: Degradation percentage
        colors = [COLORS["critical"] if d > 30 else
                 COLORS["moderate"] if d > 15 else
                 COLORS["minor"] for d in degradations]

        ax2.plot(ablations, degradations, marker='o', linewidth=2,
                color=COLORS["critical"], markersize=8)
        ax2.fill_between(ablations, degradations, alpha=0.3, color=COLORS["critical"])

        ax2.set_xlabel('Ablated Component', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Performance Degradation (%)', fontsize=12, fontweight='bold')
        ax2.set_xticklabels(ablations, rotation=45, ha='right')
        ax2.grid(alpha=0.3)

        # Add threshold lines
        ax2.axhline(y=30, color='red', linestyle='--', alpha=0.5, label='Critical Threshold')
        ax2.axhline(y=15, color='orange', linestyle='--', alpha=0.5, label='Moderate Threshold')
        ax2.legend()

        plt.tight_layout()

        # Save
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"performance_degradation_{timestamp}.png"

        filepath = os.path.join(self.results_dir, output_file)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Performance degradation graph saved to: {filepath}")
        return filepath

    def create_metric_comparison_heatmap(self, results: Dict[str, Any],
                                        output_file: Optional[str] = None):
        """Create heatmap comparing metrics across ablations"""
        # Extract metric comparisons
        ablations = list(results.keys())

        # Get all unique metrics
        all_metrics = set()
        for data in results.values():
            all_metrics.update(data.get("metric_comparisons", {}).keys())

        all_metrics = sorted(list(all_metrics))

        # Create matrix
        matrix = np.zeros((len(all_metrics), len(ablations)))

        for j, ablation in enumerate(ablations):
            metric_comp = results[ablation].get("metric_comparisons", {})
            for i, metric in enumerate(all_metrics):
                if metric in metric_comp:
                    matrix[i, j] = metric_comp[metric]["percent_delta"]
                else:
                    matrix[i, j] = 0

        # Create figure
        fig, ax = plt.subplots(figsize=(16, 10))

        # Plot heatmap
        im = ax.imshow(matrix, cmap='RdYlGn_r', aspect='auto')

        # Set ticks
        ax.set_xticks(np.arange(len(ablations)))
        ax.set_yticks(np.arange(len(all_metrics)))
        ax.set_xticklabels([a.replace("_", " ").title() for a in ablations], rotation=45, ha='right')
        ax.set_yticklabels([m.replace("_", " ").title() for m in all_metrics])

        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Performance Change (%)', rotation=270, labelpad=20, fontsize=11)

        # Add text annotations
        for i in range(len(all_metrics)):
            for j in range(len(ablations)):
                text = ax.text(j, i, f'{matrix[i, j]:.1f}',
                             ha="center", va="center", color="black", fontsize=8)

        ax.set_title('ASTRA Ablation Study: Metric Comparison Heatmap',
                    fontsize=14, fontweight='bold')
        ax.set_xlabel('Ablated Component', fontsize=12, fontweight='bold')
        ax.set_ylabel('Evaluation Metric', fontsize=12, fontweight='bold')

        plt.tight_layout()

        # Save
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"metric_heatmap_{timestamp}.png"

        filepath = os.path.join(self.results_dir, output_file)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Metric comparison heatmap saved to: {filepath}")
        return filepath

    def create_radar_chart(self, results: Dict[str, Any],
                          ablations_to_show: Optional[List[str]] = None,
                          output_file: Optional[str] = None):
        """Create radar chart showing performance across metric categories"""
        # Select ablations to show
        if ablations_to_show is None:
            # Show baseline + top 3 degradations
            sorted_ablations = sorted(results.items(),
                                     key=lambda x: x[1]["percent_degradation"],
                                     reverse=True)
            ablations_to_show = ["full_system"] + [a[0] for a in sorted_ablations[:3]]

        # Extract metric categories
        categories = [
            "Hypothesis Generation",
            "Scientific Accuracy",
            "Reasoning Quality",
            "Cross-Domain Synthesis",
            "Efficiency",
            "Robustness"
        ]

        # Prepare data for each ablation
        data_by_ablation = {}
        for ablation_name in ablations_to_show:
            if ablation_name not in results:
                continue

            metric_comp = results[ablation_name].get("metric_comparisons", {})

            # Aggregate by category
            category_scores = {cat: [] for cat in categories}

            for metric_name, comp_data in metric_comp.items():
                # Map metric to category
                if "novelty" in metric_name or "feasibility" in metric_name or "specificity" in metric_name:
                    category_scores["Hypothesis Generation"].append(comp_data["ablated"])
                elif "factual" in metric_name or "physics" in metric_name or "citation" in metric_name:
                    category_scores["Scientific Accuracy"].append(comp_data["ablated"])
                elif "logical" in metric_name or "reasoning" in metric_name or "inference" in metric_name:
                    category_scores["Reasoning Quality"].append(comp_data["ablated"])
                elif "domain" in metric_name or "synthesis" in metric_name or "analogy" in metric_name:
                    category_scores["Cross-Domain Synthesis"].append(comp_data["ablated"])
                elif "processing" in metric_name or "memory" in metric_name:
                    category_scores["Efficiency"].append(comp_data["ablated"])
                elif "error" in metric_name or "confidence" in metric_name:
                    category_scores["Robustness"].append(comp_data["ablated"])

            # Average scores for each category
            avg_scores = []
            for cat in categories:
                scores = category_scores[cat]
                avg_scores.append(np.mean(scores) if scores else 0.5)

            data_by_ablation[ablation_name] = avg_scores

        # Create radar chart
        fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(projection='polar'))

        # Number of variables
        N = len(categories)

        # Compute angle for each axis
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]

        # Plot each ablation
        colors = [COLORS["baseline"], COLORS["critical"], COLORS["moderate"], COLORS["minor"]]

        for i, (ablation_name, scores) in enumerate(data_by_ablation.items()):
            scores += scores[:1]  # Complete the circle

            ax.plot(angles, scores, 'o-', linewidth=2,
                   label=ablation_name.replace("_", " ").title(),
                   color=colors[i % len(colors)])
            ax.fill(angles, scores, alpha=0.15, color=colors[i % len(colors)])

        # Add category labels
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=10)

        # Set y-axis limits
        ax.set_ylim(0, 1)
        ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
        ax.set_yticklabels(['0.2', '0.4', '0.6', '0.8', '1.0'], size=8)
        ax.set_ylabel('Score', size=10)

        # Add title and legend
        ax.set_title('ASTRA Ablation Study: Performance by Metric Category',
                    fontsize=14, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))

        plt.tight_layout()

        # Save
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"radar_chart_{timestamp}.png"

        filepath = os.path.join(self.results_dir, output_file)
        plt.savefig(filepath, dpi=300, bbox_inches='tight')
        plt.close()

        print(f"Radar chart saved to: {filepath}")
        return filepath


def generate_all_visualizations(results_file: str,
                                output_dir: Optional[str] = None):
    """Generate all visualizations from ablation results"""
    visualizer = AblationVisualizer(output_dir)

    # Load results
    results = visualizer.load_results(results_file)

    print("\n" + "="*60)
    print("GENERATING ABLATION STUDY VISUALIZATIONS")
    print("="*60)

    # Create visualizations
    visualizer.create_component_importance_chart(results)
    visualizer.create_performance_degradation_graph(results)
    visualizer.create_metric_comparison_heatmap(results)
    visualizer.create_radar_chart(results)

    print("\n" + "="*60)
    print("All visualizations generated successfully!")
    print("="*60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate visualizations from ablation results")
    parser.add_argument("results_file", help="JSON file containing ablation results")
    parser.add_argument("--output", help="Output directory for visualizations")

    args = parser.parse_args()

    generate_all_visualizations(args.results_file, args.output)
