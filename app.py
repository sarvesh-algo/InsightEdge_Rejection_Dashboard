from __future__ import annotations

from datetime import date
import math
import pandas as pd
import streamlit as st

from src.charts import (
    control_chart,
    grouped_bar,
    horizontal_bar,
    line_chart,
    location_bar,
    multi_top_trend,
    pareto_chart,
    ppm_bar,
    ppm_lines,
    segmented_monthly_share,
    ppm_trend,
    rolling_ppm_chart,
    ppm_rank_bar,
    ppm_heatmap,
    ppm_by_location,
    ppm_distribution_chart,
    production_vs_ppm,
    ppm_gauge,
    ppm_donut,
    ppm_part_lines,
    create_cost_pie_chart,
)
from src.data_prep import (
    aggregate_ppm,
    filter_data,
    load_data,
    monthly_ppm_top_part_lines,
    monthly_summary,
    monthly_totals,
    period_for_agenda,
    ppm_top_parts,
    top_n,
    top_n_by_group,
)

st.set_page_config(
    page_title="InsightEdge | Quality Intelligence",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="expanded",
)

TARGET_PPM = 20_000

CSS = """
<style>
:root {
    --bg:#04111f;
    --bg2:#071a2d;
    --card:#0b2138;
    --card2:#0e2944;
    --line:#173a5d;
    --line2:#214c73;
    --text:#edf5ff;
    --muted:#8fa9c4;
    --blue:#2f8cff;
    --cyan:#24c8d8;
    --green:#34d399;
    --red:#ff5c72;
}
html, body, [class*="css"] {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.stApp {
    background:
        radial-gradient(circle at 55% -10%, #0d2d4d 0%, transparent 36%),
        radial-gradient(circle at 100% 35%, #09243d 0%, transparent 28%),
        linear-gradient(180deg, #061526 0%, #04111f 100%);
    color:var(--text);
}
.block-container {
    max-width: 1680px;
    padding: .75rem 1rem 1.5rem 1rem;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#06182b 0%,#04111f 100%);
    border-right:1px solid #173a5d;
}
[data-testid="stSidebar"] .block-container { padding: .75rem .65rem 1rem .65rem; }
[data-testid="stSidebar"] * { color:#dce8f6; }
[data-testid="stSidebar"] [data-testid="stRadio"] > div { gap:3px; }
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    min-height:38px;
    padding:9px 11px;
    border-radius:9px;
    margin:0 0 4px 0;
    transition:all .18s ease;
    background:transparent;
    border:1px solid transparent;
    font-size:13px;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background:#102b47;
    border-color:#1b476d;
    transform:translateX(2px);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background:linear-gradient(90deg,#1557a0,#123b67);
    border-color:#2673bd;
    box-shadow:0 4px 16px rgba(0,0,0,.18);
    color:#ffffff !important;
    font-weight:700;
}
[data-testid="stSidebar"] [data-testid="stRadio"] input[type="radio"] { display:none; }
[data-testid="stMetric"] {
    background:linear-gradient(145deg,#102c49,#0a2036);
    border:1px solid #173a5d;
    border-radius:10px;
    padding:11px 13px;
    min-height:86px;
    box-shadow:0 8px 22px rgba(0,0,0,.13);
}
[data-testid="stMetricLabel"] { color:#9db4cc !important; font-size:10px !important; }
[data-testid="stMetricValue"] { color:#f4f8fc !important; font-size:23px !important; font-weight:750 !important; }
[data-testid="stMetricDelta"] { font-size:10px !important; }
[data-testid="stPlotlyChart"] {
    background:#0d2540;
    border:1px solid #173a5d;
    border-radius:10px;
    overflow:hidden;
    box-shadow:0 7px 20px rgba(0,0,0,.12);
}
div[data-testid="stDataFrame"] { border:1px solid #173a5d; border-radius:10px; overflow:hidden; }
h1,h2,h3 { color:#f4f8fc !important; letter-spacing:-.02em; }
.small-muted { color:#8fa9c4; font-size:10px; line-height:1.5; }
.brand {
    display:flex; align-items:center; gap:10px; padding:5px 5px 13px 5px;
    border-bottom:1px solid #173a5d; margin-bottom:12px;
}
.brand-mark {
    width:34px; height:34px; border-radius:10px;
    background:linear-gradient(135deg,#2f8cff,#20d0c2);
    display:flex; align-items:center; justify-content:center;
    font-weight:900; color:white; box-shadow:0 6px 15px rgba(47,140,255,.25);
}
.brand-title { font-size:17px; font-weight:800; line-height:1.05; }
.brand-sub { color:#8fa9c4; font-size:9px; margin-top:2px; }
.nav-label { color:#6f8ca9; font-size:9px; text-transform:uppercase; letter-spacing:.12em; margin:8px 7px 7px; }
.page-head {
    display:flex; justify-content:space-between; align-items:flex-end;
    margin:0 0 9px 0;
}
.page-title { font-size:21px; font-weight:800; color:#f4f8fc; }
.page-sub { color:#8fa9c4; font-size:10px; }
.section-title { font-size:12px; font-weight:750; color:#dce8f6; margin:4px 0 6px; }
.dashboard-card {
    background:linear-gradient(145deg,#0c2742,#0a1f34);
    border:1px solid #173a5d; border-radius:10px; padding:13px;
}
.alert-card {
    background:linear-gradient(145deg,#261b25,#101e2f);
    border:1px solid #593447; border-radius:10px; padding:13px;
}
.insight-card {
    background:linear-gradient(145deg,#0b2b39,#0a2034);
    border:1px solid #19506a; border-radius:10px; padding:13px;
}
.kpi-note { color:#8fa9c4; font-size:9px; margin-top:2px; }
.status-good { color:#39e29c; font-weight:700; }
.status-warn { color:#f6c453; font-weight:700; }
.status-bad { color:#ff6478; font-weight:700; }
.stButton>button {
    background:#0d2b4c; border:1px solid #1e568a; color:#b9d8f7;
    border-radius:8px; min-height:34px;
}
.stButton>button:hover { border-color:#2f8cff; color:white; background:#123b63; }
.stSelectbox label,.stMultiSelect label,.stDateInput label,.stSlider label {
    color:#9db4cc !important; font-size:10px !important;
}
[data-testid="stExpander"] { border-color:#173a5d; background:#081a2d; }
hr { border-color:#173a5d !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def get_dataset() -> pd.DataFrame:
    return load_data()


def chart(fig):
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False, "responsive": True})


def ppm_value(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    rejection = float(df["rejection quantity"].sum())
    denominator = float(df["ppm_denominator"].sum())
    return rejection * 1_000_000 / denominator if denominator > 0 else 0.0


def previous_equal_period(df: pd.DataFrame, start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    days = (end.normalize() - start.normalize()).days + 1
    prev_end = start - pd.Timedelta(days=1)
    prev_start = prev_end - pd.Timedelta(days=days - 1)
    return filter_data(df, prev_start, prev_end)


def kpi_strip(df: pd.DataFrame, baseline: pd.DataFrame | None = None):
    rej = float(df["rejection quantity"].sum())
    prod = float(df["production quantity"].sum())
    ppm = ppm_value(df)
    cost = float(df["total_cost"].sum())
    rate = (rej / prod * 100) if prod > 0 else 0
    affected_parts = int((df.groupby("part_no_clean")["rejection quantity"].sum() > 0).sum())

    delta_rej = delta_ppm = delta_cost = None
    if baseline is not None and not baseline.empty:
        b_rej = float(baseline["rejection quantity"].sum())
        b_ppm = ppm_value(baseline)
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
    cols[5].metric("Affected Parts", f"{affected_parts:,}")


def render_header(df: pd.DataFrame):
    # ---------------------------------------------------------
    # SAFE DATE INITIALIZATION
    # ---------------------------------------------------------
    # Always initialize the date widget inside the real dataset
    # boundaries. The agenda helper can produce 01-Apr-2024,
    # while the dataset starts on 22-Apr-2024, which Streamlit
    # rejects before the page renders.
    data_min = pd.Timestamp(df["Date"].min()).normalize()
    data_max = pd.Timestamp(df["Date"].max()).normalize()

    st.markdown(
        '<div class="page-head"><div><div class="page-title">InsightEdge Quality Intelligence</div>'
        '<div class="page-sub">Real-time quality, rejection and PPM performance</div></div>'
        '<div class="page-sub">Executive Quality Dashboard</div></div>',
        unsafe_allow_html=True,
    )

    # ---------------------------------------------------------
    # TOP HEADER
    # ---------------------------------------------------------
    left, right = st.columns([1.05, 1.25])

    with left:
        locations = ["All"] + sorted(
            [x for x in df["location"].unique() if x]
        )
        selected_location = st.selectbox(
            "Location",
            locations,
            index=0,
            key="top_location_v2",
        )

    with right:
        selected_range = st.date_input(
            "Date Range",
            value=(data_min.date(), data_max.date()),
            min_value=data_min.date(),
            max_value=data_max.date(),
            key="top_date_range_v2",
        )

    if isinstance(selected_range, (tuple, list)) and len(selected_range) == 2:
        start_date, end_date = selected_range
    else:
        start_date = selected_range
        end_date = selected_range

    # ---------------------------------------------------------
    # ADDITIONAL FILTERS
    # ---------------------------------------------------------
    st.markdown(
        '<div class="section-title">Dashboard Filters</div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        processes = st.multiselect(
            "Process",
            sorted([x for x in df["process"].unique() if x]),
            key="top_process_v2",
        )

    with c2:
        machines = st.multiselect(
            "Machine",
            sorted([x for x in df["machine"].unique() if x]),
            key="top_machine_v2",
        )

    with c3:
        parts = st.multiselect(
            "Part",
            sorted([x for x in df["part_no_clean"].unique() if x]),
            max_selections=20,
            key="top_part_v2",
        )

    with c4:
        defects = st.multiselect(
            "Defect",
            sorted([x for x in df["defect"].unique() if x]),
            max_selections=20,
            key="top_defect_v2",
        )

    # ---------------------------------------------------------
    # APPLY FILTERS
    # ---------------------------------------------------------
    period_df = filter_data(
        df,
        start_date,
        end_date,
        locations=(
            None
            if selected_location == "All"
            else [selected_location]
        ),
        processes=processes or None,
        machines=machines or None,
        defects=defects or None,
        parts=parts or None,
    )

    return (
        period_df,
        pd.Timestamp(start_date),
        pd.Timestamp(end_date),
        selected_location,
    )


def render_overview(df: pd.DataFrame):
    st.subheader("Overview")
    c1, c2 = st.columns([1.2, 1])
    with c1:
        chart(line_chart(monthly_totals(df), "month_start", "rejection_quantity", title="Monthly Rejection Trend"))
    with c2:
        chart(pareto_chart(df, "defect", top_n=5, title="Top Defects (Pareto)"))
    c1, c2, c3 = st.columns(3)
    with c1:
        chart(horizontal_bar(top_n(df, "process", n=5).rename(columns={"process":"Process"}), "Process", title="Rejections by Process"))
    with c2:
        chart(horizontal_bar(top_n(df, "machine", n=5).rename(columns={"machine":"Machine"}), "Machine", title="Rejections by Machine"))
    with c3:
        chart(location_bar(df, title="Rejections by Location"))


def render_ppm_dashboard(df: pd.DataFrame):
    """Complete PPM dashboard based on the newsletter PPM analysis and supplied data."""
    monthly = aggregate_ppm(df, ["month_start"])
    process = aggregate_ppm(df, ["process"])
    machine = aggregate_ppm(df, ["machine"])
    location = aggregate_ppm(df, ["location"])
    part = aggregate_ppm(df, ["part_no_clean"])
    defect = aggregate_ppm(df, ["defect"])

    overall = ppm_value(df)
    latest_month_ppm = 0.0
    best_month = 0.0
    worst_month = 0.0
    if not monthly.empty:
        monthly = monthly.sort_values("month_start")
        latest_month_ppm = float(monthly.iloc[-1]["ppm"])
        valid_months = monthly[monthly["ppm_denominator"] > 0]
        if not valid_months.empty:
            best_month = float(valid_months["ppm"].min())
            worst_month = float(valid_months["ppm"].max())

    ytd_avg = float(monthly["ppm"].mean()) if not monthly.empty else 0.0
    target_status = "Within target" if overall <= TARGET_PPM else "Above target"
    target_class = "status-good" if overall <= TARGET_PPM else "status-bad"

    st.markdown(
        '<div class="page-head"><div><div class="page-title">PPM Dashboard</div>'
        '<div class="page-sub">Parts Per Million performance · PPM = (Rejection Qty × 1,000,000) / Sale Qty</div></div>'
        '<div class="page-sub">Target ≤ 20,000 PPM</div></div>',
        unsafe_allow_html=True,
    )

    denominator_label = "Sale Qty" if "sale quantity" in df.columns else "Production Qty"
    if "sale quantity" not in df.columns:
        st.info(
            "The uploaded CSV does not contain a Sale Qty column. "
            "The dashboard therefore uses Production Qty as the denominator available in the dataset. "
            "Once Sale Qty is supplied, the same formula will automatically use it."
        )

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("PPM (Overall)", f"{overall:,.0f}")
    k2.metric("PPM (Latest Month)", f"{latest_month_ppm:,.0f}")
    k3.metric("PPM (YTD Avg)", f"{ytd_avg:,.0f}")
    k4.metric("Best Month PPM", f"{best_month:,.0f}")
    k5.metric("Worst Month PPM", f"{worst_month:,.0f}")
    k6.metric("PPM Target", f"≤ {TARGET_PPM:,.0f}")

    st.markdown(
        f'<div class="small-muted" style="margin:5px 0 10px 2px;">'
        f'Denominator used: <b>{denominator_label}</b> · Current status: '
        f'<span class="{target_class}">{target_status}</span></div>',
        unsafe_allow_html=True,
    )

    # Hero row: trend + gauge + alerts.
    c1, c2, c3 = st.columns([1.55, .85, .75])
    with c1:
        chart(ppm_trend(monthly, TARGET_PPM, "PPM Trend (Overall)"))
    with c2:
        chart(ppm_gauge(overall, TARGET_PPM))
    with c3:
        st.markdown('<div class="section-title">PPM Alerts</div>', unsafe_allow_html=True)
        high_process = process.sort_values("ppm", ascending=False).head(1)
        high_machine = machine.sort_values("ppm", ascending=False).head(1)
        high_part = part[part["part_no_clean"].astype(str).str.len() > 0].sort_values("ppm", ascending=False).head(1)
        alerts = []
        if overall > TARGET_PPM:
            alerts.append(("🔴", f"Overall PPM is {overall:,.0f}, above target"))
        if not high_process.empty and high_process.iloc[0]["ppm"] > TARGET_PPM:
            alerts.append(("🟠", f"{high_process.iloc[0]['process']} process PPM is {high_process.iloc[0]['ppm']:,.0f}"))
        if not high_machine.empty and high_machine.iloc[0]["ppm"] > TARGET_PPM:
            alerts.append(("🟡", f"{high_machine.iloc[0]['machine']} machine PPM is {high_machine.iloc[0]['ppm']:,.0f}"))
        if not high_part.empty and high_part.iloc[0]["ppm"] > TARGET_PPM:
            alerts.append(("🔴", f"Part {high_part.iloc[0]['part_no_clean']} has PPM {high_part.iloc[0]['ppm']:,.0f}"))
        if not alerts:
            alerts = [("🟢", "No PPM threshold breaches in the selected period"),
                      ("🔵", "Continue monitoring monthly movement"),
                      ("🟢", "Target performance is currently stable")]
        for icon, text in alerts[:5]:
            st.markdown(
                f'<div style="padding:9px 4px;border-bottom:1px solid #173a5d;font-size:10px;">'
                f'<span style="font-size:14px">{icon}</span>&nbsp; {text}</div>',
                unsafe_allow_html=True,
            )

    # Core comparison charts.
    c1, c2, c3 = st.columns(3)
    with c1:
        chart(ppm_rank_bar(process, "process", "PPM by Process", 10))
    with c2:
        chart(ppm_rank_bar(machine, "machine", "PPM by Machine · Top 10", 10))
    with c3:
        chart(ppm_by_location(df, "PPM by Location"))

    c1, c2 = st.columns([1.05, 1])
    with c1:
        chart(ppm_bar(ppm_top_parts(df, 10), title="Top 10 Parts by PPM"))
    with c2:
        chart(ppm_donut(df, "Defect Contribution to Rejections"))

    # Trend / statistical section.
    c1, c2 = st.columns(2)
    with c1:
        chart(rolling_ppm_chart(monthly, TARGET_PPM, "Monthly PPM · Rolling 3M & 6M"))
    with c2:
        chart(control_chart(monthly, "month_start", "ppm", "PPM Control Chart · 3σ Limits"))

    c1, c2 = st.columns(2)
    with c1:
        chart(ppm_part_lines(df, max_parts=6, title="Top Parts · Monthly PPM Trend"))
    with c2:
        chart(production_vs_ppm(df, "Production Quantity vs PPM"))

    # Heatmaps from the same PPM aggregation logic.
    c1, c2 = st.columns(2)
    with c1:
        chart(ppm_heatmap(df, "process", "PPM Heatmap · Process vs Month", top_n=10))
    with c2:
        chart(ppm_heatmap(df, "machine", "PPM Heatmap · Machine vs Month", top_n=10))

    c1, c2 = st.columns(2)
    with c1:
        chart(ppm_heatmap(df, "location", "PPM Heatmap · Location vs Month", top_n=10))
    with c2:
        chart(ppm_heatmap(df, "defect", "PPM Heatmap · Defect vs Month", top_n=10))

    c1, c2 = st.columns(2)
    with c1:
        chart(ppm_distribution_chart(df, TARGET_PPM, "PPM Distribution"))
    with c2:
        chart(pareto_chart(df, "part_no_clean", "rejection quantity", 15, "Part Rejection Pareto · PPM Context"))

    # Newsletter-style top-part table: highest PPM part per month and track it.
    st.markdown('<div class="section-title">Monthly Highest-PPM Parts</div>', unsafe_allow_html=True)
    trend_parts = monthly_ppm_top_part_lines(df, max_parts=10)
    if not trend_parts.empty:
        pivot = trend_parts.pivot_table(index="part_no_clean", columns="month_start", values="ppm", fill_value=0)
        pivot.columns = [pd.Timestamp(c).strftime("%b %y") for c in pivot.columns]
        pivot = pivot.round(0).reset_index()
        st.dataframe(pivot, use_container_width=True, hide_index=True, height=260)

    # AI-style summary and actions.
    st.markdown('<div class="section-title">AI Quality Summary & Recommended Actions</div>', unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        process_name = str(high_process.iloc[0]["process"]) if not high_process.empty else "N/A"
        process_ppm = float(high_process.iloc[0]["ppm"]) if not high_process.empty else 0
        machine_name = str(high_machine.iloc[0]["machine"]) if not high_machine.empty else "N/A"
        machine_ppm = float(high_machine.iloc[0]["ppm"]) if not high_machine.empty else 0
        part_name = str(high_part.iloc[0]["part_no_clean"]) if not high_part.empty else "N/A"
        part_ppm = float(high_part.iloc[0]["ppm"]) if not high_part.empty else 0
        st.markdown(
            f'<div class="insight-card">'
            f'<b>Overall PPM:</b> {overall:,.0f} · '
            f'<span class="{target_class}">{target_status}</span><br><br>'
            f'🔴 Highest process: <b>{process_name}</b> ({process_ppm:,.0f} PPM)<br>'
            f'🟠 Highest machine: <b>{machine_name}</b> ({machine_ppm:,.0f} PPM)<br>'
            f'🟡 Highest-PM part: <b>{part_name}</b> ({part_ppm:,.0f} PPM)<br>'
            f'📈 Monthly average: <b>{ytd_avg:,.0f} PPM</b>'
            f'</div>', unsafe_allow_html=True,
        )
    with right:
        actions = []
        if process_name != "N/A": actions.append(f"Investigate high PPM in {process_name} process")
        if machine_name != "N/A": actions.append(f"Inspect {machine_name} for tooling / parameter issues")
        if part_name != "N/A": actions.append(f"Perform root-cause review for part {part_name}")
        actions.append("Review top defects contributing to rejected quantity")
        actions.append("Monitor rolling 3M and 6M PPM against target")
        html = '<div class="dashboard-card"><b>Recommended Actions</b><br><br>'
        for i, action in enumerate(actions[:5]):
            priority = "High" if i < 3 else "Medium"
            html += f'<div style="padding:7px 0;border-bottom:1px solid #173a5d;font-size:10px;">✓ {action} <span style="float:right;color:{"#ff6478" if priority == "High" else "#f6c453"};font-weight:700">{priority}</span></div>'
        html += '</div>'
        st.markdown(html, unsafe_allow_html=True)


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


def render_trend_analysis(df: pd.DataFrame):
    st.subheader("Trend Analysis")
    monthly = monthly_totals(df)
    c1, c2 = st.columns(2)
    with c1:
        chart(line_chart(monthly, "month_start", "rejection_quantity", title="Monthly Rejection Trend"))
    with c2:
        chart(ppm_trend(aggregate_ppm(df, ["month_start"]), TARGET_PPM, "Monthly PPM Trend"))
    chart(segmented_monthly_share(monthly_summary(df), title="Monthly Location Contribution %"))


def render_reports(df: pd.DataFrame):
    st.subheader("Reports")
    st.markdown("Use the current filters above to generate the report-ready dataset.")
    summary = aggregate_ppm(df, ["location", "process"])
    st.dataframe(summary.sort_values("ppm", ascending=False), use_container_width=True, hide_index=True, height=360)


def render_ai_chatbot(df: pd.DataFrame):
    st.subheader("AI Chatbot")
    st.markdown(
        '<div class="dashboard-card"><b>Ask about the current quality data</b><br>'
        '<span class="small-muted">Suggested questions: Why did PPM increase? Which part has the highest PPM? '
        'Which process is above target? Compare locations.</span></div>', unsafe_allow_html=True
    )
    question = st.text_input("Type your question", placeholder="Why did PPM increase?")
    if question:
        current = ppm_value(df)
        process = aggregate_ppm(df, ["process"]).sort_values("ppm", ascending=False).head(1)
        part = aggregate_ppm(df, ["part_no_clean"])
        part = part[part["part_no_clean"].astype(str).str.len() > 0].sort_values("ppm", ascending=False).head(1)
        answer = f"Current overall PPM is {current:,.0f}. "
        if not process.empty:
            answer += f"Highest process PPM is {process.iloc[0]['process']} at {process.iloc[0]['ppm']:,.0}. "
        if not part.empty:
            answer += f"Highest part PPM is {part.iloc[0]['part_no_clean']} at {part.iloc[0]['ppm']:,.0}."
        st.info(answer)


def detail_table(df: pd.DataFrame):
    cols = ["Date", "location", "process", "machine", "part_no_clean", "part_name_clean",
            "defect", "rejection quantity", "production quantity", "ppm_denominator", "total_cost", "safe_ppm"]
    cols = [c for c in cols if c in df.columns]
    st.dataframe(df[cols].sort_values("Date", ascending=False), use_container_width=True, height=280, hide_index=True)


def main():
    df = get_dataset()

    # Sidebar: navigation only. Filters are intentionally moved into the top header.
    with st.sidebar:
        st.markdown(
            '<div class="brand"><div class="brand-mark">◇</div><div>'
            '<div class="brand-title">InsightEdge</div><div class="brand-sub">Quality Intelligence</div>'
            '</div></div>', unsafe_allow_html=True
        )
        st.markdown('<div class="nav-label">Navigation</div>', unsafe_allow_html=True)
        pages = [
            "🏠 Overview",
            "📊 PPM Dashboard",
            "📦 Part Analysis",
            "❌ Defect Analysis",
            "⚙️ Process Analysis",
            "🏭 Machine Analysis",
            "📍 Location Analysis",
            "💰 Cost Analysis",
            "📈 Trend Analysis",
            "📄 Reports",
            "🤖 AI Chatbot",
        ]
        page = st.radio("Navigation", pages, label_visibility="collapsed", key="page_selection")
        page = page.split(" ", 1)[1] if " " in page else page

        st.markdown("---")
        st.markdown('<div class="nav-label">Dataset</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="small-muted">Date coverage<br><b>{df["Date"].min():%d %b %Y} – {df["Date"].max():%d %b %Y}</b>'
            f'<br><br>Total records<br><b>{len(df):,}</b>'
            f'<br><br>Locations<br><b>{df["location"].nunique():,}</b></div>', unsafe_allow_html=True
        )
        st.markdown("---")
        st.caption("PPM target: ≤ 20,000")

    period_df, start_date, end_date, selected_location = render_header(df)

    if period_df.empty:
        st.warning("No rows match the current filters. Expand the date range or clear one or more filters.")
        st.stop()

    baseline = previous_equal_period(df, start_date, end_date)

    # Keep the original KPI strip on non-PPM pages; PPM page has its own KPI design.
    if page != "PPM Dashboard":
        kpi_strip(period_df, baseline)

    if page == "Overview":
        render_overview(period_df)
    elif page == "PPM Dashboard":
        render_ppm_dashboard(period_df)
    elif page == "Part Analysis":
        render_part_analysis(period_df)
    elif page == "Defect Analysis":
        render_defect_analysis(period_df)
    elif page == "Process Analysis":
        render_process_analysis(period_df)
    elif page == "Machine Analysis":
        render_machine_analysis(period_df)
    elif page == "Location Analysis":
        render_location_analysis(period_df)
    elif page == "Cost Analysis":
        render_cost_analysis(period_df)
    elif page == "Trend Analysis":
        render_trend_analysis(period_df)
    elif page == "Reports":
        render_reports(period_df)
    elif page == "AI Chatbot":
        render_ai_chatbot(period_df)

    with st.expander("View filtered complaint records"):
        detail_table(period_df)


if __name__ == "__main__":
    main()
