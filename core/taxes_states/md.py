# core/taxes_states/md.py
# Maryland placeholder: flat 4.75% of state-taxable income.
# (We’ll reintroduce the full data-driven logic later.)

def compute_state_tax(income: float) -> float:
    """
    Maryland-specific placeholder: flat 4.75%.
    `income` should be the state-taxable base you're passing (e.g., AGI proxy for now).
    """
    return max(0.0, income) * 0.0475
