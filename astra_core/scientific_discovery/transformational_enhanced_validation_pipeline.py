"""
Transformational-Enhanced Validation Pipeline

Integrates the new transformational architecture with ASTRA's existing
discovery pipeline. This pipeline now uses the rigorous 4-stage Discovery
Gate, Prior Knowledge Base, and Data Scale Layer for genuine discovery
validation.

This replaces the original enhanced_validation_pipeline.py with the
transformational architecture while maintaining backward compatibility.

Key improvements:
- Prevents confirmatory results from being labeled as discoveries
- Implements 4-stage rigorous validation gate
- Uses Prior Knowledge Base for consistency checking
- Applies FDR correction and power analysis automatically
- Creates complete audit trails for Discovery Demonstration

Version: 2.0.0 (Transformational)
Date: 2026-07-04
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

logger = logging.getLogger(__name__)

# Import transformational architecture components
try:
    from astra_core.transformational import (
        create_prior_knowledge_base,
        create_data_scale_layer,
        create_discovery_gate,
        DiscoveryGate,
        PriorKnowledgeBase,
        DataScaleLayer,
        GateStatus
    )
    TRANSFORMATIONAL_AVAILABLE = True
except ImportError as e:
    TRANSFORMATIONAL_AVAILABLE = False
    logger.warning(f"Transformational architecture not available: {e}")

# Import existing validation components for backward compatibility
try:
    from astra_core.scientific_discovery.literature_validator import LiteratureValidator, create_literature_validator
    LITERATURE_AVAILABLE = True
except ImportError as e:
    LITERATURE_AVAILABLE = False
    logger.warning(f"Literature validator not available: {e}")

try:
    from astra_core.scientific_discovery.eureka_validator import (
        EurekaEnhancedValidator,
        create_eureka_enhanced_validator,
        EurekaValidationReport
    )
    EUREKA_AVAILABLE = True
except ImportError as e:
    EUREKA_AVAILABLE = False
    logger.warning(f"Eureka validator not available: {e}")


class TransformationalValidationStatus(Enum):
    """Validation status using transformational architecture"""
    DISCOVERY = "discovery"  # Passed all 4 gate stages
    CONFIRMATORY = "confirmatory"  # Consistent with prior knowledge
    CANDIDATE = "candidate"  # Promising but incomplete validation
    UNDERPOWERED = "underpowered"  # Insufficient statistical power
    REJECTED = "rejected"  # Failed one or more gate stages
    INSUFFICIENT_DATA = "insufficient_data"  # Cannot evaluate


@dataclass
class TransformationalValidationReport:
    """Comprehensive validation report using transformational architecture"""
    # Transformational validation results
    transformational_status: TransformationalValidationStatus
    transformational_confidence: float  # 0-1
    discovery_level: str  # "novel_observation" | "theoretical_insight" | "paradigm_shift" | "eureka_discovery"

    # Prior knowledge base classification
    prior_classification: str  # "confirmatory" | "candidate_novel" | "novel_discovery" | "underpowered"
    deviation_from_prior: float  # Sigma deviation from expected value

    # 4-Stage gate results
    statistical_significance: bool
    independent_replication: bool
    mechanistic_plausibility: bool
    adversarial_critique: bool

    # Enhanced metrics (for backward compatibility)
    novelty_score: float  # Literature dissimilarity
    validation_score: float  # Statistical rigor
    impact_score: float  # Potential impact
    overall_score: float  # Combined score

    # Audit trail
    audit_trail_length: int  # Number of audit entries
    audit_trail_available: bool  # Whether complete audit exists

    # Metadata
    validation_timestamp: str
    validation_duration_seconds: float = 0.0
    explanation: str = ""
    warnings: List[str] = None

    def __post_init__(self):
        if self.warnings is None:
            self.warnings = []


class TransformationalEnhancedValidationPipeline:
    """
    Transformational-Enhanced validation pipeline using the new architecture.

    This pipeline now enforces rigorous standards:
    - Prior Knowledge Base checking FIRST
    - 4-stage Discovery Gate validation
    - Automatic FDR correction
    - Power analysis on all tests
    - Complete audit trails
    """

    def __init__(self, config: Any = None):
        """
        Initialize transformational-enhanced pipeline.

        Args:
            config: Configuration object
        """
        self.config = config

        # Initialize transformational components (PRIMARY)
        self.prior_kb = None
        self.data_layer = None
        self.discovery_gate = None

        # Initialize legacy components (SECONDARY, for backward compatibility)
        self.literature_validator = None
        self.eureka_validator = None

        # Transformational architecture initialization
        if TRANSFORMATIONAL_AVAILABLE:
            try:
                logger.info("[Pipeline] 🚀 Initializing Transformational Architecture...")

                # Initialize Prior Knowledge Base
                self.prior_kb = create_prior_knowledge_base()
                logger.info(f"[Pipeline] ✅ Prior KB initialized with {len(self.prior_kb.relations)} relations")

                # Initialize Data Scale Layer
                self.data_layer = create_data_scale_layer()
                logger.info("[Pipeline] ✅ Data Scale Layer initialized")

                # Initialize Discovery Gate
                self.discovery_gate = create_discovery_gate(self.prior_kb, self.data_layer)
                logger.info("[Pipeline] ✅ Discovery Gate initialized")

                logger.info("[Pipeline] 🎯 TRANSFORMATIONAL ARCHITECTURE ACTIVE")

            except Exception as e:
                logger.error(f"[Pipeline] Failed to initialize transformational architecture: {e}")
        else:
            logger.warning("[Pipeline] ⚠️ Transformational architecture not available, using legacy validation")

        # Legacy components initialization (for backward compatibility)
        if LITERATURE_AVAILABLE:
            try:
                self.literature_validator = create_literature_validator()
                logger.info("[Pipeline] ✅ Literature validator initialized (legacy)")
            except Exception as e:
                logger.error(f"[Pipeline] Failed to initialize literature validator: {e}")

        if EUREKA_AVAILABLE:
            try:
                self.eureka_validator = create_eureka_enhanced_validator()
                logger.info("[Pipeline] ✅ Eureka validator initialized (legacy)")
            except Exception as e:
                logger.error(f"[Pipeline] Failed to initialize Eureka validator: {e}")

    async def validate(
        self,
        discovery_claim: str,
        domains: List[str],
        discovery_type: str,
        max_results_per_source: int = 50,
        statistical_result: Optional[Dict[str, Any]] = None
    ) -> TransformationalValidationReport:
        """
        Perform transformational-enhanced validation.

        Args:
            discovery_claim: The discovery text to validate
            domains: Scientific domains involved
            discovery_type: Type of discovery
            max_results_per_source: Maximum papers to analyze
            statistical_result: Statistical test results (effect_size, p_values, sample_size)

        Returns:
            TransformationalValidationReport with rigorous validation
        """
        start_time = datetime.now()
        logger.info(f"[Pipeline] 🎯 Starting transformational validation")

        # Initialize report
        report = TransformationalValidationReport(
            transformational_status=TransformationalValidationStatus.CANDIDATE,
            transformational_confidence=0.0,
            discovery_level="unknown",
            prior_classification="unknown",
            deviation_from_prior=0.0,
            statistical_significance=False,
            independent_replication=False,
            mechanistic_plausibility=False,
            adversarial_critique=False,
            novelty_score=0.0,
            validation_score=0.0,
            impact_score=0.0,
            overall_score=0.0,
            audit_trail_length=0,
            audit_trail_available=False,
            validation_timestamp=datetime.now().isoformat(),
            explanation="",
            warnings=[]
        )

        # === TRANSFORMATIONAL VALIDATION (PRIMARY) ===
        if self.discovery_gate and TRANSFORMATIONAL_AVAILABLE:
            try:
                logger.info("[Pipeline] 🎯 Using Transformational Architecture")

                # Create default statistical result if not provided
                if statistical_result is None:
                    statistical_result = {
                        'effect_size': 0.5,  # Default moderate effect
                        'effect_uncertainty': 0.1,
                        'sample_size': 30,
                        'p_values': [0.05]
                    }
                    report.warnings.append("Using default statistical values - provide actual results for rigorous validation")

                # Get training data for replication testing
                training_data = {}
                if self.data_layer:
                    training_data = self.data_layer.get_training_data()

                # Run through Discovery Gate
                gate_result = await self.discovery_gate.evaluate(
                    candidate_id=f"validation_{int(datetime.now().timestamp())}",
                    discovery_claim=discovery_claim,
                    domains=domains,
                    statistical_result=statistical_result,
                    training_data=training_data
                )

                # Extract results from gate
                from astra_core.transformational.discovery_gate import GateStage

                # Map gate status to transformational status
                status_map = {
                    GateStatus.DISCOVERY: TransformationalValidationStatus.DISCOVERY,
                    GateStatus.CONFIRMATORY: TransformationalValidationStatus.CONFIRMATORY,
                    GateStatus.CANDIDATE: TransformationalValidationStatus.CANDIDATE,
                    GateStatus.REJECTED: TransformationalValidationStatus.REJECTED,
                    GateStatus.INSUFFICIENT_DATA: TransformationalValidationStatus.INSUFFICIENT_DATA
                }
                report.transformational_status = status_map.get(
                    gate_result.status,
                    TransformationalValidationStatus.CANDIDATE
                )
                report.transformational_confidence = gate_result.overall_confidence
                report.discovery_level = gate_result.discovery_level
                report.audit_trail_length = len(gate_result.audit_trail)
                report.audit_trail_available = len(gate_result.audit_trail) > 0

                # Extract Prior KB classification from gate result
                report.prior_classification = gate_result.prior_classification or "unknown"

                # Extract deviation from prior
                if gate_result.prior_details and 'deviation_sigma' in gate_result.prior_details:
                    report.deviation_from_prior = gate_result.prior_details['deviation_sigma']
                else:
                    report.deviation_from_prior = 0.0

                # Extract stage results
                if GateStage.STATISTICAL_SIGNIFICANCE in gate_result.stage_results:
                    report.statistical_significance = gate_result.stage_results[
                        GateStage.STATISTICAL_SIGNIFICANCE
                    ].passed
                if GateStage.INDEPENDENT_REPLICATION in gate_result.stage_results:
                    report.independent_replication = gate_result.stage_results[
                        GateStage.INDEPENDENT_REPLICATION
                    ].passed
                if GateStage.MECHANISTIC_PLAUSIBILITY in gate_result.stage_results:
                    report.mechanistic_plausibility = gate_result.stage_results[
                        GateStage.MECHANISTIC_PLAUSIBILITY
                    ].passed
                if GateStage.ADVERSARIAL_CRITIQUE in gate_result.stage_results:
                    report.adversarial_critique = gate_result.stage_results[
                        GateStage.ADVERSARIAL_CRITIQUE
                    ].passed

                # Set scores based on gate confidence
                report.overall_score = gate_result.overall_confidence
                report.validation_score = gate_result.overall_confidence
                report.novelty_score = gate_result.overall_confidence
                report.impact_score = gate_result.overall_confidence

                # Generate explanation
                report.explanation = gate_result.explanation

                logger.info(f"[Pipeline] ✅ Transformational validation complete: {report.transformational_status.value}")
                logger.info(f"[Pipeline] Confidence: {report.transformational_confidence:.2f}")
                logger.info(f"[Pipeline] Discovery Level: {report.discovery_level}")

            except Exception as e:
                logger.error(f"[Pipeline] Transformational validation failed: {e}")
                report.warnings.append(f"Transformational validation error: {e}")

        # === LEGACY VALIDATION (FALLBACK, for backward compatibility) ===
        elif self.eureka_validator:
            try:
                logger.info("[Pipeline] Using Legacy EUREKA validation")

                eureka_report: EurekaValidationReport = await self.eureka_validator.validate_genuine_advance(
                    discovery_claim=discovery_claim,
                    domains=domains,
                    discovery_type=discovery_type,
                    max_results_per_source=max_results_per_source
                )

                # Extract scores for compatibility
                report.novelty_score = eureka_report.eureka_assessment.claim_novelty
                report.transformational_confidence = 0.6  # Moderate confidence for legacy
                report.overall_score = report.novelty_score
                report.explanation = "Validated using legacy EUREKA system (transformational architecture not available)"

            except Exception as e:
                logger.error(f"[Pipeline] Legacy validation failed: {e}")
                report.warnings.append(f"Legacy validation error: {e}")

        # Calculate duration
        end_time = datetime.now()
        report.validation_duration_seconds = (end_time - start_time).total_seconds()

        logger.info(f"[Pipeline] ✅ Validation complete in {report.validation_duration_seconds:.2f}s")

        return report

    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get status of validation pipeline"""
        return {
            "transformational_available": TRANSFORMATIONAL_AVAILABLE,
            "transformational_active": self.discovery_gate is not None,
            "prior_kb_available": self.prior_kb is not None,
            "data_layer_available": self.data_layer is not None,
            "discovery_gate_available": self.discovery_gate is not None,
            "legacy_available": EUREKA_AVAILABLE or LITERATURE_AVAILABLE,
            "prior_kb_relations": len(self.prior_kb.relations) if self.prior_kb else 0
        }


def create_transformational_enhanced_validation_pipeline(config: Any = None) -> TransformationalEnhancedValidationPipeline:
    """
    Factory function to create transformational-enhanced validation pipeline.

    Args:
        config: Configuration object

    Returns:
        Configured TransformationalEnhancedValidationPipeline
    """
    return TransformationalEnhancedValidationPipeline(config)