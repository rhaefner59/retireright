# core/projection.py
# Master Projection engine (years table + dynamic account columns + taxes)

from __future__ import annotations
import pandas as pd
from typing import Dict, Any, List, Optional

from .schema import Profile, Inputs, Assumptions
from .rmd import rmd_start_age_from_dob, year_to_age
from .social_security import ss_annual_at_claim, compute_ss_for_year
from .taxes_states.registry import get_state_calculator


# ---------------------------
# Simple Federal Tax (ordinary only, for now)
# ---------------------------
def fed_tax_piecewise_ordinary(
    taxable: float,
    b12: float = 100_000,
    b22: float = 190_750,
    b24: float = 364_200,
    b32: float = 462_500,
    b35: float = 693_750,
) -> float:
    if taxable <= 0:
        return 0.0
    tax = 0.0
    bands = [
        (b12, 0.12),
        (b22, 0.22),
        (b24, 0.24),
        (b32, 0.32),
        (b35, 0.35),
        (float("inf"), 0.37),
    ]
    prev_top, rem = 0.0, taxable
    for top, rate in bands:
        span = max(0.0, min(rem, top - prev_top))
        if span > 0:
            tax += span * rate
            rem -= span
            prev_top = top
        if rem <= 0:
            break
    return max(0.0, tax)


def ss_taxable_mfj(ss_total: float, provisional: float, base: float = 32_000, adj: float = 44_000) -> float:
    """Simplified 0/50/85% approach."""
    if ss_total <= 0:
        return 0.0
    part1 = max(0.0, min(provisional - base, max(0.0, adj - base))) * 0.5
    part2 = max(0.0, provisional - adj) * 0.85
    return min(0.85 * ss_total, part1 + part2)


# ---------------------------
# Projection.run
# ---------------------------
def run(profile: Profile, inputs: Inputs, assumptions: Assumptions,
        state_rate: float | None = None, local_rate: float | None = None,
        senior_bill_on: bool = True, round_whole: bool = True) -> Dict[str, Any]:

    """
    Returns: {"table": DataFrame}
    Columns include:
      - Year, Ages, SS Total
      - Account balances (one column per included account)
      - Federal Tax, State Tax, Total Tax
    """

    years: List[int] = list(range(int(inputs.start_year), int(inputs.end_year) + 1))

    # Ages by year
    py = int(profile.primary_dob.split("-")[0])
    sy = int(profile.spouse_dob.split("-")[0]) if profile.spouse_dob else None

    # Social Security bases
    base_you = ss_annual_at_claim(inputs.social_security.get("fra_monthly_primary", 0.0),
                                  int(inputs.social_security.get("primary_age", 70)))
    base_sp  = ss_annual_at_claim(inputs.social_security.get("fra_monthly_spouse", 0.0),
                                  int(inputs.social_security.get("spouse_age", 65))) if profile.spouse_dob else 0.0
    cola     = float(inputs.social_security.get("cola", 0.02))

    first_year_you = int(inputs.start_year + (int(inputs.social_security.get("primary_age", 70)) - (inputs.start_year - py)))
    first_year_sp  = int(inputs.start_year + (int(inputs.social_security.get("spouse_age", 65))  - (inputs.start_year - sy))) if profile.spouse_dob else 9999

    you_month = int(inputs.social_security.get("primary_month", 1))
    sp_month  = int(inputs.social_security.get("spouse_month", 9))

    # Accounts (balances roll forward with growth only for now)
    acct_names: List[str] = list(inputs.balances.keys())
    balances: Dict[str, float] = {k: float(v) for k, v in inputs.balances.items()}
    returns: Dict[str, float]  = {k: float(v) for k, v in inputs.returns.items()}

    # State tax function
    state_code = (profile.state or "").upper()
    state_fn = get_state_calculator(state_code)

    rows: List[Dict[str, Any]] = []

    for yr in years:
        # Ages
        age_you = year_to_age(py, int(inputs.start_year), yr)
        age_sp  = year_to_age(sy, int(inputs.start_year), yr) if profile.spouse_dob else None

        # Social Security this year
        ss_you = compute_ss_for_year(yr, first_year_you, you_month, base_you, cola)
        ss_sp  = compute_ss_for_year(yr, first_year_sp,  sp_month,  base_sp,  cola) if profile.spouse_dob else 0.0
        ss_total = ss_you + ss_sp

        # AGI proxy (only SS taxable for now)
        provisional = 0.5 * ss_total
        ss_taxable  = ss_taxable_mfj(ss_total, provisional)
        agi_proxy   = ss_taxable

        # Federal Tax
        fed_tax = fed_tax_piecewise_ordinary(agi_proxy)

        # State Tax (function-based now)
        state_tax = float(state_fn(agi_proxy))
        local_tax = 0.0
        total_tax = fed_tax + state_tax + local_tax

        # Roll forward accounts
        end_cols: Dict[str, float] = {}
        for nm in acct_names:
            bal = balances.get(nm, 0.0)
            ret = returns.get(nm, 0.0)
            end_bal = bal * (1.0 + ret)
            end_cols[nm] = round(end_bal, 2)
            balances[nm] = end_bal

        row = {
            "Year": yr,
            "Your Age": age_you,
            "Spouse Age": age_sp,
            "Social Security": round(ss_total, 2),
            "Federal Tax": round(fed_tax, 2),
            "State Tax": round(state_tax, 2),
            "Total Tax": round(total_tax, 2),
        }
        row.update(end_cols)
        rows.append(row)

    df = pd.DataFrame(rows)

    # Order: core cols first, then account cols
    core_cols = ["Year", "Your Age", "Spouse Age", "Social Security", "Federal Tax", "State Tax", "Total Tax"]
    acct_cols = [c for c in df.columns if c not in core_cols]
    df = df[core_cols + acct_cols]

    return {"table": df}
