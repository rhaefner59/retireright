# core/rmd.py
# Helpers for RMD start ages and Uniform Lifetime divisors (SECURE 2.0)

from typing import Optional

# SECURE 2.0 starting ages (simplified):
# - Born 1951–1959  -> first RMD age 73
# - Born 1960 or later -> first RMD age 75
# - Born 1950 or earlier -> 72 (legacy rule; included for completeness)
def rmd_start_age_from_dob(dob: str) -> int:
    """
    dob format: 'YYYY-MM-DD' (only the year is used)
    Returns the age at which RMDs begin under SECURE 2.0 rules.
    """
    year = int(dob.split("-")[0])
    if year >= 1960:
        return 75
    if 1951 <= year <= 1959:
        return 73
    return 72


# IRS Uniform Lifetime Table (selected ages). Extend as needed.
UNIFORM_DIVISORS = {
    73: 26.5, 74: 25.5, 75: 24.7, 76: 23.8, 77: 22.9, 78: 22.0, 79: 21.2, 80: 20.3,
    81: 19.5, 82: 18.7, 83: 17.9, 84: 17.1, 85: 16.3, 86: 15.6, 87: 14.8, 88: 14.1,
    89: 13.4, 90: 12.7, 91: 12.0, 92: 11.4, 93: 10.8, 94: 10.1, 95: 9.5, 96: 8.9,
    97: 8.4, 98: 7.8, 99: 7.3, 100: 6.8
}


def rmd_uniform(amount_age: int, balance: float) -> float:
    """
    Simple RMD: balance / divisor for the given age.
    If age not present or balance <= 0, returns 0.
    """
    if balance <= 0:
        return 0.0
    d = UNIFORM_DIVISORS.get(int(amount_age))
    if d is None:
        return 0.0
    return balance / d


def year_to_age(birth_year: int, start_year: int, current_year: int) -> int:
    """
    Compute age in a given current_year given birth_year and the start_year reference.
    Assumes we treat ages as of year-end (coarse, adequate for annual modeling).
    """
    # If you track DOB months, adjust here; we keep it annual/simplified.
    base_age_at_start = start_year - birth_year
    return base_age_at_start + (current_year - start_year)


def maybe_rmd(age: int, balance: float, rmd_start_age: int) -> float:
    """
    Returns the RMD amount if age >= rmd_start_age, else 0.
    """
    if age < rmd_start_age:
        return 0.0
    return rmd_uniform(age, balance)
