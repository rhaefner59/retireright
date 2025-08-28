# core/projection.py
from __future__ import annotations
import pandas as pd
from typing import Dict, Any, List, Tuple

from .schema import Profile, Inputs, Assumptions
from .rmd import year_to_age
from .social_security import ss_annual_at_claim, compute_ss_for_year
from .taxes_states.registry import get_state_calculator

# -------- Federal helpers (demo bands) --------
BRACKETS_MFJ = [
    (100_000, 0.12),
    (190_750, 0.22),
    (364_200, 0.24),
    (462_500, 0.32),
    (693_750, 0.35),
    (float("inf"), 0.37),
]
BRACKETS_SINGLE = [
    (47_000, 0.12),
    (95_000, 0.22),
    (182_100, 0.24),
    (231_250, 0.32),
    (578_100, 0.35),
    (float("inf"), 0.37),
]
STD_AUTO = {"MFJ": 31_500, "MFS": 15_750, "HOH": 22_500, "SINGLE": 15_750}
AGE_ADD = 1_600  # per 65+ taxpayer

def pick_brackets(fs: str):
    fs = (fs or "MFJ").upper()
    if fs in ("SINGLE","HOH","MFS"):
        return BRACKETS_SINGLE
    return BRACKETS_MFJ

def fed_tax_piecewise_ordinary(taxable: float, filing_status: str) -> Tuple[float, str]:
    if taxable <= 0:
        return 0.0, "0%"
    tax = 0.0
    marginal = "0%"
    prev_top, rem = 0.0, taxable
    for top, rate in pick_brackets(filing_status):
        span = max(0.0, min(rem, top - prev_top))
        if span > 0:
            tax += span * rate
            rem -= span
            prev_top = top
            marginal = f"{int(rate*100)}%"
        if rem <= 0:
            break
    return max(0.0, tax), marginal

def ss_taxable(ss_total: float, provisional: float, filing_status: str) -> float:
    if ss_total <= 0:
        return 0.0
    if filing_status.upper() == "MFJ":
        base, adj = 32_000, 44_000
    else:
        base, adj = 25_000, 34_000
    part1 = max(0.0, min(provisional - base, max(0.0, adj - base))) * 0.5
    part2 = max(0.0, provisional - adj) * 0.85
    return min(0.85 * ss_total, part1 + part2)

# -------- Engine --------
def run(profile: Profile, inputs: Inputs, assumptions: Assumptions,
        state_rate: float | None = None, local_rate: float | None = None,
        senior_bill_on: bool = True, round_whole: bool = True,
        std_override: float | None = None,
        strategy: Dict[str, Any] | None = None) -> Dict[str, Any]:

    years = list(range(int(inputs.start_year), int(inputs.end_year) + 1))
    py = int(profile.primary_dob.split("-")[0])
    sy = int(profile.spouse_dob.split("-")[0]) if profile.spouse_dob else None

    # SS bases (FRA monthly at 67 → annual at claim)
    base_you = ss_annual_at_claim(inputs.social_security.get("fra_monthly_primary", 0.0),
                                  int(inputs.social_security.get("primary_age", 70)))
    base_sp  = ss_annual_at_claim(inputs.social_security.get("fra_monthly_spouse", 0.0),
                                  int(inputs.social_security.get("spouse_age", 65))) if profile.spouse_dob else 0.0
    cola     = float(inputs.social_security.get("cola", 0.02))

    first_year_you = int(inputs.start_year + (int(inputs.social_security.get("primary_age", 70)) - (inputs.start_year - py)))
    first_year_sp  = int(inputs.start_year + (int(inputs.social_security.get("spouse_age", 65))  - (inputs.start_year - sy))) if profile.spouse_dob else 9999
    you_month = int(inputs.social_security.get("primary_month", 1))
    sp_month  = int(inputs.social_security.get("spouse_month", 9))

    acct_names = list(inputs.balances.keys())
    balances   = {k: float(v) for k, v in inputs.balances.items()}
    returns    = {k: float(v) for k, v in inputs.returns.items()}

    # map meta (withdrawals + brokerage settings)
    meta = {}
    for item in (inputs.withdrawals_plan or []):
        nm = str(item.get("name",""))
        meta[nm] = {
            "annual": float(item.get("annual", 0.0)),
            "tax_class": str(item.get("tax_class","cash")).lower(),
            "div_yield_pct": float(item.get("div_yield_pct", 0.0)),
            "realize_gains_pct": float(item.get("realize_gains_pct", 0.0)),
        }

    # State tax function (function-based; for non-MD we feed rates)
    state_fn = get_state_calculator((profile.state or "").upper(), state_rate=state_rate, local_rate=local_rate)

    # Strategy (weights) or manual
    strategy = strategy or {"mode":"manual","weights":{},"total_withdraw":0.0}
    mode = strategy.get("mode","manual")

    rows = []
    for yr in years:
        age_you = year_to_age(py, int(inputs.start_year), yr)
        age_sp  = year_to_age(sy, int(inputs.start_year), yr) if profile.spouse_dob else None

        # Social Security
        ss_you = compute_ss_for_year(yr, first_year_you, you_month, base_you, cola)
        ss_sp  = compute_ss_for_year(yr, first_year_sp,  sp_month,  base_sp,  cola) if profile.spouse_dob else 0.0
        ss_total = ss_you + ss_sp

        # Determine withdrawals this year
        wd_map = {}  # {name: amount}
        if mode == "manual":
            for nm in acct_names:
                wd_map[nm] = float(meta.get(nm, {}).get("annual", 0.0))
        else:
            # weights mode: split strategy["total_withdraw"] across tax classes
            want_total = float(strategy.get("total_withdraw", 0.0))
            weights = strategy.get("weights", {})
            by_class_target = {
                "pre_tax":  want_total * float(weights.get("pre_tax", 0.0)),
                "roth":     want_total * float(weights.get("roth", 0.0)),
                "brokerage":want_total * float(weights.get("brokerage", 0.0)),
                "cash":     want_total * float(weights.get("cash", 0.0)),
            }
            # build list of accounts per class
            class_to_accounts = {"pre_tax":[], "roth":[], "brokerage":[], "cash":[]}
            for nm in acct_names:
                tc = str(meta.get(nm, {}).get("tax_class","cash")).lower()
                if tc in class_to_accounts:
                    class_to_accounts[tc].append(nm)
            # allocate per class proportional to available balances
            wd_map = {nm: 0.0 for nm in acct_names}
            for tc, target in by_class_target.items():
                names = [n for n in class_to_accounts[tc] if balances.get(n,0.0) > 0]
                if not names or target <= 0:
                    continue
                tot_bal = sum(balances[n] for n in names)
                if tot_bal <= 0:
                    continue
                for n in names:
                    share = balances[n] / tot_bal
                    wd_map[n] += min(balances[n], target * share)

        # Apply withdrawals + brokerage flows (before growth)
        ordinary_income_from_wd = 0.0
        div_income = 0.0
        ltcg_income = 0.0
        end_cols = {}

        for nm in acct_names:
            bal0 = balances.get(nm, 0.0)
            ret  = returns.get(nm, 0.0)
            m    = meta.get(nm, {"annual":0.0,"tax_class":"cash","div_yield_pct":0.0,"realize_gains_pct":0.0})
            tax_class  = str(m.get("tax_class","cash")).lower()
            div_yield  = float(m.get("div_yield_pct", 0.0)) / 100.0
            realize_gp = float(m.get("realize_gains_pct", 0.0)) / 100.0

            wd_req = max(0.0, float(wd_map.get(nm, 0.0)))
            wd_taken = min(bal0, wd_req)
            bal_after_wd = max(0.0, bal0 - wd_taken)

            # tax character
            if tax_class == "pre_tax":
                ordinary_income_from_wd += wd_taken
            # roth/hsa/cash/brokerage wd not taxable themselves here

            if tax_class == "brokerage":
                div = bal_after_wd * div_yield if div_yield > 0 else 0.0
                div_income += div
                growth = bal_after_wd * ret
                realized = max(0.0, growth) * realize_gp if realize_gp > 0 else 0.0
                ltcg_income += realized
                end_bal = max(0.0, bal_after_wd + growth - realized)
            else:
                end_bal = bal_after_wd * (1.0 + ret)

            end_cols[nm] = end_bal
            balances[nm] = end_bal

        # Income buckets
        ordinary_income = ordinary_income_from_wd + div_income
        provisional     = ordinary_income + 0.5 * ss_total
        ss_taxable_amt  = ss_taxable(ss_total, provisional, profile.filing_status)
        total_income    = ordinary_income + ss_total + ltcg_income

        # Standard deduction
        if std_override is not None:
            std = float(std_override)
        else:
            base_std = STD_AUTO.get(profile.filing_status.upper(), STD_AUTO["MFJ"])
            num65 = (1 if age_you>=65 else 0) + (1 if (age_sp and age_sp>=65) else 0)
            std = base_std + num65*AGE_ADD

        ordinary_tax_base = max(0.0, (ordinary_income + ss_taxable_amt) - std)
        taxable_total     = max(0.0, ordinary_income + ss_taxable_amt + ltcg_income - std)
        ltcg_tax_base     = max(0.0, taxable_total - ordinary_tax_base)

        fed_ord_tax, marginal = fed_tax_piecewise_ordinary(ordinary_tax_base, profile.filing_status)
        fed_ltcg_tax = ltcg_tax_base * 0.15  # simple placeholder
        fed_tax = fed_ord_tax + fed_ltcg_tax

        state_tax = float(state_fn(taxable_total))
        total_tax = fed_tax + state_tax

        row = {
            "Year": yr,
            "Your Age": age_you,
            "Spouse Age": age_sp,
            "Social Security": round(ss_total, 2),
            "Income (Ordinary)": round(ordinary_income, 2),
            "LTCG Income": round(ltcg_income, 2),
            "Total Income": round(total_income, 2),
            "Standard Deduction": round(std, 2),
            "Taxable Income (Fed)": round(taxable_total, 2),
            "Marginal Bracket": marginal,
            "Federal Tax": round(fed_tax, 2),
            "State Tax": round(state_tax, 2),
            "Total Tax": round(total_tax, 2),
            "Effective Tax Rate": round((total_tax / total_income) if total_income > 0 else 0.0, 4),
        }
        for k, v in end_cols.items():
            row[k] = round(v, 2)
        rows.append(row)

    df = pd.DataFrame(rows)
    core_cols = [
        "Year","Your Age","Spouse Age","Social Security",
        "Income (Ordinary)","LTCG Income","Total Income",
        "Standard Deduction","Taxable Income (Fed)","Marginal Bracket",
        "Federal Tax","State Tax","Total Tax","Effective Tax Rate",
    ]
    acct_cols = [c for c in df.columns if c not in core_cols]
    df = df[core_cols + acct_cols]

    if round_whole:
        num_cols = df.select_dtypes(include=["float64","float32","int64","int32"]).columns
        df[num_cols] = df[num_cols].round(0)

    return {"table": df}
