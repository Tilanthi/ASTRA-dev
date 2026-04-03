"""
MORK Data Models

Defines data structures for MORK integration based on CSIG-main.
Implements BiologicalField and AgentNamespace for stigmergic field persistence.
"""

from enum import Enum
from typing import Optional
from dataclasses import dataclass
from datetime import datetime


class FieldType(Enum):
    """Biological field types from Gordon's principles"""
    TAU = "tau"        # Trail strength (pheromone concentration)
    ETA = "eta"        # Encounter rate (contact frequency)
    C_K = "c_k"        # Curiosity value (exploration rate)


@dataclass
class AgentNamespace:
    """
    Hierarchical namespace for multi-colony organization

    Format: colony-{ID}/squad-{ID}/agent-{ID}
    Enables isolated knowledge spaces per colony/squad.
    """
    colony_id: str
    squad_id: str
    agent_id: str

    def to_path(self) -> str:
        """Convert to hierarchical path string"""
        return f"colony-{self.colony_id}/squad-{self.squad_id}/agent-{self.agent_id}"

    def to_squad_path(self) -> str:
        """Get squad-level path"""
        return f"colony-{self.colony_id}/squad-{self.squad_id}"

    def to_colony_path(self) -> str:
        """Get colony-level path"""
        return f"colony-{self.colony_id}"

    @staticmethod
    def from_path(path: str) -> 'AgentNamespace':
        """
        Parse namespace from path string

        Args:
            path: Path string (e.g., "colony-A/squad-1/agent-001")

        Returns:
            AgentNamespace instance

        Raises:
            ValueError: If path format is invalid
        """
        parts = path.split('/')
        if len(parts) != 3:
            raise ValueError(f"Invalid namespace path: {path}. Expected format: colony-X/squad-Y/agent-Z")

        # Extract IDs
        colony_id = parts[0].replace('colony-', '')
        squad_id = parts[1].replace('squad-', '')
        agent_id = parts[2].replace('agent-', '')

        return AgentNamespace(colony_id=colony_id, squad_id=squad_id, agent_id=agent_id)

    def __str__(self) -> str:
        return self.to_path()


@dataclass
class BiologicalField:
    """
    Stigmergic biological field with validation

    Stores field values (tau, eta, c_k) for agent coordination.
    Values normalized to [0.0, 1.0] range.
    """
    namespace: AgentNamespace
    field_type: FieldType
    value: float
    timestamp: datetime

    def __post_init__(self):
        """Validate field value"""
        if not 0.0 <= self.value <= 1.0:
            raise ValueError(f"Field value must be in [0.0, 1.0], got {self.value}")

    def to_s_expression(self) -> str:
        """
        Convert to MORK S-expression format

        Returns:
            S-expression string for MORK storage
        """
        path = self.namespace.to_path()
        field = self.field_type.value
        value = self.value
        ts = int(self.timestamp.timestamp())

        return f"(field {path} {field} {value} {ts})"

    def to_field_path(self) -> str:
        """Get field-specific storage path"""
        return f"{self.namespace.to_path()}/{self.field_type.value}"

    @staticmethod
    def from_s_expression(s_expr: str) -> 'BiologicalField':
        """
        Parse BiologicalField from S-expression

        Args:
            s_expr: S-expression string

        Returns:
            BiologicalField instance
        """
        # Simple parser: (field colony-A/squad-1/agent-001 tau 0.85 1234567890)
        s_expr = s_expr.strip('()')
        parts = s_expr.split()

        if len(parts) != 5 or parts[0] != 'field':
            raise ValueError(f"Invalid S-expression: {s_expr}")

        namespace_path = parts[1]
        field_type = FieldType(parts[2])
        value = float(parts[3])
        timestamp = datetime.fromtimestamp(int(parts[4]))

        namespace = AgentNamespace.from_path(namespace_path)

        return BiologicalField(
            namespace=namespace,
            field_type=field_type,
            value=value,
            timestamp=timestamp
        )

    def __str__(self) -> str:
        return f"BiologicalField({self.namespace}, {self.field_type.value}={self.value:.3f})"


@dataclass
class SymbolicAbstraction:
    """
    V36 symbolic abstraction stored as S-expression

    Bridges V36 symbolic causal reasoning with MORK symbolic storage.
    """
    namespace: AgentNamespace
    variable_name: str
    template: str                    # e.g., "stable_autoregressive"
    parameters: dict                 # e.g., {"alpha": 0.995, "sigma": 0.02}
    canonical_form: str              # Human-readable form
    timestamp: datetime

    def to_s_expression(self) -> str:
        """
        Convert to MORK S-expression

        Returns:
            S-expression for MORK storage
        """
        path = self.namespace.to_path()
        params_str = ' '.join(f"({k} {v})" for k, v in self.parameters.items())

        return f"(symbolic-form {path} {self.variable_name} (template {self.template}) {params_str})"

    def __str__(self) -> str:
        return f"SymbolicAbstraction({self.variable_name}: {self.canonical_form})"


@dataclass
class PheromoneField:
    """
    Pheromone field for stigmergic pathfinding

    Used for A* pathfinding with pheromone weights in swarm systems.
    """
    source_asset: str
    target_asset: str
    pheromone_strength: float       # tau value [0.0, 1.0]
    base_cost: float                # Base transition cost
    timestamp: datetime

    def effective_cost(self, beta: float = 0.395) -> float:
        """
        Calculate effective cost with pheromone weighting

        Args:
            beta: Pheromone weight parameter (Gordon's beta)

        Returns:
            Adjusted cost: c'_ij = c_base * (1 - beta * (1 - 1/tau))
        """
        if self.pheromone_strength == 0:
            return float('inf')

        return self.base_cost * (1 - beta * (1 - 1 / self.pheromone_strength))

    def to_s_expression(self) -> str:
        """Convert to MORK S-expression"""
        ts = int(self.timestamp.timestamp())
        return f"(pheromone {self.source_asset} {self.target_asset} {self.pheromone_strength} {self.base_cost} {ts})"

    def __str__(self) -> str:
        return f"Pheromone({self.source_asset}→{self.target_asset}, τ={self.pheromone_strength:.3f})"
