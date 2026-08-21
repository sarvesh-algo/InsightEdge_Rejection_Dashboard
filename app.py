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
    data_min = pd.Timestamp(df["Date"].min()).normalize()
    data_max = pd.Timestamp(df["Date"].max()).normalize()

    st.markdown(
        '<div class="page-head"><div><div class="page-title">InsightEdge Quality Intelligence</div>'
        '<div class="page-sub">Real-time quality, rejection and PPM performance</div></div>'
        '<div class="page-sub">Executive Quality Dashboard</div></div>',
        unsafe_allow_html=True,
    )

    # Only Location and Date Range remain at the top of the page.
    left, right = st.columns([1.05, 1.25])

    with left:
        locations = ["All"] + sorted(
            [x for x in df["location"].unique() if x]
        )
        selected_location = st.selectbox(
            "Location",
            locations,
            index=0,
            key="top_location_v4",
        )

    with right:
        selected_range = st.date_input(
            "Date Range",
            value=(data_min.date(), data_max.date()),
            min_value=data_min.date(),
            max_value=data_max.date(),
            key="top_date_range_v4",
        )

    if isinstance(selected_range, (tuple, list)) and len(selected_range) == 2:
        start_date, end_date = selected_range
    else:
        start_date = selected_range
        end_date = selected_range

    # Filtering is intentionally handled in main(), using sidebar controls.
    return (
        filter_data(
            df,
            start_date,
            end_date,
            locations=None if selected_location == "All" else [selected_location],
        ),
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

    # Requested mentor change: keep the control chart on Overview.
    monthly = aggregate_ppm(df, ["month_start"])
    if not monthly.empty:
        chart(control_chart(monthly, "month_start", "ppm", "PPM Control Chart · 3σ Limits"))


def render_ppm_dashboard(df: pd.DataFrame):
    """PPM dashboard with only the mentor-requested removals/changes."""
    monthly = aggregate_ppm(df, ["month_start"])
    process = aggregate_ppm(df, ["process"])
    machine = aggregate_ppm(df, ["machine"])
    location = aggregate_ppm(df, ["location"])
    part = aggregate_ppm(df, ["part_no_clean"])

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

    # ---------------------------------------------------------
    # Mentor-requested top row:
    # Left  = PPM by Location
    # Right = PPM Trend
    # ---------------------------------------------------------
    c1, c2 = st.columns(2)
    with c1:
        chart(ppm_by_location(df, "PPM by Location"))
    with c2:
        chart(ppm_trend(monthly, TARGET_PPM, "PPM Trend (Overall)"))

    # Keep the existing gauge + alert panel; it was not requested to be removed.
    c1, c2 = st.columns([1, 1.6])
    with c1:
        chart(ppm_gauge(overall, TARGET_PPM))
    with c2:
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
            alerts = [
                ("🟢", "No PPM threshold breaches in the selected period"),
                ("🔵", "Continue monitoring monthly movement"),
                ("🟢", "Target performance is currently stable"),
            ]
        for icon, text in alerts[:5]:
            st.markdown(
                f'<div style="padding:9px 4px;border-bottom:1px solid #173a5d;font-size:10px;">'
                f'<span style="font-size:14px">{icon}</span>&nbsp; {text}</div>',
                unsafe_allow_html=True,
            )

    # Mentor requested these two charts to be commented out.
    # chart(ppm_rank_bar(process, "process", "PPM by Process", 10))
    # chart(ppm_rank_bar(machine, "machine", "PPM by Machine · Top 10", 10))

    # Top 10 parts remains, but mentor requested TABLE format instead of chart.
    st.markdown('<div class="section-title">Top 10 Parts by PPM</div>', unsafe_allow_html=True)
    top_parts = ppm_top_parts(df, 10).copy()
    if not top_parts.empty:
        preferred = [c for c in ["part_no_clean", "ppm", "rejection quantity", "ppm_denominator"] if c in top_parts.columns]
        table = top_parts[preferred].copy()
        rename = {
            "part_no_clean": "Part No.",
            "ppm": "PPM",
            "rejection quantity": "Rejection Qty",
            "ppm_denominator": "Denominator",
        }
        table = table.rename(columns=rename)
        if "PPM" in table.columns:
            table["PPM"] = table["PPM"].round(0).astype(int)
        st.dataframe(table, use_container_width=True, hide_index=True, height=300)
    else:
        st.info("No part-level PPM data available for the selected filters.")

    # Mentor requested Defect Contribution to be commented out.
    # chart(ppm_donut(df, "Defect Contribution to Rejections"))

    # Mentor requested Rolling 3M / 6M PPM to be commented out.
    # chart(rolling_ppm_chart(monthly, TARGET_PPM, "Monthly PPM · Rolling 3M & 6M"))

    # Keep the existing part-level PPM plots requested earlier.
    # These are intentionally retained because they were not part of the removal list.
    c1, c2 = st.columns(2)
    with c1:
        chart(ppm_part_lines(df, max_parts=6, title="Top Parts · Monthly PPM Trend"))
    with c2:
        chart(production_vs_ppm(df, "Production Quantity vs PPM"))

    ppm_selected_parts = st.session_state.get("ppm_selected_parts", [])
    ppm_selected_part = st.session_state.get("ppm_selected_part", "All")

    p1, p2 = st.columns(2)
    with p1:
        if ppm_selected_parts:
            selected_parts_df = df[df["part_no_clean"].isin(ppm_selected_parts)]
            chart(
                ppm_part_lines(
                    selected_parts_df,
                    max_parts=max(1, len(ppm_selected_parts)),
                    title="Monthly PPM · Selected Parts",
                )
            )
        else:
            chart(ppm_part_lines(df, max_parts=6, title="Monthly PPM · Top Parts"))

    with p2:
        if ppm_selected_part != "All":
            single_part_df = df[df["part_no_clean"] == ppm_selected_part]
            chart(
                ppm_part_lines(
                    single_part_df,
                    max_parts=1,
                    title=f"PPM Over Time · {ppm_selected_part}",
                )
            )
        else:
            st.markdown(
                '<div class="dashboard-card" style="height:100%;">'
                '<b>PPM Over Time · Selected Part</b><br><br>'
                '<span class="small-muted">Select a part number from the PPM Part Analysis section in the sidebar.</span>'
                '</div>',
                unsafe_allow_html=True,
            )

    # ---------------------------------------------------------
    # Mentor request: remove heatmaps and everything that was
    # below the heatmap section. Therefore the PPM dashboard ends
    # here; no heatmaps/distribution/pareto/AI summary are rendered.
    # ---------------------------------------------------------


def _unique_join(series: pd.Series) -> str:
    values = []
    for value in series.dropna().astype(str):
        value = value.strip()
        if value and value.lower() not in {"nan", "none"} and value not in values:
            values.append(value)
    return ", ".join(values)


def _customer_complaint_part_tables(df: pd.DataFrame):
    """Build the two newsletter-style Top-50 part tables.

    The requested newsletter period is fixed to August 2024 through June 2025.
    Occurrences mean rejection-entry rows for each part; rejection quantity and
    cost are summed.
    """
    start = pd.Timestamp("2024-08-01")
    end = pd.Timestamp("2025-06-30 23:59:59")
    work = df.copy()
    work["Date"] = pd.to_datetime(work["Date"], errors="coerce")
    work = work[(work["Date"] >= start) & (work["Date"] <= end)].copy()

    if work.empty or "part_no_clean" not in work.columns:
        return pd.DataFrame(), pd.DataFrame()

    work["_month"] = work["Date"].dt.to_period("M")
    months = pd.period_range("2024-08", "2025-06", freq="M")
    month_labels = ["Aug", "Sept", "Oct", "Nov", "Dec", "Jan", "Feb", "Mar", "Apr", "May", "June"]

    # Normalize numeric columns without changing the source dataframe.
    for col in ["rejection quantity", "total_cost"]:
        if col in work.columns:
            work[col] = pd.to_numeric(work[col], errors="coerce").fillna(0)
        else:
            work[col] = 0.0

    # A rejection occurrence means an actual rejection entry, i.e. a row
    # with positive rejection quantity. Other quality/activity rows are not
    # counted as rejection occurrences.
    work = work[work["rejection quantity"] > 0].copy()

    if work.empty:
        return pd.DataFrame(), pd.DataFrame()

    group_cols = "part_no_clean"
    grouped = work.groupby(group_cols, dropna=False)

    base = grouped.agg(
        **{
            "Total rejection occurrences": ("part_no_clean", "size"),
            "Total rejection quantity": ("rejection quantity", "sum"),
            "Total rejection cost": ("total_cost", "sum"),
        }
    ).reset_index()

    # Monthly occurrence counts.
    # Monthly occurrence counts. Use groupby/unstack rather than pivot_table
    # because the part number is both the index and the occurrence value.
    occ = (
        work.groupby([group_cols, "_month"], dropna=False)
        .size()
        .unstack("_month", fill_value=0)
        .reindex(columns=months, fill_value=0)
        .reset_index()
    )
    occ.columns = [group_cols] + month_labels

    # Monthly rejection quantities.
    qty = (
        work.groupby([group_cols, "_month"], dropna=False)["rejection quantity"]
        .sum()
        .unstack("_month", fill_value=0)
        .reindex(columns=months, fill_value=0)
        .reset_index()
    )
    qty.columns = [group_cols] + month_labels

    # Unique descriptors for the whole requested period.
    descriptor = grouped.agg(
        **{
            "Defects": ("defect", _unique_join) if "defect" in work.columns else ("part_no_clean", lambda s: ""),
            "Processes": ("process", _unique_join) if "process" in work.columns else ("part_no_clean", lambda s: ""),
            "Location(s)": ("location", _unique_join) if "location" in work.columns else ("part_no_clean", lambda s: ""),
        }
    ).reset_index()

    common = base.merge(descriptor, on=group_cols, how="left")

    # Table 1: rank by rejection-entry occurrences.
    table_occ = occ.merge(common, on=group_cols, how="left")
    table_occ = table_occ[
        [group_cols] + month_labels + [
            "Total rejection occurrences",
            "Total rejection quantity",
            "Total rejection cost",
            "Defects",
            "Processes",
            "Location(s)",
        ]
    ]
    table_occ = table_occ.sort_values(
        ["Total rejection occurrences", "Total rejection quantity"],
        ascending=[False, False],
    ).head(50).reset_index(drop=True)

    # Table 2: rank by rejection quantity.
    table_qty = qty.merge(common, on=group_cols, how="left")
    table_qty = table_qty[
        [group_cols] + month_labels + [
            "Total rejection quantity",
            "Total rejection occurrences",
            "Total rejection cost",
            "Defects",
            "Processes",
            "Location(s)",
        ]
    ]
    table_qty = table_qty.sort_values(
        ["Total rejection quantity", "Total rejection occurrences"],
        ascending=[False, False],
    ).head(50).reset_index(drop=True)

    # Presentation-friendly names / number formats.
    table_occ = table_occ.rename(columns={"part_no_clean": "Part No."})
    table_qty = table_qty.rename(columns={"part_no_clean": "Part No."})
    for table in [table_occ, table_qty]:
        for col in month_labels:
            table[col] = pd.to_numeric(table[col], errors="coerce").fillna(0).round(0).astype(int)
        for col in ["Total rejection occurrences", "Total rejection quantity"]:
            if col in table.columns:
                table[col] = pd.to_numeric(table[col], errors="coerce").fillna(0).round(0).astype(int)
        if "Total rejection cost" in table.columns:
            table["Total rejection cost"] = pd.to_numeric(table["Total rejection cost"], errors="coerce").fillna(0).round(2)

    return table_occ, table_qty


def render_part_analysis(df: pd.DataFrame):
    st.subheader("Part Analysis")

    # Keep the original Part Analysis plots. The requested tables are added
    # below them instead of replacing/removing the visual analysis.
    c1, c2 = st.columns(2)
    with c1:
        chart(horizontal_bar(
            top_n(df, "part_name_clean", n=10).rename(columns={"part_name_clean":"Part"}),
            "Part",
            title="Top 10 Defective Parts",
        ))
    with c2:
        chart(ppm_bar(ppm_top_parts(df, 10), title="Top 10 Parts by PPM"))
    chart(multi_top_trend(df, "part_name_clean", "Top Defective Parts · 6M Trend", max_series=5))

    st.markdown('<div class="section-title">Customer Complaints · Top 50 Parts</div>', unsafe_allow_html=True)
    st.caption("Fixed newsletter period: August 2024 to June 2025 · All locations")

    occurrence_table, quantity_table = _customer_complaint_part_tables(df)

    st.markdown(
        '<div class="section-title">1. Top 50 Parts with Highest Rejection Occurrences</div>',
        unsafe_allow_html=True,
    )
    if occurrence_table.empty:
        st.info("No complaint records found for August 2024 to June 2025.")
    else:
        st.dataframe(
            occurrence_table,
            use_container_width=True,
            hide_index=True,
            height=520,
        )

    st.markdown(
        '<div class="section-title">2. Top 50 Parts with Highest Rejection Quantities</div>',
        unsafe_allow_html=True,
    )
    if quantity_table.empty:
        st.info("No complaint records found for August 2024 to June 2025.")
    else:
        st.dataframe(
            quantity_table,
            use_container_width=True,
            hide_index=True,
            height=520,
        )


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

    # Sidebar: keep the existing navigation/design and move all secondary
    # filters here. Nothing from the existing navigation is removed.
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

        page = st.radio(
            "Navigation",
            pages,
            label_visibility="collapsed",
            key="page_selection",
        )
        page = page.split(" ", 1)[1] if " " in page else page

        st.markdown("---")
        st.markdown('<div class="nav-label">Dashboard Filters</div>', unsafe_allow_html=True)

        selected_processes = st.multiselect(
            "Process",
            sorted([x for x in df["process"].unique() if x]),
            key="sidebar_processes_v4",
        )

        selected_machines = st.multiselect(
            "Machine",
            sorted([x for x in df["machine"].unique() if x]),
            key="sidebar_machines_v4",
        )

        selected_parts = st.multiselect(
            "Part",
            sorted([x for x in df["part_no_clean"].unique() if x]),
            max_selections=20,
            key="sidebar_parts_v4",
        )

        selected_defects = st.multiselect(
            "Defect",
            sorted([x for x in df["defect"].unique() if x]),
            max_selections=20,
            key="sidebar_defects_v4",
        )

        # PPM-specific selectors are also kept in the sidebar so the
        # dashboard itself remains clean and compact.
        if page == "PPM Dashboard":
            st.markdown("---")
            st.markdown('<div class="nav-label">PPM Part Analysis</div>', unsafe_allow_html=True)

            ppm_parts = st.multiselect(
                "Compare Parts",
                sorted([x for x in df["part_no_clean"].unique() if x]),
                max_selections=6,
                key="ppm_selected_parts",
                help="Monthly PPM for the selected parts.",
            )

            ppm_single = st.selectbox(
                "PPM Over Time · Part",
                ["All"] + sorted([x for x in df["part_no_clean"].unique() if x]),
                key="ppm_selected_part",
                help="Show PPM over time for one selected part.",
            )

        st.markdown("---")
        st.markdown('<div class="nav-label">Dataset</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="small-muted">Date coverage<br><b>{df["Date"].min():%d %b %Y} – {df["Date"].max():%d %b %Y}</b>'
            f'<br><br>Total records<br><b>{len(df):,}</b>'
            f'<br><br>Locations<br><b>{df["location"].nunique():,}</b></div>',
            unsafe_allow_html=True,
        )
        st.markdown("---")
        st.caption("PPM target: ≤ 20,000")

    # Only Location + Date Range are rendered at the top.
    period_df, start_date, end_date, selected_location = render_header(df)

    # Apply sidebar filters to the already date/location-filtered data.
    period_df = filter_data(
        df,
        start_date,
        end_date,
        locations=None if selected_location == "All" else [selected_location],
        processes=selected_processes or None,
        machines=selected_machines or None,
        defects=selected_defects or None,
        parts=selected_parts or None,
    )

    if period_df.empty:
        st.warning(
            "No rows match the current filters. Expand the date range or clear one or more filters."
        )
        st.stop()

    baseline = previous_equal_period(df, start_date, end_date)

    # Keep the original KPI strip on non-PPM pages; the existing PPM dashboard
    # has its own KPI strip and all its original visualizations.
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
