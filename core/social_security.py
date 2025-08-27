FRA = 67

def ss_annual_at_claim(fra_monthly: float, claim_age: int) -> float:
    if fra_monthly <= 0 or claim_age < 62:
        return 0.0
    if claim_age >= FRA:
        years = min(claim_age - FRA, 3)
        factor = 1.0 + 0.08*years
    else:
        years = FRA - claim_age
        factor = max(0.70, 1.0 - 0.06*years)
    return fra_monthly*12.0*factor

def compute_ss_for_year(year:int, first_year:int, start_month:int, base_annual:float, cola:float) -> float:
    if base_annual <= 0:
        return 0.0
    if year < first_year:
        return 0.0
    years_since = max(0, year-first_year)
    full = base_annual * ((1.0+cola)**years_since)
    if year == first_year:
        months = max(0, min(12, 13 - int(start_month)))
        return full * (months/12.0)
    return full