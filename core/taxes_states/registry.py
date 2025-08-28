# core/taxes_states/registry.py
# Registry of state-specific tax calculators

from . import generic
from . import md

REGISTRY = {
    "GENERIC": generic,
    "MD": md,
}


def get_state_calculator(state_code: str):
    """
    Look up a state calculator module by its code.
    Falls back to GENERIC if not found.
    """
    mod = REGISTRY.get(state_code.upper())
    if not mod:
        mod = REGISTRY["GENERIC"]
    return mod
