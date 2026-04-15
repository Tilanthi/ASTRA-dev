#!/usr/bin/env python3

# Copyright 2024-2026 Glenn J. White (The Open University / RAL Space)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Initialize ASTRA with baseline astrophysical hypotheses.
Run this to populate the hypothesis queue when starting fresh.
"""
import sys
sys.path.insert(0, '/Users/gjw255/astrodata/SWARM/ASTRA-dev-main')

from astra_live_backend.hypotheses import HypothesisStore, Phase
from astra_live_backend.state_persistence import save_hypotheses

# Initialize store
store = HypothesisStore()

# Core astrophysical hypotheses (18 total)
hypotheses = [
    ("H001", "Pantheon+ SNe Ia Distance Modulus", "Astrophysics",
     "Test ΛCDM distance-redshift relation using 1,701 Pantheon+ Type Ia supernovae. "
     "Constrain H0 and w(z) through Bayesian model comparison with Planck/SH0ES predictions.",
     "pantheon"),

    ("H002", "SDSS Galaxy Color Bimodality", "Astrophysics",
     "Quantify red sequence and blue cloud separation in SDSS DR18 galaxy photometry. "
     "Fit Gaussian mixture model to g-r color distribution, measure green valley fraction.",
     "sdss"),

    ("H003", "Exoplanet Mass-Period Relation", "Astrophysics",
     "Test Kepler's Third Law scaling in NASA Exoplanet Archive confirmed planets. "
     "Power-law fit between log(mass) and log(period), compare to theoretical P∝M^(1/3) prediction.",
     "exoplanets"),

    ("H004", "Gaia Main Sequence Structure", "Astrophysics",
     "Characterize main sequence width and structure in Gaia DR3 HR diagram. "
     "Measure scatter as function of metallicity, test for multiple populations.",
     "gaia"),

    ("H005", "SDSS Redshift Clustering", "Astrophysics",
     "Test for significant galaxy clustering in SDSS spectroscopic redshift distribution. "
     "KS test against uniform distribution, quantify large-scale structure signal.",
     "sdss"),

    ("H006", "Exoplanet Period Valley", "Astrophysics",
     "Test for bimodal period distribution around 10 days in NASA Exoplanet Archive. "
     "Search for hot Neptune desert and period valley in confirmed transiting planets.",
     "exoplanets"),

    ("H007", "Gaia Parallax Systematic Errors", "Astrophysics",
     "Quantify systematic parallax errors in Gaia DR3 via magnitude- and position-dependent analysis. "
     "Test for correlations between parallax residual and G magnitude, sky position.",
     "gaia"),

    ("H008", "SDSS Star Formation Rate", "Astrophysics",
     "Use u-r color as star formation rate proxy in SDSS galaxies. "
     "Measure correlation between SFR indicator and redshift, test for evolution.",
     "sdss"),

    ("H009", "Exoplanet Transit Depth Distribution", "Astrophysics",
     "Analyze distribution of transit depths in NASA Exoplanet Archive. "
     "Test for multiple populations (hot Jupiters vs mini-Nepterts vs super-Earths).",
     "exoplanets"),

    ("H010", "Hubble Tension Model Comparison", "Astrophysics",
     "Compare Planck 2018 and SH0ES 2022 H0 constraints using Pantheon+ distance moduli. "
     "Bayesian model selection via χ² and BIC, quantify tension significance.",
     "pantheon"),

    ("H011", "LIGO Chirp Mass Distribution", "Astrophysics",
     "Test for bimodal chirp mass distribution in LIGO/Virgo GWTC events. "
     "KS test against power-law model, search for sub-populations.",
     "ligo"),

    ("H012", "Planck CMB Acoustic Peaks", "Astrophysics",
     "Measure angular scale of acoustic peaks in Planck 2018 TT power spectrum. "
     "Constrain cosmological parameters via peak position and amplitude analysis.",
     "planck"),

    ("H013", "ZTF Transient Classification", "Astrophysics",
     "Test SNe vs non-SNe classification in ZTF transient light curves. "
     "Use statistical features (rise time, peak magnitude, color evolution) for automated classification.",
     "ztf"),

    ("H014", "TESS Exoplanet Mass-Radius Relation", "Astrophysics",
     "Measure mass-radius relation for TESS-hosted exoplanets with RV follow-up. "
     "Power-law fit to test theoretical M∝R relation for different compositions.",
     "tess"),

    ("H015", "SDSS Cluster Richness-Mass Relation", "Astrophysics",
     "Test redMaPPer richness as mass proxy in SDSS galaxy clusters. "
     "Measure scatter in richness-mass relation, test for redshift evolution.",
     "sdss"),

    ("H016", "GW-EM Multi-Messenger Follow-up", "Astrophysics",
     "Cross-match LIGO GW events with ZTF transients for electromagnetic counterparts. "
     "Test for temporal and spatial coincidence, quantify counterpart detection efficiency.",
     "ligo"),

    ("H017", "TESS-Gaia Stellar Parameters", "Astrophysics",
     "Link TESS Input Catalog host stars with Gaia DR3 astrometry for precise stellar parameters. "
     "Improve radius and luminosity estimates via parallax constraints.",
     "tess"),

    ("H018", "SDSS Quasar clustering", "Astrophysics",
     "Measure quasar clustering in SDSS spectroscopic sample. "
     "Test for redshift-dependent clustering strength, constrain dark matter halo masses.",
     "sdss"),
]

# Add all hypotheses
for hid, name, domain, desc, source in hypotheses:
    h = store.add(name, domain, desc, confidence=0.35)
    h.phase = Phase.TESTING
    h.data_source = source
    h.priority = "normal"
    print(f"Added {hid}: {name}")

# Add proposed hypotheses (3-5 to maintain queue)
proposed = [
    ("H019", "SDSS g-r Color vs Redshift Evolution", "Astrophysics",
     "Track g-r color evolution with redshift in SDSS DR18 galaxies. "
     "Test for star formation history evolution across cosmic time.",
     "sdss"),

    ("H020", "Gaia Proper Motion Kinematics", "Astrophysics",
     "Analyze velocity distributions from Gaia DR3 proper motions. "
     "Identify stellar populations via kinematic clustering.",
     "gaia"),

    ("H021", "Exoplanet Radius Gap Edge Detection", "Astrophysics",
     "Locate Fulton gap (radius valley) in NASA Exoplanet archive. "
     "Measure gap center and width as function of orbital period.",
     "exoplanets"),

    ("H022", "Pantheon+ Hubble Diagram Residuals", "Astrophysics",
     "Analyze residuals from ΛCDM fit to Pantheon+ distance moduli. "
     "Test for redshift-dependent systematics or new physics.",
     "pantheon"),

    ("H023", "SDSS Emission Line Diagnostics", "Astrophysics",
     "Use [OIII]/Hβ vs [NII]/Hα diagnostic diagram for SDSS galaxies. "
     "Classify star-forming vs AGN populations, measure mixing fraction.",
     "sdss"),
]

for hid, name, domain, desc, source in proposed:
    h = store.add(name, domain, desc, confidence=0.20)
    h.phase = Phase.PROPOSED
    h.data_source = source
    h.priority = "normal"
    print(f"Added {hid}: {name} [PROPOSED]")

# Save state
save_hypotheses(store)
print(f"\n✅ Initialized {len(store.hypotheses)} hypotheses")
print(f"   Saved to astra_state/hypotheses.json")
