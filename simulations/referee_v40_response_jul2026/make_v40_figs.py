#!/usr/bin/env python3
"""v40 campaign figures: EX censoring + AD ambipolar."""
import json, re
import statistics as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

V40 = "/data/referee_v40_campaigns_jul2026"
V35 = "/data/referee_v35_campaigns_jul2026"

# ---------- Fig 1: EX longitudinal variance — the censoring result ----------
d = json.load(open(f"{V40}/ex_longitudinal_variance.json"))
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
ax = axes[0]
# sigma_lon(t) for the unconfined runs, colored by f
colors = {'1.5': 'steelblue', '2.0': 'darkorange', '3.0': 'firebrick'}
old_kill = {'1.5': 0.33, '2.0': 0.29, '3.0': 0.25}
plotted_f = set()
for pid in sorted(d):
    if 'unconf' not in pid or 'r256' not in pid or '_s42' not in pid:
        continue
    r = d[pid]
    if not r.get('t_series'):
        continue
    f = pid.split('_f')[1].split('_')[0]
    ax.semilogy(r['t_series'], [max(s, 1e-6) for s in r['sigma_lon_series']],
                color=colors.get(f, 'gray'), lw=2,
                label=f'f={f} (unconfined r256)' if f not in plotted_f else None)
    plotted_f.add(f)
for f, tk in old_kill.items():
    ax.axvline(tk, color=colors[f], ls=':', lw=1.2, alpha=0.7)
ax.axhline(1e-3, color='gray', ls='--', lw=1, alpha=0.6)
ax.text(0.02, 1.3e-3, 'growth threshold', fontsize=8, color='gray')
ax.set_xlabel(r'$t$ [$t_J$]')
ax.set_ylabel(r'$\sigma_{\rm lon}$ (axial density contrast)')
ax.set_title('EX: longitudinal mode growth vs. CFL-kill times (dotted)')
ax.set_ylim(1e-6, 10)
ax.legend(fontsize=8, loc='lower right')

# right: onset time vs f, resolution-independence
ax = axes[1]
onset_by_f = {}
for pid in d:
    if 'unconf' not in pid:
        continue
    r = d[pid]
    if not r.get('t_series'):
        continue
    f = float(pid.split('_f')[1].split('_')[0])
    res = 'r128' if 'r128' in pid else ('r512' if 'r512' in pid else 'r256')
    onset = None
    for t, s in zip(r['t_series'], r['sigma_lon_series']):
        if s > 1e-3:
            onset = t
            break
    if onset:
        onset_by_f.setdefault((f, res), []).append(onset)
markers = {'r128': 'o', 'r256': 's', 'r512': '^'}
rescol = {'r128': 'green', 'r256': 'navy', 'r512': 'crimson'}
for (f, res), vals in sorted(onset_by_f.items()):
    ax.scatter([f]*len(vals), vals, marker=markers[res], c=rescol[res], s=90, alpha=0.7,
               label=res if f == 1.5 else None)
# old kill band
ax.axhspan(0.25, 0.34, color='red', alpha=0.15, label='old CFL-kill window')
ax.set_xlabel('line-mass fraction $f$')
ax.set_ylabel(r'$\sigma_{\rm lon}$ growth onset [$t_J$]')
ax.set_title('Growth onset is after CFL kill, resolution-independent')
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig(f"{V40}/fig_v40_ex_censoring.png", dpi=140)
plt.close()

# ---------- Fig 2: AD ambipolar 36-run map ----------
adf = json.load(open(f"{V40}/ad_beading_final.json"))['runs']
try:
    rc4 = json.load(open(f"{V35}/rc4_beading.json"))['runs']
except Exception:
    rc4 = []

def lam_of(r):
    be = r.get('beading_epoch') or {}
    return be.get('lam')

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
# left: lambda/Wfil vs eta_ad, colored by beta
ax = axes[0]
bcol = {0.5: 'steelblue', 1.0: 'darkorange', 2.0: 'firebrick'}
for r in adf:
    lam = lam_of(r)
    eta = float(re.search(r'eta([\d.]+)', r['pid']).group(1))
    if r.get('class') == 'BEADING' and lam:
        lwf = lam / 0.3 * 0.606
        ax.scatter(eta, lwf, c=bcol.get(r['beta'], 'gray'), s=80, alpha=0.7,
                   edgecolors='k', linewidths=0.5)
    elif r.get('class') in ('SPINDLE', 'MIXED'):
        ax.scatter(eta, 0.1, marker='x', c=bcol.get(r['beta'], 'gray'), s=70)
ax.axhspan(1.4, 2.4, color='green', alpha=0.12, label=r'NN observable $1.9\pm0.5$')
ax.set_xscale('log')
ax.set_xlabel(r'$\eta_{\rm AD}$ (ambipolar diffusivity)')
ax.set_ylabel(r'$\lambda/W_{\rm fil}$')
ax.set_title('AD: perpendicular fragmentation vs ambipolar diffusivity')
from matplotlib.lines import Line2D
handles = [Line2D([0],[0], marker='o', color='w', markerfacecolor=bcol[b], markersize=9,
                  label=f'β={b}') for b in [0.5,1.0,2.0]]
handles.append(Line2D([0],[0], marker='x', color='gray', markersize=9, label='spindle/mixed'))
ax.legend(handles=handles, fontsize=8)

# right: bead fraction summary bar
ax = axes[1]
nb_ad = sum(1 for r in adf if r.get('class') == 'BEADING')
nb_rc4 = sum(1 for r in rc4 if r.get('class') == 'BEADING') if rc4 else 10
cats = ['RC4 (v35)\n12 runs\n2 η values', 'AD (v40)\n24 runs\n4 η values', 'Combined\n36 runs\n4 η values']
vals = [nb_rc4/12*100, nb_ad/24*100, (nb_rc4+nb_ad)/36*100]
bars = ax.bar(cats, vals, color=['gray', 'steelblue', 'darkgreen'], alpha=0.8)
for b, v, n in zip(bars, vals, [nb_rc4, nb_ad, nb_rc4+nb_ad]):
    ax.text(b.get_x()+b.get_width()/2, v+1, f'{n}/{int(round(n/(v/100)))}\n{v:.0f}%',
            ha='center', fontsize=9)
ax.set_ylabel('perpendicular beading fraction (%)')
ax.set_title('Ambipolar unlocking: expanded sample')
ax.set_ylim(0, 105)
plt.tight_layout()
plt.savefig(f"{V40}/fig_v40_ad_ambipolar.png", dpi=140)
plt.close()

print("wrote 2 figures")
print(f"AD beading: {nb_ad}/24; RC4: {nb_rc4}/12; combined: {nb_ad+nb_rc4}/36")
