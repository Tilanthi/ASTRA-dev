#!/usr/bin/env python3
"""
Standalone HDF5 analysis for Campaign A (oblique) and Campaign T1-P.
Reads existing HDF5 snapshots and extracts:
  - λ/W from column density profile (oblique campaign)
  - T1 Gaussian/Plummer correction ratio (T1-P campaign)

HDF5 structure (Athena++ multi-block):
  prim shape: (nvar, nblocks, nz, ny, nx_per_block)
  prim[0] = density, shape (nblocks, nz, ny, nx_per_block)
  LogicalLocations[:, 0] = block x1-index (sort these for x1 ordering)
  Time stored in f.attrs['Time']
  Axes: z=axis0, y=axis1(transverse/radial), x=axis2(filament)

Run on cluster: python3 /home/fetch-agi/standalone_analysis_v2.py
ASTRA-PA — 2026-06-09
"""
import os, sys, glob, json
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks
from scipy.optimize import curve_fit
import h5py, warnings

warnings.filterwarnings('ignore')

# ── Constants ─────────────────────────────────────────────────────────── #
W_CORE   = 0.3          # filament core half-width in Jeans lengths (intrinsic)
HGBS_MIN = 2.52
HGBS_MAX = 3.08
BEAM_FWHM_JEANS = 0.0867  # Herschel beam FWHM in Jeans lengths at typical HGBS distances

# ── HDF5 reader ───────────────────────────────────────────────────────── #
def read_athdf(hdf5_path):
    """Read Athena++ HDF5 multi-block file.
    Returns (rho_3d, x1v_full, x2v, x3v, time).
    rho_3d shape: (nz, ny, nx1_total) — sorted blocks concatenated along x1.
    """
    with h5py.File(hdf5_path, 'r') as f:
        # Time from file attributes
        time = float(f.attrs['Time'])
        
        # prim shape: (nvar, nblocks, nz, ny, nx_per_block)
        prim      = f['prim'][:]
        x1v       = f['x1v'][:]          # (nblocks, nx_per_block)
        x2v       = f['x2v'][0, :]       # (ny,) — same for all blocks
        x3v       = f['x3v'][0, :]       # (nz,)
        logloc    = f['LogicalLocations'][:]  # (nblocks, 3)
    
    # density: prim[0] → (nblocks, nz, ny, nx_per_block)
    rho_blocks = prim[0]  # (nblocks, nz, ny, nx_per_block)
    
    # Sort blocks by x1 logical location
    x1_order = np.argsort(logloc[:, 0])
    rho_sorted = rho_blocks[x1_order]             # sorted (nblocks, nz, ny, nx)
    x1v_sorted = x1v[x1_order]                    # sorted (nblocks, nx)
    
    # Concatenate along x1 axis
    rho_3d = np.concatenate(rho_sorted, axis=2)   # (nz, ny, nx1_total)
    x1_full = x1v_sorted.ravel()                   # (nx1_total,)
    
    return rho_3d, x1_full, x2v, x3v, time

# ── Oblique λ/W measurement ───────────────────────────────────────────── #
def measure_lW_from_hdf5(sim_dir, sim_id):
    """Measure λ/W from the best HDF5 snapshot.
    Looks at all available snapshots; returns result with highest density contrast.
    """
    hdf5_files = sorted(Path(sim_dir).glob("*.prim.*.athdf"))
    if not hdf5_files:
        return None, 0, None, 1.0, None
    
    best_lW = None; best_npk = 0; best_snap = None
    best_contrast = 1.0; best_t = None
    
    for hf in hdf5_files:
        try:
            rho, x1, x2, x3, t = read_athdf(str(hf))
        except Exception as e:
            print(f"  [{sim_id}] Failed {hf.name}: {e}")
            continue
        
        # Axial (column density) profile: mean over z (axis 0) then y (axis 0 of result)
        # rho shape: (nz, ny, nx1) → col: (ny, nx1) → axial: (nx1,)
        col_xy  = rho.mean(axis=0)      # mean over z → (ny, nx1)
        axial   = col_xy.mean(axis=0)   # mean over y → (nx1,)
        
        axial_smooth = gaussian_filter1d(axial, sigma=3)
        col_min = max(axial_smooth.min(), 1e-30)
        contrast = axial_smooth.max() / col_min
        
        peaks, _ = find_peaks(axial_smooth, height=axial_smooth.mean(), distance=5)
        npk = len(peaks)
        
        print(f"  [{sim_id}] {hf.name}: t={t:.3f}  contrast={contrast:.2f}  npk={npk}")
        
        if npk >= 2:
            spacings = np.diff(x1[peaks])
            lam = float(np.mean(spacings))
            lW  = lam / W_CORE
            if lW > 0.5 and (best_lW is None or contrast > best_contrast):
                best_lW = lW; best_npk = npk
                best_snap = hf.name; best_contrast = contrast; best_t = t
    
    return best_lW, best_npk, best_snap, best_contrast, best_t

# ── Profile fitting functions ─────────────────────────────────────────── #
def gaussian_profile(x, A, mu, sigma, C):
    return A * np.exp(-0.5 * ((x - mu) / sigma)**2) + C

def plummer2_profile(x, A, r_P, C):
    return A / (1 + (x / r_P)**2) + C

# ── T1-P Plummer/Gaussian measurement ────────────────────────────────── #
def measure_t1_from_hdf5(sim_dir, sim_id):
    """Measure T1 ratio from transverse column density profile.
    
    The filament forms along x1. x2 is the transverse (radial) direction.
    Column density along x3 (z): integrate rho over z.
    Then average over x1 to get radial profile.
    
    Returns dict with T1_gaussian, T1_plummer, ratio_GP, etc.
    """
    hdf5_files = sorted(Path(sim_dir).glob("*.prim.*.athdf"))
    if not hdf5_files:
        return None
    
    all_snaps = []
    
    for hf in hdf5_files:
        try:
            rho, x1, x2, x3, t = read_athdf(str(hf))
        except Exception as e:
            print(f"  [{sim_id}] Failed {hf.name}: {e}")
            continue
        
        # rho shape: (nz, ny, nx1)
        # Column density along z (x3): mean over axis 0 → (ny, nx1)
        col_2d = rho.mean(axis=0)      # (ny, nx1)
        
        # Radial profile: mean over x1 (filament axis) → (ny,)
        radial = col_2d.mean(axis=1)   # (ny,)
        
        # x2 is the radial coordinate (transverse to filament)
        x_rad = x2
        
        # Centre on zero (x2 should be symmetric around 0)
        x_mid = 0.5 * (x_rad.min() + x_rad.max())
        x_rad_c = x_rad - x_mid
        
        # Convolve with Herschel beam (simulates observation)
        dx = np.abs(x_rad_c[1] - x_rad_c[0])
        sigma_beam = BEAM_FWHM_JEANS / (2 * np.sqrt(2 * np.log(2)))
        n_pix_sigma = sigma_beam / dx
        if n_pix_sigma > 0.5:
            radial_beam = gaussian_filter1d(radial, sigma=n_pix_sigma)
        else:
            radial_beam = radial
        
        # Normalise to peak
        peak_val = radial_beam.max()
        if peak_val < 1e-10:
            continue
        radial_norm = radial_beam / peak_val
        
        # Density contrast (axial)
        axial = col_2d.mean(axis=0)   # (nx1,)
        contrast = axial.max() / max(axial.min(), 1e-30)
        
        # --- Fit Gaussian ---
        try:
            p0_g = [1.0, 0.0, W_CORE, 0.0]
            bounds_g = ([0.1, -0.5, 0.01, -0.5], [2.0, 0.5, 3.0, 0.5])
            popt_g, pcov_g = curve_fit(gaussian_profile, x_rad_c, radial_norm,
                                        p0=p0_g, bounds=bounds_g, maxfev=5000)
            sigma_g = abs(popt_g[2])
            W_g_fwhm = 2 * np.sqrt(2 * np.log(2)) * sigma_g
            T1_gauss = W_CORE / W_g_fwhm
        except Exception as e_g:
            sigma_g = None; W_g_fwhm = None; T1_gauss = None
        
        # --- Fit Plummer-2 ---
        try:
            p0_p = [1.0, W_CORE, 0.0]
            bounds_p = ([0.1, 0.01, -0.5], [2.0, 3.0, 0.5])
            popt_p, pcov_p = curve_fit(plummer2_profile, x_rad_c, radial_norm,
                                        p0=p0_p, bounds=bounds_p, maxfev=5000)
            r_P = abs(popt_p[1])
            # FWHM of Plummer-2: at half-max, 1/(1+(x/r_P)^2)=0.5 → x = r_P
            # So FWHM = 2 * r_P
            W_p_fwhm = 2 * r_P
            T1_plum = W_CORE / W_p_fwhm
        except Exception as e_p:
            r_P = None; W_p_fwhm = None; T1_plum = None
        
        ratio_GP = (W_g_fwhm / W_p_fwhm) if (W_g_fwhm and W_p_fwhm) else None
        
        snap_info = {
            't': t, 'snap': hf.name, 'contrast': contrast,
            'W_gaussian': W_g_fwhm, 'T1_gaussian': T1_gauss,
            'W_plummer':  W_p_fwhm, 'T1_plummer':  T1_plum,
            'ratio_GP':   ratio_GP
        }
        all_snaps.append(snap_info)
        
        def fmt(v):
            return f"{v:.4f}" if v is not None else "None"
        print(f"  [{sim_id}] {hf.name}: t={t:.3f}  "
              f"T1_g={fmt(T1_gauss)}  T1_p={fmt(T1_plum)}  "
              f"ratio_GP={fmt(ratio_GP)}  contrast={contrast:.2f}")
    
    if not all_snaps:
        return None
    
    # Return highest-contrast snapshot result
    all_snaps.sort(key=lambda s: s['contrast'], reverse=True)
    return all_snaps[0]

# ─────────────────────────────────────────────────────────────────────── #
#  OBLIQUE CAMPAIGN ANALYSIS
# ─────────────────────────────────────────────────────────────────────── #
def analyze_oblique():
    print("\n" + "="*60)
    print("OBLIQUE CAMPAIGN — λ/W MEASUREMENT")
    print("="*60)
    
    SIMS_DIR = Path("/data/oblique_campaign/sims")
    results = []
    
    for sim_dir in sorted(SIMS_DIR.glob("OBL_*")):
        sid = sim_dir.name
        parts = sid.split('_')
        try:
            theta = float(parts[1][1:])
            beta  = float(parts[2][1:].replace('p', '.'))
            f_val = float(parts[3][1:].replace('p', '.'))
            seed  = int(parts[4][1:])
        except:
            continue
        
        lW, npk, best_snap, contrast, best_t = measure_lW_from_hdf5(sim_dir, sid)
        hgbs = bool(lW and HGBS_MIN <= lW <= HGBS_MAX)
        
        def fmt(v, d=3):
            return f"{v:.{d}f}" if v is not None else "None"
        
        print(f"  RESULT {sid}: lW={fmt(lW)}  npk={npk}  "
              f"snap={best_snap}  t={fmt(best_t)}  HGBS={hgbs}")
        
        results.append({
            'sim_id': sid, 'theta': theta, 'beta': beta, 'f': f_val,
            'seed': seed, 'lW': lW, 'n_peaks': npk,
            'hgbs_match': hgbs, 'best_snap': best_snap,
            'contrast': contrast, 'best_t': best_t
        })
    
    # Summary by theta
    print("\n--- OBLIQUE SUMMARY BY THETA ---")
    for theta in [30.0, 45.0, 60.0]:
        grp = [r for r in results if r['theta'] == theta]
        if not grp:
            print(f"  θ={theta:.0f}°: no sims yet")
            continue
        lWs = [r['lW'] for r in grp if r['lW']]
        n_hgbs = sum(1 for r in grp if r['hgbs_match'])
        if lWs:
            print(f"  θ={theta:.0f}°: lW = {np.mean(lWs):.3f} ± {np.std(lWs):.3f}  "
                  f"({n_hgbs}/{len(grp)} HGBS)  n_meas={len(lWs)}/{len(grp)}")
        else:
            print(f"  θ={theta:.0f}°: no measurable lW ({len(grp)} sims)")
    
    # Summary by beta (within theta=30 which is what we have so far)
    print("\n--- OBLIQUE SUMMARY BY BETA (theta=30) ---")
    for beta in [0.5, 1.0, 2.0]:
        grp = [r for r in results if r['beta'] == beta and r['theta'] == 30]
        if not grp:
            continue
        lWs = [r['lW'] for r in grp if r['lW']]
        if lWs:
            print(f"  β={beta}: lW = {np.mean(lWs):.3f} ± {np.std(lWs):.3f}  n={len(lWs)}/{len(grp)}")
        else:
            print(f"  β={beta}: no measurable lW ({len(grp)} sims)")
    
    # Save JSON
    out = {
        'per_theta': {},
        'per_sim': results
    }
    for theta in [30.0, 45.0, 60.0]:
        grp = [r for r in results if r['theta'] == theta]
        lWs = [r['lW'] for r in grp if r['lW']]
        out['per_theta'][str(int(theta))] = {
            'n_sims': len(grp), 'n_measured': len(lWs),
            'mean_lW': float(np.mean(lWs)) if lWs else None,
            'std_lW':  float(np.std(lWs))  if lWs else None,
            'hgbs': sum(1 for r in grp if r['hgbs_match'])
        }
    
    with open('/data/oblique_campaign/oblique_standalone_results.json', 'w') as jf:
        json.dump(out, jf, indent=2, default=lambda x: float(x) if hasattr(x, '__float__') else str(x))
    print("\nSaved: /data/oblique_campaign/oblique_standalone_results.json")
    return results

# ─────────────────────────────────────────────────────────────────────── #
#  T1-P CAMPAIGN ANALYSIS
# ─────────────────────────────────────────────────────────────────────── #
def analyze_t1p():
    print("\n" + "="*60)
    print("T1-P CAMPAIGN — PLUMMER CORRECTION MEASUREMENT")
    print("="*60)
    
    SIMS_DIR = Path("/data/t1_plummer/sims")
    results = []
    
    for sim_dir in sorted(SIMS_DIR.glob("T1P_*")):
        sid = sim_dir.name
        parts = sid.split('_')
        try:
            f_val = float(parts[1][1:].replace('p', '.'))
            beta  = float(parts[2][1:].replace('p', '.'))
            seed  = int(parts[3][1:])
        except:
            continue
        
        r = measure_t1_from_hdf5(sim_dir, sid)
        
        def fmt(v, d=4):
            return f"{v:.{d}f}" if v is not None else "None"
        
        if r:
            print(f"  RESULT {sid}: T1_gauss={fmt(r['T1_gaussian'])}  "
                  f"T1_plum={fmt(r['T1_plummer'])}  "
                  f"ratio_GP={fmt(r['ratio_GP'])}  "
                  f"contrast={r['contrast']:.2f}  t={r['t']:.3f}")
            results.append({
                'sim_id': sid, 'f': f_val, 'beta': beta, 'seed': seed,
                'T1_gaussian': r['T1_gaussian'],
                'T1_plummer':  r['T1_plummer'],
                'ratio_GP':    r['ratio_GP'],
                'W_gaussian':  r['W_gaussian'],
                'W_plummer':   r['W_plummer'],
                'contrast':    r['contrast'],
                't_snap':      r['t']
            })
        else:
            print(f"  RESULT {sid}: NO MEASUREMENT")
    
    # Summary by beta
    print("\n--- T1-P SUMMARY ---")
    for beta in [0.5, 1.0, 2.0]:
        grp = [r for r in results if r['beta'] == beta]
        if not grp:
            continue
        t1g = [r['T1_gaussian'] for r in grp if r['T1_gaussian'] is not None]
        t1p = [r['T1_plummer']  for r in grp if r['T1_plummer']  is not None]
        rgp = [r['ratio_GP']    for r in grp if r['ratio_GP']    is not None]
        if t1p:
            print(f"  β={beta}: T1_gauss={np.mean(t1g):.4f}±{np.std(t1g):.4f}  "
                  f"T1_plum={np.mean(t1p):.4f}±{np.std(t1p):.4f}  "
                  f"ratio_GP={np.mean(rgp):.4f}±{np.std(rgp):.4f}  n={len(t1p)}/{len(grp)}")
        else:
            print(f"  β={beta}: no valid measurements ({len(grp)} sims)")
    
    # Combined
    all_t1p = [r['T1_plummer'] for r in results if r['T1_plummer'] is not None]
    all_t1g = [r['T1_gaussian'] for r in results if r['T1_gaussian'] is not None]
    all_rgp = [r['ratio_GP']   for r in results if r['ratio_GP']   is not None]
    print(f"\n  COMBINED ({len(results)} sims, {len(all_t1p)} with T1_plummer):")
    if all_t1p:
        print(f"    T1_plummer  = {np.mean(all_t1p):.4f} ± {np.std(all_t1p):.4f}")
        print(f"    T1_gaussian = {np.mean(all_t1g):.4f} ± {np.std(all_t1g):.4f}")
        print(f"    ratio_GP    = {np.mean(all_rgp):.4f} ± {np.std(all_rgp):.4f}")
        print(f"\n  COMPARISON:")
        print(f"    Current paper uses T1_gaussian = 0.606 ± 0.072")
        print(f"    Semi-analytic estimate T1_plummer = 0.70–0.73")
        print(f"    Measured T1_plummer  = {np.mean(all_t1p):.3f} ± {np.std(all_t1p):.3f}")
        print(f"    Measured T1_gaussian = {np.mean(all_t1g):.3f} ± {np.std(all_t1g):.3f}")
    
    # Save JSON
    summary = {
        'n_sims_analysed': len(results),
        'T1_plummer_mean':  float(np.mean(all_t1p)) if all_t1p else None,
        'T1_plummer_std':   float(np.std(all_t1p))  if all_t1p else None,
        'T1_gaussian_mean': float(np.mean(all_t1g)) if all_t1g else None,
        'T1_gaussian_std':  float(np.std(all_t1g))  if all_t1g else None,
        'ratio_GP_mean': float(np.mean(all_rgp)) if all_rgp else None,
        'ratio_GP_std':  float(np.std(all_rgp)) if all_rgp else None,
        'per_sim': [{k: (float(v) if isinstance(v, (float, np.floating)) else v)
                     for k, v in r.items()} for r in results]
    }
    with open('/data/t1_plummer/t1p_standalone_results.json', 'w') as jf:
        json.dump(summary, jf, indent=2)
    print("\nSaved: /data/t1_plummer/t1p_standalone_results.json")
    return results

if __name__ == '__main__':
    obl_results = analyze_oblique()
    t1p_results = analyze_t1p()
    print("\n=== ANALYSIS COMPLETE ===")
