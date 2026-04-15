# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
ASTRA Live — Export Formats (Phase 11.2)
Export discoveries, hypotheses, and provenance in JSON, CSV, and LaTeX formats.
"""

import csv
import io
import json
import re
import time
from dataclasses import asdict
from typing import Optional


# Characters that need escaping in LaTeX
_LATEX_SPECIAL = re.compile(r"([&%$#_{}~^\\])")
_LATEX_REPLACEMENTS = {
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
    "\\": r"\textbackslash{}",
}


def _escape_latex(text: str) -> str:
    """Escape special LaTeX characters in *text*."""
    if not isinstance(text, str):
        text = str(text)
    # Process backslash first to avoid double-escaping
    text = text.replace("\\", r"\textbackslash{}")
    for char in "&%$#_{}":
        text = text.replace(char, _LATEX_REPLACEMENTS[char])
    text = text.replace("~", _LATEX_REPLACEMENTS["~"])
    text = text.replace("^", _LATEX_REPLACEMENTS["^"])
    return text


def _discovery_to_dict(rec) -> dict:
    """Convert a DiscoveryRecord (dataclass) to a plain dict."""
    if hasattr(rec, "__dataclass_fields__"):
        return asdict(rec)
    if hasattr(rec, "__dict__"):
        return dict(rec.__dict__)
    return dict(rec)


def _hypothesis_to_dict(h) -> dict:
    """Convert a Hypothesis dataclass to a JSON-safe dict."""
    try:
        d = asdict(h)
    except Exception:
        d = dict(h.__dict__) if hasattr(h, "__dict__") else {}
    # Phase enum → string
    if "phase" in d and hasattr(d["phase"], "value"):
        d["phase"] = d["phase"].value
    elif "phase" in d and not isinstance(d["phase"], str):
        d["phase"] = str(d["phase"])
    return d


def _provenance_to_dict(p) -> dict:
    """Convert a provenance record to a plain dict."""
    if hasattr(p, "__dataclass_fields__"):
        return asdict(p)
    if hasattr(p, "__dict__"):
        return dict(p.__dict__)
    if isinstance(p, dict):
        return p
    return {"raw": str(p)}


class ASTRAExporter:
    """Export ASTRA discoveries, hypotheses and provenance in multiple formats."""

    def __init__(self, engine):
        self.engine = engine

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_discoveries(self):
        """Return list of DiscoveryRecord objects (or empty list)."""
        mem = getattr(self.engine, "discovery_memory", None)
        if mem is None:
            return []
        return list(getattr(mem, "discoveries", []))

    def _get_provenance_for(self, discovery_id: str) -> list:
        """Return provenance records for a specific discovery."""
        tracker = getattr(self.engine, "provenance_tracker", None)
        if tracker is None:
            return []
        try:
            recs = tracker.get_by_discovery(discovery_id)
            return [_provenance_to_dict(r) for r in recs] if recs else []
        except Exception:
            return []

    def _get_all_provenance(self) -> list:
        """Return all provenance records."""
        tracker = getattr(self.engine, "provenance_tracker", None)
        if tracker is None:
            return []
        try:
            recs = tracker.get_all()
            return [_provenance_to_dict(r) for r in recs] if recs else []
        except Exception:
            return []

    # ------------------------------------------------------------------
    # 1. JSON export of discoveries
    # ------------------------------------------------------------------

    def export_discoveries_json(self, filter_domain: Optional[str] = None) -> str:
        """Export all discoveries as a JSON array, with provenance attached.

        Parameters
        ----------
        filter_domain : str, optional
            If set, only include discoveries whose domain contains this
            substring (case-insensitive).

        Returns
        -------
        str
            Pretty-printed JSON array.
        """
        discoveries = self._get_discoveries()

        if filter_domain:
            needle = filter_domain.lower()
            discoveries = [
                d for d in discoveries
                if needle in getattr(d, "domain", "").lower()
            ]

        result = []
        for d in discoveries:
            entry = _discovery_to_dict(d)
            did = entry.get("id", "")
            entry["provenance"] = self._get_provenance_for(did)
            result.append(entry)

        return json.dumps(result, indent=2, default=str)

    # ------------------------------------------------------------------
    # 2. CSV export of discoveries
    # ------------------------------------------------------------------

    _CSV_COLUMNS = [
        "id", "timestamp", "cycle", "hypothesis_id", "domain",
        "finding_type", "variables", "statistic", "p_value",
        "description", "data_source", "strength", "effect_size",
    ]

    def export_discoveries_csv(self, filter_domain: Optional[str] = None) -> str:
        """Export discoveries as CSV.

        Parameters
        ----------
        filter_domain : str, optional
            Case-insensitive partial match on domain.

        Returns
        -------
        str
            CSV text with header row.
        """
        discoveries = self._get_discoveries()

        if filter_domain:
            needle = filter_domain.lower()
            discoveries = [
                d for d in discoveries
                if needle in getattr(d, "domain", "").lower()
            ]

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(self._CSV_COLUMNS)

        for d in discoveries:
            dd = _discovery_to_dict(d)
            row = []
            for col in self._CSV_COLUMNS:
                val = dd.get(col, "")
                # Flatten lists to semicolon-separated strings
                if isinstance(val, (list, tuple)):
                    val = "; ".join(str(v) for v in val)
                row.append(val)
            writer.writerow(row)

        return buf.getvalue()

    # ------------------------------------------------------------------
    # 3. LaTeX export of a single hypothesis
    # ------------------------------------------------------------------

    def export_hypothesis_latex(self, hypothesis_id: str) -> Optional[str]:
        """Generate a LaTeX section for one hypothesis.

        Parameters
        ----------
        hypothesis_id : str
            ID of the hypothesis to export.

        Returns
        -------
        str or None
            LaTeX source text, or ``None`` if the hypothesis is not found.
        """
        store = getattr(self.engine, "store", None)
        if store is None:
            return None

        h = store.get(hypothesis_id)
        if h is None:
            return None

        name = _escape_latex(getattr(h, "name", hypothesis_id))
        desc = _escape_latex(getattr(h, "description", ""))
        confidence = getattr(h, "confidence", 0.0)
        phase = getattr(h, "phase", "UNKNOWN")
        phase_str = phase.value if hasattr(phase, "value") else str(phase)
        phase_str = _escape_latex(phase_str)

        lines = [
            r"\subsection{" + name + "}",
            "",
            r"\textbf{Description:} " + desc,
            "",
            r"\textbf{Confidence:} " + f"{confidence:.4f}",
            "",
            r"\textbf{Phase:} " + phase_str,
            "",
        ]

        # Test results table
        test_results = getattr(h, "test_results", []) or []
        if test_results:
            lines.append(r"\subsubsection*{Test Results}")
            lines.append("")
            # Determine column keys from first result
            if test_results:
                keys = list(test_results[0].keys()) if isinstance(test_results[0], dict) else []
            if keys:
                col_spec = "|".join(["l"] * len(keys))
                header = " & ".join(_escape_latex(k) for k in keys) + r" \\"
                lines.append(r"\begin{tabular}{" + col_spec + "}")
                lines.append(r"\hline")
                lines.append(header)
                lines.append(r"\hline")
                for tr in test_results:
                    if isinstance(tr, dict):
                        cells = " & ".join(
                            _escape_latex(str(tr.get(k, ""))) for k in keys
                        )
                    else:
                        cells = _escape_latex(str(tr))
                    lines.append(cells + r" \\")
                lines.append(r"\hline")
                lines.append(r"\end{tabular}")
                lines.append("")

        # Provenance
        prov = self._get_provenance_for(hypothesis_id)
        # Also try discoveries linked to this hypothesis
        discoveries = self._get_discoveries()
        linked = [d for d in discoveries if getattr(d, "hypothesis_id", "") == hypothesis_id]

        if prov or linked:
            lines.append(r"\subsubsection*{Provenance}")
            lines.append("")
            if prov:
                lines.append(r"\begin{itemize}")
                for p in prov:
                    summary = _escape_latex(
                        p.get("description", p.get("action", str(p)))
                    )
                    lines.append(r"  \item " + summary)
                lines.append(r"\end{itemize}")
                lines.append("")
            if linked:
                lines.append(
                    r"\textbf{Linked discoveries:} "
                    + _escape_latex(", ".join(getattr(d, "id", "?") for d in linked))
                )
                lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 4. Full report JSON
    # ------------------------------------------------------------------

    def export_full_report_json(self) -> str:
        """Export a comprehensive JSON report of the entire engine state.

        Returns
        -------
        str
            Pretty-printed JSON with keys: hypotheses, discoveries,
            provenance, engine_state, export_timestamp, version.
        """
        # Hypotheses
        store = getattr(self.engine, "store", None)
        hypotheses = []
        if store is not None:
            for h in store.all():
                hypotheses.append(_hypothesis_to_dict(h))

        # Discoveries (with provenance each)
        discoveries = []
        for d in self._get_discoveries():
            entry = _discovery_to_dict(d)
            entry["provenance"] = self._get_provenance_for(entry.get("id", ""))
            discoveries.append(entry)

        # All provenance
        provenance = self._get_all_provenance()

        # Engine state
        engine_state = {}
        try:
            engine_state = self.engine.get_state()
        except Exception:
            pass

        report = {
            "version": "ASTRA-Live-Phase-11.2",
            "export_timestamp": time.time(),
            "hypotheses": hypotheses,
            "discoveries": discoveries,
            "provenance": provenance,
            "engine_state": engine_state,
        }

        return json.dumps(report, indent=2, default=str)
