#!/usr/bin/env python3
"""Reproduces the 39-run ambient-confined supercritical ensemble statistics used in the
report for referee points A3, A6 and D (T1 factor / arithmetic).
Inputs: ../data/rc1_beading.json, ../data/rc2_beading.json"""
import json, numpy as np, os
base = os.path.join(os.path.dirname(__file__), "..", "data")
load = lambda f: json.load(open(os.path.join(base, f)))["runs"]
ens = load("rc1_beading.json") + load("rc2_beading.json")
print("N =", len(ens))
lams = []
for r in ens:
    be = r.get("beading_epoch") or {}
    lam = be.get("lam"); npk = be.get("npk", 0)
    if lam and npk >= 3 and lam < 3.9:
        lams.append(lam)
lams = np.array(lams)
med = np.median(lams); lwc = med / 0.3
print("beaded runs:", len(lams))
print("median lambda = %.3f lamJ ; lambda/Wcore = %.3f" % (med, lwc))
print("  x0.606 -> %.3f (equals the value printed as 2.0 in the paper)" % (lwc * 0.606))
print("  x0.65  -> %.3f (recommended, consistent with Eq. 4/5)" % (lwc * 0.65))
lw606 = np.array([l / 0.3 * 0.606 for l in lams])
lw65 = np.array([l / 0.3 * 0.65 for l in lams])
print("median-of-ratios x0.606 = %.3f (IQR %.2f-%.2f)" % (np.median(lw606), np.percentile(lw606, 25), np.percentile(lw606, 75)))
print("median-of-ratios x0.65  = %.3f (IQR %.2f-%.2f)" % (np.median(lw65), np.percentile(lw65, 25), np.percentile(lw65, 75)))
# A6 merging: is npeaks monotonic to the end (no merging)?
last = 0; decl = 0
for r in ens:
    s = r.get("series") or {}
    npk = s.get("npeaks") or []
    if not npk:
        continue
    npk = np.array([x or 0 for x in npk]); ie = int(np.argmax(npk))
    if ie >= len(npk) - 2:
        last += 1
    if ie < len(npk) - 1 and npk[-1] < npk[ie] * 0.8:
        decl += 1
print("A6: max-npeaks within last 2 snaps: %d/39 ; runs showing merging decline: %d/39" % (last, decl))
