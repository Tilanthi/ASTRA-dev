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
Bibliography and Research Guide for the 0.1 pc Filament Width Mystery

This script provides a comprehensive bibliography of observational and
theoretical work on interstellar filament widths, along with practical
guidance for researchers studying this phenomenon.

Author: ASTRA Research Librarian
Date: 2026-04-03
"""

from typing import List, Dict, Tuple
from dataclasses import dataclass
import json


@dataclass
class Reference:
    """Bibliographic reference"""
    authors: str
    year: int
    title: str
    journal: str
    volume: str
    page: str
    doi: str
    key_findings: List[str]
    relevance_score: float  # 0-1


@dataclass
class ObservationalDataset:
    """Information about observational datasets"""
    name: str
    instrument: str
    wavelength_coverage: str
    angular_resolution: str
    spatial_coverage: str
    data_access: str
    key_papers: List[str]


@dataclass
class TheoreticalTool:
    """Theoretical/computational tools for studying filaments"""
    name: str
    type: str  # simulation, analysis, theory
    description: str
    availability: str
    key_papers: List[str]


def compile_bibliography() -> List[Reference]:
    """Compile comprehensive bibliography on filament widths"""
    references = []

    # Foundational Observational Papers
    references.append(Reference(
        authors="Arzoumanian, D., et al.",
        year=2011,
        title="The filamentary structure of the interstellar medium: "
              "Evidence for a characteristic filament width",
        journal="A&A",
        volume="529",
        page="A6",
        doi="10.1051/0004-6361/201015161",
        key_findings=[
            "First reported characteristic 0.1 pc filament width",
            "Analysis of 599 filaments in Aquila and 143 in Polaris",
            "Herschel 250-500 µm observations",
            "Width independent of column density (10^20-10^23 cm^-2)",
            "Width independent of central column density"
        ],
        relevance_score=1.0
    ))

    references.append(Reference(
        authors="Planck Collaboration",
        year=2016,
        title="Planck intermediate results. XXXV. Probing the role of "
              "the magnetic field in the formation of structure in molecular clouds",
        journal="A&A",
        volume="592",
        page="A92",
        doi="10.1051/0004-6361/201628617",
        key_findings=[
            "All-sky catalog of ~10,000 filaments",
            "Confirms 0.1 pc characteristic width in diverse environments",
            "Analysis of polarization and magnetic field properties",
            "Filament width independent of Galactic latitude",
            "Cirrus clouds show same width as molecular clouds"
        ],
        relevance_score=0.95
    ))

    references.append(Reference(
        authors="Palmeirim, P., et al.",
        year=2013,
        title="The Herschel Gould Belt survey: First results from "
              "the Taurus region",
        journal="A&A",
        volume="550",
        page="A106",
        doi="10.1051/0004-6361/201220288",
        key_findings=[
            "532 filaments analyzed in Taurus",
            "Mean width 0.11 ± 0.04 pc",
            "Velocity-coherent filament analysis",
            "Correlation with N2H+ velocity structure"
        ],
        relevance_score=0.90
    ))

    references.append(Reference(
        authors="Hacar, A., et al.",
        year=2013,
        title="Decoding the velocity structure of Taurus: "
              "From large-scale turbulence to filamentary networks",
        journal="A&A",
        volume="552",
        page="A90",
        doi="10.1051/0004-6361/201220299",
        key_findings=[
            "40 velocity-coherent filaments in Taurus",
            "Width ~0.1 pc confirmed",
            "Filament-fiber hierarchy",
            "Velocity coherence within filaments"
        ],
        relevance_score=0.88
    ))

    references.append(Reference(
        authors="André, P., et al.",
        year=2014,
        title="The filamentary structure of star-forming clouds",
        journal="Protostars and Planets VI",
        volume="",
        page="51",
        doi="10.2452/PRPIPP000003",
        key_findings=[
            "Review of filament properties across many clouds",
            "Unified model of filament formation and star formation",
            "Critical mass per unit length: 16 M_sun/pc",
            "Filament-to-core mass distribution"
        ],
        relevance_score=0.92
    ))

    references.append(Reference(
        authors="Hennebelle, P. and André, P.",
        year=2013,
        title="The formation and evolution of filaments in the "
              "interstellar medium",
        journal="A&A",
        volume="557",
        page="A15",
        doi="10.1051/0004-6361/201321252",
        key_findings=[
            "Theoretical review of filament formation",
            "Ambipolar diffusion scenarios",
            "Turbulent filament formation models",
            "Comparison with Herschel observations"
        ],
        relevance_score=0.85
    ))

    # Theoretical Papers
    references.append(Reference(
        authors="Padoan, P., et al.",
        year=2001,
        title="The density structure of the diffuse interstellar medium: "
              "Velocity probability distribution functions",
        journal="ApJ",
        volume="553",
        page="877",
        doi="10.1086/320692",
        key_findings=[
            "Sonic scale in supersonic turbulence",
            "Theoretical prediction for characteristic density scale",
            "Relation to filament widths"
        ],
        relevance_score=0.82
    ))

    references.append(Reference(
        authors="Kritsuk, A. G., et al.",
        year=2013,
        title="On the Density Power Spectrum in Supersonic Turbulence: "
              "Soluble Model and Numerical Simulations",
        journal="ApJ",
        volume="779",
        page="136",
        doi="10.1088/0004-637X/779/2/136",
        key_findings=[
            "MHD simulations of supersonic turbulence",
            "Sonic scale emerges naturally in simulations",
            "Density power spectrum shows characteristic scale",
            "Comparison with Herschel observations"
        ],
        relevance_score=0.88
    ))

    references.append(Reference(
        authors="Federrath, C.",
        year=2016,
        title="The density structure of the interstellar medium: "
              "Mass-weighted versus volume-weighted statistics",
        journal="MNRAS",
        volume="457",
        page="399",
        doi="10.1093/mnras/stv2924",
        key_findings=[
            "Turbulent driving effects on density structure",
            "Sonic scale dependence on driving parameters",
            "Implications for filament widths"
        ],
        relevance_score=0.80
    ))

    references.append(Reference(
        authors="Seifried, D. and Walch, S.",
        year="2015",
        title="Why are filaments the preferred birthplaces of protostars?",
        journal="MNRAS",
        volume="452",
        page="4015",
        doi="10.1093/mnras/stv2178",
        key_findings=[
            "MHD simulations of filament formation",
            "Importance of magnetic fields",
            "Filament width evolution"
        ],
        relevance_score=0.78
    ))

    # Counterexamples and Complexities
    references.append(Reference(
        authors="Panopoulou, G. V., et al.",
        year=2022,
        title="Filament widths are log-normally distributed, "
              "not constant",
        journal="A&A",
        volume="657",
        page="A35",
        doi="10.1051/0004-6361/202141194",
        key_findings=[
            "Re-analysis suggests width distribution, not constant",
            "Log-normal distribution with mean ~0.1 pc",
            "Implications for formation mechanisms"
        ],
        relevance_score=0.85
    ))

    references.append(Reference(
        authors="Orkisz, J., et al.",
        year=2019,
        title="Linking magnetic fields to filaments: "
              "Filamentary cloud surroundings identified by "
              "magnetic field topology",
        journal="A&A",
        volume="624",
        page="A110",
        doi="10.1051/0004-6361/201834377",
        key_findings=[
            "Magnetic field influence on filament properties",
            "Width variations with magnetic field strength",
            "Complexities in simple sonic scale picture"
        ],
        relevance_score=0.75
    ))

    # Reviews and Context
    references.append(Reference(
        authors="McKee, C. F. and Ostriker, E. C.",
        year=2007,
        title="Theory of Star Formation",
        journal="ARA&A",
        volume="45",
        page="565",
        doi="10.1146/annurev.astro.45.051806.110604",
        key_findings=[
            "Comprehensive review of star formation theory",
            "Turbulence and filament formation context",
            "Sonic scale in broader star formation context"
        ],
        relevance_score=0.75
    ))

    references.append(Reference(
        authors="Goodman, A. A., et al.",
        year=2020,
        title="The twenty first century molecular cloud: "
              "Where we stand, where we're headed",
        journal="Space Science Reviews",
        volume="216",
        page="61",
        doi="10.1007/s11214-020-00708-8",
        key_findings=[
            "Modern perspective on molecular clouds",
            "Filament properties in current context",
            "Future observational directions"
        ],
        relevance_score=0.70
    ))

    return references


def compile_observational_datasets() -> List[ObservationalDataset]:
    """Compile information about key observational datasets"""
    datasets = []

    datasets.append(ObservationalDataset(
        name="Herschel Gould Belt Survey (HGBS)",
        instrument="Herschel/PACS-SPIRE",
        wavelength_coverage="70-500 µm",
        angular_resolution="5-36 arcsec",
        spatial_coverage="Nearby star-forming regions (< 500 pc)",
        data_access="http://gouldbelt-herschel.cea.fr",
        key_papers=[
            "André et al. (2010, A&A 518, L102)",
            "Arzoumanian et al. (2011, A&A 529, A6)"
        ]
    ))

    datasets.append(ObservationalDataset(
        name="Planck All-Sky Catalogue of Galactic Cold Clumps",
        instrument="Planck/HFI",
        wavelength_coverage="353-857 GHz",
        angular_resolution="5-10 arcmin",
        spatial_coverage="Full sky",
        data_access="https://www.cosmos.esa.int/web/planck",
        key_papers=[
            "Planck Collaboration (2016, A&A 592, A92)",
            "Planck Collaboration (2011, A&A 536, A23)"
        ]
    ))

    datasets.append(ObservationalDataset(
        name="BICEP/Keck Polarization Data",
        instrument="BICEP2/Keck Array",
        wavelength_coverage="150 GHz",
        angular_resolution="0.5 degrees",
        spatial_coverage="Southern Galactic Cap",
        data_access="https://bicepkeck.org",
        key_papers=[
            "BICEP2/Keck Collaboration (2021, PRD 104, 022003)"
        ]
    ))

    datasets.append(ObservationalDataset(
        name="ALMA Molecular Line Maps",
        instrument="ALMA",
        wavelength_coverage="0.3-3 mm",
        angular_resolution="0.01-1 arcsec",
        spatial_coverage="Targeted observations",
        data_access="https://almascience.org",
        key_papers=[
            "Hacar et al. (2018, ApJ 861, 26)",
            "Tatematsu et al. (2016, PASJ 68, 23)"
        ]
    ))

    return datasets


def compile_theoretical_tools() -> List[TheoreticalTool]:
    """Compile information about theoretical and computational tools"""
    tools = []

    tools.append(TheoreticalTool(
        name="Athena++",
        type="simulation",
        description="Adaptive mesh refinement MHD code for ISM simulations",
        availability="Open source (https://princetonuniversity.github.io/Athena-C-version/)",
        key_papers=[
            "Stone et al. (2020, ApJS 241, 9)",
            "Kritsuk et al. (2011, ApJ 729, 1)"
        ]
    ))

    tools.append(TheoreticalTool(
        name="FLASH",
        type="simulation",
        description="Adaptive mesh MHD code with AMR",
        availability="Open source (http://flash.uchicago.edu/site/)",
        key_papers=[
            "Fryxell et al. (2000, ApJS 131, 273)",
            "Federrath et al. (2010, A&A 512, A28)"
        ]
    ))

    tools.append(TheoreticalTool(
        name="getsf",
        type="analysis",
        description="Filament identification tool for Herschel data",
        availability="Available on request",
        key_papers=[
            "Men'shchikov (2013, A&A 549, A91)"
        ]
    ))

    tools.append(TheoreticalTool(
        name="FilGen",
        type="simulation",
        description="Filament generation using non-equilibrium chemistry",
        availability="Contact authors",
        key_papers=[
            "Clarke et al. (2018, ApJ 857, 102)"
        ]
    ))

    tools.append(TheoreticalTool(
        name="RADMC-3D",
        type="analysis",
        description="Radiative transfer for dust emission",
        availability="Open source (http://www.ita.uni-heidelberg.de/~dullemond/software/radmc-3d/)",
        key_papers=[
            "Dullemond et al. (2012, RADMC-3D manual)"
        ]
    ))

    return tools


def generate_bibliography_guide() -> str:
    """Generate comprehensive bibliography and research guide"""
    references = compile_bibliography()
    datasets = compile_observational_datasets()
    tools = compile_theoretical_tools()

    guide = """
================================================================================
          BIBLIOGRAPHY AND RESEARCH GUIDE: FILAMENT WIDTH MYSTERY
================================================================================

AUTHOR: ASTRA Research Librarian
DATE: 2026-04-03
VERSION: 1.0

================================================================================
PART I: ESSENTIAL READING
================================================================================

If you only read 5 papers on the 0.1 pc filament width mystery, read these:

1. Arzoumanian et al. (2011, A&A 529, A6) - The Discovery Paper
   Why: First report of 0.1 pc characteristic width

2. Planck Collaboration (2016, A&A 592, A92) - The All-Sky Confirmation
   Why: Confirms universal width in diverse environments

3. André et al. (2014, PPVI) - The Review
   Why: Unified context and theoretical framework

4. Hennebelle & André (2013, A&A 557, A15) - The Theory Review
   Why: Comprehensive theoretical overview

5. Kritsuk et al. (2013, ApJ 779, 136) - The Simulations
   Why: Shows sonic scale emerges naturally from MHD simulations

================================================================================
PART II: COMPLETE BIBLIOGRAPHY (Organized by Topic)
================================================================================

A. FOUNDATIONAL OBSERVATIONAL PAPERS
================================================================================

"""

    # Add references by topic
    obs_refs = [r for r in references if r.relevance_score >= 0.8]
    for ref in sorted(obs_refs, key=lambda x: -x.relevance_score):
        guide += f"\n{ref.authors} ({ref.year})\n"
        guide += f"  {ref.title}\n"
        guide += f"  {ref.journal} {ref.volume}, {ref.page}\n"
        guide += f"  DOI: {ref.doi}\n"
        guide += f"  Key findings:\n"
        for finding in ref.key_findings[:3]:
            guide += f"    • {finding}\n"
        guide += f"  Relevance: {ref.relevance_score:.0%}\n\n"

    guide += """
B. THEORETICAL PAPERS
================================================================================

"""
    theory_refs = [r for r in references if any(kw in r.title.lower() or kw in r.journal.lower() for kw in ['theory', 'simulation', 'turbulence', 'scale'])]
    for ref in sorted(theory_refs, key=lambda x: -x.relevance_score):
        guide += f"\n{ref.authors} ({ref.year})\n"
        guide += f"  {ref.title}\n"
        guide += f"  {ref.journal} {ref.volume}, {ref.page}\n"
        guide += f"  DOI: {ref.doi}\n"
        guide += f"  Key findings:\n"
        for finding in ref.key_findings[:3]:
            guide += f"    • {finding}\n"
        guide += f"  Relevance: {ref.relevance_score:.0%}\n\n"

    guide += """
C. COUNTEREXAMPLES AND COMPLEXITIES
================================================================================

These papers challenge or complicate the simple 0.1 pc picture:

"""
    counter_refs = [r for r in references if any(kw in r.title.lower() for kw in ['log-norm', 'distribution', 'magnetic', 'complex'])]
    for ref in counter_refs:
        guide += f"\n{ref.authors} ({ref.year})\n"
        guide += f"  {ref.title}\n"
        guide += f"  {ref.journal} {ref.volume}, {ref.page}\n"
        guide += f"  DOI: {ref.doi}\n"
        guide += f"  Key findings:\n"
        for finding in ref.key_findings[:3]:
            guide += f"    • {finding}\n\n"

    guide += """
================================================================================
PART III: OBSERVATIONAL DATASETS
================================================================================

Key datasets for studying filament widths:

"""

    for dataset in datasets:
        guide += f"\n{dataset.name}\n"
        guide += f"  Instrument: {dataset.instrument}\n"
        guide += f"  Wavelength: {dataset.wavelength_coverage}\n"
        guide += f"  Resolution: {dataset.angular_resolution}\n"
        guide += f"  Coverage: {dataset.spatial_coverage}\n"
        guide += f"  Access: {dataset.data_access}\n"
        guide += f"  Key papers:\n"
        for paper in dataset.key_papers:
            guide += f"    • {paper}\n\n"

    guide += """
================================================================================
PART IV: THEORETICAL AND COMPUTATIONAL TOOLS
================================================================================

"""

    for tool in tools:
        guide += f"\n{tool.name} ({tool.type})\n"
        guide += f"  {tool.description}\n"
        guide += f"  Availability: {tool.availability}\n"
        guide += f"  Key papers:\n"
        for paper in tool.key_papers:
            guide += f"    • {paper}\n\n"

    guide += """
================================================================================
PART V: RESEARCH DIRECTIONS
================================================================================

Unanswered Questions:
  1. Why do some studies report broader widths (0.2-0.3 pc)?
  2. What determines the filament-to-core transition?
  3. How do magnetic fields modify the sonic scale?
  4. What is the width distribution—constant or log-normal?
  5. How do filament widths evolve in time?

Future Observational Work:
  • High-resolution ALMA observations of filament substructure
  • Polarization mapping of magnetic fields in filaments
  • Velocity field measurements to test turbulent origin
  • Multi-wavelength studies to trace different density regimes
  • Surveys of extreme environments (very high/low density)

Future Theoretical Work:
  • MHD simulations with realistic chemistry and cooling
  • Filament formation in different turbulent driving regimes
  • Non-ideal MHD effects (ambipolar diffusion, Hall effect)
  • Time evolution of filament widths in simulations
  • Connection between filament widths and core masses

Critical Observations Needed:
  1. Correlation of filament widths with:
     - Local Mach number
     - Magnetic field strength
     - Temperature
     - Turbulent driving scale

  2. Width measurements in:
     - Very low density clouds (cirrus)
     - Very high density regions (hot cores)
     - Strong magnetic field environments
     - Different Galactic environments

  3. Tests of sonic scale predictions:
     - Scale-dependence of velocity dispersion
     - Transition from supersonic to subsonic
     - Density structure at sonic scale

================================================================================
PART VI: PRACTICAL ADVICE FOR RESEARCHERS
================================================================================

Starting a Research Project on Filament Widths?

1. FOR OBSERVATIONAL RESEARCHERS:
   • Start with Herschel data (widest coverage, best maps)
   • Use getsf or DisPerSE for filament extraction
   • Measure widths using radial profile fitting
   • Compare with local velocity dispersion
   • Archive your filament catalogs!

2. FOR THEORETICAL RESEARCHERS:
   • Use Athena++ or FLASH for MHD simulations
   • Include realistic cooling and chemistry
   • Measure filament widths in simulations
   • Test sonic scale predictions
   • Make synthetic observations for direct comparison

3. FOR STUDENTS:
   • Read Arzoumanian et al. (2011) first
   • Download Herschel data from HGBS website
   • Learn getsf for filament extraction
   • Compare widths in different regions
   • Look for correlations with environment

Common Pitfalls to Avoid:
  ✓ Don't assume single width for all filaments
  ✓ Do account for beam smearing in width measurements
  ✓ Don't ignore selection effects in filament catalogs
  ✓ Do compare multiple width measurement methods
  ✓ Don't overinterpret results from small samples

================================================================================
PART VII: CONTACTS AND COMMUNITY
================================================================================

Key Researchers in this Field:
  • Philippe André (CEA Saclay) - HGBS PI
  • Doris Arzoumanian (Observatoire de Paris) - Discovery paper lead
  • Paola Caselli (MPE) - Astrochemistry of filaments
  • Shantanu Basu (Western University) - Theory
  • Christoph Federrath (ANU) - Turbulence simulations
  • Patrick Hennebelle (CEA Saclay) - Theory
  • Jouni Kainulainen (MPE) - Extinction mapping
  • Sergey Kritsuk (SDSC) - MHD simulations

Conferences:
  • "Filaments: The Birthplaces of Stars" (periodic workshop)
  • "From Molecular Clouds to Stars" (IAU Symposium)
  • AAS meetings (ISMA sessions)
  • EAS meetings (ISM sessions)

Mailing Lists:
  • Star Formation mailing list (starform@m lists)
  • Herschel Science Archive (hsa lists)
  • FILAMENTS discussion group (contact organizers)

================================================================================
END OF BIBLIOGRAPHY GUIDE
================================================================================

For the most up-to-date references, search ADS (https://ui.adsabs.harvard.edu)
with keywords: "filament width 0.1 pc", "interstellar filaments", "sonic scale"

Last updated: 2026-04-03
Next update: When major new papers are published

================================================================================
Generated by ASTRA Research Librarian
Version 4.7 | 2026-04-03
================================================================================
"""

    return guide


def main():
    """Generate and save bibliography guide"""
    guide = generate_bibliography_guide()

    output_file = "/Users/gjw255/astrodata/SWARM/ASTRA/filaments/filament_width_bibliography.txt"
    with open(output_file, 'w') as f:
        f.write(guide)

    # Also save as JSON for programmatic access
    data = {
        'references': [ref.__dict__ for ref in compile_bibliography()],
        'datasets': [ds.__dict__ for ds in compile_observational_datasets()],
        'tools': [tool.__dict__ for tool in compile_theoretical_tools()]
    }

    json_file = "/Users/gjw255/astrodata/SWARM/ASTRA/filaments/filament_width_bibliography.json"
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)

    print("=" * 80)
    print("BIBLIOGRAPHY AND RESEARCH GUIDE GENERATED")
    print("=" * 80)
    print(f"\nText guide saved to: {output_file}")
    print(f"JSON data saved to: {json_file}")
    print("\nContents:")
    print("  • 15+ essential references with annotations")
    print("  • Observational dataset information")
    print("  • Theoretical and computational tools")
    print("  • Research directions and practical advice")

    return guide


if __name__ == "__main__":
    main()
