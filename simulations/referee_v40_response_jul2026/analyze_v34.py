#!/usr/bin/env python3
"""Referee-v34 arbitration campaign analyzer (Jul 2026).

Per run (AM_/EQ_/TR_ pids): radial collapse C(t)=rho_max/rho_mean, axial
profile rms, fragmentation-band mode power P_band (n=2..8), interior peak
count/positions (prominence >= max(3*rms, 0.02)), median adjacent peak
spacing lambda (code units = lambda_J).

Classification:
  BEADING : >=2 interior axial peaks develop with axial rms >= 0.05
            (non-linear) before/at the end of the run
  SPINDLE : radial runaway (C_final >= 20) with axial rms_final < 0.02
            and no multi-peak structure
  MIXED/OTHER otherwise.

Usage: python3 analyze_v34.py --include 'AM_*' --odt 0.05 --out am.json
"""
import argparse
import glob
import json
import re
from pathlib import Path

import h5py
import numpy as np


def parse(pid):
    def g(p, cast, default=None):
        m = re.search(p, pid)
        return cast(m.group(1)) if m else default
    return {'pid': pid,
            'campaign': g(r'^([A-Z0-9]+)_', str),
            'profile': g(r'^[A-Z0-9]+_([a-z]+)_', str),
            'f': g(r'_f([0-9.]+)', float),
            'beta': g(r'_b([0-9.]+)', float),
            'theta': g(r'_th(\d+)', float),
            'd': g(r'_d([0-9.]+)', float),
            'bc': g(r'_(user|refl|peri)_', str),
            'seed': g(r'_s(\d+)', int),
            'ampl': ('1.0' if pid.endswith('_aP') else
                     ('1e-4' if pid.endswith('_a4') else '1e-2'))}


def global_rho(fn):
    with h5py.File(fn, 'r') as h5:
        prim = np.array(h5['prim'][0])
        loc = np.array(h5['LogicalLocations'])
    nb, nzb, nyb, nxb = prim.shape
    rho = np.empty(((loc[:, 2].max() + 1) * nzb,
                    (loc[:, 1].max() + 1) * nyb,
                    (loc[:, 0].max() + 1) * nxb), dtype=prim.dtype)
    for b in range(nb):
        xi, yi, zi = loc[b]
        rho[zi * nzb:(zi + 1) * nzb, yi * nyb:(yi + 1) * nyb,
            xi * nxb:(xi + 1) * nxb] = prim[b]
    return rho


def axial_stats(rho, Lx=8.0):
    C = float(rho.max() / (rho.mean() + 1e-30))
    prof = rho.mean(axis=(0, 1))
    d = prof / (prof.mean() + 1e-30) - 1.0
    rms = float(d.std())
    n = len(d)
    P = np.abs(np.fft.rfft(d)) ** 2 / n
    pband = float(P[2:9].sum())
    thr = max(3.0 * rms, 0.02)
    pk_pos = []
    for i in range(2, n - 2):
        if d[i] > d[i - 1] and d[i] >= d[i + 1] and d[i] > thr:
            pk_pos.append(i * Lx / n)
    lam = None
    if len(pk_pos) >= 2:
        sp = np.diff(pk_pos)
        # periodic wrap spacing
        wrap = Lx - (pk_pos[-1] - pk_pos[0])
        sp = np.append(sp, wrap)
        lam = float(np.median(sp))
    return C, rms, pband, pk_pos, lam


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--include', default='*')
    ap.add_argument('--odt', type=float, default=0.05)
    ap.add_argument('--out', default='v34_analysis.json')
    a = ap.parse_args()

    pids = sorted(set(re.sub(r'\.prim\..*$', '', Path(x).stem)
                      for x in glob.glob(f'{a.include}.prim.*.athdf')))
    print(f'{len(pids)} runs', flush=True)
    runs = []
    for pid in pids:
        rec = dict(parse(pid))
        snaps = sorted(glob.glob(f'{pid}.prim.*.athdf'),
                       key=lambda s: int(re.search(r'\.(\d+)\.athdf$', s).group(1)))
        ts, Cs, rmss, pbands, npks, lams = [], [], [], [], [], []
        best = {'npk': 0, 't': None, 'lam': None, 'rms': None, 'pos': None}
        for fn in snaps:
            ix = int(re.search(r'\.(\d+)\.athdf$', fn).group(1))
            try:
                rho = global_rho(fn)
            except Exception:
                continue
            C, rms, pband, pk_pos, lam = axial_stats(rho)
            t = ix * a.odt
            ts.append(t); Cs.append(C); rmss.append(rms)
            pbands.append(pband); npks.append(len(pk_pos)); lams.append(lam)
            if len(pk_pos) >= best['npk'] and len(pk_pos) >= 2:
                best = {'npk': len(pk_pos), 't': t, 'lam': lam, 'rms': rms,
                        'pos': [round(p, 3) for p in pk_pos]}
        ts = np.array(ts); Cs = np.array(Cs)
        rec['n_snapshots'] = len(ts)
        rec['t_final'] = float(ts[-1]) if len(ts) else None
        rec['C_final'] = float(Cs[-1]) if len(Cs) else None
        rec['rms_final'] = float(rmss[-1]) if rmss else None
        rec['Pband_final'] = float(pbands[-1]) if pbands else None
        rec['peaks_max'] = int(max(npks)) if npks else 0
        rec['beading_epoch'] = best
        # classification
        beading = best['npk'] >= 2 and (best['rms'] or 0) >= 0.05
        spindle = (rec['C_final'] or 0) >= 20 and (rec['rms_final'] or 1) < 0.02 \
            and rec['peaks_max'] < 2
        rec['class'] = ('BEADING' if beading else
                        'SPINDLE' if spindle else 'MIXED')
        rec['lambda_med'] = best['lam']
        rec['lambda_over_Wfil'] = best['lam']          # W_fil = 1 lambda_J norm
        rec['lambda_over_Wcore'] = (best['lam'] / 0.3) if best['lam'] else None
        rec['series'] = {'t': [float(x) for x in ts],
                         'C': [round(float(x), 3) for x in Cs],
                         'rms': [round(float(x), 5) for x in rmss],
                         'Pband': [float(x) for x in pbands],
                         'npeaks': npks}
        runs.append(rec)
        print(f"{pid}: {rec['class']} C_f={rec['C_final']:.1f} "
              f"rms_f={rec['rms_final']:.2e} peaks_max={rec['peaks_max']} "
              f"lam={rec['lambda_med']} t_f={rec['t_final']}", flush=True)

    Path(a.out).write_text(json.dumps(
        {'purpose': 'referee v34 BC-arbitration analysis', 'runs': runs},
        indent=2))
    print('wrote', a.out)


if __name__ == '__main__':
    main()
