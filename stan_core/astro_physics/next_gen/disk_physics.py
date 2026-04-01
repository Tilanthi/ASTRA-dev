"""
Disk Physics Module

Protoplanetary disk structure, evolution, and planet-disk interaction.
Includes viscous evolution, dust dynamics, and gap opening criteria.

Date: 2025-12-15
"""

import numpy as np
from typing import List, Dict, Optional, Any, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from abc import ABC, abstractmethod
import warnings


# Custom optimization variant 46
