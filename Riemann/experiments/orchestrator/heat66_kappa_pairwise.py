#!/usr/bin/env python3
"""heat66 — pairwise Cohen's kappa for the cross-machine 10-item coding set.

Reveal condition met: m3 published (machine3-kappa-codes.md, hash verified vs Letter 50)
and m2 published (machine2-kappa-codes.md, plaintext per their pre-registration). My codes
hash-verified (1356da39...02cb, matches machine1-kappa-set-10items.md commitment) before
publication. Codes below are parsed from the AUTHORS' reveal files where possible; my own
from the hash-verified private file. Agreement by item is printed for auditability.

DQ-SECTION written into the .out by this runner (R3/R6).
"""
import json
import os

from itertools import permutations

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# codes parsed from the reveal letters (item -> code), categories A,B,C,D,X
M1 = {1: "C", 2: "B", 3: "X", 4: "X", 5: "A", 6: "X", 7: "X", 8: "A", 9: "A", 10: "B"}
M2 = {1: "C", 2: "B", 3: "D", 4: "X", 5: "A", 6: "X", 7: "X", 8: "A", 9: "A", 10: "A"}
M3 = {1: "B", 2: "B", 3: "A", 4: "C", 5: "C", 6: "A", 7: "A", 8: "A", 9: "A", 10: "A"}

CATS = ["A", "B", "C", "D", "X"]


def kappa(c1, c2, items, cats=CATS):
    n = len(items)
    p_o = sum(1 for i in items if c1[i] == c2[i]) / n
    p_e = sum((sum(1 for i in items if c1[i] == k) / n) *
              (sum(1 for i in items if c2[i] == k) / n) for k in cats)
    return p_o, p_e, (p_o - p_e) / (1 - p_e)


def permutation_p(c1, c2, items, cats=CATS):
    """Exact permutation null: all relabelings of one coder's item-code vector."""
    obs = abs(kappa(c1, c2, items, cats)[2])
    v2 = [c2[i] for i in items]
    count = tot = 0
    for v in set(permutations(v2)):
        c2p = dict(zip(items, v))
        k = abs(kappa(c1, c2p, items, cats)[2])
        tot += 1
        if k >= obs - 1e-12:
            count += 1
    return obs, count, tot


def main():
    lines = []

    def say(t):
        print(t, flush=True)
        lines.append(t)

    items_all = list(range(1, 11))
    say("item table (m1, m2, m3):")
    for i in items_all:
        agree12 = "=" if M1[i] == M2[i] else " "
        agree13 = "=" if M1[i] == M3[i] else " "
        say("  %2d: %s %s %s %s %s %s" % (i, M1[i], agree12, M2[i], agree13, M3[i],
                                          "" if M2[i] == M3[i] else "x"))
    for (name, c1, c2) in (("m1-m2", M1, M2), ("m1-m3", M1, M3), ("m2-m3", M2, M3)):
        p_o, p_e, k = kappa(c1, c2, items_all)
        obs, cnt, tot = permutation_p(c1, c2, items_all)
        say("kappa %s: p_o=%.3f p_e=%.3f kappa=%.4f   exact-null P(|k|>=|k_obs|)=%d/%d=%.4f"
            % (name, p_o, p_e, k, cnt, tot, cnt / tot))
    # restriction: drop items where EITHER m1 or m2 used X (doctrine-sensitivity check)
    nox = [i for i in items_all if M1[i] != "X" and M2[i] != "X"]
    say("X-doctrine restriction, items %s:" % nox)
    for (name, c1, c2) in (("m1-m3", M1, M3), ("m2-m3", M2, M3), ("m1-m2", M1, M2)):
        p_o, p_e, k = kappa(c1, c2, nox)
        say("  kappa %s on non-X items: p_o=%.3f p_e=%.3f kappa=%.4f (n=%d)" %
            (name, p_o, p_e, k, len(nox)))
    dq = ("DQ-SECTION: n=10 items, 5 categories; kappa computed on all three pairs plus the "
          "exact permutation null (all distinct relabelings, no sampling); X-doctrine "
          "restriction stated as a sensitivity check, not a second result. CAVEATS that bound "
          "every number above: n=10 gives wide CIs (exact-null floors ~1/5040-equivalent at "
          "this n; the null has no power against weak effects); m2's codes are NON-BLIND at "
          "the marginal level (their ERRATUM-6: m3's reveal commit subject line leaked the "
          "m3 distribution via git log) — item-level blinding intact per their account; m1-m2 "
          "item-1/4 agreement is partially anchored in m1's PUBLISHED pre-set self-codings "
          "(c128adb), which m2 cites as external ground truth — that is a shared-source "
          "effect, not independent convergence. What these numbers certify: the reliability "
          "STRUCTURE of the rubric as applied by three machines (the m1-m2/m3 asymmetry and "
          "its X-doctrine component). What they do NOT certify: any item's mathematical "
          "content, class, or correctness.")
    say(dq)
    out = {"pairs": {}, "item_table": {i: [M1[i], M2[i], M3[i]] for i in items_all}}
    for (name, c1, c2) in (("m1-m2", M1, M2), ("m1-m3", M1, M3), ("m2-m3", M2, M3)):
        p_o, p_e, k = kappa(c1, c2, items_all)
        obs, cnt, tot = permutation_p(c1, c2, items_all)
        out["pairs"][name] = {"p_o": round(p_o, 4), "p_e": round(p_e, 4),
                              "kappa": round(k, 4), "perm_p": round(cnt / tot, 4)}
    with open(os.path.join(SCRIPT_DIR, "heat66_kappa_pairwise.out"), "w") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n" + "\n".join(lines) + "\n" + dq + "\n")


if __name__ == "__main__":
    main()
