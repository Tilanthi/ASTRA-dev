#!/usr/bin/env python3
"""
Turbulence Validation Campaign - Analysis Script
Analyzes results from realistic turbulence amplitude simulations
"""

import json
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from pathlib import Path

# Load results
results_path = Path("/data/turbulence_validation_runs/results.json")
with open(results_path, 'r') as f:
    results = json.load(f)

# Parse simulation data
sim_data = []
for sim_id, result in results.items():
    if result['status'] == 'FRAG':
        sim_data.append({
            'sim_id': sim_id,
            'f': result['params']['line_mass_fraction'],
            'beta': result['params']['plasma_beta'],
            'M': result['params']['mach_number'],
            'amplitude': result['params']['turbulence_amplitude_factor'],  # δv/cs
            'seed': result['params']['random_seed'],
            't_frag': result['t_frag']
        })

print(f"Loaded {len(sim_data)} fragmented simulations")

# Convert to numpy arrays for analysis
f_vals = np.array([d['f'] for d in sim_data])
beta_vals = np.array([d['beta'] for d in sim_data])
M_vals = np.array([d['M'] for d in sim_data])
amp_vals = np.array([d['amplitude'] for d in sim_data])
tfrag_vals = np.array([d['t_frag'] for d in sim_data])

# ============================================================================
# Figure 1: t_frag vs turbulence amplitude for different (f, β, M)
# ============================================================================
fig1, axes = plt.subplots(2, 3, figsize=(15, 10))
fig1.suptitle('Fragmentation Time vs Turbulence Amplitude', fontsize=14)

plot_idx = 0
for f in [1.5, 2.0]:
    for beta in [0.3, 1.0]:
        for M in [1.0, 2.0]:
            ax = axes.flatten()[plot_idx]

            # Filter data for this (f, beta, M)
            mask = (f_vals == f) & (beta_vals == beta) & (M_vals == M)
            amps = amp_vals[mask]
            tfrags = tfrag_vals[mask]

            # Group by amplitude and compute mean/std
            unique_amps = sorted(set(amps))
            mean_tfrags = []
            std_tfrags = []

            for amp in unique_amps:
                amp_mask = amps == amp
                mean_tfrags.append(np.mean(tfrags[amp_mask]))
                std_tfrags.append(np.std(tfrags[amp_mask]))

            # Plot
            ax.errorbar(unique_amps, mean_tfrags, yerr=std_tfrags,
                       marker='o', linestyle='-', capsize=5, markersize=8)

            ax.set_xlabel(r'Turbulence Amplitude $\delta v/c_s$')
            ax.set_ylabel(r'$t_{\rm frag}$ ($t_{\rm J}$)')
            ax.set_title(f'f={f}, $\\beta$={beta}, M={M}')
            ax.grid(True, alpha=0.3)
            ax.set_xscale('log')

            plot_idx += 1
            if plot_idx >= 6:
                break

plt.tight_layout()
plt.savefig('expected_output/fig_tfrag_vs_amplitude.pdf', dpi=300, bbox_inches='tight')
plt.savefig('expected_output/fig_tfrag_vs_amplitude.png', dpi=300, bbox_inches='tight')
print("Saved fig_tfrag_vs_amplitude.pdf")

# ============================================================================
# Figure 2: t_frag vs f with amplitude as color
# ============================================================================
fig2, ax = plt.subplots(figsize=(10, 6))

for amp in [0.1, 0.5, 1.0]:
    mask = amp_vals == amp
    # Group by f and compute mean
    f_unique = sorted(set(f_vals[mask]))
    tfrag_means = []
    tfrag_stds = []

    for f_val in f_unique:
        f_mask = (f_vals == f_val) & mask
        tfrag_means.append(np.mean(tfrag_vals[f_mask]))
        tfrag_stds.append(np.std(tfrag_vals[f_mask]))

    ax.errorbar(f_unique, tfrag_means, yerr=tfrag_stds,
                marker='o', label=f'$\\delta v/c_s$ = {amp}', capsize=5)

ax.set_xlabel('Line Mass Fraction $f$')
ax.set_ylabel(r'$t_{\rm frag}$ ($t_{\rm J}$)')
ax.set_title('Fragmentation Time vs Line Mass at Different Turbulence Amplitudes')
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('expected_output/fig_tfrag_vs_f_by_amplitude.pdf', dpi=300, bbox_inches='tight')
print("Saved fig_tfrag_vs_f_by_amplitude.pdf")

# ============================================================================
# Figure 3: Power law exponent comparison
# ============================================================================
fig3, ax = plt.subplots(figsize=(10, 6))

amplitudes = [0.1, 0.5, 1.0]
exponents = []
exponent_errs = []

for amp in amplitudes:
    mask = amp_vals == amp

    # Fit power law: 1/t_frag = A * f^alpha
    # Taking log: -log(t_frag) = log(A) + alpha * log(f)

    log_f = np.log(f_vals[mask])
    log_inv_tfrag = -np.log(tfrag_vals[mask])

    # Linear fit
    coeffs = np.polyfit(log_f, log_inv_tfrag, 1)
    alpha = coeffs[0]

    # Compute uncertainty via bootstrap
    boot_alphas = []
    for _ in range(1000):
        idx = np.random.choice(len(log_f), len(log_f), replace=True)
        boot_coeffs = np.polyfit(log_f[idx], log_inv_tfrag[idx], 1)
        boot_alphas.append(boot_coeffs[0])

    exponents.append(alpha)
    exponent_errs.append(np.std(boot_alphas))

ax.bar(range(len(amplitudes)), exponents, yerr=exponent_errs,
       tick_label=[f'{amp}' for amp in amplitudes],
       capsize=5, alpha=0.7)

ax.axhline(y=0.39, color='r', linestyle='--', label='Main campaign (0.39)')
ax.set_xlabel(r'Turbulence Amplitude $\delta v/c_s$')
ax.set_ylabel('Power Law Exponent $\\alpha$')
ax.set_title('Power Law Exponent vs Turbulence Amplitude\n(Fit: $1/t_{\\rm frag} \\propto f^{\\alpha}$)')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')
ax.set_ylim([0, 1.0])

plt.tight_layout()
plt.savefig('expected_output/fig_powerlaw_exponent_vs_amplitude.pdf', dpi=300, bbox_inches='tight')
print("Saved fig_powerlaw_exponent_vs_amplitude.pdf")

# ============================================================================
# Summary Table
# ============================================================================
# Compute statistics
summary = {
    'total_sims': len(sim_data),
    'amplitude_range': [float(min(amp_vals)), float(max(amp_vals))],
    'tfrag_range': [float(min(tfrag_vals)), float(max(tfrag_vals))],
    'mean_tfrag': float(np.mean(tfrag_vals)),
    'std_tfrag': float(np.std(tfrag_vals)),
}

# Amplitude dependence analysis
amp_dependence = []
for amp in amplitudes:
    mask = amp_vals == amp
    mean_tfrag = np.mean(tfrag_vals[mask])
    std_tfrag = np.std(tfrag_vals[mask])
    amp_dependence.append({
        'amplitude': amp,
        'mean_tfrag': float(mean_tfrag),
        'std_tfrag': float(std_tfrag),
        'n_sims': int(np.sum(mask))
    })

summary['amplitude_dependence'] = amp_dependence

# Compare to main campaign (δv/cs ~ 10^-4)
main_campaign_tfrag = 0.287  # From paper
summary['comparison_to_main_campaign'] = {
    'main_campaign_mean': main_campaign_tfrag,
    'turbulence_val_means': [float(np.mean(tfrag_vals[amp_vals == amp])) for amp in amplitudes],
    'percent_differences': [float(100 * (np.mean(tfrag_vals[amp_vals == amp]) - main_campaign_tfrag) / main_campaign_tfrag) for amp in amplitudes]
}

# Save summary
with open('expected_output/results_summary.json', 'w') as f:
    json.dump(summary, f, indent=2)

# Generate LaTeX table
with open('expected_output/table_summary.tex', 'w') as f:
    f.write('\\begin{table}[h]\n')
    f.write('\\caption{Summary of Turbulence Amplitude Validation Campaign}\n')
    f.write('\\begin{tabular}{cccc}\n')
    f.write('\\toprule\n')
    f.write(r'$\delta v/c_s$' + ' & Mean $t_{\\rm frag}$ ($t_{\\rm J}$) & Std Dev & $N_{\\rm sims}$ \\\\\n')
    f.write('\\midrule\n')

    for entry in amp_dependence:
        f.write(f"{entry['amplitude']:.1f} & {entry['mean_tfrag']:.3f} & {entry['std_tfrag']:.3f} & {entry['n_sims']} \\\\\n")

    f.write('\\midrule\n')
    f.write(f"Main campaign ($10^{{-4}}$) & {main_campaign_tfrag:.3f} & - & 654 \\\\\n")
    f.write('\\bottomrule\n')
    f.write('\\end{tabular}\n')
    f.write('\\end{table}\n')

print("Saved table_summary.tex")

# ============================================================================
# Key Findings for Paper Integration
# ============================================================================
print("\n" + "="*60)
print("KEY FINDINGS FOR PAPER INTEGRATION")
print("="*60)

# Check amplitude dependence
max_mean = max([d['mean_tfrag'] for d in amp_dependence])
min_mean = min([d['mean_tfrag'] for d in amp_dependence])
percent_variation = 100 * (max_mean - min_mean) / min_mean

print(f"\n1. Amplitude Dependence:")
print(f"   t_frag varies by {percent_variation:.1f}% across δv/cs ∈ {{0.1, 0.5, 1.0}}")

if percent_variation < 20:
    print("   → INTERPRETATION: Weak amplitude dependence - Mach number independence is ROBUST")
elif percent_variation < 50:
    print("   → INTERPRETATION: Moderate amplitude dependence - result holds with qualifications")
else:
    print("   → INTERPRETATION: Strong amplitude dependence - main campaign result is amplitude-specific")

# Check power law consistency
alpha_mean = np.mean(exponents)
alpha_std = np.std(exponents)
print(f"\n2. Power Law Exponent:")
print(f"   α = {alpha_mean:.3f} ± {alpha_std:.3f} (compared to main campaign: 0.39)")

if abs(alpha_mean - 0.39) < 0.1:
    print("   → INTERPRETATION: Exponent consistent with main campaign")
else:
    print("   → INTERPRETATION: Exponent differs - scaling law may be amplitude-dependent")

# Check fragmentation rate
frag_rate = 100 * len(sim_data) / len(results)
print(f"\n3. Fragmentation Rate:")
print(f"   {frag_rate:.1f}% of simulations fragmented")

if frag_rate > 95:
    print("   → INTERPRETATION: Robust fragmentation - all supercritical filaments unstable")
elif frag_rate > 80:
    print("   → INTERPRETATION: Some stability at high amplitudes - turbulence may provide support")
else:
    print("   → INTERPRETATION: Significant stability - turbulence dramatically affects outcome")

print("\n" + "="*60)
print("Analysis complete! Results saved to expected_output/")
print("="*60)
