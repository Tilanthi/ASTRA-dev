#!/usr/bin/env python3
"""Figures for the v34 referee-response report."""
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

am = json.load(open('am_analysis.json'))['runs']
eq = json.load(open('eq_analysis.json'))['runs']
runs = {r['pid']: r for r in am + eq}

# ── Fig 1: mode-competition growth curves for the arbitration matrix ─────────
fig, axes = plt.subplots(1, 3, figsize=(15, 4.2), sharey=False)
picks = [
    ('AM_gaus_f2.0_b1.0_th0_d0.5_user_s42', 'd=0.5 user (paper config)', 'C0', '-'),
    ('AM_gaus_f2.0_b1.0_th0_d0.5_refl_s42', 'd=0.5 reflecting', 'C1', '-'),
    ('AM_gaus_f2.0_b1.0_th0_d1.0_user_s42', 'd=1.0 user', 'C0', '--'),
    ('AM_gaus_f2.0_b1.0_th0_d1.0_refl_s42', 'd=1.0 reflecting', 'C1', '--'),
    ('AM_gaus_f2.0_b1.0_th0_d1.0_peri_s42', 'd=1.0 periodic', 'C2', '--'),
]
ax = axes[0]
for pid, lab, c, ls in picks:
    r = runs[pid]; s = r['series']
    ax.semilogy(s['t'], s['C'], ls, color=c, label=lab, lw=1.6)
ax.set_xlabel(r'$t\ [t_J]$'); ax.set_ylabel(r'density contrast $C=\rho_{max}/\bar\rho$')
ax.legend(fontsize=7, loc='lower right'); ax.set_title('(a) radial collapse', fontsize=10)

ax = axes[1]
for pid, lab, c, ls in picks:
    r = runs[pid]; s = r['series']
    ax.semilogy(s['t'], np.array(s['Pband']) + 1e-16, ls, color=c, lw=1.6)
ax.set_xlabel(r'$t\ [t_J]$'); ax.set_ylabel(r'fragmentation-band power $P_{band}$')
ax.set_title('(b) longitudinal mode growth (n=2-8)', fontsize=10)

ax = axes[2]
for pid, lab, c, ls in picks:
    r = runs[pid]; s = r['series']
    ax.plot(s['t'], s['npeaks'], ls, color=c, lw=1.6, marker='.', ms=4)
ax.set_xlabel(r'$t\ [t_J]$'); ax.set_ylabel('interior axial peaks')
ax.set_title('(c) beading', fontsize=10)
for a in axes: a.grid(alpha=0.3)
fig.suptitle('Boundary-condition arbitration, single binary, f=2.0, beta=1, theta=0, identical ICs',
             fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.95])
fig.savefig('fig_v34_arbitration.png', dpi=160)
print('fig_v34_arbitration.png')

# ── Fig 2: bead-spacing ensemble ─────────────────────────────────────────────
fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
ax = axes[0]
lams, labs, cols = [], [], []
for r in am + eq:
    if r['d'] == 1.0 and r['theta'] == 0.0 and r['lambda_med'] and r['peaks_max'] >= 3:
        lams.append(r['lambda_med'] / 0.3)       # lambda/W_core
        cols.append('C0' if r['profile'] == 'gaussian' else 'C3')
ax.hist(lams, bins=np.arange(2.5, 11, 0.5), color='C0', alpha=0.75, edgecolor='k')
ax.axvline(2.52/0.606, color='g', ls='--', label='HGBS window (T1-corrected)')
ax.axvline(3.08/0.606, color='g', ls='--')
ax.axvline(1.9/0.606, color='r', ls=':', label='observed NN 1.9 (T1 units)')
ax.set_xlabel(r'$\lambda/W_{core}$'); ax.set_ylabel('N runs')
ax.set_title('(a) supercritical bead spacing, d=1.0 embedded', fontsize=10)
ax.legend(fontsize=8); ax.grid(alpha=0.3)

ax = axes[1]
# collapse-time vs boundary distance
data = {}
for r in am + eq:
    if r['theta'] == 90 or r['class'] == 'MIXED' and r['d'] != 0.5: continue
    key = (r['d'], r['bc'])
    data.setdefault(key, []).append(r['t_final'])
markers = {'user': 'o', 'refl': 's', 'peri': '^'}
labels = {'user': 'user (zero-gradient outflow)', 'refl': 'reflecting', 'peri': 'periodic'}
for bc in ('user', 'refl', 'peri'):
    xs = sorted(d for (d, b) in data if b == bc)
    ys = [np.mean([t for (d, b), ts in data.items() if b == bc and d == x for t in ts]) for x in xs]
    ax.plot(xs, ys, markers[bc] + '-', label=labels[bc], ms=7)
ax.set_xlabel(r'transverse boundary distance $d\ [\lambda_J]$')
ax.set_ylabel(r'collapse/runaway time $[t_J]$')
ax.set_title('(b) collapse time vs boundary distance', fontsize=10)
ax.legend(fontsize=8); ax.grid(alpha=0.3)
fig.tight_layout()
fig.savefig('fig_v34_lambda_distance.png', dpi=160)
print('fig_v34_lambda_distance.png')
