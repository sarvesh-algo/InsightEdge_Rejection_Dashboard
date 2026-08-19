from __future__ import annotations

import math
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.express as px

BG = "#07182c"
CARD = "#0d2540"
GRID = "rgba(151, 180, 210, 0.12)"
TEXT = "#dce8f6"
MUTED = "#8fa9c4"
BLUE = "#2f8cff"
CYAN = "#24c8d8"
GREEN = "#34d399"
LIME = "#70e36f"
PURPLE = "#b05cff"
ORANGE = "#f5a524"
RED = "#ff5c72"
YELLOW = "#f7c948"

LOCATION_COLORS = {"PUN": CYAN, "LKN": ORANGE, "JSR": GREEN}
PALETTE = [BLUE, CYAN, GREEN, PURPLE, ORANGE, RED, YELLOW, "#6ea8fe", "#c084fc", "#2dd4bf"]


def _empty(title: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text="No data", x=.5, y=.5, xref="paper", yref="paper", showarrow=False, font=dict(color=MUTED, size=14))
    return style_figure(fig, title, "", "")


def style_figure(fig: go.Figure, title: str, xaxis: str = "", yaxis: str = "", height: int = 250) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, x=0.02, xanchor="left", font=dict(size=14, color=TEXT)),
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=dict(family="Inter, Arial, sans-serif", size=10, color=TEXT),
        margin=dict(l=48, r=18, t=42, b=42),
        height=height,
        hoverlabel=dict(bgcolor="#102d4d", font_color="white"),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1, font=dict(size=9, color=MUTED)),
    )
    fig.update_xaxes(title_text=xaxis, title_font=dict(size=9, color=MUTED), tickfont=dict(size=9, color=MUTED), showgrid=False, zeroline=False, linecolor=GRID)
    fig.update_yaxes(title_text=yaxis, title_font=dict(size=9, color=MUTED), tickfont=dict(size=9, color=MUTED), showgrid=True, gridcolor=GRID, zeroline=False)
    return fig


def location_bar(df: pd.DataFrame, value_col="rejection quantity", group_col="location", title="Rejections by Location") -> go.Figure:
    if df.empty: return _empty(title)
    x = df.groupby(group_col, as_index=False)[value_col].sum().sort_values(value_col, ascending=False)
    total = x[value_col].sum() or 1
    fig = go.Figure(go.Bar(
        x=x[group_col], y=x[value_col],
        marker_color=[LOCATION_COLORS.get(v, BLUE) for v in x[group_col]],
        text=[f"{v:,.0f}<br>{v/total:.0%}" for v in x[value_col]], textposition="outside",
        hovertemplate="%{x}<br>Rejections: %{y:,.0f}<extra></extra>"
    ))
    return style_figure(fig, title, "Location", "Rejection Qty")


def horizontal_bar(df: pd.DataFrame, category_col: str, value_col="rejection quantity", title="Top Items", n=None) -> go.Figure:
    if df.empty: return _empty(title)
    x = df.copy()
    if n: x = x.nlargest(n, value_col)
    x = x.sort_values(value_col, ascending=True)
    fig = go.Figure(go.Bar(
        x=x[value_col], y=x[category_col], orientation="h",
        marker=dict(color=[PALETTE[i % len(PALETTE)] for i in range(len(x))]),
        text=[f"{v:,.0f}" for v in x[value_col]], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>%{x:,.0f}<extra></extra>"
    ))
    return style_figure(fig, title, "Rejection Qty", "")


def grouped_bar(df: pd.DataFrame, category_col: str, group_col: str, value_col="rejection quantity", title="Grouped Comparison") -> go.Figure:
    if df.empty: return _empty(title)
    fig = go.Figure()
    categories = list(dict.fromkeys(df[category_col].astype(str).tolist()))
    for i, (group, g) in enumerate(df.groupby(group_col)):
        s = g.set_index(category_col).reindex(categories).astype(pd.StringDtype()).fillna('0')
        vals = s[value_col].tolist()
        fig.add_bar(name=str(group), x=categories, y=vals, marker_color=LOCATION_COLORS.get(str(group), PALETTE[i % len(PALETTE)]), text=[f"{v}" if v else "" for v in vals], textposition="outside")
    fig.update_layout(barmode="group")
    fig.update_xaxes(tickangle=-35)
    return style_figure(fig, title, "", "Rejection Qty")


def line_chart(df: pd.DataFrame, x_col: str, y_col: str, group_col: str | None = None, title="Trend", annotate=False) -> go.Figure:
    if df.empty: return _empty(title)
    fig = go.Figure()
    if group_col is None:
        groups = [("Rejections", df)]
    else:
        groups = list(df.groupby(group_col))
    for i, (name, g) in enumerate(groups):
        g = g.sort_values(x_col)
        color = LOCATION_COLORS.get(str(name), PALETTE[i % len(PALETTE)])
        fig.add_scatter(
            x=g[x_col], y=g[y_col], mode="lines+markers+text" if annotate else "lines+markers",
            name=str(name), line=dict(color=color, width=2), marker=dict(size=5),
            text=[f"{v:,.0f}" for v in g[y_col]] if annotate else None,
            textposition="top center", textfont=dict(size=8),
            hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>"
        )
    return style_figure(fig, title, "Month", "Rejection Qty")


def segmented_monthly_share(df: pd.DataFrame, month_col="month_start", group_col="location", value_col="rejection quantity", title="Monthly Contribution %") -> go.Figure:
    if df.empty: return _empty(title)
    p = df.pivot_table(index=month_col, columns=group_col, values=value_col, aggfunc="sum", fill_value=0).sort_index()
    share = p.div(p.sum(axis=1).replace(0, math.nan), axis=0).fillna(0) * 100
    fig = go.Figure()
    for i, group in enumerate(share.columns):
        fig.add_bar(x=share.index, y=share[group], name=str(group), marker_color=LOCATION_COLORS.get(str(group), PALETTE[i]), text=[f"{v:.0f}%" if v >= 8 else "" for v in share[group]], textposition="inside")
    fig.update_layout(barmode="stack")
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    return style_figure(fig, title, "Month", "Share")


def pareto_chart(df: pd.DataFrame, category_col: str, value_col="rejection quantity", top_n=10, title="Pareto Analysis") -> go.Figure:
    if df.empty: return _empty(title)
    s = df[df[category_col].astype(str).str.len() > 0].groupby(category_col, as_index=False)[value_col].sum().sort_values(value_col, ascending=False).head(top_n)
    if s.empty: return _empty(title)
    s["cum"] = s[value_col].cumsum() / max(s[value_col].sum(), 1) * 100
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=s[category_col], y=s[value_col], name="Rejection Qty" if value_col == "rejection quantity" else "Rejection Cost", marker_color=BLUE, secondary_y=False)
    fig.add_scatter(x=s[category_col], y=s["cum"], name="Cumulative %", mode="lines+markers", line=dict(color=LIME, width=2), secondary_y=True)
    fig.add_hline(y=80, line_dash="dot", line_color=MUTED, secondary_y=True)
    fig.update_yaxes(title_text="Qty" if value_col == "rejection quantity" else "₹ Cost", secondary_y=False, gridcolor=GRID, tickfont=dict(color=MUTED, size=9))
    fig.update_yaxes(title_text="Cumulative %", secondary_y=True, range=[0, 105], ticksuffix="%", showgrid=False, tickfont=dict(color=MUTED, size=9))
    fig.update_xaxes(tickangle=-35)
    return style_figure(fig, title, "", "")


def control_chart(df: pd.DataFrame, x_col: str, y_col: str, title="Control Chart") -> go.Figure:
    if df.empty: return _empty(title)
    x = df.sort_values(x_col).copy()
    mean = x[y_col].mean(); std = x[y_col].std(ddof=0)
    ucl = mean + 3 * std; lcl = max(0, mean - 3 * std)
    out = (x[y_col] > ucl) | (x[y_col] < lcl)
    fig = go.Figure()
    fig.add_scatter(x=x[x_col], y=x[y_col], mode="lines+markers", name="Rejections", line=dict(color=BLUE, width=2))
    fig.add_scatter(x=x[x_col], y=[mean]*len(x), mode="lines", name="Mean", line=dict(color=GREEN, dash="dash"))
    fig.add_scatter(x=x[x_col], y=[ucl]*len(x), mode="lines", name="UCL", line=dict(color=RED, dash="dash"))
    fig.add_scatter(x=x[x_col], y=[lcl]*len(x), mode="lines", name="LCL", line=dict(color=CYAN, dash="dash"))
    if out.any(): fig.add_scatter(x=x.loc[out, x_col], y=x.loc[out, y_col], mode="markers", name="Out of Control", marker=dict(color=ORANGE, size=9, symbol="circle-open"))
    return style_figure(fig, title, "Month", "Rejection Qty")


def ppm_bar(df: pd.DataFrame, category_col="part_no_clean", ppm_col="ppm", title="Top PPM Parts") -> go.Figure:
    if df.empty: return _empty(title)
    x = df.sort_values(ppm_col, ascending=False)
    fig = go.Figure(go.Bar(x=x[category_col], y=x[ppm_col], marker_color=PURPLE, text=[f"{v:,.0f}" for v in x[ppm_col]], textposition="outside"))
    fig.update_xaxes(tickangle=-35)
    return style_figure(fig, title, "Part No.", "PPM")


def ppm_lines(df: pd.DataFrame, title="PPM Trends") -> go.Figure:
    if df.empty: return _empty(title)
    fig = go.Figure()
    for i, (part, g) in enumerate(df.groupby("part_no_clean")):
        fig.add_scatter(x=g["month_start"], y=g["ppm"], mode="lines+markers", name=str(part), line=dict(color=PALETTE[i % len(PALETTE)], width=1.6), marker=dict(size=4))
    fig.update_layout(legend=dict(orientation="v", x=1.01, y=1, xanchor="left", yanchor="top", font=dict(size=7)))
    return style_figure(fig, title, "Month", "PPM", height=260)


def multi_top_trend(df: pd.DataFrame, category_col: str, title: str, top_per_month=1, max_series=6) -> go.Figure:
    if df.empty: return _empty(title)
    monthly = df.groupby(["month_start", category_col], as_index=False)["rejection quantity"].sum()
    winners = monthly.sort_values(["month_start", "rejection quantity"], ascending=[True, False]).groupby("month_start").head(top_per_month)
    cats = winners[category_col].drop_duplicates().head(max_series).tolist()
    months = sorted(df["month_start"].dropna().unique())
    grid = pd.MultiIndex.from_product([months, cats], names=["month_start", category_col]).to_frame(index=False)
    tracked = grid.merge(monthly[monthly[category_col].isin(cats)], how="left", on=["month_start", category_col]).fillna({"rejection quantity": 0})
    return line_chart(tracked, "month_start", "rejection quantity", category_col, title, annotate=False)


def create_cost_pie_chart(df: pd.DataFrame) -> px.Pie:
    """
    Creates a pie chart from cost data.
    
    Args:
        df (pd.DataFrame): DataFrame containing cost data
    
    Returns:
        px.Pie: Plotly Express pie chart figure
    """
    # Assuming cost data is in a column named 'Cost'
    fig = px.pie(df, values='Cost', names='Category', title='Cost Distribution')
    return fig
