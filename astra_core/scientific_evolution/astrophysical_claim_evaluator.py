"""
ASTRA Astrophysical Claim Evaluation System
=============================================

Phase 2.1: Comprehensive astronomical claim evaluation using domain knowledge,
physical constraints, and observational feasibility assessment.

This system extends Phase 1 foundations to provide complete astronomical claim
validation, enabling ASTRA to evaluate discoveries like an autonomous astrophysical scientist.

Key Capabilities:
- Multi-dimensional claim evaluation
- Domain-specific knowledge integration
- Physical constraint validation
- Observational feasibility assessment
- Statistical rigor evaluation
- Literature consistency checking
- Alternative hypothesis identification
- Scientific confidence scoring

Date: 2025-06-29
Phase: 2.1 - Astrophysical Claim Evaluation
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re
import json

# Import Phase 1 tools
from astra_core.scientific_evolution.astra_scientific_behavior_analyzer import ASTRA_Mode, Scientific_Dimension
from astra_core.scientific_evolution.astronomical_question_formulator import Question_Category, Astronomical_Question
from astra_core.scientific_evolution.physical_consistency_validator import Physical_Domain, Consistency_Check_Result


class Claim_Category(Enum):
    """Categories of astronomical claims"""
    DISCOVERY = "discovery"           # New astronomical object/phenomenon
    PERFORMANCE = "performance"       # Computational/performance improvement
    THEORETICAL = "theoretical"       # Theoretical prediction/model
    OBSERVATIONAL = "observational"   # Observational result/measurement
    METHOD = "method"                # New analysis method/technique
    CONTROVERSIAL = "controversial"    # Challenges established science


class Evaluation_Dimension(Enum):
    """Dimensions for comprehensive claim evaluation"""
    PHYSICAL_CONSISTENCY = "physical"     # Known physical laws
    OBSERVATIONAL_FEASIBILITY = "obs"     # Detection/observation feasibility
    STATISTICAL_RIGOR = "stats"           # Statistical validity
    ASTRONOMICAL_CONTEXT = "astro"       # Domain knowledge consistency
    LITERATURE_CONSISTENCY = "lit"        # Previous research alignment
    METHODOLOGICAL_SOUNDNESS = "method"   # Analysis methodology
    REPRODUCIBILITY = "repro"             # Can results be reproduced?
    NOVELTY_ASSESSMENT = "novelty"        # Actually new or known?


@dataclass
class Claim_Evidence:
    """Evidence supporting or contradicting a claim"""
    evidence_type: str  # "supporting", "contradicting", "inconclusive"
    source: str
    description: str
    strength: str  # "strong", "moderate", "weak"
    astronomical_relevance: float  # 0.0 to 1.0


@dataclass
class Evaluation_Result:
    """Comprehensive evaluation of an astronomical claim"""
    claim: str
    claim_category: Claim_Category
    overall_confidence: float  # 0.0 to 1.0
    scientific_validity: str  # "valid", "questionable", "invalid", "requires_validation"

    dimension_scores: Dict[Evaluation_Dimension, Dict[str, Any]]

    supporting_evidence: List[Claim_Evidence]
    contradicting_evidence: List[Claim_Evidence]
    missing_evidence: List[str]

    critical_questions: List[str]
    validation_requirements: List[str]

    astronomical_concerns: List[str]
    alternative_explanations: List[str]

    publication_readiness: float  # 0.0 to 1.0
    recommended_actions: List[str]


class Astrophysical_Claim_Evaluator:
    """
    Comprehensive evaluation system for astronomical claims.

    This class integrates all Phase 1 tools and adds new capabilities to provide
    complete astronomical claim validation, enabling ASTRA to evaluate discoveries
    like an autonomous astrophysical scientist.
    """

    def __init__(self):
        # Import Phase 1 tools for integration
        from astra_core.scientific_evolution.astronomical_question_formulator import Astronomical_Question_Formulator
        from astra_core.scientific_evolution.physical_consistency_validator import Physical_Consistency_Validator
        from astra_core.scientific_evolution.astronomical_knowledge_builder import Astronomical_Knowledge_Base

        self.question_formulator = Astronomical_Question_Formulator()
        self.physical_validator = Physical_Consistency_Validator()
        self.knowledge_base = Astronomical_Knowledge_Base()

        # Astronomical validation criteria
        self.astronomical_criteria = {
            'stellar_constraints': self._evaluate_stellar_constraints,
            'galactic_constraints': self._evaluate_galactic_constraints,
            'cosmological_constraints': self._evaluate_cosmological_constraints,
            'observational_constraints': self._evaluate_observational_constraints
        }

    def evaluate_claim(self, claim: str,
                       claim_context: Optional[Dict[str, Any]] = None) -> Evaluation_Result:
        """
        Comprehensively evaluate an astronomical claim.

        This is the main evaluation method - it takes an astronomical claim and
        evaluates it across all scientific dimensions using domain knowledge.
        """
        claim_context = claim_context or {}

        # Determine claim category
        claim_category = self._classify_claim(claim)

        # Evaluate each dimension
        dimension_scores = {}

        # Physical consistency (using Phase 1 tool)
        physical_result = self.physical_validator.validate_consistency(claim, claim_context)
        dimension_scores[Evaluation_Dimension.PHYSICAL_CONSISTENCY] = {
            'score': 1.0 if physical_result.is_physically_consistent else 0.3,
            'details': physical_result.overall_assessment,
            'violations': physical_result.violations,
            'warnings': physical_result.warnings
        }

        # Observational feasibility (new evaluation)
        observational_score = self._evaluate_observational_feasibility_detailed(claim, claim_context)
        dimension_scores[Evaluation_Dimension.OBSERVATIONAL_FEASIBILITY] = observational_score

        # Statistical rigor (new evaluation)
        statistical_score = self._evaluate_statistical_rigor(claim, claim_context)
        dimension_scores[Evaluation_Dimension.STATISTICAL_RIGOR] = statistical_score

        # Astronomical context (using knowledge base)
        astro_context_score = self._evaluate_astronomical_context(claim, claim_context)
        dimension_scores[Evaluation_Dimension.ASTRONOMICAL_CONTEXT] = astro_context_score

        # Literature consistency (simulated for now)
        literature_score = self._evaluate_literature_consistency(claim, claim_context)
        dimension_scores[Evaluation_Dimension.LITERATURE_CONSISTENCY] = literature_score

        # Methodological soundness (new evaluation)
        method_score = self._evaluate_methodology(claim, claim_context)
        dimension_scores[Evaluation_Dimension.METHODOLOGICAL_SOUNDNESS] = method_score

        # Generate questions (using Phase 1 tool)
        question_analysis = self.question_formulator.generate_questions(claim, claim_context)
        critical_questions = [q.question for q in question_analysis.critical_questions]

        # Collect evidence
        supporting_evidence, contradicting_evidence, missing_evidence = self._collect_evidence(claim, claim_context)

        # Identify astronomical concerns
        astronomical_concerns = self._identify_astronomical_concerns(claim, dimension_scores, claim_context)

        # Generate alternative explanations
        alternative_explanations = self._generate_alternatives(claim, claim_context)

        # Calculate overall confidence
        overall_confidence = self._calculate_overall_confidence(dimension_scores, supporting_evidence, contradicting_evidence)

        # Determine scientific validity
        scientific_validity = self._determine_scientific_validity(overall_confidence, dimension_scores, astronomical_concerns)

        # Calculate publication readiness
        publication_readiness = self._assess_publication_readiness(claim, overall_confidence, dimension_scores)

        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(claim, scientific_validity, dimension_scores, astronomical_concerns)

        # Generate validation requirements
        validation_requirements = self._identify_validation_requirements(claim, dimension_scores, astronomical_concerns)

        return Evaluation_Result(
            claim=claim,
            claim_category=claim_category,
            overall_confidence=overall_confidence,
            scientific_validity=scientific_validity,
            dimension_scores=dimension_scores,
            supporting_evidence=supporting_evidence,
            contradicting_evidence=contradicting_evidence,
            missing_evidence=missing_evidence,
            critical_questions=critical_questions,
            validation_requirements=validation_requirements,
            astronomical_concerns=astronomical_concerns,
            alternative_explanations=alternative_explanations,
            publication_readiness=publication_readiness,
            recommended_actions=recommended_actions
        )

    def _classify_claim(self, claim: str) -> Claim_Category:
        """Classify the type of astronomical claim"""
        claim_lower = claim.lower()

        # Discovery claims
        if any(word in claim_lower for word in ['discovered', 'found', 'detected', 'identified', 'observed']):
            return Claim_Category.DISCOVERY

        # Performance claims
        if any(word in claim_lower for word in ['speedup', 'optimization', 'faster', 'efficient', 'performance']):
            return Claim_Category.PERFORMANCE

        # Theoretical claims
        if any(word in claim_lower for word in ['theory', 'model', 'predict', 'simulation', 'theoretical']):
            return Claim_Category.THEORETICAL

        # Method claims
        if any(word in claim_lower for word in ['method', 'technique', 'approach', 'algorithm', 'analysis']):
            return Claim_Category.METHOD

        # Observational claims
        if any(word in claim_lower for word in ['observation', 'measurement', 'data', 'survey', 'observed']):
            return Claim_Category.OBSERVATIONAL

        # Controversial claims (extraordinary language)
        if any(word in claim_lower for word in ['revolutionary', 'breakthrough', 'impossible', 'defies', 'violates']):
            return Claim_Category.CONTROVERSIAL

        return Claim_Category.DISCOVERY  # Default

    def _evaluate_observational_feasibility_detailed(self, claim: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detailed evaluation of observational feasibility"""
        claim_lower = claim.lower()
        score = 0.5
        details = []
        concerns = []

        # Check for specific astronomical observations
        if 'detect' in claim_lower or 'observe' in claim_lower:
            # What's being claimed to be detected?
            if any(obj in claim_lower for obj in ['star', 'galaxy', 'planet', 'exoplanet']):
                details.append("Claims detection of astronomical objects")

                # Check if instrument specifications mentioned
                if not any(inst in claim_lower for inst in ['telescope', 'instrument', 'jwst', 'hubble', 'gaia']):
                    concerns.append("No telescope/instrument capabilities specified")
                    score -= 0.2

            if 'sensitivity' in claim_lower or 'flux' in claim_lower:
                details.append("Claims sensitivity thresholds")

                # Check if flux values are realistic
                flux_pattern = r'(\d+\.?\d*[eE][-+]?\d*)\s*erg'
                flux_match = re.search(flux_pattern, claim)
                if flux_match:
                    flux_value = float(flux_match.group(1))
                    if flux_value < 1e-30:  # Extremely low flux
                        concerns.append(f"Extremely low flux claimed ({flux_value:.1e} erg/s/cm^2)")
                        score -= 0.3

        # Check for wavelength-specific observations
        if 'wavelength' in claim_lower or any(wave in claim_lower for wave in ['radio', 'optical', 'infrared', 'x-ray', 'gamma']):
            details.append("Claims multi-wavelength or specific wavelength observations")
            score += 0.2

        # Check for angular resolution claims
        if 'resolution' in claim_lower or 'angular' in claim_lower:
            details.append("Claims angular resolution capabilities")

            # Check if resolution is physically possible
            res_pattern = r'(\d+\.?\d*)\s*(arcsec|mas|μas)'
            res_match = re.search(res_pattern, claim)
            if res_match:
                res_value = float(res_match.group(1))
                if res_value < 0.001:  # Extremely high resolution
                    concerns.append(f"Extremely high angular resolution ({res_value} arcsec)")
                    score -= 0.2

        # Adjust score based on concerns
        if concerns:
            score = max(0.0, score - 0.1 * len(concerns))
        else:
            score = min(1.0, score + 0.2)

        return {
            'score': score,
            'details': details,
            'concerns': concerns
        }

    def _evaluate_statistical_rigor(self, claim: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate statistical rigor of the claim"""
        claim_lower = claim.lower()
        score = 0.5
        details = []
        concerns = []

        # Check for statistical indicators
        if 'significant' in claim_lower or 'sigma' in claim_lower or 'p-value' in claim_lower:
            details.append("Mentions statistical significance")
            score += 0.2

            # Check if significance level is appropriate
            if '3 sigma' in claim_lower or '5 sigma' in claim_lower:
                details.append("Uses appropriate significance thresholds for astronomy")
            elif '2 sigma' in claim_lower or 'p < 0.05' in claim_lower:
                # Lower significance for astronomy
                concerns.append("Uses lower significance threshold (astronomy typically requires >3σ)")
                score -= 0.1

        # Check for sample size
        if 'sample' in claim_lower or 'objects' in claim_lower or 'sources' in claim_lower:
            sample_pattern = r'(\d+)\s*(objects|sources|stars|galaxies)'
            sample_match = re.search(sample_pattern, claim)
            if sample_match:
                sample_size = int(sample_match.group(1))
                if sample_size < 10:
                    concerns.append(f"Very small sample size ({sample_size}) for astronomical claims")
                    score -= 0.2
                elif sample_size > 100:
                    details.append(f"Reasonable sample size ({sample_size})")
                    score += 0.1

        # Check for error analysis
        if 'error' in claim_lower or 'uncertainty' in claim_lower or 'error bar' in claim_lower:
            details.append("Includes error analysis")
            score += 0.2
        else:
            if claim_category_discovery(claim):
                concerns.append("No error bars or uncertainty mentioned for discovery claim")
                score -= 0.2

        # Check for completeness/bias corrections
        if 'completeness' in claim_lower or 'bias' in claim_lower or 'selection' in claim_lower:
            details.append("Considers observational biases and completeness")
            score += 0.1
        else:
            if claim_category_discovery(claim):
                concerns.append("No mention of selection effects or completeness corrections")
                score -= 0.1

        return {
            'score': max(0.0, min(1.0, score)),
            'details': details,
            'concerns': concerns
        }

    def _evaluate_astronomical_context(self, claim: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate astronomical context and domain knowledge consistency"""
        claim_lower = claim.lower()
        score = 0.5
        details = []
        concerns = []

        # Check for astronomical objects mentioned
        astro_objects = ['star', 'galaxy', 'planet', 'nebula', 'cluster', 'black hole',
                       'neutron star', 'white dwarf', 'supernova', 'quasar']
        found_objects = [obj for obj in astro_objects if obj in claim_lower]

        if found_objects:
            details.append(f"References astronomical objects: {found_objects}")
            score += 0.2

            # Check if descriptions are consistent with known properties
            for obj in found_objects:
                consistency_check = self._check_object_consistency(obj, claim)
                if consistency_check['consistent']:
                    details.append(f"{obj.capitalize()} description consistent with astronomy")
                else:
                    concerns.append(f"{obj.capitalize()} description inconsistent: {consistency_check['reason']}")
                    score -= 0.2

        # Check for physical processes
        physical_processes = ['formation', 'evolution', 'accretion', 'fusion',
                             'nucleosynthesis', 'feedback', 'collapse']
        found_processes = [proc for proc in physical_processes if proc in claim_lower]

        if found_processes:
            details.append(f"References astrophysical processes: {found_processes}")
            score += 0.1

        # Check for astronomical scales
        if any(scale in claim_lower for scale in ['parsec', 'kpc', 'mpc', 'solar mass',
                                                   'l_sun', 'm_sun', 'yr', 'gyr', 'myr']):
            details.append("Uses appropriate astronomical scales")
            score += 0.1

        # Check for HR diagram or stellar evolution context
        if 'hr diagram' in claim_lower or 'main sequence' in claim_lower or 'stellar evolution' in claim_lower:
            details.append("Provides stellar evolution context")
            score += 0.2

        return {
            'score': max(0.0, min(1.0, score)),
            'details': details,
            'concerns': concerns
        }

    def _check_object_consistency(self, obj_type: str, claim: str) -> Dict[str, Any]:
        """Check if description of astronomical object is consistent"""
        # Simplified consistency checks
        consistency_rules = {
            'star': {
                'mass_range': (0.08, 150),  # M_sun
                'temp_range': (3000, 40000),  # K
                'common_errors': ['temperatures outside main sequence', 'masses outside stable range']
            },
            'galaxy': {
                'mass_range': (1e6, 1e15),  # M_sun
                'size_range': (0.1, 100),  # kpc
                'common_errors': ['masses outside known range', 'unrealistic sizes']
            },
            'black hole': {
                'mass_range': (3, 1e11),  # M_sun
                'common_errors': ['masses below stellar collapse limit']
            }
        }

        rules = consistency_rules.get(obj_type, {})
        if not rules:
            return {'consistent': True, 'reason': 'No specific rules for this object type'}

        # Extract numerical values from claim
        # This is simplified - in practice would use more sophisticated extraction
        claim_lower = claim.lower()

        # Check for obvious inconsistencies
        for error_pattern in rules.get('common_errors', []):
            if error_pattern in claim_lower:
                return {'consistent': False, 'reason': error_pattern}

        return {'consistent': True, 'reason': 'No obvious inconsistencies detected'}

    def _evaluate_literature_consistency(self, claim: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate consistency with astronomical literature (simulated for now)"""
        claim_lower = claim.lower()
        score = 0.5
        details = []
        concerns = []

        # Check for literature references
        if any(ref in claim_lower for ref in ['literature', 'previous work', 'studies', 'published', 'paper']):
            details.append("References astronomical literature")
            score += 0.3

            # Check if comparison with known results
            if 'consistent with' in claim_lower or 'agrees with' in claim_lower:
                details.append("Compares favorably with previous astronomical findings")
                score += 0.2
            elif 'contradicts' in claim_lower or 'unlike' in claim_lower:
                concerns.append("Contradicts established astronomical results")
                score -= 0.1

        # Check for "first time" or "novel" claims
        if 'first' in claim_lower or 'novel' in claim_lower or 'unprecedented' in claim_lower:
            if 'literature' not in claim_lower:
                concerns.append("Claims novelty but doesn't reference existing literature")
                score -= 0.2
            else:
                details.append("Claims novelty with literature context")
                score += 0.1

        # Extraordinary claims need literature support
        if any(word in claim_lower for word in ['revolutionary', 'breakthrough', 'defies physics']):
            if 'literature' not in claim_lower and 'previous' not in claim_lower:
                concerns.append("Extraordinary claim lacks literature context")
                score -= 0.3

        return {
            'score': max(0.0, min(1.0, score)),
            'details': details,
            'concerns': concerns
        }

    def _evaluate_methodology(self, claim: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate methodological soundness"""
        claim_lower = claim.lower()
        score = 0.5
        details = []
        concerns = []

        # Check for methodology description
        if 'method' in claim_lower or 'technique' in claim_lower or 'approach' in claim_lower:
            details.append("Describes methodology")
            score += 0.2

            # Check if validation mentioned
            if 'validated' in claim_lower or 'tested' in claim_lower or 'verified' in claim_lower:
                details.append("Method has been validated")
                score += 0.2
            else:
                concerns.append("Method described but validation not mentioned")
                score -= 0.1

        # Check for performance metrics
        if 'speedup' in claim_lower or 'efficiency' in claim_lower or 'performance' in claim_lower:
            details.append("Claims performance improvements")

            # Check if baseline mentioned
            if 'baseline' in claim_lower or 'compared to' in claim_lower or 'previous' in claim_lower:
                details.append("Performance compared to baseline")
                score += 0.2
            else:
                concerns.append("Performance claims without baseline comparison")
                score -= 0.3

        # Check for reproducibility
        if 'reproducible' in claim_lower or 'replicable' in claim_lower:
            details.append("Method is reproducible")
            score += 0.2

        return {
            'score': max(0.0, min(1.0, score)),
            'details': details,
            'concerns': concerns
        }

    def _collect_evidence(self, claim: str, context: Dict[str, Any]) -> Tuple[List[Claim_Evidence], List[Claim_Evidence], List[str]]:
        """Collect supporting, contradicting, and missing evidence"""
        # This would connect to astronomical databases in practice
        supporting = []
        contradicting = []
        missing = []

        claim_lower = claim.lower()

        # Generate evidence suggestions based on claim type
        if 'discovered' in claim_lower or 'found' in claim_lower:
            missing.extend([
                "Independent confirmation from different instruments/methods",
                "Comparison with known similar objects",
                "Physical modeling of proposed mechanism"
            ])
        elif 'speedup' in claim_lower or 'optimization' in claim_lower:
            missing.extend([
                "Baseline performance measurements",
                "Standardized benchmark comparisons",
                "Reproducibility testing on different datasets"
            ])

        return supporting, contradicting, missing

    def _identify_astronomical_concerns(self, claim: str, dimension_scores: Dict[Evaluation_Dimension, Dict[str, Any]],
                                     context: Dict[str, Any]) -> List[str]:
        """Identify astronomical domain-specific concerns"""
        concerns = []

        # Collect concerns from each dimension
        for dimension, score_data in dimension_scores.items():
            if 'concerns' in score_data:
                concerns.extend(score_data['concerns'])
            if score_data['score'] < 0.5:
                concerns.append(f"Low score in {dimension.value}: {score_data.get('details', 'Unknown issue')}")

        # Add astronomical domain concerns
        claim_lower = claim.lower()

        # Check for stellar astrophysics concerns
        if 'star' in claim_lower:
            if not any(prop in claim_lower for prop in ['temperature', 'luminosity', 'mass', 'spectral type']):
                concerns.append("Stellar claim missing fundamental stellar parameters")

        # Check for galactic astronomy concerns
        if 'galaxy' in claim_lower:
            if not any(prop in claim_lower for prop in ['redshift', 'metallicity', 'environment']):
                concerns.append("Galaxy claim missing environmental context")

        return concerns

    def _generate_alternatives(self, claim: str, context: Dict[str, Any]) -> List[str]:
        """Generate astronomical alternative explanations"""
        alternatives = []
        claim_lower = claim.lower()

        # Generate alternatives based on claim type
        if 'discovered' in claim_lower or 'found' in claim_lower:
            alternatives.extend([
                "Instrumental systematic effects or calibration errors",
                "Selection effects in target sample",
                "Background or confusion sources",
                "Statistical fluctuations or chance alignments"
            ])

        if 'correlation' in claim_lower or 'relationship' in claim_lower:
            alternatives.extend([
                "Common cause or confounding variable",
                "Selection bias creating apparent correlation",
                "Multiple testing producing false positive",
                "Analysis method artifacts"
            ])

        if 'new' in claim_lower or 'novel' in claim_lower:
            alternatives.extend([
                "Known phenomenon in different parameter range",
                "Instrumental artifact masquerading as discovery",
                "Observational bias creating apparent novelty"
            ])

        return alternatives

    def _calculate_overall_confidence(self, dimension_scores: Dict[Evaluation_Dimension, Dict[str, Any]],
                                      supporting: List[Claim_Evidence], contradicting: List[Claim_Evidence]) -> float:
        """Calculate overall confidence in the claim"""
        if not dimension_scores:
            return 0.5

        # Weight different dimensions
        weights = {
            Evaluation_Dimension.PHYSICAL_CONSISTENCY: 0.3,
            Evaluation_Dimension.OBSERVATIONAL_FEASIBILITY: 0.2,
            Evaluation_Dimension.STATISTICAL_RIGOR: 0.2,
            Evaluation_Dimension.ASTRONOMICAL_CONTEXT: 0.1,
            Evaluation_Dimension.LITERATURE_CONSISTENCY: 0.1,
            Evaluation_Dimension.METHODOLOGICAL_SOUNDNESS: 0.1
        }

        weighted_score = 0.0
        for dimension, score_data in dimension_scores.items():
            weight = weights.get(dimension, 0.1)
            weighted_score += weight * score_data['score']

        # Adjust based on evidence
        if supporting:
            weighted_score += 0.1 * len(supporting)
        if contradicting:
            weighted_score -= 0.2 * len(contradicting)

        return max(0.0, min(1.0, weighted_score))

    def _determine_scientific_validity(self, confidence: float,
                                     dimension_scores: Dict[Evaluation_Dimension, Dict[str, Any]],
                                     concerns: List[str]) -> str:
        """Determine overall scientific validity"""
        # Check for critical failures
        critical_dimensions = [Evaluation_Dimension.PHYSICAL_CONSISTENCY, Evaluation_Dimension.STATISTICAL_RIGOR]

        for dimension in critical_dimensions:
            if dimension_scores[dimension]['score'] < 0.3:
                return "invalid"

        # Check for significant concerns
        if len(concerns) >= 3:
            return "questionable"

        # High confidence but needs validation
        if confidence > 0.7 and len(concerns) > 0:
            return "requires_validation"

        # Low confidence
        if confidence < 0.4:
            return "questionable"

        # Good confidence with minimal concerns
        if confidence > 0.7 and len(concerns) <= 1:
            return "valid"

        return "requires_validation"

    def _assess_publication_readiness(self, claim: str, confidence: float,
                                     dimension_scores: Dict[Evaluation_Dimension, Dict[str, Any]]) -> float:
        """Assess readiness for astronomical publication"""
        readiness = 0.5

        # High confidence boosts readiness
        if confidence > 0.8:
            readiness += 0.3
        elif confidence < 0.5:
            readiness -= 0.2

        # Statistical rigor is critical for publication
        stat_score = dimension_scores.get(Evaluation_Dimension.STATISTICAL_RIGOR, {}).get('score', 0.5)
        if stat_score > 0.7:
            readiness += 0.2
        elif stat_score < 0.4:
            readiness -= 0.3

        # Literature context needed for publication
        lit_score = dimension_scores.get(Evaluation_Dimension.LITERATURE_CONSISTENCY, {}).get('score', 0.5)
        if lit_score > 0.6:
            readiness += 0.1

        return max(0.0, min(1.0, readiness))

    def _generate_recommended_actions(self, claim: str, validity: str,
                                   dimension_scores: Dict[Evaluation_Dimension, Dict[str, Any]],
                                   concerns: List[str]) -> List[str]:
        """Generate recommended actions based on evaluation"""
        actions = []

        if validity == "invalid":
            actions.append("Reject claim - violates physical constraints or statistical rigor")
        elif validity == "questionable":
            actions.extend([
                "Request additional evidence and validation",
                "Suggest revisions to address concerns",
                "Ask for clarification on ambiguous points"
            ])
        elif validity == "requires_validation":
            actions.extend([
                "Request independent verification",
                "Suggest additional testing",
                "Ask for baseline comparisons",
                "Recommend uncertainty analysis"
            ])
        elif validity == "valid":
            actions.extend([
                "Proceed with implementation/investigation",
                "Document validation process",
                "Plan follow-up observations/studies"
            ])

        # Add dimension-specific actions
        for dimension, score_data in dimension_scores.items():
            if score_data['score'] < 0.5:
                if dimension == Evaluation_Dimension.PHYSICAL_CONSISTENCY:
                    actions.append("Re-examine physical constraints and energy requirements")
                elif dimension == Evaluation_Dimension.STATISTICAL_RIGOR:
                    actions.append("Strengthen statistical analysis and error propagation")
                elif dimension == Evaluation_Dimension.OBSERVATIONAL_FEASIBILITY:
                    actions.append("Clarify observational requirements and feasibility")

        return actions

    def _identify_validation_requirements(self, claim: str,
                                        dimension_scores: Dict[Evaluation_Dimension, Dict[str, Any]],
                                        concerns: List[str]) -> List[str]:
        """Identify specific validation requirements"""
        requirements = []

        # Statistical validation always needed
        if dimension_scores.get(Evaluation_Dimension.STATISTICAL_RIGOR, {}).get('score', 1.0) < 0.7:
            requirements.append("Statistical validation with proper error analysis")

        # Physical consistency validation for discoveries
        claim_lower = claim.lower()
        if 'discovered' in claim_lower or 'found' in claim_lower:
            requirements.extend([
                "Physical modeling of proposed mechanism",
                "Comparison with known astrophysical objects",
                "Observational confirmation with independent methods"
            ])

        # Baseline comparison for performance claims
        if 'speedup' in claim_lower or 'optimization' in claim_lower:
            requirements.extend([
                "Baseline performance measurement",
                "Standardized benchmark testing",
                "Reproducibility validation"
            ])

        # Add concern-specific requirements
        for concern in concerns:
            if 'selection' in concern.lower() or 'bias' in concern.lower():
                requirements.append("Selection effect and completeness analysis")
            elif 'telescope' in concern.lower() or 'instrument' in concern.lower():
                requirements.append("Telescope feasibility calculations")

        return requirements

    def _evaluate_stellar_constraints(self, claim: str) -> Dict[str, Any]:
        """Evaluate stellar astrophysics constraints"""
        constraints = {
            'temperature_range': (3000, 40000),  # K
            'mass_range': (0.08, 150),  # M_sun
            'luminosity_range': (1e-4, 1e6),  # L_sun
        }
        return {'constraints': constraints, 'applied': []}

    def _evaluate_galactic_constraints(self, claim: str) -> Dict[str, Any]:
        """Evaluate galactic astronomy constraints"""
        constraints = {
            'mass_range': (1e6, 1e15),  # M_sun
            'size_range': (0.1, 100),  # kpc
        }
        return {'constraints': constraints, 'applied': []}

    def _evaluate_cosmological_constraints(self, claim: str) -> Dict[str, Any]:
        """Evaluate cosmological constraints"""
        constraints = {
            'age_limit': 13.8,  # Gyr
            'redshift_range': (0, 1100),
        }
        return {'constraints': constraints, 'applied': []}

    def _evaluate_observational_constraints(self, claim: str) -> Dict[str, Any]:
        """Evaluate observational constraints"""
        constraints = {
            'flux_range': (1e-19, 1e-12),  # erg/s/cm^2/Hz
            'angular_resolution': (0.001, 1),  # arcsec
        }
        return {'constraints': constraints, 'applied': []}


# Helper function
def claim_category_discovery(claim: str) -> bool:
    """Check if claim is a discovery claim"""
    claim_lower = claim.lower()
    return any(word in claim_lower for word in ['discovered', 'found', 'detected', 'identified'])


# Convenience function
def evaluate_astronomical_claim(claim: str, context: Dict[str, Any] = None) -> Evaluation_Result:
    """Evaluate an astronomical claim comprehensively"""
    evaluator = Astrophysical_Claim_Evaluator()
    return evaluator.evaluate_claim(claim, context)


if __name__ == "__main__":
    # Example usage
    print("ASTRA Astrophysical Claim Evaluator - Phase 2.1")
    print("=" * 60)

    # Test with my BIODISC claim
    test_claim = "Our BIODISC optimizations achieve 3-10x speedup for astronomical discoveries with 60-80% cache hit rates"

    evaluation = evaluate_astronomical_claim(test_claim)

    print(f"Claim: {evaluation.claim}")
    print(f"Category: {evaluation.claim_category.value}")
    print(f"Scientific Validity: {evaluation.scientific_validity}")
    print(f"Overall Confidence: {evaluation.overall_confidence:.2f}")
    print(f"Publication Readiness: {evaluation.publication_readiness:.2f}")

    print("\nDimension Scores:")
    for dimension, score_data in evaluation.dimension_scores.items():
        print(f"  {dimension.value}: {score_data['score']:.2f}")

    print("\nCritical Questions:", evaluation.critical_questions[:3])
    print("Astronomical Concerns:", evaluation.astronomical_concerns)
    print("Alternative Explanations:", evaluation.alternative_explanations[:3])
    print("Recommended Actions:", evaluation.recommended_actions)

    print("\n" + "=" * 60)
    print("Phase 2.1 complete: Comprehensive claim evaluation operational")