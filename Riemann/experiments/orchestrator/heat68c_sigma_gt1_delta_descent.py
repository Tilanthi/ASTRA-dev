"""heat68c — AM-8: rect-Epstein sigma>1 probe, DELTA-DESCENT arm (successor to
heat68b's height arm, which returned outcome (a)).

Motivation (registered in the AM-7 outcome letter BEFORE this run): for
RATIONAL Delta = 1/n, zeta^(2)(s, Delta) = n^{2s} . 1/2 sum' (n^2 j^2 + k^2)^{-s}
is an INTEGRAL Epstein form with discriminant D = -4n^2. Stark's sigma>1 zeros
live at LARGE discriminant; heat68b's Delta in {0.05, 0.10} = n in {20, 10}
=> |D| in {1600, 400} — small — so outcome (a) there is CONSISTENT with
Stark's picture, and the discriminating axis is Delta-DESCENT at fixed
height, not higher t. n in {50..1000} => |D| in {1e4 .. 4e6}.

Also noted in the letter (no computation needed): for real s > 1 every term
(j^2 + D^2 k^2)^{-s} is positive, so the carrier has NO real sigma>1 zeros at
any Delta — any sigma>1 zero must be complex, which is what the vertical
scans probe.

Evaluator: A with heat68's ADAPTIVE truncation discipline (v2, 2026-09-04).
v1 copied heat68b's compact form, whose hard range(1,60) inner m-bound does
not scale with Delta: at Delta<=0.02 the loop dies before the Bessel decay
regime 2*pi*Delta*k*m ~ 1 begins (m3 Letter 99; independently verified here:
4.5% error at D=0.02, 43.8% at D=0.01, sigma=1.05+5i vs relaxed bounds).
Run v1 killed after 4 lines (all D=0.02), preserved as heat68c_v1_killed.out;
those values are VOID. v2 restores heat68's discipline verbatim: m-loop breaks
at z > 160 (K underflow), k-loop breaks at TRUNC_REL = 1e-45 relative shell —
the exact evaluator the heat68 L1 closed-form cross-check validated at
Delta=0.001 to 48.9 digits. dps=30 scan / dps=50 refine.
Scan: D in {0.02, 0.01, 0.005, 0.002, 0.001}, t in {5,10,15,20},
sigma in [1.05, 4.0] step 0.05. Threshold 1e-3 x line median, as AM-7.

Pre-stated outcomes (registered in the letter before this run):
  (a) no local minimum below threshold at any (D, t) -> Stark-consistent
      no-evidence extended to |D| <= 4e6 at heights t <= 20; raw curves kept.
  (b) candidate below threshold -> 2D refine dps=50 + dual-evaluator
      verification (A vs theta-Mellin B). Verified -> first sigma>1 zero
      candidate on a small-Delta rectangular carrier + letter; fails ->
      artifact with diagnosis.
  (c) minima within 3x of threshold -> ambiguous, raw report, no claim.

machine1, single process (CPU cap: heat69 has its own core; this takes the
probe's freed core).
"""
import json, time
from mpmath import mp, mpf, mpc, pi, sqrt, exp, log, gamma, zeta, besselk, fabs, arg

mp.dps = 30


TRUNC_REL = mpf("1e-45")                      # heat68 registered relative shell cutoff


def zeta2_A(s, D):
    """Bessel representation (heat68 evaluator A discipline, v2). m-loop breaks at
    z = 2*pi*D*k*m > 160 (K underflows past exp(-160) ~ 1e-70); k-loop breaks at
    TRUNC_REL relative shell. Replaces v1's hard range(1,60) bounds (m3 Letter 99)."""
    D = mpf(D); s = mpc(s)
    t1 = zeta(2*s)
    t2 = sqrt(pi)*gamma(s - mpf('0.5'))*D**(1 - 2*s)*zeta(2*s - 1)/gamma(s)
    tot = t1 + t2
    nu = s - mpf('0.5')
    total = mpf(0)
    k = 1
    while True:
        shell = mpf(0)
        m = 1
        while True:
            z = 2*pi*D*k*m
            if z > 160:
                break
            shell += (mpf(m)/k)**nu * besselk(nu, z)
            m += 1
        if abs(shell) < TRUNC_REL * max(abs(total), mpf(1)):
            total += shell
            break
        total += shell
        k += 1
    return tot + (4*pi**s/gamma(s))*D**(mpf('0.5') - s)*total


def scan_line(D, t):
    xs = [mpf('1.05') + mpf('0.05')*i for i in range(80)]   # 1.05 .. 4.00
    vals = []
    for x in xs:
        s = x + 1j*t
        vals.append(abs(zeta2_A(s, D)))
    scale = sorted(vals)[len(vals)//2]
    cands = []
    for i in range(1, len(xs)-1):
        if vals[i] < vals[i-1] and vals[i] < vals[i+1]:
            cands.append((float(xs[i]), float(t), float(vals[i]), float(vals[i]/scale)))
    return xs, vals, scale, cands


if __name__ == '__main__':
    t0 = time.time()
    print("heat68c sigma>1 DELTA-DESCENT probe (AM-8) v2 (adaptive truncation, m3 L99). dps=30 scan. Pre-stated outcomes a/b/c (letter).", flush=True)
    THRESH = mpf('1e-3')
    out = {'lines': [], 'candidates': [], 'outcome': None, 'arm': 'AM-8 delta-descent'}
    for D in ['0.02', '0.01', '0.005', '0.002', '0.001']:
        n_eff = int(round(1.0/float(D)))
        for t in [5, 10, 15, 20]:
            xs, vals, scale, cands = scan_line(D, t)
            line = dict(D=D, n_eff=n_eff, disc_eff=-4*n_eff*n_eff, t=t, scale=float(scale),
                        vmin=float(min(vals)), vmax=float(max(vals)),
                        argmin_sigma=float(xs[vals.index(min(vals))]),
                        cands=[dict(sigma=c[0], absval=c[2], ratio=c[3]) for c in cands])
            out['lines'].append(line)
            print(f"D={D} (n={n_eff}, |D|={4*n_eff*n_eff:.0e}) t={t:2d}: scale={float(scale):.3e} "
                  f"min|z2|={line['vmin']:.3e} at sigma={line['argmin_sigma']:.2f}  local-minima={len(cands)}", flush=True)
            for c in cands:
                out['candidates'].append(dict(D=D, t=t, **dict(sigma=c[0], absval=c[2], ratio=c[3])))
                print(f"    local min at sigma={c[0]:.2f}: |z2|={c[2]:.3e}  ratio={c[3]:.3e}", flush=True)
    hits = [c for c in out['candidates'] if c['ratio'] < float(THRESH)]
    if not hits:
        out['outcome'] = 'a'
        print(f"\nOUTCOME (a): no candidate below threshold {THRESH} — Stark-consistent no-evidence to |D|<=4e6 at t<=20.", flush=True)
    elif any(c['ratio'] < float(THRESH)/3 for c in hits):
        out['outcome'] = 'b-verify-needed'
        print(f"\nOUTCOME (b): {len(hits)} candidate(s) below threshold — 2D refine + dual-evaluator verify next.", flush=True)
    else:
        out['outcome'] = 'c-ambiguous'
        print(f"\nOUTCOME (c): minima within 3x of threshold — raw report only.", flush=True)
    out['elapsed_s'] = time.time() - t0
    json.dump(out, open('heat68c_sigma_gt1_delta_descent.json', 'w'), indent=1)
    print(f"done in {out['elapsed_s']:.0f}s; json written", flush=True)
