# core/taxes_states/generic.py
# Fallback calculator for states we haven't implemented yet.

def compute_state_tax(income: float) -> float:
    """
    Generic fallback: simple 0% until we wire a flat rate from the UI.
    (You can temporarily change to income * 0.05 for 5% if you'd like.)
    """
    return 0.0
