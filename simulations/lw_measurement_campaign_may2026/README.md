# λ/W Measurement Campaign — May 2026

**Completed**: 2026-05-02 03:38 UTC | astra-climate 220 vCPU AMD EPYC

## Campaign Summary
66 Athena++ MHD simulations across 3 sub-campaigns measuring fragmentation wavelength λ/W.

| Campaign | Sims | θ | Domain | Domain Lx | Result |
|----------|------|---|--------|-----------|--------|
| DOMAIN_TEST | 3 | 0° | 1024×64×64 | 32 λ_J | λ/W=8.39±1.6 |
| LW_DIRECT | 36 | 0° | 1024×64×64 | 32 λ_J | λ/W=7.02±3.07 |
| PERP_TIMESERIES | 27 | 90° | 768×64×64 | 24 λ_J | **λ/W=1.631±0.034** |

## Key Science Results

### Perpendicular B (θ=90°) — λ/W = 1.631 ± 0.034
- **Universal**: independent of f∈[1.0,2.0], β∈[0.3,3.0], random seed
- 27/27 BEADING, 23–26 peaks per simulation
- C6 (short domain, 16 λ_J) gave λ/W=1.25; this campaign gives more reliable λ/W=1.63
- β=0.3 shows full axial fragmentation (C6 FLAT_PROFILE was domain-length artefact)

### Longitudinal B (θ=0°) — λ/W = 7.02 ± 3.07, strongly β-dependent
- β=0.3–1.0: λ/W ≈ 6–10 (strong B suppresses short-λ modes; few, widely-spaced fragments)
- β=3.0: λ/W ≈ 2.2–2.8 (~Nagasawa thermal limit: 16–27 peaks per sim)
- Domain-size effect: C5/C7 (8 λ_J) gave λ/W=3.44; 32 λ_J domain gives more natural mode

### Longitudinal/Perpendicular Ratio
- β=0.3: λ/W_para / λ/W_perp ≈ 7.5/1.63 ≈ 4.6×
- β=3.0: λ/W_para / λ/W_perp ≈ 2.5/1.63 ≈ 1.5×

## Files
- `lw_campaign_results_may2026.tar.gz` — All JSON results + logs
- Contains: DOMAIN_TEST_lw_results.json, LW_DIRECT_lw_results.json, PERP_TIMESERIES_lw_results.json, all_results.json

## Technical Notes
- Runner: /data/lw_campaign_runner.py (custom, from scratch — provided run_campaign.py had HDF5 format errors)
- Watchdog v2: /data/lw_watchdog_v2.py — kills sims with dt<1e-5 OR HST stale for 180s
- Athena++ v24 HDF5: prim[0] = density, shape (nmb, nx3, nx2, nx1), LogicalLocations for block positions
- FFT gravity: perpendicular-B sims need np=24 with 32-cell meshblocks in x (768/32=24)
- Domain size effect: important systematic — longer domains give larger λ/W for longitudinal B
