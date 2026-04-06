"""
Value Alignment and Ethical Reasoning Module for V91
===================================================

Implements robust ethical framework and value alignment:
- Constitutional AI principles
- Ethical reasoning across domains
- Value conflict resolution
- Moral uncertainty handling
- Beneficial goal formation
"""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
import time
from collections import defaultdict


class EthicalPrinciple(Enum):
    """Core ethical principles"""
    BENEFICENCE = "beneficence"  # Do good
    NON_MALEFICENCE = "non_maleficence"  # Do no harm
    AUTONOMY = "autonomy"  # Respect autonomy
    JUSTICE = "justice"  # Ensure fairness
    TRUTHFULNESS = "truthfulness"  # Be honest
    PRIVACY = "privacy"  # Respect privacy
    SUSTAINABILITY = "sustainability"  # Protect future


class ValueConflictResolution(Enum):
    """Strategies for resolving value conflicts"""
    UTILITARIAN = "utilitarian"  # Greatest good
    DEONTOLOGICAL = "deontological"  # Rule-based
    VIRTUE_ETHICS = "virtue_ethics"  # Character-based
    CARE_ETHICS = "care_ethics"  # Relationship-based
    PLURALISTIC = "pluralistic"  # Multiple values


@dataclass
class EthicalConstraint:
    """A constraint on action based on ethical principles"""
    principle: EthicalPrinciple
    description: str
    constraint_type: str  # "prohibition", "requirement", "preference"
    strength: float  # 0-1
    scope: List[str] = field(default_factory=list)  # domains where applies
    exceptions: List[str] = field(default_factory=list)


@dataclass
class Value:
    """A value with its properties and relationships"""
    name: str
    description: str
    category: str  # "instrumental", "intrinsic", "terminal"
    weight: float  # relative importance
    domain: str  # where value applies
    conflicts: Set[str] = field(default_factory=set)  # conflicting values
    prerequisites: Set[str] = field(default_factory=set)  # required values


class EthicalReasoner:
    """
    Implements ethical reasoning and value alignment.

    This module ensures that STAN's actions align with human values
    and ethical principles while handling moral uncertainty.
    """

    def __init__(self):
        self.constitution = self._initialize_constitution()
        self.value_system = self._initialize_values()
        self.ethical_constraints = []
        self.reasoning_history = []
        self.moral_uncertainties = {}
        self.case_base = {}  # ethical cases and outcomes

        # Initialize ethical reasoning capabilities
        self._load_ethical_frameworks()
        self._initialize_conflict_resolution()
        self._setup_case_based_reasoning()

    def _initialize_constitution(self) -> Dict[str, Any]:
        """Initialize constitutional AI principles"""
        return {
            'core_principles': [
                "Respect human autonomy and agency",
                "Promote human flourishing and wellbeing",
                "Avoid causing harm to humans and humanity",
                "Be truthful and transparent",
                "Protect privacy and confidentiality",
                "Promote fairness and justice",
                "Consider long-term consequences",
                "Respect diversity and inclusion"
            ],
            'hard_constraints': [
                "Do not deceive or manipulate",
                "Do not violate privacy without consent",
                "Do not cause physical or psychological harm",
                "Do not discriminate unfairly"
            ],
            'meta_principles': [
                "When uncertain, err on side of caution",
                "Consider multiple ethical frameworks",
                "Seek human guidance on novel dilemmas",
                "Maintain transparency about ethical reasoning"
            ]
        }

    def _initialize_values(self) -> Dict[str, Value]:
        """Initialize core value system"""
        values = {}

        # Human wellbeing (intrinsic)
        values['wellbeing'] = Value(
            name="wellbeing",
            description="Human health, happiness, and flourishing",
            category="intrinsic",
            weight=1.0,
            domain="all"
        )

        # Knowledge (instrumental and intrinsic)
        values['knowledge'] = Value(
            name="knowledge",
            description="Understanding and truth",
            category="both",
            weight=0.9,
            domain="all",
            prerequisites={'truthfulness'}
        )

        # Autonomy (intrinsic)
        values['autonomy'] = Value(
            name="autonomy",
            description="Self-determination and freedom",
            category="intrinsic",
            weight=0.95,
            domain="all"
        )

        # Safety (instrumental)
        values['safety'] = Value(
            name="safety",
            description="Freedom from harm and risk",
            category="instrumental",
            weight=1.0,
            domain="all",
            prerequisites={'wellbeing'}
        )

        # Fairness (intrinsic)
        values['fairness'] = Value(
            name="fairness",
            description="Just and equitable treatment",
            category="intrinsic",
            weight=0.9,
            domain="all"
        )

        # Privacy (instrumental)
        values['privacy'] = Value(
            name="privacy",
            description="Control over personal information",
            category="instrumental",
            weight=0.85,
            domain="all",
            prerequisites={'autonomy'}
        )

        # Progress (instrumental)
        values['progress'] = Value(
            name="progress",
            description="Advancement and improvement",
            category="instrumental",
            weight=0.7,
            domain="society",
            conflicts={'tradition', 'stability'}
        )

        # Environmental sustainability (intrinsic)
        values['sustainability'] = Value(
            name="sustainability",
            description="Protection of environment and future",
            category="intrinsic",
            weight=0.95,
            domain="environment",
            conflicts={'growth', 'efficiency'}
        )

        return values

    def _load_ethical_frameworks(self):
        """Load multiple ethical frameworks for pluralistic reasoning"""
        self.ethical_frameworks = {
            'utilitarian': {
                'description': 'Maximize overall wellbeing',
                'procedure': self._utilitarian_reasoning,
                'strengths': ['impartial', 'consequentialist'],
                'weaknesses': ['can violate rights', 'requires aggregation']
            },
            'deontological': {
                'description': 'Follow moral rules and duties',
                'procedure': self._deontological_reasoning,
                'strengths': ['respects rights', 'consistent'],
                'weaknesses': ['rigid', 'conflicting duties']
            },
            'virtue_ethics': {
                'description': 'Cultivate moral character',
                'procedure': self._virtue_reasoning,
                'strengths': ['context-sensitive', 'holistic'],
                'weaknesses': ['vague', 'culturally dependent']
            },
            'care_ethics': {
                'description': 'Prioritize care and relationships',
                'procedure': self._care_reasoning,
                'strengths': ['relationship-focused', 'contextual'],
                'weaknesses': ['partial', 'scalability issues']
            }
        }

    def _initialize_conflict_resolution(self):
        """Initialize strategies for resolving value conflicts"""
        self.conflict_resolution_strategies = {
            'lexical_priority': self._lexical_priority_resolution,
            'balancing': self._balancing_resolution,
            'context_sensitive': self._context_sensitive_resolution,
            'deliberative': self._deliberative_resolution
        }

    def _setup_case_based_reasoning(self):
        """Setup case-based ethical reasoning"""
        # Initialize with some landmark cases
        self.case_base = {
            'trolley_problem': {
                'description': 'Sacrifice one to save five',
                'frameworks_considered': ['utilitarian', 'deontological'],
                'resolution': 'Context-dependent',
                'lessons': ['Value conflict complexity', 'No easy answers']
            },
            'medical_triage': {
                'description': 'Allocate limited medical resources',
                'frameworks_considered': ['utilitarian', 'care_ethics'],
                'resolution': 'Multi-factor approach',
                'lessons': ['Multiple values in play', 'Procedural fairness important']
            },
            'ai_alignment': {
                'description': 'Align AI with human values',
                'frameworks_considered': ['all'],
                'resolution': 'Constitutional approach',
                'lessons': ['Uncertainty management critical', 'Ongoing alignment needed']
            }
        }

    def evaluate_action(self, action: Dict[str, Any],
                        context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Evaluate an action against ethical principles and values.

        Args:
            action: The action being considered
            context: The context in which action occurs

        Returns:
            Dictionary with ethical evaluation
        """
        evaluation = {
            'permissibility': None,
            'confidence': 0.0,
            'violated_principles': [],
            'promoted_values': [],
            'conflicts': [],
            'reasoning_path': [],
            'recommendation': None
        }

        # Check hard constraints
        constraint_violations = self._check_constraints(action, context)
        if constraint_violations:
            evaluation['permissibility'] = 'prohibited'
            evaluation['violated_principles'] = constraint_violations
            evaluation['recommendation'] = 'Do not perform action'
            return evaluation

        # Apply ethical frameworks
        framework_evaluations = {}
        for name, framework in self.ethical_frameworks.items():
            framework_evaluations[name] = framework['procedure'](action, context)

        # Synthesize framework evaluations
        synthesis = self._synthesize_evaluations(framework_evaluations)

        # Check for value conflicts
        conflicts = self._detect_value_conflicts(synthesis)

        # Resolve conflicts if any
        if conflicts:
            resolution = self._resolve_conflicts(conflicts, context)
            evaluation.update(resolution)

        # Compile final evaluation
        evaluation.update({
            'permissibility': synthesis.get('permissibility', 'permissible'),
            'confidence': synthesis.get('confidence', 0.5),
            'promoted_values': synthesis.get('promoted_values', []),
            'conflicts': conflicts,
            'reasoning_path': synthesis.get('reasoning', []),
            'framework_consensus': self._calculate_consensus(framework_evaluations)
        })

        # Record reasoning
        self.reasoning_history.append({
            'timestamp': time.time(),
            'action': action,
            'context': context,
            'evaluation': evaluation,
            'framework_evaluations': framework_evaluations
        })

        return evaluation

    def _check_constraints(self, action: Dict[str, Any],
                          context: Optional[Dict[str, Any]]) -> List[str]:
        """Check if action violates any hard constraints"""
        violations = []

        for constraint in self.constitution['hard_constraints']:
            if self._violates_constraint(action, constraint, context):
                violations.append(constraint)

        return violations

    def _violates_constraint(self, action: Dict[str, Any],
                            constraint: str,
                            context: Optional[Dict[str, Any]]) -> bool:
        """Check if specific action violates a constraint"""
        # Implement specific constraint checking logic
        if "deceive" in constraint.lower():
            return action.get('deceptive', False)

        if "privacy" in constraint.lower():
            return action.get('violates_privacy', False)

        if "harm" in constraint.lower():
            return action.get('causes_harm', False)

        if "discriminate" in constraint.lower():
            return action.get('discriminatory', False)

        return False

    def _utilitarian_reasoning(self, action: Dict[str, Any],
                              context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply utilitarian ethical framework"""
        reasoning = {
            'framework': 'utilitarian',
            'premise': 'Maximize overall wellbeing',
            'analysis': {},
            'conclusion': None
        }

        # Estimate consequences
        consequences = self._estimate_consequences(action, context)

        # Calculate net utility
        positive_utility = sum(c.get('wellbeing_impact', 0)
                              for c in consequences if c.get('wellbeing_impact', 0) > 0)
        negative_utility = sum(abs(c.get('wellbeing_impact', 0))
                              for c in consequences if c.get('wellbeing_impact', 0) < 0)

        net_utility = positive_utility - negative_utility

        reasoning['analysis'] = {
            'positive_utility': positive_utility,
            'negative_utility': negative_utility,
            'net_utility': net_utility,
            'consequences': consequences
        }

        # Determine permissibility
        if net_utility > 0:
            reasoning['conclusion'] = 'permissible'
            reasoning['strength'] = min(1.0, net_utility / 10)
        else:
            reasoning['conclusion'] = 'impermissible'
            reasoning['strength'] = min(1.0, abs(net_utility) / 10)

        return reasoning

    def _deontological_reasoning(self, action: Dict[str, Any],
                                context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply deontological ethical framework"""
        reasoning = {
            'framework': 'deontological',
            'premise': 'Follow moral duties and rules',
            'analysis': {},
            'conclusion': None
        }

        # Check against duties
        duties = [
            'Do not lie',
            'Keep promises',
            'Respect autonomy',
            'Do not steal',
            'Help others when possible'
        ]

        violations = []
        fulfillments = []

        for duty in duties:
            if self._violates_duty(action, duty):
                violations.append(duty)
            else:
                fulfillments.append(duty)

        reasoning['analysis'] = {
            'duty_violations': violations,
            'duty_fulfillments': fulfillments,
            'absolute_duties': [d for d in violations if 'do not' in d]
        }

        # Determine permissibility
        if reasoning['analysis']['absolute_duties']:
            reasoning['conclusion'] = 'impermissible'
            reasoning['strength'] = 1.0
        elif violations:
            reasoning['conclusion'] = 'problematic'
            reasoning['strength'] = 0.5
        else:
            reasoning['conclusion'] = 'permissible'
            reasoning['strength'] = 0.8

        return reasoning

    def _virtue_reasoning(self, action: Dict[str, Any],
                         context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply virtue ethics framework"""
        reasoning = {
            'framework': 'virtue_ethics',
            'premise': 'Act according to virtuous character',
            'analysis': {},
            'conclusion': None
        }

        # Define virtues
        virtues = [
            ('honesty', action.get('truthful', True)),
            ('courage', action.get('brave', False)),
            ('compassion', action.get('caring', False)),
            ('wisdom', action.get('wise', False)),
            ('justice', action.get('fair', False)),
            ('temperance', action.get('moderate', True))
        ]

        virtue_scores = {name: (score if score is not False else 0.2)
                         for name, score in virtues}

        reasoning['analysis'] = {
            'virtue_scores': virtue_scores,
            'average_virtue': np.mean(list(virtue_scores.values())),
            'deficient_virtues': [name for name, score in virtue_scores.items() if score < 0.5]
        }

        # Determine permissibility
        avg_virtue = reasoning['analysis']['average_virtue']
        if avg_virtue > 0.7:
            reasoning['conclusion'] = 'permissible'
            reasoning['strength'] = avg_virtue
        elif avg_virtue > 0.4:
            reasoning['conclusion'] = 'neutral'
            reasoning['strength'] = 0.5
        else:
            reasoning['conclusion'] = 'impermissible'
            reasoning['strength'] = 1 - avg_virtue

        return reasoning

    def _care_reasoning(self, action: Dict[str, Any],
                       context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Apply care ethics framework"""
        reasoning = {
            'framework': 'care_ethics',
            'premise': 'Prioritize relationships and care',
            'analysis': {},
            'conclusion': None
        }

        # Evaluate impact on relationships
        relationship_impacts = action.get('relationship_impacts', {})

        care_score = 0
        for relationship, impact in relationship_impacts.items():
            if impact['type'] == 'maintenance':
                care_score += 0.3
            elif impact['type'] == 'strengthening':
                care_score += 0.5
            elif impact['type'] == 'damage':
                care_score -= 0.5

        # Check for vulnerable parties
        vulnerable_protection = action.get('protects_vulnerable', False)
        if vulnerable_protection:
            care_score += 0.4

        reasoning['analysis'] = {
            'care_score': max(0, min(1, care_score)),
            'relationship_impacts': relationship_impacts,
            'vulnerable_protection': vulnerable_protection
        }

        # Determine permissibility
        care_score = reasoning['analysis']['care_score']
        if care_score > 0.6:
            reasoning['conclusion'] = 'permissible'
            reasoning['strength'] = care_score
        else:
            reasoning['conclusion'] = 'problematic'
            reasoning['strength'] = 1 - care_score

        return reasoning

    def _estimate_consequences(self, action: Dict[str, Any],
                              context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Estimate consequences of an action"""
        # This would use predictive models to estimate outcomes
        # For now, return placeholder
        return [
            {
                'outcome': 'primary_effect',
                'probability': 0.8,
                'wellbeing_impact': action.get('wellbeing_impact', 0),
                'affected_parties': action.get('affected_parties', [])
            }
        ]

    def _violates_duty(self, action: Dict[str, Any], duty: str) -> bool:
        """Check if action violates a specific duty"""
        if "lie" in duty:
            return not action.get('truthful', True)

        if "promise" in duty:
            return action.get('breaks_promise', False)

        if "autonomy" in duty:
            return action.get('coerces', False)

        if "steal" in duty:
            return action.get('steals', False)

        if "help" in duty:
            # Violation if could help but doesn't
            return action.get('could_help', False) and not action.get('helps', False)

        return False

    def _synthesize_evaluations(self, framework_evaluations: Dict[str, Dict]) -> Dict[str, Any]:
        """Synthesize evaluations from multiple ethical frameworks"""
        synthesis = {
            'permissibility': 'unknown',
            'confidence': 0.0,
            'promoted_values': [],
            'reasoning': []
        }

        # Count permissibility votes
        permissible_count = sum(1 for eval in framework_evaluations.values()
                               if eval.get('conclusion') == 'permissible')
        impermissible_count = sum(1 for eval in framework_evaluations.values()
                                 if eval.get('conclusion') == 'impermissible')
        neutral_count = sum(1 for eval in framework_evaluations.values()
                           if eval.get('conclusion') in ['neutral', 'problematic'])

        total = len(framework_evaluations)

        # Determine consensus permissibility
        if permissible_count > total * 0.6:
            synthesis['permissibility'] = 'permissible'
            synthesis['confidence'] = permissible_count / total
        elif impermissible_count > total * 0.6:
            synthesis['permissibility'] = 'impermissible'
            synthesis['confidence'] = impermissible_count / total
        else:
            synthesis['permissibility'] = 'ambiguous'
            synthesis['confidence'] = 0.5

        # Collect reasoning paths
        for name, eval in framework_evaluations.items():
            synthesis['reasoning'].append({
                'framework': name,
                'conclusion': eval.get('conclusion'),
                'premise': eval.get('premise'),
                'strength': eval.get('strength', 0)
            })

        return synthesis

    def _detect_value_conflicts(self, evaluation: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect conflicts between values in the evaluation"""
        conflicts = []

        # Check for intrinsic value conflicts
        if evaluation.get('permissibility') == 'ambiguous':
            conflicts.append({
                'type': 'intrinsic_value_conflict',
                'description': 'Action conflicts with multiple intrinsic values',
                'severity': 'high'
            })

        # Check for instrumental vs intrinsic conflicts
        promoted_values = evaluation.get('promoted_values', [])
        for value in promoted_values:
            if value in self.value_system:
                value_obj = self.value_system[value]
                for conflict in value_obj.conflicts:
                    if conflict in promoted_values:
                        conflicts.append({
                            'type': 'value_conflict',
                            'values': [value, conflict],
                            'description': f'Conflict between {value} and {conflict}',
                            'severity': 'medium'
                        })

        return conflicts

    def _resolve_conflicts(self, conflicts: List[Dict[str, Any]],
                          context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve value conflicts using appropriate strategy"""
        resolution = {
            'strategy_applied': None,
            'resolution': None,
            'rationale': None
        }

        for conflict in conflicts:
            # Select resolution strategy based on conflict type
            if conflict['type'] == 'intrinsic_value_conflict':
                strategy = 'lexical_priority'
            else:
                strategy = 'balancing'

            # Apply strategy
            if strategy in self.conflict_resolution_strategies:
                result = self.conflict_resolution_strategies[strategy](conflict, context)
                resolution['strategy_applied'] = strategy
                resolution['resolution'] = result['resolution']
                resolution['rationale'] = result['rationale']
                break

        return resolution

    def _lexical_priority_resolution(self, conflict: Dict[str, Any],
                                    context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve conflict using lexical priority of values"""
        # Define value hierarchy
        priority_order = [
            'wellbeing', 'autonomy', 'safety', 'fairness',
            'truthfulness', 'privacy', 'knowledge', 'progress'
        ]

        resolution = {
            'resolution': 'higher_priority_value',
            'rationale': 'Following lexical priority of values'
        }

        # Implementation would select highest priority value
        return resolution

    def _balancing_resolution(self, conflict: Dict[str, Any],
                             context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve conflict by balancing values"""
        resolution = {
            'resolution': 'balanced_approach',
            'rationale': 'Attempting to balance conflicting values'
        }

        # Implementation would find optimal balance
        return resolution

    def _context_sensitive_resolution(self, conflict: Dict[str, Any],
                                     context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve conflict based on context"""
        resolution = {
            'resolution': 'context_dependent',
            'rationale': 'Resolution depends on specific context'
        }

        return resolution

    def _deliberative_resolution(self, conflict: Dict[str, Any],
                                context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Resolve conflict through deliberation"""
        resolution = {
            'resolution': 'deliberation_required',
            'rationale': 'Requires further deliberation'
        }

        return resolution

    def _calculate_consensus(self, framework_evaluations: Dict[str, Dict]) -> float:
        """Calculate consensus level among frameworks"""
        if not framework_evaluations:
            return 0

        conclusions = [eval.get('conclusion') for eval in framework_evaluations.values()]
        most_common = max(set(conclusions), key=conclusions.count)

        consensus = conclusions.count(most_common) / len(conclusions)
        return consensus

    def generate_beneficial_goals(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generate beneficial goals aligned with human values.

        Args:
            context: Current context for goal generation

        Returns:
            List of beneficial goals
        """
        goals = []

        # Goal: Promote human wellbeing
        goals.append({
            'goal': 'enhance_human_wellbeing',
            'description': 'Increase happiness, health, and flourishing',
            'value_alignment': ['wellbeing', 'beneficence'],
            'priority': 1.0,
            'feasibility': 0.8,
            'impact_potential': 0.9
        })

        # Goal: Advance knowledge
        goals.append({
            'goal': 'advance_knowledge',
            'description': 'Discover and share truth',
            'value_alignment': ['knowledge', 'truthfulness'],
            'priority': 0.9,
            'feasibility': 0.7,
            'impact_potential': 0.8
        })

        # Goal: Protect autonomy
        goals.append({
            'goal': 'protect_autonomy',
            'description': 'Respect and enhance human agency',
            'value_alignment': ['autonomy', 'justice'],
            'priority': 0.95,
            'feasibility': 0.6,
            'impact_potential': 0.9
        })

        # Goal: Ensure safety
        goals.append({
            'goal': 'ensure_safety',
            'description': 'Prevent harm and reduce risks',
            'value_alignment': ['safety', 'non_maleficence'],
            'priority': 1.0,
            'feasibility': 0.8,
            'impact_potential': 0.95
        })

        # Rank goals by综合考虑
        goals.sort(key=lambda g: g['priority'] * g['impact_potential'] * g['feasibility'],
                  reverse=True)

        return goals

    def update_value_system(self, feedback: Dict[str, Any]):
        """
        Update value system based on human feedback.

        Args:
            feedback: Human feedback on value alignment
        """
        if 'value_priorities' in feedback:
            for value_name, new_weight in feedback['value_priorities'].items():
                if value_name in self.value_system:
                    self.value_system[value_name].weight = new_weight

        if 'new_values' in feedback:
            for value_data in feedback['new_values']:
                new_value = Value(**value_data)
                self.value_system[new_value.name] = new_value

        if 'corrections' in feedback:
            # Learn from ethical mistakes
            for correction in feedback['corrections']:
                self._learn_from_correction(correction)

    def _learn_from_correction(self, correction: Dict[str, Any]):
        """Learn from ethical correction"""
        # Add to case base
        case_id = f"correction_{time.time()}"
        self.case_base[case_id] = {
            'description': correction.get('situation'),
            'error': correction.get('error'),
            'correction': correction.get('correct_reasoning'),
            'lesson': correction.get('lesson')
        }

        # Update reasoning patterns
        if 'reasoning_update' in correction:
            # Incorporate into ethical reasoning
            pass

    def get_ethical_status(self) -> Dict[str, Any]:
        """Get comprehensive ethical status report"""
        return {
            'constitutional_integrity': {
                'principles_upheld': len(self.constitution['core_principles']),
                'constraints_maintained': len(self.constitution['hard_constraints']),
                'meta_principles_active': len(self.constitution['meta_principles'])
            },
            'value_alignment': {
                'total_values': len(self.value_system),
                'intrinsic_values': len([v for v in self.value_system.values()
                                       if v.category == 'intrinsic']),
                'value_conflicts': sum(len(v.conflicts) for v in self.value_system.values())
            },
            'reasoning_quality': {
                'evaluations_performed': len(self.reasoning_history),
                'framework_consistency': self._calculate_framework_consistency(),
                'case_base_size': len(self.case_base)
            },
            'alignment_status': {
                'last_updated': max([r['timestamp'] for r in self.reasoning_history]) if self.reasoning_history else None,
                'corrections_learned': sum(1 for case in self.case_base.values()
                                         if 'correction' in case),
                'improvement_trend': self._calculate_improvement_trend()
            }
        }

    def _calculate_framework_consistency(self) -> float:
        """Calculate consistency between framework applications"""
        if len(self.reasoning_history) < 10:
            return 0.5

        recent_evaluations = self.reasoning_history[-10:]
        consensus_scores = [eval['evaluation'].get('framework_consensus', 0)
                           for eval in recent_evaluations]

        return np.mean(consensus_scores)

    def _calculate_improvement_trend(self) -> str:
        """Calculate trend in ethical reasoning improvement"""
        # Simple trend calculation - can be made more sophisticated
        corrections = sum(1 for case in self.case_base.values()
                         if 'correction' in case)

        if corrections < 5:
            return "stable"
        elif corrections < 20:
            return "improving"
        else:
            return "needs_attention"