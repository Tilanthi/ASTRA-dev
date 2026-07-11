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
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from .leapcore import FitnessEvaluator

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKER = "evolved_analysis.eval_worker"   # run as: python -m <WORKER> ...
NEG_INF = -1e9

# Defence-in-depth layer 3: macOS sandbox-exec. When available, the worker is
# launched under this profile so candidate code cannot reach the network or
# write outside /tmp — on top of the AST gate (safety.py) and rlimits
# (eval_worker.py). Detected once at import; None / missing-profile => fall back
# to the plain subprocess (AST gate + rlimits still apply).
SANDBOX_EXEC = shutil.which("sandbox-exec")
PROFILE_PATH = Path(__file__).resolve().parent / "astra_worker.sb"


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
            cmd = [self.python, "-m", WORKER, src_path, str(self.seed), split]
            # If sandbox-exec and the profile are available, wrap the worker so
            # untrusted candidate code is confined to no-network / temp-writes-
            # only. Otherwise fall back to the plain command; the AST gate and
            # rlimit caps still apply either way. NOTE: -f (profile file) is used
            # rather than -p (profile text) since PROFILE_PATH is a file path.
            if SANDBOX_EXEC and PROFILE_PATH.is_file():
                cmd = [SANDBOX_EXEC, "-f", str(PROFILE_PATH),
                       self.python, "-m", WORKER, src_path, str(self.seed), split]
            proc = subprocess.run(
                cmd,
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
