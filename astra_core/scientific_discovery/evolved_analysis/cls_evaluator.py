"""cls_evaluator.py — leapcore FitnessEvaluator for the classification task.

Runs a candidate classify_object program in an isolated subprocess on REAL SDSS
data; fitness = balanced_accuracy (higher = better; maximised). Bad code scores
-1 (never crashes the loop). Mirrors RealDataProgramEvaluator's subprocess design.
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
WORKER = "evolved_analysis.cls_eval_worker"


class ClsEvaluator(FitnessEvaluator):
    def __init__(self, seed: int = 42, timeout: float = 90.0, python: str | None = None):
        self.seed = seed
        self.timeout = timeout
        self.python = python or sys.executable
        self.n_calls = 0
        self.n_failed = 0

    def evaluate(self, chrom) -> float:
        self.n_calls += 1
        m = self._run(chrom.metadata.get("source", ""), "eval")
        chrom.fitness = m["balanced_accuracy"] if "error" not in m else -1.0
        chrom.metadata = dict(chrom.metadata or {})
        chrom.metadata["metrics"] = m
        if "error" in m:
            self.n_failed += 1
        return chrom.fitness

    def evaluate_split(self, src: str, split: str) -> dict:
        return self._run(src, split)

    def _run(self, src: str, split: str) -> dict:
        if not src or "def classify_object" not in src:
            return {"balanced_accuracy": -1.0, "error": "no classify_object"}
        with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as tf:
            tf.write(src); tf.flush(); sp = tf.name
        try:
            env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
            p = subprocess.run([self.python, "-m", WORKER, sp, str(self.seed), split],
                               capture_output=True, text=True, timeout=self.timeout,
                               cwd=str(REPO_ROOT), env=env)
        except subprocess.TimeoutExpired:
            return {"balanced_accuracy": -1.0, "error": "timeout"}
        except Exception as e:
            return {"balanced_accuracy": -1.0, "error": f"spawn:{type(e).__name__}"}
        finally:
            try: Path(sp).unlink()
            except OSError: pass
        out = p.stdout.strip().splitlines()
        if not out:
            return {"balanced_accuracy": -1.0, "error": p.stderr.strip()[:160]}
        try:
            return json.loads(out[-1])
        except json.JSONDecodeError:
            return {"balanced_accuracy": -1.0, "error": f"unparseable: {out[-1][:120]}"}
