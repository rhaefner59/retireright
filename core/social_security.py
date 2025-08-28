# core/social_security.py
# Helpers for Social Security claiming ages, proration, and COLA adjustments

FRA = 67  # Full Retirement Age (simplified constant)


def ss_annual_at_claim(fra_monthly: float, claim_age: int) -> float:
    """
    Compute the annual Social Security benefit at claim age, based on FRA monthly benefit.
    - FRA (67): baseline
    - Delay up to 3 years (to 70): +8% per year
    - Early claim down to 62: ~6% reduction per year
    Returns annual benefit (12 * monthly * adjustment).
    """
    if fra_monthly <= 0 or claim_age < 62:
        return 0.0

    if claim_age >= FRA:
        years = min(claim_age - FRA, 3)
        factor = 1.0 + 0.08 * years
    else:
        years = FRA - claim_age
        factor = max(0.70, 1.0 - 0.06 * years)

    return fra_monthly * 12.0 * factor


def compute_ss_for_year(year: int, first_year: int, start_month: int,
                        base_annual: float, cola: float) -> float:
    """
    Returns the SS benefit paid in year `year`.

    Rules:
    - If year < first_year: 0
    - If year == first_year: prorated by months = 13 - start_month
      (e.g. claim in September -> 4 months paid)
    - If year > first_year: full annual, adjusted by COLA compounded
    """
    if base_annual <= 0:
        return 0.0
    if year < first_year:
        return 0.0

    years_since_claim = max(0, year - first_year)
    full_year_amount = base_annual * ((1.0 + cola) ** years_since_claim)

    if year == first_year:
        months = max(0, min(12, 13 - int(start_month)))
        return full_year_amount * (months / 12.0)

    return full_year_amount
