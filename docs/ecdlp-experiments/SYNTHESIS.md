# ECDLP Experiment Series: Master Synthesis — ECCp-131

**Date**: 2026-04-06  
**Experiments**: 5 completed  
**Target**: ECCp-131 (Certicom challenge curve, 131-bit prime-order)  
**Overall Verdict**: No algebraic weakness found. Curve is generically hard. ECDLP complexity remains O(√n) ≈ 2⁶⁵.

---

## Executive Summary

Across five experiments — endomorphism ring computation, isogeny volcano exploration, Pollard rho walk statistics, lattice attack analysis, and p-adic lifting — we found **zero exploitable weaknesses** in ECCp-131. The curve has a prime group order, a maximal embedding degree, a 132-bit CM discriminant with conductor 1, no special j-invariant, and a trace of Frobenius firmly in the generic range. Every known algebraic shortcut (Pohlig-Hellman, MOV/Frey-Rück pairing, Smart's anomalous attack, CM method, GLV endomorphism, isogeny descent, HNP lattice, BSGS hybrid) is provably inapplicable. The only viable path is generic group algorithms (Pollard rho with distinguished points), requiring ~2⁶⁵ group operations — but our Pollard rho implementation has a critical **negation map 2-cycle bug** that traps 96% of walks within ~40 steps, which must be fixed before any serious computation can proceed.

---

## Curve Profile

| Property | Value | Source |
|----------|-------|--------|
| Field prime q | `0x048E1D43F293469E33194C43186B3ABC0B` (131 bits) | Params |
| Coefficient a | `0x041CB121CE2B31F608A76FC8F23D73CB66` | Params |
| Coefficient b | `0x02F74F717E8DEC90991E5EA9B2FF03DA58` | Params |
| Group order n | `0x048E1D43F293469E317F7ED728F6B8E6F1` (131 bits, **prime**) | Params |
| Trace of Frobenius t | 29,529,377,007,934,231,835 (65 bits) | Exp 1 |
| t factorization | 5 × 11 × 17 × 251 × 32,749 × 3,842,119,859 | Exp 5 |
| t / 2√q | 0.375 (37.5% of Hasse bound) | Exp 5 |
| CM discriminant D | −5,328,143,084,860,676,590,809,120,034,441,032,302,419 (132 bits) | Exp 1 |
| \|D\| factorization | 67 × 173 × 2,087 × 4,903 × 44,923,194,445,989,685,202,159,178,469 | Exp 1 |
| D squarefree? | **Yes** | Exp 1 |
| Fundamental discriminant D₀ | = D (conductor f = 1) | Exp 1 |
| Endomorphism ring | Z[(1+√D₀)/2] — maximal order in Q(√D₀) | Exp 1 |
| Class number h(D) | ≈ 2.1 × 10²¹ (≈ 2⁷⁰) | Exp 1 |
| j-invariant | `0x13F849C0EED01093D8EFE9C7343113569` (generic) | Exp 2 |
| j = 0 or 1728? | **No** | Exp 2 |
| Embedding degree k | n − 1 (maximal, 131 bits) | Exp 1 |
| Anomalous (t = 1)? | **No** (t ≈ 2⁶⁵) | Exp 1, 5 |
| Supersingular (t = 0)? | **No** | Exp 2 |
| GLV applicable? | **No** (D is 132 bits, not small CM) | Exp 1 |
| Rational 2-torsion | None | Exp 2 |
| Rational 3-torsion | None | Exp 2 |
| Isogenies over F_q | 2 each at ℓ = 5, 7, 13; none at ℓ = 2, 3, 11 | Exp 2 |
| Volcano position | Crater (f = 1) for all ℓ | Exp 2 |
| n − 1 factorization | 2⁴ × 3 × 73 × 283 × (111-bit composite) | Exp 2 |

---

## Experiment Results Matrix

| # | Experiment | Approach | Verdict | Key Finding |
|---|-----------|----------|---------|-------------|
| 1 | Endomorphism Ring | Compute trace, CM discriminant, class number, check GLV/MOV/anomalous | ❌ No weakness | D is 132-bit squarefree, h ≈ 10²¹, embedding degree maximal, no special endomorphisms |
| 2 | Isogeny Volcano | Explore ℓ-isogenies for ℓ = 2,3,5,7,11,13; check neighbors for weakness | ❌ No weakness | 6 isogenous curves found; all share same prime order n (Tate's theorem) — isogeny walking cannot find weaker curve |
| 3 | Pollard Rho Statistics | Benchmark walk speed, partition uniformity, cycle detection, DP collection | ⚠️ Implementation bug | **96% of walks trapped in 2-cycles** within ~40 steps due to negation map interaction; 14.5K iter/s in pure Python |
| 4 | Lattice Attack | HNP analysis, LLL on x-coordinates, BSGS hybrid, multi-scalar lattice | ❌ Inapplicable | Lattice methods require side-channel leakage (known bits, oracle) that pure ECDLP does not provide |
| 5 | p-adic Lifting | Hensel lift to Z/q^k Z, formal group analysis, Smart's attack attempt | ❌ Inapplicable | Smart's attack requires t = 1 exactly (binary threshold); t ≈ 2⁶⁵ yields zero information |

---

## Mathematical Analysis

### Experiment 1: Endomorphism Ring

The trace of Frobenius t = 29,529,377,007,934,231,835 (65 bits) satisfies the Hasse bound and places ECCp-131 firmly in the ordinary regime. The CM discriminant D = t² − 4q is 132 bits, squarefree, and equals its own fundamental discriminant (conductor f = 1), meaning the endomorphism ring is the maximal order Z[(1+√D)/2] in Q(√D). The class number h(D) ≈ 2.1 × 10²¹ makes isogeny class enumeration completely infeasible. The embedding degree is maximal (n − 1), eliminating all pairing-based attacks.

### Experiment 2: Isogeny Volcano

Kronecker symbol analysis correctly predicted the isogeny structure: no ℓ-isogenies over F_q for ℓ = 2, 3, 11 (where (D/ℓ) = −1), and exactly 2 neighbors each for ℓ = 5, 7, 13 (where (D/ℓ) = +1). Six isogenous curves were found and verified via modular polynomials. By Tate's theorem, all isogenous curves share the same group order n (which is prime), so isogeny walking cannot produce a curve vulnerable to Pohlig-Hellman, pairing attacks, or anomalous attack. The crater of each volcano has ~h(D) ≈ 2⁷⁰ vertices — far too many to traverse.

### Experiment 3: Pollard Rho Statistics

The r-adding walk with negation map and L = 20 partitions was benchmarked at 14,494 iterations/second on ECCp-131 in pure Python, projecting to ~71.8 billion years for a single-threaded solve. The critical finding was a **negation map 2-cycle trap** affecting 96% of walks: after ~40 steps on average, the walk oscillates between two points whose sum (after normalization) maps back to the same partition. The Brent cycle detector catches these but they produce degenerate collisions (identical b-coefficients). This is a well-known issue documented by Bernstein, Lange, and Schwabe (2013), with standard fixes involving 2-cycle escape mechanisms and hash-based partition functions.

### Experiment 4: Lattice Attack

A systematic analysis of five lattice-based methods (Boneh-Venkatesan HNP, known-bit BSGS hybrid, multi-scalar lattice, x-coordinate lattice, structural 2D lattice) shows all are categorically inapplicable to pure ECDLP. The fundamental barrier is that lattice methods require approximate linear relationships in integers, while ECDLP provides only the nonlinear relationship Q = kP on an elliptic curve. Without side-channel leakage (known bits, timing, power analysis, nonce reuse), there is no oracle to feed a lattice construction. Even partial Pollard rho progress cannot be converted to HNP queries.

### Experiment 5: p-adic Lifting

Hensel lifting of P and Q to Z/q^k Z for k = 2, 3, 4 produced well-defined formal group elements, but the ratio ψ(Q̃)/ψ(P̃) does **not** equal the discrete logarithm. This was verified computationally (the candidate scalar gives the wrong point) and explained theoretically: Smart's attack has a **binary threshold** at t = 1. For t = 1 (anomalous curves), the formal logarithm perfectly linearizes the discrete log; for t ≠ 1, it provides zero information. Small-curve experiments confirmed this: the attack succeeds perfectly at t = 1 and degenerates to zero at t = 2, 3. ECCp-131's trace t ≈ 2⁶⁵ is as far from anomalous as a random curve.

---

## Critical Finding: Pollard Rho 2-Cycle Bug

### The Problem

When using the **negation map** (normalizing points so y ≤ q/2) combined with an **r-adding walk** (partitioning by x mod L), a 2-cycle trap occurs when:

1. Walk arrives at point R in partition j
2. Computes S = normalize(R + R_j)
3. S also falls in partition j
4. Computes T = normalize(S + R_j)
5. T = R — the walk is permanently trapped, alternating R ↔ S forever

### Measured Impact

| Metric | ECCp-131 | 20-bit curve | 14-bit curve |
|--------|----------|--------------|--------------|
| Trap rate | **96%** | 8% | 10% |
| Mean steps to trap | 39.6 | — | — |
| Solver success rate | — | 7/10 (expected ~100%) | 19/20 |
| Walk output uniqueness | 8.5% | — | — |
| DP distance inflation | 2–8× expected | — | — |

The trap rate increases with curve size because larger curves have more partition collisions relative to the walk's mixing time.

### Root Cause

The negation map halves the effective point space but does NOT halve the partition space. When normalize(R + R_j) lands back in partition j, the deterministic walk creates a fixed point of the 2-step map, forming an inescapable cycle.

### Standard Fixes (from literature)

1. **2-cycle escape**: Track previous point; if R_new = R_prev, apply a secondary perturbation (e.g., use partition (j+1) mod L)
2. **Hash-based partition**: Replace `x mod L` with a multiplicative hash to decorrelate partition assignment from EC addition structure
3. **Larger partition size**: Increase L from 20 to 64+ to reduce self-referencing probability

### References

- Bernstein, Lange, Schwabe (2013): "On the correct use of the negation map in the Pollard rho method"
- Bos, Kaihara, Kleinjung, Lenstra, Montgomery (2012): "Solving a 112-bit prime ECDLP on game consoles"

---

## Attack Surface Assessment

Ranked from most to least promising:

| Rank | Attack Vector | Feasibility | Complexity | Notes |
|------|--------------|-------------|-----------|-------|
| 1 | **Pollard rho (parallel, optimized)** | Only viable path | O(√n) ≈ 2⁶⁵ ops | Requires: fix 2-cycle bug, C/GMP implementation, massive parallelism (distinguished points), ~10⁹× speedup over pure Python |
| 2 | **BSGS / Baby-step Giant-step** | Theoretically equivalent | O(√n) time + O(√n) space | Needs ~2⁶⁵ stored points (~10²⁰ bytes) — infeasible in practice |
| 3 | **Index calculus (summation polynomials)** | Speculative, unexplored | Sub-exponential? | Semaev's method; best results on binary curves, unclear for prime field curves of this size |
| 4 | **Isogeny-based** | Provably no advantage | Same O(√n) | Tate's theorem: all isogenous curves share same prime order |
| 5 | **Lattice (HNP/LLL)** | Categorically inapplicable | N/A | Requires side-channel leakage that pure ECDLP lacks |
| 6 | **p-adic lifting (Smart's)** | Categorically inapplicable | N/A | Binary threshold at t=1; our t ≈ 2⁶⁵ |
| 7 | **Pairing-based (MOV)** | Categorically inapplicable | N/A | Embedding degree = n−1 (maximal) |
| 8 | **Pohlig-Hellman** | Categorically inapplicable | N/A | Group order n is prime |

**Honest assessment**: The 2⁶⁵ generic lower bound is real. There are no shortcuts. A 131-bit ECDLP has ~65.5 bits of security, which is at the boundary of computational feasibility for well-resourced actors but far beyond what is achievable in a research/educational setting without specialized hardware and significant parallelism.

---

## Recommended Next Steps

### Priority 1: Fix Pollard Rho Implementation (Critical)

1. Implement 2-cycle escape mechanism (track R_prev, perturb on trap detection)
2. Switch to hash-based partition function (Knuth multiplicative hash or similar)
3. Increase partition count to L = 64 or L = 128
4. Re-run Experiment 3 statistics to verify fix: walk output should be ~95%+ unique, DP distances should match expected values, trap rate should drop to <1%
5. Verify solver achieves 100% success rate on 20-bit and 30-bit test curves

### Priority 2: Performance Engineering

1. Rewrite EC arithmetic in C with GMP for arbitrary-precision modular arithmetic
2. Target: ~10⁷ iterations/second per core (vs current 14.5K in Python → ~700× speedup)
3. Implement Montgomery ladder for constant-time scalar multiplication
4. Implement projective coordinates to eliminate modular inversions per step

### Priority 3: Parallelization

1. Implement distinguished points (DP) method for embarrassingly parallel Pollard rho
2. Each worker walks independently; reports when it hits a DP (e.g., low 20 bits of x = 0)
3. Central server collects DPs and checks for collisions
4. Expected DPs before collision: ~2⁶⁵⁻²⁰ = 2⁴⁵ ≈ 35 trillion (still enormous)

### Priority 4: Explore Unexplored Directions

1. **Summation polynomials / index calculus**: Semaev's approach adapted for prime-field curves — largely unexplored for curves of this size, and theoretical complexity is unclear
2. **Weil descent**: Check if the field extension structure of q allows any descent attack (unlikely for a random prime)
3. **Kangaroo method**: Pollard lambda — useful if k is known to lie in a restricted interval (not our case, but worth benchmarking)

### Priority 5: Scale Assessment

1. Estimate total cost in core-hours for a full 2⁶⁵ Pollard rho computation
2. Compare against known records (Certicom ECCp-109 solved in 2004; ECCp-131 remains open as of 2026)
3. Determine if cloud computing (e.g., 10,000 cores × 1 year) brings this into range

---

## Complete Numerical Results

| Quantity | Value | Bits |
|----------|-------|------|
| Field prime q | 1,550,031,797,834,347,859,248,576,414,813,139,942,411 | 131 |
| Group order n | 1,550,031,797,834,347,859,219,047,037,805,205,710,577 | 131 |
| Trace t | 29,529,377,007,934,231,835 | 65 |
| t/2√q ratio | 0.375020 | — |
| CM discriminant \|D\| | 5,328,143,084,860,676,590,809,120,034,441,032,302,419 | 132 |
| Largest factor of \|D\| | 44,923,194,445,989,685,202,159,178,469 | 96 |
| Class number h(D) | ≈ 2.1 × 10²¹ | ~70 |
| Embedding degree k | n − 1 | 131 |
| j-invariant | 0x13F849C0EED01093D8EFE9C7343113569 | 129 |
| Pollard rho iterations needed | ≈ √(πn/2) ≈ 3.69 × 10¹⁹ | ~65 |
| Pure Python speed | 14,494 iter/s | — |
| Projected single-thread time | ~71.8 × 10⁹ years | — |
| 2-cycle trap rate (ECCp-131) | 96% | — |
| Mean steps to trap | 39.6 | — |
| Negation map frequency (pre-trap) | 50.18% (p = 0.81) | — |
| Isogenous curves found | 6 (via ℓ = 5, 7, 13) | — |
| p-adic ratio (t_Q/t_P mod q) | 1,480,426,698,131,557,594,817,025,221,811,632,609,553 | 131 |
| p-adic ratio = discrete log? | **No** (verified) | — |
| Smooth factors of n−1 | 2⁴ × 3 × 73 × 283 = 396,816 (≈19 bits) | 19 |
| t factorization | 5 × 11 × 17 × 251 × 32,749 × 3,842,119,859 | — |

---

## Methodology Notes

- All computations performed in pure Python with native arbitrary-precision integers
- Modular polynomials sourced from Sutherland's database (MIT)
- Every factorization verified by reconstruction
- Every isogenous j-invariant verified by substitution into Φ_ℓ(j, j')
- Hensel lifts verified by checking curve equation mod q^k at each precision
- Small-curve experiments used as ground-truth validation for each method
- No external computer algebra system (SageMath, Magma) used — all results independently computed

---

*Compiled from Experiments 1–5, 2026-04-06. All results are reproducible from scripts in `/workspace/`.*
