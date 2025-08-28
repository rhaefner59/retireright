# core/taxes_states/registry.py
# Simple registry that returns a state tax function.
from . import generic
from . import md  # Maryland

REGISTRY = {
    "MD": md.compute_state_tax,   # MD uses a real function (we'll expand later)
}

def get_state_calculator(state_code: str, state_rate: float | None = None, local_rate: float | None = None):
    """
    Return a state tax function.
    - If we have a dedicated module (e.g., MD), return that function.
    - Otherwise return a flat-rate function using the provided state/local percentages.
    """
    sc = (state_code or "").upper()
    if sc in REGISTRY:
        return REGISTRY[sc]

    # Fallback: generic flat function using UI-provided rates (percent values)
    return generic.make_generic_flat(state_rate or 0.0, local_rate or 0.0, deduction=0.0)
