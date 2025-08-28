# core/taxes_states/registry.py
# Simple registry that returns a state tax function.

from . import generic
from . import md  # Maryland

# Map state codes to the function that computes that state's tax.
REGISTRY = {
    "MD": md.compute_state_tax,
}

def get_state_calculator(state_code: str):
    """
    Return the state-specific tax function if present;
    otherwise fall back to the generic calculator.
    """
    sc = (state_code or "").upper()
    return REGISTRY.get(sc, generic.compute_state_tax)
