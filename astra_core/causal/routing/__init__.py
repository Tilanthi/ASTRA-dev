"""
MoE-inspired Routing Module for STAN_IX_ASTRO

This module implements Mixture-of-Experts (MoE) style routing for dynamic
capability selection and conditional computation.

Key components:
- MoECapabilityRouter: Routes tasks to relevant specialized experts
- ConditionalComputationEngine: Orchestrates execution with routing
"""

from .moe_router import (
    MoECapabilityRouter,
    ConditionalComputationEngine,
    TaskType,
    Expert,
    RoutingDecision,
    create_moe_router,
    create_conditional_engine,
)

__all__ = [
    'MoECapabilityRouter',
    'ConditionalComputationEngine',
    'TaskType',
    'Expert',
    'RoutingDecision',
    'create_moe_router',
    'create_conditional_engine',
]
