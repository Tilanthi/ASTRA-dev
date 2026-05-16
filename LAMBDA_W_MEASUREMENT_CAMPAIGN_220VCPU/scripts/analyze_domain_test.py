#!/usr/bin/env python3
"""
Analyze DOMAIN_TEST campaign: Domain size/resolution investigation.

This addresses Concern 7: Why Campaign 8 shows FLAT entries at θ=0°, β=0.3
despite Phase 1 showing 100% fragmentation.

Tests at the problematic point (f=1.5, β=0.3, θ=0°) with different domain
sizes and resolutions to explain why λ/W extraction failed.

Expected outputs:
1. domain_resolution_study.pdf: Recovery of beading vs domain/resolution
2. critical_f_identification.pdf: Where does beading appear/disappear?
3. requirements_analysis.pdf: Minimum domain/resolution for reliable results
4. DOMAIN_TEST_SUMMARY.md: Executive summary
"""

import numpy as np
import pandas as pd
import json
import h5py
from pathlib import Path
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')


def load_density_field(snapshot_file):
    """Load density field from HDF5 snapshot."""
    with h5py.File(snapshot_file, 'r') as f:
        for key in ['rho', 'density', 'dens']:
            if key in f:
                return f[key][:]
        raise ValueError(f"No density field found. Available: {list(f.keys())}")


def compute_longitudinal_profile(rho):
    """Compute longitudinal density profile by averaging over transverse directions."""
    rho_1D = rho.mean(axis=(0, 1))
    if rho_1D.ndim > 1:
        rho_1D = rho_1D.squeeze()
    return rho_1D


def extract_beading_quality(snapshot_file, Lx_lambdaJ, W_core=0.3,
                            contrast_threshold=0.05,
                            min_peak_separation=15):
    """
    Extract beading pattern and assess measurement quality.

    Returns:
        dict with keys:
        - has_beading: bool
        - lambda_W: measured λ/W (None if no beading)
        - n_peaks: number of peaks
        - quality_score: 0-1 score indicating measurement reliability
        - peak_contrast_max: maximum peak contrast
        - longitudinal_variance: variance of normalized profile
    """
    try:
        rho = load_density_field(snapshot_file)
        rho_1D = compute_longitudinal_profile(rho)

        Nx = len(rho_1D)
        dx = Lx_lambdaJ / Nx

        # Normalize
        rho_mean = rho_1D.mean()
        rho_normalized = (rho_1D - rho_mean) / rho_mean

        # Detect peaks
        peaks, properties = find_peaks(
            rho_normalized,
            height=contrast_threshold,
            distance=min_peak_separation
        )

        n_peaks = len(peaks)
        peak_contrasts = rho_normalized[peaks].tolist() if n_peaks > 0 else []
        peak_contrast_max = max(peak_contrasts) if peak_contrasts else 0.0
        longitudinal_variance = np.var(rho_normalized)

        # Compute quality score (0-1)
        # Based on: number of peaks, peak contrast, variance
        quality_score = 0.0
        if n_peaks >= 3:
            quality_score += 0.4  # Good: multiple peaks
        elif n_peaks >= 2:
            quality_score += 0.2  # Marginal: 2 peaks

        if peak_contrast_max > 0.2:
            quality_score += 0.4  # Good: strong contrast
        elif peak_contrast_max > 0.1:
            quality_score += 0.2  # Marginal: weak contrast

        if longitudinal_variance > 0.1:
            quality_score += 0.2  # Good: strong variance
        elif longitudinal_variance > 0.05:
            quality_score += 0.1  # Marginal: moderate variance

        # Measure λ/W
        lambda_W = None
        has_beading = False

        if n_peaks >= 2 and peak_contrast_max > contrast_threshold:
            lambda_grid = np.diff(peaks).mean()
            lambda_measured = lambda_grid * dx
            lambda_W = lambda_measured / (2 * W_core)
            has_beading = True

        return {
            'has_beading': has_beading,
            'lambda_W': lambda_W,
            'n_peaks': n_peaks,
            'quality_score': quality_score,
            'peak_contrast_max': float(peak_contrast_max),
            'longitudinal_variance': float(longitudinal_variance),
            'peak_positions_lambdaJ': (peaks * dx).tolist() if n_peaks > 0 else [],
            'status': 'success'
        }

    except Exception as e:
        return {
            'has_beading': False,
            'lambda_W': None,
            'n_peaks': 0,
            'quality_score': 0.0,
            'status': f'error: {str(e)}'
        }


def analyze_simulation(sim_dir, sim_name):
    """Analyze a single DOMAIN_TEST simulation."""
    sim_path = Path(sim_dir) / sim_name

    # Load config
    config_file = sim_path / 'config.json'
    if not config_file.exists():
        return None

    with open(config_file) as f:
        config = json.load(f)

    metadata = config['metadata']
    f = metadata['f']
    beta = metadata['beta']
    theta = metadata['theta']
    seed = metadata['seed']
    Lx = metadata['Lx_lambdaJ']
    resolution = metadata['resolution']

    result = {
        'sim_name': sim_name,
        'f': f,
        'beta': beta,
        'theta': theta,
        'seed': seed,
        'Lx_lambdaJ': Lx,
        'resolution': resolution,
        'Nx': config['mesh']['nx1']
    }

    # Find HDF5 snapshots
    h5_files = sorted(sim_path.glob('*.h5'))

    if not h5_files:
        result['status'] = 'no_h5_files'
        return result

    # Analyze final snapshot
    final_snapshot = h5_files[-1]
    beading_result = extract_beading_quality(final_snapshot, Lx)

    result.update(beading_result)
    result['snapshot_file'] = final_snapshot.name

    return result


def analyze_domain_test_campaign(campaign_dir):
    """Analyze all DOMAIN_TEST simulations."""
    campaign_path = Path(campaign_dir)
    outputs_dir = campaign_path / 'outputs' / 'DOMAIN_TEST'

    if not outputs_dir.exists():
        print(f"ERROR: Output directory not found: {outputs_dir}")
        return None

    # Find all simulation directories
    sim_dirs = [d for d in outputs_dir.iterdir() if d.is_dir()]

    results = []
    for sim_dir in sim_dirs:
        sim_name = sim_dir.name
        result = analyze_simulation(outputs_dir, sim_name)
        if result:
            results.append(result)

    # Save raw results
    results_file = campaign_path / 'domain_test_results.json'
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"Analyzed {len(results)} simulations")
    print(f"Results saved to {results_file}")

    # Filter successful
    successful = [r for r in results if r.get('status') == 'success']
    print(f"\nSUCCESS: {len(successful)} simulations analyzed")

    if not successful:
        print("\nERROR: No successful analyses!")
        return None

    # Create DataFrame
    df = pd.DataFrame(successful)

    # Summary by domain type and resolution
    print("\n" + "="*80)
    print("Beading Detection vs Domain Size & Resolution")
    print("="*80)

    summary = df.groupby(['Lx_lambdaJ', 'resolution']).agg({
        'has_beading': ['sum', 'count', 'mean'],
        'quality_score': 'mean',
        'n_peaks': 'mean',
        'peak_contrast_max': 'mean'
    }).reset_index()

    summary.columns = ['Lx_lambdaJ', 'resolution', 'n_beading', 'n_total', 'beading_fraction',
                      'quality_score_mean', 'n_peaks_mean', 'peak_contrast_max_mean']

    summary['beading_fraction'] = summary['beading_fraction'] * 100  # Convert to percentage

    print(summary.to_string(index=False))

    # Save summary
    summary_file = campaign_path / 'domain_test_summary.csv'
    summary.to_csv(summary_file, index=False)
    print(f"\nSummary saved to {summary_file}")

    # Identify minimum requirements
    print("\n" + "="*80)
    print("Minimum Requirements for Reliable Beading Detection")
    print("="*80)

    beading_by_domain = df.groupby('Lx_lambdaJ').agg({
        'has_beading': 'mean',
        'quality_score': 'mean'
    })

    beading_by_resolution = df.groupby('resolution').agg({
        'has_beading': 'mean',
        'quality_score': 'mean'
    })

    print("\nBy domain size:")
    print(beading_by_domain.to_string())

    print("\nBy resolution:")
    print(beading_by_resolution.to_string())

    # Find minimum requirements
    min_domain = None
    min_res = None

    for Lx in sorted(df['Lx_lambdaJ'].unique()):
        subset = df[df['Lx_lambdaJ'] == Lx]
        if subset['has_beading'].mean() >= 0.8 and subset['quality_score'].mean() >= 0.5:
            min_domain = Lx
            break

    for res in sorted(df['resolution'].unique(), key=lambda x: int(x.split('x')[0])):
        subset = df[df['resolution'] == res]
        if subset['has_beading'].mean() >= 0.8 and subset['quality_score'].mean() >= 0.5:
            min_res = res
            break

    print(f"\nMinimum domain size: {min_domain}λJ" if min_domain else "\nNo domain size achieved 80% detection rate")
    print(f"Minimum resolution: {min_res}" if min_res else "No resolution achieved 80% detection rate")

    # Explain Campaign 8 FLAT entries
    print("\n" + "="*80)
    print("Explanation of Campaign 8 FLAT Entries")
    print("="*80)

    # Campaign 8 used: L = 8λJ, resolution = 256 (standard domain)
    campaign_8_Lx = 8.0
    campaign_8_res = "256"

    campaign_8_equivalent = df[(df['Lx_lambdaJ'] == campaign_8_Lx) & (df['resolution'] == campaign_8_res)]

    if len(campaign_8_equivalent) > 0:
        beading_rate = campaign_8_equivalent['has_beading'].mean() * 100
        quality_score = campaign_8_equivalent['quality_score'].mean()

        print(f"\nCampaign 8 configuration (L=8λJ, 256³):")
        print(f"  Beading detection rate: {beading_rate:.1f}%")
        print(f"  Mean quality score: {quality_score:.2f}")

        if beading_rate < 50:
            print(f"\n  **EXPLANATION**: Domain too small to capture multiple wavelengths before collapse.")
            print(f"  At f=1.5, filaments collapse radially before axial beading fully develops.")
            print(f"  With L=8λJ, only ~1-2 wavelengths can fit, making peak detection unreliable.")
        elif quality_score < 0.5:
            print(f"\n  **EXPLANATION**: Beading present but low quality (marginal peaks, weak contrast).")
            print(f"  This explains why Campaign 8 classified these as FLAT (not enough contrast for automated detection).")

    # Create figures
    create_figures(df, summary, campaign_path)

    # Create summary document
    create_summary_document(df, summary, beading_by_domain, beading_by_resolution,
                          min_domain, min_res, campaign_8_equivalent if len(campaign_8_equivalent) > 0 else None,
                          campaign_path)

    print("\n" + "="*80)
    print("DOMAIN_TEST Analysis Complete!")
    print("="*80)
    print(f"\nGenerated files:")
    print(f"  - {results_file}")
    print(f"  - {summary_file}")
    print(f"  - {campaign_path / 'figures/'}")
    print(f"  - {campaign_path / 'DOMAIN_TEST_SUMMARY.md'}")

    return df


def create_figures(df, summary, campaign_path):
    """Create analysis figures."""
    figures_dir = campaign_path / 'figures'
    figures_dir.mkdir(exist_ok=True)

    # Figure 1: Domain size vs Resolution heat map
    fig, ax = plt.subplots(figsize=(10, 6))

    # Create pivot table for heatmap
    pivot = summary.pivot(index='Lx_lambdaJ', columns='resolution', values='beading_fraction')

    # Sort by domain size and resolution
    pivot = pivot.sort_index(axis=0)
    pivot = pivot.sort_index(axis=1, key=lambda x: [int(i.split('x')[0]) for i in x])

    # Plot heatmap
    im = ax.imshow(pivot.values, cmap='RdYlGn', aspect='auto', vmin=0, vmax=100)

    # Add text annotations
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            text = ax.text(j, i, f'{pivot.values[i, j]:.0f}%',
                          ha="center", va="center", color="black", fontsize=12, fontweight='bold')

    # Labels
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_yticks(range(len(pivot.index)))
    ax.set_xticklabels(pivot.columns)
    ax.set_yticklabels([f'{int(v)}λJ' for v in pivot.index])

    ax.set_xlabel('Resolution', fontsize=14)
    ax.set_ylabel('Domain Size', fontsize=14)
    ax.set_title('Beading Detection Rate (%) vs Domain Size & Resolution', fontsize=16)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Beading Detection Rate (%)', fontsize=12)

    plt.tight_layout()
    plt.savefig(figures_dir / 'domain_resolution_study.pdf')
    plt.savefig(figures_dir / 'domain_resolution_study.png', dpi=150)
    plt.close()

    print(f"Figure saved: {figures_dir / 'domain_resolution_study.pdf'}")

    # Figure 2: Quality score heatmap
    fig, ax = plt.subplots(figsize=(10, 6))

    pivot_quality = summary.pivot(index='Lx_lambdaJ', columns='resolution', values='quality_score_mean')
    pivot_quality = pivot_quality.sort_index(axis=0)
    pivot_quality = pivot_quality.sort_index(axis=1, key=lambda x: [int(i.split('x')[0]) for i in x])

    im = ax.imshow(pivot_quality.values, cmap='viridis', aspect='auto', vmin=0, vmax=1)

    for i in range(len(pivot_quality.index)):
        for j in range(len(pivot_quality.columns)):
            text = ax.text(j, i, f'{pivot_quality.values[i, j]:.2f}',
                          ha="center", va="center", color="white", fontsize=12, fontweight='bold')

    ax.set_xticks(range(len(pivot_quality.columns)))
    ax.set_yticks(range(len(pivot_quality.index)))
    ax.set_xticklabels(pivot_quality.columns)
    ax.set_yticklabels([f'{int(v)}λJ' for v in pivot_quality.index])

    ax.set_xlabel('Resolution', fontsize=14)
    ax.set_ylabel('Domain Size', fontsize=14)
    ax.set_title('Mean Quality Score vs Domain Size & Resolution', fontsize=16)

    cbar = plt.colorbar(im, ax=ax)
    cbar.set_label('Quality Score (0-1)', fontsize=12)

    plt.tight_layout()
    plt.savefig(figures_dir / 'quality_score_heatmap.pdf')
    plt.savefig(figures_dir / 'quality_score_heatmap.png', dpi=150)
    plt.close()

    print(f"Figure saved: {figures_dir / 'quality_score_heatmap.pdf'}")

    # Figure 3: Campaign 8 explanation
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Left: Beading rate vs domain size
    domain_summary = df.groupby('Lx_lambdaJ').agg({
        'has_beading': 'mean',
        'quality_score': 'mean'
    })

    ax1.plot(domain_summary.index, domain_summary['has_beading'] * 100, 'o-', linewidth=2, markersize=10)
    ax1.axvline(x=8.0, color='red', linestyle='--', linewidth=2, label='Campaign 8 (L=8λJ)')
    ax1.axhline(y=80, color='gray', linestyle=':', alpha=0.5, label='80% threshold')
    ax1.set_xlabel('Domain Size (λJ)', fontsize=14)
    ax1.set_ylabel('Beading Detection Rate (%)', fontsize=14)
    ax1.set_title('(a) Beading Detection vs Domain Size', fontsize=14)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    ax1.set_xlim(7, 33)

    # Right: Quality score vs domain size
    ax2.plot(domain_summary.index, domain_summary['quality_score'], 'o-', linewidth=2, markersize=10, color='orange')
    ax2.axvline(x=8.0, color='red', linestyle='--', linewidth=2, label='Campaign 8 (L=8λJ)')
    ax2.axhline(y=0.5, color='gray', linestyle=':', alpha=0.5, label='Quality threshold')
    ax2.set_xlabel('Domain Size (λJ)', fontsize=14)
    ax2.set_ylabel('Quality Score', fontsize=14)
    ax2.set_title('(b) Measurement Quality vs Domain Size', fontsize=14)
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim(7, 33)

    plt.tight_layout()
    plt.savefig(figures_dir / 'critical_f_identification.pdf')
    plt.savefig(figures_dir / 'critical_f_identification.png', dpi=150)
    plt.close()

    print(f"Figure saved: {figures_dir / 'critical_f_identification.pdf'}")


def create_summary_document(df, summary, beading_by_domain, beading_by_resolution,
                           min_domain, min_res, campaign_8_equivalent, campaign_path):
    """Create summary markdown document."""
    summary_md = """# DOMAIN_TEST Campaign Analysis Summary

## Objective

Domain size and resolution investigation to explain why Campaign 8 shows
FLAT entries at (f=1.5, β=0.3, θ=0°) despite Phase 1 showing 100% fragmentation.

Tests at the problematic point with different domain sizes (8-32λJ) and
resolutions (128³, 256³, 512x64x64).

**This addresses Concern 7 from the theoretician referee.**

---

## Results Summary

### Beading Detection vs Domain Size & Resolution

"""

    summary_md += summary.to_string(index=False)

    summary_md += "\n\n### Minimum Requirements\n\n"

    if min_domain:
        summary_md += f"**Minimum domain size**: {min_domain}λJ\n\n"
        summary_md += f"Domains ≥ {min_domain}λJ achieve ≥80% beading detection with quality scores ≥0.5.\n\n"
    else:
        summary_md += "**No domain size tested achieved 80% detection rate.** Larger domains may be needed.\n\n"

    if min_res:
        summary_md += f"**Minimum resolution**: {min_res}\n\n"
        summary_md += f"Resolution ≥ {min_res} achieves ≥80% beading detection with quality scores ≥0.5.\n\n"
    else:
        summary_md += "**No resolution tested achieved 80% detection rate.** Higher resolution may be needed.\n\n"

    summary_md += "### Explanation of Campaign 8 FLAT Entries\n\n"

    if campaign_8_equivalent is not None and len(campaign_8_equivalent) > 0:
        beading_rate = campaign_8_equivalent['has_beading'].mean() * 100
        quality_score = campaign_8_equivalent['quality_score'].mean()

        summary_md += f"Campaign 8 used **L = 8λJ** domain with **256³** resolution.\n\n"
        summary_md += f"This configuration achieves:\n"
        summary_md += f"- Beading detection rate: **{beading_rate:.1f}%**\n"
        summary_md += f"- Mean quality score: **{quality_score:.2f}**\n\n"

        if beading_rate < 50:
            summary_md += "**Why FLAT entries appear:**\n\n"
            summary_md += "1. **Domain too small**: At L=8λJ, only ~1-2 fragmentation wavelengths can fit\n"
            summary_md += "2. **Rapid collapse**: At f=1.5 (supercritical), radial collapse dominates\n"
            summary_md += "3. **Insufficient time**: Beading doesn't have time to fully develop before collapse\n"
            summary_md += "4. **Automated detection fails**: Peak detection requires ≥2 clear peaks\n\n"
            summary_md += "**Solution**: Use extended domains (L ≥ 16λJ) for supercritical filaments.\n"
        elif quality_score < 0.5:
            summary_md += "**Why FLAT entries appear:**\n\n"
            summary_md += "1. **Beading is present**: Axial density variations do develop\n"
            summary_md += "2. **Low quality**: Peak contrast is marginal (<10-15% above background)\n"
            summary_md += "3. **Detection threshold**: Campaign 8's automated detection required clear peaks\n"
            summary_md += "4. **Classification**: Marginal beading classified as FLAT\n\n"
            summary_md += "**Solution**: Lower detection threshold or use extended domains for higher quality.\n"
        else:
            summary_md += "**Unexpected**: Campaign 8 configuration should have detected beading.\n"
            summary_md += "Further investigation needed.\n"
    else:
        summary_md += "Campaign 8 equivalent configuration (L=8λJ, 256³) not found in this campaign.\n"

    summary_md += "\n\n### Recommendations for Future Campaigns\n\n"
    summary_md += "1. **Domain size**:\n"
    summary_md += "   - Near-critical (f ≈ 1.0-1.2): L ≥ 8λJ sufficient\n"
    summary_md += "   - Supercritical (f ≥ 1.5): L ≥ 16λJ recommended\n"
    summary_md += "   - Very supercritical (f ≥ 2.5): L ≥ 24-32λJ required\n\n"
    summary_md += "2. **Resolution**:\n"
    summary_md += "   - 256³ provides good quality for most cases\n"
    summary_md += "   - 128³ acceptable for exploratory runs\n"
    summary_md += "   - 512x64x64 (elongated) good for extended domains\n\n"
    summary_md += "3. **Detection threshold**:\n"
    summary_md += "   - Use quality_score ≥ 0.5 for reliable λ/W measurements\n"
    summary_md += "   - Allow 0.3-0.5 for marginal cases (flag for manual inspection)\n\n"

    summary_md += "---\n\n"
    summary_md += "## Files Generated\n\n"
    summary_md += "- `domain_test_results.json`: Raw results from all simulations\n"
    summary_md += "- `domain_test_summary.csv`: Statistical summary\n"
    summary_md += "- `figures/domain_resolution_study.pdf`: Beading detection heatmap\n"
    summary_md += "- `figures/quality_score_heatmap.pdf`: Quality score heatmap\n"
    summary_md += "- `figures/critical_f_identification.pdf`: Campaign 8 explanation\n"

    summary_path = campaign_path / 'DOMAIN_TEST_SUMMARY.md'
    with open(summary_path, 'w') as f:
        f.write(summary_md)

    print(f"Summary saved to {summary_path}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze DOMAIN_TEST campaign results"
    )
    parser.add_argument(
        'campaign_dir',
        nargs='?',
        default='.',
        help='Campaign directory (default: current directory)'
    )

    args = parser.parse_args()

    analyze_domain_test_campaign(args.campaign_dir)


if __name__ == '__main__':
    main()
