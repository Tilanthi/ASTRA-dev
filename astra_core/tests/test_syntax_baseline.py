"""CI guard against NEW truncated / syntax-broken source files in astra_core.

A 2026-07-17 external review found ~44 source files truncated mid-expression in
astra_core (a fabrication-adjacent failure mode from an automated edit session).
Those pre-existing broken files are baselined in ``known_broken_syntax.txt``: they
have been broken since the earliest reachable git history, so no intact copy exists
to restore -> they are NOT guess-repaired (guessing the missing content would be the
exact fabrication failure mode the discovery pipeline is policed against).

This test fails if:
  * any NEW file is broken beyond the baseline (blocks new breakage), OR
  * a baseline file is fixed (prompts an honest baseline update).

Nothing invented, nothing hidden. Run: python3 -m pytest astra_core/tests/test_syntax_baseline.py
"""
import pathlib
import py_compile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parents[1]                 # repo root
PKG = REPO / "astra_core"
BASELINE = HERE / "known_broken_syntax.txt"


def _broken_files() -> set:
    broken = set()
    for p in PKG.rglob("*.py"):
        try:
            py_compile.compile(str(p), doraise=True)
        except Exception:
            broken.add(str(p.relative_to(REPO)).replace("\\", "/"))
    return broken


def _baseline() -> set:
    return {ln.strip() for ln in BASELINE.read_text().splitlines() if ln.strip()}


def test_no_new_syntax_errors_beyond_baseline():
    live, base = _broken_files(), _baseline()
    new_breakage = sorted(live - base)
    fixed = sorted(base - live)
    msgs = []
    if new_breakage:
        msgs.append("NEW broken files beyond baseline -- fix these (CI blocks new breakage):\n  "
                    + "\n  ".join(new_breakage))
    if fixed:
        msgs.append("Baseline files now compile -- update known_broken_syntax.txt:\n  "
                    + "\n  ".join(fixed))
    assert not msgs, "\n".join(msgs)
