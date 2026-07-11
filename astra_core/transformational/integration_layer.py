"""
Integration Layer: Transformational Architecture ↔ Existing ASTRA System

This module bridges the new rigorous transformational architecture with ASTRA's
existing discovery pipeline, enabling gradual upgrade without breaking existing
functionality.

Version: 1.0.0
Date: 2026-07-04
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import asyncio

logger = logging.getLogger(__name__)


class IntegrationMode(Enum):
    """Integration mode for backward compatibility"""
    LEGACY_ONLY = "legacy_only"  # Use only existing ASTRA validation
    TRANSFORMATIONAL_ONLY = "transformational_only"  # Use only new architecture
    HYBRID = "hybrid"  # Use both, compare results
    GRADUAL_UPGRADE = "gradual_upgrade"  # Gradually phase in new components


@dataclass
class ValidationResult:
    """Combined validation result from both systems"""
    # Legacy ASTRA validation
    legacy_novelty: float
    legacy_probability: float
    legacy_status: str

    # Transformational architecture validation
    transformational_status: str  # "discovery" | "candidate" | "confirmatory" | "rejected"
    transformational_confidence: float
    transformational_level: str  # Discovery level
    prior_classification: str  # "confirmatory" | "underpowered" | "candidate_novel" | "novel_discovery"

    # Gate results
    statistical_significance: bool
    independent_replication: bool
    mechanistic_plausibility: bool
    adversarial_critique: bool

    # Comparison
    systems_agree: bool
    recommendation: str  # Final recommendation

    # Metadata
    validation_timestamp: str
    integration_mode: str
    warnings: List[str]


class TransformationalIntegrationLayer:
    """
    Integration layer for bridging transformational architecture with
    existing ASTRA system.

    This enables:
    - Gradual upgrade path
    - Side-by-side comparison
    - Backward compatibility
    - Transparent migration
    """

    def __init__(self, mode: IntegrationMode = IntegrationMode.HYBRID):
        """
        Initialize integration layer.

        Args:
            mode: Integration mode (default: HYBRID)
        """
        self.mode = mode

        # Legacy system components
        self.legacy_pipeline = None
        self.legacy_coordinator = None

        # Transformational components
        self.data_scale_layer = None
        self.prior_kb = None
        self.discovery_gate = None

        # Statistics
        self.total_validations = 0
        self.agreement_count = 0
        self.disagreement_count = 0

        logger.info(f"[IntegrationLayer] Initialized in {mode.value} mode")

    def initialize_legacy_system(self, legacy_pipeline=None, legacy_coordinator=None):
        """Initialize legacy ASTRA system components"""
        self.legacy_pipeline = legacy_pipeline
        self.legacy_coordinator = legacy_coordinator
        logger.info("[IntegrationLayer] Legacy system components initialized")

    def initialize_transformational_system(
        self,
        data_scale_layer=None,
        prior_kb=None,
        discovery_gate=None
    ):
        """Initialize transformational architecture components"""
        self.data_scale_layer = data_scale_layer
        self.prior_kb = prior_kb
        self.discovery_gate = discovery_gate
        logger.info("[IntegrationLayer] Transformational components initialized")

    async def validate_discovery(
        self,
        discovery_claim: str,
        domains: List[str],
        discovery_type: str,
        statistical_result: Optional[Dict[str, Any]] = None,
        max_results_per_source: int = 50
    ) -> ValidationResult:
        """
        Validate discovery using integrated systems.

        Args:
            discovery_claim: The discovery text to validate
            domains: Scientific domains involved
            discovery_type: Type of discovery
            statistical_result: Statistical test results
            max_results_per_source: Max papers for literature validation

        Returns:
            ValidationResult with combined results from both systems
        """
        self.total_validations += 1

        # Initialize result
        result = ValidationResult(
            legacy_novelty=0.0,
            legacy_probability=0.0,
            legacy_status="unknown",
            transformational_status="unknown",
            transformational_confidence=0.0,
            transformational_level="unknown",
            prior_classification="unknown",
            statistical_significance=False,
            independent_replication=False,
            mechanistic_plausibility=False,
            adversarial_critique=False,
            systems_agree=False,
            recommendation="validation_incomplete",
            validation_timestamp=datetime.now().isoformat(),
            integration_mode=self.mode.value,
            warnings=[]
        )

        # Legacy validation (if enabled)
        if self.mode in [IntegrationMode.LEGACY_ONLY, IntegrationMode.HYBRID, IntegrationMode.GRADUAL_UPGRADE]:
            if self.legacy_pipeline:
                try:
                    logger.info("[IntegrationLayer] Running legacy validation...")
                    legacy_result = await self.legacy_pipeline.validate(
                        discovery_claim=discovery_claim,
                        domains=domains,
                        discovery_type=discovery_type,
                        max_results_per_source=max_results_per_source
                    )

                    result.legacy_novelty = legacy_result.novelty_score if hasattr(legacy_result, 'novelty_score') else 0.0
                    result.legacy_probability = legacy_result.traditional_probability if hasattr(legacy_result, 'traditional_probability') else 0.0
                    result.legacy_status = legacy_result.status.value if hasattr(legacy_result, 'status') else "unknown"

                except Exception as e:
                    logger.error(f"[IntegrationLayer] Legacy validation failed: {e}")
                    result.warnings.append(f"Legacy validation error: {e}")

        # Transformational validation (if enabled)
        if self.mode in [IntegrationMode.TRANSFORMATIONAL_ONLY, IntegrationMode.HYBRID]:
            if self.prior_kb and self.discovery_gate:
                try:
                    logger.info("[IntegrationLayer] Running transformational validation...")

                    # Stage 1: Prior knowledge base classification
                    if statistical_result and self.prior_kb:
                        prior_classification, prior_details = self.prior_kb.classify_result(
                            observed_value=statistical_result.get('effect_size', 0.0),
                            observed_uncertainty=statistical_result.get('effect_uncertainty', 0.0),
                            relation_id="universal_filament_width",  # Example relation
                            sample_size=statistical_result.get('sample_size', 0)
                        )
                        result.prior_classification = prior_classification.value

                    # Stage 2: Discovery gate evaluation
                    if self.discovery_gate and statistical_result:
                        gate_result = await self.discovery_gate.evaluate(
                            candidate_id=f"validation_{self.total_validations}",
                            discovery_claim=discovery_claim,
                            domains=domains,
                            statistical_result=statistical_result
                        )

                        result.transformational_status = gate_result.status.value
                        result.transformational_confidence = gate_result.overall_confidence
                        result.transformational_level = gate_result.discovery_level

                        # Extract stage results
                        from astra_core.transformational.discovery_gate import GateStage
                        if GateStage.STATISTICAL_SIGNIFICANCE in gate_result.stage_results:
                            result.statistical_significance = gate_result.stage_results[
                                GateStage.STATISTICAL_SIGNIFICANCE
                            ].passed
                        if GateStage.INDEPENDENT_REPLICATION in gate_result.stage_results:
                            result.independent_replication = gate_result.stage_results[
                                GateStage.INDEPENDENT_REPLICATION
                            ].passed
                        if GateStage.MECHANISTIC_PLAUSIBILITY in gate_result.stage_results:
                            result.mechanistic_plausibility = gate_result.stage_results[
                                GateStage.MECHANISTIC_PLAUSIBILITY
                            ].passed
                        if GateStage.ADVERSARIAL_CRITIQUE in gate_result.stage_results:
                            result.adversarial_critique = gate_result.stage_results[
                                GateStage.ADVERSARIAL_CRITIQUE
                            ].passed

                except Exception as e:
                    logger.error(f"[IntegrationLayer] Transformational validation failed: {e}")
                    result.warnings.append(f"Transformational validation error: {e}")

        # Compare results and determine agreement
        result = self._compare_and_recommend(result)

        logger.info(f"[IntegrationLayer] ✅ Validation complete: {result.recommendation}")
        return result

    def _compare_and_recommend(self, result: ValidationResult) -> ValidationResult:
        """Compare legacy and transformational results, make recommendation"""
        # Check if systems agree
        systems_agree = False

        if self.mode == IntegrationMode.HYBRID:
            # Both systems ran, compare results
            legacy_high_confidence = result.legacy_novelty >= 0.70
            transformational_discovery = result.transformational_status == "discovery"

            systems_agree = (legacy_high_confidence and transformational_discovery) or \
                           (not legacy_high_confidence and not transformational_discovery)

            if systems_agree:
                self.agreement_count += 1
                result.systems_agree = True
            else:
                self.disagreement_count += 1
                result.systems_agree = False
                result.warnings.append("Legacy and transformational systems disagree")

        # Make final recommendation
        if self.mode == IntegrationMode.TRANSFORMATIONAL_ONLY:
            # Trust transformational system
            result.recommendation = result.transformational_status

        elif self.mode == IntegrationMode.LEGACY_ONLY:
            # Trust legacy system
            result.recommendation = result.legacy_status

        elif self.mode == IntegrationMode.HYBRID:
            # Prefer transformational but flag disagreements
            if result.transformational_status == "confirmatory":
                result.recommendation = "confirmatory"  # Trust prior KB
            elif result.transformational_status in ["discovery", "candidate"]:
                result.recommendation = result.transformational_status
            else:
                result.recommendation = result.transformational_status

        elif self.mode == IntegrationMode.GRADUAL_UPGRADE:
            # Use transformational for classification, legacy for comparison
            result.recommendation = result.transformational_status

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """Get integration statistics"""
        agreement_rate = (
            self.agreement_count / self.total_validations
            if self.total_validations > 0 else 0.0
        )

        return {
            "integration_mode": self.mode.value,
            "total_validations": self.total_validations,
            "agreement_count": self.agreement_count,
            "disagreement_count": self.disagreement_count,
            "agreement_rate": agreement_rate,
            "legacy_system_available": self.legacy_pipeline is not None,
            "transformational_system_available": (
                self.prior_kb is not None and
                self.discovery_gate is not None
            )
        }


def create_integration_layer(mode: IntegrationMode = IntegrationMode.HYBRID) -> TransformationalIntegrationLayer:
    """
    Factory function to create integration layer.

    Args:
        mode: Integration mode

    Returns:
        Configured TransformationalIntegrationLayer
    """
    return TransformationalIntegrationLayer(mode)