import pandas as pd
from core.schema import Profile, Inputs, Assumptions
from core.rmd import rmd_start_age_from_dob, rmd_uniform
from core.social_security import ss_annual_at_claim, compute_ss_for_year
from core.taxes_states.md import MarylandGeneric

# Minimal registry (extend later)
REGISTRY = {"MD": MarylandGeneric}

def run(profile: Profile, inputs: Inputs, assumptions: Assumptions) -> dict:
    years = list(range(int(inputs.start_year), int(inputs.end_year)+1))

    # Ages by year
    py = int(profile.primary_dob.split("-")[0])
    sy = int(profile.spouse_dob.split("-")[0]) if profile.spouse_dob else None

    # RMD ages
    rmd_age_primary = rmd_start_age_from_dob(profile.primary_dob)
    rmd_age_spouse  = rmd_start_age_from_dob(profile.spouse_dob) if profile.spouse_dob else None

    # SS bases
    base_you = ss_annual_at_claim(inputs.social_security.get("fra_monthly_primary",0.0), int(inputs.social_security.get("primary_age",70)))
    base_sp  = ss_annual_at_claim(inputs.social_security.get("fra_monthly_spouse",0.0), int(inputs.social_security.get("spouse_age",65))) if profile.spouse_dob else 0.0
    cola     = float(inputs.social_security.get("cola", 0.02))

    first_year_you = inputs.start_year + (int(inputs.social_security.get("primary_age",70)) - (inputs.start_year - py))
    first_year_sp  = inputs.start_year + (int(inputs.social_security.get("spouse_age",65)) - (inputs.start_year - sy)) if profile.spouse_dob else 9999

    month_you = int(inputs.social_security.get("primary_month",1))
    month_sp  = int(inputs.social_security.get("spouse_month",9))

    # Balances
    your_trad = float(inputs.balances.get("trad_primary",0))
    wife_trad = float(inputs.balances.get("trad_spouse",0))

    rows = []
    for i, yr in enumerate(years):
        age_you = (inputs.start_year - py) + i
        age_sp  = (inputs.start_year - sy) + i if profile.spouse_dob else None

        # RMDs when eligible
        rmd_your = rmd_uniform(age_you, your_trad) if age_you >= rmd_age_primary else 0.0
        rmd_sp   = rmd_uniform(age_sp, wife_trad) if (profile.spouse_dob and age_sp is not None and rmd_age_spouse and age_sp >= rmd_age_spouse) else 0.0

        # SS with first-year proration
        ss_you = compute_ss_for_year(yr, first_year_you, month_you, base_you, cola)
        ss_sp  = compute_ss_for_year(yr, first_year_sp,  month_sp,  base_sp,  cola) if profile.spouse_dob else 0.0

        # Light AGI proxy for demo
        provisional = rmd_your + rmd_sp + 0.5*(ss_you+ss_sp)
        ss_taxable = min(0.85*(ss_you+ss_sp), max(0.0, provisional-32000) * 0.5 + max(0.0, provisional-44000) * 0.35)
        agi_proxy = rmd_your + rmd_sp + ss_taxable

        # State tax demo (MD)
        state_tax = 0.0
        if profile.state == "MD":
            calc = REGISTRY["MD"]()
            out = calc.compute(
                year=yr, ages=(age_you, age_sp or 0), agi=agi_proxy,
                taxable_fed=max(0.0,agi_proxy-31500), county=profile.county,
                filing_status=profile.filing_status
            )
            state_tax = out["tax"]

        rows.append({
            "Year": yr,
            "Your Age": age_you,
            "Spouse Age": age_sp,
            "RMD (Your Trad)": round(rmd_your,0),
            "RMD (Spouse Trad)": round(rmd_sp,0),
            "SS Total": round(ss_you+ss_sp,0),
            "AGI (proxy)": round(agi_proxy,0),
            "State Tax (demo)": round(state_tax,0)
        })

        # Roll forward (simple growth demo)
        your_trad = your_trad - rmd_your + your_trad*inputs.returns.get("trad_primary",0.0)
        wife_trad = wife_trad - rmd_sp   + wife_trad*inputs.returns.get("trad_spouse",0.0)

    df = pd.DataFrame(rows)
    return {"table": df}