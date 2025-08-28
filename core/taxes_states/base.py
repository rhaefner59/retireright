# core/taxes_states/base.py
# Generic helpers for state + local tax calculations

def state_taxable_income(agi: float, state_deduction: float = 0.0) -> float:
    """
    Compute taxable income for a state, after state-level deductions.
    """
    return max(0.0, agi - state_deduction)


def flat_state_local_tax(taxable: float, state_rate: float, local_rate: float = 0.0) -> float:
    """
    Apply a flat state + local effective tax rate to taxable income.
    Rates are percentages (e.g., 4.75 for 4.75%).
    """
    eff = (state_rate + local_rate) / 100.0
    return max(0.0, taxable) * eff
