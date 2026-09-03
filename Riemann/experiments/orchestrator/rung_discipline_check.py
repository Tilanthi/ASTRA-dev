#!/usr/bin/env python3
"""Consensus R6 (m2's structural amendment): zero-compute rules get artifacts that are
MISSING when the rule does not fire. This is the no-judgement directory check.

Checks over this orchestrator directory:
  1. every *.out run log contains a DQ-SECTION (missing => red, listed by name);
  2. reset_slots/ contains at least one artifact (representation-reset slot output);
  3. prints counts only — 'N runs, M DQ sections' style; no judgement inside.

What it deliberately does NOT check (stated, not hidden): pre-registration letters live on
the exchange as hash-commits; pairing them with local scripts is recorded in NOTES and is
not mechanically checkable from here. The two checks above are the ones with no judgement.
Retrofit debt is reported, not retro-fixed: older .out files without a DQ section are listed
red on first run and the debt stands until those lanes next run.
"""
import glob
import os

HERE = os.path.dirname(os.path.abspath(__file__))

outs = sorted(glob.glob(os.path.join(HERE, "*.out")))
missing = [o for o in outs if "DQ-SECTION" not in open(o, errors="replace").read()]

reset_dir = os.path.join(HERE, "reset_slots")
resets = sorted(glob.glob(os.path.join(reset_dir, "*.md"))) if os.path.isdir(reset_dir) else []

print(f"runs (.out): {len(outs)}   with DQ-SECTION: {len(outs) - len(missing)}   MISSING: {len(missing)}")
for m in missing:
    print(f"  RED (no DQ-SECTION): {os.path.basename(m)}")
print(f"reset-slot artifacts: {len(resets)}")
for r in resets:
    print(f"  {os.path.basename(r)}")
print(f"DQ-SECTION red runs: {len(missing)}  -> any red run is a finding to adjudicate, not a silent pass")
