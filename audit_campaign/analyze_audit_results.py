#!/usr/bin/env python3
"""
AUDIT CAMPAIGN ANALYSIS — extracts t_frag and lambda/W from outputs.
Reads HDF5 snapshots + history files, classifies fragmentation mode,
computes lambda/W_core, and produces summary JSON + figures.

Usage:
  python3 analyze_audit_results.py --results audit_campaign_results.json --output_dir analysis_output

Feed back to Claude: the summary JSON (audit_summary.json).
"""
import json, glob, re, argparse
import numpy as np
from pathlib import Path
from scipy.signal import find_peaks

W_CORE = 0.3  # lambda_J

def parse_pid(pid):
    """Parse simulation ID to extract parameters."""
    m = re.search(r'f(\d+\.?\d*)', pid); f = float(m.group(1)) if m else None
    m = re.search(r'b(\d+\.?\d*)', pid); beta = float(m.group(1)) if m else None
    m = re.search(r'th(\d+\.?\d*)', pid); theta = float(m.group(1)) if m else 0.0
    m = re.search(r'Lx(\d+)', pid); Lx = int(m.group(1)) if m else 8
    m = re.search(r's(\d+)', pid); seed = int(m.group(1)) if m else 0
    return {"f": f, "beta": beta, "theta": theta, "Lx": Lx, "seed": seed}

def extract_t_frag(output_dir):
    """Extract fragmentation time from the history file (min dt = CFL crash)."""
    hst_files = glob.glob(str(Path(output_dir) / "*.hst"))
    if not hst_files: return None
    try:
        data = np.loadtxt(hst_files[0])
        if data.ndim == 1: data = data.reshape(1,-1)
        times = data[:, 0]
        dts = np.diff(times)
        if len(dts) == 0: return None
        min_dt_idx = np.argmin(dts)
        t_frag = times[min_dt_idx]
        return float(t_frag)
    except: return None

def extract_lambda_W(output_dir):
    """Extract lambda/W from the last HDF5 density snapshot."""
    try:
        import h5py
    except ImportError:
        return None, "RADIAL", 0
    hdf5_files = sorted(glob.glob(str(Path(output_dir) / "*.athdf")))
    if not hdf5_files:
        return None, "NO_OUTPUT", 0
    try:
        with h5py.File(hdf5_files[-1], 'r') as f:
            # Extract density field
            rho = f['rho'][:]  # shape (Nx, Ny, Nz) or (Nblocks, ...)
            if rho.ndim == 4: rho = rho[0]  # first block if multi
            # Longitudinal density profile (average over transverse)
            longitudinal = np.mean(rho, axis=tuple(range(1, rho.ndim)))
            # Find peaks
            peaks, props = find_peaks(longitudinal, height=np.max(longitudinal)*0.1,
                                       distance=len(longituditudinal)//20)
            if len(peaks) >= 2:
                spacings = np.diff(peaks)
                # Convert to lambda_J: dx = Lx/Nx
                nx = len(longitudinal)
                Lx = float(f.attrs.get("RootGridX1Max", nx))  # fallback
                dx = Lx / nx
                mean_spacing = np.median(spacings) * dx  # in lambda_J
                lam_over_W = mean_spacing / W_CORE
                max_contrast = float(np.max(longitudinal) / np.mean(longitudinal))
                return float(lam_over_W), "BEADING", len(peaks)
            else:
                max_contrast = float(np.max(longitudinal) / np.mean(longitudinal)) if np.mean(longitudinal) > 0 else 0
                if max_contrast > 1.5:
                    return None, "TRANSITIONAL", 0
                return None, "RADIAL_COLLAPSE", 0
    except Exception as e:
        return None, f"ERROR:{e}", 0

def analyze_all(results_file, output_dir):
    results = json.loads(Path(results_file).read_text())
    summaries = []

    for r in results:
        if r["status"] != "OK":
            summaries.append({**r, "t_frag": None, "lambda_W": None,
                              "frag_mode": "SIM_FAILED", "n_peaks": 0})
            continue
        pid = r["pid"]
        params = parse_pid(pid)
        # Find output directory
        output_path = Path(f"outputs/{pid}")
        t_frag = extract_t_frag(output_path)
        lam_W, mode, n_peaks = extract_lambda_W(output_path)
        summaries.append({
            "pid": pid, **params, "status": r["status"],
            "wall_s": r["wall_s"], "t_frag": t_frag,
            "lambda_W": lam_W, "frag_mode": mode, "n_peaks": n_peaks,
        })
        print(f"  {pid}: t_frag={t_frag}, lam/W={lam_W}, mode={mode}, peaks={n_peaks}")

    # Aggregate by parameter
    agg = {}
    for s in summaries:
        key = f"f{s.get('f')}_b{s.get('beta')}_th{s.get('theta')}_Lx{s.get('Lx')}"
        if key not in agg: agg[key] = []
        agg[key].append(s)

    summary = {"per_sim": summaries, "aggregated": {}}
    for key, sims in agg.items():
        frag_sims = [s for s in sims if s["frag_mode"] == "BEADING" and s["lambda_W"] is not None]
        radial = [s for s in sims if s["frag_mode"] in ("RADIAL_COLLAPSE", "TRANSITIONAL")]
        tfrags = [s["t_frag"] for s in sims if s["t_frag"] is not None]
        lamWs = [s["lambda_W"] for s in frag_sims]
        summary["aggregated"][key] = {
            "n_total": len(sims),
            "n_beading": len(frag_sims),
            "n_radial": len(radial),
            "t_frag_mean": float(np.mean(tfrags)) if tfrags else None,
            "t_frag_std": float(np.std(tfrags)) if tfrags else None,
            "lambda_W_mean": float(np.mean(lamWs)) if lamWs else None,
            "lambda_W_std": float(np.std(lamWs)) if lamWs else None,
        }

    out_file = Path(output_dir) / "audit_summary.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(summary, indent=2))
    print(f"\nSummary written to {out_file}")
    print(f"Feed this file back to Claude for paper integration.")
    return summary

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="audit_campaign_results.json")
    ap.add_argument("--output_dir", default="analysis_output")
    args = ap.parse_args()
    print("="*60); print("AUDIT CAMPAIGN ANALYSIS"); print("="*60)
    analyze_all(args.results, args.output_dir)
