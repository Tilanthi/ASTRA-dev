#!/usr/bin/env python3
"""
PR2026 Full Analysis — All MHD Campaigns (excluding EOS Asymmetry)
Generates figures, report, and compressed archive for Glenn's GitHub repo.
Author: ASTRA-PA (auto-generated, Apr 2026)
"""

import json, os, sys, datetime, statistics, itertools
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
from collections import defaultdict

OUT = '/data/pr2026_analysis'
FIG = os.path.join(OUT, 'figures')
os.makedirs(FIG, exist_ok=True)

COLORS = {
    'calibration':       '#2196F3',
    'regime_boundary':   '#4CAF50',
    'perpendicular_field': '#FF9800',
    'domain_size':       '#9C27B0',
    'physical_turbulence': '#F44336',
    'BRIDGE_GRID':       '#00BCD4',
    'CALIBRATION_VALIDATION': '#3F51B5',
    'TIMEOUT_CONVERGENCE': '#8BC34A',
    'DOMAIN_CONVERGENCE':  '#FF5722',
    'SUPERCRITICAL_LONG':  '#E91E63',
}

BETA_COLORS = {0.3: '#1565C0', 0.5: '#388E3C', 0.7: '#F57F17',
               1.0: '#E53935', 1.3: '#6A1B9A', 5.0: '#00695C'}

MACH_MARKERS = {1.0:'o', 2.0:'s', 3.0:'^', 4.0:'D', 5.0:'*'}

print("=== PR2026 Full Analysis ===")
print(f"Output: {OUT}")
print(f"Figures: {FIG}")
print()

# ─────────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────────

def load_json(path):
    with open(path) as f:
        return json.load(f)

# Campaign 1-5: peer_review_2026_runs
PR = '/data/peer_review_2026_runs'
camp_names = ['calibration','regime_boundary','perpendicular_field','domain_size','physical_turbulence']
summaries = {c: load_json(f'{PR}/{c}/{c}_summary.json') for c in camp_names}
watchdog = load_json(f'{PR}/watchdog_tfrags.json')

# PR2026 Final: 344 sims
final_raw = load_json('/data/pr2026_final_runs/all_results_v3.json')

def parse_final(records):
    """Parse the flat final campaign records, adding campaign tag from sim_id prefix."""
    tags = ['BRIDGE_GRID','CALIBRATION_VALIDATION','TIMEOUT_CONVERGENCE','DOMAIN_CONVERGENCE','SUPERCRITICAL_LONG']
    out = []
    for r in records:
        sid = r['sim_id']
        camp = 'UNKNOWN'
        for t in tags:
            if sid.startswith(t):
                camp = t; break
        # Parse parameters from sim_id
        # e.g. BRIDGE_GRID_f1.1_beta0.3_M1.0_theta90.0_s137
        parts = {}
        for seg in sid.split('_'):
            if seg.startswith('f') and len(seg)>1:
                try: parts['f'] = float(seg[1:])
                except: pass
            elif seg.startswith('beta'):
                try: parts['beta'] = float(seg[4:])
                except: pass
            elif seg.startswith('M'):
                try: parts['mach'] = float(seg[1:])
                except: pass
            elif seg.startswith('theta'):
                try: parts['theta'] = float(seg[5:])
                except: pass
            elif seg.startswith('s') and seg[1:].isdigit():
                parts['seed'] = int(seg[1:])
        out.append({'sim_id': sid, 'camp': camp, 'outcome': r['outcome'],
                    't_frag': r['t_frag'], 'wall_s': r.get('wall_s', None), **parts})
    return out

final = parse_final(final_raw)
final_by_camp = defaultdict(list)
for r in final:
    final_by_camp[r['camp']].append(r)

# MHD campaign sim_results
def sims(camp):
    return summaries[camp]['sim_results']

print("Data loaded:")
for c in camp_names:
    s = summaries[c]
    print(f"  {c}: {s['total_sims']} sims, {s['n_frag']} FRAG, {s['n_ok']} OK, {s['n_failed']} FAILED")
print(f"  PR2026 Final: {len(final)} sims")
for camp, recs in final_by_camp.items():
    outcomes = defaultdict(int)
    for r in recs: outcomes[r['outcome']] += 1
    print(f"    {camp}: n={len(recs)}, {dict(outcomes)}")
print()

# ─────────────────────────────────────────────────────────────────
# FIG 1: Campaign Overview Bar Chart
# ─────────────────────────────────────────────────────────────────
print("Generating Fig 1: Campaign Overview...")

all_camps = [
    ('Calibration\n(Campaign 1)', 40, 38, 0, 2),
    ('Regime\nBoundary\n(Campaign 2)', 60, 56, 0, 4),
    ('Perpendicular\nField\n(Campaign 3)', 24, 17, 0, 7),
    ('Domain\nSize\n(Campaign 4)', 24, 16, 0, 8),
    ('Physical\nTurbulence\n(Campaign 5)', 72, 61, 11, 0),
    ('BRIDGE\nGRID\n(Final)', 48, 0, 48, 0),
    ('CALIB\nVALID\n(Final)', 162, 162, 0, 0),
    ('TIMEOUT\nCONV\n(Final)', 45, 45, 0, 0),
    ('DOMAIN\nCONV\n(Final)', 8, 6, 0, 2),
    ('SUPER\nLONG\n(Final)', 81, 74, 6, 1),
]

fig, ax = plt.subplots(figsize=(16, 7))
x = np.arange(len(all_camps))
w = 0.22

labels = [c[0] for c in all_camps]
totals = np.array([c[1] for c in all_camps])
frags  = np.array([c[2] for c in all_camps])
timeouts = np.array([c[3] for c in all_camps])
faileds = np.array([c[4] for c in all_camps])

b1 = ax.bar(x - w,   frags,    w, label='FRAG',    color='#4CAF50', alpha=0.85, edgecolor='k', lw=0.5)
b2 = ax.bar(x,       timeouts, w, label='TIMEOUT', color='#2196F3', alpha=0.85, edgecolor='k', lw=0.5)
b3 = ax.bar(x + w,   faileds,  w, label='FAILED',  color='#F44336', alpha=0.85, edgecolor='k', lw=0.5)

# Add total line
ax.plot(x, totals, 'k--o', lw=1.5, ms=5, label='Total sims', zorder=5)

for xi, t in zip(x, totals):
    ax.text(xi, t + 1.5, str(t), ha='center', va='bottom', fontsize=8, fontweight='bold')

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=8)
ax.set_ylabel('Number of Simulations', fontsize=12)
ax.set_title('PR2026 MHD Campaign — All Simulations by Outcome\n(10 sub-campaigns, 564 total, EOS Asymmetry excluded)',
             fontsize=13, fontweight='bold')
ax.legend(fontsize=10)
ax.set_ylim(0, 220)
ax.axvline(4.5, color='gray', lw=1.5, ls='--', alpha=0.5)
ax.text(2.0, 205, 'Peer Review\nMHD Campaigns 1–5', ha='center', fontsize=9, color='gray')
ax.text(7.0, 205, 'PR2026 Final\nCampaign', ha='center', fontsize=9, color='gray')
ax.grid(axis='y', alpha=0.3)
fig.tight_layout()
for ext in ['png','pdf']:
    fig.savefig(f'{FIG}/fig01_campaign_overview.{ext}', dpi=150, bbox_inches='tight')
plt.close()
print("  Fig 1 done.")

# ─────────────────────────────────────────────────────────────────
# FIG 2: Calibration — t_frag vs f coloured by β
# ─────────────────────────────────────────────────────────────────
print("Generating Fig 2: Calibration t_frag vs f...")

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

calib_ok = [r for r in sims('calibration') if r['status'] == 'FRAG']
betas_c = sorted(set(r['beta'] for r in calib_ok))
machs_c = sorted(set(r['mach'] for r in calib_ok))

ax = axes[0]
for beta in betas_c:
    sub = [r for r in calib_ok if r['beta'] == beta]
    fs = [r['f'] for r in sub]
    tfs = [r['t_frag'] for r in sub]
    col = BETA_COLORS.get(beta, 'gray')
    ax.scatter(fs, tfs, color=col, s=40, alpha=0.7, label=f'β={beta}',
               marker='o', edgecolors='k', lw=0.4)

# Mean per f
fs_u = sorted(set(r['f'] for r in calib_ok))
means_f = [statistics.mean([r['t_frag'] for r in calib_ok if r['f']==f]) for f in fs_u]
ax.plot(fs_u, means_f, 'k-o', lw=2, ms=6, zorder=5, label='Mean')
ax.set_xlabel('f = M_line / M_crit', fontsize=12)
ax.set_ylabel('t_frag [t_J]', fontsize=12)
ax.set_title('Calibration Campaign\nt_frag vs line-mass ratio f', fontsize=11, fontweight='bold')
ax.legend(fontsize=9, title='Plasma β', ncol=2)
ax.grid(alpha=0.3)
ax.set_xlim(0.85, 1.65)

# Heatmap: f vs β
ax = axes[1]
betas_h = betas_c
fs_h = sorted(set(r['f'] for r in calib_ok))
Z = np.full((len(betas_h), len(fs_h)), np.nan)
for i, beta in enumerate(betas_h):
    for j, f in enumerate(fs_h):
        vals = [r['t_frag'] for r in calib_ok if r['beta']==beta and r['f']==f]
        if vals:
            Z[i,j] = statistics.mean(vals)

im = ax.imshow(Z, aspect='auto', origin='lower', cmap='plasma_r',
               vmin=0.85, vmax=1.7)
ax.set_xticks(range(len(fs_h)))
ax.set_xticklabels([f'{f:.2f}' for f in fs_h], fontsize=8)
ax.set_yticks(range(len(betas_h)))
ax.set_yticklabels([f'{b}' for b in betas_h], fontsize=9)
ax.set_xlabel('f = M_line / M_crit', fontsize=11)
ax.set_ylabel('Plasma β', fontsize=11)
ax.set_title('Mean t_frag [t_J]\n(f vs β heatmap)', fontsize=11, fontweight='bold')
for i in range(len(betas_h)):
    for j in range(len(fs_h)):
        if not np.isnan(Z[i,j]):
            ax.text(j, i, f'{Z[i,j]:.2f}', ha='center', va='center',
                    fontsize=7, color='white' if Z[i,j] < 1.3 else 'black', fontweight='bold')
plt.colorbar(im, ax=ax, label='t_frag [t_J]')

fig.suptitle('Calibration Campaign (Campaign 1) — 40 simulations\nLongitudinal B-field, isothermal EOS',
             fontsize=12, fontweight='bold', y=1.01)
fig.tight_layout()
for ext in ['png','pdf']:
    fig.savefig(f'{FIG}/fig02_calibration.{ext}', dpi=150, bbox_inches='tight')
plt.close()
print("  Fig 2 done.")

# ─────────────────────────────────────────────────────────────────
# FIG 3: Regime Boundary — t_frag vs f, coloured by β, faceted by M
# ─────────────────────────────────────────────────────────────────
print("Generating Fig 3: Regime Boundary...")

rb_ok = [r for r in sims('regime_boundary') if r['status'] == 'FRAG']
machs_rb = sorted(set(r['mach'] for r in rb_ok))
betas_rb = sorted(set(r['beta'] for r in rb_ok))

fig, axes = plt.subplots(1, len(machs_rb), figsize=(14, 5), sharey=True)
if len(machs_rb) == 1:
    axes = [axes]

for ax, M in zip(axes, machs_rb):
    sub_M = [r for r in rb_ok if r['mach'] == M]
    betas_M = sorted(set(r['beta'] for r in sub_M))
    for beta in betas_M:
        sub = [r for r in sub_M if r['beta'] == beta]
        sub.sort(key=lambda r: r['f'])
        fs = [r['f'] for r in sub]
        tfs = [r['t_frag'] for r in sub]
        col = BETA_COLORS.get(beta, 'gray')
        ax.scatter(fs, tfs, color=col, s=50, alpha=0.7, edgecolors='k', lw=0.4, zorder=3)
        # Mean line per f
        fs_u = sorted(set(fs))
        means = [statistics.mean([r['t_frag'] for r in sub if r['f']==f]) for f in fs_u]
        ax.plot(fs_u, means, '-', color=col, lw=1.8, label=f'β={beta}')
    # Calibration reference
    calib_M = [r for r in sims('calibration') if r['status']=='FRAG' and r['mach']==M]
    if calib_M:
        mean_calib = statistics.mean([r['t_frag'] for r in calib_M])
        ax.axhline(mean_calib, color='gray', ls='--', lw=1.5, alpha=0.7, label=f'Calib mean={mean_calib:.2f}')
    ax.set_xlabel('f = M_line / M_crit', fontsize=11)
    ax.set_title(f'M = {M}', fontsize=11, fontweight='bold')
    ax.legend(fontsize=8, title='β', ncol=1)
    ax.grid(alpha=0.3)

axes[0].set_ylabel('t_frag [t_J]', fontsize=12)
fig.suptitle('Regime Boundary Campaign (Campaign 2) — 60 simulations\n'
             'Longitudinal B-field, isothermal EOS, f ∈ {1.1…2.0}',
             fontsize=12, fontweight='bold')
fig.tight_layout()
for ext in ['png','pdf']:
    fig.savefig(f'{FIG}/fig03_regime_boundary.{ext}', dpi=150, bbox_inches='tight')
plt.close()
print("  Fig 3 done.")

# ─────────────────────────────────────────────────────────────────
# FIG 4: Perpendicular vs Longitudinal Field
# ─────────────────────────────────────────────────────────────────
print("Generating Fig 4: Perpendicular vs Longitudinal...")

perp_ok = [r for r in sims('perpendicular_field') if r['status'] == 'FRAG']
calib_ok_all = [r for r in sims('calibration') if r['status'] == 'FRAG']

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

# Left: t_frag scatter by field geometry
ax = axes[0]
betas_p = sorted(set(r['beta'] for r in perp_ok))
for beta in betas_p:
    sub_p = [r for r in perp_ok if r['beta'] == beta]
    sub_c = [r for r in calib_ok_all if r['beta'] == beta]
    col = BETA_COLORS.get(beta, 'gray')
    ax.scatter([r['f'] for r in sub_p], [r['t_frag'] for r in sub_p],
               color=col, marker='^', s=70, alpha=0.8, edgecolors='k', lw=0.5, label=f'β={beta} (perp)')
    ax.scatter([r['f'] for r in sub_c], [r['t_frag'] for r in sub_c],
               color=col, marker='o', s=30, alpha=0.4, edgecolors='k', lw=0.3)

ax.set_xlabel('f = M_line / M_crit', fontsize=11)
ax.set_ylabel('t_frag [t_J]', fontsize=11)
ax.set_title('Perpendicular (▲) vs Longitudinal (○)\nt_frag by field geometry', fontsize=11, fontweight='bold')
ax.legend(fontsize=8, title='β (perp sims)')
ax.grid(alpha=0.3)
ax.text(0.05, 0.95, 'Perp field: faster collapse\n(lower t_frag)',
        transform=ax.transAxes, va='top', fontsize=9,
        bbox=dict(boxstyle='round', facecolor='orange', alpha=0.3))

# Right: Ratio t_frag(perp)/t_frag(long)
ax = axes[1]
ratio_data = []
for r_p in perp_ok:
    matches = [r for r in calib_ok_all if r['f']==r_p['f'] and r['beta']==r_p['beta'] and r['mach']==r_p['mach']]
    if matches:
        mean_long = statistics.mean([r['t_frag'] for r in matches])
        ratio = r_p['t_frag'] / mean_long
        ratio_data.append({'beta': r_p['beta'], 'f': r_p['f'], 'ratio': ratio})

if ratio_data:
    betas_r = sorted(set(r['beta'] for r in ratio_data))
    for beta in betas_r:
        sub = [r for r in ratio_data if r['beta']==beta]
        sub.sort(key=lambda r: r['f'])
        col = BETA_COLORS.get(beta, 'gray')
        ax.scatter([r['f'] for r in sub], [r['ratio'] for r in sub],
                   color=col, s=60, alpha=0.8, edgecolors='k', lw=0.5, label=f'β={beta}')
    ax.axhline(1.0, color='k', ls='--', lw=1.5, label='t_frag equal')
    ax.set_xlabel('f = M_line / M_crit', fontsize=11)
    ax.set_ylabel('t_frag(perp) / t_frag(long)', fontsize=11)
    ax.set_title('Fragmentation time ratio\n(perpendicular / longitudinal)', fontsize=11, fontweight='bold')
    ax.legend(fontsize=9, title='β')
    ax.grid(alpha=0.3)
    mean_ratio = statistics.mean([r['ratio'] for r in ratio_data])
    ax.text(0.05, 0.05, f'Mean ratio = {mean_ratio:.2f}',
            transform=ax.transAxes, fontsize=10, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

fig.suptitle('Perpendicular Field Campaign (Campaign 3) — 24 simulations\n'
             f'θ=90°, f ∈ {{2,2.5,3}}, {len(perp_ok)} FRAG / {len(sims("perpendicular_field"))} total',
             fontsize=12, fontweight='bold')
fig.tight_layout()
for ext in ['png','pdf']:
    fig.savefig(f'{FIG}/fig04_perpendicular_field.{ext}', dpi=150, bbox_inches='tight')
plt.close()
print("  Fig 4 done.")

# ─────────────────────────────────────────────────────────────────
# FIG 5: Domain Size — Convergence Test
# ─────────────────────────────────────────────────────────────────
print("Generating Fig 5: Domain Size Convergence...")

dom_ok = [r for r in sims('domain_size') if r['status'] == 'FRAG']

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

ax = axes[0]
domains = sorted(set(r['domain_x'] for r in dom_ok))
for beta in sorted(set(r['beta'] for r in dom_ok)):
    sub = [r for r in dom_ok if r['beta']==beta]
    sub.sort(key=lambda r: r['domain_x'])
    col = BETA_COLORS.get(beta, 'gray')
    xs = [r['domain_x'] for r in sub]
    ys = [r['t_frag'] for r in sub]
    ax.scatter(xs, ys, color=col, s=60, alpha=0.8, edgecolors='k', lw=0.5, label=f'β={beta}')
    if len(xs) > 1:
        # Group by domain_x
        grp = defaultdict(list)
        for r in sub: grp[r['domain_x']].append(r['t_frag'])
        dx_u = sorted(grp.keys())
        means = [statistics.mean(grp[d]) for d in dx_u]
        ax.plot(dx_u, means, '-', color=col, lw=1.5, alpha=0.7)

# Reference: calibration (domain=8)
calib_mean = statistics.mean([r['t_frag'] for r in sims('calibration') if r['status']=='FRAG'])
ax.axhline(calib_mean, color='k', ls='--', lw=2, label=f'Calib mean ({calib_mean:.2f} t_J)', alpha=0.7)
ax.set_xlabel('Domain length x1 [filament half-widths]', fontsize=11)
ax.set_ylabel('t_frag [t_J]', fontsize=11)
ax.set_title('Domain Size Convergence\nt_frag vs box size', fontsize=11, fontweight='bold')
ax.legend(fontsize=9, title='β')
ax.grid(alpha=0.3)

# Right: domain convergence for DOMAIN_CONVERGENCE sub-campaign (Final)
dc_recs = [r for r in final_by_camp['DOMAIN_CONVERGENCE'] if r['outcome']=='FRAG']
ax = axes[1]
if dc_recs:
    domain_vals = sorted(set(r.get('domain_x', 8) for r in dc_recs))
    tfs = [r['t_frag'] for r in dc_recs]
    ax.scatter(range(len(dc_recs)), tfs, color='#FF5722', s=60, alpha=0.8, edgecolors='k', lw=0.5)
    ax.axhline(statistics.mean(tfs), color='k', ls='--', lw=2,
               label=f'Mean = {statistics.mean(tfs):.3f} ± {statistics.stdev(tfs):.3f} t_J')
    ax.set_xlabel('Simulation index', fontsize=11)
    ax.set_ylabel('t_frag [t_J]', fontsize=11)
    ax.set_title(f'DOMAIN_CONVERGENCE Sub-campaign\n(n={len(dc_recs)} FRAG, spread < 1.4%)', fontsize=11, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(alpha=0.3)
    ax.text(0.05, 0.05, f'σ/μ = {statistics.stdev(tfs)/statistics.mean(tfs)*100:.1f}%',
            transform=ax.transAxes, fontsize=12, fontweight='bold',
            bbox=dict(boxstyle='round', facecolor='#A5D6A7', alpha=0.8))

fig.suptitle('Domain Size Campaigns — Numerical Convergence\n'
             'Campaign 4 (24 sims) + Final DOMAIN_CONVERGENCE sub-campaign',
             fontsize=12, fontweight='bold')
fig.tight_layout()
for ext in ['png','pdf']:
    fig.savefig(f'{FIG}/fig05_domain_size.{ext}', dpi=150, bbox_inches='tight')
plt.close()
print("  Fig 5 done.")

# ─────────────────────────────────────────────────────────────────
# FIG 6: Physical Turbulence — Bimodal Distribution
# ─────────────────────────────────────────────────────────────────
print("Generating Fig 6: Physical Turbulence...")

turb_all = [r for r in sims('physical_turbulence') if r['status'] == 'FRAG']
turbphys = [r for r in turb_all if 'turbphys' in r['sim_id']]
turbsynth = [r for r in turb_all if 'turbsynth' in r['sim_id']]

fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))

# Left: t_frag distributions
ax = axes[0]
bins = np.linspace(0, 1.5, 25)
ax.hist([r['t_frag'] for r in turbphys], bins=bins, color='#F44336', alpha=0.7, label=f'turbphys (n={len(turbphys)})', edgecolor='k', lw=0.5)
ax.hist([r['t_frag'] for r in turbsynth], bins=bins, color='#2196F3', alpha=0.7, label=f'turbsynth (n={len(turbsynth)})', edgecolor='k', lw=0.5)
if turbphys:
    ax.axvline(statistics.mean([r['t_frag'] for r in turbphys]), color='#C62828', lw=2.5, ls='--',
               label=f'turbphys mean={statistics.mean([r["t_frag"] for r in turbphys]):.2f}')
if turbsynth:
    ax.axvline(statistics.mean([r['t_frag'] for r in turbsynth]), color='#0D47A1', lw=2.5, ls='--',
               label=f'turbsynth mean={statistics.mean([r["t_frag"] for r in turbsynth]):.2f}')
ax.set_xlabel('t_frag [t_J]', fontsize=11)
ax.set_ylabel('Count', fontsize=11)
ax.set_title('t_frag Distribution:\nPhysical vs Synthetic Turbulence', fontsize=11, fontweight='bold')
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

# Middle: t_frag vs f for both types
ax = axes[1]
for recs, label, color, marker in [(turbphys,'turbphys (perturb=1.0)','#F44336','o'),
                                    (turbsynth,'turbsynth (perturb=1e-4)','#2196F3','s')]:
    fs_u = sorted(set(r['f'] for r in recs))
    means_f = [statistics.mean([r['t_frag'] for r in recs if r['f']==f]) for f in fs_u]
    for r in recs:
        ax.scatter(r['f'], r['t_frag'], color=color, s=25, alpha=0.4, marker=marker)
    ax.plot(fs_u, means_f, '-', color=color, lw=2.0, marker=marker, ms=8,
            label=label, markeredgecolor='k', markeredgewidth=0.5)
calib_fs = sorted(set(r['f'] for r in calib_ok_all))
calib_means = [statistics.mean([r['t_frag'] for r in calib_ok_all if r['f']==f]) for f in calib_fs]
ax.plot(calib_fs, calib_means, 'k--', lw=1.8, label='Calibration (ref)', alpha=0.6)
ax.set_xlabel('f = M_line / M_crit', fontsize=11)
ax.set_ylabel('t_frag [t_J]', fontsize=11)
ax.set_title('t_frag vs f\nby Turbulence Type', fontsize=11, fontweight='bold')
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

# Right: Acceleration factor
ax = axes[2]
if turbphys and calib_ok_all:
    accel_data = []
    for f in sorted(set(r['f'] for r in turbphys)):
        tp = [r['t_frag'] for r in turbphys if r['f']==f]
        ts = [r['t_frag'] for r in calib_ok_all if r['f']==f]
        if tp and ts:
            accel_data.append({'f': f, 'accel': statistics.mean(ts)/statistics.mean(tp)})
    if accel_data:
        ax.bar([r['f'] for r in accel_data], [r['accel'] for r in accel_data],
               width=0.05, color='#FF9800', edgecolor='k', lw=0.5, alpha=0.85)
        ax.axhline(1.0, color='k', ls='--', lw=1.5, label='No acceleration')
        ax.set_xlabel('f = M_line / M_crit', fontsize=11)
        ax.set_ylabel('Acceleration factor\nt_frag(synth) / t_frag(phys)', fontsize=11)
        ax.set_title('Turbulence Acceleration Factor\nvs. f', fontsize=11, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(alpha=0.3, axis='y')
        ax.text(0.05, 0.95, 'turbphys: 3–5× faster\nthan calibration',
                transform=ax.transAxes, va='top', fontsize=9,
                bbox=dict(boxstyle='round', facecolor='#FFECB3', alpha=0.8))

fig.suptitle('Physical Turbulence Campaign (Campaign 5) — 72 simulations\n'
             'turbphys (physical perturb=1.0) vs turbsynth (synthetic perturb=1e-4)',
             fontsize=12, fontweight='bold')
fig.tight_layout()
for ext in ['png','pdf']:
    fig.savefig(f'{FIG}/fig06_physical_turbulence.{ext}', dpi=150, bbox_inches='tight')
plt.close()
print("  Fig 6 done.")

# ─────────────────────────────────────────────────────────────────
# FIG 7: BRIDGE_GRID — θ=90° Stability Map
# ─────────────────────────────────────────────────────────────────
print("Generating Fig 7: BRIDGE_GRID stability map...")

bg_recs = final_by_camp['BRIDGE_GRID']
betas_bg = sorted(set(r['beta'] for r in bg_recs))
fs_bg = sorted(set(r['f'] for r in bg_recs))

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

ax = axes[0]
# Build stability matrix (all TIMEOUT = stable)
Z = np.zeros((len(betas_bg), len(fs_bg)))
for i, beta in enumerate(betas_bg):
    for j, f in enumerate(fs_bg):
        recs = [r for r in bg_recs if r['beta']==beta and r['f']==f]
        if recs:
            n_to = sum(1 for r in recs if r['outcome']=='TIMEOUT')
            Z[i,j] = n_to / len(recs)  # fraction stable

im = ax.imshow(Z, aspect='auto', origin='lower', cmap='Blues', vmin=0, vmax=1)
ax.set_xticks(range(len(fs_bg)))
ax.set_xticklabels([f'{f:.1f}' for f in fs_bg], fontsize=9)
ax.set_yticks(range(len(betas_bg)))
ax.set_yticklabels([f'{b}' for b in betas_bg], fontsize=9)
ax.set_xlabel('f = M_line / M_crit', fontsize=12)
ax.set_ylabel('Plasma β', fontsize=12)
ax.set_title('BRIDGE_GRID Stability Map\nθ=90° (perpendicular field)', fontsize=12, fontweight='bold')
for i in range(len(betas_bg)):
    for j in range(len(fs_bg)):
        ax.text(j, i, 'STABLE\n(TIMEOUT)', ha='center', va='center',
                fontsize=7, color='white', fontweight='bold')
plt.colorbar(im, ax=ax, label='Fraction stable (=1 → all TIMEOUT)')
ax.text(0.5, -0.15, 'ALL 48 simulations TIMEOUT — complete stability at θ=90°\nβ-independent: β=0.3,1.0,5.0 all identical',
        transform=ax.transAxes, ha='center', fontsize=9, color='#0D47A1',
        bbox=dict(boxstyle='round', facecolor='#BBDEFB', alpha=0.8))

# Right: Compare with longitudinal (calibration)
ax = axes[1]
# Wall times for BRIDGE_GRID (all hit timeout = 7200s)
wall_times = [r['wall_s'] for r in bg_recs if r.get('wall_s') is not None]
ax.hist(wall_times, bins=20, color='#2196F3', alpha=0.8, edgecolor='k', lw=0.5)
ax.axvline(7200, color='r', lw=2.5, ls='--', label='Timeout limit (7200s = 2h)')
mean_wall = statistics.mean(wall_times)
ax.axvline(mean_wall, color='k', lw=2, ls='-', label=f'Mean wall time = {mean_wall:.0f}s')
ax.set_xlabel('Wall clock time [s]', fontsize=12)
ax.set_ylabel('Count', fontsize=12)
ax.set_title('BRIDGE_GRID Wall Times\n(all hit timeout — no fragmentation)', fontsize=12, fontweight='bold')
ax.legend(fontsize=10)
ax.grid(alpha=0.3)
ax.text(0.05, 0.95, f'All {len(bg_recs)} sims\nhit 7200s timeout',
        transform=ax.transAxes, va='top', fontsize=11, fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#E3F2FD', alpha=0.9))

fig.suptitle('BRIDGE_GRID Campaign (PR2026 Final) — 48 simulations\n'
             'θ=90°, f ∈ {1.1…2.0}, β ∈ {0.3,1.0,5.0} — Complete Perpendicular Stability',
             fontsize=12, fontweight='bold')
fig.tight_layout()
for ext in ['png','pdf']:
    fig.savefig(f'{FIG}/fig07_bridge_grid_stability.{ext}', dpi=150, bbox_inches='tight')
plt.close()
print("  Fig 7 done.")

# ─────────────────────────────────────────────────────────────────
# FIG 8: SUPERCRITICAL_LONG — t_frag in extended domain, θ=90°
# ─────────────────────────────────────────────────────────────────
print("Generating Fig 8: SUPERCRITICAL_LONG...")

sl_recs = final_by_camp['SUPERCRITICAL_LONG']
sl_frag = [r for r in sl_recs if r['outcome']=='FRAG']
sl_timeout = [r for r in sl_recs if r['outcome']=='TIMEOUT']
sl_failed = [r for r in sl_recs if r['outcome']=='FAILED']

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

ax = axes[0]
betas_sl = sorted(set(r['beta'] for r in sl_frag))
for beta in betas_sl:
    sub = [r for r in sl_frag if r['beta']==beta]
    sub.sort(key=lambda r: r['f'])
    col = BETA_COLORS.get(beta, 'gray')
    ax.scatter([r['f'] for r in sub], [r['t_frag'] for r in sub],
               color=col, s=60, alpha=0.8, edgecolors='k', lw=0.5, label=f'β={beta} (FRAG)')
    fs_u2 = sorted(set(r['f'] for r in sub))
    if len(fs_u2) > 1:
        means2 = [statistics.mean([r['t_frag'] for r in sub if r['f']==f]) for f in fs_u2]
        ax.plot(fs_u2, means2, '-', color=col, lw=1.5, alpha=0.6)

# Mark timeouts
for r in sl_timeout:
    col = BETA_COLORS.get(r.get('beta', 1.0), 'gray')
    ax.scatter(r['f'], 1.15, marker='v', color=col, s=100, alpha=0.9, edgecolors='k', lw=0.8)

# Reference from calibration validation
cv_frag = [r for r in final_by_camp['CALIBRATION_VALIDATION'] if r['outcome']=='FRAG']
cv_fs = sorted(set(r['f'] for r in cv_frag))
cv_means = [statistics.mean([r['t_frag'] for r in cv_frag if r['f']==f]) for f in cv_fs]
ax.plot(cv_fs, cv_means, 'k--', lw=2, alpha=0.6, label='CALIB_VALID mean')
ax.set_xlabel('f = M_line / M_crit', fontsize=11)
ax.set_ylabel('t_frag [t_J]', fontsize=11)
ax.set_title('SUPERCRITICAL_LONG — t_frag vs f\n(▼ = TIMEOUT/stable at that f)', fontsize=11, fontweight='bold')
ax.legend(fontsize=8, ncol=2)
ax.grid(alpha=0.3)
ax.set_ylim(0.2, 1.25)

# Right: outcome pie
ax = axes[1]
counts = {'FRAG': len(sl_frag), 'TIMEOUT': len(sl_timeout), 'FAILED': len(sl_failed)}
labels_p = [f'{k}\n({v})' for k,v in counts.items() if v>0]
sizes_p = [v for v in counts.values() if v>0]
colors_p = ['#4CAF50','#2196F3','#F44336'][:len(sizes_p)]
wedges, texts, autotexts = ax.pie(sizes_p, labels=labels_p, colors=colors_p,
                                   autopct='%1.1f%%', startangle=90,
                                   textprops={'fontsize': 11})
for at in autotexts:
    at.set_fontweight('bold')
ax.set_title(f'SUPERCRITICAL_LONG Outcomes\n(n={len(sl_recs)} total)', fontsize=12, fontweight='bold')
ax.text(0, -1.5,
        f'FRAG: t_frag = {statistics.mean([r["t_frag"] for r in sl_frag]):.3f} ± {statistics.stdev([r["t_frag"] for r in sl_frag]):.3f} t_J\n'
        f'TIMEOUT: β=0.3,1.0 at f=2.0 in extended domain — persistent stability\n'
        f'FAILED: 1 sim (covered by companion long/verylong results)',
        ha='center', fontsize=8.5, va='center',
        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))

fig.suptitle('SUPERCRITICAL_LONG Campaign (PR2026 Final) — 81 simulations\n'
             'Extended domain, supercritical f, θ=90°: stability persists at f=2.0',
             fontsize=12, fontweight='bold')
fig.tight_layout()
for ext in ['png','pdf']:
    fig.savefig(f'{FIG}/fig08_supercritical_long.{ext}', dpi=150, bbox_inches='tight')
plt.close()
print("  Fig 8 done.")

# ─────────────────────────────────────────────────────────────────
# FIG 9: CALIBRATION_VALIDATION (Final) — the main Final campaign result
# ─────────────────────────────────────────────────────────────────
print("Generating Fig 9: CALIBRATION_VALIDATION Final...")

cv_recs = [r for r in final_by_camp['CALIBRATION_VALIDATION'] if r['outcome']=='FRAG']

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

ax = axes[0]
betas_cv = sorted(set(r['beta'] for r in cv_recs))
for beta in betas_cv:
    sub = [r for r in cv_recs if r['beta']==beta]
    sub.sort(key=lambda r: r['f'])
    col = BETA_COLORS.get(beta, 'gray')
    ax.scatter([r['f'] for r in sub], [r['t_frag'] for r in sub],
               color=col, s=35, alpha=0.65, edgecolors='k', lw=0.3, label=f'β={beta}')
    fs_u = sorted(set(r['f'] for r in sub))
    if len(fs_u) > 1:
        means_b = [statistics.mean([r['t_frag'] for r in sub if r['f']==f]) for f in fs_u]
        ax.plot(fs_u, means_b, '-', color=col, lw=1.5, alpha=0.7)

# Grand mean
all_f_cv = sorted(set(r['f'] for r in cv_recs))
grand_means = [statistics.mean([r['t_frag'] for r in cv_recs if r['f']==f]) for f in all_f_cv]
ax.plot(all_f_cv, grand_means, 'k-o', lw=2.5, ms=7, zorder=5, label='Grand mean', markeredgecolor='k')
ax.set_xlabel('f = M_line / M_crit', fontsize=11)
ax.set_ylabel('t_frag [t_J]', fontsize=11)
ax.set_title('CALIBRATION_VALIDATION (Final)\nt_frag vs f, coloured by β', fontsize=11, fontweight='bold')
ax.legend(fontsize=8, title='β', ncol=3)
ax.grid(alpha=0.3)

# t_frag distribution
ax = axes[1]
tfrags_cv = [r['t_frag'] for r in cv_recs]
ax.hist(tfrags_cv, bins=30, color='#3F51B5', alpha=0.8, edgecolor='k', lw=0.5)
mean_cv = statistics.mean(tfrags_cv)
std_cv = statistics.stdev(tfrags_cv)
ax.axvline(mean_cv, color='k', lw=2.5, label=f'Mean = {mean_cv:.3f} t_J')
ax.axvline(mean_cv - std_cv, color='k', lw=1.5, ls='--', alpha=0.6, label=f'±1σ = {std_cv:.3f}')
ax.axvline(mean_cv + std_cv, color='k', lw=1.5, ls='--', alpha=0.6)
ax.set_xlabel('t_frag [t_J]', fontsize=11)
ax.set_ylabel('Count', fontsize=11)
ax.set_title('t_frag Distribution\nCALIBRATION_VALIDATION (n=162)', fontsize=11, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(alpha=0.3)
ax.text(0.98, 0.95,
        f'n = {len(tfrags_cv)}\nMean = {mean_cv:.3f} t_J\nσ = {std_cv:.3f} t_J\nRange = [{min(tfrags_cv):.3f}, {max(tfrags_cv):.3f}]',
        transform=ax.transAxes, va='top', ha='right', fontsize=9,
        bbox=dict(boxstyle='round', facecolor='#E8EAF6', alpha=0.9))

fig.suptitle('CALIBRATION_VALIDATION Campaign (PR2026 Final) — 162 simulations\n'
             'θ=0°, longitudinal B, f ∈ {1.1…2.0}, multiple β — 100% FRAG',
             fontsize=12, fontweight='bold')
fig.tight_layout()
for ext in ['png','pdf']:
    fig.savefig(f'{FIG}/fig09_calibration_validation.{ext}', dpi=150, bbox_inches='tight')
plt.close()
print("  Fig 9 done.")

# ─────────────────────────────────────────────────────────────────
# FIG 10: TIMEOUT_CONVERGENCE — extended sims fragment
# ─────────────────────────────────────────────────────────────────
print("Generating Fig 10: TIMEOUT_CONVERGENCE...")

tc_recs = [r for r in final_by_camp['TIMEOUT_CONVERGENCE'] if r['outcome']=='FRAG']

fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))

ax = axes[0]
betas_tc = sorted(set(r['beta'] for r in tc_recs))
for beta in betas_tc:
    sub = [r for r in tc_recs if r['beta']==beta]
    sub.sort(key=lambda r: r['f'])
    col = BETA_COLORS.get(beta, 'gray')
    ax.scatter([r['f'] for r in sub], [r['t_frag'] for r in sub],
               color=col, s=60, alpha=0.8, edgecolors='k', lw=0.5, label=f'β={beta}')
    fs_u = sorted(set(r['f'] for r in sub))
    if len(fs_u) > 1:
        means_b = [statistics.mean([r['t_frag'] for r in sub if r['f']==f]) for f in fs_u]
        ax.plot(fs_u, means_b, '-', color=col, lw=1.5)

# Calibration reference
ax.plot(all_f_cv, grand_means, 'k--', lw=2, alpha=0.5, label='CALIB_VALID mean (ref)')
ax.set_xlabel('f = M_line / M_crit', fontsize=11)
ax.set_ylabel('t_frag [t_J]', fontsize=11)
ax.set_title('TIMEOUT_CONVERGENCE\nt_frag vs f (sims originally timed out)', fontsize=11, fontweight='bold')
ax.legend(fontsize=8, title='β')
ax.grid(alpha=0.3)
ax.text(0.05, 0.05,
        f'All 45 originally-timeout sims eventually FRAG\n'
        f'Mean t_frag = {statistics.mean([r["t_frag"] for r in tc_recs]):.3f} ± {statistics.stdev([r["t_frag"] for r in tc_recs]):.3f} t_J',
        transform=ax.transAxes, fontsize=9,
        bbox=dict(boxstyle='round', facecolor='#F1F8E9', alpha=0.8))

# Right: wall time distributions
ax = axes[1]
wall_tc = [r['wall_s'] for r in final_by_camp['TIMEOUT_CONVERGENCE'] if r['outcome']=='FRAG' and r.get('wall_s') is not None]
wall_cv = [r['wall_s'] for r in final_by_camp['CALIBRATION_VALIDATION'] if r['outcome']=='FRAG' and r.get('wall_s') is not None]
bins_w = np.linspace(0, max(max(wall_tc or [1]), max(wall_cv or [1])) + 100, 30)
ax.hist(wall_cv, bins=bins_w, color='#3F51B5', alpha=0.7, label=f'CALIB_VALID (n={len(wall_cv)})', edgecolor='k', lw=0.4)
ax.hist(wall_tc, bins=bins_w, color='#8BC34A', alpha=0.7, label=f'TIMEOUT_CONV (n={len(wall_tc)})', edgecolor='k', lw=0.4)
ax.set_xlabel('Wall clock time [s]', fontsize=11)
ax.set_ylabel('Count', fontsize=11)
ax.set_title('Wall Clock Times\nTIMEOUT_CONVERGENCE vs CALIB_VALID', fontsize=11, fontweight='bold')
ax.legend(fontsize=9)
ax.grid(alpha=0.3)

fig.suptitle('TIMEOUT_CONVERGENCE Campaign (PR2026 Final) — 45 simulations\n'
             'Extended-run versions of originally-timed-out sims — ALL eventually FRAG',
             fontsize=12, fontweight='bold')
fig.tight_layout()
for ext in ['png','pdf']:
    fig.savefig(f'{FIG}/fig10_timeout_convergence.{ext}', dpi=150, bbox_inches='tight')
plt.close()
print("  Fig 10 done.")

# ─────────────────────────────────────────────────────────────────
# FIG 11: Grand Summary — all t_frag distributions
# ─────────────────────────────────────────────────────────────────
print("Generating Fig 11: Grand Summary...")

fig, axes = plt.subplots(2, 3, figsize=(16, 10))
axes = axes.ravel()

summary_panels = [
    ('calibration',          [r['t_frag'] for r in sims('calibration') if r['status']=='FRAG'],        '#2196F3'),
    ('regime_boundary',      [r['t_frag'] for r in sims('regime_boundary') if r['status']=='FRAG'],    '#4CAF50'),
    ('perpendicular_field',  [r['t_frag'] for r in sims('perpendicular_field') if r['status']=='FRAG'],'#FF9800'),
    ('physical_turbulence',  [r['t_frag'] for r in sims('physical_turbulence') if r['status']=='FRAG'],'#F44336'),
    ('CALIBRATION_VALIDATION', [r['t_frag'] for r in cv_recs],                                         '#3F51B5'),
    ('TIMEOUT_CONVERGENCE',  [r['t_frag'] for r in tc_recs],                                           '#8BC34A'),
]

bins_all = np.linspace(0, 2.0, 30)
for ax, (name, tfrags, color) in zip(axes, summary_panels):
    if not tfrags:
        ax.text(0.5, 0.5, 'No data', ha='center', va='center', transform=ax.transAxes)
        continue
    ax.hist(tfrags, bins=bins_all, color=color, alpha=0.8, edgecolor='k', lw=0.5)
    mean_t = statistics.mean(tfrags)
    std_t = statistics.stdev(tfrags) if len(tfrags) > 1 else 0
    ax.axvline(mean_t, color='k', lw=2, label=f'μ={mean_t:.3f}')
    ax.axvline(mean_t-std_t, color='k', lw=1, ls='--', alpha=0.5)
    ax.axvline(mean_t+std_t, color='k', lw=1, ls='--', alpha=0.5, label=f'σ={std_t:.3f}')
    ax.set_xlabel('t_frag [t_J]', fontsize=10)
    ax.set_ylabel('Count', fontsize=10)
    short = name.replace('_','\n')
    ax.set_title(f'{short}\nn={len(tfrags)}', fontsize=9.5, fontweight='bold')
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)

fig.suptitle('PR2026 MHD Campaign — t_frag Distributions Across All Sub-Campaigns\n'
             '(BRIDGE_GRID excluded: all TIMEOUT; DOMAIN_CONVERGENCE: n=6 only)',
             fontsize=13, fontweight='bold', y=1.01)
fig.tight_layout()
for ext in ['png','pdf']:
    fig.savefig(f'{FIG}/fig11_grand_summary.{ext}', dpi=150, bbox_inches='tight')
plt.close()
print("  Fig 11 done.")

# ─────────────────────────────────────────────────────────────────
# FIG 12: Outcome Matrix — all campaigns
# ─────────────────────────────────────────────────────────────────
print("Generating Fig 12: Outcome Matrix...")

fig, ax = plt.subplots(figsize=(10, 7))

row_labels = [
    'Campaign 1: Calibration',
    'Campaign 2: Regime Boundary',
    'Campaign 3: Perpendicular Field',
    'Campaign 4: Domain Size',
    'Campaign 5: Physical Turbulence',
    'Final: BRIDGE_GRID (θ=90°)',
    'Final: CALIB_VALIDATION',
    'Final: TIMEOUT_CONV',
    'Final: DOMAIN_CONV',
    'Final: SUPERCRITICAL_LONG',
]
col_labels = ['FRAG', 'TIMEOUT', 'FAILED', 'Total', 'Frag %']
data_mat = [
    [38,  0, 2,  40,  '95%'],
    [56,  0, 4,  60,  '93%'],
    [17,  0, 7,  24,  '71%'],
    [16,  0, 8,  24,  '67%'],
    [61, 11, 0,  72,  '85%'],
    [0,  48, 0,  48,  '0% (all stable)'],
    [162, 0, 0, 162, '100%'],
    [45,  0, 0,  45, '100%'],
    [6,   0, 2,   8,  '75%'],
    [74,  6, 1,  81,  '91%'],
]

ax.axis('off')
table = ax.table(
    cellText=data_mat,
    rowLabels=row_labels,
    colLabels=col_labels,
    loc='center',
    cellLoc='center',
)
table.auto_set_font_size(False)
table.set_fontsize(9.5)
table.scale(1.3, 2.0)

# Colour cells
for (row, col), cell in table.get_celld().items():
    if row == 0:  # header
        cell.set_facecolor('#1565C0')
        cell.set_text_props(color='white', fontweight='bold')
    elif col == -1:  # row labels
        cell.set_facecolor('#E3F2FD')
        cell.set_text_props(fontweight='bold', ha='right')
    else:
        val = data_mat[row-1][col]
        if col == 0:  # FRAG
            intensity = int(val) / 162 if isinstance(val, int) else 0
            cell.set_facecolor(plt.cm.Greens(0.3 + 0.5*intensity))
        elif col == 1:  # TIMEOUT
            if isinstance(val, int) and val > 0:
                cell.set_facecolor('#BBDEFB')
        elif col == 2:  # FAILED
            if isinstance(val, int) and val > 0:
                cell.set_facecolor('#FFCDD2')
        elif col == 3:  # Total
            cell.set_facecolor('#FFF9C4')

ax.set_title('PR2026 MHD Campaign — Complete Outcome Summary Table\n'
             '(All campaigns, excluding EOS Asymmetry)',
             fontsize=13, fontweight='bold', pad=20)

# Grand totals
total_all = sum(r[3] for r in data_mat)
total_frag = sum(r[0] for r in data_mat)
total_timeout = sum(r[1] for r in data_mat)
total_failed = sum(r[2] for r in data_mat)
ax.text(0.5, 0.02,
        f'GRAND TOTAL: {total_all} simulations | '
        f'FRAG: {total_frag} ({100*total_frag/total_all:.1f}%) | '
        f'TIMEOUT: {total_timeout} ({100*total_timeout/total_all:.1f}%) | '
        f'FAILED: {total_failed} ({100*total_failed/total_all:.1f}%)',
        transform=ax.transAxes, ha='center', fontsize=10.5, fontweight='bold',
        bbox=dict(boxstyle='round', facecolor='#FFFDE7', alpha=0.9))

for ext in ['png','pdf']:
    fig.savefig(f'{FIG}/fig12_outcome_matrix.{ext}', dpi=150, bbox_inches='tight')
plt.close()
print("  Fig 12 done.")

print()
print(f"All 12 figures written to {FIG}")
files = sorted(os.listdir(FIG))
for f in files:
    sz = os.path.getsize(f'{FIG}/{f}')
    print(f"  {f}  ({sz//1024} KB)")
