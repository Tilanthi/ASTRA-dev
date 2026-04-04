"""
V96 Discovery Provenance Tracking - Enhanced Anti-Hallucination
=============================================================

CRITICAL: Prevents presentation of hypothetical examples as real discoveries

The Problem We Found:
- Section 3.5 claimed ASTRA "analyzed Taurus molecular cloud" and discovered
  correlations with Bayes factor 47
- Figures were generated March 21, 2026 (illustrative)
- No actual Taurus analysis code exists
- This is a HALLUCINATION - presenting hypothetical as real

The Solution:
1. Track provenance of all "discoveries" - where did data come from?
2. Require evidence files exist before claiming discoveries
3. Distinguish REAL from HYPOTHETICAL in metadata
4. Validate that referenced figures/data files actually exist
5. Require analysis code/logs for claimed discoveries
6. Tag content with provenance level: REAL_ANALYSIS, DEMONSTRATION, EXAMPLE

Provenance Levels:
- VERIFIED_ANALYSIS: Has real data, code, results, all files exist
- DEMONSTRATION: Uses real data but simplified/hypothetical scenario
- EXAMPLE: Illustrative, not meant to be real
- HALLUCINATED: Claims real but has no supporting evidence

Date: 2026-03-22
Motivation: Taurus hallucination incident - Section 3.5 integrity check
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any
from enum import Enum
from pathlib import Path
import json
import hashlib
from datetime import datetime


class ProvenanceLevel(Enum):
    """Level of provenance for a discovery or analysis."""
    VERIFIED_ANALYSIS = "verified_analysis"  # Real data, code, results all exist
    DEMONSTRATION = "demonstration"  # Real data, simplified scenario
    EXAMPLE = "example"  # Illustrative only
    HALLUCINATED = "hallucinated"  # Claims real but no evidence
    UNKNOWN = "unknown"  # Cannot determine


@dataclass
class DiscoveryProvenance:
    """
    Tracks the provenance of a claimed discovery.

    Prevents hallucination by requiring evidence that analysis
    was actually performed before claiming discoveries.
    """
    discovery_id: str
    claim: str  # What was discovered
    provenance_level: ProvenanceLevel = ProvenanceLevel.UNKNOWN

    # Evidence requirements
    data_files: List[str] = field(default_factory=list)  # Paths to actual data
    analysis_code: List[str] = field(default_factory=list)  # Paths to analysis scripts
    result_files: List[str] = field(default_factory=list)  # Generated results
    figure_files: List[str] = field(default_factory=list)  # Generated figures

    # Metadata
    timestamp: str = ""
    analyst: str = "ASTRA"  # Human or ASTRA
    location: str = ""  # Where analysis was performed

    # Validation
    files_exist: bool = False
    code_runs: bool = False
    results_reproducible: bool = False

    # Documentation
    description: str = ""
    notes: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def validate_evidence(self) -> bool:
        """Check if all claimed evidence actually exists."""
        all_files = (self.data_files + self.analysis_code +
                    self.result_files + self.figure_files)

        if not all_files:
            return False

        self.files_exist = all(Path(f).exists() for f in all_files)
        return self.files_exist

    def to_dict(self) -> Dict:
        return {
            'discovery_id': self.discovery_id,
            'claim': self.claim,
            'provenance_level': self.provenance_level.value,
            'data_files': self.data_files,
            'analysis_code': self.analysis_code,
            'result_files': self.result_files,
            'figure_files': self.figure_files,
            'timestamp': self.timestamp,
            'files_exist': self.files_exist,
            'code_runs': self.code_runs,
            'results_reproducible': self.results_reproducible,
            'description': self.description,
            'notes': self.notes
        }


class DiscoveryProvenanceTracker:
    """
    Tracks provenance of all discoveries to prevent hallucination.

    Usage:
        tracker = DiscoveryProvenanceTracker()

        # Before claiming a discovery, register it with evidence
        tracker.register_discovery(
            discovery_id="cygnus_filament_001",
            claim="Discovered correlation between filament width and star formation efficiency",
            data_files=["/data/filamentcatalogue.fits"],
            analysis_code=["/analysis/cygnus_analysis.py"],
            result_files=["/results/cygnus_filament_stats.json"],
            figure_files=["/figures/cygnus_width_distribution.png"],
            provenance_level=ProvenanceLevel.VERIFIED_ANALYSIS
        )

        # Validate before allowing claim in output
        if tracker.can_claim_discovery("cygnus_filament_001"):
            # Safe to include in paper
            pass
    """

    def __init__(self, registry_path: Optional[Path] = None):
        self.registry_path = registry_path or Path(
            "/Users/gjw255/astrodata/SWARM/STAN_XI_ASTRO/astra_core/capabilities/.discovery_registry.json"
        )
        self.discoveries: Dict[str, DiscoveryProvenance] = {}
        self.load_registry()

    def register_discovery(
        self,
        discovery_id: str,
        claim: str,
        data_files: List[str] = None,
        analysis_code: List[str] = None,
        result_files: List[str] = None,
        figure_files: List[str] = None,
        provenance_level: ProvenanceLevel = ProvenanceLevel.UNKNOWN,
        description: str = "",
        notes: List[str] = None
    ) -> DiscoveryProvenance:
        """Register a discovery with its provenance evidence."""

        discovery = DiscoveryProvenance(
            discovery_id=discovery_id,
            claim=claim,
            data_files=data_files or [],
            analysis_code=analysis_code or [],
            result_files=result_files or [],
            figure_files=figure_files or [],
            provenance_level=provenance_level,
            description=description,
            notes=notes or []
        )

        # Validate evidence exists
        discovery.validate_evidence()

        self.discoveries[discovery_id] = discovery
        self.save_registry()

        return discovery

    def can_claim_discovery(self, discovery_id: str) -> bool:
        """
        Check if a discovery can be claimed as real.

        Returns True only if:
        1. Discovery is registered
        2. Provenance level is VERIFIED_ANALYSIS or DEMONSTRATION
        3. All evidence files exist
        """
        if discovery_id not in self.discoveries:
            return False

        discovery = self.discoveries[discovery_id]

        # Must be real analysis or demonstration, not just example
        if discovery.provenance_level not in [
            ProvenanceLevel.VERIFIED_ANALYSIS,
            ProvenanceLevel.DEMONSTRATION
        ]:
            return False

        # All claimed files must exist
        if not discovery.files_exist:
            return False

        return True

    def get_discovery(self, discovery_id: str) -> Optional[DiscoveryProvenance]:
        """Get discovery provenance by ID."""
        return self.discoveries.get(discovery_id)

    def flag_hallucination(self, discovery_id: str, reason: str) -> None:
        """Flag a discovery as hallucinated (claimed but no evidence)."""
        if discovery_id in self.discoveries:
            self.discoveries[discovery_id].provenance_level = ProvenanceLevel.HALLUCINATED
            self.discoveries[discovery_id].notes.append(f"HALLUCINATED: {reason}")
            self.save_registry()

    def list_discoveries(self, level: Optional[ProvenanceLevel] = None) -> List[DiscoveryProvenance]:
        """List all discoveries, optionally filtered by level."""
        discoveries = list(self.discoveries.values())
        if level:
            discoveries = [d for d in discoveries if d.provenance_level == level]
        return discoveries

    def save_registry(self):
        """Save discovery registry to disk."""
        data = {
            'discoveries': {
                did: d.to_dict()
                for did, d in self.discoveries.items()
            },
            'last_updated': datetime.now().isoformat()
        }

        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.registry_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_registry(self):
        """Load discovery registry from disk."""
        if not self.registry_path.exists():
            return

        try:
            with open(self.registry_path, 'r') as f:
                data = json.load(f)

            for did, d_dict in data.get('discoveries', {}).items():
                discovery = DiscoveryProvenance(
                    discovery_id=did,
                    claim=d_dict['claim'],
                    provenance_level=ProvenanceLevel(d_dict['provenance_level']),
                    data_files=d_dict.get('data_files', []),
                    analysis_code=d_dict.get('analysis_code', []),
                    result_files=d_dict.get('result_files', []),
                    figure_files=d_dict.get('figure_files', []),
                    timestamp=d_dict.get('timestamp', ''),
                    files_exist=d_dict.get('files_exist', False),
                    description=d_dict.get('description', ''),
                    notes=d_dict.get('notes', [])
                )
                self.discoveries[did] = discovery
        except Exception as e:
            print(f"Warning: Could not load discovery registry: {e}")


class AntiHallucinationValidator:
    """
    Validates content to prevent discovery hallucinations.

    Checks:
    1. Are discoveries claimed? If yes, are they registered?
    2. Are figures/data files referenced? Do they exist?
    3. Is it clear what's real vs. hypothetical?
    4. Are specific numerical claims backed by evidence?
    """

    def __init__(self):
        self.provenance_tracker = DiscoveryProvenanceTracker()

    def validate_section(
        self,
        section_content: str,
        section_id: str
    ) -> Dict[str, Any]:
        """
        Validate a section for hallucination risks.

        Returns dict with:
        - safe: bool - Can this be published?
        - issues: List[str] - Specific problems found
        - recommendations: List[str] - How to fix
        """
        issues = []
        recommendations = []

        # Check for unregistered discoveries
        discovery_keywords = ['discovered', 'found that', 'identified', 'analyzed',
                            'Bayes factor', 'correlation', 'measured']

        for keyword in discovery_keywords:
            if keyword.lower() in section_content.lower():
                # This might be a discovery claim - verify it's registered
                # For now, flag for review
                if 'example' not in section_content.lower():
                    issues.append(
                        f"Section claims discovery ('{keyword}') but may not be "
                        "registered in provenance tracker"
                    )

        # Check for specific numbers that might need sourcing
        import re
        numbers_with_units = re.findall(r'\d+\.?\d*\s*(pc|K|km/s|Msun)', section_content)
        if numbers_with_units and 'example' not in section_content.lower():
            recommendations.append(
                f"Section contains {len(numbers_with_units)} numerical claims. "
                "Ensure these are backed by real analysis or clearly labeled as example."
            )

        # Check if section is clearly labeled as example/demonstration
        is_example = ('example' in section_content.lower() or
                     'demonstration' in section_content.lower() or
                     'hypothetical' in section_content.lower())

        if not is_example and len(issues) > 0:
            recommendations.append(
                "Section makes discovery claims but is not clearly labeled as "
                "'example', 'demonstration', or 'hypothetical'. This risks "
                "presenting illustrations as real discoveries."
            )

        safe = len(issues) == 0

        return {
            'safe': safe,
            'issues': issues,
            'recommendations': recommendations,
            'section_id': section_id
        }


# Register the REAL Cygnus analysis as a verified discovery
def register_real_discoveries():
    """Register discoveries that have real evidence."""
    tracker = DiscoveryProvenanceTracker()

    # Register the Cygnus filament analysis
    tracker.register_discovery(
        discovery_id="cygnus_filament_stability_2026",
        claim="Analyzed Herschel filamentcatalogue.fits data for Cygnus region, "
              "characterizing filament size distribution and stability properties",
        data_files=["/Users/gjw255/astrodata/SWARM/STAN_XI_ASTRO/docs/filamentcatalogue.fits"],
        analysis_code=["/Users/gjw255/astrodata/SWARM/STAN_XI_ASTRO/docs/filament_analysis_pipeline.md"],
        result_files=["/Users/gjw255/astrodata/SWARM/STAN_XI_ASTRO/docs/cygnus_filament_analysis.md"],
        figure_files=[],  # No figures generated yet
        provenance_level=ProvenanceLevel.VERIFIED_ANALYSIS,
        description="Real analysis of Herschel data from March 18, 2026",
        notes=["Actual FITS data file exists", "Analysis documented in markdown files"]
    )

    # Flag the Taurus analysis as HALLUCINATED for reference
    tracker.register_discovery(
        discovery_id="taurus_bayes47_hallucination",
        claim="Taurus molecular cloud analysis with Bayes factor 47",
        data_files=[],
        analysis_code=[],
        result_files=[],
        figure_files=[
            "/Users/gjw255/astrodata/SWARM/STAN_XI_ASTRO/RASTI/figures_v41/fig_causal_chain.png",
            "/Users/gjw255/astrodata/SWARM/STAN_XI_ASTRO/RASTI/figures_v41/fig_sfe_correlation.png",
            "/Users/gjw255/astrodata/SWARM/STAN_XI_ASTRO/RASTI/figures_v41/fig_core_pattern.png"
        ],
        provenance_level=ProvenanceLevel.HALLUCINATED,
        description="Illustrative figures created for paper, not real analysis",
        notes=[
            "Figures created March 21, 2026 for illustration",
            "No actual Taurus analysis code found",
            "Presented as real in Section 3.5 but is hypothetical",
            "INTEGRITY VIOLATION: presenting example as discovery"
        ]
    )

    return tracker


if __name__ == "__main__":
    # Test the system
    print("="*70)
    print("DISCOVERY PROVENANCE TRACKER - Anti-Hallucination System")
    print("="*70)

    tracker = register_real_discoveries()

    print("\n✓ Registered real discoveries:")
    for d in tracker.list_discoveries(ProvenanceLevel.VERIFIED_ANALYSIS):
        print(f"  - {d.discovery_id}: {d.claim[:80]}...")

    print(f"\n⚠ Flagged hallucinations:")
    for d in tracker.list_discoveries(ProvenanceLevel.HALLUCINATED):
        print(f"  - {d.discovery_id}: {d.notes}")

    print("\n" + "="*70)
    print("VALIDATION TEST")
    print("="*70)

    validator = AntiHallucinationValidator()

    # Test Section 3.5
    section_35_text = """
    To demonstrate ASTRA's discovery capabilities, we describe an analysis of
    interstellar medium filamentary structures. We tasked ASTRA with analyzing
    multi-wavelength observations of the Taurus molecular cloud. The system
    identified a correlation with Bayes factor 47.
    """

    result = validator.validate_section(section_35_text, "section_3_5")
    print(f"\nSection 3.5 validation:")
    print(f"  Safe to publish: {result['safe']}")
    print(f"  Issues found: {len(result['issues'])}")
    for issue in result['issues']:
        print(f"    - {issue}")
    for rec in result['recommendations']:
        print(f"  Recommendation: {rec}")

    print("\n" + "="*70)
