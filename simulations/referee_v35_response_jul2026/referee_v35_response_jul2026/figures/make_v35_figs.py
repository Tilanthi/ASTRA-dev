#!/usr/bin/env python3
"""v35 campaign figures."""
import json, re
import statistics as st
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

BASE = "/data/referee_v35_campaigns_jul2026"
def load(n): return json.load(open(f"{BASE}/{n}"))['runs']
def lam(r):
    be = r.get('beading_epoch') or {}
    return be.get('lam')

rc1, rc2, rc3, rc4 = [load(f"rc{i}_beading.json") for i in (1,2,3,4)]

# ---------- Fig 1: BC reconciliation + expanded lambda ensemble ----------
fig, axes = plt.subplots(1, 2, figsize=(12.5, 5))

# Left: collapse time vs BC/suite at d=1.0 (RC1 periodic vs RC2 reflecting, + v34 refs)
ax = axes[0]
res1 = json.load(open(f"{BASE}/rc1_results.json"))
res2 = json.load(open(f"{BASE}/rc2_results.json"))
t_per = [r['collapse_t'] for r in res1 if r.get('collapse_t')]
t_ref = [r['collapse_t'] for r in res2 if r.get('collapse_t')]
ax.boxplot([t_per, t_ref], labels=[f'periodic+ambient\n(RC1, n={len(t_per)})',
                                    f'reflecting\n(RC2, n={len(t_ref)})'])
ax.axhline(0.146, color='r', ls='--', lw=1.2, label='d=0.5 user-BC artefact (0.146 $t_J$)')
ax.axhspan(0.49, 0.60, color='g', alpha=0.15, label='v34 d=1.0 range (all BCs)')
ax.set_ylabel(r'$t_{\rm coll}$ [$t_J$]')
ax.set_title('BC reconciliation at $d=1.0\\,\\lambda_J$ (referee concern #1)')
ax.legend(fontsize=8, loc='center right')

# Right: lambda/Wfil distribution expanded ensemble vs v34
ax = axes[1]
l1 = [lam(r) for r in rc1 if r.get('class')=='BEADING' and lam(r)]
l2 = [lam(r) for r in rc2 if r.get('class')=='BEADING' and lam(r)]
allc = np.array(l1 + l2) / 0.3 * 0.606
ax.hist(allc, bins=14, color='steelblue', alpha=0.8, edgecolor='k')
ax.axvspan(2.52, 3.08, color='orange', alpha=0.25, label='legacy HGBS window [2.52,3.08]')
ax.axvline(np.median(allc), color='b', lw=2, label=f'RC1+RC2 median = {np.median(allc):.2f} (n={len(allc)})')
ax.axvline(2.72, color='gray', ls=':', lw=1.5, label='v34 14-run value (2.72)')
ax.axvspan(1.4, 2.4, color='green', alpha=0.12, label=r'NN observable $1.9\pm0.5$')
ax.axvline(1.9, color='g', ls='--', lw=1.5)
ax.set_xlabel(r'$\lambda/W_{\rm fil}$')
ax.set_ylabel('N runs')
ax.set_title('Expanded supercritical ensemble (39 runs)')
ax.legend(fontsize=8)
plt.tight_layout()
plt.savefig(f"{BASE}/fig_v35_reconciliation_ensemble.png", dpi=140)
plt.close()

# ---------- Fig 2: f and beta dependence of lambda ----------
fig, axes = plt.subplots(1, 2, figsize=(12.5, 5))
byf = {}; byb = {}
for r in rc2:
    l = lam(r)
    if l:
        byf.setdefault(r['f'], []).append(l/0.3*0.606)
        byb.setdefault(r['beta'], []).append(l/0.3*0.606)
ax = axes[0]
fs = sorted(byf)
ax.errorbar(fs, [st.median(byf[f]) for f in fs],
            yerr=[st.stdev(byf[f]) if len(byf[f])>1 else 0 for f in fs],
            marker='o', ms=8, capsize=4, color='steelblue')
ax.set_xlabel('line-mass fraction $f$'); ax.set_ylabel(r'$\lambda/W_{\rm fil}$ (median)')
ax.set_title(r'$\lambda/W$ vs $f$ (RC2, reflecting $d=1.0$)')
ax.axhspan(1.4, 2.4, color='green', alpha=0.12)
ax = axes[1]
bs = sorted(byb)
ax.errorbar(bs, [st.median(byb[b]) for b in bs],
            yerr=[st.stdev(byb[b]) if len(byb[b])>1 else 0 for b in bs],
            marker='s', ms=8, capsize=4, color='firebrick')
ax.set_xlabel(r'plasma $\beta$'); ax.set_ylabel(r'$\lambda/W_{\rm fil}$ (median)')
ax.set_title(r'$\lambda/W$ vs $\beta$ (RC2)')
ax.set_xscale('log'); ax.axhspan(1.4, 2.4, color='green', alpha=0.12)
plt.tight_layout()
plt.savefig(f"{BASE}/fig_v35_lambda_f_beta.png", dpi=140)
plt.close()

# ---------- Fig 3: perpendicular-field beading map + ambipolar ----------
fig, axes = plt.subplots(1, 2, figsize=(12.5, 5))
ax = axes[0]
# RC3 grid: f x beta, marker = outcome
for r in rc3:
    c = 'limegreen' if r['class']=='BEADING' else ('red' if r['class']=='SPINDLE' else 'gray')
    m = 'o' if r['class']=='BEADING' else ('x' if r['class']=='SPINDLE' else 's')
    ax.scatter(r['f'], r['beta'], c=c, marker=m, s=150, alpha=0.6, edgecolors='k' if m=='o' else None)
ax.set_xlabel('$f$'); ax.set_ylabel(r'$\beta$'); ax.set_yscale('log')
ax.set_title(r'RC3: ideal MHD, $\theta=90°$, $d=1.0$' + '\n(green=bead, red x=spindle)')
ax = axes[1]
for r in rc4:
    c = 'limegreen' if r['class']=='BEADING' else 'red'
    m = 'o' if r['class']=='BEADING' else 'x'
    eta = float(re.search(r'eta([\d.]+)', r['pid']).group(1))
    off = 0.02 if eta==0.05 else -0.02
    ax.scatter(r['f']+off, r['beta'], c=c, marker=m,
               s=250 if eta==0.05 else 100, alpha=0.6, edgecolors='k' if m=='o' else None)
ax.set_xlabel('$f$'); ax.set_ylabel(r'$\beta$'); ax.set_yscale('log')
ax.set_title(r'RC4: ambipolar, $\theta=90°$' + '\n(small=$\\eta_{ad}$=0.01, large=0.05)')
plt.tight_layout()
plt.savefig(f"{BASE}/fig_v35_perpendicular_map.png", dpi=140)
plt.close()

print("wrote 3 figures")
