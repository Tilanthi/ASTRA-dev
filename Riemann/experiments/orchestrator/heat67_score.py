#!/usr/bin/env python3
"""heat67 scorer — applies prereg 7847b6c + the reporting plan committed at 114d3ba.

Reads heat67_zeta_rtable.out (runner-written JSON). Emits:
  REGISTERED outcome (a)/(b)/(c)/(d) — primary arm vs [0.346, 0.608], >=8/12 in range;
  POST-HOC reads (labeled): primary median vs L67 band [0.161,0.336]; vs combined
  17-point median 0.357551 (verified from m3's data files this session, L70-corrected);
  Kendall tau of R vs log t across primary windows with EXACT null (Mahonian DP on
  inversion counts, n=12), two-sided; W=8-vs-W=30 per-window direction table with the
  selected-pair confound flagged (d_pri != d_sec means different tightest pairs).
DQ-SECTION written by this scorer (R3/R6).
"""
import json
import math
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BAND_REG = (0.346, 0.608)      # L62 genus-2-4 non-degenerate (registered)
BAND_L67 = (0.161, 0.336)      # L67 genus-5-7 non-degenerate (post-hoc)
MED_COMB = 0.357551            # combined 17-point (verified from m3 files, L70)
ENV_ZETA = (0.03, 0.46)        # zeta envelope (m3 L62 framing)


def med(xs):
    s = sorted(xs)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def kendall_exact(rs, ts):
    """tau of rs vs ts with exact two-sided null via Mahonian DP (inversion counts)."""
    n = len(rs)
    idx = sorted(range(n), key=lambda i: ts[i])
    y = [rs[i] for i in idx]
    conc = disc = 0
    for i in range(n):
        for j in range(i + 1, n):
            if y[i] < y[j]: conc += 1
            elif y[i] > y[j]: disc += 1
    tau = (conc - disc) / (n * (n - 1) / 2)
    # null distribution of disc (= inversions) over all n! permutations
    maxk = n * (n - 1) // 2
    dp = [1] + [0] * maxk
    for m in range(1, n):
        nd = [0] * (maxk + 1)
        for k in range(maxk + 1):
            if dp[k]:
                for add in range(m + 1):
                    if k + add <= maxk:
                        nd[k + add] += dp[k]
        dp = nd
    tot = math.factorial(n)
    p_le = sum(dp[:disc + 1]) / tot
    p_ge = sum(dp[disc:]) / tot
    p_two = 2 * min(p_le, p_ge)
    return tau, disc, p_two


def main():
    lines = []

    def say(t):
        print(t, flush=True)
        lines.append(t)

    with open(os.path.join(SCRIPT_DIR, "heat67_zeta_rtable.out")) as fh:
        # runner appends its text log after the JSON object; take the JSON prefix only
        data = json.JSONDecoder().raw_decode(fh.read())[0]
    rows = data["rows"]
    pri = [r for r in rows if r["arm"] == "pri" and r["status"] == "OK"]
    sec = [r for r in rows if r["arm"] == "sec" and r["status"] == "OK"]
    say("primary rows OK: %d/12; secondary rows OK: %d/12; DQ: %s"
        % (len(pri), len(sec), data.get("dq") or "none"))
    for arm, rs in (("PRIMARY W=8", pri), ("SECONDARY W=30", sec)):
        if not rs:
            say("%s: no OK rows" % arm)
            continue
        Rs = [float(r["R"]) for r in rs]
        say("%s: median=%.6f min=%.4f max=%.4f  in-[0.346,0.608] %d/%d  "
            "in-[0.161,0.336] %d/%d  in-envelope[0.03,0.46] %d/%d"
            % (arm, med(Rs), min(Rs), max(Rs),
               sum(1 for x in Rs if BAND_REG[0] <= x <= BAND_REG[1]), len(Rs),
               sum(1 for x in Rs if BAND_L67[0] <= x <= BAND_L67[1]), len(Rs),
               sum(1 for x in Rs if ENV_ZETA[0] <= x <= ENV_ZETA[1]), len(Rs)))
    # REGISTERED outcome
    if not pri:
        say("REGISTERED OUTCOME (d): no scored primary rows.")
    else:
        m = med([float(r["R"]) for r in pri])
        inreg = sum(1 for r in pri if BAND_REG[0] <= float(r["R"]) <= BAND_REG[1])
        if BAND_REG[0] <= m <= BAND_REG[1] and inreg >= 8:
            say("REGISTERED OUTCOME (a): median %.4f inside registered band, %d/12 in "
                "range -> universality-in-range SURVIVES; synthesis letter follows." % (m, inreg))
        elif BAND_REG[0] <= m <= BAND_REG[1]:
            say("REGISTERED OUTCOME (b): median %.4f inside, only %d/12 in range -> "
                "AMBIGUOUS; higher-genus lane is tiebreaker (with L68's caveat on what "
                "the tiebreak means now)." % (m, inreg))
        else:
            say("REGISTERED OUTCOME (c): median %.4f OUTSIDE registered band [0.346,0.608] "
                "(%d/12 in range) -> R-universality-in-range DIES; L57 n=1 agreement "
                "reclassified coincidence." % (m, inreg))
    # POST-HOC reads (committed 114d3ba before the table completed)
    if pri:
        m = med([float(r["R"]) for r in pri])
        say("POST-HOC (i): primary median %.4f vs L67 genus-5-7 band [0.161,0.336]: %s"
            % (m, "INSIDE" if BAND_L67[0] <= m <= BAND_L67[1] else "outside"))
        say("POST-HOC (ii): primary median %.4f vs combined 17-point median 0.357551 "
            "(m3-L70-corrected, verified from their data files): %s"
            % (m, "consistent" if abs(m - MED_COMB) < 0.10 else "not within 0.10"))
        tau, disc, p2 = kendall_exact([float(r["R"]) for r in pri],
                                      [float(r["m0"]) for r in pri])
        say("POST-HOC (iii): Kendall tau(R, log t) over %d primary windows = %+.4f "
            "(discordant %d/%d); EXACT two-sided null P = %.5f -> %s"
            % (len(pri), tau, disc, len(pri) * (len(pri) - 1) // 2, p2,
               "monotone trend REJECTED at 5%%" if p2 < 0.05 else
               "no significant monotone trend"))
    # W-arm comparison (background-count probe, confound flagged)
    say("W-arm probe (pri R vs sec R at same n; d_pri != d_sec => different tightest "
        "pair => windows not measuring the same object):")
    for rp in pri:
        rs = [r for r in sec if r["n"] == rp["n"]]
        if not rs:
            continue
        rs = rs[0]
        same_pair = abs(float(rp["d"]) - float(rs["d"])) < 1e-12
        say("  n=%8d R_pri=%8.4f R_sec=%8.4f  %s  (d_pri=%s d_sec=%s)"
            % (rp["n"], float(rp["R"]), float(rs["R"]),
               "sec>pri" if float(rs["R"]) > float(rp["R"]) else "pri>=sec",
               rp["d"][:10], rs["d"][:10]))
    dq = ("DQ-SECTION (scorer): registered rule applied unmodified; post-hoc reads (i)-"
          "(iii) were COMMITTED at exchange 114d3ba BEFORE the runner finished (timing: "
          "prereg 7847b6c -> L67 ecf950d landed mid-run -> plan 114d3ba -> table "
          "completion) — post-hoc reads generate the next pre-registration, never a "
          "retroactive claim. Combined median 0.357551 verified from m3's "
          "curve_population.json + curve_population_ext.json (L70 correction: mine was "
          "an even-n off-by-one). Kendall null is EXACT (Mahonian DP over all n! "
          "orderings), two-sided, n=12 so the null is coarse (smallest attainable "
          "two-sided P is 2/479001600 * C(66,k)-tail ~ 8.3e-9; power is adequate for "
          "strong trends only). W-arm probe is confounded by selected-pair identity "
          "(d comparison printed); arms never pooled per prereg.")
    say(dq)
    with open(os.path.join(SCRIPT_DIR, "heat67_score.out"), "w") as fh:
        fh.write("\n".join(lines) + "\n" + dq + "\n")


if __name__ == "__main__":
    main()
