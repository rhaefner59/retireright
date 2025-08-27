import streamlit as st
from datetime import date

# --- fix Python path so we can import core ---
import sys, os
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
# ---------------------------------------------

from core.schema import Profile, Inputs, Assumptions
from core.projection import run

# -------------------------------------------------
# App title and configuration
# -------------------------------------------------
st.set_page_config(page_title="RetireRight — Retirement Projection", layout="wide")
st.title("RetireRight — Retirement Projection")

st.header("👤 Profile")
col1, col2, col3 = st.columns(3)

with col1:
    filing_status = st.selectbox("Filing Status", ["MFJ", "Single", "MFS", "HOH"], index=0)

with col2:
    primary_dob = st.date_input("Primary DOB", value=date(1959, 12, 31), format="YYYY-MM-DD")

with col3:
    spouse_dob_enable = st.checkbox("Add Spouse", value=True)
    spouse_dob = None
    if spouse_dob_enable:
        spouse_dob = st.date_input("Spouse DOB", value=date(1961, 9, 9), format="YYYY-MM-DD")

# -------------------------------------------------
# State and County / Locality selection
# -------------------------------------------------
col4, col5 = st.columns(2)

with col4:
    state = st.selectbox("State", [
        "AL","AK","AZ","AR","CA","CO","CT","DE","DC","FL","GA","HI","ID","IL","IN","IA","KS",
        "KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC",
        "ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"
    ], index=20)

with col5:
    county = st.text_input("County / Locality (demo for MD)", "Montgomery")

# -------------------------------------------------
# Build Profile object
# -------------------------------------------------
profile = Profile(
    filing_status=filing_status,
    primary_dob=str(primary_dob),
    spouse_dob=str(spouse_dob) if spouse_dob else None,
    state=state,
    county=county if county not in ("", None) else None
)

# -------------------------------------------------
# Run projection
# -------------------------------------------------
st.header("📊 Projection Results")
results = run(profile)

# Display results (simple table for now)
st.write("### Projection Output")
st.dataframe(results)
