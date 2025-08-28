# apps/streamlit_app/Home.py
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
# App configuration
# -------------------------------------------------
st.set_page_config(page_title="RetireRight — Retirement Projection", layout="wide")
st.title("RetireRight — Retirement Projection")
st.set_option("client.showErrorDetails", True)

# ===============================
# TABS
# ===============================
tab_profile, tab_accounts, tab_taxes, tab_proj = st.tabs(["Profile", "Accounts", "Taxes", "Projections"])

# ===============================
# PROFILE
# ===============================
with tab_profile:
    st.header("👤 Profile")
    c1, c2, c3 = st.columns(3)
    with c1:
        filing_status = st.selectbox("Filing Status", ["MFJ", "Single", "MFS", "HOH"], index=0)
    with c2:
        primary_dob = st.date_input("Primary DOB", value=date(1959, 12, 31), format="YYYY-MM-DD")
    with c3:
        add_spouse   = st.checkbox("Add Spouse", value=True)
        spouse_dob   = st.date_input("Spouse DOB", value=date(1961, 9, 9), format="YYYY-MM-DD") if add_spouse else None

    c4, c5 = st.columns(2)
    with c4:
        state = st.selectbox(
            "State",
            ["AL","AK","AZ","AR","CA","CO","CT","DE","DC","FL","GA","HI","ID","IL","IN","IA","KS","KY","LA","ME",
             "MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI",
             "SC","SD","TN","TX","UT","VT","VA","WA","WV","WI","WY"],
            index=20
        )
    with c5:
        county = st.text_input("County / Locality (for MD demo)", "Montgomery")

    profile = Profile(
        filing_status=filing_status,
        primary_dob=str(primary_dob),
        spouse_dob=str(spouse_dob) if spouse_dob else None,
        state=state,
        county=county if county else None,
    )

# ===============================
# ACCOUNTS
# ===============================
with tab_accounts:
    st.header("🏦 Accounts")
    st.caption("You can add multiple Roth/HSAs/cash/brokerage. Toggle **include** for which accounts appear. "
               "Use **withdraw_annual** for Manual mode. For brokerage, set **div_yield_pct** and **realize_gains_pct**.")
    import pandas as pd
    default_accounts = pd.DataFrame([
        {"name":"His Trad IRA",    "owner":"his",   "type":"IRA",       "tax_class":"pre_tax",  "start_balance":1_138_000, "return_pct":8.0,  "withdraw_annual":0.0, "div_yield_pct":0.0, "realize_gains_pct":0.0, "include":True},
        {"name":"Her Trad IRA",    "owner":"hers",  "type":"IRA",       "tax_class":"pre_tax",  "start_balance":325_000,   "return_pct":4.5,  "withdraw_annual":0.0, "div_yield_pct":0.0, "realize_gains_pct":0.0, "include":True},
        {"name":"Joint Brokerage", "owner":"joint", "type":"brokerage", "tax_class":"brokerage","start_balance":250_000,   "return_pct":7.0,  "withdraw_annual":0.0, "div_yield_pct":2.0, "realize_gains_pct":25.0, "include":False},
        {"name":"Cash",            "owner":"joint", "type":"cash",      "tax_class":"cash",     "start_balance":100_000,   "return_pct":3.0,  "withdraw_annual":0.0, "div_yield_pct":0.0, "realize_gains_pct":0.0, "include":True},
        {"name":"HSA (His)",       "owner":"his",   "type":"HSA",       "tax_class":"hsa",      "start_balance":0.0,       "return_pct":5.0,  "withdraw_annual":0.0, "div_yield_pct":0.0, "realize_gains_pct":0.0, "include":False},
        {"name":"Roth (His)",      "owner":"his",   "type":"Roth",      "tax_class":"roth",     "start_balance":0.0,       "return_pct":14.0, "withdraw_annual":0.0, "div_yield_pct":0.0, "realize_gains_pct":0.0, "include":False},
    ])
    if "accounts_df" not in st.session_state:
        st.session_state.accounts_df = default_accounts.copy()
    with st.expander("Edit accounts table", expanded=False):
        edited = st.data_editor(
            st.session_state.accounts_df,
            use_container_width=True,
            num_rows="dynamic",
            column_config={
                "name":"Account Name",
                "owner":"Owner",
                "type":"Type",
                "tax_class": st.column_config.SelectboxColumn("Tax Class", options=["pre_tax","roth","hsa","cash","brokerage"]),
                "start_balance":"Start Balance ($)",
                "return_pct":"Return % (annual)",
                "withdraw_annual":"Withdraw Annual ($) (Manual mode)",
                "div_yield_pct":"Div Yield % (brokerage)",
                "realize_gains_pct":"Realize Gains % of growth (brokerage)",
                "include":"Include",
            }
        )
        if not edited.equals(st.session_state.accounts_df):
            st.session_state.accounts_df = edited

# ===============================
# TAXES + SOCIAL SECURITY
# ===============================
with tab_taxes:
    st.header("🧾 Taxes")
    c1, c2, c3 = st.columns(3)
    with c1:
        senior_bill_on = st.checkbox("Apply senior credits (Beautiful Bill)", value=True)
    with c2:
        state_rate_pct = st.number_input("State flat rate % (non-MD)", value=0.0, step=0.25)
    with c3:
        local_rate_pct = st.number_input("Local flat rate % (non-MD)", value=0.0, step=0.25)

    std_override = st.number_input("Standard deduction override ($, blank=auto)", value=0.0, step=500.0)
    round_whole = st.checkbox("Round to whole dollars", value=True)

    st.subheader("Social Security (enter FRA monthly at 67)")
    s0, s1 = st.columns(2)
    with s0:
        fra_primary = st.number_input("Your FRA monthly (at 67)", value=2981.0, step=50.0)
    with s1:
        fra_spouse  = st.number_input("Spouse FRA monthly (at 67)", value=2800.0, step=50.0)

    s2, s3, s4 = st.columns(3)
    with s2:
        you_age   = st.number_input("Your claim age", value=70, min_value=62, max_value=70)
    with s3:
        sp_age    = st.number_input("Spouse claim age", value=65, min_value=62, max_value=70)
    with s4:
        cola      = st.number_input("SS COLA %", value=2.0, step=0.25)

    m1, m2 = st.columns(2)
    with m1:
        you_month = st.number_input("Your start month (1–12)", value=1, min_value=1, max_value=12)
    with m2:
        sp_month  = st.number_input("Spouse start month (1–12)", value=9, min_value=1, max_value=12)

# ===============================
# PROJECTIONS (Manual vs Strategy sliders)
# ===============================
with tab_proj:
    st.header("📆 Window & Strategy")
    p1, p2 = st.columns(2)
    with p1:
        start_year = st.number_input("Start Year", value=2025, step=1)
    with p2:
        end_year   = st.number_input("End Year", value=2034, step=1, min_value=start_year)

    st.subheader("Withdrawal Mode")
    mode = st.radio("Choose how withdrawals are set:", ["Manual (per account)", "Strategy sliders"], index=0, horizontal=True)

    acc = st.session_state.accounts_df.copy()
    acc["return_pct"] = acc["return_pct"].astype(float) / 100.0

    strategy = {"mode":"manual", "weights":{}, "total_withdraw":0.0}
    if mode == "Strategy sliders":
        strategy["mode"] = "weights"
        st.caption("Set a total annual withdrawal target and split by tax class using sliders.")
        tw = st.number_input("Total withdrawal per year (all accounts combined)", value=0.0, step=5000.0)
        st.write("Split by tax class (must total 100%)")
        cpt, crt, cbr, cca = st.columns(4)
        with cpt:
            w_pre = st.number_input("% Pre-Tax", value=50.0, step=1.0)
        with crt:
            w_roth = st.number_input("% Roth", value=25.0, step=1.0)
        with cbr:
            w_bro = st.number_input("% Brokerage", value=25.0, step=1.0)
        with cca:
            w_cash = st.number_input("% Cash", value=0.0, step=1.0)

        total_w = max(1.0, w_pre + w_roth + w_bro + w_cash)  # avoid divide-by-zero
        strategy["total_withdraw"] = float(tw)
        strategy["weights"] = {
            "pre_tax": float(w_pre/total_w),
            "roth":    float(w_roth/total_w),
            "brokerage": float(w_bro/total_w),
            "cash":    float(w_cash/total_w),
        }

    st.divider()
    run_now = st.button("Run Projection", type="primary")
    if run_now:
        with st.spinner("Running projection..."):
            # Build Inputs: balances/returns for included accounts
            balances, returns = {}, {}
            withdrawals_plan = []  # used in manual mode

            for _, row in acc.iterrows():
                if not row.get("include", True):
                    continue
                nm = str(row.get("name", ""))
                balances[nm] = float(row.get("start_balance", 0.0))
                returns[nm]  = float(row.get("return_pct", 0.0))
                wd = float(row.get("withdraw_annual", 0.0))
                tax_class = str(row.get("tax_class", "cash"))
                div_yield = float(row.get("div_yield_pct", 0.0))
                rg_pct    = float(row.get("realize_gains_pct", 0.0))
                withdrawals_plan.append({"name": nm, "annual": wd, "tax_class": tax_class,
                                         "div_yield_pct": div_yield, "realize_gains_pct": rg_pct})

            inputs = Inputs(
                start_year=int(start_year),
                end_year=int(end_year),
                balances=balances,
                returns=returns,
                withdrawals_mode="manual" if strategy["mode"]=="manual" else "weights",
                withdrawals_plan=withdrawals_plan,
                fixed_withdrawal=0.0,
                include_roth_in_fixed=False,
                conversions={"annual":0.0,"years":0},
                social_security={
                    "primary_age": int(you_age),
                    "spouse_age":  int(sp_age),
                    "primary_month": int(you_month),
                    "spouse_month":  int(sp_month),
                    "fra_monthly_primary": float(fra_primary),
                    "fra_monthly_spouse":  float(fra_spouse),
                    "cola": float(cola)/100.0 if cola > 1 else float(cola),
                }
            )
            assumptions = Assumptions(rules_version="2025.v1")

            try:
                result = run(
                    profile, inputs, assumptions,
                    state_rate=state_rate_pct, local_rate=local_rate_pct,
                    senior_bill_on=senior_bill_on, round_whole=round_whole,
                    std_override=(std_override if std_override > 0 else None),
                    strategy=strategy
                )

                df = result["table"] if isinstance(result, dict) and "table" in result else result
                st.subheader("📊 Projection Results")
                st.dataframe(df, use_container_width=True)
            except Exception as e:
                st.error("Projection failed. Details below.")
                st.exception(e)
    else:
        st.caption("Choose Manual or Strategy, set your inputs, then click **Run Projection**.")
