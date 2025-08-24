
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import StringIO

st.set_page_config(page_title="Streaming & Consumer Trends", layout="wide")

st.title("Streaming & Consumer Trends — Macro, Costs, and Behavior")

st.markdown("""
This interactive dashboard combines **macro indicators** with **streaming industry trends**. 
Use the side panel to upload your own datasets (optional) or rely on the defaults provided.
""")

# ---------- Helpers ----------

@st.cache_data
def load_csv(path: str) -> pd.DataFrame:
    try:
        return pd.read_csv(path)
    except Exception:
        return pd.DataFrame()

def ensure_datetime(df: pd.DataFrame, col: str) -> pd.DataFrame:
    if col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def monthly_average(df: pd.DataFrame, date_col: str, value_cols: list) -> pd.DataFrame:
    if date_col not in df.columns:
        return pd.DataFrame()
    d = df.copy()
    d[date_col] = pd.to_datetime(d[date_col], errors="coerce")
    d = d.dropna(subset=[date_col])
    d = d.set_index(date_col).sort_index()
    return d[value_cols].resample("M").mean().reset_index()

def create_default_subs() -> pd.DataFrame:
    data = {
        "date": pd.to_datetime([
            "2020-01-01","2021-01-01","2022-01-01","2023-01-01","2024-01-01","2025-08-01"
        ]),
        "Netflix": [190, 214, 223, 260, 280, 301.6],
        "DisneyPlus": [74, 100, 137, 150, 150, 124.6],
        "WBD_Max_DiscoveryPlus": [np.nan, np.nan, 92, 98, 103.3, 122.3],
    }
    return pd.DataFrame(data).sort_values("date")

def line_chart_simple(x, ys: dict, title: str, xlabel: str, ylabel: str):
    fig = plt.figure(figsize=(8,4))
    ax = plt.gca()
    for label, series in ys.items():
        ax.plot(x, series, marker="o", label=label)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.legend(loc="best")
    fig.tight_layout()
    return fig

# ---------- Sidebar: Data Inputs ----------

st.sidebar.header("Data Inputs (optional uploads)")

default_consumer_path = "consumer_shift_dataset.csv"
uploaded_consumer = st.sidebar.file_uploader("Consumer Shift Dataset (CSV)", type=["csv"], key="consumer_shift")
if uploaded_consumer is not None:
    consumer_df = pd.read_csv(uploaded_consumer)
else:
    consumer_df = load_csv(default_consumer_path)

default_prices_path = "streaming_pivot.csv"
uploaded_prices = st.sidebar.file_uploader("Streaming Prices Pivot (CSV)", type=["csv"], key="prices_pivot")
if uploaded_prices is not None:
    prices_df = pd.read_csv(uploaded_prices, parse_dates=["date"]).set_index("date").sort_index()
else:
    prices_df = load_csv(default_prices_path)
    if not prices_df.empty and "date" in prices_df.columns:
        prices_df["date"] = pd.to_datetime(prices_df["date"], errors="coerce")
        prices_df = prices_df.set_index("date").sort_index()

default_fed_path = "fedfunds_clean.csv"
uploaded_fed = st.sidebar.file_uploader("Fed Funds Monthly (CSV)", type=["csv"], key="fedfunds")
if uploaded_fed is not None:
    fed_df = pd.read_csv(uploaded_fed, parse_dates=["date"]).set_index("date").sort_index()
else:
    fed_df = load_csv(default_fed_path)
    if not fed_df.empty and "date" in fed_df.columns:
        fed_df["date"] = pd.to_datetime(fed_df["date"], errors="coerce")
        fed_df = fed_df.set_index("date").sort_index()

uploaded_subs = st.sidebar.file_uploader("Subscriptions Timeline (CSV)", type=["csv"], key="subs")
if uploaded_subs is not None:
    subs_df = pd.read_csv(uploaded_subs, parse_dates=["date"]).sort_values("date")
else:
    subs_df = create_default_subs()

# ---------- Overview KPIs ----------

colA, colB, colC, colD = st.columns(4)

with colA:
    if not fed_df.empty:
        latest_rate = fed_df["fedfunds_rate"].dropna().iloc[-1]
        st.metric("Latest Fed Funds Rate (%)", f"{latest_rate:.2f}")
    else:
        st.metric("Latest Fed Funds Rate (%)", "—")

with colB:
    if not consumer_df.empty and "cable_live_tv_cpi_index" in consumer_df.columns:
        latest_cpi = consumer_df.sort_values("year")["cable_live_tv_cpi_index"].dropna().iloc[-1]
        st.metric("Cable/Live TV CPI Index", f"{latest_cpi:.1f}")
    else:
        st.metric("Cable/Live TV CPI Index", "—")

with colC:
    if not consumer_df.empty and {"avg_cable_bill_usd","avg_streaming_spend_usd"}.issubset(consumer_df.columns):
        last = consumer_df.sort_values("year").iloc[-1]
        gap = (last["avg_cable_bill_usd"] - last["avg_streaming_spend_usd"])
        st.metric("Monthly Cost Gap (Cable − Streaming)", f"${gap:.0f}")
    else:
        st.metric("Monthly Cost Gap", "—")

with colD:
    if not subs_df.empty:
        cols = [c for c in subs_df.columns if c != "date"]
        total_latest = subs_df[cols].drop(columns=["date"], errors="ignore").iloc[-1].sum() if "date" in subs_df.columns else subs_df.iloc[-1].sum()
        st.metric("Total Latest Subs (sum of series, M)", f"{total_latest:.1f}")
    else:
        st.metric("Total Latest Subs (M)", "—")

st.markdown("---")

# ---------- Section 1: Adoption ----------
st.header("1) Adoption — Households with Cable vs Streaming (2015–2025)")

if consumer_df.empty or not {"year","households_cable_pct","households_streaming_pct"}.issubset(consumer_df.columns):
    st.info("Upload a consumer_shift_dataset.csv with columns: year, households_cable_pct, households_streaming_pct.")
else:
    d = consumer_df.sort_values("year")
    fig1 = plt.figure(figsize=(8,4))
    ax1 = plt.gca()
    ax1.plot(d["year"], d["households_cable_pct"], marker="o", label="Households with Cable/Satellite (%)")
    ax1.plot(d["year"], d["households_streaming_pct"], marker="o", label="Households Using Streaming (%)")
    ax1.set_title("U.S. Household Adoption: Cable vs Streaming (2015–2025)")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Household %")
    ax1.legend(loc="best")
    fig1.tight_layout()
    st.pyplot(fig1)

st.markdown("---")

# ---------- Section 2: Viewing Share (Starts at 2020) ----------
st.header("2) Viewing Share — Streaming vs Cable vs Broadcast")

if consumer_df.empty or not {"year","view_share_streaming_pct","view_share_cable_pct","view_share_broadcast_pct"}.issubset(consumer_df.columns):
    st.info("Upload a consumer_shift_dataset.csv with viewing share columns.")
else:
    d = consumer_df.sort_values("year")
    # NEW: Filter to 2020+
    d = d[d["year"] >= 2020]
    fig2 = plt.figure(figsize=(8,4))
    ax2 = plt.gca()
    ax2.stackplot(d["year"],
                  d["view_share_streaming_pct"].fillna(0),
                  d["view_share_cable_pct"].fillna(0),
                  d["view_share_broadcast_pct"].fillna(0),
                  labels=["Streaming Share (%)","Cable Share (%)","Broadcast Share (%)"])
    ax2.set_title("TV Viewing Share (2020–2025)")
    ax2.set_xlabel("Year")
    ax2.set_ylabel("Share of Viewing (%)")
    ax2.legend(loc="upper left")
    fig2.tight_layout()
    st.pyplot(fig2)

st.markdown("---")

# ---------- Section 3: Cost Divergence + CPI ----------
st.header("3) Costs — Cable vs Streaming + Cable/Live TV CPI")

if consumer_df.empty or not {"year","avg_cable_bill_usd","avg_streaming_spend_usd","cable_live_tv_cpi_index"}.issubset(consumer_df.columns):
    st.info("Upload a consumer_shift_dataset.csv with cost & CPI columns.")
else:
    d = consumer_df.sort_values("year")
    fig3, ax3 = plt.subplots(figsize=(10,4))
    ax3.plot(d["year"], d["avg_cable_bill_usd"], marker="o", label="Avg Cable Bill ($)")
    ax3.plot(d["year"], d["avg_streaming_spend_usd"], marker="o", label="Avg Streaming Spend ($)")
    ax3.set_xlabel("Year")
    ax3.set_ylabel("Monthly Cost (USD)")
    ax3.set_title("Cost Divergence: Cable vs Streaming + CPI")
    ax3.legend(loc="upper left")

    ax4 = ax3.twinx()
    ax4.plot(d["year"], d["cable_live_tv_cpi_index"], linewidth=2, label="Cable/Live TV CPI Index")
    ax4.set_ylabel("CPI Index (Dec 1983 = 100)")

    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax4.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2, loc="upper center", ncol=2)

    fig3.tight_layout()
    st.pyplot(fig3)

st.markdown("---")

# ---------- Section 4: Interest Rates vs Subscriptions ----------
st.header("4) Interest Rates vs Streaming Subscriptions")

if 'fed_df' not in locals() or fed_df.empty:
    st.info("Upload a fedfunds_clean.csv file with columns: date, fedfunds_rate.")
else:
    series_cols = [c for c in subs_df.columns if c != "date"]
    chosen = st.multiselect("Choose subscription series to plot:", options=series_cols, default=series_cols)
    subs_plot = subs_df[["date"] + chosen].dropna(how="all")
    subs_plot = subs_plot.set_index("date").sort_index()

    subs_q = subs_plot.resample("Q").mean()
    fed_q = fed_df.resample("Q").mean()

    fig4, ax5 = plt.subplots(figsize=(10,4))
    for c in chosen:
        ax5.plot(subs_q.index, subs_q[c], marker="o", label=f"{c} (M)")
    ax5.set_ylabel("Subscribers (Millions)")
    ax5.set_title("Streaming Subscriptions vs Fed Funds Rate")
    ax5.legend(loc="upper left")

    ax6 = ax5.twinx()
    ax6.plot(fed_q.index, fed_q["fedfunds_rate"], linewidth=2, label="Fed Funds Rate (%)")
    ax6.set_ylabel("Fed Funds Rate (%)")

    l1, lb1 = ax5.get_legend_handles_labels()
    l2, lb2 = ax6.get_legend_handles_labels()
    ax5.legend(l1 + l2, lb1 + lb2, loc="upper center", ncol=2)

    fig4.tight_layout()
    st.pyplot(fig4)

st.markdown("---")

# ---------- Section 5: Streaming Prices ----------
st.header("5) Streaming Prices — On‑Demand Services")

if 'prices_df' not in locals() or prices_df.empty:
    st.info("Upload a streaming_pivot.csv with columns: date, <service columns...>")
else:
    services = [c for c in prices_df.columns if c != "date"]
    if not services:
        services = prices_df.columns.tolist()
    chosen_svcs = st.multiselect("Select services to plot:", options=services, default=services[:min(5, len(services))])
    if chosen_svcs:
        fig5 = plt.figure(figsize=(10,4))
        ax7 = plt.gca()
        ax7.plot(prices_df.index, prices_df[chosen_svcs])
        ax7.set_title("On‑Demand Streaming Prices Over Time")
        ax7.set_xlabel("Date")
        ax7.set_ylabel("Monthly Price (USD)")
        ax7.legend(chosen_svcs, loc="best")
        fig5.tight_layout()
        st.pyplot(fig5)

st.markdown("---")

st.caption("Notes: Figures may include approximations for illustrative purposes. Replace any dataset via the sidebar to use your own time series.")
