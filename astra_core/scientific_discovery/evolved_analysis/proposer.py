"""proposer.py — AlphaEvolve-style "creative generation".

Given a parent program (source + metrics) and inspirations (other good
programs), a Proposer produces a CHILD program source. Two backends:

  * LLMProposer     — asks Claude (via the configured gateway) for an improvement,
                      as either a search/replace DIFF or a full rewrite. This is
                      the real AlphaEvolve path.
  * GeneticProposer — offline fallback: mutates a structured spec and re-renders
                      source. Always available; fully reproducible.

apply_diff() parses the <<<SEARCH ... >>> <<<REPLACE ... >>> block format and
falls back to a fenced full-rewrite, then to the parent unchanged.
"""
from __future__ import annotations

import os
import re
import copy
from typing import List, Optional, Tuple

from .program import (
    render_source, validate_source, NAIVE_SPEC)

ALL_PAIRS = ["ug", "gr", "ri", "iz"]


# --------------------------------------------------------------------------- #
# diff parsing / application                                                   #
# --------------------------------------------------------------------------- #

_SEARCH_RE = re.compile(
    r"<<<\s*SEARCH\s*>>>(.*?)<<<\s*REPLACE\s*>>>(.*?)<<<\s*END\s*>>>",
    re.DOTALL)


def extract_python_block(text: str) -> Optional[str]:
    m = re.search(r"```python\s*(.*?)```", text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None


def apply_diff(parent_src: str, response: str, entry_point: str = "estimate_redshift") -> Tuple[str, str]:
    """Return (child_source, mode) where mode in
    {'diff','rewrite','unchanged'}. Never raises."""
    # 1) try SEARCH/REPLACE blocks
    blocks = _SEARCH_RE.findall(response)
    if blocks:
        out = parent_src
        for old, new in blocks:
            old_s, new_s = old.strip("\n"), new.strip("\n")
            if old_s and old_s in out:
                out = out.replace(old_s, new_s, 1)
            else:
                return parent_src, "unchanged"   # a block failed to match -> bail
        if validate_source(out, entry_point):
            return out, "diff"
    # 2) try a fenced full rewrite
    py = extract_python_block(response)
    if py and validate_source(py, entry_point):
        return py, "rewrite"
    # 3) last resort: maybe the whole response IS the function
    if validate_source(response, entry_point):
        return response.strip(), "rewrite"
    return parent_src, "unchanged"


# --------------------------------------------------------------------------- #
# proposer interface + backends                                               #
# --------------------------------------------------------------------------- #

class Proposer:
    name = "base"

    def propose(self, parent_source: str, parent_metrics: dict,
                parent_spec: Optional[dict], inspirations: List[str]
                ) -> Tuple[Optional[str], Optional[dict], dict]:
        """Return (child_source, child_spec, info).
        child_source None means 'could not propose'."""
        raise NotImplementedError


class LLMProposer(Proposer):
    name = "llm"

    def __init__(self, model: Optional[str] = None,
                 max_tokens: int = 1600, timeout: float = 90.0,
                 context_level: str = "rich",
                 task_system: Optional[str] = None,
                 entry_point: str = "estimate_redshift"):
        # Load the canonical gateway decoupled from astra_core/__init__ (evolved_analysis
        # runs with PYTHONPATH=astra_core/scientific_discovery). See _llm.py.
        from ._llm import gateway_module
        LLMGateway = gateway_module().LLMGateway
        self._gw = LLMGateway(
            model=(model or os.environ.get("ASTRA_PROPOSER_MODEL",
                                           "claude-sonnet-5-20250929")),
            max_tokens=max_tokens, timeout=timeout)
        self.client = self._gw.client
        self.model = self._gw.model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.context_level = context_level   # "minimal" | "rich"
        # Task generality (WP5): an alternative task system prompt + entry point.
        # Defaults preserve the photo-z behaviour exactly.
        self.task_system = task_system
        self.entry_point = entry_point
        self.n_calls = 0
        self.n_errors = 0

    BASE_SYSTEM = (
        "You are an expert astronomer and ML engineer. You improve a Python "
        "function `estimate_redshift(df_train, df_eval)` that predicts "
        "spectroscopic redshift (z_spec) of galaxies from SDSS u,g,r,i,z model "
        "magnitudes. It is graded on REAL held-out galaxies by two metrics: "
        "sigma_NMAD (robust scatter) and eta (outlier fraction, |dz|/(1+z)>0.15). "
        "Lower is better.\n"
        "HARD RULES:\n"
        "- Keep the EXACT signature: def estimate_redshift(df_train, df_eval)\n"
        "- df_train has columns u,g,r,i,z AND z_spec. df_eval has u,g,r,i,z.\n"
        "- Return a 1-D numpy array of predictions for df_eval rows (same order).\n"
        "- You may import ONLY: numpy, scipy, sklearn, pandas (already available).\n"
        "- No file I/O, no network, no plotting, no global side effects.\n"
        "- Be correct and self-contained.\n"
        "RESPOND WITH EITHER:\n"
        "  (a) one or more diff blocks (use this exact format):\n"
        "<<<SEARCH>>>\nexact existing code to replace\n<<<REPLACE>>>\nnew code\n<<<END>>>\n"
        "  (b) a single complete rewritten function in one ```python``` block.\n"
        "Prefer small targeted diffs. Output ONLY the diff or code, no explanation."
    )

    # keep SYSTEM alias so any external refs still work
    SYSTEM = BASE_SYSTEM

    def _render_diagnostics(self, m: dict) -> str:
        if not m:
            return "(no diagnostics available)"
        if "balanced_accuracy" in m:           # classification task (WP5)
            r = {k: m[k] for k in ("recall_STAR", "recall_GALAXY", "recall_QSO")
                 if k in m}
            parts = " ".join(f"{k.split('_')[1]}:{v:.2f}" for k, v in r.items())
            return (f"balanced_accuracy={m['balanced_accuracy']:.3f}  "
                    f"accuracy={m.get('accuracy',0):.3f}  per-class recall [{parts}]")
        if "sigma_nmad" not in m:
            return "(no diagnostics available)"
        lines = [f"sigma_NMAD={m['sigma_nmad']:.4f}  eta={m['eta']:.3f}  "
                 f"bias={m.get('bias', 0):+.4f}"]
        prof = m.get("profile") or []
        if prof:
            parts = [f"z~{b['z']}: med_dz={b['med_dz']:+.4f} (n={b['n']})"
                     for b in prof]
            lines.append("Residual profile by redshift bin: " + " | ".join(parts))
        return "\n".join(lines)

    def propose(self, parent_source, parent_metrics, parent_spec, inspirations,
                hints=None, context_level=None):
        """context_level: 'minimal' (parent source only) or 'rich' (source +
        rendered diagnostics + inspirations). hints: extra strategy lines
        appended to the system prompt (meta-prompt co-evolution)."""
        level = context_level or self.context_level
        system = self.task_system if self.task_system else self.BASE_SYSTEM
        if hints:
            system += "\n\nAdditional strategy hints to follow:\n- " + \
                      "\n- ".join(hints)
        msg = []
        if level == "minimal":
            msg.append(f"Current program:\n```python\n{parent_source}\n```")
        else:
            msg.append("Current program and its diagnostics on real held-out "
                       f"galaxies:\n{self._render_diagnostics(parent_metrics)}\n"
                       f"```python\n{parent_source}\n```")
            if inspirations:
                joined = "\n\n---\n\n".join(inspirations)
                msg.append("Inspirations (other, diverse approaches — borrow ideas):\n"
                           f"```python\n{joined}\n```")
        msg.append("Propose an improvement that lowers sigma_NMAD and eta on real "
                   "held-out data. Keep it correct.")
        try:
            self.n_calls += 1
            r = self.client.messages.create(
                model=self.model, max_tokens=self.max_tokens,
                system=system, messages=[{"role": "user",
                                          "content": "\n\n".join(msg)}])
            text = "".join(b.text for b in r.content if hasattr(b, "text"))
            child, mode = apply_diff(parent_source, text, self.entry_point)
            return child, None, {"mode": mode, "raw_len": len(text),
                                 "model": self.model,
                                 "in": getattr(r.usage, "input_tokens", 0),
                                 "out": getattr(r.usage, "output_tokens", 0)}
        except Exception as e:
            self.n_errors += 1
            return None, None, {"error": f"{type(e).__name__}: {str(e)[:120]}",
                                "model": self.model}


class GeneticProposer(Proposer):
    """Offline fallback. Mutates a structured spec and re-renders source."""
    name = "genetic"

    def __init__(self, seed=0):
        import numpy as np
        self.rng = np.random.default_rng(seed)
        self.n_calls = 0

    def _mutate_spec(self, spec):
        s = copy.deepcopy(spec)
        move = self.rng.choice(["color", "model", "scale", "degree", "alpha",
                                "trees", "depth", "include_r"])
        if move == "color":
            cur = list(s["color_pairs"])
            if cur and self.rng.random() < 0.5:
                del cur[self.rng.integers(0, len(cur))]
            else:
                missing = [p for p in ALL_PAIRS if p not in cur]
                if missing:
                    cur.append(str(self.rng.choice(missing)))
            s["color_pairs"] = cur
        elif move == "model":
            s["model"] = str(self.rng.choice(["linear", "ridge", "rf"]))
        elif move == "scale":
            s["scale"] = str(self.rng.choice(["none", "standard", "robust"]))
        elif move == "degree":
            s["degree"] = int(self.rng.choice([1, 2, 3]))
        elif move == "alpha":
            s["alpha"] = float(10 ** self.rng.uniform(-3, 3))
        elif move == "trees":
            s["rf_trees"] = int(self.rng.integers(20, 201))
        elif move == "depth":
            s["rf_depth"] = int(self.rng.integers(3, 16))
        elif move == "include_r":
            s["include_r"] = not bool(s.get("include_r", False))
        # guarantee >=1 feature
        if not s["color_pairs"] and not s.get("include_r"):
            s["include_r"] = True
        return s

    def propose(self, parent_source, parent_metrics, parent_spec, inspirations):
        self.n_calls += 1
        spec = parent_spec if parent_spec else copy.deepcopy(NAIVE_SPEC)
        child_spec = self._mutate_spec(spec)
        return render_source(child_spec), child_spec, {"mode": "genetic"}
