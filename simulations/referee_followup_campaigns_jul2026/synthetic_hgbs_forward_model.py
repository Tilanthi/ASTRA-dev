#!/usr/bin/env python3
"""Campaign B -- synthetic-HGBS T1 forward model (referee #5).

For each filament simulation this builds a synthetic column-density map, folds
in the HGBS beam, and fits the radial profile with the SAME Plummer methodology
used on real HGBS data -- yielding W_fil (Plummer FWHM) directly, rather than
inferring the T1 normalisation through a Gaussian-convolution proxy.

Pipeline per run:
  1. select a pre-collapse (relaxed) snapshot;
  2. column density N(x,y) = integral of rho along the line of sight;
  3. radial profile N(r) about the filament spine (averaged along the spine);
  4. W_form  = Gaussian FWHM of the RAW profile (intrinsic formation width);
  5. convolve N(r) with a Gaussian beam (HGBS 18" mapped to lambda_J units);
  6. W_gauss = Gaussian FWHM of the beam-convolved profile;
     W_plum  = Plummer-2 FWHM of the beam-convolved profile
               (N(r)=N_c/[1+(r/R_flat)^2]^(p/2); FWHM = 2 R_flat sqrt(2^(2/p)-1));
  7. T1 = W_form / W_plum ;   ratio_GP = W_gauss / W_plum .

Run from the directory containing the .athdf outputs:
  python3 synthetic_hgbs_forward_model.py
"""
import glob
import json
import re
from pathlib import Path

import h5py
import numpy as np
from scipy.optimize import curve_fit

# HGBS 18" beam at 250 um mapped to code units (lambda_J = 1).
# With W_core = 0.3 lambda_J ~ 0.1 pc, lambda_J ~ 0.33 pc, so the 18" beam is
# ~0.012 pc (140 pc) to ~0.035 pc (400 pc) = 0.036-0.105 lambda_J FWHM.
BEAM_FWHMS_LAMDAJ = [0.04, 0.08, 0.12]
T1_PAPER = 0.606
T1_PLUMMER_PAPER = 0.71


def parse(pid):
    def g(p, cast, default=None):
        m = re.search(p, pid)
        return cast(m.group(1)) if m else default
    return {'pid': pid,
            'f': g(r'_f([0-9.]+)', float),
            'beta': g(r'_b([0-9.]+)', float),
            'seed': g(r'_s([0-9.]+)', int)}


def get_density(h5):
    """Return the 3D density array from an Athena++ prim .athdf file."""
    cands = []

    def rec(g, path=''):
        for k, v in g.items():
            p = path + '/' + k
            if isinstance(v, h5py.Dataset):
                cands.append((p, v))
            elif isinstance(v, h5py.Group):
                rec(v, p)
    rec(h5)
    # prefer a name suggesting density
    for name in ('rho', 'dens'):
        for p, d in cands:
            if name in p.lower() and len(d.shape) >= 3:
                a = np.array(d).squeeze()
                while a.ndim > 3:
                    a = a[0]
                if a.ndim == 3:
                    return a
    # else first 3D dataset (Athena++ writes density first in prim)
    for p, d in cands:
        if len(d.shape) >= 3:
            a = np.array(d).squeeze()
            while a.ndim > 3:
                a = a[0]
            if a.ndim == 3:
                return a
    return None


def column_density(rho):
    """N(x,y) = line-of-sight integral of rho (LOS = the smallest axis)."""
    axis = int(np.argmin(rho.shape))   # thin transverse direction as LOS
    return rho.sum(axis=axis)


def radial_profile(Nmap):
    """Azimuthally-averaged radial profile about the column-density peak.

    Returns (r_bins, N_profile) in code (lambda_J) units. The grid spacing is
    uniform with x2,x3 in [-0.5,0.5] and nx2=nx3=64 -> dx = 1/64.
    """
    ny, nx = Nmap.shape if Nmap.shape[0] <= Nmap.shape[1] else (Nmap.shape[1], Nmap.shape[0])
    Nmap2 = Nmap if Nmap.shape[0] <= Nmap.shape[1] else Nmap.T
    ny, nx = Nmap2.shape
    # spine = peak column in each longitudinal cut, then we profile about the
    # global centroid for a clean radial average
    iy, ix = np.unravel_index(np.argmax(Nmap2), Nmap2.shape)
    dx = 1.0 / nx   # x in [-0.5,0.5] over nx cells -> but use actual spacing
    # use physical spacing from the [-0.5,0.5] domain
    ys = (np.arange(ny) + 0.5) / ny - 0.5
    xs = (np.arange(nx) + 0.5) / nx - 0.5
    yy, xx = np.meshgrid(ys, xs, indexing='ij')
    r = np.sqrt((xx - xs[ix]) ** 2 + (yy - ys[iy]) ** 2).ravel()
    Nv = Nmap2.ravel()
    rmax = r.max()
    nb = min(50, max(10, nx // 2))
    edges = np.linspace(0, rmax, nb + 1)
    idx = np.digitize(r, edges) - 1
    prof = np.array([Nv[idx == j].mean() if np.any(idx == j) else np.nan
                     for j in range(nb)])
    cents = 0.5 * (edges[:-1] + edges[1:])
    good = np.isfinite(prof) & (prof > 0)
    return cents[good], prof[good]


def gauss(r, A, s, off):
    return A * np.exp(-r ** 2 / (2 * s ** 2)) + off


def plummer(r, Nc, Rflat, p, off):
    return Nc / (1 + (r / Rflat) ** 2) ** (p / 2.0) + off


def fwhm_gauss(s):
    return 2.0 * np.sqrt(2.0 * np.log(2.0)) * s


def fwhm_plummer(Rflat, p):
    return 2.0 * Rflat * np.sqrt(2.0 ** (2.0 / p) - 1.0)


def fit_widths(r, N):
    """Return (W_gauss, W_plum, p_plum) or None on failure."""
    r = np.asarray(r, float)
    N = np.asarray(N, float)
    W_g = None
    try:
        p0 = [N.max() - N.min(), 0.1, float(N.min())]
        popt, _ = curve_fit(gauss, r, N, p0=p0,
                            bounds=([0, 1e-3, 0], [np.inf, 1.0, np.inf]),
                            maxfev=10000)
        W_g = fwhm_gauss(popt[1])
    except Exception:
        W_g = None
    W_p = p_p = None
    try:
        p0 = [N.max() - N.min(), 0.1, 2.0, float(N.min())]
        popt, _ = curve_fit(plummer, r, N, p0=p0,
                            bounds=([0, 1e-3, 1.0, 0], [np.inf, 1.0, 4.0, np.inf]),
                            maxfev=10000)
        W_p = fwhm_plummer(popt[1], popt[2])
        p_p = popt[2]
    except Exception:
        W_p = p_p = None
    return W_g, W_p, p_p


def select_epoch_snapshot(pid):
    """Pick the latest pre-collapse snapshot (relaxed filament). We approximate
    'pre-collapse' as the snapshot with the largest time index among those whose
    peak/mean column contrast is still modest (<50). Falls back to the last
    snapshot."""
    snaps = sorted(glob.glob(f'{pid}*.athdf'))
    if not snaps:
        return None
    best = None
    best_t = -1
    for fn in snaps:
        try:
            with h5py.File(fn, 'r') as h5:
                rho = get_density(h5)
                t = float(np.array(h5['Time']).squeeze()) if 'Time' in h5 else \
                    int(re.search(r'\.prim\.(\d+)\.', fn).group(1)) * 0.02
        except Exception:
            continue
        if rho is None:
            continue
        Nmap = column_density(rho)
        contrast = Nmap.max() / (Nmap.mean() + 1e-30)
        if contrast < 50 and t > best_t:
            best_t, best = t, fn
    return best or snaps[-1]


def measure_run(pid):
    fn = select_epoch_snapshot(pid)
    if fn is None:
        return {'pid': pid, 'error': 'no snapshots'}
    with h5py.File(fn, 'r') as h5:
        rho = get_density(h5)
        t = float(np.array(h5['Time']).squeeze()) if 'Time' in h5 else None
    if rho is None:
        return {'pid': pid, 'error': 'no density', 'file': fn}
    r, Nraw = radial_profile(column_density(rho))
    W_form_g, _, _ = fit_widths(r, Nraw)
    rec = dict(parse(pid))
    rec['epoch_file'] = Path(fn).name
    rec['epoch_t'] = t
    rec['W_form'] = W_form_g
    rec['beams'] = {}
    for fwhm in BEAM_FWHMS_LAMDAJ:
        sigma = fwhm / 2.355
        Nr = len(r)
        rgrid = np.linspace(0, r.max(), max(200, Nr))
        kernel = np.exp(-rgrid ** 2 / (2 * sigma ** 2))
        kernel /= kernel.sum()
        Nfine = np.interp(rgrid, r, Nraw)
        Nconv = np.convolve(Nfine, kernel, mode='same')
        Wg, Wp, pp = fit_widths(rgrid, Nconv)
        T1 = (W_form_g / Wp) if (W_form_g and Wp) else None
        rgp = (Wg / Wp) if (Wg and Wp) else None
        rec['beams'][f'{fwhm:.2f}'] = {'beam_fwhm': fwhm,
                                       'W_gauss': Wg, 'W_plum': Wp, 'p_plum': pp,
                                       'T1': T1, 'ratio_GP': rgp}
    # primary result: mid beam (0.08 lambda_J)
    mid = rec['beams'].get('0.08', {})
    rec['T1'] = mid.get('T1')
    rec['ratio_GP'] = mid.get('ratio_GP')
    return rec


def main():
    pids = sorted(set(re.sub(r'\.prim\..*$', '', Path(x).stem)
                      for x in glob.glob('*.athdf')))
    if not pids:
        for rj in glob.glob('campaignB_results*.json'):
            pids = sorted({x['pid'] for x in json.load(open(rj))})
            break
    out = {'runs': [], 'beam_fwhms_lambdaJ': BEAM_FWHMS_LAMDAJ,
           'paper_T1': T1_PAPER, 'paper_T1_plummer': T1_PLUMMER_PAPER}
    for pid in pids:
        rec = measure_run(pid)
        out['runs'].append(rec)
        print(f"{pid}: T1={rec.get('T1')} ratio_GP={rec.get('ratio_GP')} "
              f"(paper T1={T1_PAPER}/{T1_PLUMMER_PAPER})", flush=True)
    # aggregate over the mid beam
    t1s = [r['T1'] for r in out['runs'] if r.get('T1')]
    rgps = [r['ratio_GP'] for r in out['runs'] if r.get('ratio_GP')]
    out['T1_mean'] = float(np.mean(t1s)) if t1s else None
    out['T1_std'] = float(np.std(t1s)) if t1s else None
    out['ratio_GP_mean'] = float(np.mean(rgps)) if rgps else None
    out['ratio_GP_std'] = float(np.std(rgps)) if rgps else None
    Path('campaignB_synthetic_hgbs_t1.json').write_text(json.dumps(out, indent=2))
    print('\n=== Campaign B: synthetic-HGBS T1 forward model ===')
    print(f'T1 (W_form/W_plum) = {out["T1_mean"]:.3f} +- {out["T1_std"]:.3f}  '
          f'(paper 0.606 / Plummer-corrected 0.71)')
    print(f'ratio_GP (W_gauss/W_plum) = {out["ratio_GP_mean"]:.3f} +- '
          f'{out["ratio_GP_std"]:.3f}  (paper 1.17)')


if __name__ == '__main__':
    main()
