"""
Phase 3: CRD-Based Extensibility System

Implements Custom Resource Definitions for dynamic extensibility:
- Plugin architecture without core changes
- Automatic lifecycle management
- Consistent API surface
- Schema validation
"""

from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import asyncio
import json
from abc import ABC, abstractmethod

from .controllers import Controller
from .operators import Operator
from .declarative import ResourceSpec, DeclarativeResource, ResourceState

logger = logging.getLogger(__name__)


class ValidationStatus(Enum):
    """Status of schema validation"""
    VALID = "valid"
    INVALID = "invalid"
    UNKNOWN = "unknown"


@dataclass
class PropertySchema:
    """Schema definition for a property"""
    type: str  # string, number, boolean, array, object
    required: bool = False
    description: str = ""
    default: Any = None
    enum: Optional[List[Any]] = None
    format: Optional[str] = None  # For additional type constraints


@dataclass
class CRDSchema:
    """Schema for a Custom Resource Definition"""
    kind: str
    version: str
    group: str  # API group (e.g., "astra.ai")
    plural: str  # Plural name (e.g., "tasks")
    singular: str  # Singular name (e.g., "task")
    scope: str = "namespaced"  # "namespaced" or "cluster"
    properties: Dict[str, PropertySchema] = field(default_factory=dict)
    validation: Optional[Callable] = None


@dataclass
class CRDValidationResult:
    """Result of CRD validation"""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class CustomResourceDefinition:
    """
    Custom Resource Definition for extending the system.

    Allows dynamic registration of new resource types without
    modifying core code.
    """

    def __init__(self, schema: CRDSchema):
        self.schema = schema

        # Registry
        self.handlers: Dict[str, Callable] = {}
        self.controllers: Dict[str, Controller] = {}
        self.operators: Dict[str, Operator] = {}

        # Instances
        self.instances: Dict[str, DeclarativeResource] = {}

        logger.info(f"Created CRD for {schema.kind}")

    def validate(self, resource: Dict[str, Any]) -> CRDValidationResult:
        """Validate a resource against the CRD schema"""
        errors = []
        warnings = []

        # Check required fields
        for prop_name, prop_schema in self.schema.properties.items():
            if prop_schema.required and prop_name not in resource.get("spec", {}):
                errors.append(f"Required property '{prop_name}' is missing")

        # Type checking
        spec = resource.get("spec", {})
        for prop_name, prop_value in spec.items():
            if prop_name not in self.schema.properties:
                warnings.append(f"Unknown property '{prop_name}'")
                continue

            prop_schema = self.schema.properties[prop_name]

            # Type validation
            if prop_schema.type == "string":
                if not isinstance(prop_value, str):
                    errors.append(f"Property '{prop_name}' must be string")
            elif prop_schema.type == "number":
                if not isinstance(prop_value, (int, float)):
                    errors.append(f"Property '{prop_name}' must be number")
            elif prop_schema.type == "boolean":
                if not isinstance(prop_value, bool):
                    errors.append(f"Property '{prop_name}' must be boolean")
            elif prop_schema.type == "array":
                if not isinstance(prop_value, list):
                    errors.append(f"Property '{prop_name}' must be array")

            # Enum validation
            if prop_schema.enum is not None:
                if prop_value not in prop_schema.enum:
                    errors.append(
                        f"Property '{prop_name}' must be one of {prop_schema.enum}"
                    )

        # Custom validation
        if self.schema.validation:
            custom_result = self.schema.validation(resource)
            if not custom_result.valid:
                errors.extend(custom_result.errors)

        return CRDValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def register_handler(self, phase: str, handler: Callable):
        """Register a handler for a specific phase"""
        self.handlers[phase] = handler
        logger.info(f"Registered handler for phase {phase}")

    async def handle_phase(self, phase: str, resource: DeclarativeResource) -> Any:
        """Handle a specific phase of resource lifecycle"""
        if phase not in self.handlers:
            raise ValueError(f"No handler registered for phase {phase}")

        handler = self.handlers[phase]

        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(resource)
            else:
                return handler(resource)
        except Exception as e:
            logger.error(f"Error in handler for phase {phase}: {e}")
            raise

    def add_instance(self, resource: DeclarativeResource):
        """Add a resource instance"""
        uid = resource.get_uid()
        self.instances[uid] = resource
        logger.info(f"Added instance {uid} of {self.schema.kind}")

    def remove_instance(self, uid: str):
        """Remove a resource instance"""
        if uid in self.instances:
            del self.instances[uid]
            logger.info(f"Removed instance {uid} of {self.schema.kind}")

    def get_instance(self, uid: str) -> Optional[DeclarativeResource]:
        """Get a resource instance"""
        return self.instances.get(uid)

    def list_instances(self) -> List[DeclarativeResource]:
        """List all instances"""
        return list(self.instances.values())


class CRDRegistry:
    """
    Registry for Custom Resource Definitions.

    Manages all CRDs in the system and provides
    a central point for registration and discovery.
    """

    def __init__(self):
        self.crds: Dict[str, CustomResourceDefinition] = {}
        self.api_groups: Dict[str, List[str]] = {}  # group -> kinds

        logger.info("CRD Registry initialized")

    def register_crd(self, crd: CustomResourceDefinition):
        """Register a new CRD"""
        kind = crd.schema.kind

        if kind in self.crds:
            logger.warning(f"CRD for {kind} already exists, updating")

        self.crds[kind] = crd

        # Update API group index
        group = crd.schema.group
        if group not in self.api_groups:
            self.api_groups[group] = []
        self.api_groups[group].append(kind)

        logger.info(f"Registered CRD for {kind}")

    def unregister_crd(self, kind: str):
        """Unregister a CRD"""
        if kind in self.crds:
            crd = self.crds[kind]

            # Remove from API group index
            group = crd.schema.group
            if group in self.api_groups and kind in self.api_groups[group]:
                self.api_groups[group].remove(kind)

            del self.crds[kind]
            logger.info(f"Unregistered CRD for {kind}")

    def get_crd(self, kind: str) -> Optional[CustomResourceDefinition]:
        """Get a CRD by kind"""
        return self.crds.get(kind)

    def list_crds(self) -> List[CRDSchema]:
        """List all registered CRDs"""
        return [crd.schema for crd in self.crds.values()]

    def list_kinds_in_group(self, group: str) -> List[str]:
        """List all kinds in an API group"""
        return self.api_groups.get(group, [])

    def validate_resource(self, kind: str, resource: Dict[str, Any]) -> CRDValidationResult:
        """Validate a resource against its CRD"""
        crd = self.get_crd(kind)
        if crd is None:
            return CRDValidationResult(
                valid=False,
                errors=[f"Unknown resource kind: {kind}"]
            )

        return crd.validate(resource)


class CapabilityCRD(CustomResourceDefinition):
    """
    CRD for defining custom capabilities.

    Allows users to define new capabilities without modifying core code.
    """

    @classmethod
    def create_schema(cls,
                     capability_name: str,
                     handler: Callable,
                     resources: Optional[Dict[str, Any]] = None,
                     dependencies: Optional[List[str]] = None) -> CRDSchema:
        """Create a schema for a capability CRD"""

        properties = {
            "name": PropertySchema(
                type="string",
                required=True,
                description="Name of the capability"
            ),
            "handler": PropertySchema(
                type="string",
                required=True,
                description="Handler function name"
            ),
            "description": PropertySchema(
                type="string",
                required=False,
                description="Description of what the capability does"
            ),
            "resources": PropertySchema(
                type="object",
                required=False,
                description="Resources required by the capability"
            ),
            "dependencies": PropertySchema(
                type="array",
                required=False,
                description="Other capabilities this depends on"
            ),
            "enabled": PropertySchema(
                type="boolean",
                required=False,
                description="Whether the capability is enabled",
                default=True
            ),
        }

        schema = CRDSchema(
            kind="Capability",
            version="v1",
            group="astra.ai",
            plural="capabilities",
            singular="capability",
            properties=properties,
        )

        return schema

    def __init__(self, schema: CRDSchema):
        super().__init__(schema)

        # Capability-specific state
        self.capability_handlers: Dict[str, Callable] = {}
        self.capability_instances: Dict[str, Any] = {}

    def register_capability_handler(self, name: str, handler: Callable):
        """Register a capability handler function"""
        self.capability_handlers[name] = handler
        logger.info(f"Registered capability handler {name}")

    async def invoke_capability(self,
                               capability_name: str,
                               query: str,
                               context: Dict[str, Any]) -> Any:
        """Invoke a capability"""
        if capability_name not in self.capability_handlers:
            raise ValueError(f"Capability not found: {capability_name}")

        handler = self.capability_handlers[capability_name]

        try:
            if asyncio.iscoroutinefunction(handler):
                return await handler(query, context)
            else:
                return handler(query, context)
        except Exception as e:
            logger.error(f"Error invoking capability {capability_name}: {e}")
            raise


# Predefined CRDs for common ASTRA resources

class AnalysisTaskCRD(CustomResourceDefinition):
    """CRD for analysis tasks (filament, discovery, etc.)"""

    @classmethod
    def get_schema(cls) -> CRDSchema:
        properties = {
            "domain": PropertySchema(
                type="string",
                required=True,
                description="Scientific domain (e.g., filaments, exoplanets)",
                enum=["filaments", "exoplanets", "gravitational_waves", "cosmology", "discovery"]
            ),
            "analysis_type": PropertySchema(
                type="string",
                required=True,
                description="Type of analysis to perform"
            ),
            "data_source": PropertySchema(
                type="string",
                required=True,
                description="Path to input data"
            ),
            "parameters": PropertySchema(
                type="object",
                required=False,
                description="Analysis parameters"
            ),
            "output_format": PropertySchema(
                type="string",
                required=False,
                description="Desired output format",
                enum=["json", "pdf", "plots", "data"]
            ),
        }

        return CRDSchema(
            kind="AnalysisTask",
            version="v1",
            group="astra.ai",
            plural="analysistasks",
            singular="analysistask",
            properties=properties,
        )


class SimulationJobCRD(CustomResourceDefinition):
    """CRD for simulation jobs"""

    @classmethod
    def get_schema(cls) -> CRDSchema:
        properties = {
            "simulation_type": PropertySchema(
                type="string",
                required=True,
                description="Type of simulation (e.g., MHD, hydro, N-body)"
            ),
            "parameters": PropertySchema(
                type="object",
                required=True,
                description="Simulation parameters"
            ),
            "domain": PropertySchema(
                type="string",
                required=True,
                description="Physical domain"
            ),
            "resolution": PropertySchema(
                type="string",
                required=False,
                description="Simulation resolution"
            ),
            "duration": PropertySchema(
                type="number",
                required=False,
                description="Simulation duration in code units"
            ),
            "output_location": PropertySchema(
                type="string",
                required=False,
                description="Where to store results"
            ),
        }

        return CRDSchema(
            kind="SimulationJob",
            version="v1",
            group="astra.ai",
            plural="simulationjobs",
            singular="simulationjob",
            properties=properties,
        )


class DiscoveryCampaignCRD(CustomResourceDefinition):
    """CRD for discovery campaigns"""

    @classmethod
    def get_schema(cls) -> CRDSchema:
        properties = {
            "campaign_name": PropertySchema(
                type="string",
                required=True,
                description="Name of the discovery campaign"
            ),
            "domain": PropertySchema(
                type="string",
                required=True,
                description="Scientific domain"
            ),
            "research_questions": PropertySchema(
                type="array",
                required=True,
                description="Research questions to investigate"
            ),
            "hypotheses": PropertySchema(
                type="array",
                required=False,
                description="Initial hypotheses to test"
            ),
            "experiments": PropertySchema(
                type="array",
                required=False,
                description="Experiments to run"
            ),
            "max_iterations": PropertySchema(
                type="number",
                required=False,
                description="Maximum discovery iterations",
                default=5
            ),
            "publication_ready": PropertySchema(
                type="boolean",
                required=False,
                description="Whether to prepare publication",
                default=False
            ),
        }

        return CRDSchema(
            kind="DiscoveryCampaign",
            version="v1",
            group="astra.ai",
            plural="discoverycampaigns",
            singular="discoverycampaign",
            properties=properties,
        )


class CRDController(Controller):
    """
    Generic controller for CRD-based resources.

    Automatically handles lifecycle of custom resources.
    """

    def __init__(self, crd_registry: CRDRegistry, kind: str):
        super().__init__(
            name=f"{kind}Controller",
            resource_type=kind
        )
        self.crd_registry = crd_registry
        self.kind = kind

    async def reconcile(self, resource: DeclarativeResource) -> bool:
        """Reconcile a CRD-based resource"""
        try:
            # Get CRD
            crd = self.crd_registry.get_crd(self.kind)
            if crd is None:
                logger.error(f"CRD not found for {self.kind}")
                return False

            # Handle based on resource state
            if resource.status.state == ResourceState.PENDING:
                # Create phase
                await crd.handle_phase("create", resource)
                resource.status.state = ResourceState.RUNNING
                resource.status.set_condition(
                    "Progressing",
                    "True",
                    "Created",
                    f"{self.kind} created successfully"
                )

            elif resource.status.state == ResourceState.RUNNING:
                # Run phase - execute the main logic
                await crd.handle_phase("run", resource)

                # Check if complete
                if self._is_complete(resource):
                    resource.status.state = ResourceState.COMPLETED
                    resource.status.set_condition(
                        "Ready",
                        "True",
                        "Completed",
                        f"{self.kind} completed successfully"
                    )
                    await crd.handle_phase("complete", resource)

            return True

        except Exception as e:
            logger.error(f"Error reconciling {self.kind}: {e}")
            resource.status.state = ResourceState.FAILED
            resource.status.error_message = str(e)
            return False

    def _is_complete(self, resource: DeclarativeResource) -> bool:
        """Check if resource processing is complete"""
        # Check for completion indicators in status
        for condition in resource.status.conditions:
            if condition.type.value == "Ready" and condition.status == "True":
                return True
        return False


def create_standard_crds(registry: CRDRegistry):
    """Create and register standard ASTRA CRDs"""

    # Analysis Task CRD
    analysis_schema = AnalysisTaskCRD.get_schema()
    analysis_crd = AnalysisTaskCRD(analysis_schema)
    registry.register_crd(analysis_crd)

    # Simulation Job CRD
    simulation_schema = SimulationJobCRD.get_schema()
    simulation_crd = SimulationJobCRD(simulation_schema)
    registry.register_crd(simulation_crd)

    # Discovery Campaign CRD
    discovery_schema = DiscoveryCampaignCRD.get_schema()
    discovery_crd = DiscoveryCampaignCRD(discovery_schema)
    registry.register_crd(discovery_crd)

    logger.info("Registered standard ASTRA CRDs")
