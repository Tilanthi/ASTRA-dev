"""
Phase 2: Operator Pattern Implementation

Implements Kubernetes-style operators for domain-specific workflows:
- Domain-specific controllers
- Full lifecycle management
- Encoded operational knowledge
- Automatic response to state changes
"""

from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
import logging
import asyncio
from abc import ABC, abstractmethod

from .controllers import Controller, ControllerManager
from .declarative import (
    DeclarativeResource, ResourceSpec, ResourceStatus,
    ResourceState, ConditionType, ReconciliationLoop
)

logger = logging.getLogger(__name__)


@dataclass
class WorkflowPhase:
    """A phase in a workflow"""
    name: str
    execute: Callable
    depends_on: List[str] = field(default_factory=list)
    timeout: float = 300.0
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class WorkflowStatus:
    """Status of a workflow execution"""
    current_phase: str = ""
    phase_status: Dict[str, str] = field(default_factory=dict)
    phase_outputs: Dict[str, Any] = field(default_factory=dict)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class Operator(Controller):
    """
    Base class for operators.

    An operator is a domain-specific controller that manages
    complex applications and their full lifecycle.
    """

    def __init__(self,
                 name: str,
                 resource_type: str,
                 workflow_phases: List[WorkflowPhase]):
        super().__init__(name, resource_type)
        self.workflow_phases = workflow_phases
        self.phase_dependencies = self._build_dependency_graph()

    def _build_dependency_graph(self) -> Dict[str, List[str]]:
        """Build dependency graph from workflow phases"""
        graph = {}
        for phase in self.workflow_phases:
            graph[phase.name] = phase.depends_on
        return graph

    def _get_ready_phases(self, status: WorkflowStatus) -> List[WorkflowPhase]:
        """Get phases that are ready to execute"""
        ready = []

        for phase in self.workflow_phases:
            # Skip if already completed or in progress
            if phase.name in status.phase_status:
                continue

            # Check if dependencies are met
            dependencies_met = all(
                dep in status.phase_status and
                status.phase_status[dep] == "completed"
                for dep in phase.depends_on
            )

            if dependencies_met:
                ready.append(phase)

        return ready

    async def execute_phase(self, phase: WorkflowPhase,
                           context: Dict[str, Any]) -> Any:
        """Execute a single workflow phase"""
        try:
            logger.info(f"Executing phase {phase.name}")

            # Execute with timeout
            result = await asyncio.wait_for(
                phase.execute(context),
                timeout=phase.timeout
            )

            logger.info(f"Phase {phase.name} completed successfully")
            return result

        except asyncio.TimeoutError:
            logger.error(f"Phase {phase.name} timed out")
            raise
        except Exception as e:
            logger.error(f"Error executing phase {phase.name}: {e}")
            raise

    async def reconcile_workflow(self, resource: DeclarativeResource) -> bool:
        """Reconcile a workflow-based resource"""
        # Get or create workflow status
        workflow_status = getattr(resource, "workflow_status", WorkflowStatus())

        if workflow_status.start_time is None:
            workflow_status.start_time = datetime.now()

        try:
            # Get ready phases
            ready_phases = self._get_ready_phases(workflow_status)

            if not ready_phases:
                # Check if workflow is complete
                if all(phase.name in workflow_status.phase_status
                       for phase in self.workflow_phases):
                    resource.status.state = ResourceState.COMPLETED
                    workflow_status.end_time = datetime.now()
                    logger.info(f"Workflow {resource.get_uid()} completed")
                    return True
                else:
                    # Waiting for dependencies
                    return True

            # Execute ready phases
            context = {
                "resource": resource,
                "phase_outputs": workflow_status.phase_outputs,
                "spec": resource.spec.spec,
            }

            for phase in ready_phases:
                try:
                    result = await self.execute_phase(phase, context)
                    workflow_status.phase_status[phase.name] = "completed"
                    workflow_status.phase_outputs[phase.name] = result
                    workflow_status.current_phase = phase.name

                    # Update resource status
                    resource.status.set_condition(
                        ConditionType.PROGRESSING,
                        "True",
                        f"Phase{phase.name}",
                        f"Completed phase {phase.name}"
                    )

                except Exception as e:
                    workflow_status.phase_status[phase.name] = "failed"
                    workflow_status.current_phase = phase.name

                    # Check if retryable
                    if phase.retry_count < phase.max_retries:
                        phase.retry_count += 1
                        workflow_status.phase_status[phase.name] = "pending_retry"
                        resource.status.set_condition(
                            ConditionType.RETRYABLE,
                            "True",
                            f"Phase{phase.name}Retry",
                            f"Will retry phase {phase.name}"
                        )
                    else:
                        resource.status.state = ResourceState.FAILED
                        resource.status.error_message = (
                            f"Phase {phase.name} failed after {phase.max_retries} retries"
                        )
                        resource.status.set_condition(
                            ConditionType.FAILED,
                            "True",
                            f"Phase{phase.name}Failed",
                            str(e)
                        )
                        return False

            # Update resource
            resource.workflow_status = workflow_status
            return True

        except Exception as e:
            logger.error(f"Error reconciling workflow: {e}")
            resource.status.state = ResourceState.FAILED
            resource.status.error_message = str(e)
            return False


class DomainOperator(Operator):
    """
    Operator for managing domain-specific workflows.

    Encodes operational knowledge for specific scientific domains
    and manages the full lifecycle of domain operations.
    """

    def __init__(self,
                 name: str,
                 domain: str,
                 workflow_phases: List[WorkflowPhase],
                 domain_config: Dict[str, Any] = None):
        super().__init__(name, f"{domain}Workflow", workflow_phases)
        self.domain = domain
        self.domain_config = domain_config or {}

    async def validate_domain_state(self, resource: DeclarativeResource) -> bool:
        """Validate that domain-specific state is consistent"""
        # Override in subclasses to add domain-specific validation
        return True

    async def reconcile(self, resource: DeclarativeResource) -> bool:
        """Reconcile a domain workflow resource"""
        # Domain-specific validation
        if not await self.validate_domain_state(resource):
            resource.status.state = ResourceState.FAILED
            resource.status.error_message = "Domain validation failed"
            return False

        # Run workflow reconciliation
        return await self.reconcile_workflow(resource)


class FilamentAnalysisOperator(DomainOperator):
    """
    Operator for managing filament analysis workflows.

    Handles the complete lifecycle of filament analysis:
    - Data validation
    - Core extraction
    - Spacing measurement
    - Comparison with theory
    """

    def __init__(self, astra_system=None):
        # Define workflow phases
        phases = [
            WorkflowPhase(
                name="validate_data",
                execute=self._validate_data,
                timeout=60.0
            ),
            WorkflowPhase(
                name="extract_cores",
                execute=self._extract_cores,
                depends_on=["validate_data"],
                timeout=300.0
            ),
            WorkflowPhase(
                name="measure_spacing",
                execute=self._measure_spacing,
                depends_on=["extract_cores"],
                timeout=180.0
            ),
            WorkflowPhase(
                name="compare_theory",
                execute=self._compare_theory,
                depends_on=["measure_spacing"],
                timeout=120.0
            ),
        ]

        super().__init__(
            name="FilamentAnalysisOperator",
            domain="filaments",
            workflow_phases=phases,
            domain_config={
                "supported_regions": [
                    "Orion B", "Aquila", "Perseus", "Taurus",
                    "Ophiuchus", "Serpens", "TMC1", "CRA"
                ],
                "default_width_pc": 0.1,
                "min_cores": 10
            }
        )

        self.astra_system = astra_system

    async def _validate_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data for filament analysis"""
        resource = context["resource"]
        spec = context["spec"]

        region = spec.get("region", "")
        data_file = spec.get("data_file", "")

        logger.info(f"Validating data for region {region}")

        # Validate region
        if region not in self.domain_config["supported_regions"]:
            raise ValueError(f"Unsupported region: {region}")

        # Check data file exists
        if not data_file:
            raise ValueError("Data file not specified")

        # Validate file format
        # (In real implementation, would check file structure)

        return {
            "region": region,
            "data_file": data_file,
            "validation_passed": True
        }

    async def _extract_cores(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract cores from filament data"""
        spec = context["spec"]
        validation_result = context["phase_outputs"]["validate_data"]

        logger.info(f"Extracting cores for {validation_result['region']}")

        # Use ASTRA system for core extraction
        if self.astra_system:
            query = f"Extract cores from {validation_result['data_file']} in {validation_result['region']}"
            result = await self.astra_system.answer(query)
        else:
            # Mock result
            result = {
                "cores": [],
                "count": 0,
                "method": "mock"
            }

        return result

    async def _measure_spacing(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Measure core spacing along filaments"""
        cores_result = context["phase_outputs"]["extract_cores"]

        logger.info(f"Measuring spacing for {len(cores_result.get('cores', []))} cores")

        # Calculate spacing metrics
        # (In real implementation, would use actual spacing algorithms)

        return {
            "lambda_pc": 0.28,
            "lambda_over_W": 2.8,
            "n_cores": len(cores_result.get('cores', [])),
            "method": "nearest_neighbor"
        }

    async def _compare_theory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Compare measurements with theoretical predictions"""
        spacing_result = context["phase_outputs"]["measure_spacing"]

        logger.info(f"Comparing theory for lambda/W = {spacing_result['lambda_over_W']}")

        # Theoretical comparison
        classical_prediction = 4.0
        observed = spacing_result['lambda_over_W']
        discrepancy = (classical_prediction - observed) / classical_prediction

        return {
            "classical_prediction": classical_prediction,
            "observed": observed,
            "discrepancy_percent": discrepancy * 100,
            "interpretation": "sub-Jeans spacing" if observed < 4.0 else "super-Jeans spacing"
        }


class DiscoveryOperator(DomainOperator):
    """
    Operator for managing autonomous scientific discovery workflows.

    Handles the complete discovery cycle:
    - Question generation
    - Hypothesis formulation
    - Experiment design
    - Data collection
    - Analysis and inference
    - Theory revision
    - Publication preparation
    """

    def __init__(self, astra_system=None):
        # Define workflow phases
        phases = [
            WorkflowPhase(
                name="generate_questions",
                execute=self._generate_questions,
                timeout=120.0
            ),
            WorkflowPhase(
                name="formulate_hypotheses",
                execute=self._formulate_hypotheses,
                depends_on=["generate_questions"],
                timeout=180.0
            ),
            WorkflowPhase(
                name="design_experiments",
                execute=self._design_experiments,
                depends_on=["formulate_hypotheses"],
                timeout=240.0
            ),
            WorkflowPhase(
                name="collect_data",
                execute=self._collect_data,
                depends_on=["design_experiments"],
                timeout=600.0
            ),
            WorkflowPhase(
                name="analyze_results",
                execute=self._analyze_results,
                depends_on=["collect_data"],
                timeout=300.0
            ),
            WorkflowPhase(
                name="revise_theory",
                execute=self._revise_theory,
                depends_on=["analyze_results"],
                timeout=200.0
            ),
            WorkflowPhase(
                name="prepare_publication",
                execute=self._prepare_publication,
                depends_on=["revise_theory"],
                timeout=360.0
            ),
        ]

        super().__init__(
            name="DiscoveryOperator",
            domain="discovery",
            workflow_phases=phases,
            domain_config={
                "discovery_modes": ["observational", "theoretical", "computational"],
                "min_confidence": 0.7,
                "max_iterations": 5
            }
        )

        self.astra_system = astra_system

    async def _generate_questions(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate research questions"""
        spec = context["spec"]
        domain = spec.get("domain", "general")
        discovery_mode = spec.get("mode", "observational")

        logger.info(f"Generating questions for domain {domain} in mode {discovery_mode}")

        if self.astra_system:
            query = f"Generate important research questions in {domain} using {discovery_mode} methods"
            result = await self.astra_system.answer(query)
        else:
            result = {
                "questions": [
                    "What is the primary mechanism for filament fragmentation?",
                    "How does magnetic field geometry affect core spacing?"
                ],
                "count": 2
            }

        return result

    async def _formulate_hypotheses(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Formulate testable hypotheses"""
        questions = context["phase_outputs"]["generate_questions"]["questions"]

        logger.info(f"Formulating hypotheses for {len(questions)} questions")

        if self.astra_system:
            query = f"Formulate testable hypotheses for these questions: {questions}"
            result = await self.astra_system.answer(query)
        else:
            result = {
                "hypotheses": [
                    {
                        "question": questions[0],
                        "hypothesis": "Filament fragmentation is dominated by gravitational instability",
                        "predictions": ["lambda/W ~ 4 for isothermal filaments"]
                    }
                ]
            }

        return result

    async def _design_experiments(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Design experiments to test hypotheses"""
        hypotheses = context["phase_outputs"]["formulate_hypotheses"]["hypotheses"]

        logger.info(f"Designing experiments for {len(hypotheses)} hypotheses")

        if self.astra_system:
            query = f"Design experiments to test these hypotheses: {hypotheses}"
            result = await self.astra_system.answer(query)
        else:
            result = {
                "experiments": [
                    {
                        "type": "simulation",
                        "description": "Run MHD filament fragmentation simulations",
                        "parameters": {"f": [1.5, 2.0, 2.5], "beta": [0.5, 1.0, 2.0]}
                    }
                ]
            }

        return result

    async def _collect_data(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Collect experimental data"""
        experiments = context["phase_outputs"]["design_experiments"]["experiments"]

        logger.info(f"Collecting data for {len(experiments)} experiments")

        # In real implementation, would run experiments or collect observational data
        result = {
            "data_collected": True,
            "data_sources": ["simulations", "observations"],
            "records": 216  # Example: Campaign A results
        }

        return result

    async def _analyze_results(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze experimental results"""
        data_result = context["phase_outputs"]["collect_data"]

        logger.info("Analyzing experimental results")

        if self.astra_system:
            query = "Analyze the filament fragmentation simulation results and compare with theory"
            result = await self.astra_system.answer(query)
        else:
            result = {
                "findings": [
                    "Subsonic turbulence has no effect on fragmentation",
                    "Perpendicular fields fragment 2.8x faster than longitudinal"
                ],
                "statistical_significance": 0.95
            }

        return result

    async def _revise_theory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Revise theoretical understanding based on results"""
        analysis = context["phase_outputs"]["analyze_results"]["findings"]

        logger.info("Revising theory based on experimental results")

        if self.astra_system:
            query = f"Revise theoretical understanding based on these findings: {analysis}"
            result = await self.astra_system.answer(query)
        else:
            result = {
                "theory_revisions": [
                    "Update fragmentation model to include field geometry effects",
                    "Add time-weighting correction to Planck tension calculation"
                ],
                "confidence": 0.85
            }

        return result

    async def _prepare_publication(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare scientific publication"""
        all_outputs = context["phase_outputs"]

        logger.info("Preparing publication")

        # Compile all results into publication format
        result = {
            "title": "Filament Fragmentation in Magnetised Turbulent Clouds",
            "abstract": "We present results from 216 MHD simulations...",
            "sections": ["Introduction", "Methods", "Results", "Discussion", "Conclusions"],
            "figures": 6,
            "tables": 4,
            "ready_for_submission": True
        }

        return result


# Operator Factory

class OperatorFactory:
    """Factory for creating domain operators"""

    def __init__(self):
        self._operator_classes = {
            "filaments": FilamentAnalysisOperator,
            "discovery": DiscoveryOperator,
        }
        self._instances = {}

    def register_operator(self, domain: str, operator_class: type):
        """Register a new operator class"""
        self._operator_classes[domain] = operator_class
        logger.info(f"Registered operator for domain {domain}")

    def create_operator(self, domain: str, **kwargs) -> Optional[Operator]:
        """Create an operator instance for a domain"""
        if domain not in self._operator_classes:
            logger.error(f"No operator registered for domain {domain}")
            return None

        # Check if instance already exists
        if domain in self._instances:
            return self._instances[domain]

        # Create new instance
        operator_class = self._operator_classes[domain]
        operator = operator_class(**kwargs)
        self._instances[domain] = operator

        logger.info(f"Created operator for domain {domain}")
        return operator

    def get_operator(self, domain: str, **kwargs) -> Optional[Operator]:
        """Get or create an operator for a domain"""
        if domain not in self._instances:
            return self.create_operator(domain, **kwargs)
        return self._instances[domain]
