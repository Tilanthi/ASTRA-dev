#!/usr/bin/env python3
"""T1 forward model v3 -- definitive synthetic-HGBS pipeline (referee #5).

Fixes over v2:
  * Assembles the FULL global grid from per-meshblock athdf arrays
    (v2 silently used only meshblock 0 -- a single x-cut).
  * Spine-averaged transverse profile over the whole filament length.
  * Plummer fits are done on a restricted window (|y| <= fit_window) with
    the background estimated from the edges AND with a free offset, to
    control the background/offset degeneracy that pegged p at bounds.
  * Reports W_form (Gaussian FWHM of the raw profile) and, for the
    beam-convolved map: W_gauss, W_plum(p free 1-4), W_plum(p=2 fixed).
  * eta_W(gauss) = W_form / W_gauss_beam  (paper's Gaussian definition,
    with W_fil normalised to the beam-convolved Gaussian width)
    eta_W(plum)  = W_form / W_plum_beam   (forward-modelled Plummer)

Usage:
  python3 t1_forward_model_v3.py --include 'B_*' --odt 0.005 --out t1_v3.json
"""
import argparse
import glob
import json
import re
from pathlib import Path

import h5py
import numpy as np
from scipy.optimize import curve_fit
from scipy.signal import fftconvolve

BEAM_FWHMS_LAMDAJ = [0.04, 0.08, 0.12]
EPOCH_IDX = [4, 10, 20]          # t = 0.02, 0.05, 0.10 at odt=0.005
FIT_WINDOW = 0.35                # |y| window for fits (~2 x filament FWHM)


def parse(pid):
    def g(p, cast, default=None):
        m = re.search(p, pid)
        return cast(m.group(1)) if m else default
    return {'pid': pid,
            'f': g(r'_f([0-9.]+)', float),
            'beta': g(r'_b([0-9.]+)', float),
            'seed': g(r'_s([0-9.]+)', int)}


def load_global_rho(fn):
    """Assemble global (nz, ny, nx) density from per-meshblock athdf."""
    with h5py.File(fn, 'r') as h5:
        prim = np.array(h5['prim'][0])          # (nb, nz, ny, nxb)
        loc = np.array(h5['LogicalLocations'])  # (nb, 3)
        ny = prim.shape[2]
    order = np.argsort(loc[:, 0])               # order blocks along x
    rho = np.concatenate([prim[i] for i in order], axis=2)  # (nz, ny, nx)
    return rho, ny


def profile_from_map(Nmap, ny):
    """N(y): spine-averaged transverse profile from a (ny, nx) column map."""
    Ny = Nmap.mean(axis=1)
    dx = 1.0 / ny
    y = (np.arange(ny) + 0.5 - ny / 2) * dx
    # recentre on smoothed peak
    k = np.exp(-0.5 * (np.arange(-3, 4) / 1.5) ** 2)
    k /= k.sum()
    y0 = (np.arange(ny))[int(np.argmax(np.convolve(Ny, k, mode='same')))]
    return y - (y0 + 0.5 - ny / 2) * dx, Ny


def gauss(r, A, s, off):
    return A * np.exp(-r ** 2 / (2 * s ** 2)) + off


def plum_free(r, Nc, R, p, off):
    return Nc / (1 + (r / R) ** 2) ** (p / 2.0) + off


def plum_p2(r, Nc, R, off):
    return Nc / (1 + (r / R) ** 2) + off


def fwhm_g(s):
    return 2.354820045 * abs(s)


def fwhm_p(R, p):
    return 2.0 * R * np.sqrt(2.0 ** (2.0 / p) - 1.0)


def fit_all(y, N, ny):
    """Fit on |y|<=FIT_WINDOW with free offset; also background-subtracted."""
    dx = 1.0 / ny
    bg = float(np.median(N[np.abs(y) > 0.35]))
    m = np.abs(y) <= FIT_WINDOW
    yw, Nw = y[m], N[m]
    out = {'background': bg}
    # --- Gaussian (window, free offset)
    try:
        p0 = [Nw.max() - Nw.min(), 0.15, float(Nw.min())]
        popt, _ = curve_fit(gauss, yw, Nw, p0=p0,
                            bounds=([0, 1e-3, 0], [np.inf, 1.0, np.inf]),
                            maxfev=20000)
        out['W_gauss'] = fwhm_g(popt[1])
    except Exception:
        out['W_gauss'] = None
    # --- Plummer free p in [1,4] (window, free offset)
    try:
        p0 = [Nw.max() - Nw.min(), 0.15, 2.0, float(Nw.min())]
        popt, _ = curve_fit(plum_free, yw, Nw, p0=p0,
                            bounds=([0, 1e-3, 1.0, 0],
                                    [np.inf, 1.0, 4.0, np.inf]),
                            maxfev=20000)
        out['W_plum'] = fwhm_p(popt[1], popt[2])
        out['p_plum'] = popt[2]
        out['p_pegged'] = bool(popt[2] > 3.9 or popt[2] < 1.1)
    except Exception:
        out['W_plum'] = out['p_plum'] = out['p_pegged'] = None
    # --- Plummer p=2 (window, background subtracted, no offset)
    try:
        Nsub = np.maximum(Nw - bg, 0.0)
        p0 = [Nsub.max(), 0.15]
        popt, _ = curve_fit(lambda r, Nc, R: plum_p2(r, Nc, R, 0.0),
                            yw, Nsub, p0=p0,
                            bounds=([0, 1e-3], [np.inf, 1.0]), maxfev=20000)
        out['W_plum_p2'] = fwhm_p(popt[1], 2.0)
    except Exception:
        out['W_plum_p2'] = None
    return out


def convolve_2d(Nmap, beam_fwhm, ny):
    dx = 1.0 / ny
    sp = (beam_fwhm / 2.354820045) / dx
    half = int(np.ceil(4 * sp))
    ax = np.arange(-half, half + 1)
    g1 = np.exp(-ax ** 2 / (2 * sp ** 2))
    K = np.outer(g1, g1)
    K /= K.sum()
    return fftconvolve(Nmap, K, mode='same')


def measure_snapshot(fn):
    rho, ny = load_global_rho(fn)
    Nmap = rho.sum(axis=0)                    # (ny, nx)
    y, Nraw = profile_from_map(Nmap, ny)
    raw = fit_all(y, Nraw, ny)
    rec = {'raw': raw}
    for fwhm in BEAM_FWHMS_LAMDAJ:
        Nc = convolve_2d(Nmap, fwhm, ny)
        y2, Np = profile_from_map(Nc, ny)
        fits = fit_all(y2, Np, ny)
        Wf = raw.get('W_gauss')
        fits['eta_gauss'] = (Wf / fits['W_gauss']
                             if Wf and fits.get('W_gauss') else None)
        fits['eta_plum'] = (Wf / fits['W_plum']
                            if Wf and fits.get('W_plum') else None)
        fits['eta_plum_p2'] = (Wf / fits['W_plum_p2']
                               if Wf and fits.get('W_plum_p2') else None)
        fits['ratio_GP'] = (fits['W_gauss'] / fits['W_plum']
                            if fits.get('W_gauss') and fits.get('W_plum')
                            else None)
        rec[f'beam_{fwhm:.2f}'] = fits
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--include', action='append', required=True)
    ap.add_argument('--odt', type=float, default=0.005)
    ap.add_argument('--out', default='t1_forward_model_v3.json')
    a = ap.parse_args()

    pids = set()
    for pat in a.include:
        for x in glob.glob(f'{pat}.prim.*.athdf'):
            pids.add(re.sub(r'\.prim\..*$', '', Path(x).stem))
    pids = sorted(pids)
    print(f'{len(pids)} runs', flush=True)

    out = {'method': 'v3: full-grid assembly, spine-averaged profile, '
                     'windowed fits (|y|<=0.35), bg-controlled Plummer',
           'beams': BEAM_FWHMS_LAMDAJ, 'runs': []}
    for pid in pids:
        snaps = sorted(glob.glob(f'{pid}.prim.*.athdf'),
                       key=lambda s: int(re.search(r'\.(\d+)\.athdf$', s).group(1)))
        if not snaps:
            continue
        idxs = [int(re.search(r'\.(\d+)\.athdf$', s).group(1)) for s in snaps]
        chosen = {}
        for want in EPOCH_IDX + [max(idxs)]:
            j = min(range(len(idxs)), key=lambda i: abs(idxs[i] - want))
            chosen[idxs[j]] = snaps[j]
        rec = dict(parse(pid))
        rec['epochs'] = {}
        for ix in sorted(chosen):
            try:
                m = measure_snapshot(chosen[ix])
            except Exception as e:
                print(f'  {pid} idx{ix}: {e}', flush=True)
                continue
            rec['epochs'][f't={ix * a.odt:.3f}'] = m
        out['runs'].append(rec)
        e0 = rec['epochs'].get(f't={min(chosen) * a.odt:.3f}', {})
        b = e0.get('beam_0.08', {})
        print(f"{pid}: W_form={e0.get('raw', {}).get('W_gauss')} "
              f"eta_plum={b.get('eta_plum')} eta_plum_p2={b.get('eta_plum_p2')}",
              flush=True)

    # aggregate at each epoch
    agg = {}
    for r in out['runs']:
        for ep, m in r['epochs'].items():
            b = m.get('beam_0.08', {})
            for key in ('eta_gauss', 'eta_plum', 'eta_plum_p2', 'ratio_GP'):
                v = b.get(key)
                if v:
                    agg.setdefault(ep, {}).setdefault(key, []).append(v)
            w = m.get('raw', {}).get('W_gauss')
            if w:
                agg.setdefault(ep, {}).setdefault('W_form', []).append(w)
    out['aggregates'] = {ep: {k: [float(np.mean(v)), float(np.std(v)), len(v)]
                              for k, v in d.items()}
                         for ep, d in sorted(agg.items())}
    Path(a.out).write_text(json.dumps(out, indent=2))
    print('\n=== v3 aggregates (mid beam 0.08) ===')
    for ep, d in sorted(agg.items()):
        line = ' '.join(f'{k}={np.mean(v):.3f}+-{np.std(v):.3f}'
                        for k, v in d.items())
        print(f'{ep}: {line}')


if __name__ == '__main__':
    main()
