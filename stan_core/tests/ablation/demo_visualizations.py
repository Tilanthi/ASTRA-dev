#!/usr/bin/env python3
"""
Quick demonstration of ablation study visualizations
"""

import matplotlib.pyplot as plt
import numpy as np

# Sample data from ablation studies
ablations = ['No Specialist\nCapabilities', 'Core Domains\nOnly', 'Minimal\nMemory',
             'Basic Physics\nOnly', 'No MMOL', 'No Causal\nDiscovery',
             'No Working\nMemory', 'No MORK\nOntology', 'No Cross-Domain\nMeta']

degradations = [45.0, 40.0, 34.9, 30.0, 20.0, 20.0, 17.9, 15.0, 12.0]

# Color coding
colors = ['#C62828' if d > 30 else '#F57C00' if d > 15 else '#1976D2' for d in degradations]

# Create figure
fig, ax = plt.subplots(figsize=(12, 8))

# Horizontal bar chart
bars = ax.barh(ablations, degradations, color=colors, edgecolor='black', linewidth=0.5)

# Customize
ax.set_xlabel('Performance Degradation (%)', fontsize=12, fontweight='bold')
ax.set_ylabel('Ablated Component', fontsize=12, fontweight='bold')
ax.set_title('ASTRA Component Importance Analysis\n(Performance Degradation When Removed)',
            fontsize=14, fontweight='bold')
ax.set_xlim(0, max(degradations) * 1.1)
ax.invert_yaxis()

# Add value labels
for bar, deg in zip(bars, degradations):
    ax.text(deg + 0.5, bar.get_y() + bar.get_height()/2,
           f'{deg:.1f}%', va='center', fontsize=10)

# Add legend
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor='#C62828', edgecolor='black', label='Critical (>30%)'),
    Patch(facecolor='#F57C00', edgecolor='black', label='Moderate (15-30%)'),
    Patch(facecolor='#1976D2', edgecolor='black', label='Minor (<15%)')
]
ax.legend(handles=legend_elements, loc='lower right')

plt.tight_layout()

# Save
output_file = 'stan_core/tests/ablation/demo_component_importance.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Demo visualization saved to: {output_file}")

plt.close()

# Create second figure: Performance comparison
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# Sample data
baseline_scores = [0.847] * len(ablations)
ablated_scores = [0.466, 0.508, 0.551, 0.593, 0.678, 0.678, 0.695, 0.720, 0.745]

# Sort by degradation
sorted_indices = np.argsort(degradations)[::-1]
sorted_ablations = [ablations[i] for i in sorted_indices]
sorted_baseline = [baseline_scores[i] for i in sorted_indices]
sorted_ablated = [ablated_scores[i] for i in sorted_indices]

# Top plot: Score comparison
x = np.arange(len(sorted_ablations))
width = 0.35

ax1.bar(x - width/2, sorted_baseline, width, label='Full System',
       color='#2E7D32', edgecolor='black', linewidth=0.5)
ax1.bar(x + width/2, sorted_ablated, width, label='Ablated System',
       color='#C62828', edgecolor='black', linewidth=0.5)

ax1.set_ylabel('Overall Score', fontsize=12, fontweight='bold')
ax1.set_title('ASTRA Ablation Study: Performance Comparison',
             fontsize=14, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(sorted_ablations, rotation=45, ha='right')
ax1.legend()
ax1.grid(axis='y', alpha=0.3)
ax1.set_ylim(0, 1.0)

# Bottom plot: Degradation percentage
sorted_degradations = [degradations[i] for i in sorted_indices]
ax2.plot(sorted_ablations, sorted_degradations, marker='o', linewidth=2,
        color='#C62828', markersize=8)
ax2.fill_between(sorted_ablations, sorted_degradations, alpha=0.3, color='#C62828')

ax2.set_xlabel('Ablated Component', fontsize=12, fontweight='bold')
ax2.set_ylabel('Performance Degradation (%)', fontsize=12, fontweight='bold')
ax2.set_xticklabels(sorted_ablations, rotation=45, ha='right')
ax2.grid(alpha=0.3)

# Add threshold lines
ax2.axhline(y=30, color='red', linestyle='--', alpha=0.5, label='Critical Threshold')
ax2.axhline(y=15, color='orange', linestyle='--', alpha=0.5, label='Moderate Threshold')
ax2.legend()

plt.tight_layout()

# Save
output_file = 'stan_core/tests/ablation/demo_performance_degradation.png'
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"Demo visualization saved to: {output_file}")

plt.close()

print("\nDemo visualizations created successfully!")
print("These demonstrate what the actual ablation study visualizations will look like.")
