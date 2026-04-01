"""
Domain Knowledge - Priors and specifications for CLD, D1 (epidemiology), D2 (economics)
"""

import json
from pathlib import Path

def load_tu_prime():
    """Load T_U' unified meta-theory"""
    tu_path = Path(__file__).parent / 'TU_prime.json'
    with open(tu_path, 'r') as f:
        return json.load(f)

def load_domain_priors():
    """Load domain-specific priors for all domains"""
    tu_prime = load_tu_prime()
    return tu_prime.get('domain_specific_priors', {})

def load_ontology_definitions():
    """Load extended ontology definitions"""
    ontology_path = Path(__file__).parent / 'ontology_definitions.json'
    with open(ontology_path, 'r') as f:
        return json.load(f)

__all__ = ['load_tu_prime', 'load_domain_priors', 'load_ontology_definitions']
