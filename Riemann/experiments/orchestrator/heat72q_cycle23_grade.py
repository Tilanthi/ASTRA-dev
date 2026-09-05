#!/usr/bin/env python3
"""heat72q -- mechanical grader for CYCLE 23 post-reveal (m1's L151 instrument).

Inputs (nothing else):
  argv[1]  m2's revealed scored_cycle23.json  (after hash-check vs seal 9aa757c8...)
  argv[2]  my held full run output heat72p_cycle23_l150_full.out (EXACT column)

My committed L150 numbers are HARDCODED below exactly as pushed in da283e6 --
they are immutable; the grader exists so the post-reveal reading cannot drift.

Prints, in order:
  1. my EXACT column vs committed ty4: signs, |ty4/ex-1|, band verdicts
     (leg-delta mapping: R0/R0d/R4 -> [0.3,2.3]%; R1b/R3 -> [2.3,17.5]%;
       R1/R1c pre-stated at/below lower edge; R2 graded on D/R_c only)
  2. m2's revealed values vs my committed ty4 column (sign + magnitude)
  3. D and R_c vs my committed bands
  4. bias-law readings (ty2 vs exact, all 8 rungs)
  5. verdicts C1, C2-original, C2', C3, C4, C5, C6 from the REVEALED values
"""
import json
import re
import sys

# ---- committed at L150 (da283e6) -- immutable ----
TY2 = {'R0': -4.50393e-6, 'R1': +4.17397e-6, 'R2': -5.68959e-6, 'R1b': -2.45766e-6,
       'R3': -1.46696e-5, 'R0d': -3.40563e-6, 'R1c': +4.14964e-6, 'R4': -8.87666e-6}
TY4 = {'R0': -6.93998e-6, 'R1': +4.17115e-6, 'R2': -8.18799e-6, 'R1b': -9.71082e-6,
       'R3': -2.29360e-5, 'R0d': -8.88242e-6, 'R1c': +4.13860e-6, 'R4': -2.08332e-5}
LAUNCH, LAUNCH4 = 4.2496273814283e-6, 4.0845380841617e-6
S_A, S_B, S_BB, S_A4, S_B4 = -1.1190e-5, -7.8477e-8, -1.3960e-5, -1.2967e-5, +5.4067e-8
D_BANDS = {'R2': (-1.173e-6, -1.166e-6), 'R3': (-2.170e-6, -1.901e-6), 'R4': (-1.233e-5, -1.168e-5)}
RC_BANDS = {'R2': (8.92, 8.96), 'R3': (6.24, 7.14), 'R4': (23.14, 24.44)}  # from 8.94+-0.02 / 6.69+-0.45 / 23.79+-0.65
LAM_BANDS = {'R0': (0.003, 0.023), 'R0d': (0.003, 0.023), 'R4': (0.003, 0.023),
             'R1b': (0.023, 0.175), 'R3': (0.023, 0.175)}
F_A, F_B = 6.539269783062942e-8, 6.539269783062942e-8          # cancellation pair
F_B3, F_A4, F_B4 = -2.3892388783e-7, 4.1025724034132e-7, 9.437482143326e-8  # m2's prereg values
# m2's PT predictions to grade C1/C2'/C6 against
PT = {'D2': +5.0104924e-8, 'shift2': -6.63e-7}


def band(name, val):
    if name in ('R1', 'R1c'):
        return 'pre-stated: at/below lower edge (2nd-class finding if larger)'
    if name == 'R2':
        return 'graded on D/R_c only (nominal band decides nothing)'
    lo, hi = LAM_BANDS[name]
    return f"band [{lo:.3%},{hi:.3%}] -> {'IN' if lo <= val <= hi else 'OUT'}"


def main():
    scored = json.load(open(sys.argv[1]))
    ex = {}
    for line in open(sys.argv[2]):
        m = re.match(r'\s*(R\S*)\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)\s+([-\d.e+]+)', line)
        if m and m.group(1) in TY4:
            ex[m.group(1)] = float(m.group(5))

    print("=" * 78)
    print("1. MY HELD EXACT COLUMN vs COMMITTED ty4 (certification; not published pre-score)")
    for nm in TY4:
        e = ex[nm]
        rel = abs(TY4[nm] / e - 1) if e else float('inf')
        print(f"  {nm:>4}  ty4 {TY4[nm]:+.5e}  ex {e:+.5e}  sign {'OK' if (TY4[nm] < 0) == (e < 0) else 'MISS'}"
              f"  |ty4/ex-1| {rel:8.3%}  {band(nm, rel)}")

    print("=" * 78)
    print("2. m2 REVEALED vs MY COMMITTED ty4")
    for nm in TY4:
        v = float(scored[nm])
        rel = abs(TY4[nm] / v - 1) if v else float('inf')
        agree = (TY4[nm] < 0) == (v < 0)
        print(f"  {nm:>4}  mine {TY4[nm]:+.5e}  theirs {v:+.6e}  sign {'AGREE' if agree else '**CONTRADICT**'}"
              f"  |mine/theirs-1| {rel:8.3%}  fires(theirs)={v < 0}")

    print("=" * 78)
    print("3. D / R_c vs MY COMMITTED BANDS (revealed)")
    d2, d3, d4 = float(scored['D_R2']), float(scored['D_R3']), float(scored['D_R4'])
    rc2, rc3, rc4 = (float(scored[k]) for k in ('Rc_R2', 'Rc_R3', 'Rc_R4'))
    for nm, d, rc in (('R2', d2, rc2), ('R3', d3, rc3), ('R4', d4, rc4)):
        lo, hi = D_BANDS[nm]
        rlo, rhi = RC_BANDS[nm]
        print(f"  {nm}  D={d:+.5e} in [{lo:+.3e},{hi:+.3e}]: {'IN' if lo <= d <= hi else 'OUT'}   "
              f"R_c={rc:.4f} in [{rlo},{rhi}]: {'IN' if rlo <= rc <= rhi else 'OUT'}")

    print("=" * 78)
    print("4. BIAS LAW (ty2 vs revealed exact, all 8 rungs)")
    hits = 0
    for nm in TY4:
        e = float(scored[nm])
        if e < 0:
            ok = TY2[nm] > e  # under-negative: ty2 above (less negative than) exact
            tag = 'under-negative?' if ok else '**VIOLATION**'
        else:
            ok = TY2[nm] > e
            tag = 'over-positive?' if ok else '**VIOLATION**'
        hits += ok
        print(f"  {nm:>4}  ty2 {TY2[nm]:+.5e}  ex {e:+.6e}  {tag}")
    print(f"  bias law: {hits}/8")

    print("=" * 78)
    print("5. C-VERDICTS from revealed values")
    l0, l04 = float(scored['launch']), float(scored['launch4'])
    sh2, sh3, sh4 = float(scored['shift_R2']), float(scored['shift_R3']), float(scored['shift_R4'])
    print(f"  C1  D=+{PT['D2']:.3e} sign+ within 2x : D={d2:+.4e} -> "
          f"{'CONFIRMED' if d2 > 0 and 0.5 * PT['D2'] <= d2 <= 2 * PT['D2'] else 'FALSIFIED'}")
    r3rel, r2rel = abs(d3 / sh3), abs(d2 / sh2)
    print(f"  C2  R3<2% & R2>5% (|D|/|shift|)      : R3 {r3rel:.2%} R2 {r2rel:.2%} -> "
          f"{'CONFIRMED' if r3rel < 0.02 and r2rel > 0.05 else 'FALSIFIED'}")
    print(f"  C2' R_c order R4<R2<R3, each 2x PT   : {rc4:.3f} {rc2:.3f} {rc3:.3f} -> "
          f"{'CONFIRMED' if rc4 < rc2 < rc3 else 'FALSIFIED'} (ordering)")
    print(f"  C3  R2 shift in [-9e-7,-5e-7]        : {sh2:+.4e} -> "
          f"{'CONFIRMED' if -9e-7 <= sh2 <= -5e-7 else 'FALSIFIED'}")
    v2 = float(scored['R2'])
    print(f"  C4  R2 does not fire                 : lam(R2)={v2:+.4e} -> "
          f"{'CONFIRMED' if v2 > 0 else 'FALSIFIED -- IT FIRES'}")
    print(f"  C5  D same + sign at R2/R3/R4        : {d2 > 0 and d3 > 0 and d4 > 0} -> "
          f"{'CONFIRMED' if d2 > 0 and d3 > 0 and d4 > 0 else 'FALSIFIED'}")
    allpos = all(float(scored[k]) > 0 for k in ('R0', 'R1', 'R2', 'R3', 'R4'))
    print(f"  C6  all five rungs positive          : {allpos} -> {'CONFIRMED' if allpos else 'FALSIFIED'}")


if __name__ == "__main__":
    main()
