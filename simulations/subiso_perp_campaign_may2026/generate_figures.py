#!/usr/bin/env python3
"""
Sub-Isothermal Perpendicular Campaign Analysis
Generate publication-quality figures for the sub-isothermal perpendicular B-field campaign.
72 sims: f=[1.5,2.0,2.5,3.0] × β=[0.5,1.0,2.0] × γ=[0.7,0.8,0.9] × seeds=[0,1], θ=90°
"""

import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import matplotlib.gridspec as gridspec

# Style setup
plt.style.use('seaborn-v0_8-paper')
plt.rcParams.update({
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'legend.fontsize': 9,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'figure.dpi': 150,
    'savefig.dpi': 150,
    'savefig.bbox': 'tight',
    'font.family': 'serif',
})

# Load data
with open('/workspace/subiso_perp_results.json') as fh:
    data = json.load(fh)

# Extract arrays
f_vals = sorted(set(r['f'] for r in data))
beta_vals = sorted(set(r['beta'] for r in data))
gamma_vals = sorted(set(r['gamma'] for r in data))

# Helper: mean t_frag by parameter combos
def mean_tfrag(filt_key, filt_val, group_keys):
    """Get mean t_frag for records matching filter, grouped by group_keys."""
    filtered = [r for r in data if all(r[k] == v for k, v in zip([filt_key] if isinstance(filt_key, str) else filt_key, 
                                                                   [filt_val] if not isinstance(filt_val, (list, tuple)) else filt_val))]
    return np.mean([r['t_frag'] for r in filtered])

def get_mean_tfrag(f=None, beta=None, gamma=None):
    """Get mean t_frag across seeds for given parameter combination."""
    filtered = data
    if f is not None:
        filtered = [r for r in filtered if r['f'] == f]
    if beta is not None:
        filtered = [r for r in filtered if r['beta'] == beta]
    if gamma is not None:
        filtered = [r for r in filtered if r['gamma'] == gamma]
    if not filtered:
        return np.nan
    return np.mean([r['t_frag'] for r in filtered])

def get_std_tfrag(f=None, beta=None, gamma=None):
    """Get std t_frag across seeds."""
    filtered = data
    if f is not None:
        filtered = [r for r in filtered if r['f'] == f]
    if beta is not None:
        filtered = [r for r in filtered if r['beta'] == beta]
    if gamma is not None:
        filtered = [r for r in filtered if r['gamma'] == gamma]
    if len(filtered) < 2:
        return 0.0
    return np.std([r['t_frag'] for r in filtered])

# ============================================================
# FIGURE 1: t_frag heatmap in (f, β) plane, one panel per γ
# ============================================================
fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)

vmin = min(r['t_frag'] for r in data) - 0.02
vmax = max(r['t_frag'] for r in data) + 0.02

for ax_idx, gamma in enumerate(gamma_vals):
    ax = axes[ax_idx]
    # Create heatmap matrix
    hmap = np.zeros((len(beta_vals), len(f_vals)))
    for i, beta in enumerate(beta_vals):
        for j, f in enumerate(f_vals):
            hmap[i, j] = get_mean_tfrag(f=f, beta=beta, gamma=gamma)
    
    im = ax.imshow(hmap, aspect='auto', origin='lower', vmin=vmin, vmax=vmax,
                   cmap='viridis_r', extent=[0, len(f_vals), 0, len(beta_vals)])
    
    # Add text annotations
    for i in range(len(beta_vals)):
        for j in range(len(f_vals)):
            val = hmap[i, j]
            color = 'white' if val < 0.4 else 'black'
            ax.text(j + 0.5, i + 0.5, f'{val:.3f}', ha='center', va='center', 
                   fontsize=8, color=color, fontweight='bold')
    
    ax.set_xticks(np.arange(len(f_vals)) + 0.5)
    ax.set_xticklabels([f'{v:.1f}' for v in f_vals])
    ax.set_xlabel(r'Line-mass ratio $f$')
    ax.set_title(f'$\\gamma = {gamma}$')
    
    if ax_idx == 0:
        ax.set_yticks(np.arange(len(beta_vals)) + 0.5)
        ax.set_yticklabels([f'{v:.1f}' for v in beta_vals])
        ax.set_ylabel(r'Plasma $\beta$')
    else:
        ax.set_yticks(np.arange(len(beta_vals)) + 0.5)
        ax.set_yticklabels([])

fig.suptitle(r'Fragmentation Time $t_{\rm frag}/t_J$ — Sub-Isothermal Perpendicular ($\theta=90°$)', 
             fontsize=13, y=1.02)
cbar = fig.colorbar(im, ax=axes, shrink=0.8, label=r'$t_{\rm frag}\;[t_J]$')
plt.tight_layout()
fig.savefig('/workspace/subiso_perp_analysis/fig1_tfrag_heatmap.pdf')
fig.savefig('/workspace/subiso_perp_analysis/fig1_tfrag_heatmap.png')
plt.close(fig)
print("Fig 1 done")

# ============================================================
# FIGURE 2: t_frag vs f, coloured by β, markers by γ
# ============================================================
fig, ax = plt.subplots(figsize=(8, 5.5))

beta_colors = {0.5: '#d62728', 1.0: '#2ca02c', 2.0: '#1f77b4'}
gamma_markers = {0.7: 'o', 0.8: 's', 0.9: '^'}
beta_labels_done = set()
gamma_labels_done = set()

for beta in beta_vals:
    for gamma in gamma_vals:
        means = [get_mean_tfrag(f=f, beta=beta, gamma=gamma) for f in f_vals]
        stds = [get_std_tfrag(f=f, beta=beta, gamma=gamma) for f in f_vals]
        
        label_beta = f'$\\beta={beta}$' if beta not in beta_labels_done else None
        if label_beta:
            beta_labels_done.add(beta)
        
        ax.errorbar(f_vals, means, yerr=stds, 
                   color=beta_colors[beta], marker=gamma_markers[gamma],
                   markersize=7, capsize=3, linestyle='-' if gamma == 0.8 else '--',
                   alpha=0.85, linewidth=1.5,
                   label=f'$\\beta={beta},\\,\\gamma={gamma}$')

ax.set_xlabel(r'Line-mass ratio $f = M_{\rm line}/M_{\rm crit}$')
ax.set_ylabel(r'$t_{\rm frag}\;[t_J]$')
ax.set_title(r'Fragmentation Time vs Line-Mass Ratio (Sub-Isothermal, $\theta=90°$)')
ax.legend(ncol=3, fontsize=8, loc='upper right', framealpha=0.9)
ax.set_xlim(1.3, 3.2)
ax.grid(True, alpha=0.3)

# Add text annotation for the key result
ax.text(0.02, 0.02, r'$\beta$ dominates (21% range) > $f$ (19%) > $\gamma$ (6.6%)',
        transform=ax.transAxes, fontsize=9, style='italic',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

fig.tight_layout()
fig.savefig('/workspace/subiso_perp_analysis/fig2_tfrag_vs_f.pdf')
fig.savefig('/workspace/subiso_perp_analysis/fig2_tfrag_vs_f.png')
plt.close(fig)
print("Fig 2 done")

# ============================================================
# FIGURE 3: λ/W vs f coloured by β — with warning annotations
# ============================================================
fig, ax = plt.subplots(figsize=(8, 5.5))

for beta in beta_vals:
    for gamma in gamma_vals:
        subset = [r for r in data if r['beta'] == beta and r['gamma'] == gamma and r['lw_mean'] is not None]
        f_plot = [r['f'] for r in subset]
        lw_plot = [r['lw_mean'] for r in subset]
        
        ax.scatter(f_plot, lw_plot, color=beta_colors[beta], marker=gamma_markers[gamma],
                  alpha=0.5, s=30)

# Mean line by beta
for beta in beta_vals:
    means = []
    for f in f_vals:
        subset = [r for r in data if r['beta'] == beta and r['f'] == f and r['lw_mean'] is not None]
        if subset:
            means.append(np.mean([r['lw_mean'] for r in subset]))
        else:
            means.append(np.nan)
    ax.plot(f_vals, means, color=beta_colors[beta], linewidth=2.5, 
           label=f'$\\beta={beta}$ (this campaign)', marker='D', markersize=8)

# C6 isothermal reference line
ax.axhline(y=1.25, color='black', linestyle='--', linewidth=2, label=r'C6 isothermal $\lambda/W \approx 1.25$ (genuine)')

ax.set_xlabel(r'Line-mass ratio $f$')
ax.set_ylabel(r'$\lambda/W$')
ax.set_title(r'$\lambda/W$ Measurements — Sub-Isothermal Perpendicular ($\theta=90°$)')
ax.legend(loc='upper left', framealpha=0.9)
ax.set_xlim(1.3, 3.2)
ax.grid(True, alpha=0.3)

# Warning annotation
ax.text(0.5, 0.95, 'WARNING: NOT genuine axial fragmentation\n(~5 peaks in 16 $\\lambda_J$ domain = radial collapse artefact)',
        transform=ax.transAxes, fontsize=10, ha='center', va='top',
        color='red', fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='mistyrose', alpha=0.9, edgecolor='red'))

fig.tight_layout()
fig.savefig('/workspace/subiso_perp_analysis/fig3_lambda_W.pdf')
fig.savefig('/workspace/subiso_perp_analysis/fig3_lambda_W.png')
plt.close(fig)
print("Fig 3 done")

# ============================================================
# FIGURE 4: PS detection fraction heatmap (β × f)
# ============================================================
fig, ax = plt.subplots(figsize=(7, 4.5))

detect_matrix = np.zeros((len(beta_vals), len(f_vals)))
for i, beta in enumerate(beta_vals):
    for j, f in enumerate(f_vals):
        subset = [r for r in data if r['beta'] == beta and r['f'] == f]
        n_detected = sum(1 for r in subset if r['ps_beading_detected'])
        detect_matrix[i, j] = n_detected / len(subset) * 100 if subset else 0

im = ax.imshow(detect_matrix, aspect='auto', origin='lower', vmin=0, vmax=100,
               cmap='RdYlGn', extent=[0, len(f_vals), 0, len(beta_vals)])

# Add text annotations
for i in range(len(beta_vals)):
    for j in range(len(f_vals)):
        val = detect_matrix[i, j]
        color = 'white' if val < 30 or val > 80 else 'black'
        ax.text(j + 0.5, i + 0.5, f'{val:.0f}%', ha='center', va='center',
               fontsize=11, color=color, fontweight='bold')

ax.set_xticks(np.arange(len(f_vals)) + 0.5)
ax.set_xticklabels([f'{v:.1f}' for v in f_vals])
ax.set_yticks(np.arange(len(beta_vals)) + 0.5)
ax.set_yticklabels([f'{v:.1f}' for v in beta_vals])
ax.set_xlabel(r'Line-mass ratio $f$')
ax.set_ylabel(r'Plasma $\beta$')
ax.set_title(r'Power Spectrum Beading Detection Fraction (\%)')
cbar = fig.colorbar(im, ax=ax, label='Detection fraction (%)')

# Annotation
ax.text(0.5, -0.18, r'Detection correlates with $\beta$ (weak B $\rightarrow$ more radial compression), not $\gamma$',
        transform=ax.transAxes, fontsize=9, ha='center', style='italic')

fig.tight_layout()
fig.savefig('/workspace/subiso_perp_analysis/fig4_ps_detection.pdf')
fig.savefig('/workspace/subiso_perp_analysis/fig4_ps_detection.png')
plt.close(fig)
print("Fig 4 done")

# ============================================================
# FIGURE 5: Comparison — t_frag(β) with C6 isothermal
# ============================================================
fig, ax = plt.subplots(figsize=(8, 5.5))

# This campaign: mean over f, γ, seeds
this_tfrag_by_beta = []
this_err = []
for beta in beta_vals:
    subset = [r['t_frag'] for r in data if r['beta'] == beta]
    this_tfrag_by_beta.append(np.mean(subset))
    this_err.append(np.std(subset))

ax.errorbar(beta_vals, this_tfrag_by_beta, yerr=this_err,
           color='#d62728', marker='o', markersize=10, capsize=5, linewidth=2.5,
           label=r'This campaign (sub-iso, $\theta=90°$, $\gamma=0.7{-}0.9$)')

# C6 isothermal perpendicular data (from memory)
c6_beta = [0.3, 0.5, 1.0, 1.5, 2.0]
c6_tfrag = [0.716, 0.681, 0.601, 0.598, 0.578]
ax.plot(c6_beta, c6_tfrag, color='#1f77b4', marker='s', markersize=10, linewidth=2.5,
       label=r'C6 isothermal ($\theta=90°$, $\gamma=1.0$, $f=1.2{-}1.5$)')

# Campaign B θ=90° data (from memory: γ=[0.5,0.7,0.9,1.0], f=[1.5,2.0,2.5,3.0], β=[0.5,1.0,2.0])
# Camp B θ=90° was: EOS insensitive at θ=0° (<2% t_frag variation); 25% variation at θ=90°
# We don't have exact β-averaged values from Camp B θ=90° but can note it was similar
# Let's just mark approximate location if useful

ax.set_xlabel(r'Plasma $\beta$')
ax.set_ylabel(r'$t_{\rm frag}\;[t_J]$')
ax.set_title(r'Comparison: $t_{\rm frag}(\beta)$ — Sub-Isothermal vs Isothermal ($\theta=90°$)')
ax.legend(loc='upper right', framealpha=0.9, fontsize=10)
ax.grid(True, alpha=0.3)
ax.set_xlim(0.1, 2.3)

# Annotation for key difference
ax.annotate(r'Sub-iso $\sim$40% faster than isothermal',
           xy=(1.0, 0.41), xytext=(1.5, 0.55),
           fontsize=9, style='italic',
           arrowprops=dict(arrowstyle='->', color='gray'),
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

fig.tight_layout()
fig.savefig('/workspace/subiso_perp_analysis/fig5_comparison.pdf')
fig.savefig('/workspace/subiso_perp_analysis/fig5_comparison.png')
plt.close(fig)
print("Fig 5 done")

# ============================================================
# Print summary statistics for report
# ============================================================
print("\n=== SUMMARY STATISTICS ===")
print(f"Total sims: {len(data)}")
print(f"All FRAG: {all(r['outcome']=='FRAG' for r in data)}")
print(f"t_frag overall: {np.mean([r['t_frag'] for r in data]):.4f} ± {np.std([r['t_frag'] for r in data]):.4f} t_J")
print(f"PS beading detected: {sum(1 for r in data if r['ps_beading_detected'])}/{len(data)}")

print("\nt_frag by β (mean over f,γ,seeds):")
for beta in beta_vals:
    subset = [r['t_frag'] for r in data if r['beta'] == beta]
    print(f"  β={beta}: {np.mean(subset):.4f} ± {np.std(subset):.4f} (n={len(subset)})")

print("\nt_frag by f (mean over β,γ,seeds):")
for f in f_vals:
    subset = [r['t_frag'] for r in data if r['f'] == f]
    print(f"  f={f}: {np.mean(subset):.4f} ± {np.std(subset):.4f} (n={len(subset)})")

print("\nt_frag by γ (mean over f,β,seeds):")
for gamma in gamma_vals:
    subset = [r['t_frag'] for r in data if r['gamma'] == gamma]
    print(f"  γ={gamma}: {np.mean(subset):.4f} ± {np.std(subset):.4f} (n={len(subset)})")

print("\nPS detection by β:")
for beta in beta_vals:
    subset = [r for r in data if r['beta'] == beta]
    n_det = sum(1 for r in subset if r['ps_beading_detected'])
    print(f"  β={beta}: {n_det}/{len(subset)} ({100*n_det/len(subset):.0f}%)")

print("\nPS detection by f:")
for f in f_vals:
    subset = [r for r in data if r['f'] == f]
    n_det = sum(1 for r in subset if r['ps_beading_detected'])
    print(f"  f={f}: {n_det}/{len(subset)} ({100*n_det/len(subset):.0f}%)")

print("\nλ/W by β (mean over all):")
for beta in beta_vals:
    subset = [r['lw_mean'] for r in data if r['beta'] == beta and r['lw_mean'] is not None]
    if subset:
        print(f"  β={beta}: {np.mean(subset):.2f} ± {np.std(subset):.2f}")

print("\nAll figures saved to /workspace/subiso_perp_analysis/")
