import streamlit as st
from datetime import date
from core.schema import Profile, Inputs, Assumptions
from core.projection import run

st.set_page_config(page_title="RetireRight — Planner", layout="wide")
st.title("RetireRight — Retirement Planner (Starter)")

# ----------- Profile -----------
st.header("1) Profile")
colp1, colp2, colp3 = st.columns(3)
with colp1:
    filing = st.selectbox("Filing status", ["MFJ","Single","MFS","HOH"], index=0)
with colp2:
    primary_dob = st.date_input("Primary DOB", value=date(1959,12,31), format="YYYY-MM-DD")
with colp3:
    spouse_dob_enable = st.checkbox("Add spouse", value=True)
spouse_dob = None
if spouse_dob_enable:
    spouse_dob = st.date_input("Spouse DOB", value=date(1961,9,9), format="YYYY-MM-DD")

colp4, colp5 = st.columns(2)
with colp4:
    state = st.selectbox(
        "State",
        ["AL","AK","AZ","AR","CA","CO","CT","DE","DC","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"],
        index=20
    )
with colp5:
    county = st.selectbox("County / Locality (demo for MD)", ["—","Anne Arundel","Baltimore County","Montgomery"]) if state=="MD" else None

profile = Profile(
    filing_status=filing,
    primary_dob=str(primary_dob),
    spouse_dob=str(spouse_dob) if spouse_dob else None,
    state=state,
    county=None if county in ("—", None) else county,
)

# ----------- Inputs -----------
st.header("2) Inputs")
coli1, coli2, coli3 = st.columns(3)
with coli1:
    start_year = st.number_input("Start Year", value=2025, step=1)
    end_year   = st.number_input("End Year", value=2054, step=1, min_value=start_year)
with coli2:
    fixed_withdrawal = st.number_input("Fixed withdrawal (gross)", value=0.0, step=5000.0)
    include_roth = st.checkbox("Allow Roth withdrawals (fixed mode)", value=True)
with coli3:
    conv_amount = st.number_input("Roth conversion amount (annual)", value=100000.0, step=5000.0)
    conv_years  = st.number_input("Roth conversion years", value=8, step=1)

st.subheader("Balances & Returns (annual %)")
colb1, colb2, colb3, colb4, colb5, colb6 = st.columns(6)
with colb1:
    trad_primary = st.number_input("Your Trad IRA / 401k", value=1_138_000.0, step=1000.0)
    trad_primary_ret = st.number_input("Return % (Your Trad)", value=8.0, step=0.5)/100
with colb2:
    trad_spouse = st.number_input("Spouse Trad IRA", value=325_000.0, step=1000.0)
    trad_spouse_ret = st.number_input("Return % (Spouse Trad)", value=4.5, step=0.5)/100
with colb3:
    roth = st.number_input("Roth IRA", value=50_000.0, step=1000.0)
    roth_ret = st.number_input("Return % (Roth)", value=14.0, step=0.5)/100
with colb4:
    cash = st.number_input("Cash/Savings", value=100_000.0, step=1000.0)
    cash_ret = st.number_input("Return % (Cash)", value=3.0, step=0.5)/100
with colb5:
    broker = st.number_input("Brokerage", value=200_000.0, step=1000.0)
    broker_ret = st.number_input("Return % (Broker)", value=7.0, step=0.5)/100
with colb6:
    inh = st.number_input("Inherited IRA", value=150_000.0, step=1000.0)
    inh_ret = st.number_input("Return % (Inherited)", value=8.0, step=0.5)/100

st.subheader("Social Security (auto-proration by month)")
cols1, cols2, cols3 = st.columns(3)
with cols1:
    ss_age_you   = st.number_input("Your claim age", value=70, min_value=62, max_value=70)
    ss_age_sp    = st.number_input("Spouse claim age", value=65, min_value=62, max_value=70)
with cols2:
    ss_month_you = st.selectbox("Your start month", list(range(1,13)), index=0)
    ss_month_sp  = st.selectbox("Spouse start month", list(range(1,13)), index=8)
with cols3:
    fra_you = st.number_input("Your FRA monthly ($)", value=2981.0, step=50.0)
    fra_sp  = st.number_input("Spouse FRA monthly ($)", value=2800.0, step=50.0)
cola = st.number_input("SS COLA % (annual)", value=2.0, step=0.25)/100

inputs = Inputs(
    start_year=start_year,
    end_year=end_year,
    balances={
        "trad_primary": trad_primary,
        "trad_spouse": trad_spouse,
        "roth": roth,
        "cash": cash,
        "broker": broker,
        "inh": inh,
    },
    returns={
        "trad_primary": trad_primary_ret,
        "trad_spouse": trad_spouse_ret,
        "roth": roth_ret,
        "cash": cash_ret,
        "broker": broker_ret,
        "inh": inh_ret,
    },
    withdrawals_mode="fixed" if fixed_withdrawal>0 else "manual",
    withdrawals_plan=[],
    fixed_withdrawal=fixed_withdrawal,
    include_roth_in_fixed=include_roth,
    conversions={"annual": conv_amount, "years": int(conv_years)},
    social_security={
        "primary_age": int(ss_age_you),
        "spouse_age": int(ss_age_sp),
        "primary_month": int(ss_month_you),
        "spouse_month": int(ss_month_sp),
        "fra_monthly_primary": float(fra_you),
        "fra_monthly_spouse": float(fra_sp),
        "cola": float(cola),
    }
)

assumptions = Assumptions(rules_version="2025.v1")

if st.button("Run Projection", type="primary"):
    result = run(profile, inputs, assumptions)
    st.success("Projection complete.")
    st.dataframe(result["table"], use_container_width=True)
    st.caption("Demo math: RMD ages (SECURE 2.0), SS first-year proration by month, MD county-effective tax placeholder.")