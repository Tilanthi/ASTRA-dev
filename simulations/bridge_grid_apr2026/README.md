# BRIDGE_GRID Campaign — θ=90° Perpendicular Field Grid (Apr 2026)

48 MHD simulations: f=1.1-2.0, beta=0.3-5.0, M=1.0, theta=90 deg, seeds 42+137.
Addresses Peer Review Issue #3 (PR2026 FINAL theta=90 stability result was an FFT gravity artifact).

## Key Result
**48/48 FRAG** — no genuine stability at theta=90 across any tested parameters.
The PR2026 FINAL 'complete perpendicular stability' was caused by np=16 vs 24 FFT meshblocks
(FATAL gravity error), plus insufficient timeout (600-720s vs 1800s needed).

## Files
- BRIDGE_GRID_CAMPAIGN_REPORT.md — full science report
- bridge_grid_reclassified_v2.json — per-sim results (stdout-corrected)
- tfrag_table.csv — t_frag grid (f x beta)
- figures/ — 4 publication-quality figures (PDF+PNG)
- reclassify_v2.py — authoritative stdout-based classifier

## t_frag Summary (t_J, mean of 2 seeds)
f=1.1: beta=0.3: 0.324, beta=1.0: 0.390, beta=5.0: 0.429
f=1.4: beta=0.3: 0.303, beta=1.0: 0.365, beta=5.0: 0.382
f=1.8: beta=0.3: 0.283, beta=1.0: 0.339, beta=5.0: 0.339
f=2.0: beta=0.3: 0.275, beta=1.0: 0.328, beta=5.0: 0.322
Overall mean: 0.346 +/- 0.041 t_J
