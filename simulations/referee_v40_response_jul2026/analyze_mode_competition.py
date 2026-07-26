#!/usr/bin/env python3
"""R1/R2 radial-vs-longitudinal mode competition analyzer (referee v32 pt 1/3).

For each run, per snapshot:
  * assemble the FULL global grid (general 3-D block placement via
    LogicalLocations -- handles multi-block y/z at high resolution);
  * radial collapse:   C(t) = rho_max / rho_mean;
  * longitudinal modes: axial profile rho_bar(x) = <rho>_{y,z},
    delta = rho_bar/mean - 1, FFT -> mode power P_n(t), n = 1..12;
  * fragmentation-band power P_band = sum_{n=2..8} P_n  (lambda ~ 1-4 lambda_J);
  * axial rms delta(t) (paper's <0.02%-at-collapse metric);
  * beading: number of axial maxima in rho_bar with prominence >= 3x rms.

Summary per run: pre-runaway mode growth rate Gamma_mode (fit log P_band vs t,
t <= 0.10), radial growth rate Gamma_radial (fit log C vs t over final 40% of
snapshots), P_band at runaway, n_peaks at final snapshot.

Compare across resolutions r64/r128/r256: if Gamma_mode does not increase with
resolution AND P_band stays deep in the linear regime while C runs away, the
supercritical radial-collapse negative result is resolution-robust.

Run from campaign dir:
  python3 analyze_mode_competition.py --include 'R1_*' --odt 0.005
"""
import argparse
import glob
import json
import re
from pathlib import Path

import h5py
import numpy as np

BAND = (2, 8)          # fragmentation band: modes n=2..8 (lambda = 8/n lambda_J)
GROWTH_T_MAX = 0.10    # pre-runaway window for mode growth-rate fit


def parse(pid):
    def g(p, cast, default=None):
        m = re.search(p, pid)
        return cast(m.group(1)) if m else default
    return {'pid': pid,
            'campaign': g(r'^(R\d)', str),
            'theta': g(r'_th(\d+)', float),
            'res': g(r'_r(\d+)', int),
            'seed': g(r'_s(\d+)', int),
            'f': g(r'_f([0-9.]+)', float)}


def global_rho(fn):
    with h5py.File(fn, 'r') as h5:
        prim = np.array(h5['prim'][0])          # (nb, nz_b, ny_b, nx_b)
        loc = np.array(h5['LogicalLocations'])  # (nb, 3)
    nb, nzb, nyb, nxb = prim.shape
    nxg = loc[:, 0].max() + 1
    nyg = loc[:, 1].max() + 1
    nzg = loc[:, 2].max() + 1
    rho = np.empty((nzg * nzb, nyg * nyb, nxg * nxb), dtype=prim.dtype)
    for b in range(nb):
        xi, yi, zi = loc[b]
        rho[zi * nzb:(zi + 1) * nzb,
            yi * nyb:(yi + 1) * nyb,
            xi * nxb:(xi + 1) * nxb] = prim[b]
    return rho


def axial_stats(rho):
    C = float(rho.max() / (rho.mean() + 1e-30))
    prof = rho.mean(axis=(0, 1))                 # rho_bar(x)
    d = prof / (prof.mean() + 1e-30) - 1.0
    rms = float(d.std())
    n = len(d)
    P = np.abs(np.fft.rfft(d)) ** 2 / n
    pband = float(P[BAND[0]:BAND[1] + 1].sum())
    # beading: local maxima with prominence >= max(3*rms, 0.02)
    peaks = 0
    thr = max(3.0 * rms, 0.02)
    for i in range(2, n - 2):
        if d[i] > d[i - 1] and d[i] >= d[i + 1] and d[i] > thr:
            peaks += 1
    return C, rms, pband, peaks, P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--include', default='R1_*')
    ap.add_argument('--odt', type=float, default=0.005)
    ap.add_argument('--out', default='mode_competition.json')
    a = ap.parse_args()

    pids = sorted(set(re.sub(r'\.prim\..*$', '', Path(x).stem)
                      for x in glob.glob(f'{a.include}.prim.*.athdf')))
    print(f'{len(pids)} runs', flush=True)
    runs = []
    for pid in pids:
        rec = dict(parse(pid))
        snaps = sorted(glob.glob(f'{pid}.prim.*.athdf'),
                       key=lambda s: int(re.search(r'\.(\d+)\.athdf$', s).group(1)))
        ts, Cs, rmss, pbands, peaks_l = [], [], [], [], []
        for fn in snaps:
            ix = int(re.search(r'\.(\d+)\.athdf$', fn).group(1))
            try:
                rho = global_rho(fn)
            except Exception:
                continue
            C, rms, pband, peaks, _ = axial_stats(rho)
            ts.append(ix * a.odt); Cs.append(C); rmss.append(rms)
            pbands.append(pband); peaks_l.append(peaks)
        ts = np.array(ts); Cs = np.array(Cs); pbands = np.array(pbands)
        rec['n_snapshots'] = len(ts)
        rec['C_final'] = float(Cs[-1]) if len(Cs) else None
        rec['rms_axial_final'] = float(rmss[-1]) if rmss else None
        rec['Pband_final'] = float(pbands[-1]) if len(pbands) else None
        rec['peaks_final'] = int(peaks_l[-1]) if peaks_l else None
        rec['peaks_max'] = int(max(peaks_l)) if peaks_l else None
        # growth rates
        m = (ts > 0.01) & (ts <= GROWTH_T_MAX) & (pbands > 0)
        if m.sum() >= 4:
            gm, _ = np.polyfit(ts[m], np.log10(pbands[m]), 1)
            rec['Gamma_mode'] = float(gm)          # dex per tJ
        else:
            rec['Gamma_mode'] = None
        m2 = np.zeros_like(ts, bool)
        if len(ts) >= 6:
            m2[-max(4, len(ts) // 3):] = True
            gr, _ = np.polyfit(ts[m2], np.log10(Cs[m2]), 1)
            rec['Gamma_radial'] = float(gr)
        else:
            rec['Gamma_radial'] = None
        rec['series'] = {'t': [float(x) for x in ts],
                         'C': [float(x) for x in Cs],
                         'rms': [float(x) for x in rmss],
                         'Pband': [float(x) for x in pbands]}
        runs.append(rec)
        print(f"{pid}: C_f={rec['C_final']:.0f} rms_f={rec['rms_axial_final']:.2e} "
              f"Pb_f={rec['Pband_final']:.2e} peaks={rec['peaks_max']} "
              f"Gm={rec['Gamma_mode']} Gr={rec['Gamma_radial']}", flush=True)

    out = {'purpose': 'referee v32 pt1/3: radial-vs-longitudinal mode '
                      'competition vs transverse resolution',
           'band_modes': BAND, 'growth_window': GROWTH_T_MAX, 'runs': runs}
    Path(a.out).write_text(json.dumps(out, indent=2))
    # summary by res/theta
    print('\nsummary (means):')
    from collections import defaultdict
    agg = defaultdict(list)
    for r in runs:
        agg[(r['campaign'], r['theta'], r['res'])].append(r)
    for (cp, th, res), rs in sorted(agg.items()):
        gm = [r['Gamma_mode'] for r in rs if r['Gamma_mode']]
        rms_f = [r['rms_axial_final'] for r in rs if r['rms_axial_final']]
        pk = [r['peaks_max'] for r in rs]
        print(f'{cp} th{th} r{res}: Gamma_mode={np.mean(gm) if gm else None:.3f} '
              f'rms_final={np.mean(rms_f) if rms_f else None:.2e} '
              f'peaks_max={max(pk) if pk else None}')


if __name__ == '__main__':
    main()
