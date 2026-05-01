#!/usr/bin/env python3
"""
BRIDGE_GRID Reclassifier v2 — reads BOTH stdout.txt and stdout_rerun.txt.
Uses earliest t_frag crossing from either file.
"""
import json, re, sys
from pathlib import Path
from datetime import datetime

OUTPUT_BASE   = Path("/data/bridge_grid_runs")
DT_THRESH     = 1e-8
RESULTS_FILE  = OUTPUT_BASE / "bridge_grid_reclassified_v2.json"
CYCLE_PAT     = re.compile(r'cycle=(\d+)\s+time=([0-9.e+\-]+)\s+dt=([0-9.e+\-]+)')

def read_stdout_dt(stdout_path: Path):
    """Return (t_frag, dt_min, t_final, n_cycles) from one stdout file."""
    t_frag = None; dt_min = float('inf'); t_final = None; n_cycles = 0
    try:
        with open(stdout_path, 'r', errors='replace') as f:
            for line in f:
                m = CYCLE_PAT.search(line)
                if not m: continue
                n_cycles += 1
                t  = float(m.group(2))
                dt = float(m.group(3))
                t_final = t
                if dt < dt_min: dt_min = dt
                if t_frag is None and dt < DT_THRESH:
                    t_frag = round(t, 6)
    except Exception:
        pass
    return t_frag, (dt_min if dt_min < float('inf') else None), t_final, n_cycles

def reclassify_sim(sim_dir: Path) -> dict:
    sim_id = sim_dir.name
    status_file = sim_dir / "status.json"

    if not status_file.exists():
        return {"sim_id": sim_id, "outcome": "MISSING_STATUS"}

    with open(status_file) as f:
        status = json.load(f)

    # Parse f and beta from dir name for sorting
    parts = sim_id.split('_')
    try:
        f_val    = float([p for p in parts if p.startswith('f')][0][1:])
        beta_val = float([p for p in parts if p.startswith('beta')][0][4:])
    except Exception:
        f_val = 0.0; beta_val = 0.0

    # Try both stdout files; pick earliest t_frag
    candidates = []
    for fname in ['stdout.txt', 'stdout_rerun.txt']:
        fp = sim_dir / fname
        if fp.exists():
            tf, dm, t_fin, nc = read_stdout_dt(fp)
            candidates.append({'file': fname, 't_frag': tf, 'dt_min': dm,
                                't_final': t_fin, 'n_cycles': nc})

    if not candidates:
        return dict(status, f=f_val, beta=beta_val,
                    note='no_stdout_found')

    # Best = earliest t_frag (prefer definite FRAG); fallback = smallest dt_min
    frag_cands = [c for c in candidates if c['t_frag'] is not None]
    if frag_cands:
        best = min(frag_cands, key=lambda c: c['t_frag'])
        all_dt_min = min((c['dt_min'] for c in candidates if c['dt_min'] is not None), default=None)
        new_status = dict(status)
        new_status.update({
            'outcome': 'FRAG',
            't_frag': best['t_frag'],
            'dt_min': all_dt_min,
            'reclassified': True,
            'source_file': best['file'],
            'f': f_val, 'beta': beta_val,
        })
        # write back
        with open(status_file, 'w') as fh:
            json.dump(new_status, fh, indent=2)
        return new_status
    else:
        # No crossing found — TIMEOUT; report dt_min
        all_dt_min = min((c['dt_min'] for c in candidates if c['dt_min'] is not None), default=None)
        t_fin = max((c['t_final'] for c in candidates if c['t_final'] is not None), default=None)
        new_status = dict(status)
        new_status.update({
            'stdout_dt_min': all_dt_min,
            'stdout_t_final': t_fin,
            'f': f_val, 'beta': beta_val,
        })
        if all_dt_min is not None and all_dt_min < 1e-4:
            new_status['outcome'] = 'TIMEOUT_NEAR_FRAG'
        return new_status

def main():
    print(f"\n{'='*70}")
    print(f"  BRIDGE_GRID Reclassifier v2 — dual-stdout t_frag recovery")
    print(f"  DT_THRESH = {DT_THRESH}")
    print(f"{'='*70}\n")

    sim_dirs = sorted([d for d in OUTPUT_BASE.iterdir()
                       if d.is_dir() and d.name.startswith("BRIDGE_GRID_")])
    print(f"Found {len(sim_dirs)} simulation directories\n")

    results = []
    for sim_dir in sim_dirs:
        r = reclassify_sim(sim_dir)
        results.append(r)

    frag    = [r for r in results if r.get('outcome') == 'FRAG']
    stable  = [r for r in results if r.get('outcome') == 'STABLE']
    near    = [r for r in results if r.get('outcome') == 'TIMEOUT_NEAR_FRAG']
    far     = [r for r in results if r.get('outcome') == 'TIMEOUT_FAR']
    other   = [r for r in results if r.get('outcome') not in
               ('FRAG','STABLE','TIMEOUT_NEAR_FRAG','TIMEOUT_FAR','MISSING_STATUS')]
    missing = [r for r in results if r.get('outcome') == 'MISSING_STATUS']

    print(f"{'='*70}")
    print(f"  RECLASSIFICATION SUMMARY (v2)")
    print(f"{'='*70}")
    print(f"  FRAG              : {len(frag)}")
    print(f"  STABLE            : {len(stable)}")
    print(f"  TIMEOUT_NEAR_FRAG : {len(near)}")
    print(f"  TIMEOUT_FAR       : {len(far)}")
    print(f"  Other/missing     : {len(other)+len(missing)}")
    print(f"{'='*70}\n")

    if frag:
        print("  FRAG DETECTIONS (sorted by f, beta):")
        print(f"  {'sim_id':<52} {'t_frag':>8}  {'dt_min':>12}  src")
        print("  " + "-"*82)
        for r in sorted(frag, key=lambda x: (x.get('f',0), x.get('beta',0),
                                              x.get('sim_id',''))):
            sid = r.get('sim_id','?')
            sid_short = sid.replace('BRIDGE_GRID_','').replace('_M1.0_theta90.0','')
            tf  = r.get('t_frag','?')
            dm  = r.get('dt_min')
            dm_s = f'{dm:.2e}' if dm else '?'
            src = r.get('source_file','?').replace('stdout','').replace('.txt','')
            rc  = '*' if r.get('reclassified') else ''
            print(f"  {sid_short:<52} {str(tf):>8}  {dm_s:>12}  {src}{rc}")

    for label, lst in [('TIMEOUT_NEAR_FRAG', near), ('TIMEOUT_FAR', far), ('OTHER', other+missing)]:
        if lst:
            print(f"\n  {label}:")
            for r in sorted(lst, key=lambda x: (x.get('f',0),x.get('beta',0))):
                sid = r.get('sim_id','?').replace('BRIDGE_GRID_','').replace('_M1.0_theta90.0','')
                dm  = r.get('stdout_dt_min') or r.get('dt_min')
                dm_s = f'{dm:.2e}' if dm else '?'
                print(f"    {sid}  dt_min={dm_s}")

    with open(RESULTS_FILE, 'w') as f:
        json.dump({'timestamp': datetime.utcnow().isoformat(),
                   'total': len(results),
                   'FRAG': len(frag), 'STABLE': len(stable),
                   'TIMEOUT_NEAR_FRAG': len(near), 'TIMEOUT_FAR': len(far),
                   'results': results}, f, indent=2)
    print(f"\nResults saved to: {RESULTS_FILE}")

if __name__ == '__main__':
    main()
