# CALIBRATION_EXTENSION Campaign Report
## theta=0 Field-Geometry Calibration at f=1.3-2.0 (Apr 2026)
Date: 2026-04-28  Wall time: 18:22-19:32 UTC (1h 10min)
Cluster: astra-climate (224 vCPU)

## Science Context
Addresses Peer Review Issue: does calibration factor C(f,beta)=lambda_frag/lambda_MJ
remain constant at ~1.11 across f=1.3-2.0, or vary with supercriticality?

## Configuration
  f: 1.3, 1.4, 1.5, 1.6, 1.8, 2.0
  beta: 0.3, 0.5, 1.0
  theta: 0 deg (longitudinal B)
  M: 1.0, seeds: 42, 137
  Mesh: 256x64x64, meshblocks 32x32x32, np=16
  Domain: 8x2x2 lambda_J
  tlim: 6.0 t_J, timeout: 3600s

## Results Summary: 36/36 FRAG (100%) — No stability

t_frag table (t_J, mean of 2 seeds):
  f=1.3: beta=0.3: 0.2946, beta=0.5: 0.3474, beta=1.0: 0.3631
  f=1.4: beta=0.3: 0.2896, beta=0.5: 0.3407, beta=1.0: 0.3533
  f=1.5: beta=0.3: 0.2968, beta=0.5: 0.3377, beta=1.0: 0.3429
  f=1.6: beta=0.3: 0.3009, beta=0.5: 0.3300, beta=1.0: 0.3312
  f=1.8: beta=0.3: 0.2883, beta=0.5: 0.3108, beta=1.0: 0.3136
  f=2.0: beta=0.3: 0.2782, beta=0.5: 0.2994, beta=1.0: 0.2992
  Overall: mean=0.3176 +/- 0.0251 t_J, range=[0.2782, 0.3631] t_J

## Physical Trends

1. t_frag DECREASES with f (higher supercriticality -> faster collapse):
   beta=1.0: 0.363 -> 0.299 t_J from f=1.3 to f=2.0

2. t_frag INCREASES with beta (stronger B -> faster collapse):
   f=1.3: beta=0.3 (0.295) < beta=0.5 (0.347) < beta=1.0 (0.363)
   INVERTED from expected longitudinal stabilisation.

3. beta=0.5 and beta=1.0 converge at high f: Δ=0.016 t_J at f=1.3, Δ=0.000 at f=2.0.

4. Seed independence: < 0.001 t_J between s42 and s137 at every grid point.

## Key Finding: Likely Radial Collapse (Not Longitudinal Beading)

CRITICAL: t_frag range (0.28-0.36 t_J) matches the BRIDGE_GRID theta=90 result,
NOT the DTC longitudinal FRAG cases (0.46-1.43 t_J).

Evidence for radial collapse:
  (a) Timescale ~0.3 t_J: too fast for longitudinal beading at theta=0
  (b) Inverted beta dependence: longitudinal B should SUPPORT against theta=0 modes
      but we see lower-beta (stronger B) fragmenting FASTER
  (c) DTC beta=0.3 stable ridge was measured on 4x4x2 domain; here 8x2x2 domain
      with narrower cross-section may suppress magnetic stabilisation

HDF5 ISSUE: snapshots at dt=0.5 t_J are post-collapse (collapse at ~0.30 t_J).
No snap captures the morphology at fragmentation time.

## Comparison with DTC Campaign (theta=0, different domain)

DTC (4x4x2 domain, 128x48x48 mesh):
  - beta=0.3, M=1, f=1.4-2.2: ALL STABLE (t_frag > 1.5 t_J)
  - beta=1.0, M=1: FRAG at t_frag=0.46-1.43 t_J

CALIB_EXT (8x2x2 domain, 256x64x64 mesh):
  - beta=0.3, M=1, f=1.3-2.0: ALL FRAG at t_frag=0.28-0.30 t_J
  - beta=1.0, M=1: FRAG at t_frag=0.30-0.36 t_J

The DTC stable ridge DOES NOT APPEAR in this domain/resolution combination.
Domain geometry critically affects the stability threshold.

## Implications

1. The DTC stable ridge (beta=0.3, M=1) is domain-dependent - caution in paper.
2. C(f,beta) calibration CANNOT be derived from these sims (radial collapse, not beading).
3. RECOMMENDED: Targeted rerun with 4x2x2 domain (matching DTC x1 length), 
   HDF5 at dt=0.05 t_J to capture morphology at t~0.3 t_J.

## Technical Notes
  np=16 (NOT 24) required for 256x64x64 / 32x32x32 meshblocks (32 total, np=24 FATAL)
  Manual kills at ~25 min when all sims past dt threshold (saves 35 min per batch)
  Classifier: stdout-based t_frag detection (HST misses rapid collapse)
