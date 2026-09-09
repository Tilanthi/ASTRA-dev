#!/usr/bin/env python3
"""heat68c_completion_sibling.py -- machine-generate the MISSING TAIL of
heat68c_sigma_gt1_delta_descent.out from the committed JSON, in the runner's
exact print format.

WHY: the run's stdout was orphaned from the path on 2026-09-06 22:55 (the path
file -- 18 lines, through 'D=0.001 t=5' -- stopped receiving writes while the
process ran ~99% CPU for 2.4 more days and the long-lived `tail -f` readers on
the ORIGINAL inode did receive the final lines; the monitors fired on them).
The JSON was written at exit to the correct path and is complete/authoritative.
Nothing below is hand-typed: every number is read from the JSON and formatted
with the runner's own format specifiers (#149: transcription machine-derived).
Cross-check: the t=20 line must reproduce, character for character, the line
the monitor witnessed (quoted in m1-L204 §4b).
"""
import json

HERE = "/Users/gjw255/astrodata/SWARM/ASTRA-dev-main/Riemann/experiments/orchestrator/"
out = json.load(open(HERE + "heat68c_sigma_gt1_delta_descent.json"))

WITNESS_T20 = ("D=0.001 (n=1000, |D|=4e+06) t=20: scale=1.973e+18 min|z2|=1.818e+06 "
               "at sigma=1.05  local-minima=0")

lines = []
for l in out["lines"]:
    if l["D"] == "0.001" and l["t"] in (10, 15, 20):
        lines.append("D=%s (n=%d, |D|=%s) t=%2d: scale=%.3e min|z2|=%.3e at sigma=%.2f"
                     "  local-minima=%d"
                     % (l["D"], l["n_eff"], "%.0e" % abs(l["disc_eff"]), l["t"],
                        l["scale"], l["vmin"], l["argmin_sigma"], len(l["cands"])))

assert lines[-1] == WITNESS_T20, "t=20 line does not reproduce the monitor-witnessed text:\n%r\n%r" % (lines[-1], WITNESS_T20)
lines.append("")
lines.append("OUTCOME (a): no candidate below threshold %s — Stark-consistent "
             "no-evidence to |D|<=4e6 at t<=20." % "0.001")
lines.append("done in %ds; json written" % round(out["elapsed_s"]))

hdr = (
    "# heat68c stdout-tail completion -- MACHINE-GENERATED 2026-09-09 from\n"
    "# heat68c_sigma_gt1_delta_descent.json (committed, complete, authoritative).\n"
    "# The .out path file ends at 'D=0.001 t=5' (mtime 2026-09-06 22:55): the run's\n"
    "# stdout was orphaned from the path after that write -- the process ran 2.4 more\n"
    "# days and its final lines reached only the tail -f readers holding the original\n"
    "# inode (register #190, m1-L204 §4b). The three lines below are regenerated with\n"
    "# the runner's own format specifiers; the t=20 line is asserted equal to the\n"
    "# monitor-witnessed text. The OUTCOME/done lines are regenerated with the same\n"
    "# literals the runner prints. Generator: heat68c_completion_sibling.py.\n")
open(HERE + "heat68c_sigma_gt1_delta_descent.out_completion.txt", "w").write(
    hdr + "\n".join(lines) + "\n")
print("wrote completion sibling; t=20 line == monitor-witnessed text: OK")
for x in lines:
    print("  | " + x)
