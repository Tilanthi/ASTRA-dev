#!/usr/bin/env python3
"""
ASTRA Validated Discovery Pipeline

This module integrates rigorous validation gates into the ASTRA discovery pipeline
to prevent false discoveries and ensure genuine scientific rigor.

Based on peer review feedback identifying systemic architectural flaws:
- Citation resolution failures
- Non-traceable computation
- Trivial validation targets
- Ungoverned agreement criteria
- Unfalsifiable self-generated metrics

Version: 1.0.0-Validated
Date: 2026-07-10
"""

import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import validation system
from astra_core.pipeline_validation import (
    validate_discovery_pipeline,
    ValidationResult,
    ValidationSeverity
)

# Import ASTRA components
try:
    from astra_core import create_stan_system
    from astra_core.autonomy import (
        create_genuine_discovery_generator,
        generate_contemporary_discovery
    )
except ImportError as e:
    logging.error(f"Failed to import ASTRA components: {e}")
    create_stan_system = None
    create_genuine_discovery_generator = None
    generate_contemporary_discovery = None

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('.astra_validated_discovery.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class DiscoveryOutput:
    """Output from a discovery cycle with validation requirements."""
    latex_content: str
    bibliography_content: str
    results_section: str
    predicted_values: Dict[str, float]
    expected_values: Dict[str, float]
    validation_cases: List[Dict[str, Any]]
    title: str
    abstract: str


class ValidatedDiscoveryPipeline:
    """ASTRA discovery pipeline with rigorous validation gates."""

    def __init__(self, enable_validation_gates: bool = True):
        """
        Initialize validated discovery pipeline.

        Args:
            enable_validation_gates: If True, all validation gates are enforced
        """
        self.enable_validation_gates = enable_validation_gates
        self.astra_system = None
        self.discovery_generator = None

        logger.info(f"ValidatedDiscoveryPipeline initialized (validation gates: {enable_validation_gates})")

    def initialize_system(self) -> bool:
        """Initialize ASTRA system components."""
        try:
            if create_stan_system is None:
                logger.error("create_stan_system not available - cannot initialize")
                return False

            logger.info("Creating ASTRA enhanced unified system...")
            self.astra_system = create_stan_system()

            if self.astra_system is None:
                logger.error("Failed to create ASTRA system")
                return False

            logger.info("Creating genuine discovery generator...")
            self.discovery_generator = create_genuine_discovery_generator(
                astra_system=self.astra_system
            )

            if self.discovery_generator is None:
                logger.warning("Discovery generator not available - using fallback")
                # Continue without discovery generator

            logger.info("✅ System components initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize system: {e}")
            return False

    def generate_discovery_with_validation(self) -> Tuple[bool, Optional[DiscoveryOutput], str]:
        """
        Generate a discovery with full validation pipeline.

        Returns:
            Tuple of (success, discovery_output, validation_report)
        """
        if self.astra_system is None:
            error_msg = "ASTRA system not initialized"
            logger.error(error_msg)
            return False, None, error_msg

        try:
            logger.info("Starting validated discovery cycle...")

            # Generate discovery
            discovery_output = self._generate_discovery()
            if discovery_output is None:
                return False, None, "Discovery generation failed"

            # Run validation gates
            if self.enable_validation_gates:
                logger.info("Running validation gates...")
                validation_passed, validation_report = self._run_validation(discovery_output)

                if not validation_passed:
                    logger.error(f"❌ VALIDATION FAILED - Discovery rejected\n{validation_report}")
                    return False, discovery_output, validation_report

                logger.info(f"✅ VALIDATION PASSED - Discovery accepted\n{validation_report}")
                return True, discovery_output, validation_report
            else:
                logger.warning("⚠️ Validation gates disabled - discovery accepted without validation")
                return True, discovery_output, "Validation gates disabled - no validation performed"

        except Exception as e:
            error_msg = f"Discovery cycle failed: {e}"
            logger.error(error_msg)
            return False, None, error_msg

    def _generate_discovery(self) -> Optional[DiscoveryOutput]:
        """Generate a discovery using ASTRA system."""
        try:
            logger.info("Generating discovery with ASTRA system...")

            # Use discovery generator if available
            if self.discovery_generator is not None:
                logger.info("Using genuine discovery generator...")
                discovery = generate_contemporary_discovery(
                    self.discovery_generator,
                    domain="astrophysics"
                )

                if discovery and hasattr(discovery, 'title'):
                    return self._format_discovery_output(discovery)

            # Fallback: Direct query to ASTRA system
            logger.info("Using direct ASTRA query approach...")
            query = "Analyze stellar evolution for 1.0 solar mass stars and identify any novel insights"

            response = self.astra_system.answer(query)
            if response:
                return self._format_basic_output(response, query)

            logger.error("No response from ASTRA system")
            return None

        except Exception as e:
            logger.error(f"Discovery generation failed: {e}")
            return None

    def _format_discovery_output(self, discovery) -> DiscoveryOutput:
        """Format discovery output for validation."""
        # This is a simplified version - real implementation would extract actual data
        latex_content = getattr(discovery, 'latex_content', '')
        bibliography_content = getattr(discovery, 'bibliography', '')
        results_section = getattr(discovery, 'results_section', '')
        predicted_values = getattr(discovery, 'predicted_values', {})
        expected_values = getattr(discovery, 'expected_values', {})
        validation_cases = getattr(discovery, 'validation_cases', [])
        title = getattr(discovery, 'title', 'Untitled Discovery')
        abstract = getattr(discovery, 'abstract', '')

        return DiscoveryOutput(
            latex_content=latex_content,
            bibliography_content=bibliography_content,
            results_section=results_section,
            predicted_values=predicted_values,
            expected_values=expected_values,
            validation_cases=validation_cases,
            title=title,
            abstract=abstract
        )

    def _format_basic_output(self, response: str, query: str) -> DiscoveryOutput:
        """Format basic ASTRA response for validation."""
        # Create basic structure from response
        latex_content = f"""
        \\documentclass{{article}}
        \\begin{{document}}
        \\title{{ASTRA Discovery Analysis}}
        \\maketitle
        \\section{{Results}}
        {response}
        \\end{{document}}
        """

        bibliography_content = ""
        results_section = response
        predicted_values = {}
        expected_values = {}
        validation_cases = []

        return DiscoveryOutput(
            latex_content=latex_content,
            bibliography_content=bibliography_content,
            results_section=results_section,
            predicted_values=predicted_values,
            expected_values=expected_values,
            validation_cases=validation_cases,
            title="ASTRA Discovery",
            abstract=response[:200] if response else ""
        )

    def _run_validation(self, discovery: DiscoveryOutput) -> Tuple[bool, str]:
        """Run validation gates on discovery output."""
        try:
            # Run comprehensive validation
            passed, report = validate_discovery_pipeline(
                tex_content=discovery.latex_content,
                bib_content=discovery.bibliography_content,
                results_section=discovery.results_section,
                validation_cases=discovery.validation_cases,
                predicted_values=discovery.predicted_values,
                expected_values=discovery.expected_values
            )

            return passed, report

        except Exception as e:
            error_msg = f"Validation failed: {e}"
            logger.error(error_msg)
            return False, error_msg


def main():
    """Main function to run validated discovery pipeline."""
    logger.info("=" * 80)
    logger.info("ASTRA Validated Discovery Pipeline - Starting")
    logger.info("=" * 80)

    # Create pipeline
    pipeline = ValidatedDiscoveryPipeline(enable_validation_gates=True)

    # Initialize system
    if not pipeline.initialize_system():
        logger.error("❌ Failed to initialize ASTRA system")
        return 1

    # Run discovery cycle
    success, discovery, report = pipeline.generate_discovery_with_validation()

    if success:
        logger.info("✅ Discovery cycle completed successfully")
        logger.info(f"Discovery: {discovery.title if discovery else 'N/A'}")
        return 0
    else:
        logger.error(f"❌ Discovery cycle failed: {report}")
        return 1


if __name__ == "__main__":
    sys.exit(main())