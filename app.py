from __future__ import annotations

from datetime import date
import pandas as pd
import streamlit as st

from src.charts import (
    control_chart, grouped_bar, horizontal_bar, line_chart, location_bar,
    multi_top_trend, pareto_chart, ppm_bar, ppm_lines, segmented_monthly_share,
)
from src.data_prep import (
    aggregate_ppm, filter_data, load_data, monthly_ppm_top_part_lines,
    monthly_summary, monthly_totals, period_for_agenda, ppm_top_parts,
    top_n, top_n_by_group,
)

st.set_page_config(page_title="InsightEdge | Quality Intelligence", page_icon="🔷", layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
:root { --bg:#061426; --card:#0d2540; --line:#173a5d; --text:#e8f1fb; --muted:#8fa9c4; --blue:#2f8cff; }
html, body, [class*="css"] { font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
.stApp { background: radial-gradient(circle at 55% 0%, #0b2440 0%, #061426 42%, #04101e 100%); color:var(--text); }
.block-container { max-width: 1550px; padding: .7rem 1rem 1.5rem 1rem; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#071b31 0%,#061426 100%); border-right:1px solid #173a5d; }
[data-testid="stSidebar"] .block-container { padding-top: .7rem; }
[data-testid="stSidebar"] * { color:#dce8f6; }
[data-testid="stMetric"] { background:linear-gradient(145deg,#102b49,#0b2038); border:1px solid #173a5d; border-radius:8px; padding:10px 12px; min-height:82px; box-shadow:0 6px 18px rgba(0,0,0,.12); }
[data-testid="stMetricLabel"] { color:#9db4cc !important; font-size:11px !important; }
[data-testid="stMetricValue"] { color:#f4f8fc !important; font-size:22px !important; font-weight:700 !important; }
[data-testid="stMetricDelta"] { font-size:10px !important; }
[data-testid="stPlotlyChart"] { background:#0d2540; border:1px solid #173a5d; border-radius:8px; overflow:hidden; box-shadow:0 6px 18px rgba(0,0,0,.12); }
div[data-testid="stDataFrame"] { border:1px solid #173a5d; border-radius:8px; overflow:hidden; }
h1,h2,h3 { color:#f4f8fc !important; letter-spacing:-.02em; }
.small-muted { color:#8fa9c4; font-size:11px; }
.brand { display:flex;align-items:center;gap:9px;padding:3px 0 12px 0;border-bottom:1px solid #173a5d;margin-bottom:12px; }
.brand-mark { width:32px;height:32px;border-radius:9px;background:linear-gradient(135deg,#2f8cff,#20d0c2);display:flex;align-items:center;justify-content:center;font-weight:900;color:white; }
.brand-title { font-size:16px;font-weight:800;line-height:1.05; } .brand-sub { color:#8fa9c4;font-size:9px; }
.page-head { display:flex;justify-content:space-between;align-items:flex-end;margin:0 0 7px 0; }
.page-title { font-size:20px;font-weight:800;color:#f4f8fc; } .page-sub { color:#8fa9c4;font-size:10px; }
.section-title { font-size:12px;font-weight:700;color:#dce8f6;margin:4px 0 6px; }
hr { border-color:#173a5d !important; }
.stButton>button { background:#0d2b4c;border:1px solid #1e568a;color:#b9d8f7;border-radius:7px; }
.stSelectbox label,.stMultiSelect label,.stDateInput label { color:#9db4cc !important;font-size:10px !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    padding: 6px 10px;
    border-radius: 6px;
    margin-bottom: 4px;
    transition: background-color 0.2s ease-in-out;
    background-color: transparent;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background-color: #1a385a;
    font-weight: 600;
    color: #e8f1fb !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background-color: #102a47;
}
[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] {
    display: none;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

@st.cache_data(show_spinner=False)
def get_dataset() -> pd.DataFrame:
    return load_data()


def chart(fig):
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})


def kpi_strip(df: pd.DataFrame, baseline: pd.DataFrame | None = None):
    rej = float(df["rejection quantity"].sum())
    prod = float(df["production quantity"].sum())
    ppm = (rej * 1_000_000 / prod) if prod > 0 else 0
    cost = float(df["total_cost"].sum())
    rate = (rej / prod * 100) if prod > 0 else 0
    critical_parts = int((df.groupby("part_no_clean")["rejection quantity"].sum() > 0).sum())

    delta_rej = delta_ppm = delta_cost = None
    if baseline is not None and not baseline.empty:
        b_rej = float(baseline["rejection quantity"].sum())
        b_prod = float(baseline["production quantity"].sum())
        b_ppm = b_rej * 1_000_000 / b_prod if b_prod else 0
        b_cost = float(baseline["total_cost"].sum())
        delta_rej = f"{((rej-b_rej)/b_rej*100):+.1f}%" if b_rej else None
        delta_ppm = f"{((ppm-b_ppm)/b_ppm*100):+.1f}%" if b_ppm else None
        delta_cost = f"{((cost-b_cost)/b_cost*100):+.1f}%" if b_cost else None

    cols = st.columns(6)
    cols[0].metric("Total Rejections", f"{rej:,.0f}", delta_rej, delta_color="inverse")
    cols[1].metric("PPM", f"{ppm:,.0f}", delta_ppm, delta_color="inverse")
    cols[2].metric("Rejection Cost", f"₹ {cost/100000:,.2f} L", delta_cost, delta_color="inverse")
    cols[3].metric("Production Qty", f"{prod:,.0f}")
    cols[4].metric("Rejection Rate", f"{rate:.3f}%")
    cols[5].metric("Affected Parts", f"{critical_parts:,}")


def previous_equal_period(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    days = (end.normalize() - start.normalize()).days + 1
    prev_end = start - pd.Timedelta(days=1)
    prev_start = prev_end - pd.Timedelta(days=days-1)
    return filter_data(df, prev_start, prev_end)


def render_overview(df: pd.DataFrame):
    c1, c2 = st.columns([1.2, 1])
    with c1:
        mt = monthly_totals(df)
        chart(line_chart(mt, "month_start", "rejection_quantity", title="Monthly Rejection Trend"))
    with c2:
        chart(pareto_chart(df, "defect", top_n=5, title="Top Defects (Pareto)"))
    c1, c2, c3 = st.columns(3)
    with c1:
        chart(horizontal_bar(top_n(df, "process", n=5).rename(columns={"process":"Process"}), "Process", title="Rejections by Process"))
    with c2:
        chart(horizontal_bar(top_n(df, "machine", n=5).rename(columns={"machine":"Machine"}), "Machine", title="Rejections by Machine"))
    with c3:
        chart(location_bar(df, title="Rejections by Location"))

def render_part_analysis(df: pd.DataFrame):
    st.subheader("Part Analysis")
    c1, c2 = st.columns(2)
    with c1:
        chart(horizontal_bar(top_n(df, "part_name_clean", n=10).rename(columns={"part_name_clean":"Part"}), "Part", title="Top 10 Defective Parts"))
    with c2:
        chart(ppm_bar(ppm_top_parts(df, 10), title="Top 10 Parts by PPM"))
    chart(multi_top_trend(df, "part_name_clean", "Top Defective Parts · 6M Trend", max_series=5))

def render_defect_analysis(df: pd.DataFrame):
    st.subheader("Defect Analysis")
    c1, c2 = st.columns(2)
    with c1:
        chart(pareto_chart(df, "defect", top_n=10, title="Pareto · Defect Types"))
    with c2:
        chart(horizontal_bar(top_n(df, "defect", n=10).rename(columns={"defect":"Defect"}), "Defect", title="Most Impactful Root Causes"))

def render_process_analysis(df: pd.DataFrame):
    st.subheader("Process Analysis")
    chart(horizontal_bar(top_n(df, "process", n=15).rename(columns={"process":"Process"}), "Process", title="Rejections by Process"))
    x = top_n_by_group(df, "location", "process", n=5).rename(columns={"location":"Location", "process":"Process"})
    chart(grouped_bar(x, "Process", "Location", title="Top Processes by Location"))

def render_machine_analysis(df: pd.DataFrame):
    st.subheader("Machine Analysis")
    chart(horizontal_bar(top_n(df, "machine", n=15).rename(columns={"machine":"Machine"}), "Machine", title="Rejections by Machine"))

def render_location_analysis(df: pd.DataFrame):
    st.subheader("Location Analysis")
    c1, c2 = st.columns(2)
    with c1:
        chart(location_bar(df, title="Rejections by Location"))
    with c2:
        ms = monthly_summary(df)
        chart(line_chart(ms, "month_start", "rejection_quantity", "location", "Location-wise Trend"))

def render_cost_analysis(df: pd.DataFrame):
    st.subheader("Cost Analysis")
    chart(pareto_chart(df, "part_no_clean", "total_cost", 15, "Pareto · Rejection Cost"))

def render_root_cause_analysis(df: pd.DataFrame):
    st.subheader("Root Cause Analysis")
    c1, c2 = st.columns(2)
    with c1:
        x = top_n_by_group(df, "location", "defect", n=5).rename(columns={"location":"Location", "defect":"Defect"})
        chart(grouped_bar(x, "Defect", "Location", title="Root Causes · Location-wise"))
    with c2:
        chart(pareto_chart(df, "defect", top_n=10, title="Pareto · Defect Types"))


def detail_table(df: pd.DataFrame):
    cols = ["Date", "location", "process", "machine", "part_no_clean", "part_name_clean", "defect", "rejection quantity", "production quantity", "total_cost", "safe_ppm"]
    cols = [c for c in cols if c in df.columns]
    st.dataframe(df[cols].sort_values("Date", ascending=False), use_container_width=True, height=280, hide_index=True)
def main():
    df = get_dataset()

    # Sidebar
    with st.sidebar:
        st.markdown('<div class="brand"><div class="brand-mark">◇</div><div><div class="brand-title">InsightEdge</div><div class="brand-sub">Quality Intelligence</div></div></div>', unsafe_allow_html=True)
        st.markdown("#### Navigation")

        PAGES = ["Overview", "Part Analysis", "Defect Analysis", "Process Analysis", "Machine Analysis", "Location Analysis", "Cost Analysis", "Root Cause Analysis"]

        # Use st.radio for navigation and update session_state
        page = st.radio("Navigation", PAGES, label_visibility="collapsed", key="page_selection")
        st.session_state.page = page

        st.markdown("---")
        st.markdown("#### Date Range")

        start_date_default, end_date_default = period_for_agenda(df, "Agenda 1 · Summary Until Generation Date")
        col1, col2 = st.columns(2)
        start_date = col1.date_input("Start Date", start_date_default)
        end_date = col2.date_input("End Date", end_date_default)
            
        st.markdown("---")
        st.markdown("#### Filters")
        locations = st.multiselect("Location", sorted([x for x in df["location"].unique() if x]))
        processes = st.multiselect("Process", sorted([x for x in df["process"].unique() if x]))
        machines = st.multiselect("Machine", sorted([x for x in df["machine"].unique() if x]))
        parts = st.multiselect("Part", sorted([x for x in df["part_no_clean"].unique() if x]), max_selections=20)
        defects = st.multiselect("Defect", sorted([x for x in df["defect"].unique() if x]), max_selections=20)
        st.markdown("---")
        st.markdown(f'<div class="small-muted">Dataset<br><b>{df["Date"].min():%d %b %Y} – {df["Date"].max():%d %b %Y}</b><br><br>Total Records<br><b>{len(df):,}</b></div>', unsafe_allow_html=True)

    period_df = filter_data(df, start_date, end_date, locations=locations or None, processes=processes or None, machines=machines or None, defects=defects or None, parts=parts or None)
    
    if period_df.empty:
        st.warning("No rows match the current filters.")
        st.stop()

    st.markdown(f'<div class="page-head"><div><div class="page-title">{st.session_state.page}</div><div class="page-sub">Real-time overview of customer complaint quality performance</div></div><div class="page-sub">InsightEdge Executive Dashboard</div></div>', unsafe_allow_html=True)
    
    baseline = previous_equal_period(df, pd.Timestamp(start_date), pd.Timestamp(end_date))
    kpi_strip(period_df, baseline)

    if st.session_state.page == "Overview":
        render_overview(period_df)
    elif st.session_state.page == "Part Analysis":
        render_part_analysis(period_df)
    elif st.session_state.page == "Defect Analysis":
        render_defect_analysis(period_df)
    elif st.session_state.page == "Process Analysis":
        render_process_analysis(period_df)
    elif st.session_state.page == "Machine Analysis":
        render_machine_analysis(period_df)
    elif st.session_state.page == "Location Analysis":
        render_location_analysis(period_df)
    elif st.session_state.page == "Cost Analysis":
        render_cost_analysis(period_df)
    elif st.session_state.page == "Root Cause Analysis":
        render_root_cause_analysis(period_df)

    with st.expander("View filtered complaint records"):
        detail_table(period_df)


if __name__ == "__main__":
    main()
