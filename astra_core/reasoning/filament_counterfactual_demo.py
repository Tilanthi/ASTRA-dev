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
Counterfactual Reasoning for Filament Width Analysis

This module implements the counterfactual reasoning test for the
Arzoumanian et al. (2011) filament width result.

Date: 2025-12-11
Version: 1.0
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from typing import Dict, Any, List, Optional

# Import from unified_world_model using absolute path
import importlib.util
spec = importlib.util.spec_from_file_location(
    "unified_world_model",
    os.path.join(os.path.dirname(__file__), "unified_world_model.py")
)
unified_world_model = importlib.util.module_from_spec(spec)
sys.modules["unified_world_model"] = unified_world_model
spec.loader.exec_module(unified_world_model)

get_world_model = unified_world_model.get_world_model
UnifiedWorldModel = unified_world_model.UnifiedWorldModel
CausalGraph = unified_world_model.CausalGraph
CausalEdge = unified_world_model.CausalEdge
Hypothesis = unified_world_model.Hypothesis
Belief = unified_world_model.Belief
BeliefType = unified_world_model.BeliefType

# Import integration bus stub
spec2 = importlib.util.spec_from_file_location(
    "integration_bus_stub",
    os.path.join(os.path.dirname(__file__), "integration_bus_stub.py")
)
integration_bus_stub = importlib.util.module_from_spec(spec2)
sys.modules["integration_bus_stub"] = integration_bus_stub
spec2.loader.exec_module(integration_bus_stub)

IntegrationBus = integration_bus_stub.IntegrationBus
EventType = integration_bus_stub.EventType
get_integration_bus = integration_bus_stub.get_integration_bus

# Import counterfactual reasoning
spec3 = importlib.util.spec_from_file_location(
    "counterfactual_reasoning",
    os.path.join(os.path.dirname(__file__), "counterfactual_reasoning.py")
)
counterfactual_reasoning = importlib.util.module_from_spec(spec3)
sys.modules["counterfactual_reasoning"] = counterfactual_reasoning
spec3.loader.exec_module(counterfactual_reasoning)

CounterfactualEngine = counterfactual_reasoning.CounterfactualEngine
CounterfactualQuery = counterfactual_reasoning.CounterfactualQuery
Intervention = counterfactual_reasoning.Intervention
InterventionType = counterfactual_reasoning.InterventionType
QueryType = counterfactual_reasoning.QueryType
CounterfactualResult = counterfactual_reasoning.CounterfactualResult


class CounterfactualReasoning:
    """
    High-level interface for counterfactual reasoning.

    This wrapper class provides a simple interface for asking
    counterfactual questions about astrophysical phenomena.
    """

    def __init__(self):
        self.world_model = get_world_model()
        self.bus = get_integration_bus()
        self.engine = CounterfactualEngine(self.world_model, self.bus)

        # Initialize filament-specific knowledge if not present
        self._initialize_filament_knowledge()

    def _initialize_filament_knowledge(self):
        """Initialize world model with filament-specific causal knowledge"""
        # Check if already initialized
        existing_hyp = self.world_model.get_hypothesis("arzoumanian_2011_filament_width")
        if existing_hyp:
            return

        # Add causal knowledge about filament formation
        causal_knowledge = [
            CausalEdge(
                source="turbulent_velocity_dispersion",
                target="filament_width",
                causal_strength=0.8,
                mechanism="turbulent_cascade",
                confidence=0.9
            ),
            CausalEdge(
                source="magnetic_field_strength",
                target="filament_width",
                causal_strength=0.6,
                mechanism="magnetic_support",
                confidence=0.85
            ),
            CausalEdge(
                source="thermal_pressure",
                target="filament_width",
                causal_strength=0.5,
                mechanism="jeans_instability",
                confidence=0.95
            ),
            CausalEdge(
                source="sonic_scale",
                target="filament_width",
                causal_strength=0.9,
                mechanism="characteristic_scale_formation",
                confidence=0.92
            ),
        ]

        for edge in causal_knowledge:
            self.world_model.causal_graph.add_edge(edge)

        # Add key hypothesis
        hypothesis = Hypothesis(
            hypothesis_id="arzoumanian_2011_filament_width",
            statement="Interstellar filaments have a characteristic width of ~0.1 pc corresponding to the sonic scale of turbulence",
            confidence=0.92,
            status="active",
            evidence=[],
            tags=["filaments", "turbulence", "sonic_scale"],
            metadata={
                "reference": "Arzoumanian et al. 2011, A&A 529, A6",
                "observed_width_pc": 0.1,
                "interpretation": "sonic_scale",
                "environments": ["Aquila", "Polynes", "Taurus", "Ophiuchus"]
            }
        )

        self.world_model.add_hypothesis(hypothesis)

    def analyze_counterfactual(self, query_text: str) -> str:
        """
        Analyze a counterfactual question about filament physics.

        Args:
            query_text: Natural language query about counterfactual scenario

        Returns:
            Detailed analysis with alternative scenarios and observational tests
        """
        # Parse the query to extract key elements
        query_info = self._parse_counterfactual_query(query_text)

        # Build factual world (what actually exists)
        factual_world = {
            "filament_width": 0.1,  # pc
            "turbulent_velocity_dispersion": 0.3,  # km/s (sonic scale)
            "magnetic_field_strength": 10.0,  # microGauss
            "thermal_pressure": 5.0e4,  # K cm^-3
            "sonic_scale": 0.1,  # pc
            "turbulent_injection_scale": 10.0,  # pc
        }

        results = []

        # Analyze each counterfactual scenario
        for scenario in query_info['scenarios']:
            scenario_name = scenario['name']
            intervention = scenario['intervention']

            # Create counterfactual query
            cf_query = CounterfactualQuery(
                query_id=f"filament_{scenario_name}",
                factual_world=factual_world,
                hypothetical_intervention=intervention,
                target_variable="filament_width"
            )

            # Run counterfactual reasoning
            try:
                result = self.engine.query_counterfactual(cf_query)
                results.append(self._format_result(scenario_name, result, scenario))
            except Exception as e:
                results.append(f"**Error analyzing {scenario_name}:** {str(e)}")

        # Combine results into comprehensive answer
        answer = self._generate_comprehensive_answer(query_info, results)

        return answer

    def _parse_counterfactual_query(self, query_text: str) -> Dict[str, Any]:
        """Parse natural language query into structured format"""
        query_lower = query_text.lower()

        # Identify what type of counterfactual is being asked
        scenarios = []

        # Scenario 1: No characteristic scale (broad distribution)
        if "not have a characteristic width" in query_lower or "broad distribution" in query_lower:
            scenarios.append({
                'name': 'no_characteristic_scale',
                'description': 'Filaments have a broad distribution of widths rather than a narrow peak at 0.1 pc',
                'intervention': Intervention(
                    variable="sonic_scale",
                    value=None,  # No characteristic scale
                    intervention_type=InterventionType.COUNTERFACTUAL
                ),
                'physical_conditions': {
                    'turbulence': 'No clear sonic scale - turbulent cascade lacks characteristic transition',
                    'magnetic_fields': 'Magnetic pressure dominates over thermal pressure',
                }
            })

        # Scenario 2: Strong magnetic fields
        if "magnetic" in query_lower:
            scenarios.append({
                'name': 'strong_magnetic_fields',
                'description': 'Strong magnetic fields suppress characteristic scale formation',
                'intervention': Intervention(
                    variable="magnetic_field_strength",
                    value=100.0,  # 10x stronger
                    intervention_type=InterventionType.DO
                ),
                'physical_conditions': {
                    'magnetic_field_strength': '100 microGauss (super-Alfvenic)',
                    'alfven_velocity': '> turbulent velocity',
                    'mechanism': 'Magnetic support prevents preferential scale formation'
                }
            })

        # Scenario 3: Different turbulent regime
        if "turbulent" in query_lower:
            scenarios.append({
                'name': 'different_turbulent_regime',
                'description': 'Turbulence lacks sonic scale transition',
                'intervention': Intervention(
                    variable="turbulent_velocity_dispersion",
                    value=2.0,  # Much higher dispersion
                    intervention_type=InterventionType.DO
                ),
                'physical_conditions': {
                    'mach_number': 'Highly supersonic (Mach > 3)',
                    'injection_scale': 'Much larger or smaller',
                    'mechanism': 'Turbulent cascade lacks characteristic transition scale'
                }
            })

        return {
            'original_query': query_text,
            'scenarios': scenarios
        }

    def _format_result(self, scenario_name: str, result: CounterfactualResult, scenario: Dict[str, Any]) -> str:
        """Format counterfactual result for display"""
        output = f"""
## {scenario_name.replace('_', ' ').title()}

**Scenario Description:** {scenario['description']}

**Counterfactual Analysis:**

**Factual World (What exists):**
- Filament width: {result.factual_outcome} pc (narrow peak at characteristic scale)

**Counterfactual World (What would happen):**
- Filament width distribution: {result.counterfactual_outcome}
- Confidence: {result.confidence:.1%}

**Physical Conditions Required:**
"""
        for param, value in scenario.get('physical_conditions', {}).items():
            output += f"- {param.replace('_', ' ').title()}: {value}\n"

        output += f"""
**Causal Mechanism:**
- {result.explanation}

**Observational Tests to Distinguish:**
"""
        # Add specific observational predictions
        tests = self._generate_observational_tests(scenario_name, scenario)
        for test in tests:
            output += f"- {test}\n"

        return output

    def _generate_observational_tests(self, scenario_name: str, scenario: Dict[str, Any]) -> List[str]:
        """Generate specific observational tests to distinguish scenarios"""
        tests = []

        if scenario_name == 'no_characteristic_scale':
            tests.append(
                "Measure filament width distribution in multiple clouds: "
                "look for power-law distribution rather than log-normal peak"
            )
            tests.append(
                "Search for correlation between filament width and local "
                "environmental properties (density, temperature, velocity dispersion)"
            )

        elif scenario_name == 'strong_magnetic_fields':
            tests.append(
                "Measure magnetic field strength via dust polarization or "
                "Zeeman effect: fields > 50 microGauss would support this scenario"
            )
            tests.append(
                "Compare filament widths in regions with different magnetic "
                "field strengths: stronger fields should have broader width distributions"
            )

        elif scenario_name == 'different_turbulent_regime':
            tests.append(
                "Measure turbulent velocity dispersion: if highly supersonic "
                "(Mach > 3), characteristic scale may be absent"
            )
            tests.append(
                "Analyze filament widths in clouds with different turbulent "
                "drivers (supernovae vs. stellar winds vs. galactic shear)"
            )

        return tests

    def _generate_comprehensive_answer(self, query_info: Dict[str, Any], results: List[str]) -> str:
        """Generate comprehensive answer combining all scenarios"""
        answer = """
# Counterfactual Analysis: Arzoumanian et al. (2011) Filament Width Result

## Original Result

Arzoumanian et al. (2011) used Herschel observations to show that interstellar
filaments in molecular clouds have a characteristic width of approximately 0.1 pc
across diverse environments. This has been interpreted as evidence for a universal
scale in filament formation, likely related to the sonic scale of interstellar
turbulence where the turbulent velocity dispersion equals the thermal sound speed.

## Counterfactual Question

**Query:** {query}

## Counterfactual Analysis

Below are alternative physical scenarios that would eliminate or significantly
modify the characteristic 0.1 pc scale, along with observational tests that could
distinguish these scenarios from the standard model.

---

{results}

---

## Summary

The characteristic 0.1 pc filament width reported by Arzoumanian et al. (2011)
is robust under standard ISM conditions (sonic-scale turbulence, moderate magnetic
fields). However, alternative scenarios could produce different width distributions:

1. **No Characteristic Scale:** Would require turbulent cascade lacking sonic-scale
   transition or magnetic pressure dominating thermal pressure

2. **Strong Magnetic Fields:** Fields > 50 microGauss could suppress characteristic
   scale formation by providing alternative support mechanism

3. **Different Turbulent Regimes:** Highly supersonic turbulence (Mach > 3) or different
   injection scales could eliminate the 0.1 pc peak

**Key Observational Test:** Measure filament width distributions across diverse
environments while simultaneously measuring magnetic field strengths and turbulent
properties. A narrow peak at 0.1 pc across all environments would confirm the
sonic-scale interpretation, while environment-dependent widths would support
alternative scenarios.
""".format(
            query=query_info['original_query'],
            results="\n---\n".join(results)
        )

        return answer


# Demonstration
if __name__ == "__main__":
    print("="*80)
    print("ASTRA COUNTERFACTUAL REASONING DEMONSTRATION")
    print("Testing: Arzoumanian et al. (2011) filament width result")
    print("="*80)
    print()

    cf_reasoner = CounterfactualReasoning()

    query = """
    CONTEXT: Arzoumanian et al. (2011) used Herschel observations to show that
    interstellar filaments in molecular clouds have a characteristic width of
    approximately 0.1 pc across diverse environments. This has been interpreted
    as evidence for a universal scale in filament formation.

    COUNTERFACTUAL QUESTION: What would have to be true about interstellar
    turbulence or magnetic fields for filaments to NOT have this characteristic
    width?

    Please analyze:
    1. What turbulent conditions would eliminate the characteristic scale?
    2. What magnetic field configurations would produce a broad distribution of widths?
    3. What specific observations would distinguish these scenarios?
    """

    result = cf_reasoner.analyze_counterfactual(query)
    print(result)
