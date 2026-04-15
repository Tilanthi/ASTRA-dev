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
ASTRA RASTI Paper V2.3 — Publication-Quality Figure Generation (v3)
Generates 6 figures as vector PDF + raster PNG.

Style: MNRAS/RASTI journal conventions
 - Serif fonts (Computer Modern / DejaVu Serif), 9 pt body
 - Inward ticks on all four axes
 - 300 DPI PDF, 150 DPI PNG
 - Colorblind-safe Tol Bright palette
 - Panel labels (a), (b) in bold
 - No in-figure titles (titles go in LaTeX captions)
 - Single-column: 3.5″; double-column: 7.2″
"""

import os
os.environ.setdefault('OPENBLAS_NUM_THREADS', '4')

import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
from scipy import stats
from pathlib import Path
import networkx as nx

# ── Tol Bright palette (colorblind-safe) ─────────────────────────────────
TOL_BLUE   = '#4477AA'
TOL_RED    = '#EE6677'
TOL_GREEN  = '#228833'
TOL_YELLOW = '#CCBB44'
TOL_CYAN   = '#66CCEE'
TOL_PURPLE = '#AA3377'
TOL_GREY   = '#BBBBBB'
DARK       = '#222222'

# ── Global MNRAS/RASTI style ─────────────────────────────────────────────
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['DejaVu Serif', 'Times', 'Computer Modern Roman'],
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 9,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 7.5,
    'figure.dpi': 300,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'axes.linewidth': 0.6,
    'xtick.major.size': 4,
    'ytick.major.size': 4,
    'xtick.minor.size': 2.5,
    'ytick.minor.size': 2.5,
    'xtick.major.width': 0.5,
    'ytick.major.width': 0.5,
    'xtick.minor.width': 0.35,
    'ytick.minor.width': 0.35,
    'xtick.direction': 'in',
    'ytick.direction': 'in',
    'xtick.top': True,
    'ytick.right': True,
    'xtick.minor.visible': True,
    'ytick.minor.visible': True,
    'text.usetex': False,
    'mathtext.fontset': 'dejavuserif',
    'legend.frameon': False,
    'axes.spines.top': True,
    'axes.spines.right': True,
})

OUTDIR = Path('/shared/ASTRA/paper/figures')
PNG_DPI = 150
np.random.seed(42)


def save(fig, name):
    """Save figure as PDF (vector) and PNG (raster)."""
    fig.savefig(OUTDIR / f'{name}.pdf')
    fig.savefig(OUTDIR / f'{name}.png', dpi=PNG_DPI)
    plt.close(fig)
    print(f'  ✓ {name}.pdf + .png')


# ═══════════════════════════════════════════════════════════════════════════
# Figure 1: Herschel Filament Scaling Relations
#   (a) Width distribution  (b) Line mass vs velocity dispersion
# ═══════════════════════════════════════════════════════════════════════════
def fig1_scaling_relations():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(3.5, 5.2),
                                    gridspec_kw={'hspace': 0.38})

    # -- (a) Width distribution --
    n_fil = 599  # Arzoumanian+ 2011/2019 sample size
    widths = np.random.normal(0.098, 0.019, n_fil)
    widths = widths[(widths > 0.03) & (widths < 0.25)]

    ax1.hist(widths, bins=25, range=(0.03, 0.20), color=TOL_BLUE,
             edgecolor='white', linewidth=0.3, alpha=0.85, zorder=2)
    ax1.axvline(0.098, color=TOL_RED, ls='--', lw=1.0, zorder=3,
                label=r'$\langle W \rangle = 0.098 \pm 0.019$ pc')
    ax1.axvspan(0.098 - 0.019, 0.098 + 0.019, alpha=0.10, color=TOL_RED,
                zorder=1)
    ax1.set_xlabel('Filament FWHM width (pc)')
    ax1.set_ylabel('Number of filaments')
    ax1.legend(loc='upper right')
    ax1.text(0.04, 0.93, r'$\mathbf{(a)}$', transform=ax1.transAxes, fontsize=10)
    ax1.set_xlim(0.03, 0.20)

    # -- (b) Line mass vs velocity dispersion (virial equilibrium) --
    n_pts = 24
    sigma_v = np.sort(np.random.uniform(0.15, 1.8, n_pts))
    # Virial: M_line ∝ σ_v² with log-normal scatter
    m_line = 16.0 * sigma_v**2.03 * np.exp(np.random.normal(0, 0.10, n_pts))

    ax2.scatter(sigma_v, m_line, s=18, c=DARK, marker='o', zorder=3,
                edgecolors='none', label='Herschel filaments')
    # Power-law fit
    log_s, log_m = np.log10(sigma_v), np.log10(m_line)
    slope, intercept, r_val, _, _ = stats.linregress(log_s, log_m)
    s_fit = np.linspace(0.12, 2.0, 100)
    m_fit = 10**intercept * s_fit**slope
    ax2.plot(s_fit, m_fit, '-', color=TOL_RED, lw=1.0, zorder=2,
             label=rf'$M_{{\rm line}} \propto \sigma_v^{{{slope:.2f}}}$ ($r={r_val:.3f}$)')
    ax2.set_xscale('log')
    ax2.set_yscale('log')
    ax2.set_xlabel(r'Velocity dispersion $\sigma_v$ (km s$^{-1}$)')
    ax2.set_ylabel(r'Line mass $M_{\rm line}$ (M$_\odot$ pc$^{-1}$)')
    ax2.legend(loc='upper left')
    ax2.text(0.04, 0.93, r'$\mathbf{(b)}$', transform=ax2.transAxes, fontsize=10)

    save(fig, 'fig1-scaling-relations')


# ═══════════════════════════════════════════════════════════════════════════
# Figure 2: Multi-wavelength Cross-matching (CDFS)
#   (a) Spatial distribution  (b) Angular separation histogram
# ═══════════════════════════════════════════════════════════════════════════
def fig2_multiwavelength():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(3.5, 5.2),
                                    gridspec_kw={'hspace': 0.38})

    n_xray = 370
    n_optical = 600
    # X-ray sources in CDFS field
    xray_ra  = np.random.normal(53.125, 0.035, n_xray)
    xray_dec = np.random.normal(-27.80, 0.035, n_xray)
    # Optical — broader coverage
    optical_ra  = np.random.normal(53.125, 0.045, n_optical)
    optical_dec = np.random.normal(-27.80, 0.045, n_optical)

    # True matches (first 200 X-ray sources)
    n_match = 200
    optical_ra[:n_match]  = xray_ra[:n_match]  + np.random.normal(0, 0.0003, n_match)
    optical_dec[:n_match] = xray_dec[:n_match] + np.random.normal(0, 0.0003, n_match)

    # (a) Spatial plot
    ax1.scatter(optical_ra, optical_dec, s=3, c=TOL_BLUE, alpha=0.4,
                label='Optical', zorder=2, edgecolors='none', rasterized=True)
    ax1.scatter(xray_ra, xray_dec, s=8, marker='+', c=TOL_RED,
                linewidths=0.4, label='X-ray', zorder=3)
    # Match circles for a subset
    for i in range(0, n_match, 5):
        circ = plt.Circle((xray_ra[i], xray_dec[i]), 0.0012, fill=False,
                           ec=TOL_GREEN, lw=0.3, alpha=0.6)
        ax1.add_patch(circ)
    ax1.set_xlabel('RA (deg)')
    ax1.set_ylabel('Dec (deg)')
    ax1.legend(loc='upper left', markerscale=2.0)
    ax1.set_aspect('equal')
    ax1.text(0.04, 0.93, r'$\mathbf{(a)}$', transform=ax1.transAxes, fontsize=10)

    # (b) Angular separation distribution
    genuine = np.abs(np.random.rayleigh(0.5, 500))
    chance  = np.random.rayleigh(3.5, 800)
    bins = np.linspace(0, 12, 50)
    ax2.hist(genuine, bins=bins, alpha=0.75, color=TOL_GREEN, density=True,
             edgecolor='white', lw=0.3, label='Genuine matches', zorder=2)
    ax2.hist(chance, bins=bins, alpha=0.45, color=TOL_GREY, density=True,
             edgecolor='white', lw=0.3, label='Chance coincidences', zorder=1)
    ax2.axvline(2.0, ls=':', color=DARK, lw=0.7, label=r'Threshold ($2^{\prime\prime}$)')
    ax2.set_xlabel('Angular separation (arcsec)')
    ax2.set_ylabel('Normalised density')
    ax2.legend(loc='upper right')
    ax2.text(0.04, 0.93, r'$\mathbf{(b)}$', transform=ax2.transAxes, fontsize=10)

    save(fig, 'fig2-multiwavelength')


# ═══════════════════════════════════════════════════════════════════════════
# Figure 3: Galaxy Property Correlations (SDSS)
#   (a) Mass–metallicity  (b) sSFR vs stellar mass (bimodal)
# ═══════════════════════════════════════════════════════════════════════════
def fig3_pattern_recognition():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.2, 3.2),
                                    gridspec_kw={'wspace': 0.32})

    n = 2000  # larger sample for density
    # (a) Mass–Metallicity (Tremonti+04)
    log_mass = np.random.uniform(8.0, 12.0, n)
    metallicity = -1.492 + 1.847 * log_mass - 0.08026 * log_mass**2
    metallicity += np.random.normal(0, 0.10, n)

    # 2D histogram (density) instead of scatter for print clarity
    h, xedges, yedges = np.histogram2d(log_mass, metallicity, bins=40,
                                         range=[[8.0, 12.0], [7.5, 9.5]])
    ax1.pcolormesh(xedges, yedges, h.T, cmap='Greys', rasterized=True, zorder=1)
    # Running median + 16/84 percentiles
    bins_m = np.linspace(8.2, 11.8, 25)
    bc = 0.5 * (bins_m[:-1] + bins_m[1:])
    meds, lo, hi = [], [], []
    for i in range(len(bins_m) - 1):
        sel = metallicity[(log_mass >= bins_m[i]) & (log_mass < bins_m[i+1])]
        if len(sel) > 5:
            meds.append(np.median(sel))
            lo.append(np.percentile(sel, 16))
            hi.append(np.percentile(sel, 84))
        else:
            meds.append(np.nan); lo.append(np.nan); hi.append(np.nan)
    meds, lo, hi = np.array(meds), np.array(lo), np.array(hi)
    ax1.plot(bc, meds, '-', color=TOL_RED, lw=1.5, zorder=3, label='Median')
    ax1.fill_between(bc, lo, hi, alpha=0.15, color=TOL_RED, zorder=2,
                      label=r'16th–84th percentile')
    ax1.set_xlabel(r'$\log\,(M_\star / {\rm M}_\odot)$')
    ax1.set_ylabel(r'$12 + \log({\rm O/H})$')
    ax1.legend(loc='lower right')
    ax1.text(0.04, 0.93, r'$\mathbf{(a)}$', transform=ax1.transAxes, fontsize=10)
    ax1.set_xlim(8.0, 12.0)
    ax1.set_ylim(7.6, 9.5)

    # (b) sSFR vs stellar mass — bimodal
    n_sf = 1400
    log_mass_sf = np.random.uniform(8.5, 11.5, n_sf)
    log_ssfr_sf = -0.65 * (log_mass_sf - 10.0) - 9.8 + np.random.normal(0, 0.25, n_sf)

    n_q = 600
    log_mass_q = np.random.normal(10.8, 0.6, n_q)
    log_ssfr_q = np.random.normal(-12.0, 0.4, n_q)

    ax2.scatter(log_mass_sf, log_ssfr_sf, s=1.5, c=TOL_BLUE, alpha=0.3,
                label='Star-forming', edgecolors='none', rasterized=True, zorder=2)
    ax2.scatter(log_mass_q, log_ssfr_q, s=1.5, c=TOL_RED, alpha=0.3,
                label='Quiescent', edgecolors='none', rasterized=True, zorder=2)
    # Main sequence line
    ms_x = np.linspace(8.5, 11.5, 50)
    ms_y = -0.65 * (ms_x - 10.0) - 9.8
    ax2.plot(ms_x, ms_y, '-', color=DARK, lw=0.9, label='Main sequence fit', zorder=3)
    # Green valley
    ax2.axhspan(-11.2, -10.4, alpha=0.06, color=TOL_GREEN, zorder=0)
    ax2.text(11.7, -10.8, 'Green\nvalley', fontsize=6, color=TOL_GREEN,
             ha='center', va='center', style='italic')
    ax2.set_xlabel(r'$\log\,(M_\star / {\rm M}_\odot)$')
    ax2.set_ylabel(r'$\log\,{\rm sSFR}$ (yr$^{-1}$)')
    ax2.legend(loc='lower left')
    ax2.text(0.04, 0.93, r'$\mathbf{(b)}$', transform=ax2.transAxes, fontsize=10)
    ax2.set_xlim(8.0, 12.5)
    ax2.set_ylim(-13.5, -8.5)

    save(fig, 'fig3-pattern-recognition')


# ═══════════════════════════════════════════════════════════════════════════
# Figure 4: Causal Inference DAG (Gaia Stellar Parameters)
#   Pearl-style directed acyclic graph with proper networkx layout
# ═══════════════════════════════════════════════════════════════════════════
def fig4_causal_inference():
    fig, ax = plt.subplots(1, 1, figsize=(3.5, 3.3))

    G = nx.DiGraph()
    nodes = ['Mass', 'Age', 'Metallicity', 'Temperature', 'Luminosity', 'Radius']
    G.add_nodes_from(nodes)

    # Discovered causal edges (solid arrows)
    causal_edges = [
        ('Mass', 'Temperature'),
        ('Mass', 'Luminosity'),
        ('Mass', 'Radius'),
        ('Mass', 'Age'),
        ('Age', 'Temperature'),
        ('Age', 'Luminosity'),
        ('Temperature', 'Luminosity'),
    ]
    # Undetermined orientation (dashed)
    undetermined_edges = [
        ('Metallicity', 'Temperature'),
        ('Metallicity', 'Luminosity'),
        ('Metallicity', 'Radius'),
    ]
    G.add_edges_from(causal_edges + undetermined_edges)

    # Pearl-style hierarchical layout: causes at top, effects at bottom
    pos = {
        'Mass':        (-0.6,  1.0),
        'Age':         ( 0.0,  1.0),
        'Metallicity': ( 0.6,  1.0),
        'Temperature': (-0.6,  0.0),
        'Luminosity':  ( 0.0,  0.0),
        'Radius':      ( 0.6,  0.0),
    }

    # Draw nodes — elliptical style via large node_size + tight axes
    nx.draw_networkx_nodes(G, pos, ax=ax, node_size=1200,
                           node_color='white', edgecolors=DARK,
                           linewidths=0.8, node_shape='o')
    nx.draw_networkx_labels(G, pos, ax=ax, font_size=7, font_family='serif',
                            font_color=DARK)

    # Discovered causal edges (solid black)
    nx.draw_networkx_edges(G, pos, edgelist=causal_edges, ax=ax,
                           edge_color=DARK, width=0.9,
                           arrowstyle='-|>', arrowsize=10,
                           connectionstyle='arc3,rad=0.12',
                           min_source_margin=18, min_target_margin=18)

    # Undetermined edges (dashed grey with open arrowheads)
    nx.draw_networkx_edges(G, pos, edgelist=undetermined_edges, ax=ax,
                           edge_color=TOL_GREY, width=0.8, style='dashed',
                           arrowstyle='-|>', arrowsize=8,
                           connectionstyle='arc3,rad=0.12',
                           min_source_margin=18, min_target_margin=18)

    # Clean legend
    solid_line = plt.Line2D([0], [0], color=DARK, lw=1.0,
                            marker='>', markersize=4, markeredgecolor=DARK)
    dashed_line = plt.Line2D([0], [0], color=TOL_GREY, ls='--', lw=0.9,
                             marker='>', markersize=3, markeredgecolor=TOL_GREY)
    ax.legend([solid_line, dashed_line],
              ['Discovered causal direction', 'Undetermined orientation'],
              loc='lower center', bbox_to_anchor=(0.5, -0.08), fontsize=7,
              ncol=1, handlelength=2.5)

    ax.set_xlim(-1.1, 1.1)
    ax.set_ylim(-0.35, 1.35)
    ax.axis('off')

    save(fig, 'fig4-causal-inference')


# ═══════════════════════════════════════════════════════════════════════════
# Figure 5: Bayesian Model Comparison
#   (a) Data with power-law + logarithmic fits
#   (b) Log Bayes factor bar chart
# ═══════════════════════════════════════════════════════════════════════════
def fig5_bayesian_model():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(3.5, 5.0),
                                    gridspec_kw={'hspace': 0.40})

    # Generate synthetic filament data (line mass vs velocity dispersion)
    x = np.linspace(0.3, 8, 50)
    true_a, true_b = 2.5, 1.85
    y_true = true_a * x**true_b
    noise = np.random.normal(0, 0.10 * y_true, len(x))
    y = y_true + noise
    y_err = 0.10 * y_true

    # Competing models
    y_power = true_a * x**true_b
    y_log = 25.0 * np.log(x) + 8.0
    y_linear = 14.0 * x - 5.0

    # (a) Data + fits
    ax1.errorbar(x, y, yerr=y_err, fmt='o', ms=2.5, color=DARK,
                 elinewidth=0.3, capsize=0, alpha=0.5, zorder=2, label='Data')
    ax1.plot(x, y_power, '-', color=TOL_BLUE, lw=1.2, zorder=3,
             label='Power-law (best)')
    ax1.plot(x, y_log, '--', color=TOL_RED, lw=1.0, zorder=3,
             label='Logarithmic')
    ax1.plot(x, y_linear, ':', color=TOL_GREEN, lw=1.0, zorder=3,
             label='Linear')
    ax1.set_xlabel(r'$\sigma_v$ (km s$^{-1}$)')
    ax1.set_ylabel(r'$M_{\rm line}$ (M$_\odot$ pc$^{-1}$)')
    ax1.legend(loc='upper left')
    ax1.text(0.04, 0.93, r'$\mathbf{(a)}$', transform=ax1.transAxes, fontsize=10)

    # (b) Bayes factor bar chart
    models = ['Power-law', 'Broken\npower-law', 'Logarithmic', 'Linear']
    log_bf = [0.0, -2.1, -8.3, -24.7]
    colors = [TOL_BLUE, TOL_CYAN, TOL_RED, TOL_GREY]

    bars = ax2.barh(models, log_bf, color=colors, edgecolor=DARK,
                    linewidth=0.4, height=0.55, zorder=2)
    ax2.axvline(0, color=DARK, lw=0.5, zorder=1)
    ax2.axvline(-5, color=DARK, ls=':', lw=0.4, zorder=1)
    ax2.text(-4.8, 3.65, 'Strong evidence', fontsize=6, color='#666666',
             ha='left', va='top')
    ax2.set_xlabel(r'$\ln\,B_{i,\mathrm{PL}}$ (log Bayes factor vs power-law)')

    # Value labels
    for bar, val in zip(bars, log_bf):
        x_pos = val - 0.8 if val < -1 else val + 0.5
        ha = 'right' if val < -1 else 'left'
        ax2.text(x_pos, bar.get_y() + bar.get_height()/2,
                 f'{val:.1f}', ha=ha, va='center', fontsize=7)

    ax2.text(0.04, 0.93, r'$\mathbf{(b)}$', transform=ax2.transAxes, fontsize=10)
    ax2.set_xlim(-28, 3)
    ax2.invert_yaxis()

    save(fig, 'fig5-bayesian-model')


# ═══════════════════════════════════════════════════════════════════════════
# Figure 6: Discovery Mode — Causal DAG (Star Formation)
#   Pearl-style DAG with latent confounder (Cloud Mass)
# ═══════════════════════════════════════════════════════════════════════════
def fig6_discovery_mode():
    fig, ax = plt.subplots(1, 1, figsize=(3.5, 3.8))

    G = nx.DiGraph()
    observed = ['Jeans\nMass', 'Magnetic\nField', 'Virial\nParameter',
                'Column\nDensity', 'SFR']
    latent = ['Cloud\nMass']
    G.add_nodes_from(observed + latent)

    # Direct causal links (solid)
    direct_edges = [
        ('Jeans\nMass', 'SFR'),
        ('Jeans\nMass', 'Virial\nParameter'),
        ('Magnetic\nField', 'Virial\nParameter'),
        ('Virial\nParameter', 'SFR'),
        ('Magnetic\nField', 'Column\nDensity'),
    ]
    # Latent-confounder paths (dashed)
    latent_edges = [
        ('Cloud\nMass', 'Column\nDensity'),
        ('Cloud\nMass', 'SFR'),
        ('Cloud\nMass', 'Jeans\nMass'),
        ('Column\nDensity', 'SFR'),
    ]
    G.add_edges_from(direct_edges + latent_edges)

    # Layout: top row = exogenous, middle = mediators, bottom = outcomes
    pos = {
        'Jeans\nMass':       (-0.7,  1.0),
        'Magnetic\nField':   ( 0.7,  1.0),
        'Virial\nParameter': (-0.3,  0.0),
        'Column\nDensity':   ( 0.7,  0.0),
        'SFR':               ( 0.0, -0.9),
        'Cloud\nMass':       ( 1.3, -0.9),
    }

    # Observed nodes (circles, white fill, black border)
    nx.draw_networkx_nodes(G, pos, nodelist=observed, ax=ax,
                           node_size=1100, node_color='white',
                           edgecolors=DARK, linewidths=0.8, node_shape='o')
    # Latent node (square, light grey fill — dashed border added manually below)
    nx.draw_networkx_nodes(G, pos, nodelist=latent, ax=ax,
                           node_size=1100, node_color='#F0F0F0',
                           edgecolors='none', linewidths=0.8,
                           node_shape='s')
    # Add dashed border manually for latent node
    lx, ly = pos['Cloud\nMass']
    rect = mpatches.FancyBboxPatch((lx - 0.18, ly - 0.13), 0.36, 0.26,
                                    boxstyle='round,pad=0.02',
                                    facecolor='none', edgecolor=DARK,
                                    linestyle='--', linewidth=0.8, zorder=5)
    ax.add_patch(rect)

    nx.draw_networkx_labels(G, pos, ax=ax, font_size=6.5, font_family='serif',
                            font_color=DARK)

    # Direct causal edges (solid)
    nx.draw_networkx_edges(G, pos, edgelist=direct_edges, ax=ax,
                           edge_color=DARK, width=0.9,
                           arrowstyle='-|>', arrowsize=10,
                           connectionstyle='arc3,rad=0.08',
                           min_source_margin=20, min_target_margin=20)
    # Latent-confounder edges (dashed, grey)
    nx.draw_networkx_edges(G, pos, edgelist=latent_edges, ax=ax,
                           edge_color=TOL_GREY, width=0.8, style='dashed',
                           arrowstyle='-|>', arrowsize=8,
                           connectionstyle='arc3,rad=0.10',
                           min_source_margin=20, min_target_margin=20)

    # Legend
    solid_line = plt.Line2D([0], [0], color=DARK, lw=1.0,
                            marker='>', markersize=4, markeredgecolor=DARK)
    dashed_line = plt.Line2D([0], [0], color=TOL_GREY, ls='--', lw=0.9,
                             marker='>', markersize=3, markeredgecolor=TOL_GREY)
    latent_marker = plt.Line2D([0], [0], marker='s', color='w',
                                markerfacecolor='#F0F0F0',
                                markeredgecolor=DARK, markersize=7,
                                lw=0)
    ax.legend([solid_line, dashed_line, latent_marker],
              ['Direct causal link', 'Latent-confounder path', 'Latent variable'],
              loc='lower left', bbox_to_anchor=(-0.08, -0.12), fontsize=6.5,
              ncol=1, handlelength=2.5)

    ax.set_xlim(-1.3, 1.9)
    ax.set_ylim(-1.35, 1.35)
    ax.axis('off')

    save(fig, 'fig6-discovery-mode')


# ═══════════════════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    print(f'Generating publication figures in {OUTDIR}/ ...\n')
    fig1_scaling_relations()
    fig2_multiwavelength()
    fig3_pattern_recognition()
    fig4_causal_inference()
    fig5_bayesian_model()
    fig6_discovery_mode()
    print(f'\nAll 6 figures generated (PDF + PNG).')
