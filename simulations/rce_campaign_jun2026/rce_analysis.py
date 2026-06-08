"""
RCE Campaign Analysis Script
Radial Confinement Escalation Campaign
288-sim Athena++ MHD campaign — June 2026
Author: ASTRA-PA for Glenn J. White (Open University)
"""

import re
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from pathlib import Path
from collections import defaultdict

# ── Parse log ────────────────────────────────────────────────────────────────
LOG = Path("/workspace/rce_stdout.log")
OUTDIR = Path("/workspace/rce_analysis")
OUTDIR.mkdir(exist_ok=True)

pat = re.compile(
    r'\[\s*(\d+)/288\]\s+(\S+)\s+'
    r'morph=(\S+)\s+lW=\s*(\S+)\s+npk=\s*(\d+)\s+wall=\s*(\d+)s\s+'
    r'P=([\d.]+)\s+(\S+)'
)

records = []
for line in LOG.read_text().splitlines():
    m = pat.search(line)
    if not m:
        continue
    idx, sid, morph, lw_raw, npk, wall, p_ext, event = m.groups()
    # parse sim_id components
    parts = sid.replace('RCE_', '').split('_')
    f_val  = float(parts[0].replace('f',''))
    b_val  = float(parts[1].replace('b',''))
    mach   = float(parts[2].replace('m',''))
    p_val  = float(parts[3].replace('p',''))
    seed   = int(parts[4].replace('s',''))
    lw     = None if lw_raw == 'None' else float(lw_raw)
    # parse collapse time
    t_event = None
    em = re.search(r'@t=([\d.]+)', event)
    if em:
        t_event = float(em.group(1))
    records.append(dict(
        idx=int(idx), sim_id=sid, morph=morph,
        f=f_val, beta=b_val, mach=mach, p_ext=p_val, seed=seed,
        lw=lw, npk=int(npk), wall=int(wall),
        event=event.split('@')[0], t_event=t_event
    ))

df = pd.DataFrame(records)
print(f"Parsed {len(df)} simulations")
print(df['event'].value_counts())
print(f"\nLambda/W measurements: {(~df['lw'].isna()).sum()}")
print(f"Unique lW values: {df['lw'].dropna().unique()}")

# ── Mark seed-3 artefact ──────────────────────────────────────────────────────
# All lW=11.4062 come exclusively from seed=3 across all beta/P_ext — confirmed artefact
df['lw_genuine'] = df['lw'].copy()
df.loc[df['seed'] == 3, 'lw_genuine'] = np.nan   # treat as noise floor

# ── Derived columns ──────────────────────────────────────────────────────────
df['collapsed']  = df['event'].isin(['GRAV_FRAG', 'DT_COLLAPSE'])
df['timed_out']  = df['event'] == 'TIMEOUT'

# ============================================================
# FIGURE 1: Outcome matrix — f vs β, all P_ext combined
# ============================================================
fig1, ax = plt.subplots(figsize=(8, 5))

f_vals    = sorted(df['f'].unique())
beta_vals = sorted(df['beta'].unique())

# fraction collapsed per (f, β)
for bi, bv in enumerate(beta_vals):
    collapse_frac = []
    for fv in f_vals:
        sub = df[(df['f']==fv) & (df['beta']==bv)]
        if len(sub) == 0:
            collapse_frac.append(np.nan)
        else:
            collapse_frac.append(sub['collapsed'].mean())
    ax.plot(f_vals, collapse_frac, 'o-', lw=2,
            label=f'β={bv}', ms=9)

ax.axhline(0.5, ls='--', color='gray', alpha=0.5, label='50% threshold')
ax.set_xlabel('Line-mass ratio  f = M/M_crit', fontsize=12)
ax.set_ylabel('Fraction collapsed', fontsize=12)
ax.set_title('Collapse fraction vs f and β\n(all P_ext, all Mach, all seeds combined)', fontsize=12)
ax.legend(fontsize=11)
ax.set_ylim(-0.05, 1.05)
ax.set_xticks(f_vals)
ax.grid(True, alpha=0.3)
fig1.tight_layout()
fig1.savefig(OUTDIR / 'RCE_F01_collapse_fraction.png', dpi=150)
plt.close(fig1)
print("Fig 1 done")

# ============================================================
# FIGURE 2: P_ext effect — collapse fraction vs P_ext for each (f, β)
# ============================================================
fig2, axes = plt.subplots(1, 3, figsize=(14, 4.5), sharey=True)
p_vals = sorted(df['p_ext'].unique())
colors = ['C0','C1','C2','C3']

for bi, (bv, ax) in enumerate(zip(beta_vals, axes)):
    for fi, fv in enumerate(f_vals):
        fracs = []
        for pv in p_vals:
            sub = df[(df['f']==fv) & (df['beta']==bv) & (df['p_ext']==pv)]
            fracs.append(sub['collapsed'].mean() if len(sub) > 0 else np.nan)
        ax.plot(p_vals, fracs, 'o-', lw=2, label=f'f={fv}', ms=7)
    ax.set_title(f'β = {bv}', fontsize=12)
    ax.set_xlabel('External pressure  P_ext / ρcs²', fontsize=11)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xticks(p_vals)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)
    if bi == 0:
        ax.set_ylabel('Fraction collapsed', fontsize=11)

fig2.suptitle('P_ext has no effect on collapse fraction — all curves flat', fontsize=12, y=1.01)
fig2.tight_layout()
fig2.savefig(OUTDIR / 'RCE_F02_pext_vs_collapse.png', dpi=150, bbox_inches='tight')
plt.close(fig2)
print("Fig 2 done")

# ============================================================
# FIGURE 3: Collapse time vs P_ext for collapsing sims
# ============================================================
fig3, axes = plt.subplots(1, 2, figsize=(12, 4.5))

coll = df[df['collapsed'] & df['t_event'].notna()]
for ax, fv in zip(axes, [1.4, 1.5]):
    sub = coll[coll['f']==fv]
    for bv in [0.5, 1.0]:
        ssub = sub[sub['beta']==bv]
        if len(ssub) == 0:
            continue
        # mean collapse time per P_ext
        grp = ssub.groupby('p_ext')['t_event'].agg(['mean','std']).reset_index()
        ax.errorbar(grp['p_ext'], grp['mean'], yerr=grp['std'].fillna(0),
                    fmt='o-', lw=2, capsize=4, label=f'β={bv}')
    ax.set_xlabel('P_ext / ρcs²', fontsize=11)
    ax.set_ylabel('Collapse time  t_collapse  (t_J)', fontsize=11)
    ax.set_title(f'f = {fv}', fontsize=12)
    ax.set_xticks(sorted(df['p_ext'].unique()))
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

fig3.suptitle('Collapse time is independent of P_ext', fontsize=12)
fig3.tight_layout()
fig3.savefig(OUTDIR / 'RCE_F03_collapse_time_vs_pext.png', dpi=150, bbox_inches='tight')
plt.close(fig3)
print("Fig 3 done")

# ============================================================
# FIGURE 4: Wall-time histograms by β (fast collapse vs TIMEOUT)
# ============================================================
fig4, axes = plt.subplots(1, 3, figsize=(13, 4))

for ax, bv in zip(axes, beta_vals):
    sub = df[df['beta']==bv]
    coll_wall = sub[sub['collapsed']]['wall'].values
    tout_wall = sub[sub['timed_out']]['wall'].values
    bins = np.linspace(0, 8000, 40)
    if len(coll_wall):
        ax.hist(coll_wall, bins=bins, alpha=0.6, label='Collapse', color='C3')
    if len(tout_wall):
        ax.hist(tout_wall, bins=bins, alpha=0.6, label='Timeout', color='C0')
    ax.set_title(f'β = {bv}', fontsize=12)
    ax.set_xlabel('Wall time (s)', fontsize=10)
    ax.set_ylabel('Count', fontsize=10)
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

fig4.suptitle('Wall-time distributions by β value', fontsize=12)
fig4.tight_layout()
fig4.savefig(OUTDIR / 'RCE_F04_walltime_histograms.png', dpi=150)
plt.close(fig4)
print("Fig 4 done")

# ============================================================
# FIGURE 5: Grand summary — outcome map over full (f, β, P_ext) grid
# ============================================================
fig5, axes = plt.subplots(1, 4, figsize=(16, 4), sharey=True)
outcome_cmap = {'GRAV_FRAG':'#d73027','DT_COLLAPSE':'#f46d43',
                'TIMEOUT':'#4575b4','STABLE':'#74add1'}

for ax, pv in zip(axes, sorted(df['p_ext'].unique())):
    sub = df[df['p_ext']==pv]
    # build matrix: rows=beta, cols=f, value=collapse fraction
    mat = np.zeros((len(beta_vals), len(f_vals)))
    for bi, bv in enumerate(beta_vals):
        for fi, fv in enumerate(f_vals):
            cell = sub[(sub['beta']==bv) & (sub['f']==fv)]
            if len(cell) == 0:
                mat[bi, fi] = np.nan
            else:
                mat[bi, fi] = cell['collapsed'].mean()
    im = ax.imshow(mat, vmin=0, vmax=1, cmap='RdYlBu_r',
                   aspect='auto', origin='lower')
    ax.set_xticks(range(len(f_vals)))
    ax.set_xticklabels([f'{v}' for v in f_vals], fontsize=9)
    ax.set_yticks(range(len(beta_vals)))
    ax.set_yticklabels([f'{v}' for v in beta_vals], fontsize=9)
    ax.set_xlabel('f', fontsize=10)
    ax.set_title(f'P_ext = {pv}', fontsize=11)
    if pv == sorted(df['p_ext'].unique())[0]:
        ax.set_ylabel('β', fontsize=10)
    # annotate cells
    for bi in range(len(beta_vals)):
        for fi in range(len(f_vals)):
            v = mat[bi, fi]
            if not np.isnan(v):
                ax.text(fi, bi, f'{v:.0%}', ha='center', va='center',
                        fontsize=9, color='white' if v > 0.5 else 'black', fontweight='bold')

fig5.colorbar(im, ax=axes[-1], label='Collapse fraction', shrink=0.8)
fig5.suptitle('Collapse fraction across full parameter space — identical across all P_ext panels',
              fontsize=11, y=1.02)
fig5.tight_layout()
fig5.savefig(OUTDIR / 'RCE_F05_outcome_map.png', dpi=150, bbox_inches='tight')
plt.close(fig5)
print("Fig 5 done")

# ============================================================
# FIGURE 6: Mach effect on collapse time
# ============================================================
fig6, axes = plt.subplots(1, 2, figsize=(11, 4.5))
mach_vals = sorted(df['mach'].unique())

for ax, fv in zip(axes, [1.4, 1.5]):
    coll_f = df[(df['f']==fv) & df['collapsed'] & df['t_event'].notna()]
    for bv in [0.5, 1.0]:
        for mv, marker in zip(mach_vals, ['o', 's']):
            sub = coll_f[(coll_f['beta']==bv) & (coll_f['mach']==mv)]
            if len(sub) == 0:
                continue
            grp = sub.groupby('p_ext')['t_event'].mean()
            ax.plot(grp.index, grp.values, marker=marker, linestyle='-', lw=1.5,
                    label=f'β={bv} M={mv}', ms=7, alpha=0.8)
    ax.set_title(f'f = {fv}: Mach number effect', fontsize=11)
    ax.set_xlabel('P_ext / ρcs²', fontsize=10)
    ax.set_ylabel('Mean t_collapse (t_J)', fontsize=10)
    ax.legend(fontsize=8, ncol=2)
    ax.set_xticks(sorted(df['p_ext'].unique()))
    ax.grid(True, alpha=0.3)

fig6.suptitle('M=3 collapses earlier than M=2 — P_ext has no effect at either Mach', fontsize=11)
fig6.tight_layout()
fig6.savefig(OUTDIR / 'RCE_F06_mach_effect.png', dpi=150)
plt.close(fig6)
print("Fig 6 done")

# ============================================================
# FIGURE 7: Key comparison — P_ext=0 vs P_ext=0.5, all parameters
# ============================================================
fig7, ax = plt.subplots(figsize=(8, 5))

df_p0  = df[df['p_ext']==0.0]
df_p05 = df[df['p_ext']==0.5]
labels = []
x0, x5, positions = [], [], []
pos = 0
for fv in f_vals:
    for bv in beta_vals:
        sub0  = df_p0[(df_p0['f']==fv)  & (df_p0['beta']==bv)]
        sub05 = df_p05[(df_p05['f']==fv) & (df_p05['beta']==bv)]
        if len(sub0) == 0 or len(sub05) == 0:
            pos += 1
            continue
        x0.append(sub0['collapsed'].mean())
        x5.append(sub05['collapsed'].mean())
        positions.append(pos)
        labels.append(f'f={fv}\nβ={bv}')
        pos += 1

x0  = np.array(x0)
x5  = np.array(x5)
positions = np.array(positions)

ax.bar(positions - 0.2, x0,  0.35, label='P_ext=0.0', color='C0', alpha=0.8)
ax.bar(positions + 0.2, x5,  0.35, label='P_ext=0.5', color='C3', alpha=0.8)
ax.set_xticks(positions)
ax.set_xticklabels(labels, fontsize=8)
ax.set_ylabel('Collapse fraction (mean over seeds × Mach)', fontsize=10)
ax.set_title('P_ext = 0.0 vs P_ext = 0.5: no change in any parameter cell', fontsize=11)
ax.legend(fontsize=10)
ax.set_ylim(0, 1.15)
ax.axhline(1.0, ls='--', color='gray', alpha=0.4)
ax.grid(True, alpha=0.3, axis='y')
fig7.tight_layout()
fig7.savefig(OUTDIR / 'RCE_F07_p0_vs_p05_comparison.png', dpi=150)
plt.close(fig7)
print("Fig 7 done")

# ============================================================
# STATISTICS TABLE
# ============================================================
print("\n\n=== STATISTICAL SUMMARY ===")
print(f"Total sims completed: {len(df)}")
print(f"Total collapsed: {df['collapsed'].sum()} ({df['collapsed'].mean()*100:.1f}%)")
print(f"Total timed out: {df['timed_out'].sum()} ({df['timed_out'].mean()*100:.1f}%)")
print(f"\nCollapses per P_ext:")
print(df.groupby('p_ext')['collapsed'].agg(['sum','mean']))
print(f"\nTimeouts per P_ext:")
print(df.groupby('p_ext')['timed_out'].agg(['sum','mean']))
print(f"\nCollapse fraction by (f, beta):")
pivot = df.pivot_table(index='beta', columns='f', values='collapsed', aggfunc='mean')
print(pivot.round(3))
print(f"\nMean collapse time by (f, beta, mach) [collapsed sims only]:")
coll_only = df[df['collapsed'] & df['t_event'].notna()]
print(coll_only.groupby(['f','beta','mach'])['t_event'].agg(['mean','std','count']))

# Save CSV
df.to_csv(OUTDIR / 'rce_all_263_results.csv', index=False)
print(f"\nData saved to {OUTDIR / 'rce_all_263_results.csv'}")
print("Analysis complete.")
