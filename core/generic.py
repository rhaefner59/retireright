# core/taxes_states/generic.py

def compute_state_tax(income: float) -> float:
    """
    Generic fallback state tax calculator.
    For now: simple flat 5% tax on taxable income.
    Later: extend with state-specific logic.
    """
    return income * 0.05
