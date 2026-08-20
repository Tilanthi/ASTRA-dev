#!/usr/bin/env python3
"""run_noise_floor.py — measure the novelty judge's own verdict noise.

The 2026-08-20 cache calibration found near-identical claims agree only ~55%
of the time, but that conflates claim differences with judge stochasticity.
This script isolates the judge: re-run the SAME (claim, cached papers) pairs
repeatedly through the judge and measure how often the verdict flips. That
flip rate is the empirical noise floor — candidates whose novelty margins sit
inside it are not distinguishable, which feeds dedup and threshold policy.

Egent (arXiv 2512.01270) called the same-model repeatability experiment the
missing measurement in its own reproducibility study; this is ASTRA's.

Usage:
    python3 -m astra_core.scientific_discovery.evolved_analysis.run_noise_floor \
        [--sample 20] [--repeats 3]

Optional: ASTRA_NOISE_MODEL=<model id> adds a second-tier column.

Output: ~/.astra_persistent/evolved_programs/noise_floor.jsonl
Cost: sample x repeats judge calls (no retrieval — papers come from cache).
"""
from __future__ import annotations

import argparse
import json
import logging
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from .novelty_gate import NoveltyResult, Paper, _judge_known, _load_cache

logger = logging.getLogger(__name__)

OUT_PATH = (Path.home() / ".astra_persistent" / "evolved_programs"
            / "noise_floor.jsonl")


def sample_entries(n: int, cache: dict = None, seed: int = 7):
    """Sample n judged cache entries (with their stored papers)."""
    if cache is None:
        cache = _load_cache()
    usable = [(k, e) for k, e in cache.items()
              if e.get("status") in ("known", "novel") and e.get("retrieved")]
    if not usable:
        return []
    random.seed(seed)
    return random.sample(usable, min(n, len(usable)))


def run_noise_check(sample_size: int = 20, repeats: int = 3,
                    judge=None, out_path: Path = None) -> dict:
    """Re-judge each sampled claim ``repeats`` times; return the flip stats.

    ``judge`` overrides _judge_known for testing.
    """
    judge = judge or _judge_known
    entries = sample_entries(sample_size)
    flips = 0
    total = 0
    judged = 0
    confs = []
    for _, e in entries:
        papers = [Paper(source=p.get("source", "arxiv"),
                        title=p.get("title", ""),
                        abstract=p.get("abstract", ""),
                        identifier=p.get("identifier", ""),
                        year=p.get("year")) for p in e["retrieved"]]
        verdicts = []
        for _ in range(repeats):
            known, _, label, _, conf = judge(e["claim"], papers)
            if label:  # judge succeeded
                verdicts.append(bool(known))
                if conf is not None:
                    confs.append(float(conf))
        if len(verdicts) >= 2:
            judged += 1
            total += len(verdicts)
            flips += sum(1 for v in verdicts[1:] if v != verdicts[0])
    result = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "n_claims": judged,
        "repeats": repeats,
        "repeat_judgements": total,
        "flip_rate": round(flips / total, 4) if total else None,
        "mean_confidence": round(sum(confs) / len(confs), 4) if confs else None,
    }
    path = out_path or OUT_PATH
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a") as f:
            f.write(json.dumps(result) + "\n")
    except Exception as ex:
        logger.warning("[noise-floor] write failed: %s", ex)
    return result


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sample", type=int, default=20)
    ap.add_argument("--repeats", type=int, default=3)
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    res = run_noise_check(args.sample, args.repeats)
    print(json.dumps(res, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
