"""
ASTRA Filament Campaign V2 — Scientific Analysis Pipeline
Glenn J. White (Open University) / Robin Dey (VBRL Holdings)
2026-04-18

Analyses 208 Athena++ MHD+self-gravity simulations.
Computes: density contrast C(t), filament spacing λ_peak,
growth rate γ, and builds regime diagrams.
"""

import json, glob, h5py, numpy as np, sys, os
from pathlib import Path
from multiprocessing import Pool, cpu_count
import warnings; warnings.filterwarnings('ignore')

# ─── Configuration ─────────────────────────────────────────────────────────
BASE_DIR   = Path('/home/fetch-agi/campaign_1day_v2')
STATUS_FILE= Path('/home/fetch-agi/campaign_status_v2.json')
OUT_DIR    = Path('/home/fetch-agi/analysis_v2')
OUT_DIR.mkdir(exist_ok=True)

# Code units: 4πG = 4π² → λ_J = 1.0, t_ff = sqrt(3π/(32Gρ₀)) ≈ 0.306
FOUR_PI_G = 4.0 * np.pi**2
LAMBDA_J  = 1.0   # Jeans length in code units (by design)
L1        = 4.0   # Domain length in x1

# ─── Assembly helper ────────────────────────────────────────────────────────
def assemble_density(hdf5_path):
    """Read one Athena++ HDF5 file and return (t, full_3D_rho, x1_centres)."""
    with h5py.File(hdf5_path, 'r') as f:
        t    = float(f.attrs['Time'])
        prim = np.array(f['prim'], dtype=np.float32)   # (nvars, nblocks, nz, ny, nx)
        locs = np.array(f['LogicalLocations'])           # (nblocks, 3)
        x1f  = np.array(f['x1f'])                        # (nblocks, nx+1)
        nvars, nblocks, nz, ny, nx = prim.shape
        max_lx = locs[:,0].max() + 1
        max_ly = locs[:,1].max() + 1
        max_lz = locs[:,2].max() + 1
        full_rho = np.zeros((max_lz*nz, max_ly*ny, max_lx*nx), dtype=np.float32)
        for b in range(nblocks):
            lx, ly, lz = locs[b]
            full_rho[lz*nz:(lz+1)*nz, ly*ny:(ly+1)*ny, lx*nx:(lx+1)*nx] = prim[0,b]
        # x1 cell centres (from block 0 faces, extrapolate)
        blk0 = np.where((locs[:,0]==0) & (locs[:,1]==0) & (locs[:,2]==0))[0][0]
        x1_faces = x1f[blk0]
        x1_cc_blk0 = 0.5*(x1_faces[:-1] + x1_faces[1:])
        dx = x1_cc_blk0[1] - x1_cc_blk0[0]
        x1_centres = np.array([x1_cc_blk0[0] + i*dx for i in range(max_lx*nx)])
    return t, full_rho, x1_centres

# ─── Per-simulation analysis ────────────────────────────────────────────────
def analyse_sim(args):
    sim_name, mach, beta, epsilon, batch = args
    sim_dir = BASE_DIR / sim_name / 'outputs'
    hdf5_files = sorted(sim_dir.glob('*.athdf'))
    if not hdf5_files:
        return None

    results = {'name': sim_name, 'mach': mach, 'beta': beta,
               'epsilon': epsilon, 'batch': batch}
    
    times, contrasts, spacings = [], [], []
    
    for hf in hdf5_files:
        try:
            t, rho, x1 = assemble_density(hf)
        except Exception as e:
            continue
        
        # Density contrast
        rho_mean = rho.mean()
        C = rho.max() / rho_mean
        times.append(float(t))
        contrasts.append(float(C))
        
        # Filament spacing: 1D power spectrum of density projected onto x1
        # Project: average over z (axis 0) and y (axis 1)
        rho_1d = rho.mean(axis=(0,1))   # shape: (nx1,)
        # Subtract mean, FFT
        rho_fluct = rho_1d - rho_1d.mean()
        fft_vals  = np.fft.rfft(rho_fluct)
        power     = np.abs(fft_vals)**2
        # Frequencies (k in units of 2π/L1)
        n = len(rho_1d)
        freqs = np.fft.rfftfreq(n, d=(x1[1]-x1[0])) * 2 * np.pi  # angular wavenumber
        # Exclude DC (freq=0)
        if len(power) > 1:
            peak_idx = np.argmax(power[1:]) + 1
            k_peak   = freqs[peak_idx] if freqs[peak_idx] > 0 else np.nan
            lam_peak = 2*np.pi / k_peak if k_peak > 0 else np.nan
        else:
            lam_peak = np.nan
        spacings.append(float(lam_peak) if not np.isnan(lam_peak) else None)
    
    results['times']     = times
    results['contrasts'] = contrasts
    results['spacings']  = spacings
    
    # Final values (t=2.0)
    results['C_final']      = contrasts[-1] if contrasts else None
    results['lam_final']    = spacings[-1]  if spacings  else None
    results['lam_J_ratio']  = (spacings[-1] / LAMBDA_J) if spacings and spacings[-1] else None
    
    # Theory: magneto-Jeans wavelength
    lam_MJ_theory = LAMBDA_J * np.sqrt(1 + 2/beta)
    results['lam_MJ_theory'] = float(lam_MJ_theory)
    
    # Linear growth rate: fit exponential to early C(t) where C < 2
    # C(t) ≈ 1 + A * exp(γ t)  → ln(C-1) = ln(A) + γ t
    early_mask = [i for i,c in enumerate(contrasts) if c > 1.001 and c < 3.0]
    if len(early_mask) >= 3:
        t_arr = np.array([times[i] for i in early_mask])
        c_arr = np.array([contrasts[i] for i in early_mask])
        log_c = np.log(c_arr - 1.0)
        try:
            coeffs = np.polyfit(t_arr, log_c, 1)
            results['growth_rate'] = float(coeffs[0])
        except:
            results['growth_rate'] = None
    else:
        results['growth_rate'] = None

    # Theoretical Jeans growth rate: γ_J = sqrt(4πGρ₀ - k²cs²) for k=2π/λ_J
    # At the Jeans wavenumber: γ_J = 0 (marginal). Peak growth at k→0.
    # For magneto-Jeans: γ_MJ = sqrt(4πGρ₀ - k²(cs² + vA²)) at k_peak
    # Simplified: γ_max ≈ sqrt(4πGρ₀) = sqrt(FOUR_PI_G) ≈ 6.28
    gamma_J_max = np.sqrt(FOUR_PI_G)   # ≈ 6.28 code units⁻¹
    results['gamma_J_theory'] = float(gamma_J_max)
    
    return results

# ─── Main ───────────────────────────────────────────────────────────────────
def main():
    print("Loading campaign status...", flush=True)
    with open(STATUS_FILE) as f:
        status = json.load(f)
    
    sim_results = status.get('results', [])
    print(f"Simulations to analyse: {len(sim_results)}", flush=True)
    
    # Build task list
    tasks = []
    for r in sim_results:
        tasks.append((r['name'], r['mach'], r['beta'],
                      r.get('epsilon', 0.01), r.get('batch', 1)))
    
    # Run analysis in parallel
    n_procs = min(64, cpu_count())
    print(f"Running analysis on {n_procs} CPU cores...", flush=True)
    
    with Pool(n_procs) as pool:
        all_results = pool.map(analyse_sim, tasks)
    
    # Filter None
    all_results = [r for r in all_results if r is not None]
    print(f"Analysed: {len(all_results)} simulations", flush=True)
    
    # Save detailed results
    out_path = OUT_DIR / 'analysis_results.json'
    with open(out_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=lambda x: None if np.isnan(x) else x)
    print(f"Saved: {out_path}", flush=True)
    
    # ─── Summary statistics ──────────────────────────────────────────────
    print("\n=== SUMMARY STATISTICS ===", flush=True)
    
    C_finals = [r['C_final'] for r in all_results if r['C_final'] is not None]
    print(f"Density contrast C_final: min={min(C_finals):.3f}, max={max(C_finals):.3f}, "
          f"mean={np.mean(C_finals):.3f}, median={np.median(C_finals):.3f}")
    
    lam_ratios = [r['lam_J_ratio'] for r in all_results if r['lam_J_ratio'] is not None]
    if lam_ratios:
        print(f"λ_peak/λ_J: min={min(lam_ratios):.3f}, max={max(lam_ratios):.3f}, "
              f"mean={np.mean(lam_ratios):.3f}")
    
    growth_rates = [r['growth_rate'] for r in all_results if r['growth_rate'] is not None]
    if growth_rates:
        print(f"Growth rates γ: min={min(growth_rates):.3f}, max={max(growth_rates):.3f}, "
              f"mean={np.mean(growth_rates):.3f}")
    
    # ─── Batch 1 regime grid (M vs β) ───────────────────────────────────
    batch1 = [r for r in all_results if r['batch'] == 1]
    print(f"\nBatch 1 (10×10 grid): {len(batch1)} simulations")
    
    # Extract unique M and β values
    M_vals  = sorted(set(round(r['mach'],2) for r in batch1))
    B_vals  = sorted(set(round(r['beta'],2) for r in batch1))
    print(f"Mach values: {M_vals}")
    print(f"Beta values: {B_vals}")
    
    # Build 2D grids for C_final and λ_peak
    C_grid   = np.full((len(B_vals), len(M_vals)), np.nan)
    lam_grid = np.full((len(B_vals), len(M_vals)), np.nan)
    gr_grid  = np.full((len(B_vals), len(M_vals)), np.nan)
    M_idx = {m: i for i, m in enumerate(M_vals)}
    B_idx = {b: i for i, b in enumerate(B_vals)}
    
    for r in batch1:
        mi = M_idx.get(round(r['mach'],2))
        bi = B_idx.get(round(r['beta'],2))
        if mi is not None and bi is not None:
            if r['C_final'] is not None:
                C_grid[bi, mi] = r['C_final']
            if r['lam_J_ratio'] is not None:
                lam_grid[bi, mi] = r['lam_J_ratio']
            if r['growth_rate'] is not None:
                gr_grid[bi, mi] = r['growth_rate']
    
    # Print C grid (M cols, β rows)
    print("\nDensity contrast C_final grid (rows=β, cols=M):")
    header = "β\\M  " + "  ".join(f"{m:5.1f}" for m in M_vals)
    print(header)
    for bi, b in enumerate(B_vals):
        row = f"{b:4.1f} " + "  ".join(
            f"{C_grid[bi,mi]:5.2f}" if not np.isnan(C_grid[bi,mi]) else "  --- "
            for mi in range(len(M_vals)))
        print(row)
    
    print("\nλ_peak/λ_J grid (rows=β, cols=M):")
    print(header)
    for bi, b in enumerate(B_vals):
        row = f"{b:4.1f} " + "  ".join(
            f"{lam_grid[bi,mi]:5.3f}" if not np.isnan(lam_grid[bi,mi]) else " ----"
            for mi in range(len(M_vals)))
        print(row)
    
    # Save grids
    grid_data = {
        'M_vals': M_vals, 'B_vals': B_vals,
        'C_grid': C_grid.tolist(), 'lam_grid': lam_grid.tolist(),
        'gr_grid': gr_grid.tolist()
    }
    with open(OUT_DIR / 'regime_grids.json', 'w') as f:
        json.dump(grid_data, f, indent=2)
    print(f"\nGrids saved to {OUT_DIR/'regime_grids.json'}")
    
    # ─── W3-comparison subset ───────────────────────────────────────────
    # W3 conditions: M~2.5-3.5, β~0.5-1.5
    w3_sims = [r for r in all_results if 2.0 <= r['mach'] <= 4.0 and 0.4 <= r['beta'] <= 2.0]
    print(f"\n=== W3 Regime Subset ({len(w3_sims)} sims, M=2-4, β=0.4-2) ===")
    w3_sims_sorted = sorted(w3_sims, key=lambda r: (r['beta'], r['mach']))
    for r in w3_sims_sorted:
        lam_str = f"{r['lam_J_ratio']:.3f}" if r['lam_J_ratio'] else "  ---"
        gr_str  = f"{r['growth_rate']:.3f}"  if r['growth_rate'] else "  ---"
        print(f"  {r['name']:30s}  M={r['mach']:.1f}  β={r['beta']:.1f}  "
              f"C={r['C_final']:.3f}  λ/λ_J={lam_str}  γ={gr_str}")
    
    # Save W3 subset
    with open(OUT_DIR / 'w3_subset.json', 'w') as f:
        json.dump(w3_sims_sorted, f, indent=2, default=lambda x: None)
    print(f"W3 subset saved.")
    
    print("\nAnalysis complete.", flush=True)
    return all_results, grid_data, w3_sims_sorted

if __name__ == '__main__':
    results, grids, w3 = main()
