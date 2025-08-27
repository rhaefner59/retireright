import streamlit as st
from datetime import date

# --- make the project root importable on Streamlit Cloud ---
import sys, os
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
# -----------------------------------------------------------

from core.schema import Profile, Inputs, Assumptions
from core.projection import run

# -------------------------------------------------
# App title and configuration
# -------------------------------------------------
st.set_page_config(page_title="RetireRight — Retirement Projection", layout="wide")
st.title("RetireRight — Retirement Projection")

# ===============================
# 1) PROFILE
# ===============================
st.header("👤 Profile")
col1, col2, col3 = st.columns(3)

with col1:
    filing_status = st.selectbox("Filing Status", ["MFJ", "Single", "MFS", "HOH"], index=0)

with col2:
    primary_dob = st.date_input("Primary DOB", value=date(1959, 12, 31), format="YYYY-MM-DD")

with col3:
    add_spouse = st.checkbox("Add Spouse", value=True)
    spouse_dob = st.date_input("Spouse DOB", value=date(1961, 9, 9), format="YYYY-MM-DD") if add_spouse else None

col4, col5 = st.columns(2)
with col4:
    state = st.selectbox(
        "State",
        ["AL","AK","AZ","AR","CA","CO","CT","DE","DC","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME",
         "MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI",
         "SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"],
        index=20
    )
with col5:
    county = st.text_input("County / Locality (demo for MD)", "Montgomery")

profile = Profile(
    filing_status=filing_status,
    primary_dob=str(primary_dob),
    spouse_dob=str(spouse_dob) if spouse_dob else None,
    state=state,
    county=county if county else None,
)

# ===============================
# 2) SETTINGS / INPUTS
# ===============================
st.header("⚙️ Settings")
c1, c2 = st.columns(2)
with c1:
    start_year = st.number_input("Start Year", value=2025, step=1)
with c2:
    end_year = st.number_input("End Year", value=2034, step=1, min_value=start_year)

st.subheader("Balances & Returns (annual %)")
b1, b2, b3 = st.columns(3)
with b1:
    trad_primary = st.number_input("Your Trad IRA / 401k ($)", value=1_138_000.0, step=1000.0)
    ret_primary  = st.number_input("Return % (Your Trad)", value=8.0, step=0.5) / 100
with b2:
    trad_spouse  = st.number_input("Spouse Trad IRA ($)", value=325_000.0, step=1000.0)
    ret_spouse   = st.number_input("Return % (Spouse Trad)", value=4.5, step=0.5) / 100
with b3:
    cash         = st.number_input("Cash/Savings ($)", value=100_000.0, step=1000.0)
    cash_ret     = st.number_input("Return % (Cash)", value=3.0, step=0.5) / 100

st.subheader("Social Security (basic)")
s1, s2, s3 = st.columns(3)
with s1:
    you_age   = st.number_input("Your claim age", value=70, min_value=62, max_value=70)
with s2:
    sp_age    = st.number_input("Spouse claim age", value=65, min_value=62, max_value=70)
with s3:
    cola      = st.number_input("SS COLA %", value=2.0, step=0.25) / 100

m1, m2 = st.columns(2)
with m1:
    you_month = st.number_input("Your start month (1–12)", value=1, min_value=1, max_value=12)
with m2:
    sp_month  = st.number_input("Spouse start month (1–12)", value=9, min_value=1, max_value=12)

# Build Inputs for the engine
inputs = Inputs(
    start_year=int(start_year),
    end_year=int(end_year),
    balances={
        "trad_primary": float(trad_primary),
        "trad_spouse":  float(trad_spouse),
        # extras for completeness (engine may ignore these today)
        "cash": float(cash),
        "roth": 0.0, "broker": 0.0, "inh": 0.0,
    },
    returns={
        "trad_primary": float(ret_primary),
        "trad_spouse":  float(ret_spouse),
        "cash": float(cash_ret),
        "roth": 0.0, "broker": 0.0, "inh": 0.0,
    },
    withdrawals_mode="manual",
    withdrawals_plan=[],
    fixed_withdrawal=0.0,
    include_roth_in_fixed=False,
    conversions={"annual": 0.0, "years": 0},
    social_security={
        "primary_age": int(you_age),
        "spouse_age":  int(sp_age),
        "primary_month": int(you_month),
        "spouse_month":  int(sp_month),
        "fra_monthly_primary": 2981.0,   # placeholders; wire to UI later if needed
        "fra_monthly_spouse":  2800.0,
        "cola": float(cola),
    }
)

assumptions = Assumptions(rules_version="2025.v1")

# ===============================
# 3) RUN & DISPLAY
# ===============================
st.header("📊 Projection Results")
try:
    result = run(profile, inputs, assumptions)

    # Show result if it's a DataFrame or a dict containing a table
    if hasattr(result, "to_dict"):
        st.dataframe(result, use_container_width=True)
    elif isinstance(result, dict) and "table" in result:
        st.dataframe(result["table"], use_container_width=True)
    else:
        st.write(result)
except Exception as e:
    st.error("Projection failed. Details below.")
    st.exception(e)
