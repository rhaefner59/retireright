# core/taxes_states/generic.py
# Fallback calculators and a tiny factory for flat state+local rates.

def compute_state_tax(income: float) -> float:
    """
    Default generic fallback: 0% state tax.
    Change to income * 0.05 for a quick 5% if desired.
    """
    return 0.0


def make_generic_flat(state_rate_pct: float = 0.0, local_rate_pct: float = 0.0, deduction: float = 0.0):
    """
    Factory that returns a function computing flat state+local tax on (income - deduction).
    state_rate_pct/local_rate_pct are in PERCENT (e.g., 5.0 for 5%).
    """
    state_rate = float(state_rate_pct) / 100.0
    local_rate = float(local_rate_pct) / 100.0
    ded = float(deduction)

    def _fn(income: float) -> float:
        taxable = max(0.0, float(income) - ded)
        return taxable * (state_rate + local_rate)

    return _fn
