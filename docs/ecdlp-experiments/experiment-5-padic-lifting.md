# Experiment 5: p-adic Lifting (Extended Smart's Attack)

**Date**: 2026-04-06
**Target**: ECCp-131 ECDLP instance
**Method**: p-adic lift of curve and points to Q_q, formal group analysis
**Verdict**: ❌ **COMPLETELY INAPPLICABLE** — zero information leakage

---

## 1. Trace of Frobenius Analysis

### Exact Value

```
t = q + 1 - n = 29,529,377,007,934,231,835
t (hex) = 0x199cd6bef7481d51b
t bit-length = 65 bits
```

### Complete Factorization

```
t = 5 × 11 × 17 × 251 × 32749 × 3842119859
```

- **All factors < 2³²** → t is **32-bit smooth**
- Largest prime factor: 3,842,119,859 (32 bits)
- t is **NOT a perfect power** (tested all exponents 2..64)

### Proximity to Special Values

| Property | Value | Significance |
|----------|-------|--------------|
| t | 29,529,377,007,934,231,835 | 65-bit trace |
| \|t - 1\| (anomalous) | 29,529,377,007,934,231,834 | 65 bits — astronomically far |
| \|t\| (supersingular) | 29,529,377,007,934,231,835 | Far from 0 |
| \|t - 2\| | 29,529,377,007,934,231,833 | Far from CM by Z[i] |
| \|t + 1\| | 29,529,377,007,934,231,836 | Far from other specials |
| \|t\| / 2√q | 0.375020 | ~37.5% of Hasse bound |
| \|t-1\| / q | 1.9 × 10⁻²⁰ | Negligible fraction of field |

### t mod Small Primes

```
t mod 2  = 1    t mod 3  = 2    t mod 5  = 0    t mod 7  = 1
t mod 11 = 0    t mod 13 = 4    t mod 17 = 0    t mod 19 = 7
t mod 23 = 22   t mod 29 = 23   t mod 31 = 19   t mod 37 = 19
t mod 41 = 15   t mod 43 = 3    t mod 47 = 2    t mod 53 = 19
t mod 59 = 48   t mod 61 = 55   t mod 67 = 1    t mod 71 = 6
t mod 73 = 23   t mod 79 = 2    t mod 83 = 2    t mod 89 = 31
t mod 97 = 81
```

Notable: t ≡ 0 mod 5, t ≡ 0 mod 11, t ≡ 0 mod 17. These contribute to t's smooth factorization.

---

## 2. p-adic Lift Results

### Method

1. **Hensel lift**: Lifted points P and Q from E(F_q) to E(Z/q^k Z) for k = 2, 3, 4
   - Kept x-coordinates fixed, lifted y via Newton's method
   - All lifts verified: y² ≡ x³ + ax + b mod q^k ✓

2. **Scalar multiplication**: Computed n·P̃ and n·Q̃ in projective coordinates mod q^k
   - Used projective (X:Y:Z) to avoid division-by-zero issues

### Results for n·P̃ mod q^k

| k | v_q(X) | v_q(Y) | v_q(Z) | In kernel? |
|---|--------|--------|--------|------------|
| 2 | 1 | 0 | 0 | Yes (Z≡0 mod q but notation differs) |
| 3 | 1 | 0 | 0 | Yes |
| 4 | 1 | 0 | 3 | Yes |

At all precisions:
- **X ≡ 0 mod q** (as expected: n·P = O in E(F_q))
- **Y ≢ 0 mod q** (non-degenerate)
- **Z ≡ 0 mod q** (point reduces to identity)
- The point n·P̃ is in E¹(Q_q), the kernel of reduction ✓

### Smart's Formula Application

Computed the formal group parameter t_P = X/Y mod q^k for n·P̃, and similarly t_Q for n·Q̃:

```
v_q(t_P) = 1 for all k (formal parameter is O(q))
v_q(t_Q) = 1 for all k

Ratio t_Q/t_P mod q:
  k=2: 1480426698131557594817025221811632609553
  k=3: 1480426698131557594817025221811632609553
  k=4: 1480426698131557594817025221811632609553
```

The ratio is **consistent across all precisions**, confirming it's a well-defined element of Z_q.

### Verification: Is the Ratio the Discrete Log?

**NO.** Computing `k_candidate × P mod q`:

```
k_candidate * P = (0xdc4b808..., 0x33ad6a4...)
Q               = (0x3aa6f00..., 0x9c21c28...)
MATCH: False
```

The ratio is a well-defined p-adic number but does **NOT** encode the discrete logarithm. This is expected from theory:

- For **anomalous curves** (t=1): The Satoh-Araki/Smart/Semaev theorem guarantees the ratio equals k mod q
- For **non-anomalous curves** (t≠1): The Hensel lift of Q is NOT the k-multiple of the Hensel lift of P at higher precision. The lift preserves the curve equation but not the group relation Q = kP beyond precision 1.

The ratio represents ψ(Q̃)/ψ(P̃) where ψ is the formal logarithm and Q̃, P̃ are independent lifts — essentially a meaningless quantity for ECDLP.

---

## 3. Formal Group Analysis

### Expansion

For E: y² = x³ + ax + b, with formal parameters z = x/y, w = 1/y near the identity:

```
w = z³ + a·z·w² + b·w³    (recursive relation)
```

Solving iteratively (converged in 6 iterations):

```
w(z) = z³ + a·z⁷ + b·z⁹ + c₁₁·z¹¹ + c₁₃·z¹³ + ...
```

where:
- w[3] = 1 (leading coefficient) ✓
- w[7] = a mod q ✓
- w[9] = b mod q ✓
- All odd-indexed coefficients; even-indexed = 0 (as expected for short Weierstrass)

The formal group structure is **completely generic** — no special symmetries or degeneracies that could be exploited.

---

## 4. Small Curve Experiments

### 4a: Smart's Attack on Anomalous Curve (t=1) ✅

**Curve**: p = 101, a = 1, b = 32, #E = 101, t = 1

```
Generator P = (4, 91)
Secret k = 42
Q = 42·P = (86, 51)

Hensel lift to mod p²:
  p·P̃ projective = (707, 5985, 0)   [Z ≡ 0 mod p]
  p·Q̃ projective = (7878, 1559, 0)  [Z ≡ 0 mod p]

Smart's extraction:
  t_P = X/Y mod p² = 4343 → ψ(P) = 4343/101 = 43
  t_Q = X/Y mod p² = 8989 → ψ(Q) = 8989/101 = 89
  
  k = ψ(Q)/ψ(P) = 89/43 = 89 × 43⁻¹ mod 101 = 42 ✅ CORRECT!
```

**Smart's attack works perfectly on anomalous curves.**

### 4b: Near-Anomalous Curves (t=2,3)

| Curve | t | n·P̃ in kernel? | t_param mod p |
|-------|---|-----------------|---------------|
| p=101, a=1, b=2 | 2 | Yes | 0 |
| p=101, a=1, b=8 | 2 | Yes | 0 (4545 mod 101 = 0) |
| p=101, a=1, b=13 | 3 | Yes | 0 (6868 mod 101 = 0) |

For **all near-anomalous curves**, the formal group parameter reduces to 0 mod p — the t=X/Y values are multiples of p but provide no useful information. The kernel element is "too deep" in the filtration to extract the log.

### Key Insight from Small Curves

Smart's attack has a **sharp threshold**, not a gradual degradation:
- **t = 1**: Perfect extraction, 100% success
- **t = 2, 3**: Zero useful information, formal parameter degenerates
- **t ≠ 1**: The formal group homomorphism doesn't linearize the discrete log problem

---

## 5. Theoretical Analysis

### Why Smart's Attack Requires t = 1 Exactly

The attack relies on a specific isomorphism in the formal group:

1. For an anomalous curve (t=1, #E = p), the **multiplication-by-p map** [p] on the formal group Ê is given by:
   ```
   [p](T) = pT + O(T²)    (the formal derivative at 0 is p)
   ```
   Since #E(F_p) = p, the p-torsion in E(Q_p) has a specific structure that makes the formal logarithm extract the discrete log.

2. For a non-anomalous curve (t ≠ 1), the key property fails: the exact sequence
   ```
   0 → Ê(pZ_p) → E(Q_p) → E(F_p) → 0
   ```
   doesn't split in the right way. The formal logarithm gives a well-defined homomorphism, but it doesn't linearize the relation Q = kP.

3. The **lifting problem**: When we Hensel-lift P and Q independently to mod q², the group relation Q = kP is preserved mod q but NOT mod q². The "correction term" at higher precision depends on k in a non-linear way that the formal logarithm cannot untangle.

### For ECCp-131 Specifically

- t = 29,529,377,007,934,231,835 (65 bits)
- |t - 1| ≈ 2.95 × 10¹⁹
- The curve is as far from anomalous as a generic random curve
- The formal group has no special structure
- The p-adic lift reveals nothing about the discrete log

---

## 6. Interesting Side Observations

### 6a: Trace Smoothness

t = 5 × 11 × 17 × 251 × 32749 × 3842119859 is **completely 32-bit smooth**.

This is mildly unusual but not exploitable for ECDLP. The trace's smoothness is relevant for:
- **MOV attack**: requires embedding degree, which depends on the multiplicative order of q mod n, not on t's factorization
- **Anomalous attack**: requires t = 1 exactly, not smooth t
- **CM-related attacks**: require t² - 4q to factor specially, not t itself

### 6b: Consistent p-adic Ratio

The ratio ψ(Q̃)/ψ(P̃) = 1,480,426,698,131,557,594,817,025,221,811,632,609,553 is well-defined and consistent across all precisions. While not the discrete log, it IS a well-defined p-adic invariant of the pair (P, Q, choice of lift). It encodes information about the geometry of the lift, not the discrete log.

### 6c: v_q Structure

For k=4: v_q(Z) = 3 for both n·P̃ and n·Q̃, while v_q(X) = 1 and v_q(Y) = 0. The Z valuation growing with k is characteristic of a non-torsion point in the formal group being scaled.

---

## 7. Verdict

### Assessment: COMPLETELY INAPPLICABLE

| Criterion | Status |
|-----------|--------|
| Anomalous (t=1)? | ❌ t = 29,529,377,007,934,231,835 |
| Near-anomalous? | ❌ \|t-1\| has 65 bits |
| p-adic lift reveals k? | ❌ Verified: ratio ≠ discrete log |
| Formal group special? | ❌ Generic structure |
| Any partial information? | ❌ Zero bits of k recovered |
| Gradual degradation? | ❌ Binary: works at t=1, fails completely otherwise |

**Smart's attack and all p-adic lifting approaches provide exactly zero information about the ECCp-131 discrete logarithm.** This is the most clear-cut negative result among all experiments — the attack has a mathematically provable binary threshold (t=1 vs t≠1) with no possibility of partial success.

The curve's trace t ≈ 2.95 × 10¹⁹ places it firmly in the "generic" category where p-adic methods contribute nothing.

---

## Appendix: Code

Full implementations at:
- `/workspace/exp5_padic.py` — Main experiment (trace analysis, lift, formal group, small curves)
- `/workspace/exp5_padic_v2.py` — Projective coordinate version (handles non-invertible elements)
- `/workspace/exp5_verify.py` — Verification that p-adic ratio ≠ discrete log
