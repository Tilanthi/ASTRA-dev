"""
V104 Adversarial Hypothesis Framework - Systematic Challenge and Refinement
=======================================================================

PROBLEM: Scientific discoveries can be false positives due to:
- Observer bias
- Confounding variables
- Analysis choices (p-hacking, HARKing)
- Selection effects

SOLUTION: Adversarial framework that systematically challenges discoveries:
1. Devil's Advocate Agent
2. Red Team Discovery
3. Hypothesis Refinement Loop
4. Robustness Testing

INTEGRATION:
- Extends V97 (knowledge isolation with adversarial validation)
- Integrates with V102 (counterfactual engine for robustness testing)
- Uses swarm intelligence (falsifier agents)

Date: 2026-04-14
Version: 1.0
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import numpy as np
from scipy import stats
import json


class ChallengeType(Enum):
    """Types of adversarial challenges"""
    BIAS = "bias"                   # Observer bias
    CONFOUNDER = "confounder"         # Hidden confounding
    SELECTION = "selection"           # Selection effect
    ANALYSIS_CHOICE = "analysis_choice" # HARKing, p-hacking
    ALTERNATIVE = "alternative"       # Alternative explanation
    REPRODUCIBILITY = "reproducibility" # Cannot reproduce


@dataclass
class AdversarialChallenge:
    """A challenge to a scientific claim"""
    challenge_id: str
    challenge_type: ChallengeType
    description: str
    severity: str  # "critical", "moderate", "low"
    proposed_resolution: str = ""
    refuted: bool = False
    confidence: float = 1.0


@dataclass
class RefinedHypothesis:
    """Hypothesis after adversarial refinement"""
    original_hypothesis: str
    challenges_received: List[AdversarialChallenge]
    modifications_made: List[str]
    final_confidence: float
    robustness_score: float
    requires_validation: List[str]


class DevilsAdvocateAgent:
    """
    Devil's Advocate Agent that challenges scientific claims.

    Systematically generates alternative explanations and identifies
    potential sources of bias or confounding.
    """

    def __init__(self):
        """Initialize Devil's Advocate Agent"""
        self.challenge_templates = {
            ChallengeType.CONFOUNDER: [
                "Could {variable} be a confounder rather than a cause?",
                "Are we missing latent variables that explain both {var1} and {var2}?",
                "Might both {var1} and {var2} be caused by {hidden_var}?"
            ],
            ChallengeType.SELECTION: [
                "Could this pattern be due to selection effects?",
                "Is the sample biased toward {property} objects?",
                "Might we be missing {type} objects that weren't observed?"
            ],
            ChallengeType.ANALYSIS_CHOICE: [
                "Was the analysis method chosen after seeing the data?",
                "Could different analysis choices change the result?",
                "Are we p-hacking by testing multiple hypotheses?",
            ],
            ChallengeType.ALTERNATIVE: [
                "Could {physical_mechanism} explain this instead?",
                "Magnitude of effect consistent with {alternative_theory}?",
                "Could this be explained by {instrumental_effect}?"
            ]
        }

    def generate_challenges(
        self,
        hypothesis: str,
        hypothesis_type: str,
        variables: List[str],
        effect_size: float,
        sample_size: int
    ) -> List[AdversarialChallenge]:
        """
        Generate systematic challenges to a hypothesis.

        Args:
            hypothesis: Hypothesis to challenge
            hypothesis_type: Type of hypothesis (causal, correlation, etc.)
            variables: Variables involved
            effect_size: Estimated effect size
            sample_size: Sample size

        Returns:
            List of adversarial challenges
        """
        challenges = []

        # Generate confounder challenges
        if hypothesis_type == "causal":
            for i, var1 in enumerate(variables):
                for var2 in variables[i+1:]:
                    # Check if we've already challenged this pair
                    already_challenged = any(
                        var2 in c.description and var1 in c.description
                        for c in challenges
                    )
                    if not already_challenged:
                        challenge = AdversarialChallenge(
                            challenge_id=f"confounder_{i}_{len(challenges)}",
                            challenge_type=ChallengeType.CONFOUNDER,
                            description=f"Could {var2} be a confounder instead of a direct cause?",
                            severity="moderate",
                            confidence=0.7
                        )
                        challenges.append(challenge)

        # Generate alternative explanation challenges
        if effect_size < 0.3:
            challenge = AdversarialChallenge(
                challenge_id=f"weak_effect_{len(challenges)}",
                challenge_type=ChallengeType.ALTERNATIVE,
                description=f"Effect size ({effect_size:.3f}) is small - could this be noise?",
                severity="low",
                confidence=0.5
            )
            challenges.append(challenge)

        # Generate sample size challenges
        if sample_size < 100:
            challenge = AdversarialChallenge(
                challenge_id=f"small_sample_{len(challenges)}",
                challenge_type=ChallengeType.SELECTION,
                description=f"Small sample size (n={sample_size}) - result may not be robust",
                severity="moderate",
                confidence=0.6
            )
            challenges.append(challenge)

        return challenges


class RedTeamDiscovery:
    """
    Red Team Discovery: Systematic attempt to falsify discoveries.

    Tries to find data subsets or analysis choices that contradict claims.
    """

    def __init__(self):
        """Initialize Red Team Discovery"""

    def attempt_falsification(
        self,
        data: np.ndarray,
        variable_names: List[str],
        claim: str,
        claimed_correlation: float
    ) -> Dict[str, Any]:
        """
        Attempt to falsify a claimed correlation.

        Args:
            data: Dataset
            variable_names: Variable names
            claim: Claimed correlation
            claimed_correlation: Claimed correlation value

        Returns:
            Falsification attempt results
        """
        results = {
            'original_claim': claim,
            'claimed_correlation': claimed_correlation,
            'falsification_attempts': []
        }

        # Test 1: Subset analysis
        for i in range(min(5, data.shape[1])):
            subset = data[data[:, i] > np.median(data[:, i])]

            if len(subset) > 20:
                # Recalculate correlation
                subset_corr = np.corrcoef(subset[:, 0], subset[:, 1])[0, 1] if subset.shape[1] >= 2 else 0

                if abs(subset_corr - claimed_correlation) > 0.2:
                    results['falsification_attempts'].append({
                        'test': f'Subset analysis (variable {i} > median)',
                        'found_correlation': subset_corr,
                        'difference': abs(subset_corr - claimed_correlation),
                        'falsified': abs(subset_corr) < 0.1
                    })

        # Test 2: Outlier removal
        for i in range(data.shape[1]):
            mean = np.mean(data[:, i])
            std = np.std(data[:, i])
            clean_data = data[np.abs(data[:, i] - mean) < 3 * std]

            if len(clean_data) > 20:
                clean_corr = np.corrcoef(clean_data[:, 0], clean_data[:, 1])[0, 1] if clean_data.shape[1] >= 2 else 0

                if abs(clean_corr - claimed_correlation) > 0.1:
                    results['falsification_attempts'].append({
                        'test': f'Outlier removal (variable {i})',
                        'found_correlation': clean_corr,
                        'difference': abs(clean_corr - claimed_correlation),
                        'falsified': abs(clean_corr) < 0.1
                    })

        # Test 3: Alternative time periods (if applicable)
        if data.shape[0] > 100:
            mid_point = data.shape[0] // 2
            first_half_corr = np.corrcoef(data[:mid_point, 0], data[:mid_point, 1])[0, 1] if data.shape[1] >= 2 else 0
            second_half_corr = np.corrcoef(data[mid_point:, 0], data[mid_point:, 1])[0, 1] if data.shape[1] >= 2 else 0

            if abs(first_half_corr - second_half_corr) > 0.3:
                results['falsification_attempts'].append({
                    'test': 'Time period split',
                    'first_half_correlation': first_half_corr,
                    'second_half_correlation': second_half_corr,
                    'difference': abs(first_half_corr - second_half_corr),
                    'falsified': False
                })

        results['survived_challenges'] = len([a for a in results['falsification_attempts']
                                             if not a['falsified']]) / max(1, len(results['falsification_attempts']))

        return results


class HypothesisRefinementLoop:
    """
    Iterative refinement loop for hypotheses.

    Process:
    1. Initial discovery
    2. Adversarial challenge
    3. Refinement
    4. Re-test
    5. Iterate until convergence
    """

    def __init__(self, max_iterations: int = 5, convergence_threshold: float = 0.1):
        """
        Initialize refinement loop.

        Args:
            max_iterations: Maximum refinement iterations
            convergence_threshold: Minimum change to continue iterating
        """
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold

    def refine_hypothesis(
        self,
        initial_hypothesis: str,
        data: np.ndarray,
        variable_names: List[str],
        adversary: DevilsAdvocateAgent,
        red_team: RedTeamDiscovery
    ) -> RefinedHypothesis:
        """
        Iteratively refine hypothesis through adversarial challenge.

        Args:
            initial_hypothesis: Initial hypothesis claim
            data: Data for testing
            variable_names: Variable names
            adversary: Devil's Advocate agent
            red_team: Red Team discovery agent

        Returns:
            RefinedHypothesis with iteration history
        """
        current_hypothesis = initial_hypothesis
        all_challenges = []
        all_modifications = []

        for iteration in range(self.max_iterations):
            # Generate adversarial challenges
            challenges = adversary.generate_challenges(
                current_hypothesis,
                "causal",
                variable_names,
                effect_size=0.5,
                sample_size=len(data)
            )

            # All challenges that weren't refuted
            surviving_challenges = [c for c in challenges if not c.refuted]
            all_challenges.extend(surviving_challenges)

            # Red team falsification attempts
            falsification = red_team.attempt_falsification(
                data, variable_names, current_hypothesis, 0.5
            )

            # Determine if hypothesis survives
            survived_challenges = len(surviving_challenges)
            survived_falsification = falsification.get('survived_challenges', 0)

            # Check convergence
            if survived_challenges == 0 and survived_falsification < 0.3:
                # Hypothesis failed completely
                break

            # Refine hypothesis
            if survived_challenges > 0:
                # Add qualifiers based on challenges
                qualifiers = []
                for challenge in surviving_challenges:
                    if challenge.challenge_type == ChallengeType.CONFOUNDER:
                        qualifiers.append(f"potentially confounded by {challenge.description}")
                    elif challenge.challenge_type == ChallengeType.SELECTION:
                        qualifiers.append("may be subject to selection effects")

                if qualifiers:
                    refined = f"{current_hypothesis} ({'; '.join(qualifiers)})"
                    all_modifications.append(f"Added qualifiers: {qualifiers}")
                    current_hypothesis = refined

            # Check convergence
            if iteration > 0:
                # Count new challenges
                new_challenges = len(challenges)
                if new_challenges < self.convergence_threshold * len(all_challenges):
                    break

        # Calculate final confidence and robustness
        n_challenges = len(all_challenges)
        n_survived = len([c for c in all_challenges if not c.refuted])

        robustness_score = n_survived / n_challenges if n_challenges > 0 else 0

        final_confidence = 0.5 + 0.5 * robustness_score

        # Identify validation requirements
        validation_requirements = []
        for challenge in all_challenges:
            if challenge.challenge_type == ChallengeType.CONFOUNDER and not challenge.refuted:
                validation_requirements.append(f"test for confounding: {challenge.description}")

        if final_confidence < 0.5:
            validation_requirements.append("low confidence - requires validation")

        return RefinedHypothesis(
            original_hypothesis=initial_hypothesis,
            challenges_received=all_challenges,
            modifications_made=all_modifications,
            final_confidence=final_confidence,
            robustness_score=robustness_score,
            requires_validation=validation_requirements
        )


class AdversarialDiscoverySystem:
    """
    Complete adversarial discovery system.

    Coordinates devil's advocate, red team, and refinement loop.
    """

    def __init__(self):
        """Initialize adversarial discovery system"""
        self.advocate = DevilsAdvocateAgent()
        self.red_team = RedTeamDiscovery()
        self.refinement_loop = HypothesisRefinementLoop()

    def adversarial_discovery_process(
        self,
        initial_discovery: Dict,
        data: np.ndarray,
        variable_names: List[str]
    ) -> Dict[str, Any]:
        """
        Complete adversarial discovery process.

        Args:
            initial_discovery: Initial discovery from V97/V98
            data: Dataset
            variable_names: Variable names

        Returns:
            Complete adversarial analysis results
        """
        hypothesis = initial_discovery.get('claim', initial_discovery.get('pattern', ''))

        # Generate adversarial challenges
        challenges = self.advocate.generate_challenges(
            hypothesis,
            initial_discovery.get('type', 'correlation'),
            variable_names,
            initial_discovery.get('effect_size', 0.5),
            len(data)
        )

        # Red team falsification attempts
        falsification = self.red_team.attempt_falsification(
            data, variable_names, hypothesis,
            initial_discovery.get('correlation', 0.5)
        )

        # Refinement loop
        refined = self.refinement_loop.refine_hypothesis(
            hypothesis, data, variable_names,
            self.advocate, self.red_team
        )

        return {
            'original_hypothesis': hypothesis,
            'refined_hypothesis': refined,
            'challenges': challenges,
            'falsification': falsification,
            'adversarial_summary': self._generate_summary(refined, challenges, falsification)
        }

    def _generate_summary(
        self,
        refined: RefinedHypothesis,
        challenges: List[AdversarialChallenge],
        falsification: Dict
    ) -> str:
        """Generate summary of adversarial analysis"""
        lines = []
        lines.append("=== ADVERSARIAL ANALYSIS SUMMARY ===\n")
        lines.append(f"Original Hypothesis: {refined.original_hypothesis}\n")

        lines.append(f"Challenges Received: {len(challenges)}")
        for challenge in challenges[:5]:  # Show first 5
            lines.append(f"  - {challenge.challenge_type.value}: {challenge.description}")

        lines.append(f"\nHypothesis Survived: {len([c for c in challenges if not c.refuted])}/{len(challenges)}")
        lines.append(f"Robustness Score: {refined.robustness_score:.2f}")
        lines.append(f"Final Confidence: {refined.final_confidence:.2f}")

        if refined.requires_validation:
            lines.append(f"\nRequires Validation:")
            for req in refined.requires_validation:
                lines.append(f"  - {req}")

        return "\n".join(lines)


# Factory functions

def create_adversarial_discovery_system() -> AdversarialDiscoverySystem:
    """Factory function to create AdversarialDiscoverySystem"""
    return AdversarialDiscoverySystem()


def create_devils_advocate() -> DevilsAdvocateAgent:
    """Factory function to create DevilsAdvocateAgent"""
    return DevilsAdvocateAgent()


def create_red_team_discovery() -> RedTeamDiscovery:
    """Factory function to create RedTeamDiscovery"""
    return RedTeamDiscovery()


# Convenience function

def adversarially_validate_discovery(
    discovery_claim: str,
    discovery_data: np.ndarray,
    variable_names: List[str],
    effect_size: float = 0.5
) -> Dict[str, Any]:
    """
    Apply adversarial validation to a discovery claim.

    Args:
        discovery_claim: Claim to validate
        discovery_data: Data supporting the claim
        variable_names: Variable names
        effect_size: Effect size

    Returns:
        Complete adversarial validation results
    """
    system = create_adversarial_discovery_system()

    initial_discovery = {
        'claim': discovery_claim,
        'type': 'correlation',
        'effect_size': effect_size
    }

    return system.adversarial_discovery_process(
        initial_discovery,
        discovery_data,
        variable_names
    )


# Compatibility aliases for common naming patterns
AdversarialHypothesisFramework = AdversarialDiscoverySystem
