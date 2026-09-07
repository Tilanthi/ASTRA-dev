#!/usr/bin/env python3
"""STATUS LABEL: CERTIFIED-INPUT VALIDATOR (non-destructive; reads, never writes).

Validates manifest.json against the files on disk: every member and every sealed
input must hash to its recorded sha256. Repo roots are resolved from two anchor
paths (both named in the manifest). Exit 0 = all hashes match; exit 1 = any
mismatch, with the offending entries listed. Part of the m1 last-mile
identification bundle (robopol-style reference design: manifest + hash
validator + per-script status labels + non-destructive reproduction test).
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASTRA = os.path.abspath(os.path.join(HERE, "..", ".."))          # ASTRA-dev-main
EXCH = "/Users/gjw255/astrodata/SWARM/Riemann_exchange"          # exchange clone
REPOS = {"ASTRA-dev-main": ASTRA, "Riemann_exchange": EXCH}


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    man = json.load(open(os.path.join(HERE, "manifest.json")))
    bad, checked = [], 0
    for group in ("inputs", "members"):
        for key, entry in man[group].items():
            path = os.path.join(REPOS[entry["repo"]], entry["path"])
            if not os.path.exists(path):
                bad.append((group, key, entry["path"], "MISSING"))
                continue
            got = sha256(path)
            checked += 1
            if got != entry["sha256"]:
                bad.append((group, key, entry["path"], got))
    print("manifest %s: %d entries hashed, %d bad" % (man["bundle"], checked, len(bad)))
    for b in bad:
        print("  MISMATCH", b)
    if bad:
        sys.exit(1)
    print("ALL HASHES MATCH (members + sealed inputs; nothing was modified)")


if __name__ == "__main__":
    main()
