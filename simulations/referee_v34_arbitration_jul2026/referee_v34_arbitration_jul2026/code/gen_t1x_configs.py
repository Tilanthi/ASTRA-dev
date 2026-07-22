#!/usr/bin/env python3
"""T1X: expanded T1/eta_W calibration grid (referee major point 5).

Extends the Jul 2026 E-suite forward-model calibration (6 runs, beta=1.0 only)
to 27 runs: f in {0.5,0.7,0.9} x beta in {0.5,1.0,2.0} x seeds {42,137,251}.
Same paper configuration (user BCs, 1 lambda_J transverse box, r64) and the
same OLD binary (/home/fetch-agi/athena/bin/athena) as the July E/B suites so
that results feed the existing synthetic-HGBS forward-model pipeline
unchanged.
"""
import json
from pathlib import Path
from common import add

manifest = {'purpose': 'T1X expanded eta_W calibration (referee v34 pt 5)',
            'suites': {}, 'total_sims': 0}

for f in (0.5, 0.7, 0.9):
    for beta in (0.5, 1.0, 2.0):
        for s in (42, 137, 251):
            pid = f'T1X_f{f}_b{beta}_th0_Lx8_s{s}'
            add(manifest, 'P2a_t1x', pid, 'configs_v34',
                f=f, beta=beta, theta=0.0, Lx=8, seed=s,
                perturb=1e-2, odt=0.02, tlim=0.5)

manifest['total_sims'] = sum(len(v) for v in manifest['suites'].values())
Path('configs_v34', 'manifest_t1x.json').write_text(
    json.dumps(manifest, indent=2))
print('T1X total', manifest['total_sims'])
