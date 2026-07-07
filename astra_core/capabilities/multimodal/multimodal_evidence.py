"""
V103 Multi-Modal Evidence Integration - Combining Text, Numerical, and Visual Evidence
========================================================================================

PROBLEM: Scientific reasoning requires combining multiple evidence types:
- Numerical data: correlations, statistical tests, measurements
- Textual evidence: literature, abstracts, observation reports
- Visual evidence: plots, images, spectra, diagnostic figures
- Code evidence: reproducible analysis scripts

Current systems treat these in isolation. V103 integrates them.

SOLUTION: Multi-modal evidence fusion with:
1. Evidence Fusion Framework
   - Unified representation for different evidence types
   - Cross-modal attention mechanisms
   - Evidence quality scoring

2. Cross-Modal Validation
   - Text confirms numerical results
   - Visualizations support textual claims
   - Code ensures reproducibility

3. Evidence Triangulation
   - Automatic identification of converging evidence
   - Flagging contradictory evidence
   - Confidence aggregation across modalities

INTEGRATION:
- Works with V97 (novelty scoring now includes multi-modal evidence)
- Integrates with V4.0 MCE (contextualizes evidence)
- Links with V106 (explainable reasoning from evidence)

USE CASES:
- Validate star formation threshold with images + data + literature
- Cross-validate AGN feedback claims across wavelengths
- Combine simulation code with observational constraints

Date: 2026-04-14
Version: 1.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
import numpy as np
from scipy import stats
import json
import warnings


class EvidenceType(Enum):
    """Types of evidence"""
    NUMERICAL = "numerical"       # Statistics, correlations, measurements
    TEXTUAL = "textual"          # Literature, abstracts, reports
    VISUAL = "visual"             # Plots, images, spectra
    CODE = "code"                 # Analysis scripts, notebooks
    THEORETICAL = "theoretical"   # Physical models, first principles


class EvidenceQuality(Enum):
    """Quality levels for evidence"""
    PEER_REVIEWED = "peer_reviewed"     # Published, peer-reviewed
    REPRODUCIBLE = "reproducible"       # Reproducible code available
    OBSERVATIONAL = "observational"     # Direct observation
    THEORETICAL = "theoretical"         # Theoretically derived
    UNVERIFIED = "unverified"           # Not independently verified


@dataclass
class EvidenceItem:
    """Single piece of evidence"""
    evidence_id: str
    evidence_type: EvidenceType
    content: Any  # Data varies by type
    source: str
    quality: EvidenceQuality
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            'evidence_id': self.evidence_id,
            'evidence_type': self.evidence_type.value,
            'source': self.source,
            'quality': self.quality.value,
            'confidence': self.confidence,
            'metadata': self.metadata
        }


@dataclass
class CrossModalLink:
    """Link between evidence items across modalities"""
    evidence_id_1: str
    evidence_id_2: str
    link_type: str  # "confirms", "contradicts", "extends", "explains"
    confidence: float
    description: str


@dataclass
class EvidenceFusionResult:
    """Result of multi-modal evidence fusion"""
    claim_id: str
    claim: str
    supporting_evidence: List[str]  # IDs of supporting evidence
    contradictory_evidence: List[str]  # IDs of contradictory evidence
    aggregate_confidence: float
    evidence_quality_score: float
    triangulation_strength: str  # "strong", "moderate", "weak", "none"
    requires_validation: bool


class EvidenceRepository:
    """
    Repository for storing and retrieving evidence across modalities.
    """

    def __init__(self):
        """Initialize evidence repository"""
        self.evidence: Dict[str, EvidenceItem] = {}
        self.links: List[CrossModalLink] = []

    def add_evidence(self, evidence: EvidenceItem):
        """Add evidence to repository"""
        self.evidence[evidence.evidence_id] = evidence

    def get_evidence(self, evidence_id: str) -> Optional[EvidenceItem]:
        """Retrieve evidence by ID"""
        return self.evidence.get(evidence_id)

    def get_evidence_by_type(
        self,
        evidence_type: EvidenceType
    ) -> List[EvidenceItem]:
        """Get all evidence of a specific type"""
        return [e for e in self.evidence.values()
                if e.evidence_type == evidence_type]

    def add_link(self, link: CrossModalLink):
        """Add cross-modal link"""
        self.links.append(link)

    def search_evidence(
        self,
        query: str,
        evidence_types: Optional[List[EvidenceType]] = None
    ) -> List[EvidenceItem]:
        """Search evidence by query string"""
        results = []
        query_lower = query.lower()

        for evidence in self.evidence.values():
            if evidence_types and evidence.evidence_type not in evidence_types:
                continue

            # Search in content (type-specific)
            content_str = self._evidence_to_string(evidence)
            if query_lower in content_str.lower():
                results.append(evidence)

        return results

    def _evidence_to_string(self, evidence: EvidenceItem) -> str:
        """Convert evidence to searchable string"""
        if evidence.evidence_type == EvidenceType.TEXTUAL:
            return str(evidence.content)
        elif evidence.evidence_type == EvidenceType.NUMERICAL:
            return f"{evidence.metadata.get('variable', '')}: {evidence.content}"
        elif evidence.evidence_type == EvidenceType.VISUAL:
            return f"{evidence.metadata.get('description', '')}: {evidence.source}"
        elif evidence.evidence_type == EvidenceType.CODE:
            return f"Script: {evidence.metadata.get('filename', '')}"
        else:
            return str(evidence.content)


class MultiModalEvidenceFusion:
    """
    Main engine for multi-modal evidence integration.

    Features:
    - Evidence fusion from multiple modalities
    - Cross-modal validation
    - Triangulation detection
    - Confidence aggregation
    """

    def __init__(self):
        """Initialize multi-modal evidence fusion"""
        self.repository = EvidenceRepository()

        # ✅ FIX: Don't load model during initialization - use lazy loading with timeout
        self.embedder = None
        self.nlp_available = False
        self.model_loading = False

        # Model will be loaded on first use with timeout protection
        # This prevents blocking during system initialization

    def _load_model_with_timeout(self, timeout_seconds=60) -> bool:
        """
        Load model with timeout to prevent blocking.

        Args:
            timeout_seconds: Maximum time to wait for model loading

        Returns:
            True if model loaded successfully, False otherwise
        """
        if self.model_loading:
            return False  # Already loading

        if self.nlp_available and self.embedder is not None:
            return True  # Already loaded

        self.model_loading = True

        try:
            import signal

            def timeout_handler(signum, frame):
                raise TimeoutError(f"Model loading timed out after {timeout_seconds}s")

            # Set alarm for timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_seconds)

            try:
                from sentence_transformers import SentenceTransformer
                self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
                self.nlp_available = True

                # Cancel alarm
                signal.alarm(0)
                return True

            except TimeoutError:
                signal.alarm(0)  # Cancel alarm
                print(f"Warning: Model loading timed out after {timeout_seconds}s")
                return False

        except Exception as e:
            signal.alarm(0)  # Ensure alarm is cancelled
            print(f"Warning: Model loading failed: {e}")
            return False

        finally:
            self.model_loading = False

    def add_numerical_evidence(
        self,
        variable1: str,
        variable2: str,
        correlation: float,
        p_value: float,
        sample_size: int,
        source: str = "analysis"
    ) -> str:
        """Add numerical evidence (correlation, statistical test)"""
        evidence = EvidenceItem(
            evidence_id=f"num_{variable1}_{variable2}_{source}",
            evidence_type=EvidenceType.NUMERICAL,
            content={
                'variables': [variable1, variable2],
                'correlation': correlation,
                'p_value': p_value,
                'sample_size': sample_size
            },
            source=source,
            quality=EvidenceQuality.OBSERVATIONAL,
            confidence=1.0 - p_value,
            metadata={
                'statistical_test': 'correlation',
                'effect_size': abs(correlation)
            }
        )
        self.repository.add_evidence(evidence)
        return evidence.evidence_id

    def add_textual_evidence(
        self,
        text: str,
        source: str,
        quality: EvidenceQuality = EvidenceQuality.OBSERVATIONAL,
        relevance_score: float = 1.0
    ) -> str:
        """Add textual evidence from literature"""
        evidence_id = f"text_{source}_{len(text)}"
        evidence = EvidenceItem(
            evidence_id=evidence_id,
            evidence_type=EvidenceType.TEXTUAL,
            content=text,
            source=source,
            quality=quality,
            confidence=relevance_score,
            metadata={'source_type': 'literature'}
        )
        self.repository.add_evidence(evidence)
        return evidence_id

    def add_visual_evidence(
        self,
        description: str,
        image_path: str,
        source: str,
        figure_type: str = "plot",
        confidence: float = 1.0
    ) -> str:
        """Add visual evidence (plot, image, spectrum)"""
        evidence = EvidenceItem(
            evidence_id=f"visual_{source}_{description[:30]}",
            evidence_type=EvidenceType.VISUAL,
            content=image_path,
            source=source,
            quality=EvidenceQuality.OBSERVATIONAL,
            confidence=confidence,
            metadata={
                'description': description,
                'figure_type': figure_type
            }
        )
        self.repository.add_evidence(evidence)
        return evidence.evidence_id

    def add_code_evidence(
        self,
        code_path: str,
        description: str,
        reproducibility: float = 1.0
    ) -> str:
        """Add code evidence (analysis script, notebook)"""
        quality = EvidenceQuality.REPRODUCIBLE if reproducibility > 0.8 else EvidenceQuality.UNVERIFIED

        evidence = EvidenceItem(
            evidence_id=f"code_{code_path}",
            evidence_type=EvidenceType.CODE,
            content=code_path,
            source="repository",
            quality=quality,
            confidence=reproducibility,
            metadata={
                'filename': code_path,
                'description': description
            }
        )
        self.repository.add_evidence(evidence)
        return evidence.evidence_id

    def fuse_evidence_for_claim(
        self,
        claim: str,
        relevant_evidence: List[str],
        claim_type: str = "causal"
    ) -> EvidenceFusionResult:
        """
        Fuse multi-modal evidence for a scientific claim.

        Args:
            claim: Scientific claim to evaluate
            relevant_evidence: IDs of relevant evidence
            claim_type: Type of claim (causal, correlation, theoretical, etc.)

        Returns:
            EvidenceFusionResult with aggregated assessment
        """
        # Retrieve evidence items
        evidence_items = []
        for ev_id in relevant_evidence:
            ev = self.repository.get_evidence(ev_id)
            if ev:
                evidence_items.append(ev)

        if not evidence_items:
            return EvidenceFusionResult(
                claim_id=f"claim_{hash(claim)}",
                claim=claim,
                supporting_evidence=[],
                contradictory_evidence=[],
                aggregate_confidence=0.0,
                evidence_quality_score=0.0,
                triangulation_strength="none",
                requires_validation=True
            )

        # Classify evidence
        supporting = []
        contradictory = []

        # Textual analysis if available
        # ✅ FIX: Lazy load model on first use with timeout protection
        if not self.nlp_available or not self.embedder:
            self._load_model_with_timeout(timeout_seconds=60)

        if self.nlp_available and self.embedder:
            claim_embedding = self.embedder.encode(claim)

            for ev in evidence_items:
                if ev.evidence_type == EvidenceType.TEXTUAL:
                    ev_embedding = self.embedder.encode(ev.content)
                    similarity = np.dot(claim_embedding, ev_embedding) / (
                        np.linalg.norm(claim_embedding) * np.linalg.norm(ev_embedding)
                    )

                    if similarity > 0.7:  # Threshold for supporting
                        supporting.append(ev.evidence_id)
                    elif similarity < -0.3:  # Contradictory
                        contradictory.append(ev.evidence_id)

        # Numerical evidence assessment
        for ev in evidence_items:
            if ev.evidence_type == EvidenceType.NUMERICAL:
                # Check if numerical results support claim
                if self._numerical_evidence_supports_claim(ev, claim):
                    supporting.append(ev.evidence_id)
                else:
                    contradictory.append(ev.evidence_id)

        # Visual evidence (requires user annotation for now)
        for ev in evidence_items:
            if ev.evidence_type == EvidenceType.VISUAL:
                # For now, assume visual evidence is supporting
                supporting.append(ev.evidence_id)

        # Code evidence (reproducibility)
        for ev in evidence_items:
            if ev.evidence_type == EvidenceType.CODE:
                supporting.append(ev.evidence_id)

        # Compute aggregate confidence
        if evidence_items:
            avg_confidence = np.mean([e.confidence for e in evidence_items])
            quality_score = np.mean([
                self._quality_to_score(e.quality) for e in evidence_items
            ])
        else:
            avg_confidence = 0.0
            quality_score = 0.0

        # Triangulation strength
        n_modalities = len(set(e.evidence_type for e in evidence_items))
        if n_modalities >= 3 and len(contradictory) == 0:
            triangulation = "strong"
        elif n_modalities >= 2 and len(contradictory) == 0:
            triangulation = "moderate"
        elif n_modalities >= 1:
            triangulation = "weak"
        else:
            triangulation = "none"

        return EvidenceFusionResult(
            claim_id=f"claim_{hash(claim)}",
            claim=claim,
            supporting_evidence=supporting,
            contradictory_evidence=contradictory,
            aggregate_confidence=avg_confidence,
            evidence_quality_score=quality_score,
            triangulation_strength=triangulation,
            requires_validation=len(contradictory) > 0
        )

    def _numerical_evidence_supports_claim(self, evidence: EvidenceItem, claim: str) -> bool:
        """Check if numerical evidence supports claim"""
        # Simplified: check if p-value indicates significance
        if evidence.content.get('p_value', 1.0) < 0.05:
            return True
        return False

    def _quality_to_score(self, quality: EvidenceQuality) -> float:
        """Convert quality enum to numeric score"""
        quality_scores = {
            EvidenceQuality.PEER_REVIEWED: 1.0,
            EvidenceQuality.REPRODUCIBLE: 0.9,
            EvidenceQuality.OBSERVATIONAL: 0.7,
            EvidenceQuality.THEORETICAL: 0.6,
            EvidenceQuality.UNVERIFIED: 0.3
        }
        return quality_scores.get(quality, 0.5)

    def detect_contradictions(
        self,
        claim: str,
        evidence_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Detect contradictions in evidence.

        Returns:
            List of contradiction descriptions
        """
        contradictions = []

        # Get evidence items
        evidence_items = []
        for ev_id in evidence_ids:
            ev = self.repository.get_evidence(ev_id)
            if ev:
                evidence_items.append(ev)

        # Check for numerical contradictions
        numerical_evidence = [e for e in evidence_items
                             if e.evidence_type == EvidenceType.NUMERICAL]

        for i, ev1 in enumerate(numerical_evidence):
            for ev2 in numerical_evidence[i+1:]:
                if ev1.content.get('variable1') == ev2.content.get('variable1'):
                    # Check if correlations conflict significantly
                    if abs(ev1.content.get('correlation', 0) - ev2.content.get('correlation', 0)) > 0.5:
                        contradictions.append({
                            'type': 'numerical_conflict',
                            'evidence_1': ev1.evidence_id,
                            'evidence_2': ev2.evidence_id,
                            'description': f"Conflicting correlations: {ev1.content.get('correlation'):.2f} vs {ev2.content.get('correlation'):.2f}"
                        })

        return contradictions

    def generate_evidence_summary(
        self,
        claim: str,
        evidence_ids: List[str]
    ) -> str:
        """
        Generate human-readable summary of evidence.

        Returns:
            Formatted summary string
        """
        fusion_result = self.fuse_evidence_for_claim(claim, evidence_ids)

        summary = []
        summary.append(f"EVIDENCE SUMMARY FOR: {claim}\n")

        summary.append(f"Aggregate Confidence: {fusion_result.aggregate_confidence:.2f}")
        summary.append(f"Evidence Quality Score: {fusion_result.evidence_quality_score:.2f}")
        summary.append(f"Triangulation Strength: {fusion_result.triangulation_strength}\n")

        summary.append(f"Supporting Evidence ({len(fusion_result.supporting_evidence)}):")
        for ev_id in fusion_result.supporting_evidence[:5]:  # Show first 5
            ev = self.repository.get_evidence(ev_id)
            if ev:
                summary.append(f"  - [{ev.evidence_type.value}] {ev.source}: {self._evidence_to_string(ev)[:60]}...")

        if fusion_result.contradictory_evidence:
            summary.append(f"\nContradictory Evidence ({len(fusion_result.contradictory_evidence)}):")
            for ev_id in fusion_result.contradictory_evidence[:5]:
                ev = self.repository.get_evidence(ev_id)
                if ev:
                    summary.append(f"  - [{ev.evidence_type.value}] {ev.source}: {self._evidence_to_string(ev)[:60]}...")

        if fusion_result.requires_validation:
            summary.append("\n⚠️ VALIDATION REQUIRED: Evidence contains contradictions")

        return "\n".join(summary)


class CrossModalAttention:
    """
    Cross-modal attention mechanism for linking evidence across modalities.

    Identifies relationships like:
    - "This plot confirms the textual claim in Paper X"
    - "This numerical result extends the visual pattern"
    """

    def __init__(self):
        """Initialize cross-modal attention"""
        self.attention_weights = {}

    def compute_cross_modal_attention(
        self,
        query: str,
        evidence_items: List[EvidenceItem]
    ) -> Dict[str, float]:
        """
        Compute attention weights for evidence items given a query.

        Args:
            query: Query string
            evidence_items: List of evidence to attend to

        Returns:
            Dictionary mapping evidence_id to attention weight
        """
        weights = {}

        # ✅ FIX: Lazy load model on first use with timeout protection
        if not self.nlp_available or not self.embedder:
            self._load_model_with_timeout(timeout_seconds=60)

        if not self.nlp_available or not self.embedder:
            # Fallback: random weights
            for ev in evidence_items:
                weights[ev.evidence_id] = 1.0 / len(evidence_items)
            return weights

        query_embedding = self.embedder.encode(query)

        for ev in evidence_items:
            if ev.evidence_type == EvidenceType.TEXTUAL:
                ev_embedding = self.embedder.encode(ev.content)
                similarity = np.dot(query_embedding, ev_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(ev_embedding)
                )
                weights[ev.evidence_id] = similarity

            elif ev.evidence_type == EvidenceType.NUMERICAL:
                # Check if query mentions variables
                if ev.content.get('variable1', '') in query or ev.content.get('variable2', '') in query:
                    weights[ev.evidence_id] = 0.8
                else:
                    weights[ev.evidence_id] = 0.2

            else:
                # Default weight for other types
                weights[ev.evidence_id] = 0.5

        return weights


# Factory functions

def create_multimodal_evidence_fusion() -> MultiModalEvidenceFusion:
    """Factory function to create MultiModalEvidenceFusion"""
    return MultiModalEvidenceFusion()


def create_cross_modal_attention() -> CrossModalAttention:
    """Factory function to create CrossModalAttention"""
    return CrossModalAttention()


# Convenience functions

def evaluate_hypothesis_with_multimodal_evidence(
    hypothesis: str,
    numerical_data: Optional[Dict] = None,
    literature_evidence: Optional[List[str]] = None,
    visual_evidence: Optional[List[Dict]] = None,
    code_evidence: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Evaluate a scientific hypothesis using multi-modal evidence.

    Args:
        hypothesis: Hypothesis to evaluate
        numerical_data: Dict with statistical test results
        literature_evidence: List of literature snippets
        visual_evidence: List of visual evidence descriptions
        code_evidence: List of code file paths

    Returns:
        Complete evaluation results
    """
    fusion = create_multimodal_evidence_fusion()
    evidence_ids = []

    # Add numerical evidence
    if numerical_data:
        for var1, var2, stats in numerical_data.get('correlations', []):
            ev_id = fusion.add_numerical_evidence(
                var1=var1,
                var2=var2,
                correlation=stats.get('correlation', 0),
                p_value=stats.get('p_value', 1),
                sample_size=stats.get('n', 0)
            )
            evidence_ids.append(ev_id)

    # Add textual evidence
    if literature_evidence:
        for text in literature_evidence:
            ev_id = fusion.add_textual_evidence(text, source="literature")
            evidence_ids.append(ev_id)

    # Add visual evidence
    if visual_evidence:
        for vis in visual_evidence:
            ev_id = fusion.add_visual_evidence(
                description=vis.get('description', ''),
                image_path=vis.get('path', ''),
                source=vis.get('source', 'visual')
            )
            evidence_ids.append(ev_id)

    # Add code evidence
    if code_evidence:
        for code_path in code_evidence:
            ev_id = fusion.add_code_evidence(code_path=code_path)
            evidence_ids.append(ev_id)

    # Fuse evidence
    fusion_result = fusion.fuse_evidence_for_claim(hypothesis, evidence_ids)

    # Generate summary
    summary = fusion.generate_evidence_summary(hypothesis, evidence_ids)

    # Detect contradictions
    contradictions = fusion.detect_contradictions(hypothesis, evidence_ids)

    return {
        'fusion_result': fusion_result,
        'summary': summary,
        'contradictions': contradictions,
        'recommendation': _generate_recommendation(fusion_result, contradictions)
    }


def _generate_recommendation(
    fusion_result: EvidenceFusionResult,
    contradictions: List
) -> str:
    """Generate recommendation based on fusion result"""
    if fusion_result.aggregate_confidence > 0.8:
        return "HIGH CONFIDENCE: Claim well-supported by multi-modal evidence"
    elif fusion_result.aggregate_confidence > 0.5:
        return "MODERATE CONFIDENCE: Claim partially supported, validation recommended"
    elif len(contradictions) > 0:
        return f"LOW CONFIDENCE: {len(contradictions)} contradictions detected, requires investigation"
    else:
        return "INSUFFICIENT EVIDENCE: Not enough evidence to evaluate claim"
