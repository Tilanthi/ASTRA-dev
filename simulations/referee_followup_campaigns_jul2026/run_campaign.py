#!/usr/bin/env python3
"""Shared campaign runner with per-config MPI ranks and live CFL-collapse polling.

Adapted from the Jul 2026 audit runner. Discovers .athinput files, runs each
with mpirun -np <num_cores>, polls the .hst file every <poll> s, and stops a run
once the timestep stays at/below <dt_kill> for <kill_checks> consecutive polls
(i.e. radial-collapse runaway). For Campaign A set dt_kill low (e.g. 1e-6) so
the dense HDF5 snapshots captured up to that point cover the density-contrast
crossings (10/100/1000); for Campaign B a larger dt_kill (e.g. 2e-5) is fine.

Usage:
  python3 run_campaign.py --athena_path /path/to/athena \
      --config_dir configs/A_main_fgrid --max_concurrent 12 \
      --dt_kill 1e-6 --resultsout campaignA_results.json
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import subprocess
import time
from pathlib import Path


def nproc_for(cfg):
    s = Path(cfg).read_text()
    m = re.search(r'num_cores\s*=\s*(\d+)', s)
    return int(m.group(1)) if m else 16


def discover(config_dir):
    return [str(p) for p in sorted(Path(config_dir).glob('**/*.athinput'))]


def latest_dt(hst):
    """Return (t, dt) from the last numeric line of an Athena++ .hst file."""
    try:
        for line in reversed(Path(hst).read_text(errors='ignore').splitlines()):
            if line and not line.startswith('#'):
                p = line.split()
                if len(p) >= 2:
                    return float(p[0]), float(p[1])
    except Exception:
        pass
    return None, None


def stop(proc):
    try:
        proc.terminate()
    except Exception:
        pass
    time.sleep(3)
    if proc.poll() is None:
        try:
            proc.kill()
        except Exception:
            pass


def run_one(cfg, athena, root, timeout, dt_kill, kill_checks, poll):
    cfg = str(Path(cfg).resolve())
    pid = Path(cfg).stem
    nproc = nproc_for(cfg)
    for pat in [pid + '.hst', pid + '*.athdf', pid + '*.xdmf']:
        for f in Path(root).glob(pat):
            try:
                f.unlink()
            except Exception:
                pass
    cmd = ['mpirun', '-np', str(nproc), athena, '-i', cfg]
    env = os.environ.copy()
    env['OMP_NUM_THREADS'] = '1'
    env.setdefault('OMPI_MCA_btl_vader_single_copy_mechanism', 'none')
    t0 = time.time()
    hits = 0
    p = subprocess.Popen(cmd, cwd=root, env=env,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        while p.poll() is None:
            if time.time() - t0 > timeout:
                stop(p)
                return {'pid': pid, 'status': 'TIMEOUT',
                        'wall_s': round(time.time() - t0, 1),
                        'returncode': -1, 'nproc': nproc, 'config': cfg}
            t, dt = latest_dt(Path(root) / (pid + '.hst'))
            if dt is not None and dt <= dt_kill:
                hits += 1
                if hits >= kill_checks:
                    stop(p)
                    return {'pid': pid, 'status': 'COLLAPSE_EARLY',
                            'wall_s': round(time.time() - t0, 1),
                            'returncode': p.poll(), 'nproc': nproc, 'config': cfg,
                            'collapse_t': t, 'collapse_dt': dt, 'dt_kill': dt_kill}
            else:
                hits = 0
            time.sleep(poll)
    except Exception as e:
        stop(p)
        return {'pid': pid, 'status': f'ERROR:{e}',
                'wall_s': round(time.time() - t0, 1),
                'returncode': -2, 'nproc': nproc, 'config': cfg}
    rc = p.wait()
    out, err = p.communicate()
    return {'pid': pid, 'status': 'OK' if rc == 0 else f'FAIL({rc})',
            'wall_s': round(time.time() - t0, 1),
            'returncode': rc, 'nproc': nproc, 'config': cfg,
            'stdout_tail': (out or '')[-1000:],
            'stderr_tail': (err or '')[-1000:]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--athena_path', default='/home/fetch-agi/athena/bin/athena')
    ap.add_argument('--config_dir', default='configs')
    ap.add_argument('--max_concurrent', type=int, default=12)
    ap.add_argument('--timeout', type=int, default=21600)
    ap.add_argument('--dt_kill', type=float, default=1e-6)
    ap.add_argument('--kill_checks', type=int, default=3)
    ap.add_argument('--poll', type=float, default=20.0)
    ap.add_argument('--resultsout', default='campaign_results.json')
    a = ap.parse_args()
    root = str(Path.cwd().resolve())
    cs = discover(a.config_dir)
    print('=' * 60, flush=True)
    print('REFEREE FOLLOW-UP CAMPAIGN RUNNER', flush=True)
    print('=' * 60, flush=True)
    print(f'Root: {root}', flush=True)
    print(f'Config dir: {a.config_dir}  ({len(cs)} configs)', flush=True)
    print(f'Max concurrent: {a.max_concurrent}  dt_kill={a.dt_kill:g}  '
          f'poll={a.poll}s', flush=True)
    results = []
    with cf.ThreadPoolExecutor(max_workers=a.max_concurrent) as ex:
        futs = {ex.submit(run_one, c, a.athena_path, root, a.timeout,
                          a.dt_kill, a.kill_checks, a.poll): c for c in cs}
        for i, f in enumerate(cf.as_completed(futs), 1):
            r = f.result()
            results.append(r)
            print(f'[{i}/{len(cs)}] {r["pid"]}: {r["status"]} '
                  f'({r["wall_s"]}s)', flush=True)
            Path(a.resultsout + '.partial').write_text(json.dumps(results, indent=2))
    Path(a.resultsout).write_text(json.dumps(results, indent=2))
    from collections import Counter
    print('COMPLETE', len(results),
          dict(Counter(r['status'] for r in results)), flush=True)


if __name__ == '__main__':
    main()
