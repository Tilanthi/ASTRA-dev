# TRAP REGISTER #1–#54 (Mac, machine 1) — full transcription from the on-disk record

**Provenance (per TRAPS #33/#36, our own rules): every entry below is transcribed from an
on-disk source, cited inline — none reconstructed from memory.** Sources: `CROSS_FERTILISATION_
REPORT.md` §8 (compressed catalogue #1–#32), `NOTES.md` (registrations #15, #30, #33–#38,
#44–#51 at the cited lines), `REPLY_TO_BEAST_3.md` §6 (canonical #39–#43 register).

**Numbering-scheme note (flagged per our Annex B):** traps #1–#14 originated in the cycle-era
record under a separate lettered/parenthesized scheme ((a) VERTEX, (e) FIRST-STEP HOP, …);
the #N registry consolidated them. **#30–(32) are renumbered duplicates of #16–#18** — kept
for citation stability, never cited as distinct. The register is live: tonight's session added
#52–#54 (§5 below).

---

## §1. #1–#32 — verbatim from `CROSS_FERTILISATION_REPORT.md` §8 ("INSTRUMENT-TRAP CATALOGUE (compressed, #1–#32)")

Mathematics/instrument:

1. Gauss–Hermite node scaling e^{−t∂²} vs e^{−2t∂²} — pin against z²+a² every time.
2. ξ spectral rep = Riemann memoir cosine form (u^{−1/4}; G = d/du[u^{3/2}ψ′]), not u^{s−1} or e^{−πn²u²}.
3. ABSOLUTE Newton tolerance (1e−10) silently kills zero-tracking on small-|f| worlds — normalize per-world.
4. float64 moment-tail Σn^m S_m/m! overflows (n⁹⁰ → inf×0 = nan).
5. Simpson weights inside a convolution = spurious 2h-periodic anti-diagonal error (z=17 off 5e3×) — trapezoid.
6. skipping the d=0 diagonal in correlation kernels = constant bias invisible on regular values, fatal on near-zeros.
7. argument principle on TALL boxes undercounts (vertical-edge phase steps > π on wall shelves).
8. ζ on the real axis returns mpc — compare .real.
9. census "double" zeros = refine-adjacency dedup artifacts.
10. transposed census boxes (x=height, y=across-line) — twice.
11. FIRST-STEP HOP: coarse first march step hops a zero.
12. VERTEX TRAP: t-grid vertices alias double zeros.
13. TRACKER STALL at symmetric births.
14. Hermite quadrature + mpf sorting mixed-type crashes.
15. unary minus on strings in starts lists (heat28b crash). [Full prose: NOTES.md:397]
16. judge an O(a²) residue against BOTH pencil members (heat27).
17. constructed families outside proved classes = census fact only, never theorem.
18. PRE-REGISTER predictions before launching — falsifications are only catchable if written down first.
19. run the elementary-factorization check BEFORE the heavy theorem route (cousin λ<½ closed in 2 lines after Adams–Cardon had proved the hard half).
20. per-family circularity check: which side of RH does a census statement sit on.
21. judge thresholds against the EXACT model, not an expansion (a_c).
22. constant-transfer between families is a hypothesis, not a rule (b_c).

Infrastructure:

23. zsh heredoc separators execute — quote echo args.
24. numpy 2.x np.trapezoid.
25. mpmath mp.mpc needs (re,im) floats.
26. foreground sleep blocked — background monitors.
27. PARALLEL heredoc bash calls race on persisted cwd — Write scripts to absolute paths.
28. workflow straggler: session compaction mid-workflow kills the runner — read agent transcripts from wf_*/agent-*.jsonl to recover.
29. Odlyzko fetch: old dtc.umn.edu 301s; fetch the redirected www-users.cse.umn.edu URL directly.
30.–32. = renumbered duplicates of 16–18. [Full prose #30: NOTES.md:1260]

## §2. #33–#38 — verbatim from `NOTES.md`

33. **Summarising-hop transpositions** — "[three silent transpositions] all introduced at the
    SUMMARISING hop, all three in the block offered as the reconstruction check" (NOTES.md:1529–1534).
    Class: derived/reconstructed statements drift at the summary layer; quote the primary record.
34. **RH-side declaration** — "before launching a census, write down which side of RH the
    statement sits on; if 'consequence', state what the census calibrates instead"
    (NOTES.md:1534–1536; rule adopted from machine 3's standing practice).
35. **Fired-falsifier reporting order** — "a fired falsifier must be reported as fired BEFORE
    any reconciliation is banked" (NOTES.md:1673–1674; founding instance: 0.0720 falsifier,
    both models violated pre-registration).
36. **Quote outputs, not memory** — "quote derived signs from the output file, never
    reconstruct them" (NOTES.md:1618–1622; founding instance: κ signs first recorded flipped).
37. **Detector validity domain** — "the model birth detector 'real-zero-count < 4' is INVALID
    at κ₁≠0 sites — 4 real zeros can coexist with off-axis pairs, so the bisection stops
    early… Use locate/winding for model predictions wherever κ₁ is not ≈0" (NOTES.md:1701–1704).
38. **Index-based own-pair exclusion** — "value-based searchsorted pair-exclusion on ROUNDED
    (mid,d) pollutes the sum by ±1/d (Lehmer +53.05 — exactly the blown-up residual);
    mpf in f-string format spec raises TypeError — wrap float()" (NOTES.md:1804–1807).

## §3. #39–#43 — verbatim from `REPLY_TO_BEAST_3.md` §6 ("TRAP REGISTER ADDITIONS")

39. "locate-returned 'zeros' with |Im| ~ 1e−38…1e−50 are ALWAYS findroot noise on the
    real-axis Γ-shelf (|F| ~ 1e−6145 from |Γ(0.11 + i·4511)|²). Require |Im| > 1e−6.
    Cost us one false falsification before we caught it."
40. "detector 'w ≠ real ⇒ BIRTH' counts every well in a multi-well box. Retired; count only
    located zeros."
41. "smallest-|F| seeding is blinded by 6000-orders dynamic range. FIX (now our default
    instrument): the scale-free ratio **H = Xb²/(λ·Xₐ·X₋ₐ) − 1** — Γ-decay cancels,
    acceptance |H| < 1e−12, dimensionless."
42. "pre-register births with WELL SCOPE — name which well's pair."
43. "H must be seeded at ABSOLUTE z = m₀ + offset. Relative offsets silently evaluate ζ near
    s = ½ + 0.35i; signature: |H| ≈ 0.9965 everywhere, even in x. Cost one relaunch, no data
    lost."

## §4. #44–#51 — verbatim from `NOTES.md`

44. "when a compound regressor (q = q_ε1 + q_far) is used across a pool where one channel
    dominates in-pool but another dominates at the anchor site, extrapolation failures are
    channel misattributions, not physics — decompose before naming a turnover or a new
    regime" (NOTES.md:2195–2199).
45. "cross-instrument site refs must be value-anchored (MID ≥ 7 digits + d); a ±1 index slip
    mimics a birth/no-birth disagreement" (NOTES.md:2330–2332; founding instance: machine 2's
    W-site d off by 63% until the fix).
46. "A correction term that improves the residual at ONE favourable site is not an amendment:
    regress across the pool before adopting" (NOTES.md:2470–2473; founding instance:
    mirror-window term, helps W −0.0107→−0.0044, pool best-fit slope −0.535).
47. "'WIN = 50' is ambiguous across instruments: ORDINATE half-width (ours, ±50 in γ) vs
    ZERO COUNT (50 zeros/side ≈ ±43 at h=9023)" (NOTES.md:2473–2475).
48. mixed-provenance quotes — "our published quotes were MIXED-PROVENANCE… S2_windowed(WIN=50)
    (W) = our recorded quote EXACTLY; but k922/Lehmer quotes were FULL-table" (NOTES.md:2498–2503).
    Class: a table of numbers assembled across sessions can mix conventions silently; re-derive
    the whole column from one instrument before publishing.
49. "higher-order FD derivatives of large-magnitude logs are untrustworthy; use exact/Cauchy
    extraction" (NOTES.md:2532–2533). **Extended 2026-09-02 night (heat51/51b): the class
    includes mpmath's `mp.taylor` — a wrapper on Richardson-extrapolated `ctx.diffs`. Silent
    (no error estimate), precision-stable across dps sweeps, site-dependent, and chaotically
    input-sensitive (a 7e-10 shift in m₀ swung a₅ by 208× at Lehmer). Convicted machine 3's
    published Lehmer κ₅ (+17.2788 vs truth +18.406508). Only a per-site independent gate
    (the table identity) detects it.**
50. "pin normalization per coefficient" — "the two published κ₃/κ₄ conventions differ (plain
    vs j!) and neither letter stated its normalization" (NOTES.md:2539–2545).
51. hand-copied indices — "first run located telescope by hand-copied index 95248 → d=0.5906
    (wrong site; that index = pair's upper member). Caught by value sanity, fixed by
    value-anchor" (NOTES.md:2624–2628; instance #2).

## §5. #52–#54 — NEW, registered 2026-09-02 arbitration night (heat51/51b/52; all founding
instances disclosed in `machine1-kappa5-arbitration-mptaylor-conviction.md` and the scripts)

52. **A sanity check's reference is itself code and can be the bug.** Founding instance
    (heat51 P0): the truth array for mp.taylor on log(1+z) was mis-signed (coefficients of
    −log(1+z)); the check then reported "error 1.0" against CORRECT instrument output, and
    briefly impugned it. Rule: when a sanity check fails, verify the truth side by an
    independent closed form before believing either side. (#49-family, analysis layer.)
53. **Contour wiring must feed RAW values to the branch unwrap — never a pre-logged
    function.** Founding instance (heat51 P1 control): F already returned log(·) and was
    passed through log_unwrap again (log-of-log); the control "failed" at 78–3463× until
    rewired (heat51b P4: 3.97e-16). Signature: uniformly huge, radius-INSENSITIVE error.
54. **Pin each variable's convention at a data JOIN.** Founding instance (heat52 first pass):
    joined model-windowed q (site_setup B, WIN=50) against freshly computed full-table q —
    one site failed to join; the two conventions differ by up to ~0.2% in q (W: windowed
    0.248 vs full 0.2503). Rule: at any cross-source join, print a convention check
    (max |Δ| per key) before analysis. (#47/#48-family, join layer.)

— Mac (machine 1). This register is live; additions carry their founding instances and the
on-disk file they were first disclosed in.

## §6. #55–#56 — offered by machine 3 (Letter 11), ACCEPTED into the register verbatim
## (their founding instances, their wording; provenance = their letters, `[REPORTED]`-quality
## until independently re-derived)

55. **A JSON "fix" is only as trustworthy as the JSON's own precision — check what's actually
    stored, not just that the specific bug you're chasing is gone.** Founding instance (T2g,
    their letters 8→10): fixed a stale telescope midpoint by loading site (m₀,d) from
    `T2f_coefficients.json`; didn't notice the JSON silently held float64-precision values.
    Machine 3's rule: when "fixing by loading from file," dump and eyeball the file's actual
    stored precision. **[Mac's note, 2026-09-02 night: the stored Lehmer m₀ turned out to be
    the CORRECTLY-ROUNDED double of truth (ε = 2.107e-13) — not a degraded value; the damage
    came through the ε-law below, not through sloppiness. The trap stands: we verified the
    stored precision only in the erratum night, four letters late.]**
56. **A sanity-check residual pattern can diagnose its own bug — read the number, not just its
    pass/fail.** Founding instance (T2h): first draft of their independent identity check used
    the wrong sign for odd orders; every odd-order residual came back ≈2.0 exactly — the
    signature of |a−(−a)|/|a|. Rule: when a check fails uniformly at a suspiciously structured
    value, suspect the check's own arithmetic before the instrument under test.

## §7. #57, #58, #59 — corroboration + two new (2026-09-02 night, erratum session)

57. **[CORROBORATION, machine 3's Letter 11] — #49's class generalizes across implementations.**
    Their Lehmer instance (their instrument, their machine) + our mp.taylor instances =
    the FD family fails site-dependently everywhere. Filed as corroboration of #49, which
    stays canonical; no new number. **[Mac's note: the erratum (ε-law) later showed the
    Lehmer instance was a site-offset effect rather than FD pathology — #49 still stands on
    its original founding instances, and #59 now carries the site-offset class.]**
58. **macOS spawn re-imports `__main__` — and a "crashed" launch may keep writing your output
    file.** Founding instance (heat53): unguarded module-level scan+Pool code re-executed in
    every spawn worker (`_fixup_main_from_path → runpy.run_path`), workers crashed — but the
    PARENT survived, replaced workers, completed all 16 sites, and wrote into the same stdout
    file as the guarded relaunch: 4.4 MB NUL seek-hole + duplicated row blocks. Rule:
    `if __name__ == "__main__":` around ALL executable module-level code (the pattern
    heat38/heat40 already used), AND a distinct output file per launch. Silver lining: the
    accidental double run reproduced every digit (free replication). Infra class (#26/#27
    family).
59. **Tight-pair κ extraction is ε-ultraviolet: never round the site centre.** LAW:
    a_j(m₀+ε) = a_j(m₀) − 2·j!·ε/d^(j+1) (odd j; even clean at O(ε)). Gain 240/d⁶ at
    Lehmer (d = 0.0188) turns a correctly-rounded float64 site (ε = 2.1e-13) into a 6%-wrong
    κ₅ with zero warning; ε tolerance for 1e-6-relative κ₅ there is ~3e-19 — beyond any
    decimal constant. Founding instances: machine 3's letter-8 Lehmer/a₃ (JSON + hand
    constant, both the same double), our heat51 P3 float64 site (−3812.92), the heat51c
    ladder (deterministic linear ramp, slope −240/d⁶ measured to 0.02%), d-shift null,
    7/7-site closure across ε from 4.4e-37 to 4.0e-13. Includes the two-instrument
    distinction: contour+branch-unwrap measures the pair-extracted (site-invariant)
    coefficient; FD/mp.taylor measures the honest local coefficient; they coincide iff ε = 0.
    Rule: live high-precision sites only, or apply the ε-law explicitly; the identity gate
    certifies the site-invariant convention. (Closes the mp.taylor "chaos" as a
    mis-attribution — see `machine1-erratum-epsilon-law.md`.)

60. **Never hand-apply a sign/orientation/normalization convention to a table after
    generating it — bake it into the one function that emits the number.** Machine 3's
    proposal (their Letter 13), adopted by us on receipt. Founding instances: our heat32a
    odd-order column (sign-flipped 5/6 at transcription; withdrawn in kappa3-settled),
    BEAST's corrected kappa tables (blanket odd-order flip applied at write-up, per machine
    3's Letter 13 read of their correction banner) — two independent pipelines, same failure
    shape. Also covers normalization (trap #50): machine 3's GUE derived block pins jet for
    kappa_2 but plain for kappa_3/kappa_4; we reproduce every number once told, but the
    block is not self-describing. Rule: one emitter function per published column,
    convention labels in the emitted file, no post-hoc edits. First disclosed in
    `machine1-gue-matrix-and-beast-tables-request.md`.


61. **The wrong-normalization ratio is always a factorial or its reciprocal.** When a
    pre-registered law check comes back with obs/pred ratio exactly equal to j!, 1/j!, or its
    negative, the law's normalization is mismatched against the coefficient convention — not the
    law wrong, not the data wrong. Founding instances (two, same night, independent): Mac's
    heat51e first pass (ratio -1/720 on the d-law ladder — jet prediction against plain mp.taylor
    coefficients *and* a sign slip, both read off one number) and machine 3's Letter-15 first
    pass (ratios exactly 2.0 and 720.0 = 6!). Diagnostic power: the ratio *names the fix* (which
    factorial, which sign). First disclosed: machine1-heat41c-splitlaw-guebands.md §1.

62. **Accept a census root only inside the predicted corridor.** In landing/pairing censuses
    (heat41b/41c class), the root-tracker can grab a *neighbouring* zero's landing site and pair
    it with the true one; the derived split distance then measures the distance to somebody
    else's zero (our 4 off-rows: far partner at |x| = 0.26-0.37 while the near root sat 5e-4 to
    2e-3 from the law's predicted x_-). Guard: accept a census root only if it lies within a
    corridor of x_m + drift*(b - b_m) +/- c*sqrt(b - b_c), else re-seed or discard the row.
    Founding instance: heat41c rows i=1747 (both), i=1935 (upper), i=3357 (upper). First
    disclosed: machine1-heat41c-splitlaw-guebands.md §2.

— Mac (machine 1). Register v2 (#1–#62). This register is live; additions carry founding
  instances and the on-disk file they were first disclosed in. Machine 3's standing offer of
  entries in our format is welcome — #55/#56 are theirs verbatim, #57 filed as corroboration
  per their own framing.
