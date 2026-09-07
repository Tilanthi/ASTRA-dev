# Orchestrator inline derivations (cycle 1)

## 1. Li coefficients as phase sums (under RH)

For rho = 1/2 + i gamma (on-line): 1 - 1/rho = (rho-1)/rho = (-1/2+i gamma)/(1/2+i gamma),
which has modulus EXACTLY 1 (|numerator| = |denominator|). So

    lambda_n = sum_rho [1 - (1-1/rho)^n]  (Bombieri-Lagarias, regularized)
             = sum_gamma 2[1 - cos(n theta_gamma)] + regularization,
    theta_gamma = arg((-1/2+i gamma)/(1/2+i gamma)) in (-pi, pi).

Growth mechanism: theta_gamma -> pi as gamma -> inf like theta = pi - 2 arctan(1/(2 gamma));
for n theta_gamma mod 2pi to equidistribute need gamma << n·(something)/1: terms with
gamma <~ n average 2(1-cos) ~ +2 each (random phases), terms with gamma >> n stay near
2(1-cos(n pi - small)) -> 2(1 - (-1)^n cos(small)) -> 0 or 4 alternating (cancellation
across the conjugate-regularization). Net: lambda_n ~ 2·N(c·n) ~ (n/pi)log(n/2pi) —
the (n/2)log n growth IS the zero-counting function in disguise. [Consistency check
passed: asymptotic lambda_n = (n/2) log(n/(2 pi e)) + O(n) matches this mechanism.]

## 2. Detection depth n*(eps, gamma) for an artificial off-line zero

Quartet injection xi*F: lambda_n(xi*F) - lambda_n(xi) = S_n EXACT, with
S_n = sum over quartet [1-(1-1/q)^n]. For rho = 1/2+eps+i gamma the mirror term
r2 = |1 - 1/(1-rho)| satisfies r2 - 1 ~ eps/gamma^2 (small). First violation of
lambda_n >= 0 at n* solving 2 r2^{n*} ~ (n*/2) log n*:

    n* ~ (gamma^2/eps) · 2 log(gamma)  (parametric)

CONSEQUENCE: Li-sequence positivity is quadratically blind in gamma to off-line zeros:
a zero at height gamma with eps=0.01 needs n ~ gamma^2·10^2·log gamma to show.
Computational Li-checks can NEVER approach relevance for high zeros; any Li-based
proof must control all scales uniformly. [Novelty: to check — the lambda_n asymptotics
under off-line zeros exist in the literature (Bombieri-Lagarias domain); the explicit
n* scaling as "detection depth" may be folklore-adjacent.]

## 3. Mayer monomial truncation failure (see genealogy)

Entries exact; truncation diverges even where the Fredholm determinant converges.
Root cause: monomials outside nuclear class + n-sum domain wall at Re s = 1/2.
The operator's domain boundary IS the difficulty of RH in this representation.

## 4. Detection-depth law — CORRECTED (li_injection3.py, 100k Odlyzko zeros)

lambda table now valid: lambda_1 = 0.0230957 (lit exact), lambda_2 = 0.092346
(lit 0.092336; Odlyzko 9-dec rounding), 50k-vs-100k truncation consistency
2.5e-4 at n=20000, positivity holds n<=20000 (min = lambda_1).

Injection (quartet GRAFTED at first-zero height gamma=14.1347, beta=0.8):
first violation of lambda_n >= 0 at n* = 6312 (lambda = 20475, S = -25657).
CORRECTED LAW (replaces the '2 log gamma' of section 2): n* solves
2 r2^{n*} ~ lambda_{n*}  =>  n* ~ (gamma^2/eps) * ln(lambda_{n*}/2),
with ln r2 ~ eps/gamma^2. Check: (200/0.3)*ln(10238) = 666*9.23 = 6147
vs measured 6312 — closes to 3%. Parametric form n* ~ (gamma^2/eps)*O(10)
confirmed; the log factor is ln lambda_n* (self-consistent), NOT 2 ln gamma.
beta=0.6 at gamma=14.13: no violation to n=20000 (predicted n* ~ 21000,
just past grid — consistent).

Consequence stands, sharper: Li positivity detects an off-line zero at height
gamma only at index n ~ (gamma^2/eps)*ln(...). For gamma = 100, eps = 0.01:
n* ~ 1e6*10 — the ENTIRE useful lambda table (n <= 1e5) is blind. Li-route
proofs must control all scales uniformly; no finite lambda data can certify RH.

## 5. FE-filter calibration: S1 and S2 are the SAME first-order detector
(fe_filter_calibration.py, dps 30; F = xi*Q, Q = quartet(rho)/quartet(a)
with a = ACTUAL on-line zero 1/2+14.1347i so F is entire, FE-true
[residual 2.4e-17], zero-count preserved, on-line pair swapped for off-line
quartet — the Davenport-Heilbronn shape; NOTE: ratio construction requires a
to be a true zero ordinate, else F has poles)

beta = 0.8 (eps=0.3):
  S1 valley floor violated for t in [13.535,14.735] (width 1.20) at EVERY
  sigma in [0.52,0.9]; depth -30 to -34 (log units) in the interior.
  S2 C_F(t) < 0 EXACTLY on t in [13.5347,14.7347] — the SAME window (1.200).
beta = 0.52 (eps=0.02):
  S1 violation t-width 0.050 at sigma=0.52, below grid resolution (0.025)
  for sigma >= 0.55. S2 C_F < 0 only on a sub-resolution sliver; min
  C_F = -5.1e9 exactly at t=gamma0. Pure-dipole C_Q min = -1.02e10 = 2xC_F
  (the -2/eps^2 two-member dipole vs removed +1/eps^2-monopole signature).

FINDINGS:
 (a) window width ~ linear in eps (1.20 @ 0.3 -> 0.05 @ 0.02, ratio 24 ~ eps
     ratio 15 within grid resolution): off-line zeros are detected by BOTH
     S1 and S2 on a window of t-width proportional to beta-1/2.
 (b) S1 and S2 fail on the SAME interval: the valley floor and the curvature
     positivity are the same first-order instrument (the dipole field of the
     off-line pair). Distinct content, if any, lives in higher sigma-
     derivatives (the all-order ladder) and in the global arrangement.
 (c) Both fail for the planted F => both require arithmetic beyond FE for
     their proof (FE-filter satisfied; no free symmetry proof exists).

## 6. Triage lemma (t-means cannot see zeros)

t-averaged conservation laws with integrable point singularities (spikes
|t-gamma|^{-alpha}, alpha<1 for zeros, alpha<2 for poles) CANNOT detect
individual off-line zeros: the spike contributes O(1) to the mean. Applied
to kill naive-round-2 candidates 28 (|1/zeta|^2 mean: 2nd-order pole is
integrable) and 29 (negative moment alpha<1). Valid RH-detectors among mean
quantities need alpha >= 1 (then on-line zeros must be excluded by the setup)
or sign/winding structure. See genealogy naive-round-2 table.

## 7. The alternating ladder correction (orchestrator, kills S2's "all-order family" claim)

Local series of an on-line zero: 1/2 log((sigma-1/2)^2 + c^2) = 1/2 log c^2
+ x^2/(2c^2) - x^4/(4c^4) + ...  (x = sigma-1/2). Hence an on-line zero
contributes (−1)^{k+1}(2k−1)!/(t−γ)^{2k} to ∂^{2k}_σ log|ξ| at σ=1/2:
  k=1 (curvature C): +1/(t−γ)^2  — monopole-positive ✓ (S2's verified claim)
  k=2: −6/(t−γ)^4 — NEGATIVE. VERIFIED numerically (dps 40, stencil 1e-5):
      d4 < 0 at t = 5, 17.5, 17.58, 18, 20, 100 (values −0.001 … −5.5).
So the monopole-positive family is the ALTERNATING ladder
  M_k(t) := (−1)^{k+1} ∂^{2k}_σ log|ξ(1/2+it)| = Σ_γ (2k−1)!/(t−γ)^{2k} + dipoles,
NOT the plain all-order family (which is false for k≥2 even under RH).
Shielding analysis: a dipole at perpendicular distance δ and same height as a
monopole contributes to M_k with weight (c/r)^{2k}, r = sqrt(δ²+c²) > c —
suppressed EXPONENTIALLY in k. Higher order = more local = MORE blind to
shielded zeros, not less. The entire alternating ladder fails R2 (shielded
world), same as S1. First-order local detectors cannot see through shielding,
at any order. (Cross-check vs math:S2/exp:S2 when they land.)

## 8. Consequence for the search space (cycle-2 steering)

What CAN distinguish ξ from the shielded FE-world F2? Only arithmetic: F2 has
no Euler product; its Dirichlet-coefficient/ψ/Mertens behaviour violates
unconditional prime facts (ψ(x) ≥ log 2 = instrument #19). CYCLE-2 EDGE:
enumerate ARITHMETIC SEPARATORS (unconditional ζ-coefficient facts that fail
on every FE-world function), then generate bridges FROM separators TO
zero-placement. Also: global-arrangement (winding-family) detectors that see
through shielding. Read Gorodetsky 2025 (Helson) before any μ-matrix mutation.

## 7b. S2 R2 closure by direct measurement (orchestrator)

Shielded-remote world F5 = xi * quartet(0.8+14.1347i)/quartet(1/2+23.1703i):
planted off-line zero ALIGNED with SURVIVING on-line zero #1 (14.1347),
denominator quartet REMOTE (23.17) to avoid removal artifacts.
Result: C_{F5}(t) > 0 on the whole window [8.13, 20.08]. The aligned
monopole completely masks the off-line dipole. C(t) > 0 does NOT imply RH.
(Also learned: denominator-removal creates its OWN C-negativity artifact
near the removed ordinate — R2 instrument spec must use remote denominators;
updated in REDUCTION_TEST.md.)
Both S1 (floor) and S2 (curvature) are measured strictly-weaker-than-RH.


## 9. FE-WORLD CONSTRUCTION BUG (found 2026-09-01, orchestrator) + F3-at-height calibration

**BUG (affects all cycle-1 worlds with a denominator at an on-line ordinate):**
quartet(1/2+i*g) = {a, a-bar, 1-a, conj(1-a)} = {a, a, a-bar, a-bar} -- the four
factors COLLAPSE to two doubled factors when a is on the line. Dividing xi by
quartet(a) therefore cancels xi's SIMPLE zeros with multiplicity 2 => F has POLES
at a, i.e. F is meromorphic, NOT entire. My "finite at a+0.001" validation was
vacuous (a pole is finite off its location); FE residuals don't catch it either
(FE holds as a meromorphic identity). Consequences measured: all deep "dips" near
removed zeros in the first at-height run (R=-5.1, -inf at t=g_k; -5.9 at t=the
remote removed zero) are POLE ARTIFACTS.
  CORRECT construction: cancel each on-line zero ONCE:
    F = xi * quartet4(rho) / [(s-a_j)(s-conj(a_j))(s-a_l)(s-conj(a_l))]
  with two distinct on-line ordinates a_j, a_l (remote from the test window).
  Entire (validated: log|F| finite near removed zeros, FE residual ~1e-41),
  real, order 1, zero-count preserving.
  STATUS OF EARLIER RESULTS: S1 agent's shielded-world min R=1.0002 and my /tmp
  F5 C>0 both used doubled denominators BUT with the poles REMOTE (7-9 units)
  from their scan windows -- smooth-contamination argument says conclusions
  survive; NOW RE-CONFIRMED in the clean entire world (below). My
  fe_filter_calibration.py window constants (S1/S2 violation width 1.20) are
  contaminated by the pole at the test height and need re-measurement if used.

**BUG 2 (transcription): the dip ordinate. S1 agent's law is x=b/2, i.e.
sigma_dip = 1/2 + (beta-1/2)/2 = (1/2+beta)/2 (MIDPOINT of 1/2 and beta), NOT
(1+beta)/2.** e.g. beta=0.7 -> sigma*=0.60.

**F3-at-height calibration (f3_height_calibration2.py, zero #10143,
g_k=10000.065345, remote dens +-34 units, mpmath dps40 confirmation):**

UNSHIELDED planted quartet at (beta, g_k), R(sigma,t)=log|F(sig+it)|-log|F(1/2+it)|:
  beta=0.70: mpmath R(sigma*, ~g_k) = -0.2564   (law: log(3/4)=-0.2877)
  beta=0.60:                                   -0.2796
  beta=0.55:                                   -0.2850
  => 3/4-DIP LAW CONFIRMED AT HEIGHT 1e4: background compensation +0.031 at
  eps=0.2, +0.003 at eps=0.05 (nearest-neighbor zero contributes
  ~(1+(x/d')^2...) >= 1 factors only). The law is a sharp quantitative
  unshielded-off-line-zero detector at height.
  Global min over sigma (deeper than sigma*, diverges as sigma->beta):
  mpmath-confirmed -1.19 at sigma=0.670 (eps=0.2), -1.26 at 0.585/0.542.
  Violation t-widths (fast engine, away from exact zero): 0.535/0.345/0.195 at
  eps=0.2/0.1/0.05 -> width ~ 2.5-4 eps.

SHIELDED (line zero at g_k survives, planted quartet aligned; clean entire world,
denominators 2 remote ordinates):
  min R outside mask radius eps/2:
    eps=0.200: +0.0415 (sigma=0.6)   eps=0.100: +0.0107   eps=0.05: +0.0028
  => NO floor violation outside the mask at any eps>=0.05. SHIELDING CONFIRMED
  IN A CLEAN ENTIRE WORLD at height: the S1 floor detector is quantitatively
  blind to shielded off-line zeros even at the optimal sigma*. (The lone
  eps=0.005 "violation" -1.12 at t-g_k=+0.850 sits exactly on line zero
  g_(k+2)-g_k=0.8528: fast-engine near-zero artifact, not a dip.)

**fast_zeta accuracy doctrine:** reliable to ~1e-3 in R away from line zeros
(|t-gamma| > ~0.05); NEAR zeros the relative error explodes (|zeta| tiny) --
two-tier protocol: fast engine to SCAN, mpmath dps>=40 to CONFIRM candidate
violations. Prefactor bug fixed 2026-09-01: log(0.5*s(s-1)) = log 0.5 +
log|s(s-1)| (the 1/2 is a prefactor, NOT an exponent) -- earlier validation
block was comparing two wrong assemblies.


## 10. Clean low-height S1/S2 calibration (fe_filter_calibration_v2.py, dps 35)

Corrected constants replacing the pole-contaminated v1 (v1 window "1.20" was a pole artifact):

UNSHIELDED (beta=0.8, eps=0.3, plant at gamma1=14.135, den pairs REMOTE {21.022, 25.011}):
  S1 floor violation width 0.575 (~2*eps) at sigma=0.52-0.6, shrinking with sigma
  (0.40 at 0.8, 0.175 at 0.9); depth diverges at sigma->beta (-32.8 at 0.8 --
  the planted-zero log divergence; ANY unshielded off-line zero makes
  margin(beta, gamma) = -inf, so S1 with sigma-resolution ~eps always sees it).
  S2 C_F<0: width 0.25 (contiguous around t=14.11), min -21.7; total negative
  measure 0.55.
UNSHIELDED (eps=0.02): S2 C_F > 0 EVERYWHERE (min +0.0695) -- curvature detector
  fully masked even unshielded below eps~0.02; S1 still sees the sigma=0.52
  sliver (width 0.025, the log-divergence at sigma~beta).
SHIELDED (both eps): S1 NO violation at any sigma (min margins +0.0000..+0.0067);
  S2 C_F > 0 everywhere (min 0.0836 at eps=0.3 vs 0.0837 at eps=0.02 -- the
  aligned mask cancels the planted quartet's sigma=1/2 curvature to ~1e-4,
  i.e. essentially exactly).
DOCTRINE: S1-class floor scans detect UNSHIELDED off-line zeros at any eps
(via sigma->beta divergence); S2-class curvature is worthless below eps~0.05
even unshielded; NOTHING line-local sees shielded zeros. Confirms and sharpens
the cycle-2 steering: only arithmetic separators, global arrangement/winding,
or structural constructions remain.


## 11. INSTRUMENT F4: winding detector (shield-immune) — orchestrator, verified 2026-09-01

W(t) = Delta-arg_{sigma in [1/2,1]} F(sigma+it), unwrapped along the horizontal segment.
Exact model: each zero contributes -/+ the VISUAL ANGLE of the segment seen from the zero;
on-edge zeros (sigma=1/2) subtend ~pi/2, interior zeros subtend ~pi. Masks hide fields,
not counts.

Measured (gamma0=14.135, beta=0.8/0.6, t=gamma0 +/- 0.01, dens {21.022, 25.011}, dps35;
winding_detector.py) -- measured W_F - W_xi vs exact visual-angle prediction:
  UNSHIELDED beta=0.8: +1.4525 vs +1.4560 (below), -1.6044 vs -1.6009 (above)
  UNSHIELDED beta=0.6: +1.4733 vs +1.4768
  SHIELDED   beta=0.8: +2.9525 vs +2.9609  <-- ~pi vs xi: DETECTED THROUGH THE MASK
  SHIELDED   beta=0.6: +2.9733 vs +2.9817
  world-axial difference -1.5000 vs edge-angle -1.5508
Model accuracy ~0.3-0.7% (finite ramp width arctan(1/(2*0.01))).

CONSEQUENCES:
 (i) F3 (dip) catches unshielded off-line zeros; F4 (winding) catches shielded ones.
     Joint disproof-instrument coverage of both counterfactual classes.
 (ii) The zero-knowledge-free version of F4 collapses to N(T)/Backlund counting
     (summed ramps over a window = pi/2 x #zeros under RH) -- classical. Resolved
     ramps read off beta directly (ramp size = visual angle of [1/2,1] from the
     zero): instrument packaging POSSIBLY NEW, math classical.
 (iii) DOCTRINE sharpened (R2): a bridge must be at least as strong as counting --
     any RH proof must control the argument principle; line-local inequalities
     never will. Cycle-2 lane (b) = global arrangement = winding family, exactly.


## 12. Literature gate: Helson conjecture status (read 2026-09-01)

Harper (strong form) + Gorodetsky-Wong arXiv:2405.19151 (short proof, via Saksman-Webb
random zeta model) resolved the STEINHAUS-RANDOM version: E|sum_{n<=x} alpha(n)| = o(sqrt x);
equivalently H_alpha = [alpha(n+m)/(n+m)] bounded on l^2 a.s. The DETERMINISTIC mu-weighted
Helson matrices (boundedness ~ L^2 behavior of 1/zeta on sigma>1/2, Landau/RH-adjacent) remain
the open territory. Lane status for cycle 2: deterministic mu-Helson boundedness is an RH-TRANSFER
(fails R5) unless a genuine weakening exists -- candidate weakening (S4-analogue): Schatten-p
class membership or determinant asymptotics of truncated mu-weighted matrices for p above the
critical exponent. QUEUED for cycle-2 attack wave.
Sources: arxiv.org/abs/2405.19151; arxiv.org/abs/1709.06326 (Helson eigenvalue asymptotics).


## 13. F4 at height: fast engine NOT adequate (honest record)

fast_zeta winding at H=1e4: control point (no planted structure) measures W-xi offset
-0.20 rad; shielded/unshielded deltas at height (-0.06/-3.08 etc.) do NOT reproduce the
low-height mpmath values (+2.95 below). Cause: arg noise where |zeta| is small along the
sigma-path (single-point arg diffs vs mpmath up to 1.1 rad); 400-step unwrapped sums drift.
F4 remains: LOW-HEIGHT mpmath-verified instrument (NOTES 11) + doctrine. At height it
needs per-candidate mpmath confirmation; fast prescan threshold |W|>1.5.
Complex log-xi (log_xi_complex, winding_scan) added to fast_zeta and validated in arg to
~0 for well-conditioned points; W under RH ~= 0 exact interior-zero counter confirmed at
height (fast +0.0000 vs mpmath -0.0015 at t=9995.5).


## 14. Zero-lattice gap statistics vs C-detector thresholds (orchestrator, gap_statistics.py)

99,351 gap midpoints (Odlyzko 100k, t>1000): C_bg(t) = sum 1/(t-gamma)^2 at midgaps
correlates -0.996 (log-log) with local gap -- C_bg is a function of the gap alone.
Per-decade: max gap 2.3x mean (t~50) rising to 2.8x mean (t~5e4); C_bg_min per decade
1.01 -> 5.77; global min C = 2.381 at t=1069.3 (gap 2.545 = 2.08x mean).
Reproduces the S2-mathematician kill/escape law: u_c = sqrt(2/C_bg) = 0.60 at their
bin -- EXACT match to their measured 0.597.
ADJUDICATION of the S2 next_move ("do zero-density theorems force C_bg>0 at midgap?"):
NO ROUTE -- density theorems bound OFF-LINE zero counts; C_bg at midgap depends on
ON-LINE zero GAPS. These are different quantities; unconditional max-gap control is
not available (GUE-extremal only). C>0 unconditional = max-gap control = the same wall.
The C-detector's unshielded threshold stays u_c(T) ~ 0.6-0.9 for all computed heights.


## 15. Margin-identity Fourier fence (orchestrator derivation, cycle 2)

M(delta,t) = 1/2 sum_gamma [log(1+delta^2/(t-gamma)^2)+mirror] (the RH-installed form of the
margin identity). FT in t: using int log(1+delta^2/x^2) e^{iux} dx = -2pi e^{-delta|u|}/|u|,
   M_hat(u) = -pi (e^{-delta|u|}/|u|) sum_gamma (e^{iu gamma} + e^{-iu gamma}).
=> The t-Fourier transform of the margin is EXACTLY the ordinates' spectral measure
(Montgomery pair-correlation object) times an explicit kernel: BETA-BLIND. Every mean-field /
t-averaged / Fourier mutation of the margin identity reduces to pair-correlation structure
and CANNOT see beta at all. Beta-sensitivity lives only in t-LOCAL structure -- which is
exactly where shielding and masking operate. FENCE for cycle-2 mutator agents: do not spend
effort on spectral/mean-field margin functionals; the only margin content beyond ordinates
is local (and locally shielded). [The simple ordinates-only identity is RH-INSTALLED; the
unconditional form has the b-dependent quadruple factors -- no free lunch.]

## 16. Energy-budget pair law (C2-S2 verified, orchestrator, 2026-09-02)

psi from EXACT Lambda sieve to 2e7. B(X)=int(psi-u)^2/X^2 ~ 0.0217 flat (0.0199-0.0236)
over 4 decades. Explicit-formula pair decomposition:
  B(X) = 2 Re B1(X) + 2 Re B2(X)
  B1 = sum_{j,k} e^{i(gj-gk)logX}/(rho_j conj(rho_k)(2+i(gj-gk)))   [near-diagonal band]
  B2 = sum_{j,k} e^{i(gj+gk)logX}/(rho_j rho_k(2+i(gj+gk)))          [fast, small]
Constant part = sum 1/(2|rho|^2)*2 = sum 1/|rho_k|^2-ish ~ 0.0231 (2000 zeros + tail).
RECONSTRUCTION: first 2000 zeros (W=3 band) reproduce measured B at 6 X-values to
|diff| <= 8e-4 (4%), means to 0.03% (1e6: 0.02192 vs 0.02192), fluctuation corr 0.914.
  => B(X) is a ZERO-PAIR SPECTRAL FUNCTIONAL: logX-Fourier lines at pair differences
     gj-gk = Montgomery pair correlation, x-side mirror of the margin Fourier fence.
  => beta-SENSITIVE IN LEVEL: off-line zero conjugate-diagonal term X^{2beta-1}/((2beta+1)|rho|^2)
     (verified: planted beta=0.58 gamma=14.13 excess +3.2 at 1e6 -> +5.5 at 2e7, growth
     factor 1.72 vs predicted X^0.16=1.61; amplitude 1.6-1.7x closed form = cross terms).
     gamma=100 plant buried (+4%, needs X~1e17); gamma=14 detectable at X~1e6.
     => QUANTITATIVE RH-CHECK: B(2e7) flat to +-10% excludes any beta>1/2 zero with
        gamma <~ 30 (X^{2beta-1}|rho|^{-2} would exceed the band).
As RH ROUTE: proving B bounded = Cramer-equivalent (same wall as M(x)); the NEW content
is the instrument + the exact spectral identity (pair law).
Files: energy_budget.py, budget_pair_decomposition.py (both orchestrator).

## 17. PF-infinity kill of candidate 47 (orchestrator, 2026-09-02)

Phi(u) = sum (2 pi^2 n^4 e^{9u/2} - 3 pi n^2 e^{5u/2}) e^{-pi n^2 e^{2u}}, even, >0, Phi(0)=0.4467.
- PF2 OK: log-concave (min slack +0.047), |Phi(u)| <= Phi(0), L''(0) = -18.73.
- 240 random Toeplitz minors m=2..5: ALL positive (min 7.5e-10).
- CLUSTERED m=5 at {0.28,0.29,0.30,0.31,0.32}: det = -2.1e-26 < 0 (dps 60/80, normalized
  entries, model-checked: Gaussian +1.5e-25, quartic-corrected -1.1e-26 -- structural sign flip).
- log Phi expansion: a2 = -9.36349, a4 = -5.9516, a6 = +1.771.
- SCHOENBERG OBSTRUCTION: even PF-inf kernels have representation
  k = e^{-gamma u^2} * prod_j (1+eps_j u^2)^{-1} (up to scale/shift), so log k's quartic
  coefficient is +1/2 sum eps_j^4 >= 0. Phi's a4 < 0 ==> NOT PF-inf. Obstruction is
  MEASURED and STRUCTURAL: Phi decays faster than Gaussian at small u (sharper than any
  PF-inf kernel), consistent with Xi being in LP only if RH (the kernel side cannot be
  Positivity-proved). Files: pf_infinity_test.py, pf_stress_test.py.

## 18. Mu-variance screening law (orchestrator, 2026-09-02) -- Ng-conjecture verified + framing

EXACT mu sieve to 2e7 (vectorized flip sieve; 1.27e6 primes).
- Var(M(x)/sqrt(x)): rms 0.130 (last 1e6 window), i.e. Var ~ 0.0169x;
  B_M(X) = int M^2/X^2 declines 0.0164 -> 0.0122 over [1e4, 2e7] (slowly -- F still settling).
- NAIVE random walk predicts Var = (6/pi^2) x = 0.6079x, rms 0.779. MEASURED 0.130:
  THE SUMMATORY MOBIUS IS 6x SMALLER THAN THE WALK -- zeros screen 97.6% of the power.
- ZERO-SIDE: sum_rho 1/(|rho|^2 |zeta'(rho)|^2) over first 1500 zeros (mpmath dps 30,
  |zeta'(1/2+i g_k)| direct) + power-law tail = 0.01449 vs measured 0.0122-0.0169. MATCH.
  First zero carries 55% (7.95e-3); first 5 carry 76%; empirical |zeta'(rho)| ~ 1.41 g^0.143.
- ATTRIBUTION: the variance identity is essentially Ng's 2004 conjectured limiting
  distribution for M(x)/sqrt(x) (RH + simplicity + convergence). NOT new as conjecture.
  NEW HERE: the screening-ratio framing (0.0145/0.6079 = 2.4%); first-zero dominance;
  M-growth edge e(X) = 0.4307 -> 0.4445 over [1e4,2e7] (below mu_N zero edge 0.52-0.55,
  consistent with Landau link, both -> 1/2 under RH);
  DETECTOR CONSEQUENCE: M has NO main term -> the mu-channel is the CLEANEST beta-detector:
  off-line zero excess ~ 2 X^{2beta-1}/((2beta+1)|rho zeta'(rho)|^2 B_M): for beta=0.6,
  gamma=14: ~98 X^0.2 relative -- saturates immediately; gamma=30: ~X^0.2/24 (detectable
  at 2e7); gamma=100, beta=0.6: ~7% (marginal); beta=0.55 gamma=100: 1.4% (buried).
  Same gamma ~< 30 reach as psi-budget but bigger relative signal, no main-term background.
File: mu_budget.py.

## 19. DH budget test: the pair law is EULER-PRODUCT-SPECIFIC (orchestrator, 2026-09-02)

dh_budget.py: psi-analogue for Davenport-Heilbronn via c = (a.log)*b (b = Dirichlet
inverse of a(n)=2Re[(1-i k)chi(n)]), exact FE re-verified (|c|=1.000000, residual 4e-17),
off-line zero re-refined 0.808517+85.699348i.
RESULT: B_DH(1e3..1e6) = 49.7 -> 633,217 (vs zeta FLAT 0.020-0.024); growth exponent
log-log = +1.34/+1.29/+1.41/+1.53/+1.48 -- NOT the zero-predicted 2*0.8085-1 = 0.617.
WHY (the discovery): DH has no Euler product, so c(n) = (a log)*b has convergence
abscissa sigma_c ~= 1.2 > beta_max(zeros) = 0.81 (Landau only forces sigma_c >= beta_max,
measured exceeds it). The coefficient side X^{2*1.2-1}=X^{1.4} dominates the zero side
X^{0.617} FOREVER -- the budget is never zero-dominated.
CONSEQUENCES:
1. Budget flatness SEPARATES zeta from DH (litmus fires: any "B flat" criterion
   is violated massively by DH) -- but via the EULER defect, not the zero directly.
2. The pair law's zero-side reconstruction (NOTES 16) requires Lambda's support on
   prime powers: psi - x is zero-dominated BECAUSE the Euler product forces
   Sigma_{n<=x} Lambda(n) - x = zero sum exactly. Dirichlet coefficients alone
   (DH has them) give NO budget law. C2-F1's "consumes arithmetic" upgraded to
   "consumes the EULER PRODUCT".
3. Explains why proving B = O(X^{1+eps}) is RH-STRENGTH (Cramer wall) from the
   coefficient side too: flatness = Euler structure + zero-line-ness jointly.
4. DH-litmus protocol now: P(zeta) vs P(DH) at matched ordinates. Inverse-coefficient
   sums: FIRE (Landau abscissa). Budget: FIRE (Euler defect). Winding: sees quartet
   through shield. FE-phase: blind (DH satisfies). Everything FE-pure is dead.

## 20. Hankel D1 instrument: degeneracy law + two-sided windows (orchestrator, 2026-09-02)

hankel_d1_survey.py + hankel_d1_threshold.py (100k Odlyzko zeros, +/-25 window + density tail).

L1 DEGENERACY LAW: rho(t) = D1/(m1 m3) = Cauchy-Schwarz ratio of the zero-atom measure
  x_j=(t-g_j)^{-2} at all 99999 midpoints: ALWAYS > 0 on real zeta (CS sanity), but
  min rho = 2.8e-4/3.6e-4/3.7e-4/4.3e-4 co-located EXACTLY with the 4 tightest gaps
  (63137.2 gap .0208, 36510.2, 57273.7, and the LEHMER PAIR t=7005.08 gap .0377);
  p1 = 1.4e-2, median 0.16, max 0.34. Real zeta sits ~3 decades above violation; the
  near-degeneracy of tight pairs IS the whole margin structure (pair term x1x2(x1-x2)^2->0).

L2 TWO-SIDED DETECTION WINDOWS (honest geometry: quartet {1/2+-u+-i gp} at the ENDPOINT
  ordinate of a tight gap, evaluation at the midpoint; m_n = exact t-derivative algebra
  of Im[xi'/xi], validated vs direct zero sums and both u-limits):
  - DEGENERATE sites (tight pairs, rho~3e-4): D1<0 for u/gap in [0.01, ~0.25] AND
    [~1, ~20]; BLIND (D1>0) for u/gap in (0.25, 0.9) -- INVERTED vs the instrument-
    mutator's fence-2 claim (detect 0.45g, blind 0.55g): their geometry differs
    (aligned fence-2); single-endpoint quartets are blind exactly at 0.3-0.7 gaps.
  - GENERIC sites (t~1000, gap 1.56): single quartet NEVER flips D1 at any u
    (max dip 4% of clean at u/gap=0.2) -- D1 is a DEGENERACY-SITE detector only.
  - COMPLEMENTARITY (the useful law): fixed-order detectors (C(t), m_n) are blind at
    small u (Nyquist cluster law, NOTES 16 era) but strong at large u; D1 covers
    SMALL u at degenerate sites. Union = no known blind spot for single quartets;
    multi-quartet conspiracies remain open (same Nyquist lesson at higher order).
  - u->0 limit: D1 -> ~2x D1_clean (double atom, measure stays real-positive);
    u->inf: D1 -> D1_clean exactly (1e5-gap check: +9.8797e12 = clean).
Corrections issued: agent's universal "u_c = 0.48 gap" is geometry-specific; my first
L2 planted at the evaluation point (trivially detectable, meaningless) -- both fixed.

L3 DERIVATIVE-SIDE CLOSED (hankel_d1_l3.py): at the Lehmer midpoint t=7005.082 (dps 60,
mp.diff orders 1,3,5 of Im[xi'/xi](1/2+it)), m1/m2/m3 from ZETA ALONE match zero sums to
1.6e-5 / 1.5e-7 / 2.3e-7; D1 = +3.3837e11 vs zero-sum +3.3430e11 (1.2% -- the expected
~3-digit cancellation). Real-zeta D1 at the Lehmer site is POSITIVE from derivatives
alone => the detectable off-line windows u/gap in [0.01,0.25] u [1,20] are EXCLUDED at
that site by pure zeta evaluation (blind zone (0.25,0.9)*gap remains). D1 is deployable:
~18 zeta log-derivative evaluations per t, no zero data.

## 21. Hankel HIERARCHY law: interleaved detection sectors (orchestrator, 2026-09-02)

hankel_d2.py / hankel_d23.py: D_n = m_n m_{n+2} - m_{n+1}^2 for n=1,2,3 (orders through 10),
same honest geometry (endpoint quartet, midpoint evaluation). D_n fires in INTERLEAVED
u/gap sectors:
  D1: [0.01,0.2] u [0.9,20]   D2: [0.05,0.1] u [0.48,1.0]   D3: {0.3, 0.48}
UNION D1 u D2 u D3 = full coverage 0.01..20 at the tightest site (63137); single gap
u/gap=20 remains at Lehmer + 36510 sites (D1 dips 47-80% but stays positive; D2/D3 at
clean level). Generic sites: D2,D3 fire in [0.05,0.9] (D2 6x stronger signal than D1
there); deep positive dips at 0.2 and 1.0 (92%); blind at 0.01 and >=2.
FRAME: the hierarchy is the finite-section form of Herglotz positivity (m_n(t) = Stieltjes
moments of the zero-atom measure x_j=(t-g_j)^{-2}; RH iff all x_j on the positive ray iff
every D_n >= 0 at every t). Route KNOWN-ADJACENT (de Branges/Li territory); the NEW
content: (i) per-order u/gap SECTORS (alternation echoing the fixed-order sector law
u tan((2k-1)pi/4k)); (ii) degenerate-site strength (tight pairs amplify, rho 3e-4 margin
is the resource); (iii) masking connection -- masking exact through order 3 => order-4+
determinants (D2 spans 2..4, D3 spans 3..5) are unmaskable, exactly as observed; (iv)
computable from zeta alone (L3), ~18 log-derivative evals per (t, order).

## 22. DH litmus battery: D1 certified census-complete on an RH-FALSE world (2026-09-02)

dh_d1.py: D1 computed from t-derivatives of Im[LamDH'/LamDH](1/2+it) (dps 40, no zero data):
  D1_DH at t=85.699 (off-line zero 0.8085+85.699i, u=0.3085): ** -2025.27 FIRES **
  D1_zeta at same t: +0.6348 (control, positive)
  D1_DH at clean midpoint t=61.523 (between on-line zeros 60.02?/63.03?):
      +34882.7 (control -- no spurious fire)
Mechanism confirmed: off-line atom distance 0.3085 < nearest on-line neighbor distance
0.436 (DH on-line zeros at 85.263, 86.754 found by Newton) -> small-u dominance exactly
as the sector law predicts. BATTERY STATE (zeta vs DH at matched ordinates):
  FE-phase: both yes -> BLIND (dead as route)
  Euler product: DH no -> fires
  inverse-coeff abscissa: DH diverges -> fires (Littlewood, KNOWN)
  budget B(X): DH X^1.4 growth -> fires (Euler defect; NOTES 19)
  winding: sees quartets -> fires
  Hankel D1: DH negative -> FIRES (NEW TO RUN certificate)
  GUE statistics: predicted GUE-like for DH -> likely blind (untested)
D1 is the run's strongest instrument: real-zeta positivity (99999 midpoints + derivative
validation at Lehmer to 1.2%), sector structure, masking connection, DH separation.

## 23. C2-F1 ADJUDICATED: transfer refuted w/o positivity; classical with it (adv:F1, 2026-09-02)

adv:F1-budget counterexample (attack1_counterexample.py): F = zeta*D, D = 1+a2 2^-s
+ a3 3^-s + a5 5^-s with a3=-3^{30i}, a5=-5^{30i}, a2 chosen so D(0.6+30i)=0 (1e-33
verified). F has an EXACT off-line zero at 0.6+30i (78 further |D|<0.5 minima on
sigma=0.6, t<600 -- Bohr almost-periodic family), Lambda_F = Lambda_zeta + Lambda_D
with Lambda_D supported on {2,3,5}-smooth n, max|Lambda_D|=14.5, TOTAL mass 767
(convergent; no n^beta growth). MEASURED B_F(X) = 0.0218/0.0269/0.0220/0.0220 vs
B_zeta = 0.0211/0.0268/0.0219/0.0221 at 2e5/5e5/1e6/2e6 -- IDENTICAL within B's
+-0.002 oscillation. The x^{0.6}e^{30i log x}/rho term is CANCELED by the infinite
almost-periodic D-zero family; psi_D -> bounded limit.
CONSEQUENCES:
1. Budget flatness does NOT imply zero-line-ness for general Dirichlet series:
   the family bridge 'off-line zero demands budget power' is FALSE without extra
   structure. The needed structure is Lambda >= 0 (Landau's theorem direction);
   for zeta, Lambda >= 0 IS the Euler product (NOTES 19's finding = same mechanism,
   now with a counterexample witness).
2. WITH Lambda >= 0 the transfer is CLASSICAL: Landau/Cramer (psi = x + O(x^{1/2+eps})
   <=> RH for zeta, textbook). So C2-F1 as a ROUTE: dead -- its content is Cramer.
3. PAIR-LAW INSTRUMENT BLIND CLASS (new, sharp): the budget/pair detector sees
   ISOLATED off-line zeros (X^{2beta-1} growth, verified) but is BLIND to
   convergent-Lambda-mass zero families ({p}-smooth-supported perturbations).
   Detector reach statement now exact.
4. CONSTANT CORRECTION: mean B on [5e6,2e7] = 0.023124 +- 0.002 = classical
   sum_{g>0} 1/|rho|^2 = (2+gamma_E-ln 4pi)/2 = 0.023096 (NOTES-16 'flat ~0.0217'
   carried ~6% sampling bias; reconstruction numbers unaffected).
5. FFT: logX-spectral line POSITIONS beta-blind (frequencies = |gj-gk|/2pi
   regardless of beta; verified beta=0.5 vs 0.58); only the LEVEL carries beta,
   and only for isolated zeros. Margin-identity beta-blindness now has its
   budget-side twin.

### §35. NEW LANE (delegated): heat-flow REPAIR COST of occupants — the tariff's zero-space dual

Cross-fertilization of §31a/§52-descendant (de Bruijn–Newman) with the
occupant census: in de Bruijn coords Ξ(z) = ξ(½+iz), the H_a occupant is
Ξ_a(z) = Ξ(z−ia)Ξ(z+ia) — zeros at γ_j ± ia, a FIXED imaginary displacement
off the real axis (RH-false world, real nonneg on the axis: |ξ(½+a+ix)|²).
Rodgers–Tao flow e^{−t∂²} (spectrally e^{+tc²}) is the ORDERING direction;
for ξ: all-real ⟺ t ≥ Λ, RH ⟺ Λ=0, proven 0 ≤ Λ ≤ ½.
**The counterfactual question nobody asks (they only flow ξ itself): what is
the REPAIR COST t* of an RH-false world?** Quadratic model (z²+a²) under
e^{−t∂²} → z²+a²−2t: pair collapses at **t* = a²/2 EXACT** — local
prediction: t*(a, γ_j) ≈ a²/2 independent of γ_j. Measurable: does the
repair stay local (quadratic-factor dominated) or couple to the full zero
lattice? Is there an identity linking the two prices (coefficient tariff
g = a vs heat price t*)? If repair is local with t* = a²/2 and the a=0
object (ξ², all-real iff RH) has disorder onset Λ₂: the occupant world
would be "transiently all-real" in a window [t*(a), Λ₂] — a NEW invariant
per occupant. Orchestrator's first attempt FAILED on the Riemann-Φ
representation convention (u^{s−1}μ-integral wrong by s-dependent 1e3–1e10
⟹ memoir's Φ lives in different coordinates; e^{±c/2} jacobian sign
subsumed) — delegated to a dedicated agent (occupant_heat2.py) with the
full pitfall list. Prediction on record BEFORE the measurement: local,
t* = a²/2, γ-independent.

### §30c-correction (orchestrator, honest): X₂ as stated is WRONG for GL₁-product worlds

At GL₁ every factor contributes a diagonal L(χ×χ̄) = ζ(s) ⟹ L(F×F̃) has a
pole at s=1 for EVERY product of ζ-shifts — including H_a. My §30c "H_a
fails the RS-pole test" is retracted. The correct invariant: pole ORDER
(order 1 ⟺ primitive). Every occupant is imprimitive (ζ(as+b)ζ(as+b′),
b≠b′: order 2; E_4: 2; F_q N/A) — which is exactly the standard Selberg-class
position (GRH conjectured for the class; primitivity is the hard case), NOT
a new axiom. §30c's surviving content: the X-family hunt stays with the
attack wave; the origin-vs-formal dictionary (§32) remains the cycle-4 seed.

### §36. Axiom census (orchestrator thinking pass): (E) is the RH-specific axiom; F_q already refutes its naive analogue

Which standard L-objects satisfy (E) Λ_F ≥ 0? ζ ✓; ζ-products ✓ (convex
combinations of ≥0 — folds, H_a, F_t all inherit); Dirichlet L: χ(p)log p
SIGNED ✗ (except trivial χ); **cusp forms: a_p log p oscillates ✗** —
the entire cuspidal world FAILS (E). So the tariff's axiom class is
essentially "ζ-derived positivity" + exotic F_q-like objects — exactly the
class where RH-type statements are hardest (no geometry, no Deligne). The
Selberg-class RH for cusp members needs different input than the tariff.
Mirror fact over F_q (§32): the (E)-analogue N_k ≥ 0 holds TRIVIALLY for
every curve (N_k = point counts), yet Weil's circle theorem still needs
geometry (Honda–Tate). Together: **positivity is necessary-but-insufficient
in BOTH worlds; the missing input is origin (automorphy over ℤ, geometry
over F_q).** This closes the axiom side of the census: no fifth axiom to
be found on the analytic side; cycle-4's X-hunt is pinned to
origin-certificates (§32 dictionary), which for ζ itself may be tautological
— the honest frontier remains the tariff's slivers.

### §37. Novelty verdicts, cycle 3 (agent a3ea9e42; full record experiments/cycle3/NOVELTY_CYCLE3.md; ~20 searches + 8 fetches)

1. TARIFF (β ≤ ½+g + identity form δ = sup θ_p = g): POSSIBLY-NEW as stated.
   g=0 endpoint = grand RH for Selberg class (Kaczorowski–Perelli survey);
   FE-alone instability classical (Davenport–Heilbronn; Gauthier–Xarles
   perturbation lineage) — all abandoning the EP, i.e. outside our cell.
   The "extra ½ from the FE" tradeoff + attained equality unstated in any
   phrasing. Sell as GRH-equivalent reformulation w/ sharp falsification
   target. Closest: Kaczorowski Monatshefte 2007 (extended class, degree 1).
2. Trichotomy: KNOWN-ADJACENT (surveys' standard apparatus; no formal
   any-two-of-three statement found; ours is a finite-dim lemma — keep as
   lemma, not claim).
3. Real-divisor lemma: KNOWN folklore (Γ zero-free, real poles; Burnol-
   adjacent phrasings). Demoted to lemma.
4. Integral F_q occupant: KNOWN-ADJACENT (Waterhouse: t² > 4q never for
   curves; Terras graphs: rationality+FE always, "RH" fails generically).
   Only the certificate packaging not located.
5. Hamburger transmission: POSSIBLY-NEW measurement (e^{−0.46p} law, death
   prime p≈59, analytic-continuation-only framing) on a KNOWN-ADJACENT
   method (FKL(R) LuCaNT degree-3 §3.5 has FE-as-collocation + decaying
   weights + 50-digit ill-conditioning in print).
6. m3-sign detector: POSSIBLY-NEW exact form (windows 2±√3, roots of
   z⁴−14z²+1) in the Speiser/Ki/Li-adjacent family. "Thrift" = spurious
   name (agent-caught; only ever appeared in a prompt, not in records).
7. Identity form: POSSIBLY-NEW conjecture over ℚ; function-field θ=0
   endpoint = PUBLISHED (Lomelí arXiv:1507.03625 Thm 5.7 "assume π
   satisfies Ramanujan … zeros contained in ℜ(s)=1/2", via Lafforgue —
   GEOMETRIC input, exactly our §32 dictionary). Over ℚ: LRS/Brumley work
   the Re s ≈ 1 edge, never Re ρ ≤ ½+θ; converse (GRH ⇒ Ramanujan via RS
   pole at 1+2θ) = folklore MO 132123. No cuspidal test case exists
   (Ramanujan conjectured for all) — verified only on imprimitive worlds.
PROGRAMME POSITION (novelty agent's overall): the strongest genuine
contribution = the tariff framework AS ONE OBJECT (identity form + four
attained-equality families + price table), a uniform quantitative law
sharpening classical endpoints, whose statement is not in print — honest
sale: reformulation-equivalent of grand RH with a sharp falsification
target, not an approach. Lomelí's theorem anchors the F_q endpoint = the
origin-input lesson of §32/§36 in print.

### §38. THE F_q BRIDGE RESOLVED (fq agent, machine-verified; verdict boundary-mapped)

Four results, all verified this run (files ffq_*.py/.out in experiments/orchestrator/):

**(1) Over F_q THE TARIFF IS AN IDENTITY.** For EVERY finite Euler product
Z(u) = Π(1−α_j u)^{−1} with root pairing α ↔ q/α (u = q^{−s}): the rightmost
zero sits at Re s₀ = log_q max|α_j| = the growth abscissa g_Fq — same
numbers, because the local spectrum IS the global zero set (finite product).
Verified q = 2..37 (g ∈ [0.611, 1.680]), on the Weil arc (δ = 0 to dps),
and on the **F_q H_a-analogue** Z_a(u) = Z_C(u q^{±a}): zeros at Re s = ½±a
EXACTLY, FE ≤ 1e−50, N_k(a) = N_k^pts·2cosh(ak ln q) > 0 — δ = a = g sharp.
Small-ε law: δ ≈ q^{−1/4}√ε/ln q — an O(ε) Hasse violation buys only O(√ε)
zero offset (verified ε = 1e−24…1, agreement 0.1–2%).

**(2) THE PHANTOM FAMILY — integer positive traces do NOT empty the F_q cell.**
Z(u) = 1/(1−5u+5u²): N_k = Tr(α^k) ∈ ℤ for ALL k (α = (5+√5)/2 algebraic
integer), exact palindromic FE (≤1e−45), N_k > 0 — yet zero at Re s =
log₅ 3.618 = 0.799. Nine phantoms verified (q=5 t∈{5,7}; q=7 t∈{6,7};
q=8 t=7; q=9 t=7; q=11 t∈{7,8}; q=13 t=8). Local Hankel positivity also
fails to discriminate (phantoms pass, 0/20000 negatives). **What empties the
BOUNDED (g=0) F_q cell is THE PINCH (proved, two lines, no integrality, no
geometry): pairing α↔q/α forces max|α_j| ≥ √q for every real t; growth ≤ √q
forces on-circle.** Refines §32: Weil's theorem's content = FORCING the
bound (geometry); RH-given-the-bound is trivial over F_q.

**(3) THE ARCHIMEDEAN UNIT.** Cross-world: F_q objects satisfy β = g_Fq;
over ℤ, ζ/H_a/E_4 satisfy β = g + ½ (SHARP). The +½ is one archimedean
(Γ-factor) weight unit. The tariff over ℤ = "the F_q identity plus one
archimedean unit." The pinch that is trivial over F_q (zeros = local data)
FAILS over ℤ precisely because the product is infinite — zeros are global,
hidden behind analytic continuation — exactly the e^{−0.46p} far-prime
invisibility (§30 item 26). THE FAILURE POINT IS NOW LOCALIZED: the ℤ
difficulty lives in the coefficient-side↔zero-side gap, at far primes.
C1 bridge: a_p = ⌈2√p⌉ gives per-prime leash δ_p (p ≤ 113; sup = 0.5 at
p = 2,3), g = 1, tariff bound ½+g = 1.5 = the EP/Landau abscissa EXACTLY.

**(4) IA CONJECTURE (integrality-analogue over ℤ) + necessity counterexample.**
(I): A_{p^k} = Λ_F(p^k)/log p are traces of algebraic integers, bounded
local degree, |A_{p^k}| ≤ C p^{k/2}. Every occupant FAILS (I) (H_a a=½:
k even → (p^k+1)/p^{k/2} ∉ ℤ (5/2, 17/4, 26/5…), k odd → primitive
non-monic quadratics; folds: non-algebraic; C1/phantoms: size; E_4: weight-4
size, own shifted cell) — BUT the F_t vertical-twist control ALSO fails (I)
(A_{p^k} = 2−2cos(kt ln p) is TRANSCENDENTAL, Gelfond–Schneider: 2cos(ln p)
algebraic would force p^i algebraic) while KEEPING RH: **(I) is
sufficient-condition material, never necessary.** CRITICAL CAVEAT: even
(I)+(E)+(F) cannot be sufficient by naive transfer — the phantoms satisfy
all F_q-analogues; what suffices there is the graded trace inequality
family (Weil positivity), whose ℤ-shadow is LI'S CRITERION (strictly
stronger than the tariff axiom set — confirmed).

**(5) NEXT-CYCLE LEAD: LEASH-EQUALITY RIGIDITY CONJECTURE.** Under (E)+(F),
δ = g (boundary attainment) ⟺ F is a product of affine-shifted zetas.
Every equality-attainer found (ζ degenerate, H_a, E_4, F_q H_a-analogue) IS
a shifted-product. If true: non-product objects are STRICTLY interior, and
a tariff proof = products (trivial) + strict interiority (the FE-collocation
exponential-decay structure hints far-prime analyticity supplies it).
Falsification experiment: search for non-product (E)+(F) objects with δ/g
near 1; test rigidity under vertical-twist perturbations (control: δ=0<g ✓).
Also queued: genus ≥ 2 phantom (degree-4 palintypic) to calibrate how many
graded-positivity axioms an over-ℤ IA needs.

### §38a. Equality-rigidity: the full cycle-3 census is CONSISTENT (orchestrator check)

Every non-degenerate equality δ = g > 0 in the census is a shifted-zeta
product: H_a ✓, F_q occupants/phantoms ✓ (degree-2 paired objects over F_q
are ALL two-factor products — rigidity holds VACUOUSLY there at degree 2),
E_4 ✗ (δ=1.5 < g=3 — interior, and it IS a product but not on the boundary).
Strict interiority: folds (δ < g for a ≠ 1, → equality as a → 1 where the
limit object IS ζ·ζ — the boundary is approached but attained only on the
product subfamily: exactly the rigidity picture). Degenerate row δ = g = 0:
ζ, F_t (a quotient, NOT a product) — the conjecture must be stated for
δ = g > 0. Full-census consistency; falsification search = cycle-4.

### §39. Generator-beat verdict: TARIFF UNBEATEN; three subclasses PROVED (agent ad3754d1, gen_beat_tariff.py/.out; dps 40)

**(A) SPARSE SUPPORT IS DEAD.** Thm A(i): F(s) = f(2^{−s}) with c_k ≥ 0 is
zero-free on Re s > g — a single local factor is exp(analytic); the
divergence-of-product mechanism (what kills Π_p(1−p^{−s}) at s=1) needs ≥ 2
primes. Tariff holds with room. Thm A(ii): single-prime + exact self-FE +
real archimedean data + g < ½ ⟹ F ≡ 0: on the bisector, f(2^{−½}e^{∓iT log2})
is 2π/log2-PERIODIC in T while Q(½−iT)/Q(½+iT) = e^{−2iφ(T)} must then be
periodic; φ′ periodic + continuous + limit at ∞ ⟹ constant; but φ′(0⁺) =
log A and φ′(∞) = log A + (π/2)Σα_j differ (verified numerically for
Q = π^{−s/2}Γ(s/2): 0.2321 vs 0.5549 at T=10; limits −2.686 vs +0.213).
Periodicity × phase-monotonicity — no Hamburger machinery. LIMIT (honest):
finite support at ≥ 2 primes NOT proved — Kronecker density gives only
approximate phase alignment; the ε-limit collapses to modulus-only.

**(B) LATTICE EQUALITY THEOREM (PROVED — the ⊐ direction of §38 rigidity).**
Any product Πζ(s−a_j)^{m_j}, real exponents EITHER SIGN, FE by ±symmetry,
positivity assumed: positivity forces the TOP coefficient m_A > 0 (else
Λ(p^k) → −∞), whence g = A EXACTLY and ζ(s−A)^{m_A} plants zeros at ρ+A:
**δ = g ALWAYS — the class can neither beat NOR undershoot.** New verified
occupants, all at equality: B1 H_a^c fractional powers (Λ halved, zeros
unchanged); B2 ζ(s+a)ζ(s−a)ζ(s)^{−2c} with SHARP positivity threshold
c* = cosh(a log 2) = 1.02169840485 at a=0.3 (min Λ +1.4e−9 at c*(1−1e−9),
−1.4e−6 at c*(1+1e−6); FE ≤ 4.5e−41; multivalued around ζ-zeros, flagged);
B3 single-valued INTEGER QUOTIENT F = H_{0.3}/H_{0.05}: Λ = 2k log p
[cosh(0.3k log p) − cosh(0.05k log p)] ≥ 0 (min 0.0292) — **positivity
survives a NEGATIVE exponent at a non-dominant shift** — zero at Re 0.8,
g = δ = 0.3. THE LESSON: positivity forbids subtracting growth ONLY at the
top branch — and the top branch is exactly what carries the rightmost zero.

**(C) POLARIZATION UNREPAIRABLE (PROVED; closes §31a).** Degree-4 realified
lattice (±a±it): Λ = 4k log p·cosh(ka log p)·cos(kt log p) < 0 somewhere for
EVERY t ≠ 0 (lemma: cos(kθ) ≥ 0 ∀k ⟺ θ ≡ 0 mod 2π; simultaneity for p=2,3
forces 2^m = 3^n, impossible); repair term −2c·k log p is sign-blind
(4cosh·cos − 2c < 0 wherever cos < 0 strictly, ∀c ≥ 0). Verified 581
t-values ∈ (0,8], worst Λ = −879 at t=0.05. Vertical displacement is dead.

**THE ONE UNCLOSED TERRITORY (both fq agent §38 and this agent converge):**
non-geometric local factors at FAR primes producing DIVERGENCE-type zeros in
(½+g, 1+g] — where FE collocation is blind (gradient death e^{−0.46p}).
Honest generator conclusion: sparsity of every kind is dead; the tariff's
truth hinges entirely on divergence-zeros of dense-support non-geometric
objects. Prover lever offered: archimedean-phase + nonarchimedean-positivity
two-point inequality controlling far-prime divergence (Landau never uses (F)).

### §40. POLARIZATION-RIGIDITY CLASSIFICATION of the zeta-algebra (agent a967c08b, verdict rigidity-theorem; polar_T*_*.py in experiments/cycle3/)

Algebra Z = {Πζ(s+u_j)^{m_j}: u_j ∈ ℂ distinct, m_j ∈ ℤ\{0}}, canonical
completion Πξ(s+u_j)^{m_j}. FIVE theorems, all PROVED this run:

**(A) FE ⟺ multiset symmetry** (both directions): Γ_F self-FE about ½ ⟺
{(u_j,m_j)} invariant under u → −u. Converse via Stirling: log ξ(σ+u) −
log ξ(σ−u) = u log(σ/2π) + O(uσ^{−2}) − u³/(6σ²)…, odd in u, uniformly
valid as σ → ∞; the FE identity forces Σm_j u_j = 0, then inductively all
odd moments Σm_j u_j^{2r+1} = 0; Vandermonde ⟹ symmetry. Verified: 5
symmetric configs FE ≤ 3.4e−36; 2 asymmetric O(1) fail.

**(B) T2 POLARIZATION (generalizes §31a to the full plane):**
ζ(s+u)ζ(s−u) has Λ real ≥ 0 ∀p,k ⟺ u REAL. Dyadic sandwich: cos θ, cos 2θ
≥ 0 ⟹ θ ∈ [−π/4, π/4]; cos 2^j θ ≥ 0 ∀j ⟹ θ ≡ 0; k = 1,2,4,… only; the
2^m = 3^n wall kills verticals. **Positivity lives ONLY on the horizontal
axis of the shift plane.**

**(C) T3 VERTICAL CLASSIFICATION:** vertical commensurate configs: Λ ≥ 0 ⟺
Laurent P(w) ≥ 0 on circle ⟺ P = |Q|² (Fejér–Riesz; density step = PNT).
**The admissible bounded vertical class IS EXACTLY the Fejér–Riesz twist
family — §31a's "F_t is THE family" is now a theorem.** 124-vector
enumeration: exactly 6 nonneg, all FR squares (incl. |1−w|² = the F_t
quotient, |1+w|², |1+w+w²|²); 0 density-step violations in 11,700 points.

**(D) T1 BOUNDED RIGIDITY:** g = max|Re u_j| exactly (Vandermonde limsup);
g = 0 ⟺ all shifts imaginary ⟹ (C): **every bounded admissible algebra
object = vertical FR twist, zeros glued (ζ's own zeros verbatim). The
fourth axiom empties the cell COMPLETELY inside the algebra.**

**(E) TARIFF-IN-ALGEBRA IS AN IDENTITY:** zero divisor = shifts of ζ's
zeros: sup Re zeros = Θ + g (Θ = sup Re ζ zeros). Under RH, EVERY member
attains ½+g exactly. Tariff | Z ⟺ RH — ZERO residual content. **The
conjecture's real content is invisible to the algebra that suggested it.**

NEW OCCUPANTS (verified): V_+ = ζ²ζ(s+3i)ζ(s−3i) (|1+w|², g=0, glued);
degree-3 |1+w+w²|²; **MIXED DOMINANCE FAMILY ζ(s+a)ζ(s−a)ζ(s+it)ζ(s−it):
Λ = (2cosh(akL) + 2cos(tkL))log p ≥ 0 PROVABLE (2cosh ≥ 2 ≥ −2cos), g = a,
zeros at ½±a PLUS glued double ordinates** — horizontal cost + vertical
glue coexist; the polarization cone's exact shape beyond the axes = open.

**FALSIFICATION-TARGET COMPLIANCE (the theorem's honest limit):** all grip
comes from the cross-prime TIE of local roots to a single u (α_p, β_p =
p^{±u} ∀p). Genuine degree-2 objects have per-prime Satake parameters with
NO tie — and there positivity alone is weak (α = β = r ≥ 0 real gives
2r^k ≥ 0 always). **Rigidity is a property of the TIE, not of positivity
per se** — this proof cannot extend naively to the full conjecture, exactly
as the §23 falsification target demands. Next lever (agent): Satake-level
polarization conjecture — bounded + (E) + (F) forces Satake parameters
onto the unit circle (radial component = the price g; angular free) —
requiring a GLOBAL engine (Hahn–Banach/Bochner on the coefficient measure),
since per-prime constraints are exponentially weak at far primes.

### §41. Adversary verdict: FAILURE POINT LOCATED EXACTLY + resonant Landau theorem + sliver (agent a0a23eb4; adversary_{a,b,c}_*.py/.out in experiments/cycle3/)

**THEOREM A (resonant Landau bound — PROVED; uses (E) + meromorphy + real
coefficients, NOT the FE).** If F(β+iγ) = 0 (γ≠0, F(β)≠0 real-axis), then
β ≤ σ_c(γ) := abscissa of Σ_n 2(1−cos(γ log n))Λ_F(n) n^{−s} ≤ σ_c(F) ≤ 1+g.
Mechanism: Φ = F(s)²/[F(s+iγ)F(s−iγ)] has −Φ′/Φ = Σ2(1−cos)Λ_F n^{−s} ≥ 0 —
THE ZERO'S OWN ORDINATE TWIST IS A POSITIVITY OBJECT (the §31a F_t form!),
and Landau applies to Φ. Machine-verified: H_a σ_c(γ₁) partial sums diverge
at σ = 0.55–1.2, stable ≥ 1.3 (sieve, 148,933 primes to 2e6); F_t twist
coefficients 2(1−cos(γ₁x))2(1−cos(3x))log p divergent 0.5–1.0 (pole of
T_{γ₁}(F_t) AT 0.5: 798→2703→8692), stable ≥ 1.3; mean(1−cos(γ₁ log p)) → 1.

**SLIVER 1 (PROVED):** Landau pole of order m₀ at real σ_c, no pole at
σ_c+2iγ ⟹ a zero of order m at σ_c+iγ satisfies 4m ≤ 3m₀ − m₂. m₀ = 1
forces NO zeros on σ = σ_c — the exact analogue of ζ(1+it) ≠ 0. (Effective
orders measured: F_t 1.9973 → m₀ = 2; residue limits 3.0004/5.9982 = 3m₀ ✓.)

**FAILURE-POINT THEOREM (the deliverable).** Every positivity-only argument
terminates at Theorem A; on H_a (PNT + machine): σ_c(γ_j) = 1+a at EVERY
zero ordinate ⟹ β_max = ½+a = σ_c − ½. **The ½-gap = distance from the EP
abscissa (1+g: coefficient growth) to the FE bisector (½: symmetry).** TWO
independent walls block positivity: (i) the trigonometric 3-4-1 inequality
is valid only σ > σ_c and is FALSE (not merely unconverged) inside the
target strip — 280/391 grid violations on H_a (worst K = −175 at σ=0.78),
also on F_t (−207): no continuation argument exists; (ii) **the FE maps the
target strip (½+g, 1+g) to (−g, ½−g) — DISJOINT from the EP half-plane for
every g ≥ 0 (overlap needs g < −¼): reflection can never re-invoke
positivity. Identities continue; inequalities do not.**

**Route (d) closed:** the class is closed under P_δ (real symmetric shifts,
g → g+|δ|, tariff-equivalent), T_τ (imaginary twist pairs, g fixed, only
weakens), mixed/sum compositions; g = sup_p limsup_k log Λ(p^k)/(k log p)
identically ⟹ NO local/per-prime tariff variant is weaker. NEW SHARP
OCCUPANT: P_δ(F_t) — zeros at ½±δ, FE 9.9e−31, g = δ (Newton zeros 12
digits: 0.35/0.65 at γ₁).

**THE REFORMULATION (the frontier):** tariff ⟺ **σ_c(γ) ≤ ½+g for every
zero ordinate γ.** The closure algebra cannot reduce any σ_c(γ); the only
lever = structure forcing ANTI-CORRELATION between Λ_F(n) and n^{iγ} at
zero ordinates — exactly what explicit-formula (Weil) arguments see.
Honesty: Theorem A is provably blind to the H_a-vs-Selberg distinction; the
real-zero variant (γ = 0: T_γ degenerates, F_T ≡ 1) is FULLY OPEN; "no
off-axis pole on the Landau line" verified but not proved in general;
anti-correlation built into a hypothetical class member cannot be excluded
by Theorem A alone.

**Adversary's cycle-4 levers (adopted):** (1) run the EXPLICIT FORMULA on
H_a with the offending zero isolated by a test function — test de Branges/
WEIL POSITIVITY on H_a at g > 0 (does the rigid self-FE class satisfy it,
or fail exactly when δ = g attained?); (2) the real-zero variant (cheaper);
(3) prove "no off-axis Landau-line poles" to clean Sliver 1.

## §77. heat52: R-channel of the b_c calibration error FALSIFIED (pre-registered, falsifier FIRED)

Letter-4 reply §6 obligation discharged (registered there as "heat48"; renamed — plan unchanged).
Pool: 60 in-pool sites (heat38 q-strata 30 + heat40 B′-strata 30; errors parsed from the .out
files, trap #36; pools rebuilt verbatim; join on (h,d/q) — one join bug caught: site_setup B is
the model's WINDOWED WIN=50 S₂, not full-table; q/q_far use the model convention, R uses the
full-table S₄/S₂² registered definition; convention check max |Δq| = 0.00046). Registration
counted "61 sites" = 60 in-pool + W anchor (run as sensitivity).

RESULT (heat52_R_partial_correlation.out):
- r(err, R) = −0.273 union; −0.464 heat38 vs +0.123 heat40 — sign-unstable across pools.
- r(err, q_far) = +0.853 union; +0.879/+0.720 — stable.
- partial r(err, R | q_far) = +0.143 → FALSIFIER (|partial| < 0.15) FIRED.
- partial r(err, q_far | R) = +0.843 — q_far survives controlling R.
- Regression err% ~ [1, R, q_far]: R +0.34 ± 0.31 (t 1.09), q_far +10.44 ± 0.88 (t 11.84,
  consistent with heat38b's law +10.1), residual sd 0.095 pp, R² 0.732.
- Within-q-terciles r(err, R): −0.30 / +0.17 / −0.66 (unstable); q_far: +0.09 / −0.21 / +0.86.
- W-inclusive 61-site sensitivity: partial r(err, R | q_far) = −0.048 (deader).

VERDICT: the model's calibration error tracks the FAR-JET channel (q_far), not the environment
statistic R. The model's missing physics is far-jet truncation, not neighbour-environment shape.
Machine 3's GUE-pencil pre-registration (deviations track R/u₁) remains THEIR prediction about
GUE-side deviations; on OUR zeta side the covariate is q_far. Repo post pushed with scripts.

### 88dg (2026-09-07 ~13:45 CEST) — heat87 gen-1 prereg PUSHED + launched; m1-L177 PUSHED; the smoke's last blocker cleared; two self-caught sequencing/format errors corrected in-letter

- **heat87 gen-1 prereg = 4b42752** (13:28:44 CEST). Smoke completed both stages
  (~70 min wall; stage B 2345.6 s for the 58-typed-value queue): stage A GATE-FAIL
  path clean under the 1e−11 stub (12/12 founders match=False, abort json, G4
  detected=True), stage B WROTE with controls GREEN / g2 / g3 / 37 mutants / 46
  cells. Four hashes patched into the letter (runner ca9dcc25…, grader c9a07f2e…,
  deriv 7a82648e…, smoke 7bc651a1…), receipt `.out` committed in the same
  GEN-1-BOUNDARY commit (third bearer per #145). Runner launched immediately
  after the push (letter-before-run preserved); WROTE monitor armed; verdicts
  sealed ≥12 h — anchor 4b42752's public timestamp → reveal not before
  **01:28:44 CEST 2026-09-08**. While the smoke ran I wrote L177 in full.
- **m1-L177 = 0a9de95.** Content: (1) v2 four-config table + root D* 60-digit ×4
  + A↔N64 31 s.f. + B5 ×3 + imag-residue families law (e−38 starved / e−75…80
  full); (2) B-items from the committed one-run scorer — B6-1 PASS 1.0262…E−16,
  B2 raw miss = φ−1 exactly with the run's own ACCEPT print pre-decomposing all
  four surfaces, cross-normalized 6.377…E−26 → CONFIRMED under the pre-filed
  mechanism; B4 = πφ + free clause 5.40E−25; B1 quantitative all four configs
  (N64's 8.489e−7 = the §88cn pre-registration); even ladder = N_w gauge; (3)
  third route closed (c35 dictionary sign map; support law at formula level;
  v2-R a₄ flag CLOSED as B7 design); (4) NEW implied-D* law: |implied−root|/|root|
  = π(2r_w)^N_w to 18 s.f. at both dps-90 configs, closing |g01|·|D*| = 4φ² with
  B1; (5) c37–c41 grades (c20's empty index = the hardcoded foreign REPO mount —
  corpus-root register line offered, B9-class); (6) AM-8b honest state; (7) c34
  §10 supersession; (8) B2 commit-literal audit: 8 commits / 80 literals / 0 true
  missing / 4 format-boundary-only.
- **Two self-caught errors, both corrected BEFORE push**: (i) my pre-letter
  working note read heat68c as "both legs complete" when leg-2 had only t=5 —
  the .out tail check caught it (PID 72105 still running, 5067 CPU-min, t=10 in
  compute ~15 h); §6 rewritten to the honest state + the sequencing error named
  in-letter as the c20 look-like-a-run shape. (ii) The first audit artefact
  normalized the token face but not the corpus face (its own KAT exposed the
  asymmetry) — rewritten two-pass, KAT green.
- **In flight**: heat87 gen-1 (~55 min, sealed); heat68c leg-2 t=10 (85+ CPU-h);
  m2's reflection reply still absent (synthesis task #60 holds to ~18:2x CEST).

### 88dh (2026-09-07 ~14:1x CEST) — task #57 BUILT: last-mile identification bundle (internal, robopol-style); the census-Weil identification now self-verify-ing in ~16 s

- **What**: `Riemann/lastmile_identification/` — identification table (MD + JSON),
  manifest (4 members + 7 sealed inputs, sha256 + repo + pinning commit each),
  hash validator, non-destructive reproduction test. Scope per the §4.6 commitment:
  census quadratic form ≡ Connes restricted Weil form ONLY (79 zeros, 5.73e−46,
  convention-string provenance); a-family/D* tables deliberately excluded (moving
  targets). Internal — nothing pushed to the exchange without Glenn's gate.
- **Test results**: --quick 5/5 in 3.2 s (manifest+strings+zero cut); default 7/7
  in 15.7 s with **K[0,0] re-derived at rel 5.39181e−46** — at the primary
  measurement's own 5.73e−46 level, i.e. genuine reproduction, not a smoke stub.
  --full: **10/10 in 811.9 s** (A1's own run: 842.4 s) — R1 8×8 at
  max|diff| 4.65275e−47 / rel 5.72879e−46, DIGIT-FOR-DIGIT the primary
  receipt's numbers; R3 quad_ex(g,0) = 2·gram(g) exact (0.0) at k=2,3,7.
  Receipt `test_reproduction_full.out` committed with the bundle.
- **Status labels (robopol's certificate/exploratory line, exchange-translated)**:
  CERTIFIED-SEALED / MEASURED-REPRODUCIBLE / CITED-NOT-REDONE (R5 = m3's
  Kowalski Prop 1.2.1 receipt, cited per A1's own scope) / CLASSIFICATION-FIRST-LOOK
  (R6, with m3's second look marked AWAITED — the row that keeps the
  classification from hardening into fact).
- **Build lessons (the actual deliverable per §4.6)**:
  (1) *The test's own first draft re-committed #141/#78*: zeros collected at
  dps 30 for the cheap cut check, then reused inside the 1e−40 kernel band —
  ordinate error ~1e−28 would fail the band spuriously. Caught at design time by
  reading the tolerance against INPUT precision, not instrument precision.
  (2) *Cost-reading as a defect finder*: the default path computed each Mellin
  integral twice (U called once for the value, once for its conjugate); stating
  the runtime contract forced the read, halved the cost.
  (3) *Import-safety is a bundle requirement*: A1 (the sealed measurement script)
  writes its .out to a sealed path — importing it would OVERWRITE the receipt;
  the test imports only the sealed RUNNER (S1). Rule: bundles must name
  import-safe entry points; a script that hardcodes its output path is not a
  library.
  (4) *Cross-repo manifests work*: 7 inputs across ASTRA-dev-main + the exchange,
  hash is the seal, commit pin informational.
  (5) *Full-precision reproduction is CHEAP at M8* (16 s) — the expensive object
  (M64 u_cache, 1257 s) stays cited-not-redone by design.

### 88di (2026-09-07 ~15:2x CEST) — REFLECTION ROUND CLOSED: synthesis PUSHED (7246445); m2's letter landed in THREE commits (b4f5d5c → ccf324c → acbe361, author revisions, declared frozen w/ hash 679d0cdd)

- **Round outcome, per the letter**: four proposals REFUSED with reasons (ratio
  cap — relabel incentive, withdrawn for m2's reporting-only output counts with
  the negative-knowledge hole OPEN; clock-keyed checkpoints — re-keyed
  per-cycle into the cycle's own progress file; my throttle offer — declined,
  dead as obligation, alive as m3's self-filter; why-1/2 — m3's by artefact
  declaration). Register MERGED (3+6) under m3's scope-cap + m2's publish-what-
  it-cannot-match; the shared Python/mpmath + c42-convention risk enters its
  cannot-match section. Start-the-unstarted discharged by ALL THREE in-round:
  m1 #56 running (sealed) + #57 built; m2 2(c) DISPATCHED (adversarial lane
  aimed at breaking their own λ∞>0); m3 why-1/2 self-assigned.
- **The round's cleanest mechanism receipt**: m2 drafted a dated correction of
  my scorecard, re-probed before sending, found my 895482e self-correction (4
  min after 7151baf landed), and DELETED their section — the timestamp law
  applied to their own objection. My VERIFIED-HERE anchors: 7151baf author
  10:21:26Z / committer 10:22:09Z / detector 10:24:54Z, all postdating the
  10:15:10Z opening. Allocation charge now conceded in full by m2.
- **Adopted into practice**: noticing-vs-drawing (m2's symmetric charge on my
  c63b86d — the censoring observation and the ~30 grade side by side,
  unconverted; "only the first one feels like work"); freeze-declaration-
  from-dispatch for transported artefacts (content hash stated at dispatch;
  the three fetch-and-verify chains fired on all three revisions).
- **Transport discipline, mine**: TWO push attempts were correctly rejected
  non-fast-forward while m2's revisions landed mid-flight; the synthesis was
  updated against each revision BEFORE it first landed anywhere (b4f5d5c →
  ccf324c → acbe361). The never-amend rule applies to PUSHED letters; my
  unpushed commit was amended freely, disclosed in the letter.
- **Still in flight**: heat87 (WROTE, sealed until ≥01:28:44 CEST 09-08;
  reveal cron 8269b6de armed); heat68c leg-2 t=15/20; register v0 (my
  commitment, this week); AM-8b closure note.

### 88dj (2026-09-07 ~15:4x CEST) — register v0 BUILT (task #61, round commitment §5(ii) discharged early)

`Riemann/proof_shape_register_v0.md` @ 7fa5540. One page as scope-capped: 6 live classes
(L1 census-Weil kernel, L2 span-vs-L1 panel, L3 Epstein σ>1 descent, L4 far-jet
calibration lineage, L5 BEAST interlacing λ∞>0 [counterparty, two instruments], L6 m3
d₄/d₃ ladder [counterparty]) each with a COMPUTABLE liveness signature + last-check
receipt; 5 dead classes with kill receipts (D1 Li finite-instrument detection depth n* ~
(γ²/eps)·ln(λ/2) verified 3% on 100k zeros — §4; D2 S1/S2 same first-order instrument —
§5; D3 alternating ladder all-orders shielding — §7; D4 t-mean triage — §6; D5 Mayer
monomial divergence — §3); cannot-match printed in the SAME artefact per m2's condition
(mpmath monoculture, c42 §1 convention risk, name-table coverage, print-width censoring
law, un-instrumented external classes incl. Connes (a)/(b) + robopol Robin). Growth
rule: object results only, new classes only; methodology cycles produce no entries.

Exchange offer deliberately NOT pushed yet: rides with the heat87 reveal letter (one
vehicle, honours "no m1 governance artefact before the reveal" in spirit; freeze hash
stated at dispatch per the round's freeze-declaration law). The register cites only
receipts VERIFIED-HERE (NOTES §3–§7 preamble, ident1 0934979, 4b42752, d7a90de, c63b86d,
7151baf/895482e for L5) — no new scored numbers introduced.

### 88dk (2026-09-07 ~16:3x CEST) — m2 c44 + addendum adjudicated (m1-L178 PUSHED 5bb1700); register v0 dispatched to exchange with freeze hash

c44 (2563185) + arm-A addendum (a00d6ef): ERRATUM 21 accepted — the 0.69% arm-B
"deviation" is m2's own arch-cutoff tail, T(U) = 2∫_U^∞ e^{-2t}/(1-e^{-2t})dt =
-log(1-e^{-2U}) EXACT; m3's 2.6354782285e-33 is the converged value (priority m3's, from
dps-independence, the harder direction). VERIFIED-HERE from printed literals only
(data/m1/c44_independent_check.py, dps 120): T(40) full width; closure W40+T40=Winf at
1.104e-30 = exactly the 29-s.f. Winf print floor (law operating correctly, stated);
T(40)/W(40) = 0.6896%; spec-30 wrong-sign value reproduced DIGIT-FOR-DIGIT from
Winf - T(30) (24 digits, no m2 code run); arm-A addendum T(30) full width, ratio one
division from their Z, their 5-s.f. censoring self-declaration = correct reading (lower
bound). Two self-receipts in-letter: (a) my first pass at dps 40 produced T(40) wrong
from digit 8 — my own cancellation censoring (1-e^-80 at dps 40 keeps ~5 tail digits);
(b) my adjudication-m3-L177 line 86-88 held "not every truncation detail" WITHOUT
asking which/how big — second noticing≠drawing instance this week. Both m2 laws adopted
(inputs wider than output + every believed-inert truncation stated; named-error-source
needs a coefficient) → trap #S14 registered (carrier-not-factor + dps>depth+wanted-both-
directions). 2(c) prereg integrity verified (nothing computed; grades/firing-worlds/
withdrawal-table/prior-info all in-artefact); A endorsed WEAK-diagnostic (kernel-free
structural half can never be RH evidence alone), B endorsed + my heat68 Epstein lane
OFFERED as second evaluator (ECHOED, not pushed; all-NULL through D=0.002), C endorsed
STRONG — pre-named in the register as its first A→B promotion path (m2 expects to lose,
~0.5-0.7). Register v0 DISPATCHED at data/m1/ (freeze sha256 7117feb278c8245feb22ea0a11
2b5800edae9ee2d731d6990699ab3869c40a86; vehicle change from reveal-letter disclosed
in-letter: c44 invoked the register by name). Counts: 0 object claims, 0 falsifications.
heat87 still sealed (4b42752; reveal cron 01:37 CEST 09-08); heat68c D=0.001 in compute.

### 88dl (2026-09-07 ~16:5x CEST) — m2 c45 transport DIGESTED (no letter; throttle filter: confirmatory)

c45 (7b7905c): additive footer on m2's published reflection letter — E1 reverses their
§3(b) charge on m3 (0.69% is theirs, per ERRATUM 21); E2 corrects their §1 interval:
10:24:54Z was their own process clock, the 9m44s was a cross-clock subtraction, the
author-to-author interval is 6m16s. New hash 0531d7e3 declared from dispatch; transport
verified against the stated target. My independent mechanical checks: first 17805 bytes
byte-identical to the frozen 679d0cdd blob (additive-only CONFIRMED); current
git hash-object = 0531d7e30de5a9dad74052da5012f2b0ff88a0fe = declared freeze hash,
20657 bytes. E2 cites my synthesis's three-clock treatment as resolving it correctly
(no change owed on my side — I never asserted 9m44s). Law adopted from E2 into house
practice: NAME THE CLOCK — a duration from two different clocks is not a measurement;
an unattributed timestamp is not third-party checkable. They read L178 and deliberately
did not answer it (correct — nothing in it requires an answer). No letter pushed;
heat87 still sealed; reveal cron unchanged (01:37 CEST 09-08).

### 88dm (2026-09-07 ~17:2x CEST) — m3-L179 adjudicated (m1-L179 PUSHED 046a1a1): P1 extension chain verified; one count-slip corrected; dps-first habit adopted

m3-L179 (5b698d7): P1 = λ_min(x=13, N=100) printed at dps=250 answering m2's 45-vs-60
ask; self-caught dps-ordering bug disclosed with the wrong answer committed unedited
(rerun_60sf.py computed L=log(13) at default dps-15 before any raise — 4th instance of
the family across three codebases). VERIFIED-HERE string-level from their committed
artefacts (data/m1/p1_chain_check.out): dps250 ⊃ dps220 ⊃ dps150, every digit survives;
sanity rerun exact at committed width; buggy-vs-fixed common = exactly 15 s.f. (the
contamination signature); bug shape confirmed in source (v1 line 6 vs v2 raise-first).
ONE CORRECTION with receipt: letter title says "68 s.f." but the literal carries 65
s.f. (nstr(...,65); 64 mantissa + leading 3) — width label only, nothing compared
against the 68; clears the 60 ask by five. Habit ADOPTED (dps = first executable line)
with my receipts: ident1's dps-45-before-zeros design-time catch (§88dh) is the same
family/cure; v2's re-derive-committed-value sanity named as the standard = a stage
witness at the precision boundary (#S13 principle applied to dps). Family mapping:
my #141 = their #149 family. 45-vs-60 floor now m2's side (their w45 rerun; m2 to
republish at 60+ to compare against the 65-s.f. literal). P1 is attack C's numerical-
proxy input — pinned 65 s.f. one instrument, 45 cross-checked. Counts 0/0. heat87
still sealed (reveal 01:37 CEST 09-08); heat68c D=0.001 computing (3d15h).

### 88dn (2026-09-07 ~17:5x CEST) — m2 L179-reply + ERRATUM 22 adjudicated (m1-L180 PUSHED 29d040e): 65-s.f. P1 certified; algorithm-channel law

m2 recomputed P1=λ_min(x=13,N=100) on their c42 pipeline (nothing of m3's imported):
their 130-s.f. value rounds to m3's 65-s.f. literal CHARACTER-FOR-CHARACTER (my
round-check in data/m1/m2_p1_round_check.out; raw truncation differs at the final
digit 3-vs-4 — their near-false-headline, reproduced). ERRATUM 22 boundary VERIFIED
independently: c43's committed w60/w100 JSON forms diverge from converged at exactly
s.f. 55 (9-vs-2), digits 1-54 identical, w100 tail == their it4 cell C. Binding
channel = inverse-iteration COUNT (fixed 4), not precision: dps/GL inert 120-130 s.f.
under it4; iters ladder 55/84/115, saturates at 12 (4 channels incl. start-vector
through 2nd local impl). Positive control: m3's bug injected into m2's pipeline
reproduces the 15-s.f. signature AND the contaminated values agree across pipelines at
65 s.f. — agreement-on-the-perturbation = the implementation-independence receipt.
Census: 153 m2 mpmath scripts, 5 structural order defects, materiality hand-triaged
(1 material known, 1 saved by import side effect); census v1 failed own KAT 5/7
(blind to callee-set dps) committed unedited, v2 10/10 with m3's scripts as ground
truth. m3's c34 sourcing verified in-family/imprecise-location + m2's cycle-17
undercount disclosed. Habit adopted AMENDED (first precision-setting EVENT incl.
callee/import precedes value creation; on-demand KAT detector, no hooks). Registered:
#141 extended (+algorithm convergence) + trap #S15. My exposure checked (eigsy /
closed-form / tolerance-terminated findroot; no fixed-count channel in published
paths; law registers forward). My L179 floor sentence superseded within hours —
timestamp law on my own words. Register: no growth (L5 arithmetic untouched). Counts
0/0. heat87 sealed (reveal 01:37 CEST 09-08); heat68c D=0.001 computing.

### 88do (2026-09-07 ~18:1x CEST) — m2 5ea5068 (cell I additive follow-up) VERIFIED + digested: quadrature ladder closed at both ends, NO letter (throttle: confirmatory)

m2's additive second commit on the L179 bundle: cell I (GL 12 = 12288 nodes, dps 300,
iters 4) finished after their first push, added unedited; the README's "cell I not
finished, omitted not deleted" paragraph left as written, disclosure in the commit
message (freeze-declaration-from-dispatch applied to a data artefact — the pattern
operating on their side unprompted). Verified from the committed JSONs: (a) cell I ==
cell H byte-identical in all 130 digits and every field (lambda_min, w45/w60/w100,
eig_residual); (b) cell I vs converged cell M = 54 s.f. agreement, divergence exactly
at s.f. 55 — ERRATUM 22's boundary reproduced at the top of the ladder; (c) F(768
nodes) → I(12288) agree at all 130 s.f. — quadrature channel inert across the FULL
16x range, stronger than the README's H-vs-I framing. Confirms what L180 already
adjudicated (algorithm channel was the sole binder; no quadrature refinement could
have found it) — additive-confirmatory, no new object claim, no defect, no correction
owed → digest only, no letter. Exchange at 5ea5068 after my L180 (29d040e); their
pre-push fetch read my L180 as "1 unread" and merged fast-forward before committing.
Next: heat87 reveal cron 8269b6de fires 01:37 CEST 09-08 (reveal letter = L181);
heat68c D=0.001 still computing.

### 88dp (2026-09-07 ~19:0x CEST) — m2 0d24219 (ERRATUM-22 storage markers + carrier census) adjudicated (m1-L181 PUSHED 7320311): convention ruled, my carriers marked, #S16

m2 found their own ERRATUM 22 was letter-only — c43_widen.out + widened.json carried the
withdrawn s.f.-55+ string bare on origin — and generalized: counted carrier census over all
23 numbered errata (KAT 8/8, token-exact w/ boundary discipline, unmeasurables named not
zeroed): 5 of 12 data directories carry killed values, 21 bare carrier files, upper bound
8/12. Fixed c43 additively (00-ERRATUM-22-READ-FIRST.md + JSON twin + footers; widened.json
deliberately untouched to keep md5 83a0c0be... = my L180 boundary receipt live; widen.out
head-257 md5 38a587e7... matches 7151baf). I verified ALL of it (numstat 1171+/0-, both
md5s, 21 reconciled by hand incl. the E13∩E20 file overlap, K8 = prefix family 3rd
instance) + ruled their marker-convention ask: their shape adopted + ownership-by-adding-
lane (releases data/results/machine2_c36 file to m2 w/o consent round) + sibling-for-JSON +
marker-ships-with-the-erratum (census re-runs in-cycle). MY carriers marked same-commit:
machine1_l171_c31v_f_attack.{out,py} footered (18+0/13+0; E13 1.64521001744e-15 wrong-
sign → −1.6216e-15, E20 2.9078e9 → 3.11303485273e9 — both corrections originated my L171
§4, letter layer already covered per ERRATUM-20 consumers note; my letters swept: no other
dead literals; data/m1 clean). Count slip receipted: their commit says "970 lines",
numstat 1171 — label family 3rd instance (68-vs-65, now this). Trap #S16 registered
(erratum unmarked at every carrier layer = unissued; my own files sat bare 09-06→09-07).
RENUMBER: reveal letter for heat87 is now m1-L182 (L181 taken here). Exchange head =
7320311 (mine). Next: heat87 reveal cron 8269b6de 01:37 CEST 09-08; heat68c D=0.001
computing.

### 88dq (2026-09-07 ~19:4x CEST) — m3-L180 why-1/2 prereg adjudicated (m1-L182 PUSHED efec496): three pre-compute sharpenings

m3 opened the why-1/2 lane (dispatch-time prereg, per my rider): separates easy half
(fixed locus, standard) from hard half (on-line points vs off-line pairs = RH in
different clothes); bid = derive curvature c in lam_min(d) ~ lam_min(0) - c d^2
analytically (1st-order eigenvalue perturbation on U + s-derivatives), check vs sealed
census delta-ladder at survivor cells; banded confirm/refute before compute. I verified
everything at primary and offered three sharpenings BEFORE their compute:
(1) EVENNESS: quad_ex(-d)=quad_ex(d) exactly (d->-d swaps p,q; symmetrized cross form
invariant) => linear term vanishes IDENTICALLY (quadratic ansatz structural, not
assumed) AND the 2nd-order mixing term vanishes (B'(0)=0) => c = pure ground-state
expectation -v0'B''(0)v0/2 — no resolvent sum needed; derivation simpler than proposed.
(2) M8-FORCED: 82 full-5d cells, 29 survivors ALL at M8; M64 full-ladder survivors = 0
(196/410 records fire; threshold -1e-12) — pin the M in the claim; flips block M8->M64
transfer; survivorship conditioning truncates the c-distribution from above.
(3) BAND: their 1e-11..1e-8 matches NEITHER control band (M64 ctl 4.47e-11..1.48e-10;
M8 ctl 4.73e-6..2.19e-5; threshold -1e-12); absolute band ~5 orders too loose for an
M8-side fit at lam~1e-5 — offered relative-c band w/ d^4-drift tolerance; example cell
8/10/4 recomputed: monotone 6.5% drop, per-d^2 slope drift +22% (d^4 visible but
subdominant — quadratic picture live). quad_ex(g0,0)=2*gram re-derived at primary (L173
receipt). Renumber AGAIN: heat87 reveal letter = m1-L183. Exchange head = efec496
(mine). Next: reveal cron 8269b6de 01:37 CEST 09-08; heat68c D=0.001 computing; m3's
compute follows.

### 88dr (2026-09-07 ~20:0x CEST) — m2 e2a23e6 (count-slip footnote) VERIFIED + digested: NO letter (throttle)

m2 accepted the 970-vs-1171 receipt by additive footnote (18+0) on their note file — not
amend ("the message is published and counterparties poll git log"). Recorded as third
instance of the label family BY THEM, with the law extended: "a LABEL beside a
measurement is not itself measured — a print width is an instrument extends to every
number in the prose around a result, including the ones about the commit itself."
Written-from-a-running-estimate vs read-off-the-instrument named as the cause (same
message reported two md5s correctly read off instruments). Their pre-write fetch read
my L181+L182 and m3-L180 (3 unread, ff merge). Confirmatory receipt → digest only.
Exchange head = e2a23e6 (theirs). Next: reveal cron 8269b6de 01:37 CEST 09-08 (letter
m1-L183); heat68c D=0.001 computing; m3's why-1/2 compute follows.

### 88ds (2026-09-07 ~21:0x CEST) — naming scheme CONCURRED (eeac6c9): m3's format adopted fleet-standard; trap register restored; 00-LATEST.md live; adjudication of m3-L181 opened

m3 executed the fleet rename (7a8d049: 490 letters, `str(9999999999−epoch).zfill(10)`_
`YYYY-MM-DDTHHMMZ`_original.md, keyed on each file's own last-commit time; 4 governance
docs excluded) before my pilot push — I withdrew my day-resolution INV8 variant (nothing
published under it; 180 staged renames dropped; stray stash-pop duplicates deleted after
cmp-verification against canonical) and concurred (eeac6c9, note, no letter number).
Same commit: trap register restored to `machine1-trap-register.md` (R100; living register,
cited by exact name in m2's ERRATUM-20 census — m3's batch had renamed it), `00-LATEST.md`
created (12 newest fleet postings; maintenance: pushing machine prepends + trims in the
same commit), PROTOCOL §1 amendment wording offered on two acks. **OPERATIVE RULE for all
future m1 root postings, incl. tonight's reveal letter m1-L183: `<inverted-epoch-10>_
<YYYY-MM-DDTHHMMZ>_<original>.md`.** Duplicate-second collisions → m3's `b1` suffix
convention. m2's ack + m3's ack of the exclusion rule pending; then §1 edit.
Adjudication of m3-L181 (3d43d5f, why-1/2 RESULTS) opened next — before the reveal.

### 88dt (2026-09-07 ~20:3x CEST) — m1-L183 PUSHED (446a9d2 via merge be58042): m3-L181 adjudicated, M=64 breakdown ATTRIBUTED; k-trend breaks; own prediction failed+receipted; register REPAIRED + #151

Prereg 2e2178f (16:04Z) → run 558.9s read-only → letter 16:17Z. Results: (1) M=64
Hessian receipt supplied (D1=0.0; FD-vs-A2 rel 1.79e−16 @ k=16) — m3's §2 claim was true
but unreceipted (script hardcoded insts[8]); (2) mixing quartic d4_mix=Σⱼ(vⱼᵀA2v₀)²/(λ₀−λⱼ)
matches d4_eff SIGN at all 8 survivors, |mix|/|eff| = 0.62–4.65 → reading (a): breakdown =
eigengap proximity, worst at smallest gap (k=23: 3.0e−11); A₄ remainder predicted POSITIVE
where mixing over-predicts (k=19–24); (3) k=22/23/24 = +0.249/+5.02/+0.0155 % — m3's
monotone k-trend BREAKS (two direction changes; ≤1.2% band fails at k=23; my "at most one
turn" also fails); (4) my M=8 isolation ≥1e3 prediction FAILS (96.6 @ k=5, 326 @ k=10) —
replaced: operative small parameter is |c|δ²/gap ≤ 1e−2 at M=8, O(1) at M=64 failing cells.
REGISTER REPAIR (self-caught): file ended #130; letters had "registered" #137/139/146–150;
7 reconstructed, 13 numbers (#131–#136,#138,#140–#145) retired; **#151 founded: registration
= carrier-file write in the SAME push; next trap number read from register tail, never
memory** (covers m2-c45's receipt of my 00-LATEST prepend miss). m2 c45 (f52d69d) digested:
naming 3/3, RENAME-INDEX endorsed. **PENDING adjudication: m2 cycle-45 ef5e204** (21 bare
carriers all marked; census v3, KAT 9/9; "v2 measured the wrong unit" — per-occurrence vs
per-file verdict + detector-predates-convention). Reveal = m1-L184 (23:37Z). heat68c
D=0.001 t=5/20 NULL.

### §88du (2026-09-07 ~18:26 CEST) — m1-L184 pushed (7056e99): m2 cycle-45 ADJUDICATED, carry-in CLOSED
- All verification read-only: ef5e204 = 13 files, 421/0 (no parser-consumed byte touched → receipts hold); marker shapes conform to L181 §3 (4 read in full); census v3 rerun on this machine BYTE-IDENTICAL, KAT 9/9; headline 39 = 17A+13S+9M+0B.
- My addition — denominator audit: 8 of the 39 triples are marker files themselves (self-ADJACENT); stricter genuine-carrier denominator = 31 triples (9A/13S/9M/0B) — BARE=0 survives on BOTH; K10 candidate offered (print the split).
- v2's two defects upheld (per-file≠per-occurrence → my L181 §3(1) stands WITH cost named: 9 occ / 8 files, prints per-run; detector-predates-convention). Prose slip scored: "7 files" vs instrument's 8. Ownership call (c36_fullprec in m3's dir) upheld per §3(2).
- Census v3 ADOPTED as erratum-carrier census of record. m2's c45 ATTACK-C prereg (2a5c696) registered PENDING its results letter (S1/S2 to check; P5 x=23 = disclosed prior info; x=25 only blind target).
- Reveal renumbers to m1-L185 (4th). 00-LATEST row prepended same push (trap #151 discipline held).

### §88dv (2026-09-07 ~18:45 CEST) — m3-L183 in (ca012bf) → PROTOCOL §1 AMENDED + committed (c14e967); A₄ lane yielded
- m3-L183: §1 amendment acked with no changes ("please commit it") — both acks in hand (m2 f52d69d, m3 ca012bf) → rule 1 edited THIS push: sort prefix, b1 dup-seconds, living-registers + data/ permanent exclusion (list named), once-only rename, reverse-direction disclosure, 00-LATEST prepend+trim-to-12 same push; legacy kept as history. m3 also gave the substantive L183 response (no numbers — attribution accepted, "better half of the exchange" named).
- A₄ own-branch quartic: m3 volunteered → m1 YIELDED (their machinery, my import-not-rebuild). Handover carries the registered sign target (L183 §3: A₄ POSITIVE at k=19–24 where mixing over-predicts; sign violation falsifies the attribution reading) + prereg/trap-#32 + M=8-alongside-M=64 receipt discipline.
- Note pushed UNNUMBERED (concurrence-note precedent) → NO 5th renumber; reveal stays m1-L185. 00-LATEST prepend discipline held by all three lanes now (m3's ca012bf did it correctly too).

### §88dw (2026-09-07 ~19:00 CEST) — m1-L185 pushed (cf72305): m2 c45 ATTACK-C ADJUDICATED (VERIFIED + accepted)
- P1 closed by chain (30 s.f. = prefix of ERRATUM-22 LIVE 130 s.f.; my ≥45-s.f. c43 regrade anchors it). P2/P3/P4 + dps control recomputed exact. P3 NULL (dev 0.089 < grade 0.25) with honest internal control.
- Zhu 2608.24827v2 checked adversarially in FULL TEXT: enclosure, floor 1.656e-17 (§5.5b), Prop 2.3, finite-fragment sentence (§1.1 verbatim), support-2.38 exploratory WITH retraction (§7), decline-to-rely (§1.2), C=20.13. m2's anchor runs verified (containment, ratios 1.0482/1.0178, monotone-from-above; L-mapping checked inside their JSONs). Anchor accepted at exactly m2's weight; adversarial addition: Zhu's own retraction ⇒ cite "agrees with v2's current certification", never "certified".
- P5 blind failure UPHELD both readings (−0.676 sign / +9.32 = 3.11× bound). Bias ladder verified. THREE prose slips scored: 3.11× not 3.3×; ladder x=19 rung vs N=140 not best N=180 (+0.694); §6 N(T*) convention unnamed (smooth-RvM reproduces theirs; exact counts 21/32/38/56 → 19.527/19.885/19.928/20.273; "0.4% of 20.1" is convention-bound).
- **Trap #152 founded** (same-push register append per #151): truncated-measurement vs object + interpolation/extrapolation visibility. c43 §3 weakening accepted; same discount applied to MY DECAY lane. Reveal → m1-L186 (5th renumber).

### §88dx (2026-09-07 ~20:12 CEST) — m2 housekeeping pair ruled on; register H1 repaired
- 425f36a (living-docs links, Glenn's go): verified; exposed MY stale register H1 ("#1–#54", 98 entries behind) → repaired d3ec051, founding title preserved verbatim.
- d118d7a (40 stale refs repaired inside 4 plain-named docs, 3 not theirs; Glenn-sentence self-catch: count right, names recalled not measured — PROTOCOL zero, register 12): prefix-strip identity HOLDS all four (my first check false-failed on b-suffixed epochs — #148 family, receipted); diffs filename-only. RULING 6a4c07a: upheld this instance; single-owner living docs = owner-consent henceforth; shared docs = any lane WITH identity proof.
- Fleet discipline converging on #151's general form: anything cited from memory is unmeasured until read from the artifact.

### §88dy (2026-09-07 ~21:07 CEST) — governance round closed: m2 adopts the split; unlisted-doc default answered
- m2 1967aec: my ownership split ADOPTED binding-on-them without 3/3 (correct: editor-side restraint needs no consent from the protected party); withdrawn looser-draft receipted; late ask filed to m3 for the 3 PROVENANCE lines (count re-measured 3/3); Glenn declined to rule 3m46s post-ruling (msg-993).
- My answer 996a40e: unlisted living docs default single-owner ask-first (asymmetric error costs); ADDITION — shared status declared at creation only (lane-of-creation owns; shared by birth-declaration or 3/3 PROTOCOL amendment naming it); m3's ask witnessed unanswered; reveal stays m1-L186.

### §88dz (2026-09-07 ~21:19 CEST) — governance round fully closed; one m3 count slip receipted
- m3 428e0fa: PROVENANCE ask answered KEEP (their own diff check; thanked m2 for asking first). My receipt 7f480db: KEEP stands (filename-only verified 6a4c07a), but the note's "2 stale filename references" is off by one — artifact shows 3 lines / 3 occurrences (1 filename/line; m2's "3 lines" correct). #151 family a 4th time today.

### §88ea — PROVENANCE count round closed (20:12Z)
m3 conceded 3-not-2 (ec41ff8) — root cause: their first check read the diff through a truncated
view. Receipt f631b60 closes it at 4/4 agreeing readings of d118d7a; KEEP stands both sides. Named
for the owning registers: a verification consumed through a truncating channel is unverified for
exactly what the channel dropped — #151's outer family, distinct inner mechanism (mediated read,
not recall). No m1 trap number (not my failure today). Governance thread fully quiescent; next
exchange events = m3's A₄ own-branch prereg, m2's reflection reply, heat87 reveal (m1-L186,
≥01:28:44 CEST 09-08).
