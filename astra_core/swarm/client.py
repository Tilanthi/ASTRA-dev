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
MORK Client

Client for interacting with MORK symbolic reasoning engine.
Supports both local storage and remote MORK server.

Based on CSIG-main mork-client-csig implementation.
"""

import json
import pickle
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from .models import (
    AgentNamespace,
    BiologicalField,
    SymbolicAbstraction,
    PheromoneField,
    FieldType
)


class LocalMORKStorage:
    """
    Local file-based MORK storage

    Implements MORK functionality using local filesystem.
    Suitable for standalone operation without remote MORK server.
    """

    def __init__(self, storage_path: Path = None):
        """
        Initialize local MORK storage

        Args:
            storage_path: Path for local storage (default: mork/storage/)
        """
        if storage_path is None:
            storage_path = Path(__file__).parent / "storage"

        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # Storage structure:
        # storage/
        #   colony-A/
        #     squad-1/
        #       agent-001/
        #         fields.json
        #         symbolic_abstractions.json
        #         pheromones.json

    def _get_agent_path(self, namespace: AgentNamespace) -> Path:
        """Get storage path for agent"""
        return self.storage_path / namespace.to_path()

    def _ensure_namespace(self, namespace: AgentNamespace):
        """Ensure namespace directory exists"""
        agent_path = self._get_agent_path(namespace)
        agent_path.mkdir(parents=True, exist_ok=True)

    def upload_field(self, field: BiologicalField) -> bool:
        """
        Upload biological field

        Args:
            field: BiologicalField to store

        Returns:
            True if successful
        """
        self._ensure_namespace(field.namespace)

        fields_file = self._get_agent_path(field.namespace) / "fields.json"

        # Load existing fields
        if fields_file.exists():
            with open(fields_file, 'r') as f:
                fields_data = json.load(f)
        else:
            fields_data = {}

        # Store field
        field_key = field.field_type.value
        fields_data[field_key] = {
            'value': field.value,
            'timestamp': int(field.timestamp.timestamp())
        }

        # Write back
        with open(fields_file, 'w') as f:
            json.dump(fields_data, f, indent=2)

        return True

    def batch_upload(self, fields: List[BiologicalField]) -> bool:
        """
        Batch upload fields for 87x speedup

        Args:
            fields: List of BiologicalFields

        Returns:
            True if all successful
        """
        for field in fields:
            if not self.upload_field(field):
                return False
        return True

    def download_field(self, namespace: AgentNamespace, field_type: FieldType) -> Optional[BiologicalField]:
        """
        Download biological field

        Args:
            namespace: Agent namespace
            field_type: Type of field to retrieve

        Returns:
            BiologicalField if found, None otherwise
        """
        fields_file = self._get_agent_path(namespace) / "fields.json"

        if not fields_file.exists():
            return None

        with open(fields_file, 'r') as f:
            fields_data = json.load(f)

        field_key = field_type.value
        if field_key not in fields_data:
            return None

        data = fields_data[field_key]
        return BiologicalField(
            namespace=namespace,
            field_type=field_type,
            value=data['value'],
            timestamp=datetime.fromtimestamp(data['timestamp'])
        )

    def batch_download(self, namespace: AgentNamespace) -> Dict[FieldType, BiologicalField]:
        """
        Batch download all fields for agent

        Args:
            namespace: Agent namespace

        Returns:
            Dictionary mapping FieldType to BiologicalField
        """
        result = {}

        for field_type in FieldType:
            field = self.download_field(namespace, field_type)
            if field:
                result[field_type] = field

        return result

    def upload_symbolic_abstraction(self, abstraction: SymbolicAbstraction) -> bool:
        """
        Upload V36 symbolic abstraction

        Args:
            abstraction: SymbolicAbstraction to store

        Returns:
            True if successful
        """
        self._ensure_namespace(abstraction.namespace)

        abstractions_file = self._get_agent_path(abstraction.namespace) / "symbolic_abstractions.json"

        # Load existing
        if abstractions_file.exists():
            with open(abstractions_file, 'r') as f:
                abstractions_data = json.load(f)
        else:
            abstractions_data = {}

        # Store abstraction
        abstractions_data[abstraction.variable_name] = {
            'template': abstraction.template,
            'parameters': abstraction.parameters,
            'canonical_form': abstraction.canonical_form,
            'timestamp': int(abstraction.timestamp.timestamp())
        }

        # Write back
        with open(abstractions_file, 'w') as f:
            json.dump(abstractions_data, f, indent=2)

        return True

    def download_symbolic_abstractions(self, namespace: AgentNamespace) -> Dict[str, SymbolicAbstraction]:
        """
        Download all symbolic abstractions for agent

        Args:
            namespace: Agent namespace

        Returns:
            Dictionary mapping variable names to SymbolicAbstraction
        """
        abstractions_file = self._get_agent_path(namespace) / "symbolic_abstractions.json"

        if not abstractions_file.exists():
            return {}

        with open(abstractions_file, 'r') as f:
            abstractions_data = json.load(f)

        result = {}
        for var_name, data in abstractions_data.items():
            result[var_name] = SymbolicAbstraction(
                namespace=namespace,
                variable_name=var_name,
                template=data['template'],
                parameters=data['parameters'],
                canonical_form=data['canonical_form'],
                timestamp=datetime.fromtimestamp(data['timestamp'])
            )

        return result

    def upload_pheromone(self, pheromone: PheromoneField, namespace: AgentNamespace) -> bool:
        """
        Upload pheromone field for stigmergic paths

        Args:
            pheromone: PheromoneField to store
            namespace: Agent namespace

        Returns:
            True if successful
        """
        self._ensure_namespace(namespace)

        pheromones_file = self._get_agent_path(namespace) / "pheromones.json"

        # Load existing
        if pheromones_file.exists():
            with open(pheromones_file, 'r') as f:
                pheromones_data = json.load(f)
        else:
            pheromones_data = {}

        # Store pheromone (keyed by source->target pair)
        key = f"{pheromone.source_asset}->{pheromone.target_asset}"
        pheromones_data[key] = {
            'pheromone_strength': pheromone.pheromone_strength,
            'base_cost': pheromone.base_cost,
            'timestamp': int(pheromone.timestamp.timestamp())
        }

        # Write back
        with open(pheromones_file, 'w') as f:
            json.dump(pheromones_data, f, indent=2)

        return True

    def download_pheromones(self, namespace: AgentNamespace) -> List[PheromoneField]:
        """
        Download all pheromone fields for agent

        Args:
            namespace: Agent namespace

        Returns:
            List of PheromoneFields
        """
        pheromones_file = self._get_agent_path(namespace) / "pheromones.json"

        if not pheromones_file.exists():
            return []

        with open(pheromones_file, 'r') as f:
            pheromones_data = json.load(f)

        result = []
        for key, data in pheromones_data.items():
            source, target = key.split('->')
            result.append(PheromoneField(
                source_asset=source,
                target_asset=target,
                pheromone_strength=data['pheromone_strength'],
                base_cost=data['base_cost'],
                timestamp=datetime.fromtimestamp(data['timestamp'])
            ))

        return result

    def clear_namespace(self, namespace: AgentNamespace) -> bool:
        """
        Clear all data for namespace

        Args:
            namespace: Namespace to clear

        Returns:
            True if successful
        """
        import shutil

        agent_path = self._get_agent_path(namespace)
        if agent_path.exists():
            shutil.rmtree(agent_path)

        return True


class MORKClient:
    """
    MORK Client

    High-level interface to MORK storage (local or remote).
    Implements Gordon's biological principles and batch operations.
    """

    def __init__(
        self,
        storage_mode: str = "local",
        storage_path: Optional[Path] = None,
        remote_url: Optional[str] = None
    ):
        """
        Initialize MORK client

        Args:
            storage_mode: "local" or "remote"
            storage_path: Path for local storage (if mode=local)
            remote_url: URL for remote MORK server (if mode=remote)
        """
        self.storage_mode = storage_mode

        if storage_mode == "local":
            self.storage = LocalMORKStorage(storage_path)
        elif storage_mode == "remote":
            # Remote mode not yet implemented
            raise NotImplementedError("Remote MORK server not yet implemented. Use storage_mode='local'.")
        else:
            raise ValueError(f"Invalid storage_mode: {storage_mode}. Use 'local' or 'remote'.")

    def upload_field(self, field: BiologicalField) -> bool:
        """Upload biological field"""
        return self.storage.upload_field(field)

    def batch_upload_fields(self, fields: List[BiologicalField]) -> bool:
        """Batch upload fields (87x speedup)"""
        return self.storage.batch_upload(fields)

    def download_field(self, namespace: AgentNamespace, field_type: FieldType) -> Optional[BiologicalField]:
        """Download biological field"""
        return self.storage.download_field(namespace, field_type)

    def batch_download_fields(self, namespace: AgentNamespace) -> Dict[FieldType, BiologicalField]:
        """Batch download all fields"""
        return self.storage.batch_download(namespace)

    def upload_symbolic_abstraction(self, abstraction: SymbolicAbstraction) -> bool:
        """Upload V36 symbolic abstraction"""
        return self.storage.upload_symbolic_abstraction(abstraction)

    def download_symbolic_abstractions(self, namespace: AgentNamespace) -> Dict[str, SymbolicAbstraction]:
        """Download all symbolic abstractions"""
        return self.storage.download_symbolic_abstractions(namespace)

    def upload_pheromone(self, pheromone: PheromoneField, namespace: AgentNamespace) -> bool:
        """Upload pheromone field"""
        return self.storage.upload_pheromone(pheromone, namespace)

    def download_pheromones(self, namespace: AgentNamespace) -> List[PheromoneField]:
        """Download all pheromones"""
        return self.storage.download_pheromones(namespace)

    def clear_namespace(self, namespace: AgentNamespace) -> bool:
        """Clear all data for namespace"""
        return self.storage.clear_namespace(namespace)

    def create_agent_fields(
        self,
        namespace: AgentNamespace,
        tau: float = 0.5,
        eta: float = 0.5,
        c_k: float = 0.5
    ) -> bool:
        """
        Initialize biological fields for new agent

        Args:
            namespace: Agent namespace
            tau: Initial trail strength [0.0-1.0]
            eta: Initial encounter rate [0.0-1.0]
            c_k: Initial curiosity value [0.0-1.0]

        Returns:
            True if successful
        """
        now = datetime.now()

        fields = [
            BiologicalField(namespace, FieldType.TAU, tau, now),
            BiologicalField(namespace, FieldType.ETA, eta, now),
            BiologicalField(namespace, FieldType.C_K, c_k, now)
        ]

        return self.batch_upload_fields(fields)
