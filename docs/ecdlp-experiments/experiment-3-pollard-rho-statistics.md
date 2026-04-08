# Experiment 3: Pollard Rho Walk Statistics

**Date**: 2026-04-06  
**Curve**: ECCp-131 (Certicom challenge), plus 14-bit and 20-bit test curves  
**Objective**: Characterize Pollard's rho walk behavior, detect non-random behavior  

---

## Executive Summary

**CRITICAL FINDING**: The current implementation suffers from **negation map 2-cycle traps** — a well-known issue in the literature. 96% of walks on ECCp-131 become trapped within ~40 steps, oscillating between exactly 2 points forever. This makes the walk completely ineffective. The Brent cycle detector catches these as collisions but they are almost always degenerate (same b-coefficient), forcing restarts that immediately re-trap. 

This is **not exploitable** in the sense of making ECDLP easier — it's a bug in our implementation that makes the solver *worse* than expected. The fix is straightforward and well-documented in the literature.

---

## 1. Iteration Speed Benchmark

| Metric | ECCp-131 (pure Python) | 14/20-bit curves |
|--------|----------------------|------------------|
| **Iterations/sec** | **14,494** | ~106,000–152,000 |
| **Time per iteration** | **69.0 µs** | ~6.6–9.5 µs |
| **Raw EC add** | ~52 µs | — |
| **Raw EC double** | ~52 µs | — |

**Analysis**: Pure Python modular arithmetic on 131-bit integers is the bottleneck. Each step requires one EC addition (1 modular inversion via Fermat's little theorem = `pow(x, q-2, q)`) plus comparisons and normalization.

**Projection for full solve** (√(n/2) ≈ 2^65 iterations at 14.5K it/s):
- Single thread: **~71.8 billion years** (completely infeasible in pure Python)
- Need ~10^9× speedup: GMP + parallelization + GPU/FPGA

---

## 2. CRITICAL BUG: Negation Map 2-Cycle Traps

### Prevalence (ECCp-131)

| Metric | Value |
|--------|-------|
| Trials | 100 |
| **Walks trapped** | **96/100 (96%)** |
| Mean steps to trap | 39.6 |
| Median steps to trap | 28 |
| Min/Max | 2 / 199 |
| Trap distribution across partitions | Roughly uniform (all 20 partitions trap) |

### Mechanism

The r-adding walk with negation map creates unavoidable 2-cycle traps:

1. Walk arrives at point R, which maps to partition j (via `R.x mod L`)
2. Step: compute S = R + R_j
3. Normalize: if S.y > q/2, replace S with -S (negation map)
4. **If normalize(S) also maps to partition j**, then:
   - Next step: compute T = normalize(S) + R_j
   - If normalize(T) == R, the walk is **permanently trapped**

**Verified on ECCp-131**: At step 10, the walk enters a 2-cycle between:
- R_a = (353398...410, 330525...063), partition 10
- R_b = (1314025...070, 396581...592), partition 10

Where R_a + R_10 = -R_b (same x, negated y), and R_b + R_10 = -R_a. Both normalize to each other.

### Impact on Solver

The Brent's cycle detector in `solve_brent()` catches the 2-cycle (R_h == R_t), but:
- The collision is almost always **degenerate** (b1 == b2 mod n) because the negation makes coefficients mirror
- Degenerate collisions yield no information about k
- Solver restarts with a new random point... which traps again in ~40 steps
- **Result**: 20-bit curve solver only succeeds 7/10 times within 1M iterations (expected ~887 iterations!)

### Reference

This is a well-known issue documented by:
- Bos, Kaihara, Kleinjung, Lenstra, Montgomery (2012): "Solving a 112-bit prime elliptic curve discrete logarithm problem on game consoles using sloppy reduction"
- Bernstein, Lange, Schwabe (2013): "On the correct use of the negation map in the Pollard rho method"

---

## 3. Partition Distribution

### Pre-Trap Steps Only (ECCp-131, L=20)

| Metric | Value |
|--------|-------|
| Total pre-trap steps | 4,739 (from 100 walks) |
| Expected per partition | 237 |
| Chi-squared | 421.7 (df=19) |
| p-value | ≈ 0.0000 |
| Min/Max count | 183 / 444 |
| **Verdict** | **Non-uniform** |

The partition is non-uniform even before trapping. This is because `x mod 20` is biased by the structure of the walk — after adding R_j, the resulting x-coordinate is not uniformly distributed because EC addition is deterministic given the partition.

### Control: Random x-coordinates

| Metric | Value |
|--------|-------|
| Random x mod 20 | χ² = 8.9, p = 0.975 |
| q mod 20 | 11 |
| **Verdict** | **Uniform** ✓ |

The partition function `x mod L` is uniform for truly random x-values. The non-uniformity comes from the walk's autocorrelation, not the partition function itself.

---

## 4. Negation Map Statistics

### Pre-Trap Steps (ECCp-131)

| Metric | Value |
|--------|-------|
| Pre-trap steps measured | 4,811 |
| Negation applied | 50.18% |
| Expected | 50.00% |
| z-statistic | 0.25 |
| p-value | 0.8064 |
| **Verdict** | **Consistent with 50%** ✓ |

When measured on pre-trap steps only, the negation map fires at the expected 50% rate. The initial v1 measurement showing 99.98% was an artifact of the 2-cycle trap, where the walk alternates between two points requiring negation every other step (effectively 100%).

---

## 5. Distinguished Point Collection

| dp_bits | Expected Distance | DPs Found | Mean Distance | Ratio | Verdict |
|---------|------------------|-----------|---------------|-------|---------|
| 8 | 256 | 100 | 489 | 1.91 | High (~2×) |
| 10 | 1,024 | 65 | 3,068 | 3.00 | Very high (~3×) |
| 12 | 4,096 | 6 | 31,718 | 7.74 | Extremely high |

**Analysis**: DP collection is severely impaired by 2-cycle traps. Walks trap quickly, requiring restarts. Each restart wastes the initial scalar multiplication (expensive) and the walk resets with no progress toward a DP. The ratio grows worse with larger dp_bits because:
- Expected walk length to DP grows as 2^dp_bits
- But walks trap after ~40 steps on average
- So most walks never reach a DP; only lucky walks that avoid trapping contribute

**After fixing 2-cycle traps**, DP collection should converge to ratio ≈ 1.0.

---

## 6. Cycle Detection on Small Curves

### 14-bit Curve (n = 10,039, expected ρ = 88.8)

| Metric | Value |
|--------|-------|
| Trials | 100 |
| 2-cycle traps | 10 (10%) |
| Mean cycle (all) | 44.0 |
| Mean cycle (non-trap) | 48.5 |
| **Ratio (non-trap/expected)** | **0.546** |
| Median | 33 |
| Min/Max | 3 / 129 |
| Solve success | **19/20** |

### 20-bit Curve (n = 1,001,977, expected ρ = 887.1)

| Metric | Value |
|--------|-------|
| Trials | 100 |
| 2-cycle traps | 8 (8%) |
| Mean cycle (all) | 59.5 |
| Mean cycle (non-trap) | 64.4 |
| **Ratio (non-trap/expected)** | **0.073** |
| Median | 33 |
| Min/Max | 3 / 257 |
| Solve success | **7/10** (within 1M iterations!) |

**Analysis**: 
- The 2-cycle trap rate is lower on small curves (~8-10%) vs ECCp-131 (96%). This makes sense: with more group elements relative to partition size, there are more possible partition mappings, and the chance of a self-referencing trap is lower.
- Even non-trap cycles are very short — much shorter than expected √(πn/4). This is because Brent's algorithm detects the cycle at the first power-of-2 boundary, which systematically underestimates cycle length.
- The 20-bit solver's 7/10 success rate (vs expected 100%) confirms the trapping issue is not just theoretical.

---

## 7. Walk Function Output Uniformity

### 14-bit Curve, 2000 Random Starts, 50 Steps Each

| Metric | Value |
|--------|-------|
| Points collected | 2,000 |
| **Unique x-coordinates** | **170 (8.5%)** |
| Chi-squared | 11,610 (df=49) |
| p-value | ≈ 0.0000 |
| Walks trapped in 50 steps | 374/500 (75%) |
| **Verdict** | **Extremely non-uniform** |

The walk concentrates on ~170 unique x-values instead of spreading across ~5,000 possible values. This is entirely caused by the 2-cycle traps: 75% of walks trap within 50 steps, and trapped walks always end at one of a small set of trap-pair points.

---

## 8. Walk Table Self-Loop Analysis (ECCp-131)

For each walk table entry R_j, checked whether R_j.x mod 20 equals j (which would guarantee self-referencing traps):

| j | R_j.x mod 20 | Self-ref? |
|---|-------------|-----------|
| 0 | 19 | No |
| 1 | 6 | No |
| 2 | 13 | No |
| ... | ... | ... |
| 10 | 15 | No |

**No walk table entries are self-referencing** — the traps don't come from R_j mapping to its own partition. Instead, they arise dynamically: the *result* of R + R_j, after normalization, happens to map back to partition j. This depends on the specific point R, not just R_j.

---

## Required Fixes

### Fix 1: 2-Cycle Escape (CRITICAL)

Add a previous-point tracker to `_step()`:

```python
def _step_with_escape(self, R, a, b, R_prev=None):
    R_new, a_new, b_new = self._step(R, a, b)
    if R_new == R_prev:  # 2-cycle detected!
        # Apply extra random perturbation
        j2 = (self._partition(R) + 1) % self.L  # use different partition
        R_new = self.curve.add(R_new, self._walk_R[j2])
        a_new = (a_new + self._walk_a[j2]) % self.n
        b_new = (b_new + self._walk_b[j2]) % self.n
        # Re-normalize
        if R_new is not INF:
            x, y = R_new
            if y > self.curve.q // 2:
                R_new = (x, (-y) % self.curve.q)
                a_new = (-a_new) % self.n
                b_new = (-b_new) % self.n
    return R_new, a_new, b_new
```

### Fix 2: Hash-Based Partition

Replace `x mod L` with a hash-based partition that breaks the structural correlation:

```python
def _partition(self, R):
    if R is INF:
        return 0
    # Use hash to decorrelate partition from EC structure
    h = (R[0] * 2654435761) & 0xFFFFFFFF  # Knuth multiplicative hash
    return h % self.L
```

### Fix 3: Larger Partition Size

Increase from L=20 to L=64 or L=128 — larger partitions make self-referencing less likely.

---

## Overall Assessment

| Aspect | Status | Notes |
|--------|--------|-------|
| Iteration speed | ✅ As expected | ~14.5K/s pure Python, consistent with 131-bit modular arithmetic |
| Negation map | ✅ Correct (pre-trap) | 50.18%, p=0.81 |
| 2-cycle traps | ❌ **CRITICAL BUG** | 96% of walks trapped within ~40 steps |
| Partition uniformity | ⚠️ Biased by traps | Uniform for random points, biased during walk |
| DP collection | ❌ Impaired | 2-8× slower than expected due to traps |
| Walk quality | ❌ Non-uniform | Only 8.5% unique outputs (should be ~95%+) |
| Small curve solving | ⚠️ Degraded | 14-bit OK (19/20), 20-bit poor (7/10) |
| Exploitability | No | Bug makes solver *worse*, not ECDLP easier |

**The walk does NOT approximate a random function** due to the 2-cycle trap bug. Once this is fixed (with the standard escape mechanism from the literature), the walk should behave as expected. No structural weakness in the ECCp-131 curve was detected — all anomalies trace back to the implementation bug.

---

## References

1. Pollard, J.M. (1978). "Monte Carlo methods for index computation (mod p)." Mathematics of Computation, 32(143).
2. Brent, R.P. (1980). "An improved Monte Carlo factorization algorithm." BIT Numerical Mathematics, 20(2).
3. Gallant, R., Lambert, R., Vanstone, S. (2000). "Improving the parallelized Pollard lambda search on anomalous binary curves." Mathematics of Computation, 69(232).
4. Bernstein, D.J., Lange, T., Schwabe, P. (2013). "On the correct use of the negation map in the Pollard rho method." PKC 2013.
5. Bos, J.W., Kaihara, M.E., Kleinjung, T., Lenstra, A.K., Montgomery, P.L. (2012). "Solving a 112-bit prime elliptic curve discrete logarithm problem on game consoles using sloppy reduction."
