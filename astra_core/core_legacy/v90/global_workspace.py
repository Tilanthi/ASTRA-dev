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
Global Workspace for V90
=======================

Simulates global workspace theory of consciousness.

Multiple specialized modules broadcast to a global consciousness
that becomes available for global processing.
"""

import time
import numpy as np
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class ConsciousContent:
    """Content that can enter conscious awareness"""
    def __init__(self, content: str, attention_level: float = 1.0,
                 modality: str = "cognitive", emotional_valence: float = 0.0):
        self.content = content
        self.attention_level = attention_level
        self.modality = modality
        self.emotional_valence = emotional_valence
        self.timestamp = time.time()
        self.broadcasters = []


class GlobalWorkspace:
    """Simulates the global workspace of consciousness"""

    def __init__(self):
        self.conscious_contents = []
        self.workspace_capacity = 7  # Miller's number
        self.attention_spotlight = None
        self.conscious_stream = []

    def broadcast(self, content: ConsciousContent) -> bool:
        """Broadcast content to global workspace"""
        # Check if content enters consciousness
        if self._enters_consciousness(content):
            self.conscious_contents.append(content)
            self._update_workspace()
            return True
        return False

    def _enters_consciousness(self, content: ConsciousContent) -> bool:
        """Determine if content enters consciousness"""
        # High attention content always enters
        if content.attention_level > 0.8:
            return True

        # Emotionally salient content
        if abs(content.emotional_valence) > 0.7:
            return True

        # Random chance for moderate attention
        if content.attention_level > 0.5 and np.random.random() < 0.3:
            return True

        return False

    def _update_workspace(self):
        """Update the global workspace state"""
        # Keep only conscious contents
        self.conscious_contents = [
            c for c in self.conscious_contents
            if time.time() - c.timestamp < 5.0  # 5 second consciousness duration
        ]

        # Update attention spotlight
        if self.conscious_contents:
            self.attention_spotlight = max(
                self.conscious_contents,
                key=lambda c: c.attention_level
            )

        # Update conscious stream
        self.conscious_stream.append({
            'timestamp': time.time(),
            'contents': [c.content for c in self.conscious_contents],
            'spotlight': self.attention_spotlight.content if self.attention_spotlight else None
        })

        # Keep stream bounded
        if len(self.conscious_stream) > 100:
            self.conscious_stream = self.conscious_stream[-50:]

    def get_current_conscious_state(self) -> Dict[str, Any]:
        """Get current state of consciousness"""
        return {
            'contents_count': len(self.conscious_contents),
            'spotlight': self.attention_spotlight.content if self.attention_spotlight else None,
            'stream_length': len(self.conscious_stream),
            'modalities': list(set(c.modality for c in self.conscious_contents))
        }