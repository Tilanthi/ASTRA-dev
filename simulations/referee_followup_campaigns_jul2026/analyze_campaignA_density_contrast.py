#!/usr/bin/env python3
"""Campaign A analysis -- validate the t_frag ~ f^-0.39 scaling against a
density-contrast diagnostic (referee #4).

For each run we build contrast(t) from the dense HDF5 snapshots and extract the
first crossing time of contrast thresholds {10, 100, 1000}; from the .hst file
we also extract the CFL-trigger time (dt <= 1e-8, matching the paper's
definition). We then fit 1/t ~ f^alpha for each diagnostic across the f-grid
and compare the exponents. If the density-contrast exponents agree with the
CFL-trigger exponent, the f-scaling reflects physical collapse dynamics rather
than the numerical trigger.

Run from the directory containing the .athdf / .hst outputs:
  python3 analyze_campaignA_density_contrast.py
"""
import glob
import json
import re
from collections import defaultdict

import h5py
import numpy as np

CONTRAST_THRESHOLDS = [10.0, 100.0, 1000.0]
DT_CFL = 1e-8  # paper's CFL-trigger threshold


def parse(pid):
    def g(p, cast, default=None):
        m = re.search(p, pid)
        return cast(m.group(1)) if m else default
    return {'pid': pid,
            'f': g(r'_f([0-9.]+)', float),
            'beta': g(r'_b([0-9.]+)', float),
            'seed': g(r'_s([0-9.]+)', int)}


def choose_density(h5):
    """Return the 3D density dataset (longest-axis layout) as a numpy array."""
    keys = []

    def rec(g, path=''):
        for k, v in g.items():
            p = path + '/' + k
            if isinstance(v, h5py.Dataset):
                keys.append((p, v))
            elif isinstance(v, h5py.Group):
                rec(v, p)
    rec(h5)
    best = None
    for p, d in keys:
        sh = d.shape
        if len(sh) < 3:
            continue
        score = max(sh) / (min(sh) + 1e-9)
        if best is None or score > best[0]:
            best = (score, p, d)
    if best is None:
        return None
    a = best[2][:]
    a = np.array(a).squeeze()
    while a.ndim > 3:
        a = a[0]
    return a


def snapshot_time(h5, idx, odt):
    """Prefer the time stored in the file; fall back to idx*odt."""
    for key in ('Time', 'time'):
        try:
            return float(h5.attrs[key])
        except Exception:
            pass
    # Athena++ sometimes stores it as a 1-element dataset
    try:
        return float(np.array(h5['Time']).squeeze())
    except Exception:
        pass
    return idx * odt


def contrasts(a):
    """Volume and transverse central density contrasts for one snapshot."""
    rho = np.asarray(a, dtype=float)
    vol_contrast = float(rho.max() / (rho.mean() + 1e-30))
    # transverse map: average over the longitudinal axis (largest dim)
    axis = int(np.argmax(rho.shape))
    trans = rho.mean(axis=axis)
    trans_contrast = float(trans.max() / (trans.mean() + 1e-30))
    return vol_contrast, trans_contrast


def odt_from_config(pid):
    """Try to read odt from the matching .athinput; default 0.005."""
    for pat in (f'configs/**/{pid}.athinput', f'**/{pid}.athinput'):
        for fn in glob.glob(pat, recursive=True):
            txt = Path(fn).read_text()
            m = re.search(r'odt\s*=\s*([0-9.eE+-]+)', txt)
            if m:
                return float(m.group(1))
    return 0.005


def first_crossing(times, values, thr):
    """Linear-interpolated first time `values` reaches `thr`."""
    times = np.asarray(times, dtype=float)
    values = np.asarray(values, dtype=float)
    order = np.argsort(times)
    times, values = times[order], values[order]
    for i in range(1, len(times)):
        if values[i - 1] < thr <= values[i] or values[i] >= thr:
            v0, v1 = values[i - 1], values[i]
            t0, t1 = times[i - 1], times[i]
            if v1 == v0:
                return float(t1)
            return float(t0 + (t1 - t0) * (thr - v0) / (v1 - v0))
    return None


def cfl_trigger_time(hst_path, dt_thr=DT_CFL):
    """First t at which dt <= dt_thr, from the .hst file."""
    try:
        data = np.loadtxt(hst_path, comments='#')
    except Exception:
        return None
    if data.ndim == 1:
        data = data[None, :]
    if data.shape[1] < 2:
        return None
    t, dt = data[:, 0], data[:, 1]
    idx = np.where(dt <= dt_thr)[0]
    return float(t[idx[0]]) if len(idx) else None


def fit_alpha(fs, ts):
    """Fit log(1/t) = a + alpha*log(f). Return (alpha, r2, n)."""
    fs = np.asarray(fs, dtype=float)
    ts = np.asarray(ts, dtype=float)
    mask = np.isfinite(ts) & (ts > 0) & np.isfinite(fs) & (fs > 0)
    fs, ts = fs[mask], ts[mask]
    if len(fs) < 3:
        return None
    x = np.log(fs)
    y = np.log(1.0 / ts)
    a, b = np.polyfit(x, y, 1)
    pred = a * x + b
    ss_res = np.sum((y - pred) ** 2)
    ss_tot = np.sum((y - y.mean()) ** 2)
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else float('nan')
    return {'alpha': float(a), 'r2': float(r2), 'n': int(len(fs))}


from pathlib import Path  # noqa: E402


def main():
    pids = sorted(set(re.sub(r'\.prim\..*$', '', Path(x).stem)
                      for x in glob.glob('*.athdf')))
    if not pids:
        # fall back to pids referenced in the results json
        for rj in glob.glob('campaignA_results*.json'):
            pids = sorted({x['pid'] for x in json.load(open(rj))})
            break
    per_run = {}
    for pid in pids:
        meta = parse(pid)
        odt = odt_from_config(pid)
        snaps = sorted(glob.glob(f'{pid}*.athdf'))
        times, vol_c, trans_c = [], [], []
        for fn in snaps:
            m = re.search(r'\.prim\.(\d+)\.', fn)
            idx = int(m.group(1)) if m else 0
            try:
                with h5py.File(fn, 'r') as h5:
                    t = snapshot_time(h5, idx, odt)
                    a = choose_density(h5)
            except Exception as e:
                print(f'  [skip] {fn}: {e}')
                continue
            if a is None or a.ndim != 3:
                continue
            vc, tc = contrasts(a)
            times.append(t)
            vol_c.append(vc)
            trans_c.append(tc)
        rec = dict(meta)
        rec['n_snapshots'] = len(times)
        if times:
            order = np.argsort(times)
            times = np.array(times)[order]
            vol_c = np.array(vol_c)[order]
            trans_c = np.array(trans_c)[order]
            rec['vol_contrast_max'] = float(np.max(vol_c))
            for thr in CONTRAST_THRESHOLDS:
                rec[f't_vol_contrast_{int(thr)}'] = first_crossing(times, vol_c, thr)
                rec[f't_trans_contrast_{int(thr)}'] = first_crossing(times, trans_c, thr)
        # CFL-trigger time from HST (paper definition, dt<=1e-8)
        hst = next(iter(glob.glob(f'{pid}.hst')), None)
        rec['t_cfl_1e-8'] = cfl_trigger_time(hst) if hst else None
        per_run[pid] = rec
        print(f'{pid}: f={rec.get("f")} n_snap={rec["n_snapshots"]} '
              f'vol_max={rec.get("vol_contrast_max"):.1f} '
              f't_cfl={rec.get("t_cfl_1e-8")}', flush=True)

    # group by f (beta=1.0 main grid), average over seeds
    by_f = defaultdict(list)
    for r in per_run.values():
        if r.get('beta') == 1.0 and r.get('f') is not None:
            by_f[r['f']].append(r)
    fs = sorted(by_f)
    fits = {}
    for diag in ['t_vol_contrast_10', 't_vol_contrast_100',
                 't_vol_contrast_1000', 't_cfl_1e-8']:
        tmean = []
        for f in fs:
            vals = [r[diag] for r in by_f[f] if r.get(diag) is not None]
            tmean.append(np.mean(vals) if vals else np.nan)
        fits[diag] = fit_alpha(fs, tmean)

    out = {'per_run': per_run,
           'fs_main_grid': fs,
           'fits_log1overT_vs_logf': fits,
           'paper_cfl_exponent': 0.39}
    Path('campaignA_density_contrast_timing.json').write_text(json.dumps(out, indent=2))

    print('\n=== Campaign A: 1/t ~ f^alpha (beta=1.0 main grid) ===')
    print(f'{"diagnostic":24s} {"alpha":>7s} {"r^2":>7s} {"n":>3s}')
    for diag, fit in fits.items():
        if fit:
            print(f'{diag:24s} {fit["alpha"]:7.3f} {fit["r2"]:7.3f} {fit["n"]:3d}')
        else:
            print(f'{diag:24s}   (insufficient data)')
    print('\nPaper CFL-trigger exponent = 0.39. Agreement (within ~0.05) between '
          'the density-contrast exponents and the CFL exponent implies the '
          'f-scaling reflects physical collapse dynamics, not the trigger.')


if __name__ == '__main__':
    main()
