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
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

AGENDAS = [
    "Agenda 1 · Summary Until Generation Date",
    "Agenda 2 · Last 6 Months (Excl. Current)",
    "Agenda 3 · Current Month",
    "Agenda 4 · Last 6 Months (Incl. Current)",
]

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


def common_charts(period_df: pd.DataFrame, compact_top=5):
    c1, c2 = st.columns([1.2, 1])
    with c1:
        mt = monthly_totals(period_df)
        chart(line_chart(mt, "month_start", "rejection_quantity", title="Monthly Rejection Trend"))
    with c2:
        chart(pareto_chart(period_df, "defect", top_n=compact_top, title="Top Defects (Pareto)"))

    c1, c2, c3 = st.columns(3)
    with c1:
        chart(horizontal_bar(top_n(period_df, "process", n=compact_top).rename(columns={"process":"Process"}), "Process", title="Rejections by Process"))
    with c2:
        chart(horizontal_bar(top_n(period_df, "machine", n=compact_top).rename(columns={"machine":"Machine"}), "Machine", title="Rejections by Machine"))
    with c3:
        chart(location_bar(period_df, title="Rejections by Location"))


def agenda_1(df: pd.DataFrame):
    common_charts(df, 6)
    c1, c2, c3 = st.columns(3)
    with c1:
        chart(horizontal_bar(top_n(df, "part_name_clean", n=5).rename(columns={"part_name_clean":"Part"}), "Part", title="Top Defective Parts"))
    with c2:
        x = top_n_by_group(df, "location", "process", n=3).rename(columns={"location":"Location", "process":"Process"})
        chart(grouped_bar(x, "Process", "Location", title="Top Processes by Location"))
    with c3:
        x = top_n_by_group(df, "location", "part_name_clean", n=3).rename(columns={"location":"Location", "part_name_clean":"Part"})
        chart(grouped_bar(x, "Part", "Location", title="Top Parts by Location"))

    c1, c2, c3 = st.columns(3)
    with c1:
        ms = monthly_summary(df)
        chart(line_chart(ms, "month_start", "rejection_quantity", "location", "Location-wise Trend"))
    with c2:
        chart(pareto_chart(df, "part_no_clean", "total_cost", 15, "Pareto · Rejection Cost"))
    with c3:
        chart(ppm_lines(monthly_ppm_top_part_lines(df, max_parts=6), "PPM Trends · Monthly Peak Parts"))


def agenda_2(df: pd.DataFrame):
    c1, c2, c3 = st.columns(3)
    with c1: chart(location_bar(df, title="6M Location Summary"))
    with c2:
        ms = monthly_summary(df); chart(line_chart(ms, "month_start", "rejection_quantity", "location", "6M Rejection Trend"))
    with c3: chart(segmented_monthly_share(df, title="Monthly Contribution to Rejections"))

    c1, c2, c3 = st.columns(3)
    with c1: chart(control_chart(monthly_totals(df), "month_start", "rejection_quantity", "Control Chart · Total Rejections"))
    with c2: chart(horizontal_bar(top_n(df, "part_name_clean", n=5).rename(columns={"part_name_clean":"Part"}), "Part", title="Top Defective Parts"))
    with c3:
        x = top_n_by_group(df, "location", "process", n=3).rename(columns={"location":"Location", "process":"Process"})
        chart(grouped_bar(x, "Process", "Location", title="Critical Processes · Location-wise"))

    c1, c2, c3 = st.columns(3)
    with c1: chart(horizontal_bar(top_n(df, "defect", n=5).rename(columns={"defect":"Defect"}), "Defect", title="Most Impactful Root Causes"))
    with c2: chart(pareto_chart(df, "defect", top_n=10, title="Pareto · Defect Types"))
    with c3: chart(ppm_bar(ppm_top_parts(df, 5), title="Top 5 Parts by PPM"))


def agenda_3(df: pd.DataFrame):
    c1, c2, c3 = st.columns(3)
    with c1: chart(location_bar(df, title="Current Month · Location Summary"))
    with c2: chart(horizontal_bar(top_n(df, "part_name_clean", n=5).rename(columns={"part_name_clean":"Part"}), "Part", title="Top Defective Parts"))
    with c3:
        x = top_n_by_group(df, "location", "part_no_clean", n=5).rename(columns={"location":"Location", "part_no_clean":"Part No."})
        chart(grouped_bar(x, "Part No.", "Location", title="Top Parts · Location-wise"))

    c1, c2, c3 = st.columns(3)
    with c1: chart(horizontal_bar(top_n(df, "process", n=5).rename(columns={"process":"Process"}), "Process", title="Top Critical Processes"))
    with c2:
        x = top_n_by_group(df, "location", "process", n=5).rename(columns={"location":"Location", "process":"Process"})
        chart(grouped_bar(x, "Process", "Location", title="Processes · Location-wise"))
    with c3: chart(horizontal_bar(top_n(df, "defect", n=5).rename(columns={"defect":"Defect"}), "Defect", title="Most Impactful Root Causes"))

    c1, c2, c3 = st.columns(3)
    with c1:
        x = top_n_by_group(df, "location", "defect", n=5).rename(columns={"location":"Location", "defect":"Defect"})
        chart(grouped_bar(x, "Defect", "Location", title="Root Causes · Location-wise"))
    with c2: chart(pareto_chart(df, "defect", top_n=10, title="Pareto · Defect Types"))
    with c3: chart(ppm_bar(ppm_top_parts(df, 5), title="Top 5 Parts by PPM"))


def agenda_4(df: pd.DataFrame):
    c1, c2, c3 = st.columns(3)
    with c1:
        ms = monthly_summary(df); chart(line_chart(ms, "month_start", "rejection_quantity", "location", "6M Trend · Including Current"))
    with c2: chart(segmented_monthly_share(df, title="Monthly Location Share"))
    with c3: chart(control_chart(monthly_totals(df), "month_start", "rejection_quantity", "6M Control Chart"))

    c1, c2, c3 = st.columns(3)
    with c1: chart(multi_top_trend(df, "part_name_clean", "Top Defective Parts · 6M Trend", max_series=5))
    with c2: chart(multi_top_trend(df, "process", "Top Critical Processes · 6M Trend", max_series=5))
    with c3: chart(multi_top_trend(df, "defect", "Top Root Causes · 6M Trend", max_series=5))

    c1, c2, c3 = st.columns(3)
    with c1: chart(pareto_chart(df, "part_no_clean", "total_cost", 15, "Pareto · Rejection Cost"))
    with c2: chart(pareto_chart(df, "defect", top_n=10, title="Pareto · Defect Types"))
    with c3: chart(ppm_lines(monthly_ppm_top_part_lines(df, max_parts=6), "PPM Trend · Peak Parts"))


def detail_table(df: pd.DataFrame):
    cols = ["Date", "location", "process", "machine", "part_no_clean", "part_name_clean", "defect", "rejection quantity", "production quantity", "total_cost", "safe_ppm"]
    cols = [c for c in cols if c in df.columns]
    st.dataframe(df[cols].sort_values("Date", ascending=False), use_container_width=True, height=280, hide_index=True)


def main():
    df = get_dataset()

    # Fix column name case sensitivity
    try:
        start_date = df['Date'].min()
        end_date = df['Date'].max()
    except KeyError:
        # Handle case where column name might be different
        df.rename(columns={'date': 'Date'}, inplace=True)
        start_date = df['Date'].min()
        end_date = df['Date'].max()

    # Sidebar with optional date range override
    with st.sidebar:
        st.markdown('<div class="brand"><div class="brand-mark">◇</div><div><div class="brand-title">InsightEdge</div><div class="brand-sub">Quality Intelligence</div></div></div>', unsafe_allow_html=True)
        st.markdown("#### Agenda Navigation")
        agenda = st.radio("Select Agenda", AGENDAS, label_visibility="collapsed")
        
        # Optional date range selection
        st.markdown("---")
        st.markdown("#### Date Range")
        show_custom_dates = st.checkbox("Custom Date Range", False)
        if show_custom_dates:
            col1, col2 = st.columns(2)
            custom_start = col1.date_input("Start Date")
            custom_end = col2.date_input("End Date")
        else:
            custom_start, custom_end = None, None
            
        st.markdown("---")
        st.markdown("#### Filters")
        locations = st.multiselect("Location", sorted([x for x in df["location"].unique() if x]))
        processes = st.multiselect("Process", sorted([x for x in df["process"].unique() if x]))
        machines = st.multiselect("Machine", sorted([x for x in df["machine"].unique() if x]))
        parts = st.multiselect("Part", sorted([x for x in df["part_no_clean"].unique() if x]), max_selections=20)
        defects = st.multiselect("Defect", sorted([x for x in df["defect"].unique() if x]), max_selections=20)
        st.markdown("---")
        st.markdown(f'<div class="small-muted">Dataset<br><b>{df["Date"].min():%d %b %Y} – {df["Date"].max():%d %b %Y}</b><br><br>Total Records<br><b>{len(df):,}</b></div>', unsafe_allow_html=True)

    base_filtered = filter_data(df, locations=locations or None, processes=processes or None, machines=machines or None, defects=defects or None, parts=parts or None)
    if base_filtered.empty:
        st.warning("No rows match the current filters.")
        st.stop()

    # Get default dates from agenda
    start_date, end_date = period_for_agenda(base_filtered, agenda)
    if show_custom_dates and custom_start and custom_end:
        start_date = custom_start
        end_date = custom_end
    period_df = filter_data(base_filtered, start_date, end_date)

    st.markdown(f'<div class="page-head"><div><div class="page-title">{agenda.split(" · ",1)[1]}</div><div class="page-sub">Real-time overview of customer complaint quality performance</div></div><div class="page-sub">InsightEdge Executive Dashboard</div></div>', unsafe_allow_html=True)

    f1, f2, f3 = st.columns([1.1, 1.1, 3.8])
    with f1:
        start_date_input = st.date_input(
            "Date From", 
            value=max(start_date, df['Date'].min().date()) if show_custom_dates else start_date
        )

    with f2:
        end_date_input = st.date_input(
            "Date To", 
            value=min(end_date, df['Date'].max().date()) if show_custom_dates else end_date,
            min_value=df['Date'].min().date()
        )
    with f3:
        st.markdown(f'<div class="small-muted" style="padding-top:27px">Showing <b>{start_date_input:%d %b %Y}</b> to <b>{end_date_input:%d %b %Y}</b> · all charts update from the same filters</div>', unsafe_allow_html=True)

    baseline = previous_equal_period(base_filtered, pd.Timestamp(start_date_input), pd.Timestamp(end_date_input))
    kpi_strip(period_df, baseline)

    if agenda.startswith("Agenda 1"):
        agenda_1(period_df)
    elif agenda.startswith("Agenda 2"):
        agenda_2(period_df)
    elif agenda.startswith("Agenda 3"):
        agenda_3(period_df)
    else:
        agenda_4(period_df)

    with st.expander("View filtered complaint records"):
        detail_table(period_df)


if __name__ == "__main__":
    main()
