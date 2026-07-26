#!/usr/bin/env python3
"""
Analyze longitudinal density variance evolution for the EX campaign.
For each EX run, compute σ_lon(t) = std(rho_bar(x)) / mean(rho_bar(x))
where rho_bar(x) = <rho>_{y,z} is the axial density profile.
This directly tests the referee's censoring concern:
if σ_lon(t) grows measurably during the run, longitudinal modes are active.
Output: ex_longitudinal_variance.json with time series per run.
"""
import glob, json, os, sys
import numpy as np

try:
    import h5py
except ImportError:
    print("h5py not available"); sys.exit(1)

BASE = "/data/referee_v40_campaigns_jul2026"
results = {}

def axial_profile(fn):
    """Return (t, rho_bar, rho_max, rho_mean) from one athdf snapshot."""
    try:
        f = h5py.File(fn, 'r')
        prim = np.array(f['prim'])  # shape (Nvar, Nz, Ny, Nx) or meshblock dims
        t = float(f.attrs.get('Time', -1))
        f.close()
    except Exception as e:
        return None
    # density is prim[0]
    rho = prim[0] if prim.ndim == 4 else prim[0, 0]
    # axial profile: mean over y,z (dims -2 and -1 if 3D stored as z,y,x)
    while rho.ndim > 1:
        rho = rho.mean(axis=0)
    rho_bar = rho
    rho_mean = float(rho_bar.mean())
    rho_max = float(rho_bar.max())
    sigma = float(rho_bar.std() / rho_mean) if rho_mean > 0 else 0.0
    return t, sigma, rho_max, rho_mean

for pid_dir in sorted(glob.glob(f"{BASE}/EX_*.hst")):
    pid = os.path.basename(pid_dir).replace('.hst', '')
    snaps = sorted(glob.glob(f"{BASE}/{pid}.prim.*.athdf"))
    if not snaps:
        results[pid] = {'error': 'no snapshots'}
        continue
    ts, sigmas, maxdens = [], [], []
    for sn in snaps:
        res = axial_profile(sn)
        if res is None: continue
        t, sig, rmax, rmean = res
        ts.append(round(t, 4)); sigmas.append(round(sig, 6)); maxdens.append(round(rmax, 3))
    # also get hst-based t_final and dt_final
    hst = pid_dir
    try:
        last = open(hst).readlines()[-1].split()
        t_hst = float(last[0]); dt_hst = float(last[1])
    except:
        t_hst = ts[-1] if ts else -1; dt_hst = -1
    results[pid] = {
        'n_snaps': len(ts),
        't_final_hst': round(t_hst, 4),
        'dt_final_hst': dt_hst,
        't_series': ts,
        'sigma_lon_series': sigmas,
        'rho_max_series': maxdens,
        'sigma_lon_final': sigmas[-1] if sigmas else None,
        'sigma_lon_max': max(sigmas) if sigmas else None,
        'sigma_growth': round(sigmas[-1] / sigmas[0], 2) if len(sigmas) > 1 and sigmas[0] > 0 else None
    }
    print(f"{pid}: n_snaps={len(ts)} t_final={t_hst:.3f} σ_lon_final={sigmas[-1] if sigmas else 'N/A':.4f}")

out = f"{BASE}/ex_longitudinal_variance.json"
with open(out, 'w') as fh:
    json.dump(results, fh, indent=2)
print(f"wrote {out}")
