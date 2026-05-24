import os
#!/usr/bin/env python3
"""
THEORETICIAN CAMPAIGN 2026 — Proven ThreadPoolExecutor Runner
Resolves: (1) Perpendicular-field λ/W crisis  (2) Supercritical extrapolation

Campaign A: 280 sims — Mixed field geometry (θ × f × β × seeds), 512×64×64, 16λJ
Campaign B:  90 sims — Supercritical extension (f × β × seeds), 768×64×64, 24λJ
Campaign C:  36 sims — Perpendicular domain convergence (L × f × seeds), 512×64×64

Uses: proven athinput format, DT_KILL watchdog, HDF5 management, λ/W analysis
"""

import subprocess, time, os, json, math, glob, signal
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# ── Paths & constants ─────────────────────────────────────────────────────────
BASE       = Path("/data/theoretician_2026")
ATHENA_BIN = "/home/fetch-agi/athena/bin/athena"
FOUR_PI_G  = 39.4784176044
DT_KILL    = 1.0e-6
POLL       = 8.0
NP         = 32       # np=32: valid for any nx1 with MB_nx1=nx1//16 → always 64 MBs
MAX_CONC   = 6        # 6 × 32 = 192 cores (within 220 vCPU)
WALL_A     = 7200     # Campaign A: 2h WALL_LIMIT
WALL_B     = 10800    # Campaign B: 3h (larger domain)
WALL_C     = 7200     # Campaign C: 2h

# ── athinput generator ───────────────────────────────────────────────────────
def make_athinput(sim_id, nx1, nx2, nx3, x1min, x1max, f, beta, seed,
                  theta_deg, tlim, hdf5_dt=0.1):
    geom = "longitudinal" if theta_deg == 0 else \
           "perpendicular" if theta_deg == 90 else "oblique"
    return f"""<job>
problem_id  = {sim_id}
coordinate  = cartesian

<time>
cfl_number  = 0.3
tlim        = {tlim}
nlim        = -1

<output1>
file_type   = hst
dt          = 0.01

<output2>
file_type   = hdf5
variable    = prim
dt          = {hdf5_dt}

<mesh>
nx1         = {nx1}
x1min       = {x1min}
x1max       = {x1max}
ix1_bc      = periodic
ox1_bc      = periodic

nx2         = {nx2}
x2min       = -0.5
x2max       = 0.5
ix2_bc      = periodic
ox2_bc      = periodic

nx3         = {nx3}
x3min       = -0.5
x3max       = 0.5
ix3_bc      = periodic
ox3_bc      = periodic

<meshblock>
nx1 = {nx1 // 16}
nx2 = 32
nx3 = 32

<hydro>
iso_sound_speed = 1.0

<gravity>
grav_mean_rho = {f:.6f}

<problem>
four_pi_G       = {FOUR_PI_G}
f_line_mass     = {f:.6f}
plasma_beta     = {beta}
mach_number     = 1.0
W_core          = 0.3
perturb_ampl    = 0.0001
random_seed     = {seed}
bfield_geometry = {geom}
theta_deg       = {float(theta_deg)}
"""

# ── Lambda/W analysis from last HDF5 snapshot ─────────────────────────────────
def measure_lambda_W(sim_dir, sim_id, nx1):
    """Measure λ/W from last HDF5 snapshot using correct meshblock-aware 3D reconstruction."""
    try:
        import numpy as np
        import h5py
        from scipy.signal import find_peaks
        from scipy.ndimage import gaussian_filter1d

        athdf_files = sorted(glob.glob(str(sim_dir / "*.athdf")))
        if not athdf_files:
            return None, "no_hdf5"

        fn = athdf_files[-1]
        with h5py.File(fn, 'r') as hf:
            if 'prim' not in hf:
                return None, "no_prim"
            prim = hf['prim'][:]   # shape: (nvar, nmb, nmb_nz, nmb_ny, nmb_nx)
            locs = hf['LogicalLocations'][:]  # (nmb, 3) = (il, jl, kl)
            MBS  = hf.attrs['MeshBlockSize']   # [MBX, MBY, MBZ]
            RGS  = hf.attrs['RootGridSize']    # [NX, NY, NZ]

        if prim.ndim != 5:
            return None, f"unexpected_prim_ndim:{prim.ndim}"

        rho_mb = prim[0]  # (nmb, nmb_nz, nmb_ny, nmb_nx)
        NX = int(RGS[0]); NY = int(RGS[1]); NZ = int(RGS[2])
        MBX = int(MBS[0]); MBY = int(MBS[1]); MBZ = int(MBS[2])

        # Reconstruct full 3D density array (NZ, NY, NX)
        full_rho = np.zeros((NZ, NY, NX), dtype=np.float32)
        for mb in range(locs.shape[0]):
            il = int(locs[mb, 0]); jl = int(locs[mb, 1]); kl = int(locs[mb, 2])
            ix0 = il * MBX; iy0 = jl * MBY; iz0 = kl * MBZ
            full_rho[iz0:iz0+MBZ, iy0:iy0+MBY, ix0:ix0+MBX] = rho_mb[mb]

        # Column density along filament axis (x = axis 2)
        col_density = full_rho.sum(axis=(0, 1)).astype(float)  # shape (NX,)

        # Smooth and find peaks
        sigma = max(4, NX // 80)
        smoothed = gaussian_filter1d(col_density, sigma=sigma)
        med = float(np.median(smoothed))
        min_dist = max(20, NX // 20)

        peaks, _ = find_peaks(smoothed, height=1.3 * med, distance=min_dist)
        if len(peaks) < 2:
            peaks, _ = find_peaks(smoothed, height=1.1 * med, distance=min_dist)
            if len(peaks) < 2:
                return None, f"too_few_peaks:{len(peaks)}"

        # λ = median peak spacing in λJ
        lambda_cells = float(np.median(np.diff(peaks)))
        lambda_lJ = lambda_cells * nx1 / NX
        lambda_W = lambda_lJ / 0.3  # W_core = 0.3 λJ

        return lambda_W, f"peaks={len(peaks)},lam={lambda_lJ:.3f}lJ"

    except Exception as e:
        return None, f"error:{e}"

# ── Sim runner ────────────────────────────────────────────────────────────────
def run_sim(sim):
    """Run one simulation with DT_KILL watchdog."""
    sim_dir = Path(sim['dir'])
    status_path = sim_dir / "status.json"

    # Skip if already done
    if status_path.exists():
        try:
            ex = json.loads(status_path.read_text())
            if ex.get('class') in ('FRAG', 'TIMEOUT', 'FAILED'):
                return ex
        except:
            pass

    sim_dir.mkdir(parents=True, exist_ok=True)
    athin = sim_dir / "athinput"
    athin.write_text(sim['athinput'])
    stdout = sim_dir / "stdout.txt"

    cmd = f"mpirun -np {NP} {ATHENA_BIN} -i {athin} > {stdout} 2>&1"
    t0 = datetime.now()
    proc = subprocess.Popen(cmd, shell=True, cwd=str(sim_dir), preexec_fn=os.setsid)

    t_frag = None
    status = "RUNNING"
    last_hdf5_purge = time.time()

    while proc.poll() is None:
        time.sleep(POLL)
        elapsed = (datetime.now() - t0).total_seconds()

        # WALL_LIMIT check
        if elapsed > sim['wall']:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except:
                try:
                    import os as _os, signal as _sig
                    _os.killpg(_os.getpgid(proc.pid), _sig.SIGKILL)
                except Exception:
                    proc.kill()
            status = "TIMEOUT"
            break

        # Periodic HDF5 purge: keep only last 2 files
        if elapsed - last_hdf5_purge > 60:
            athdf_files = sorted(glob.glob(str(sim_dir / "*.athdf")))
            if len(athdf_files) > 2:
                for f in athdf_files[:-2]:
                    try: os.remove(f)
                    except: pass
            last_hdf5_purge = elapsed

        # DT_KILL check
        try:
            lines = stdout.read_text().split('\n')
            for line in reversed(lines[-60:]):
                if 'dt=' in line:
                    for part in line.split():
                        if part.startswith('dt='):
                            try:
                                dt_val = float(part[3:])
                                if dt_val < DT_KILL:
                                    for pp in line.split():
                                        if pp.startswith('time='):
                                            t_frag = float(pp[5:])
                                            break
                                    try:
                                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                                    except:
                                        proc.kill()
                                    status = "FRAG"
                            except:
                                pass
                            break
                    break
        except:
            pass

        if status != "RUNNING":
            break

    if proc.poll() is None:
        try:
            os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
        except:
            proc.kill()
    if status == "RUNNING":
        status = "TIMEOUT"

    # Fallback t_frag extraction
    if status == "FRAG" and t_frag is None:
        try:
            lines = stdout.read_text().split('\n')
            for line in reversed(lines[-300:]):
                if 'time=' in line and 'dt=' in line:
                    for pp in line.split():
                        if pp.startswith('time='):
                            t_frag = float(pp[5:]); break
                    if t_frag: break
        except:
            pass

    # λ/W measurement
    lw, lw_note = measure_lambda_W(sim_dir, sim['sim_id'], sim.get('x_domain_lJ', 16))

    # Keep only last HDF5 snapshot (for potential re-analysis)
    athdf_files = sorted(glob.glob(str(sim_dir / "*.athdf")))
    for f in athdf_files[:-1]:
        try: os.remove(f)
        except: pass

    wall_time = (datetime.now() - t0).total_seconds()
    result = {
        'sim_id':  sim['sim_id'],
        'class':   status,
        't_frag':  t_frag,
        'lambda_W': lw,
        'lw_note': lw_note,
        'f':       sim['f'],
        'beta':    sim['beta'],
        'theta':   sim['theta'],
        'seed':    sim['seed'],
        'campaign': sim['campaign'],
        'wall_time': wall_time,
    }
    if 'L_lJ' in sim:
        result['L_lJ'] = sim['L_lJ']

    status_path.write_text(json.dumps(result, indent=2))

    flag = "✓" if status=="FRAG" else ("T" if status=="TIMEOUT" else "✗")
    lw_str = f"λ/W={lw:.2f}" if lw else f"λ/W=n/a({lw_note})"
    tf_str = f"t={t_frag:.4f}" if t_frag else "t=n/a"
    ts = datetime.now().strftime('%H:%M:%S')
    print(f"[{ts}] {flag} {sim['sim_id']:<55} {status:<8} {tf_str}  {lw_str}  wall={wall_time:.0f}s", flush=True)
    return result

# ── Campaign builders ─────────────────────────────────────────────────────────
def build_campaign_A():
    """280 sims: θ×f×β×seed, 512×64×64, L=16λJ"""
    sims = []
    theta_vals = [0, 15, 30, 45, 60, 75, 90]
    f_vals     = [1.0, 1.5, 2.0, 2.5]
    beta_vals  = [0.3, 1.0]
    seeds      = [42, 137, 251, 367, 499]
    NX1, NX2, NX3 = 512, 64, 64
    L = 16  # λJ
    TLIM = 3.0
    for theta in theta_vals:
        for f in f_vals:
            for beta in beta_vals:
                for seed in seeds:
                    ts = str(theta).replace('.','p')
                    fs = str(f).replace('.','p')
                    bs = str(beta).replace('.','p')
                    sid = f"A_th{ts}_f{fs}_b{bs}_s{seed}"
                    d = BASE / "A" / sid
                    sims.append({
                        'sim_id': sid, 'campaign': 'A',
                        'f': f, 'beta': beta, 'theta': theta, 'seed': seed,
                        'x_domain_lJ': L, 'wall': WALL_A,
                        'dir': str(d),
                        'athinput': make_athinput(
                            sid, NX1, NX2, NX3, -L/2, L/2,
                            f, beta, seed, theta, TLIM
                        ),
                    })
    return sims

def build_campaign_B():
    """90 sims: f×β×seed, 768×64×64, L=24λJ, θ=0°"""
    sims = []
    f_vals    = [1.3, 1.5, 1.8, 2.0, 2.5, 3.0]
    beta_vals = [0.3, 1.0, 3.0]
    seeds     = [42, 137, 251, 367, 499]
    NX1, NX2, NX3 = 768, 64, 64
    L = 24
    TLIM = 2.0
    for f in f_vals:
        for beta in beta_vals:
            for seed in seeds:
                fs = str(f).replace('.','p')
                bs = str(beta).replace('.','p')
                sid = f"B_f{fs}_b{bs}_s{seed}"
                d = BASE / "B" / sid
                sims.append({
                    'sim_id': sid, 'campaign': 'B',
                    'f': f, 'beta': beta, 'theta': 0, 'seed': seed,
                    'x_domain_lJ': L, 'wall': WALL_B,
                    'dir': str(d),
                    'athinput': make_athinput(
                        sid, NX1, NX2, NX3, -L/2, L/2,
                        f, beta, seed, 0, TLIM
                    ),
                })
    return sims

def build_campaign_C():
    """36 sims: L×f×seed, 512×64×64, θ=90°, β=1.0"""
    sims = []
    L_vals = [12, 16, 20, 24]
    f_vals = [1.0, 1.5, 2.0]
    seeds  = [42, 137, 251]
    NX2, NX3 = 64, 64
    TLIM = 3.0
    for L in L_vals:
        NX1 = 512  # fixed resolution cells, variable physical extent
        for f in f_vals:
            for seed in seeds:
                Ls = str(L)
                fs = str(f).replace('.','p')
                sid = f"C_L{Ls}_f{fs}_s{seed}"
                d = BASE / "C" / sid
                sims.append({
                    'sim_id': sid, 'campaign': 'C',
                    'f': f, 'beta': 1.0, 'theta': 90, 'seed': seed,
                    'L_lJ': L, 'x_domain_lJ': L, 'wall': WALL_C,
                    'dir': str(d),
                    'athinput': make_athinput(
                        sid, NX1, NX2, NX3, -L/2, L/2,
                        f, 1.0, seed, 90, TLIM
                    ),
                })
    return sims

# ── Progress reporter ─────────────────────────────────────────────────────────
def report(results, campaign_name, total):
    frag = [r for r in results if r.get('class')=='FRAG']
    tout = [r for r in results if r.get('class')=='TIMEOUT']
    lw_ok = [r for r in frag if r.get('lambda_W')]
    lw_vals = [r['lambda_W'] for r in lw_ok]
    lw_str = f"mean λ/W={sum(lw_vals)/len(lw_vals):.3f}" if lw_vals else "λ/W=n/a"
    disk_r = subprocess.run("df -h /data | tail -1", shell=True, capture_output=True, text=True)
    disk = disk_r.stdout.strip().split()[4] if disk_r.stdout else "?"
    print(f"[progress] {campaign_name}: {len(results)}/{total} | FRAG:{len(frag)} TOUT:{len(tout)} | {lw_str} | disk:{disk}", flush=True)

# ── Campaign runner ───────────────────────────────────────────────────────────
def run_campaign(sims, campaign_name, results_path):
    print(f"\n{'='*70}", flush=True)
    print(f"{campaign_name}: {len(sims)} simulations | np={NP} | max_conc={MAX_CONC}", flush=True)
    print(f"{'='*70}", flush=True)

    results = []
    done_count = 0

    with ThreadPoolExecutor(max_workers=MAX_CONC) as executor:
        futures = {executor.submit(run_sim, sim): sim for sim in sims}
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            done_count += 1
            if done_count % 10 == 0 or done_count == len(sims):
                report(results, campaign_name, len(sims))
                results_path.write_text(json.dumps(results, indent=2))

    results_path.write_text(json.dumps(results, indent=2))

    # Final purge: keep NO HDF5 from completed campaign (already kept last per-sim)
    # Now purge all HDF5 to free disk
    n_purged = 0
    camp_dir = BASE / campaign_name.split()[0][-1]  # 'A', 'B', 'C'
    for f in glob.glob(str(camp_dir / "**/*.athdf"), recursive=True):
        try: os.remove(f); n_purged += 1
        except: pass
    for f in glob.glob(str(camp_dir / "**/*.athdf.xdmf"), recursive=True):
        try: os.remove(f); n_purged += 1
        except: pass
    if n_purged > 0:
        print(f"[purge] {campaign_name}: deleted {n_purged} HDF5 files", flush=True)

    disk_r = subprocess.run("df -h /data | tail -1", shell=True, capture_output=True, text=True)
    print(f"[disk] {disk_r.stdout.strip()}", flush=True)

    frag = [r for r in results if r.get('class')=='FRAG']
    tout = [r for r in results if r.get('class')=='TIMEOUT']
    lw_vals = [r['lambda_W'] for r in frag if r.get('lambda_W')]
    print(f"\n{campaign_name} COMPLETE: {len(frag)}/{len(results)} FRAG | {len(tout)} TIMEOUT", flush=True)
    if lw_vals:
        import numpy as np
        print(f"  λ/W: mean={np.mean(lw_vals):.3f} ± {np.std(lw_vals):.3f} (n={len(lw_vals)})", flush=True)
    return results

# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    BASE.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    print("=" * 70, flush=True)
    print("THEORETICIAN CAMPAIGN 2026", flush=True)
    print(f"Start: {ts}", flush=True)
    print(f"Binary: {ATHENA_BIN}", flush=True)
    print(f"np={NP} | max_conc={MAX_CONC} | DT_KILL={DT_KILL}", flush=True)
    print("=" * 70, flush=True)

    disk_r = subprocess.run("df -h /data | tail -1", shell=True, capture_output=True, text=True)
    print(f"[disk] {disk_r.stdout.strip()}", flush=True)

    # Build sim lists
    sims_A = build_campaign_A()
    sims_B = build_campaign_B()
    sims_C = build_campaign_C()
    print(f"\nSimulations: A={len(sims_A)} | B={len(sims_B)} | C={len(sims_C)} | Total={len(sims_A)+len(sims_B)+len(sims_C)}", flush=True)

    # Campaign A
    res_A = run_campaign(sims_A, "Campaign A (Mixed Field)", BASE / "A_results.json")

    # Campaign B
    res_B = run_campaign(sims_B, "Campaign B (Supercritical)", BASE / "B_results.json")

    # Campaign C
    res_C = run_campaign(sims_C, "Campaign C (Perp Domain)", BASE / "C_results.json")

    # Combined summary
    all_results = {'A': res_A, 'B': res_B, 'C': res_C}
    (BASE / "theoretician_all_results.json").write_text(json.dumps(all_results, indent=2))

    # Final summary
    all_sims = res_A + res_B + res_C
    n_frag = sum(1 for r in all_sims if r.get('class')=='FRAG')
    n_tout = sum(1 for r in all_sims if r.get('class')=='TIMEOUT')
    lw_all = [r['lambda_W'] for r in all_sims if r.get('lambda_W')]
    print(f"\n{'='*70}", flush=True)
    print("ALL CAMPAIGNS COMPLETE", flush=True)
    print(f"Total: {len(all_sims)} | FRAG:{n_frag} | TIMEOUT:{n_tout}", flush=True)
    if lw_all:
        import numpy as np
        print(f"Overall λ/W: {np.mean(lw_all):.3f} ± {np.std(lw_all):.3f} (n={len(lw_all)})", flush=True)
    disk_r = subprocess.run("df -h /data | tail -1", shell=True, capture_output=True, text=True)
    print(f"[disk] {disk_r.stdout.strip()}", flush=True)
    print(f"Results: {BASE}/theoretician_all_results.json", flush=True)
    print("=" * 70, flush=True)

if __name__ == "__main__":
    main()
