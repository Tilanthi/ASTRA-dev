#!/usr/bin/env python3
"""
AUDIT CAMPAIGN RUNNER — Ray-distributed Athena++ execution.
Runs all configs from manifest.json on a 220-CPU cluster via Ray.

Usage:
  python3 run_audit_campaign.py --athena_path /path/to/athena++ [--max_concurrent 13]

The athena++ binary must be compiled with the filament problem generator.
Set --max_concurrent based on available CPUs (220 CPUs / 16 cores-per-sim ≈ 13).
"""
import ray, json, time, argparse, subprocess, os
from pathlib import Path

@ray.remote(num_cpus=16)
def run_one_sim(config_path, athena_path, timeout_s=21600):
    """Run a single Athena++ simulation."""
    import subprocess, time, json
    pid = Path(config_path).stem
    t0 = time.time()
    try:
        result = subprocess.run(
            [athena_path, "-i", str(config_path)],
            capture_output=True, text=True, timeout=timeout_s,
            cwd=str(Path(config_path).parent))
        elapsed = time.time() - t0
        status = "OK" if result.returncode == 0 else f"FAIL({result.returncode})"
        stderr_tail = result.stderr[-500:] if result.stderr else ""
        return {"pid": pid, "config": str(config_path), "status": status,
                "wall_s": round(elapsed, 1), "returncode": result.returncode,
                "stderr_tail": stderr_tail}
    except subprocess.TimeoutExpired:
        return {"pid": pid, "config": str(config_path), "status": "TIMEOUT",
                "wall_s": timeout_s, "returncode": -1}
    except Exception as e:
        return {"pid": pid, "config": str(config_path), "status": f"ERROR:{e}",
                "wall_s": round(time.time()-t0, 1), "returncode": -2}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--athena_path", default="./athena++", help="Path to compiled Athena++ binary")
    ap.add_argument("--config_dir", default="configs", help="Config directory")
    ap.add_argument("--max_concurrent", type=int, default=13, help="Max concurrent sims (220 CPU / 16 = 13)")
    ap.add_argument("--timeout", type=int, default=21600, help="Per-sim timeout (seconds)")
    args = ap.parse_args()

    # Load manifest
    manifest = json.loads(Path(f"{args.config_dir}/manifest.json").read_text())
    all_configs = []
    for camp in manifest["campaigns"].values():
        all_configs.extend(camp["configs"])

    print(f"{'='*60}")
    print(f"AUDIT CAMPAIGN RUNNER")
    print(f"{'='*60}")
    print(f"Athena++ binary: {args.athena_path}")
    print(f"Total simulations: {len(all_configs)}")
    print(f"Max concurrent: {args.max_concurrent}")
    print(f"Estimated wall-time: {len(all_configs)/args.max_concurrent * 1.5:.0f} hours")
    print()

    # Verify athena binary exists
    if not Path(args.athena_path).exists():
        print(f"ERROR: Athena++ binary not found at {args.athena_path}")
        print("Compile Athena++ with the filament problem generator first.")
        return

    # Init Ray
    ray.init(num_cpus=220)
    print(f"Ray initialised: {ray.available_resources()}")

    # Launch sims in batches
    results = []
    pending = []
    config_iter = iter(all_configs)
    done = 0

    # Initial fill
    for _ in range(args.max_concurrent):
        try:
            cfg = next(config_iter)
            pending.append(run_one_sim.remote(cfg, args.athena_path, args.timeout))
        except StopIteration:
            break

    while pending:
        finished, pending = ray.wait(pending, num_returns=1)
        result = ray.get(finished[0])
        results.append(result)
        done += 1
        status = result["status"]
        print(f"  [{done}/{len(all_configs)}] {result['pid']}: {status} ({result['wall_s']:.0f}s)")

        # Launch next
        try:
            cfg = next(config_iter)
            pending.append(run_one_sim.remote(cfg, args.athena_path, args.timeout))
        except StopIteration:
            pass

    # Save results
    output_file = Path("audit_campaign_results.json")
    output_file.write_text(json.dumps(results, indent=2))
    print(f"\n{'='*60}")
    print(f"CAMPAIGN COMPLETE: {len(results)} simulations")
    ok = sum(1 for r in results if r["status"] == "OK")
    print(f"  OK: {ok}, FAIL/TIMEOUT: {len(results)-ok}")
    print(f"  Results: {output_file}")
    print(f"{'='*60}")
    ray.shutdown()

if __name__ == "__main__":
    main()
