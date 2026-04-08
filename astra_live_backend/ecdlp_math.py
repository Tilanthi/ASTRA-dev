#!/usr/bin/env python3
"""
ECCp-131 Mathematical Structure Analysis
==========================================

Comprehensive mathematical analysis of the ECCp-131 Certicom challenge curve,
checking for exploitable structural weaknesses that could enable sub-generic attacks.

Analyses performed:
  1. Anomalous curve check (Smart's attack)
  2. Supersingular check (MOV with small k)
  3. Embedding degree (MOV/Frey-Rück transfer)
  4. CM discriminant and j-invariant
  5. Group order factorization (Pohlig-Hellman)
  6. Smooth factor analysis of p-1 and p+1
  7. Twist security
  8. Automorphism group
  9. Index calculus feasibility (Petit's framework)
  10. Summation polynomial analysis
  11. Cross-domain connections (endomorphism ring, isogeny class)

Uses only Python builtins + the EC arithmetic from ecdlp_solver.py.

Author: ASTRA (Autonomous Scientific & Technological Research Agent)
Date: 2026-04-06
"""

import math
import time
import sys
from typing import Dict, List, Optional, Tuple

from astra_live_backend.ecdlp_solver import (
    ECCP131, ECCP131_P, ECCP131_Q,
    EllipticCurve, ECPoint, INF,
)

# ---------------------------------------------------------------------------
# Integer Factoring Utilities (trial division + Pollard's rho for integers)
# ---------------------------------------------------------------------------

def _small_primes(limit: int = 100_000) -> List[int]:
    """Sieve of Eratosthenes up to limit."""
    sieve = [True] * (limit + 1)
    sieve[0] = sieve[1] = False
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            for j in range(i*i, limit + 1, i):
                sieve[j] = False
    return [i for i in range(2, limit + 1) if sieve[i]]


SMALL_PRIMES = _small_primes(1_000_000)  # primes up to 1M


def trial_division(n: int, bound: int = 1_000_000) -> Tuple[Dict[int, int], int]:
    """
    Factor n by trial division up to bound.
    Returns (factors_dict, remaining_cofactor).
    """
    factors = {}
    for p in SMALL_PRIMES:
        if p > bound or p * p > n:
            break
        while n % p == 0:
            factors[p] = factors.get(p, 0) + 1
            n //= p
    return factors, n


def pollard_rho_factor(n: int, max_iterations: int = 500_000, max_time: float = 10.0) -> Optional[int]:
    """
    Pollard's rho factoring for integers.
    Returns a non-trivial factor of n, or None if not found.
    """
    if n % 2 == 0:
        return 2
    if _is_probable_prime(n):
        return n

    from math import gcd
    t0 = time.time()
    for c in range(1, 20):
        x = 2
        y = 2
        d = 1
        iters = 0
        while d == 1 and iters < max_iterations:
            x = (x * x + c) % n
            y_tmp = (y * y + c) % n
            y = (y_tmp * y_tmp + c) % n
            d = gcd(abs(x - y), n)
            iters += 1
            if iters % 10000 == 0 and (time.time() - t0) > max_time:
                break
        if 1 < d < n:
            return d
        if (time.time() - t0) > max_time:
            break
    return None


def _is_probable_prime(n: int, k: int = 20) -> bool:
    """Miller-Rabin primality test with k rounds."""
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0:
        return False

    # Write n-1 as 2^r * d
    r, d = 0, n - 1
    while d % 2 == 0:
        r += 1
        d //= 2

    # Deterministic witnesses for n < 2^64
    witnesses = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37]
    if n < 3_317_044_064_679_887_385_961_981:
        witnesses = witnesses[:min(k, len(witnesses))]

    for a in witnesses:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def full_factor(n: int, trial_bound: int = 1_000_000, max_time: float = 30.0) -> Dict[int, int]:
    """
    Factor n completely using trial division + Pollard's rho.
    Returns {prime: exponent} dict. Unfactored composites are stored as-is.
    """
    if n <= 1:
        return {}

    t0 = time.time()
    factors, cofactor = trial_division(n, trial_bound)

    # Now factor the remaining cofactor with Pollard's rho
    stack = [cofactor] if cofactor > 1 else []
    while stack:
        if (time.time() - t0) > max_time:
            # Time budget exceeded — store remaining as unfactored
            for m in stack:
                if m > 1:
                    factors[m] = factors.get(m, 0) + 1
            break
        m = stack.pop()
        if m <= 1:
            continue
        if _is_probable_prime(m):
            factors[m] = factors.get(m, 0) + 1
            continue
        remaining_time = max(1.0, max_time - (time.time() - t0))
        d = pollard_rho_factor(m, max_time=min(10.0, remaining_time))
        if d is None or d == m:
            factors[m] = factors.get(m, 0) + 1
            continue
        stack.append(d)
        stack.append(m // d)

    return factors


def format_factorization(factors: Dict[int, int]) -> str:
    """Format a factorization dict as a human-readable string."""
    if not factors:
        return "1"
    parts = []
    for p in sorted(factors.keys()):
        e = factors[p]
        if e == 1:
            parts.append(str(p))
        else:
            parts.append(f"{p}^{e}")
    return " × ".join(parts)


def smoothness_bound(factors: Dict[int, int]) -> int:
    """Return the largest prime factor."""
    if not factors:
        return 1
    return max(factors.keys())


def smooth_part(n: int, bound: int) -> Tuple[int, int]:
    """
    Compute the B-smooth part of n.
    Returns (smooth_part, cofactor) where n = smooth_part * cofactor
    and all prime factors of smooth_part are <= bound.
    """
    s = 1
    remaining = n
    for p in SMALL_PRIMES:
        if p > bound:
            break
        while remaining % p == 0:
            s *= p
            remaining //= p
    return s, remaining


# ---------------------------------------------------------------------------
# 1. Curve Structure Analysis
# ---------------------------------------------------------------------------

def analyze_curve_structure() -> Dict:
    """
    Run ALL structural weakness checks on the ECCp-131 curve.
    Returns a comprehensive analysis dict.
    """
    t_start = time.time()
    results = {
        "curve_parameters": {},
        "checks": {},
        "factorizations": {},
        "recommendations": [],
        "vulnerabilities_found": [],
        "analysis_time_sec": 0,
    }

    q = ECCP131.q       # field prime
    a = ECCP131.a        # curve coefficient a
    b = ECCP131.b        # curve coefficient b
    n = ECCP131.order    # group/point order

    results["curve_parameters"] = {
        "q": hex(q),
        "a": hex(a),
        "b": hex(b),
        "n": hex(n),
        "q_bits": q.bit_length(),
        "n_bits": n.bit_length(),
        "P": (hex(ECCP131_P[0]), hex(ECCP131_P[1])),
        "Q": (hex(ECCP131_Q[0]), hex(ECCP131_Q[1])),
    }

    # ---- Check 1: Anomalous curve (Smart's attack) ----
    check1 = _check_anomalous(q, n)
    results["checks"]["anomalous"] = check1

    # ---- Check 2: Supersingular check ----
    check2 = _check_supersingular(q, n)
    results["checks"]["supersingular"] = check2

    # ---- Check 3: Trace of Frobenius ----
    check3 = _compute_trace(q, n)
    results["checks"]["frobenius_trace"] = check3

    # ---- Check 4: CM discriminant ----
    check4 = _compute_cm_discriminant(q, n)
    results["checks"]["cm_discriminant"] = check4

    # ---- Check 5: j-invariant ----
    check5 = _compute_j_invariant(q, a, b)
    results["checks"]["j_invariant"] = check5

    # ---- Check 6: Embedding degree (MOV attack) ----
    check6 = _check_embedding_degree(q, n, max_k=1000)
    results["checks"]["embedding_degree"] = check6

    # ---- Check 7: Group order primality & factorization ----
    check7 = _check_order_structure(n)
    results["checks"]["order_structure"] = check7

    # ---- Check 8: Pohlig-Hellman analysis ----
    check8 = _pohlig_hellman_analysis(q, n)
    results["checks"]["pohlig_hellman"] = check8

    # ---- Check 9: p-1 smoothness ----
    check9 = _smooth_factor_analysis(q)
    results["checks"]["p_minus_1_smoothness"] = check9["p_minus_1"]
    results["checks"]["p_plus_1_smoothness"] = check9["p_plus_1"]
    results["factorizations"] = check9.get("factorizations", {})

    # ---- Check 10: Twist security ----
    check10 = _check_twist_security(q, n)
    results["checks"]["twist_security"] = check10

    # ---- Check 11: Automorphism group ----
    check11 = _compute_automorphisms(q, a, b)
    results["checks"]["automorphisms"] = check11

    # ---- Check 12: Index calculus feasibility ----
    check12 = _index_calculus_feasibility(q, n)
    results["checks"]["index_calculus"] = check12

    # ---- Check 13: Summation polynomial analysis ----
    check13 = _summation_polynomial_analysis(q, n)
    results["checks"]["summation_polynomials"] = check13

    # ---- Check 14: Cross-domain connections ----
    check14 = _cross_domain_analysis(q, a, b, n)
    results["checks"]["cross_domain"] = check14

    # ---- Check 15: Near-prime-power field ----
    check15 = _check_prime_power(q)
    results["checks"]["prime_power_field"] = check15

    # Compile vulnerabilities and recommendations
    for name, check in results["checks"].items():
        if isinstance(check, dict):
            if check.get("vulnerable"):
                results["vulnerabilities_found"].append({
                    "check": name,
                    "detail": check.get("detail", ""),
                    "severity": check.get("severity", "HIGH"),
                })
            if check.get("recommendation"):
                results["recommendations"].append({
                    "check": name,
                    "recommendation": check["recommendation"],
                    "priority": check.get("priority", "LOW"),
                })

    results["analysis_time_sec"] = round(time.time() - t_start, 3)

    # Overall verdict
    if results["vulnerabilities_found"]:
        results["verdict"] = "VULNERABILITIES FOUND — exploitable weaknesses detected!"
    else:
        results["verdict"] = "NO EXPLOITABLE WEAKNESSES — curve appears to be secure against all known structural attacks."

    return results


# ---------------------------------------------------------------------------
# Individual Check Functions
# ---------------------------------------------------------------------------

def _check_anomalous(q: int, n: int) -> Dict:
    """Check 1: Is #E(F_q) == q? (Smart's attack → O(n) solve)"""
    is_anomalous = (n == q)
    trace = q + 1 - n
    return {
        "description": "Anomalous curve check (Smart's attack)",
        "is_anomalous": is_anomalous,
        "trace_equals_1": (trace == 1),
        "group_order_equals_field_prime": is_anomalous,
        "vulnerable": is_anomalous,
        "severity": "CRITICAL" if is_anomalous else "NONE",
        "detail": (
            "CRITICAL: Curve is anomalous! DLP solvable in polynomial time via p-adic lift."
            if is_anomalous else
            f"Curve is NOT anomalous. n - q = {n - q} (non-zero)."
        ),
        "recommendation": (
            "Apply Smart's anomalous curve attack immediately!"
            if is_anomalous else None
        ),
        "priority": "CRITICAL" if is_anomalous else None,
    }


def _check_supersingular(q: int, n: int) -> Dict:
    """Check 2: Is trace of Frobenius ≡ 0 mod char? (Supersingular → MOV with k ≤ 6)"""
    t = q + 1 - n  # trace of Frobenius
    char = q  # characteristic = q for prime field
    is_supersingular = (t % char == 0)  # t ≡ 0 mod p for odd p means supersingular

    # For prime fields, t ≡ 0 mod p means t = 0 (since |t| < 2√q < q for q > 4)
    is_ss_simple = (t == 0)

    return {
        "description": "Supersingular curve check",
        "trace": t,
        "is_supersingular": is_ss_simple,
        "vulnerable": is_ss_simple,
        "severity": "CRITICAL" if is_ss_simple else "NONE",
        "detail": (
            "CRITICAL: Curve is supersingular! MOV attack with embedding degree ≤ 6."
            if is_ss_simple else
            f"Curve is ordinary (trace t = {t}, non-zero). Supersingular MOV does NOT apply."
        ),
        "recommendation": (
            "Apply MOV attack — transfer DLP to F_{q^k}* with k ≤ 6."
            if is_ss_simple else None
        ),
        "priority": "CRITICAL" if is_ss_simple else None,
    }


def _compute_trace(q: int, n: int) -> Dict:
    """Check 3: Compute and analyze the trace of Frobenius."""
    t = q + 1 - n
    t_abs = abs(t)
    hasse_bound = 2 * int(math.isqrt(q))

    # Hasse's theorem: |t| ≤ 2√q
    within_hasse = (t_abs <= hasse_bound)

    return {
        "description": "Frobenius trace analysis",
        "trace_t": t,
        "trace_hex": hex(t) if t >= 0 else f"-{hex(-t)}",
        "trace_bits": t_abs.bit_length(),
        "hasse_bound_2sqrt_q": hasse_bound,
        "within_hasse_bound": within_hasse,
        "trace_abs_over_2sqrt_q": round(t_abs / hasse_bound, 6) if hasse_bound > 0 else None,
        "detail": (
            f"Trace t = {t} ({t_abs.bit_length()}-bit). "
            f"Hasse bound: |t| ≤ {hasse_bound}. "
            f"|t|/2√q = {t_abs/hasse_bound:.6f}. "
            f"{'Trace is within Hasse bound ✓' if within_hasse else 'WARNING: violates Hasse bound!'}"
        ),
    }


def _compute_cm_discriminant(q: int, n: int) -> Dict:
    """Check 4: Compute the CM discriminant D = t² - 4q."""
    t = q + 1 - n
    D = t * t - 4 * q
    D_abs = abs(D)

    # Small |D| could indicate special structure
    is_small_D = (D_abs.bit_length() < 40)

    # Check if D is a perfect square (would mean endomorphism ring = Z, unusual)
    sqrt_D = math.isqrt(D_abs)
    is_perfect_square = (sqrt_D * sqrt_D == D_abs)

    # Fundamental discriminant: remove square factors
    # D = f² · D_0 where D_0 is the fundamental discriminant
    D_0 = D_abs
    f_squared = 1
    for p in SMALL_PRIMES[:100]:  # check small primes
        while D_0 % (p * p) == 0:
            D_0 //= (p * p)
            f_squared *= p

    return {
        "description": "CM (Complex Multiplication) discriminant",
        "D": D,
        "D_hex": hex(D) if D >= 0 else f"-{hex(-D)}",
        "D_bits": D_abs.bit_length(),
        "is_negative": D < 0,
        "is_small": is_small_D,
        "is_perfect_square": is_perfect_square,
        "conductor_f": f_squared if f_squared > 1 else 1,
        "fundamental_discriminant_D0": -D_0 if D < 0 else D_0,
        "vulnerable": is_small_D,
        "severity": "MEDIUM" if is_small_D else "NONE",
        "detail": (
            f"D = t² - 4q = {D} ({D_abs.bit_length()}-bit). "
            f"{'SMALL discriminant — may indicate CM by a small order!' if is_small_D else 'Large discriminant — typical for random curve.'} "
            f"{'D is a perfect square!' if is_perfect_square else ''}"
        ),
        "recommendation": (
            "Investigate CM structure — small discriminant may allow specialized attacks."
            if is_small_D else None
        ),
        "priority": "HIGH" if is_small_D else None,
    }


def _compute_j_invariant(q: int, a: int, b: int) -> Dict:
    """Check 5: Compute the j-invariant. j=0 or j=1728 means special structure."""
    # j = 1728 * 4a³ / (4a³ + 27b²) mod q
    a3 = pow(a, 3, q)
    b2 = pow(b, 2, q)
    numerator = (1728 * 4 * a3) % q
    denominator = (4 * a3 + 27 * b2) % q

    if denominator == 0:
        j = None
        j_detail = "SINGULAR CURVE (4a³ + 27b² = 0) — this should not happen for a valid curve!"
    else:
        j = (numerator * pow(denominator, q - 2, q)) % q
        j_detail = f"j = {j} (hex: {hex(j)})"

    is_special = (j == 0 or j == 1728)

    return {
        "description": "j-invariant (extra automorphisms check)",
        "j_invariant": j,
        "j_hex": hex(j) if j is not None else None,
        "is_zero": j == 0,
        "is_1728": j == 1728,
        "has_extra_automorphisms": is_special,
        "automorphism_order": (
            6 if j == 0 else (4 if j == 1728 else 2)
        ) if j is not None else None,
        "vulnerable": is_special,
        "severity": "LOW" if is_special else "NONE",
        "detail": (
            f"{j_detail}. "
            f"{'j=0: curve has automorphism group of order 6 (hexagonal lattice CM by Z[ζ₃])!' if j == 0 else ''}"
            f"{'j=1728: curve has automorphism group of order 4 (square lattice CM by Z[i])!' if j == 1728 else ''}"
            f"{'Generic j-invariant — automorphism group is {±1} (order 2). No extra speedup.' if not is_special else ''}"
        ),
        "recommendation": (
            f"Exploit {'order-6' if j == 0 else 'order-4'} automorphism group for Pollard rho speedup (factor of {3 if j == 0 else 2} improvement)."
            if is_special else None
        ),
        "priority": "MEDIUM" if is_special else None,
    }


def _check_embedding_degree(q: int, n: int, max_k: int = 1000) -> Dict:
    """Check 6: Find smallest k where q^k ≡ 1 (mod n). Small k → MOV/FR attack."""
    # We need n | (q^k - 1), i.e., q^k ≡ 1 (mod n)
    embedding_k = None
    qk_mod_n = q % n
    for k in range(1, max_k + 1):
        if qk_mod_n == 1:
            embedding_k = k
            break
        qk_mod_n = (qk_mod_n * q) % n

    is_small = (embedding_k is not None and embedding_k <= 20)

    if embedding_k is not None:
        target_field_bits = q.bit_length() * embedding_k
    else:
        target_field_bits = None

    return {
        "description": f"Embedding degree check (MOV/Frey-Rück attack), checked k=1..{max_k}",
        "embedding_degree": embedding_k,
        "checked_up_to": max_k,
        "is_small_embedding_degree": is_small,
        "target_field_bits": target_field_bits,
        "vulnerable": is_small,
        "severity": "CRITICAL" if is_small else "NONE",
        "detail": (
            f"Embedding degree k = {embedding_k}. "
            f"{'CRITICAL: MOV attack feasible! Transfer DLP to F_q^' + str(embedding_k) + ' (' + str(target_field_bits) + '-bit field).' if is_small else ''}"
            f"{'Embedding degree is large enough to resist MOV/FR attacks.' if embedding_k and not is_small else ''}"
            f"{'No embedding degree found for k ≤ ' + str(max_k) + ' — likely k ≈ n, MOV/FR completely infeasible.' if embedding_k is None else ''}"
        ),
        "recommendation": (
            f"Apply MOV attack: transfer ECDLP to DLP in F_q^{embedding_k} ({target_field_bits}-bit). "
            f"Use index calculus (NFS) to solve the transferred DLP."
            if is_small else
            ("Extend search to larger k if computational budget allows." if embedding_k is None else None)
        ),
        "priority": "CRITICAL" if is_small else ("LOW" if embedding_k is None else None),
    }


def _check_order_structure(n: int) -> Dict:
    """Check 7: Analyze group order n — primality and factorization."""
    is_prime = _is_probable_prime(n)

    if is_prime:
        factors = {n: 1}
        factor_str = f"{n} (prime)"
    else:
        factors = full_factor(n)
        factor_str = format_factorization(factors)

    return {
        "description": "Group order structure (Pohlig-Hellman relevance)",
        "order_n": n,
        "order_hex": hex(n),
        "order_bits": n.bit_length(),
        "is_prime": is_prime,
        "factorization": factor_str,
        "num_prime_factors": len(factors),
        "largest_prime_factor": max(factors.keys()) if factors else n,
        "largest_factor_bits": max(factors.keys()).bit_length() if factors else n.bit_length(),
        "vulnerable": not is_prime and max(factors.keys()).bit_length() < 80,
        "severity": "HIGH" if (not is_prime and max(factors.keys()).bit_length() < 80) else "NONE",
        "detail": (
            f"Order n is {'PRIME' if is_prime else 'COMPOSITE'}. "
            f"{'Pohlig-Hellman does NOT apply (order is prime — no subgroup decomposition).' if is_prime else ''}"
            f"{'Factorization: ' + factor_str + '. Pohlig-Hellman reduces DLP to subgroups.' if not is_prime else ''}"
        ),
    }


def _pohlig_hellman_analysis(q: int, n: int) -> Dict:
    """Check 8: Full Pohlig-Hellman decomposition analysis."""
    t = q + 1 - n
    curve_order = q + 1 - t  # = n for prime-order curves, but could differ

    # The curve group order #E(F_q) could differ from n if n is the order of the *point* P
    # For the challenge, n = order of P (which is stated to be prime)
    # But #E(F_q) might be a multiple of n

    # Actually for ECCp-131, the order given IS the group order
    # Check: if n is prime and n divides #E = q+1-t, and #E = n, then group is cyclic of prime order

    is_n_prime = _is_probable_prime(n)

    # Factor q+1-t to see if there are small cofactors
    group_order = q + 1 - t
    cofactor = group_order // n if group_order % n == 0 else None

    return {
        "description": "Pohlig-Hellman decomposition analysis",
        "point_order_n": n,
        "point_order_prime": is_n_prime,
        "group_order": group_order,
        "group_order_hex": hex(group_order),
        "cofactor_h": cofactor,
        "vulnerable": not is_n_prime,
        "severity": "HIGH" if not is_n_prime else "NONE",
        "detail": (
            f"Point order n = {hex(n)} ({'prime' if is_n_prime else 'COMPOSITE'}). "
            f"Group order #E = {hex(group_order)}. "
            f"Cofactor h = {cofactor}. "
            f"{'Since n is prime, Pohlig-Hellman cannot decompose the DLP into smaller subproblems.' if is_n_prime else 'COMPOSITE order — Pohlig-Hellman applies!'}"
        ),
    }


def _smooth_factor_analysis(q: int) -> Dict:
    """Check 9: Analyze p-1 and p+1 for smooth factors (Petit's index calculus)."""
    results = {"factorizations": {}}

    # --- p - 1 analysis ---
    pm1 = q - 1
    pm1_factors = full_factor(pm1)
    pm1_str = format_factorization(pm1_factors)
    pm1_largest = max(pm1_factors.keys()) if pm1_factors else 1
    pm1_smooth_16, pm1_cofactor_16 = smooth_part(pm1, 2**16)
    pm1_smooth_32, pm1_cofactor_32 = smooth_part(pm1, 2**32)

    # How many bits are in the smooth part?
    pm1_smooth_bits_16 = pm1_smooth_16.bit_length() if pm1_smooth_16 > 1 else 0
    pm1_smooth_bits_32 = pm1_smooth_32.bit_length() if pm1_smooth_32 > 1 else 0

    results["p_minus_1"] = {
        "description": "p-1 smoothness analysis (Petit's index calculus, instance 1)",
        "p_minus_1": hex(pm1),
        "factorization": pm1_str,
        "largest_prime_factor": pm1_largest,
        "largest_factor_bits": pm1_largest.bit_length(),
        "smooth_part_2_16_bits": pm1_smooth_bits_16,
        "smooth_part_2_32_bits": pm1_smooth_bits_32,
        "total_bits": pm1.bit_length(),
        "smooth_fraction_2_16": round(pm1_smooth_bits_16 / pm1.bit_length(), 4) if pm1.bit_length() > 0 else 0,
        "smooth_fraction_2_32": round(pm1_smooth_bits_32 / pm1.bit_length(), 4) if pm1.bit_length() > 0 else 0,
        "petit_applicable": pm1_smooth_bits_32 > 40,  # heuristic threshold
        "detail": (
            f"p-1 factorization: {pm1_str}. "
            f"Largest factor: {pm1_largest} ({pm1_largest.bit_length()}-bit). "
            f"2^16-smooth part: {pm1_smooth_bits_16} bits / {pm1.bit_length()} total. "
            f"2^32-smooth part: {pm1_smooth_bits_32} bits / {pm1.bit_length()} total."
        ),
        "recommendation": (
            "p-1 has significant smooth part — investigate Petit's index calculus instance 1."
            if pm1_smooth_bits_32 > 40 else
            "p-1 has no significant smooth part — Petit's instance 1 unlikely to help."
        ),
        "priority": "HIGH" if pm1_smooth_bits_32 > 40 else "LOW",
    }
    results["factorizations"]["p_minus_1"] = pm1_str

    # --- p + 1 analysis ---
    pp1 = q + 1
    pp1_factors = full_factor(pp1)
    pp1_str = format_factorization(pp1_factors)
    pp1_largest = max(pp1_factors.keys()) if pp1_factors else 1
    pp1_smooth_16, pp1_cofactor_16 = smooth_part(pp1, 2**16)
    pp1_smooth_32, pp1_cofactor_32 = smooth_part(pp1, 2**32)
    pp1_smooth_bits_16 = pp1_smooth_16.bit_length() if pp1_smooth_16 > 1 else 0
    pp1_smooth_bits_32 = pp1_smooth_32.bit_length() if pp1_smooth_32 > 1 else 0

    results["p_plus_1"] = {
        "description": "p+1 smoothness analysis",
        "p_plus_1": hex(pp1),
        "factorization": pp1_str,
        "largest_prime_factor": pp1_largest,
        "largest_factor_bits": pp1_largest.bit_length(),
        "smooth_part_2_16_bits": pp1_smooth_bits_16,
        "smooth_part_2_32_bits": pp1_smooth_bits_32,
        "total_bits": pp1.bit_length(),
        "smooth_fraction_2_16": round(pp1_smooth_bits_16 / pp1.bit_length(), 4) if pp1.bit_length() > 0 else 0,
        "smooth_fraction_2_32": round(pp1_smooth_bits_32 / pp1.bit_length(), 4) if pp1.bit_length() > 0 else 0,
        "detail": (
            f"p+1 factorization: {pp1_str}. "
            f"Largest factor: {pp1_largest} ({pp1_largest.bit_length()}-bit). "
            f"2^16-smooth part: {pp1_smooth_bits_16} bits / {pp1.bit_length()} total."
        ),
    }
    results["factorizations"]["p_plus_1"] = pp1_str

    return results


def _check_twist_security(q: int, n: int) -> Dict:
    """Check 10: Analyze the quadratic twist's group order."""
    t = q + 1 - n
    twist_order = q + 1 + t  # #E'(F_q) = q + 1 + t

    twist_is_prime = _is_probable_prime(twist_order)

    if not twist_is_prime:
        twist_factors = full_factor(twist_order)
        twist_str = format_factorization(twist_factors)
        twist_largest = max(twist_factors.keys())
    else:
        twist_factors = {twist_order: 1}
        twist_str = f"{twist_order} (prime)"
        twist_largest = twist_order

    return {
        "description": "Quadratic twist security",
        "twist_order": twist_order,
        "twist_order_hex": hex(twist_order),
        "twist_order_bits": twist_order.bit_length(),
        "twist_is_prime": twist_is_prime,
        "twist_factorization": twist_str,
        "twist_largest_factor_bits": twist_largest.bit_length(),
        "detail": (
            f"Twist order #E'(F_q) = q+1+t = {hex(twist_order)} ({twist_order.bit_length()}-bit). "
            f"{'Twist order is prime — good twist security.' if twist_is_prime else 'Twist factorization: ' + twist_str}"
        ),
    }


def _compute_automorphisms(q: int, a: int, b: int) -> Dict:
    """Check 11: Determine the automorphism group of the curve."""
    # j-invariant determines automorphism group
    a3 = pow(a, 3, q)
    b2 = pow(b, 2, q)
    denom = (4 * a3 + 27 * b2) % q
    if denom == 0:
        return {"description": "Singular curve", "error": "4a³ + 27b² = 0"}

    j = (1728 * 4 * a3 * pow(denom, q - 2, q)) % q

    if j == 0 and a == 0:
        aut_order = 6
        aut_group = "Z/6Z (hexagonal CM by Z[ζ₃])"
        rho_speedup = "√3 ≈ 1.73×"
    elif j == 1728 and b == 0:
        aut_order = 4
        aut_group = "Z/4Z (square CM by Z[i])"
        rho_speedup = "√2 ≈ 1.41×"
    else:
        aut_order = 2
        aut_group = "Z/2Z (negation map only)"
        rho_speedup = "Already using negation map (standard √2 from equivalence classes)"

    return {
        "description": "Automorphism group of the curve",
        "j_invariant": j,
        "automorphism_order": aut_order,
        "automorphism_group": aut_group,
        "pollard_rho_speedup": rho_speedup,
        "detail": (
            f"Aut(E) = {aut_group}, order {aut_order}. "
            f"Pollard rho speedup from automorphisms: {rho_speedup}."
        ),
    }


def _index_calculus_feasibility(q: int, n: int) -> Dict:
    """Check 12: Assess Petit-style index calculus feasibility."""
    pm1 = q - 1

    # Compute smooth part of p-1
    smooth_16, cofactor_16 = smooth_part(pm1, 2**16)
    smooth_32, cofactor_32 = smooth_part(pm1, 2**32)

    smooth_bits_16 = smooth_16.bit_length() if smooth_16 > 1 else 0
    smooth_bits_32 = smooth_32.bit_length() if smooth_32 > 1 else 0

    # Petit's instance 1 requires a large smooth divisor of p-1
    # The factor base size is related to the smooth part
    # For index calculus to beat Pollard rho, we need smooth part > ~2^40

    # Estimate: if smooth(p-1, B) has s bits, then factor base ~ B, relations ~ B,
    # per-relation cost ~ B^c for some c
    # Total cost ~ B^(1+c), must be < 2^65.5 (Pollard rho cost)

    petit_viable = smooth_bits_32 > 50  # very rough heuristic

    # Also check: can we decompose p-1 into a tower of small-degree extensions?
    # p-1 = 2 * something. If something = q1 * q2 * ... with qi small → useful

    return {
        "description": "Index calculus feasibility (Petit 2016 framework)",
        "p_minus_1_smooth_bits_B16": smooth_bits_16,
        "p_minus_1_smooth_bits_B32": smooth_bits_32,
        "p_minus_1_total_bits": pm1.bit_length(),
        "smooth_ratio_B16": round(smooth_bits_16 / pm1.bit_length(), 4),
        "smooth_ratio_B32": round(smooth_bits_32 / pm1.bit_length(), 4),
        "petit_instance_1_viable": petit_viable,
        "pollard_rho_cost_bits": 65.5,
        "detail": (
            f"p-1 has {smooth_bits_32}-bit smooth part (B=2^32). "
            f"Petit's instance 1 requires large smooth divisor of p-1. "
            f"{'Smooth part is significant — Petit may be viable!' if petit_viable else 'Smooth part too small — Petit unlikely to beat Pollard rho.'} "
            f"Pollard rho baseline: ~2^65.5 iterations."
        ),
        "recommendation": (
            "Implement Petit's factor-base construction using smooth part of p-1."
            if petit_viable else
            "Index calculus unlikely to help — p-1 lacks smooth structure."
        ),
        "priority": "HIGH" if petit_viable else "LOW",
    }


def _summation_polynomial_analysis(q: int, n: int) -> Dict:
    """Check 13: Analyze Semaev's summation polynomial approach."""
    # S_3(x1, x2, x3) = 0 iff P1 + P2 + P3 = O on the curve
    # S_3 has degree 2 in each variable
    # Factor base F = {(x,y) : x < B} has size ≈ B/2 (half of x-coords have y)

    # For index calculus with S_3 and factor base size S:
    # - Need S + small_const relations
    # - Each relation: find x1, x2 < B such that S_3(x1, x2, x_R) = 0
    # - This is a system of 1 equation in 2 unknowns over F_q, degree 2 in each
    # - Solutions exist with probability ≈ S/q (heuristic)
    # - Per-relation cost: enumerate ~q/S candidates, each costing O(poly(log q))
    # - Total: S * (q/S) * poly(log q) = q * poly(log q)
    # - This is WORSE than Pollard rho (2^65.5) since q ≈ 2^131

    # With S_4 (3 unknowns, degree 4):
    # - Relations per attempt: ≈ S²/q (more solutions due to more variables)
    # - But per-attempt cost grows (degree 4 system)

    # Optimal factor base size (heuristic): S ≈ q^(1/3) ≈ 2^44
    # Relations needed: ~S ≈ 2^44
    # Per-relation attempts: ~q/S² ≈ 2^131 / 2^88 = 2^43
    # Per-attempt cost: Gröbner basis on degree-2 system in 2 variables → O(1) essentially
    # Total: ~2^44 * 2^43 = 2^87 — still worse than 2^65.5

    optimal_S_bits = q.bit_length() // 3
    total_cost_s3 = q.bit_length()  # rough: total cost ≈ q (no savings)
    pollard_cost = 65.5

    return {
        "description": "Semaev summation polynomial (S_3) analysis",
        "field_size_bits": q.bit_length(),
        "s3_degree_per_variable": 2,
        "s4_degree_per_variable": 4,
        "optimal_factor_base_bits": optimal_S_bits,
        "estimated_cost_s3_bits": total_cost_s3,
        "pollard_rho_cost_bits": pollard_cost,
        "s3_beats_pollard": total_cost_s3 < pollard_cost,
        "detail": (
            f"S_3 approach: degree-2 bivariate system over {q.bit_length()}-bit field. "
            f"Optimal factor base ~2^{optimal_S_bits}. "
            f"Estimated total cost: ~2^{total_cost_s3} (vs Pollard rho 2^{pollard_cost}). "
            f"{'S_3 approach is FASTER!' if total_cost_s3 < pollard_cost else 'S_3 approach is SLOWER than Pollard rho for prime fields.'} "
            f"Prime fields lack the Weil descent that makes S_3 efficient for binary fields."
        ),
        "recommendation": "Summation polynomials do not beat Pollard rho for 131-bit prime fields.",
        "priority": "LOW",
    }


def _cross_domain_analysis(q: int, a: int, b: int, n: int) -> Dict:
    """Check 14: Cross-domain connections (endomorphism ring, isogeny structure)."""
    t = q + 1 - n
    D = t * t - 4 * q  # CM discriminant

    # The endomorphism ring of E is an order in Q(√D)
    # If D = f² · D_0, the endomorphism ring is Z[fω] where ω = (1+√D_0)/2 or √D_0/2

    D_abs = abs(D)
    D_0 = D_abs
    f = 1
    for p in SMALL_PRIMES[:200]:
        while D_0 % (p * p) == 0:
            D_0 //= (p * p)
            f *= p

    # Class number h(D) — for large |D|, h(D) ≈ √|D| / π
    # Exact computation requires more sophisticated methods
    h_estimate = int(math.sqrt(D_abs) / math.pi) if D_abs > 0 else 0

    # Check if D_0 is one of the known small CM discriminants
    small_cm_discs = [-3, -4, -7, -8, -11, -12, -16, -19, -27, -28, -43, -67, -163]
    has_known_cm = (-D_0 in small_cm_discs)

    # Isogeny class: curves with same trace t over F_q are isogenous
    # Two curves are F_q-isogenous iff they have the same number of points

    return {
        "description": "Cross-domain analysis (endomorphism ring, CM, isogeny class)",
        "cm_discriminant_D": D,
        "fundamental_discriminant_D0": -D_0,
        "conductor_f": f,
        "cm_field": f"Q(√{-D_0})" if D < 0 else f"Q(√{D_0})",
        "estimated_class_number": h_estimate,
        "has_known_small_cm": has_known_cm,
        "endomorphism_ring": (
            f"Z[{f}·ω] ⊂ O_K where K = Q(√{-D_0})"
            if D < 0 else
            "Endomorphism ring analysis requires D < 0 (ordinary curve)"
        ),
        "detail": (
            f"CM discriminant D = {D} = {f}² × {-D_0 if D < 0 else D_0}. "
            f"CM field: Q(√{-D_0}). "
            f"Estimated class number h(D) ≈ {h_estimate}. "
            f"{'Has known small CM discriminant — special structure!' if has_known_cm else 'No known small CM — generic curve.'} "
            f"Class group DLP reduction would require efficient map E(F_q) → Cl(D), which is not known."
        ),
    }


def _check_prime_power(q: int) -> Dict:
    """Check 15: Verify q is not a perfect prime power (needed for Weil descent)."""
    # Check if q = r^m for small m
    is_prime_power = False
    base = None
    exponent = None

    for m in range(2, 133):
        r = round(q ** (1.0 / m))
        # Check r-1, r, r+1 to handle floating point
        for candidate in [r - 1, r, r + 1]:
            if candidate > 1 and pow(candidate, m) == q:
                is_prime_power = True
                base = candidate
                exponent = m
                break
        if is_prime_power:
            break

    return {
        "description": "Prime power field check (Weil descent applicability)",
        "is_prime": _is_probable_prime(q),
        "is_prime_power": is_prime_power,
        "base": base,
        "exponent": exponent,
        "vulnerable": is_prime_power and exponent >= 2,
        "severity": "HIGH" if (is_prime_power and exponent >= 2) else "NONE",
        "detail": (
            f"q is {'a prime power: ' + str(base) + '^' + str(exponent) if is_prime_power else 'a prime (not a prime power)'}. "
            f"{'Weil descent MAY apply — F_q has extension structure!' if is_prime_power and exponent >= 2 else 'Weil descent does NOT apply — F_q is a prime field with no subfield structure.'}"
        ),
        "recommendation": (
            f"Investigate Weil descent: map E(F_{base}^{exponent}) to a higher-genus curve over F_{base}."
            if is_prime_power and exponent >= 2 else None
        ),
        "priority": "HIGH" if (is_prime_power and exponent >= 2) else None,
    }


# ---------------------------------------------------------------------------
# Pretty Printer
# ---------------------------------------------------------------------------

def print_report(results: Dict):
    """Print a comprehensive human-readable analysis report."""
    print()
    print("╔" + "═" * 78 + "╗")
    print("║" + " ASTRA ECCp-131 Mathematical Structure Analysis ".center(78) + "║")
    print("║" + " Certicom Challenge — Structural Weakness Scan ".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    print()

    # Curve parameters
    params = results.get("curve_parameters", {})
    print("┌─ Curve Parameters " + "─" * 59)
    print(f"│  Field prime q  = {params.get('q', '?')}")
    print(f"│  Coefficient a  = {params.get('a', '?')}")
    print(f"│  Coefficient b  = {params.get('b', '?')}")
    print(f"│  Point order n  = {params.get('n', '?')}")
    print(f"│  q bits: {params.get('q_bits', '?')},  n bits: {params.get('n_bits', '?')}")
    print(f"│  Generator P    = {params.get('P', '?')}")
    print(f"│  Target    Q    = {params.get('Q', '?')}")
    print("└" + "─" * 78)
    print()

    # Individual checks
    checks = results.get("checks", {})
    check_order = [
        "anomalous", "supersingular", "frobenius_trace", "cm_discriminant",
        "j_invariant", "embedding_degree", "order_structure", "pohlig_hellman",
        "p_minus_1_smoothness", "p_plus_1_smoothness", "twist_security",
        "automorphisms", "index_calculus", "summation_polynomials",
        "cross_domain", "prime_power_field",
    ]

    for i, name in enumerate(check_order, 1):
        check = checks.get(name)
        if not check or not isinstance(check, dict):
            continue

        desc = check.get("description", name)
        detail = check.get("detail", "")
        vuln = check.get("vulnerable", False)
        severity = check.get("severity", "NONE")
        rec = check.get("recommendation")

        # Status icon
        if vuln:
            icon = "🔴" if severity in ("CRITICAL", "HIGH") else "🟡"
        else:
            icon = "🟢"

        print(f"  {icon}  Check {i}: {desc}")
        # Wrap detail text
        for line in _wrap_text(detail, 72):
            print(f"      {line}")
        if rec:
            print(f"      → Recommendation: {rec}")
        print()

    # Factorizations
    factorizations = results.get("factorizations", {})
    if factorizations:
        print("┌─ Factorizations " + "─" * 60)
        for name, fac in factorizations.items():
            print(f"│  {name}: {fac}")
        print("└" + "─" * 78)
        print()

    # Vulnerabilities summary
    vulns = results.get("vulnerabilities_found", [])
    print("┌─ Vulnerability Summary " + "─" * 54)
    if vulns:
        for v in vulns:
            print(f"│  ⚠️  {v['check']}: {v['detail'][:70]} [{v['severity']}]")
    else:
        print("│  ✅ No exploitable structural weaknesses found.")
        print("│     The curve appears resistant to all known structural attacks.")
    print("└" + "─" * 78)
    print()

    # Recommendations
    recs = results.get("recommendations", [])
    if recs:
        print("┌─ Recommendations " + "─" * 59)
        for r in recs:
            priority = r.get("priority", "LOW")
            print(f"│  [{priority}] {r['check']}: {r['recommendation']}")
        print("└" + "─" * 78)
        print()

    # Verdict
    verdict = results.get("verdict", "Unknown")
    print("═" * 78)
    if "VULNERABILITIES" in verdict.upper():
        print(f"  🚨 VERDICT: {verdict}")
    else:
        print(f"  ✅ VERDICT: {verdict}")
    print(f"  ⏱  Analysis completed in {results.get('analysis_time_sec', '?')} seconds.")
    print("═" * 78)
    print()


def _wrap_text(text: str, width: int) -> List[str]:
    """Simple word-wrap for display."""
    words = text.split()
    lines = []
    current = []
    length = 0
    for word in words:
        if length + len(word) + 1 > width and current:
            lines.append(" ".join(current))
            current = [word]
            length = len(word)
        else:
            current.append(word)
            length += len(word) + 1
    if current:
        lines.append(" ".join(current))
    return lines or [""]


# ---------------------------------------------------------------------------
# Main — Run all analyses
# ---------------------------------------------------------------------------

def main():
    print("\n  Running comprehensive structural analysis of ECCp-131...\n")
    results = analyze_curve_structure()
    print_report(results)

    # Also output key findings as structured data
    print("\n  === Key Numeric Results ===")
    checks = results.get("checks", {})

    trace_info = checks.get("frobenius_trace", {})
    print(f"  Trace of Frobenius t = {trace_info.get('trace_t', '?')}")

    cm_info = checks.get("cm_discriminant", {})
    print(f"  CM discriminant D = {cm_info.get('D', '?')} ({cm_info.get('D_bits', '?')}-bit)")

    j_info = checks.get("j_invariant", {})
    print(f"  j-invariant = {j_info.get('j_hex', '?')}")

    emb_info = checks.get("embedding_degree", {})
    print(f"  Embedding degree k = {emb_info.get('embedding_degree', 'not found (k > ' + str(emb_info.get('checked_up_to', '?')) + ')')}")

    order_info = checks.get("order_structure", {})
    print(f"  Order n is {'PRIME' if order_info.get('is_prime') else 'COMPOSITE'}")

    pm1_info = checks.get("p_minus_1_smoothness", {})
    print(f"  p-1 factorization: {pm1_info.get('factorization', '?')}")
    print(f"  p-1 largest factor: {pm1_info.get('largest_factor_bits', '?')}-bit")

    pp1_info = checks.get("p_plus_1_smoothness", {})
    print(f"  p+1 factorization: {pp1_info.get('factorization', '?')}")
    print(f"  p+1 largest factor: {pp1_info.get('largest_factor_bits', '?')}-bit")

    twist_info = checks.get("twist_security", {})
    print(f"  Twist order is {'prime' if twist_info.get('twist_is_prime') else 'composite: ' + str(twist_info.get('twist_factorization', '?'))}")

    cross_info = checks.get("cross_domain", {})
    print(f"  CM field: {cross_info.get('cm_field', '?')}")
    print(f"  Estimated class number h(D) ≈ {cross_info.get('estimated_class_number', '?')}")

    print()


if __name__ == "__main__":
    main()
