"""evaluator.py — REAL leapcore FitnessEvaluator that grades code on real data.

Subclasses astra_core.intelligence.leapcore_evolution.FitnessEvaluator (loaded
by file path in leapcore.py). Each Chromosome carries its program source in
``chrom.metadata['source']``. evaluate() runs that source in an isolated child
process on REAL SDSS data and returns a machine-graded scalar:

    fitness = -(sigma_NMAD + 3 * eta)        (higher = better; maximised)

Bad / hanging / crashing code is contained by the subprocess + hard timeout and
scores -inf, never crashing the loop.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from .leapcore import FitnessEvaluator

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER = "evolved_analysis.eval_worker"   # run as: python -m <WORKER> ...
NEG_INF = -1e9


class RealDataProgramEvaluator(FitnessEvaluator):
    """Grades a Chromosome's ``metadata['source']`` on real held-out data."""

    def __init__(self, seed: int = 42, timeout: float = 60.0,
                 python: str | None = None):
        self.seed = seed
        self.timeout = timeout
        self.python = python or sys.executable
        self.n_calls = 0
        self.n_failed = 0

    def evaluate(self, chrom) -> float:
        """Required FitnessEvaluator implementation. Writes fitness + metrics
        onto the chromosome and returns the scalar."""
        self.n_calls += 1
        src = (chrom.metadata or {}).get("source", "")
        m = self._run_subprocess(src, split="eval")
        chrom.fitness = -(m["sigma_nmad"] + 3.0 * m["eta"]) if "error" not in m else NEG_INF
        chrom.metadata = dict(chrom.metadata or {})
        chrom.metadata["metrics"] = m
        if "error" in m:
            self.n_failed += 1
        return chrom.fitness

    def evaluate_split(self, src: str, split: str) -> dict:
        """Score an arbitrary source string on a named split (for final TEST)."""
        return self._run_subprocess(src, split=split)

    # ------------------------------------------------------------------ #
    def _run_subprocess(self, src: str, split: str) -> dict:
        if not src or "def estimate_redshift" not in src:
            return {"sigma_nmad": 9.99, "eta": 1.0, "error": "no estimate_redshift"}
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False,
                                         dir=str(Path.cwd())) as tf:
            tf.write(src)
            tf.flush()
            src_path = tf.name
        try:
            env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
            proc = subprocess.run(
                [self.python, "-m", WORKER, src_path, str(self.seed), split],
                capture_output=True, text=True, timeout=self.timeout,
                cwd=str(REPO_ROOT), env=env)
        except subprocess.TimeoutExpired:
            return {"sigma_nmad": 9.99, "eta": 1.0, "error": "timeout"}
        except Exception as e:
            return {"sigma_nmad": 9.99, "eta": 1.0,
                    "error": f"spawn:{type(e).__name__}:{str(e)[:80]}"}
        finally:
            try:
                Path(src_path).unlink()
            except OSError:
                pass
        out = proc.stdout.strip().splitlines()
        if not out:
            return {"sigma_nmad": 9.99, "eta": 1.0,
                    "error": (proc.stderr.strip()[:160] or "no stdout")}
        try:
            return json.loads(out[-1])
        except json.JSONDecodeError:
            return {"sigma_nmad": 9.99, "eta": 1.0,
                    "error": f"unparseable: {out[-1][:120]}"}
