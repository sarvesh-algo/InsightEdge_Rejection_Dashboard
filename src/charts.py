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


def _empty(title: str, height: int = 280) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text="No data", x=.5, y=.5, xref="paper", yref="paper", showarrow=False,
                       font=dict(color=MUTED, size=14))
    return style_figure(fig, title, "", "", height)


def style_figure(fig: go.Figure, title: str, xaxis: str = "", yaxis: str = "", height: int = 280) -> go.Figure:
    fig.update_layout(
        title=dict(text=title, x=0.02, xanchor="left", font=dict(size=14, color=TEXT)),
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=dict(family="Inter, Arial, sans-serif", size=10, color=TEXT),
        margin=dict(l=48, r=18, t=44, b=46),
        height=height,
        hoverlabel=dict(bgcolor="#102d4d", font_color="white"),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="right", x=1,
                    font=dict(size=9, color=MUTED)),
        hovermode="x unified",
    )
    fig.update_xaxes(title_text=xaxis, title_font=dict(size=9, color=MUTED),
                     tickfont=dict(size=9, color=MUTED), showgrid=False, zeroline=False,
                     linecolor=GRID)
    fig.update_yaxes(title_text=yaxis, title_font=dict(size=9, color=MUTED),
                     tickfont=dict(size=9, color=MUTED), showgrid=True, gridcolor=GRID,
                     zeroline=False)
    return fig


def location_bar(df: pd.DataFrame, value_col="rejection quantity", group_col="location",
                 title="Rejections by Location") -> go.Figure:
    if df.empty:
        return _empty(title)
    x = df.groupby(group_col, as_index=False)[value_col].sum().sort_values(value_col, ascending=False)
    total = x[value_col].sum() or 1
    fig = go.Figure(go.Bar(x=x[group_col], y=x[value_col],
        marker_color=[LOCATION_COLORS.get(v, BLUE) for v in x[group_col]],
        text=[f"{v:,.0f}<br>{v/total:.0%}" for v in x[value_col]], textposition="outside",
        hovertemplate="%{x}<br>Rejections: %{y:,.0f}<extra></extra>"))
    return style_figure(fig, title, "Location", "Rejection Qty")


def horizontal_bar(df: pd.DataFrame, category_col: str, value_col="rejection quantity",
                   title="Top Items", n=None) -> go.Figure:
    if df.empty:
        return _empty(title)
    x = df.copy()
    if n:
        x = x.nlargest(n, value_col)
    x = x.sort_values(value_col, ascending=True)
    fig = go.Figure(go.Bar(x=x[value_col], y=x[category_col], orientation="h",
        marker=dict(color=[PALETTE[i % len(PALETTE)] for i in range(len(x))]),
        text=[f"{v:,.0f}" for v in x[value_col]], textposition="outside", cliponaxis=False,
        hovertemplate="%{y}<br>%{x:,.0f}<extra></extra>"))
    return style_figure(fig, title, "Rejection Qty", "")


def grouped_bar(df: pd.DataFrame, category_col: str, group_col: str,
                value_col="rejection quantity", title="Grouped Comparison") -> go.Figure:
    if df.empty:
        return _empty(title)
    fig = go.Figure()
    categories = list(dict.fromkeys(df[category_col].astype(str).tolist()))
    for i, (group, g) in enumerate(df.groupby(group_col)):
        vals = g.set_index(category_col).reindex(categories)[value_col].fillna(0).tolist()
        fig.add_bar(name=str(group), x=categories, y=vals,
                    marker_color=LOCATION_COLORS.get(str(group), PALETTE[i % len(PALETTE)]),
                    text=[f"{v:,.0f}" if v else "" for v in vals], textposition="outside")
    fig.update_layout(barmode="group")
    fig.update_xaxes(tickangle=-35)
    return style_figure(fig, title, "", "Rejection Qty")


def line_chart(df: pd.DataFrame, x_col: str, y_col: str, group_col: str | None = None,
               title="Trend", annotate=False) -> go.Figure:
    if df.empty:
        return _empty(title)
    fig = go.Figure()
    groups = [("Rejections", df)] if group_col is None else list(df.groupby(group_col))
    for i, (name, g) in enumerate(groups):
        g = g.sort_values(x_col)
        color = LOCATION_COLORS.get(str(name), PALETTE[i % len(PALETTE)])
        fig.add_scatter(x=g[x_col], y=g[y_col], mode="lines+markers+text" if annotate else "lines+markers",
                        name=str(name), line=dict(color=color, width=2), marker=dict(size=5),
                        text=[f"{v:,.0f}" for v in g[y_col]] if annotate else None,
                        textposition="top center", textfont=dict(size=8),
                        hovertemplate="%{x}<br>%{y:,.0f}<extra></extra>")
    return style_figure(fig, title, "Month", "Rejection Qty")


def segmented_monthly_share(df: pd.DataFrame, month_col="month_start", group_col="location",
                            value_col="rejection quantity", title="Monthly Contribution %") -> go.Figure:
    if df.empty:
        return _empty(title)
    p = df.pivot_table(index=month_col, columns=group_col, values=value_col, aggfunc="sum", fill_value=0).sort_index()
    share = p.div(p.sum(axis=1).replace(0, math.nan), axis=0).fillna(0) * 100
    fig = go.Figure()
    for i, group in enumerate(share.columns):
        fig.add_bar(x=share.index, y=share[group], name=str(group),
                    marker_color=LOCATION_COLORS.get(str(group), PALETTE[i % len(PALETTE)]),
                    text=[f"{v:.0f}%" if v >= 8 else "" for v in share[group]], textposition="inside")
    fig.update_layout(barmode="stack")
    fig.update_yaxes(range=[0, 100], ticksuffix="%")
    return style_figure(fig, title, "Month", "Share")


def pareto_chart(df: pd.DataFrame, category_col: str, value_col="rejection quantity",
                 top_n=10, title="Pareto Analysis") -> go.Figure:
    if df.empty:
        return _empty(title)
    s = (df[df[category_col].astype(str).str.len() > 0]
         .groupby(category_col, as_index=False)[value_col].sum()
         .sort_values(value_col, ascending=False).head(top_n))
    if s.empty:
        return _empty(title)
    s["cum"] = s[value_col].cumsum() / max(s[value_col].sum(), 1) * 100
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=s[category_col], y=s[value_col], name="Rejection Qty" if value_col == "rejection quantity" else "Rejection Cost",
                marker_color=BLUE, secondary_y=False)
    fig.add_scatter(x=s[category_col], y=s["cum"], name="Cumulative %", mode="lines+markers",
                    line=dict(color=LIME, width=2), secondary_y=True)
    fig.add_hline(y=80, line_dash="dot", line_color=MUTED, secondary_y=True)
    fig.update_yaxes(title_text="Qty" if value_col == "rejection quantity" else "₹ Cost", secondary_y=False,
                     gridcolor=GRID, tickfont=dict(color=MUTED, size=9))
    fig.update_yaxes(title_text="Cumulative %", secondary_y=True, range=[0, 105], ticksuffix="%",
                     showgrid=False, tickfont=dict(color=MUTED, size=9))
    fig.update_xaxes(tickangle=-45)
    return style_figure(fig, title, "", "")


def control_chart(df: pd.DataFrame, x_col: str, y_col: str, title="Control Chart") -> go.Figure:
    if df.empty:
        return _empty(title)
    x = df.sort_values(x_col).copy()
    mean = x[y_col].mean()
    std = x[y_col].std(ddof=0)
    ucl = mean + 3 * std
    lcl = max(0, mean - 3 * std)
    out = (x[y_col] > ucl) | (x[y_col] < lcl)
    fig = go.Figure()
    fig.add_scatter(x=x[x_col], y=x[y_col], mode="lines+markers", name="PPM",
                    line=dict(color=BLUE, width=2))
    fig.add_scatter(x=x[x_col], y=[mean] * len(x), mode="lines", name="Mean",
                    line=dict(color=GREEN, dash="dash"))
    fig.add_scatter(x=x[x_col], y=[ucl] * len(x), mode="lines", name="UCL",
                    line=dict(color=RED, dash="dash"))
    fig.add_scatter(x=x[x_col], y=[lcl] * len(x), mode="lines", name="LCL",
                    line=dict(color=CYAN, dash="dash"))
    if out.any():
        fig.add_scatter(x=x.loc[out, x_col], y=x.loc[out, y_col], mode="markers",
                        name="Out of Control", marker=dict(color=ORANGE, size=10, symbol="circle-open"))
    return style_figure(fig, title, "Month", "PPM", height=300)


def ppm_bar(df: pd.DataFrame, category_col="part_no_clean", ppm_col="ppm",
            title="Top PPM Parts") -> go.Figure:
    if df.empty:
        return _empty(title)
    x = df.sort_values(ppm_col, ascending=True)
    fig = go.Figure(go.Bar(x=x[ppm_col], y=x[category_col], orientation="h",
                           marker_color=PURPLE,
                           text=[f"{v:,.0f}" for v in x[ppm_col]], textposition="outside",
                           cliponaxis=False,
                           hovertemplate="%{y}<br>PPM: %{x:,.0f}<extra></extra>"))
    return style_figure(fig, title, "PPM", "", height=310)


def ppm_lines(df: pd.DataFrame, title="PPM Trends") -> go.Figure:
    if df.empty:
        return _empty(title)
    fig = go.Figure()
    for i, (part, g) in enumerate(df.groupby("part_no_clean")):
        g = g.sort_values("month_start")
        fig.add_scatter(x=g["month_start"], y=g["ppm"], mode="lines+markers",
                        name=str(part), line=dict(color=PALETTE[i % len(PALETTE)], width=1.8), marker=dict(size=4))
    fig.update_layout(legend=dict(orientation="v", x=1.01, y=1, xanchor="left", yanchor="top", font=dict(size=8)))
    return style_figure(fig, title, "Month", "PPM", height=320)


def multi_top_trend(df: pd.DataFrame, category_col: str, title: str,
                    top_per_month=1, max_series=6) -> go.Figure:
    if df.empty:
        return _empty(title)
    monthly = df.groupby(["month_start", category_col], as_index=False)["rejection quantity"].sum()
    winners = monthly.sort_values(["month_start", "rejection quantity"], ascending=[True, False]).groupby("month_start").head(top_per_month)
    cats = winners[category_col].drop_duplicates().head(max_series).tolist()
    months = sorted(df["month_start"].dropna().unique())
    grid = pd.MultiIndex.from_product([months, cats], names=["month_start", category_col]).to_frame(index=False)
    tracked = grid.merge(monthly[monthly[category_col].isin(cats)], how="left", on=["month_start", category_col]).fillna({"rejection quantity": 0})
    return line_chart(tracked, "month_start", "rejection quantity", category_col, title, annotate=False)


def ppm_trend(monthly: pd.DataFrame, target: float = 20000, title="PPM Trend (Overall)") -> go.Figure:
    if monthly.empty:
        return _empty(title)
    x = monthly.sort_values("month_start").copy()
    if "ppm" not in x.columns:
        x["ppm"] = 0.0
        ok = x["ppm_denominator"] > 0
        x.loc[ok, "ppm"] = x.loc[ok, "rejection_quantity"] * 1_000_000 / x.loc[ok, "ppm_denominator"]
    fig = go.Figure()
    fig.add_scatter(x=x["month_start"], y=x["ppm"], mode="lines+markers+text", name="PPM",
                    line=dict(color=BLUE, width=2.5), marker=dict(size=6),
                    text=[f"{v:,.0f}" for v in x["ppm"]], textposition="top center",
                    textfont=dict(size=8), hovertemplate="%{x|%b %Y}<br>PPM: %{y:,.0f}<extra></extra>")
    fig.add_hline(y=target, line_dash="dot", line_color=RED,
                  annotation_text=f"Target {target:,.0f} PPM", annotation_position="top right")
    fig.update_yaxes(tickformat=",.0f")
    return style_figure(fig, title, "Month", "PPM", height=330)


def rolling_ppm_chart(monthly: pd.DataFrame, target: float = 20000, title="PPM with Rolling Average") -> go.Figure:
    if monthly.empty:
        return _empty(title)
    x = monthly.sort_values("month_start").copy()
    if "ppm" not in x.columns:
        x["ppm"] = 0.0
        ok = x["ppm_denominator"] > 0
        x.loc[ok, "ppm"] = x.loc[ok, "rejection_quantity"] * 1_000_000 / x.loc[ok, "ppm_denominator"]
    x["rolling_3m"] = x["ppm"].rolling(3, min_periods=1).mean()
    x["rolling_6m"] = x["ppm"].rolling(6, min_periods=1).mean()
    fig = go.Figure()
    fig.add_scatter(x=x["month_start"], y=x["ppm"], mode="lines+markers", name="Monthly PPM",
                    line=dict(color=BLUE, width=1.6))
    fig.add_scatter(x=x["month_start"], y=x["rolling_3m"], mode="lines", name="Rolling 3M",
                    line=dict(color=GREEN, width=2))
    fig.add_scatter(x=x["month_start"], y=x["rolling_6m"], mode="lines", name="Rolling 6M",
                    line=dict(color=PURPLE, width=2))
    fig.add_hline(y=target, line_dash="dot", line_color=RED)
    return style_figure(fig, title, "Month", "PPM", height=300)


def ppm_rank_bar(df: pd.DataFrame, category_col: str, title: str, top_n: int = 10) -> go.Figure:
    if df.empty:
        return _empty(title)
    x = df[df[category_col].astype(str).str.len() > 0].nlargest(top_n, "ppm").sort_values("ppm")
    fig = go.Figure(go.Bar(x=x["ppm"], y=x[category_col], orientation="h",
                           marker=dict(color=[PALETTE[i % len(PALETTE)] for i in range(len(x))]),
                           text=[f"{v:,.0f}" for v in x["ppm"]], textposition="outside", cliponaxis=False,
                           hovertemplate="%{y}<br>PPM: %{x:,.0f}<extra></extra>"))
    return style_figure(fig, title, "PPM", "", height=max(270, 24 * len(x) + 90))


def ppm_heatmap(df: pd.DataFrame, row_col: str, title: str, top_n: int = 10) -> go.Figure:
    if df.empty:
        return _empty(title, 330)
    base = df.copy()
    base = base[base[row_col].astype(str).str.len() > 0]
    totals = base.groupby(row_col)["rejection quantity"].sum().nlargest(top_n).index.tolist()
    base = base[base[row_col].isin(totals)]
    agg = base.groupby([row_col, "month_start"], as_index=False).agg(
        rejection_quantity=("rejection quantity", "sum"),
        ppm_denominator=("ppm_denominator", "sum"),
    )
    agg["ppm"] = 0.0
    ok = agg["ppm_denominator"] > 0
    agg.loc[ok, "ppm"] = agg.loc[ok, "rejection_quantity"] * 1_000_000 / agg.loc[ok, "ppm_denominator"]
    pivot = agg.pivot(index=row_col, columns="month_start", values="ppm").fillna(0)
    pivot = pivot.loc[[r for r in totals if r in pivot.index]]
    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale=[[0, "#0d5c4b"], [0.5, "#f0c94b"], [1, "#e74c3c"]],
        colorbar=dict(title="PPM", tickfont=dict(color=MUTED)),
        hovertemplate="%{y}<br>%{x|%b %Y}<br>PPM: %{z:,.0f}<extra></extra>",
    ))
    fig.update_xaxes(tickformat="%b %y")
    return style_figure(fig, title, "Month", row_col.title(), height=max(300, 24 * len(pivot) + 110))


def ppm_by_location(df: pd.DataFrame, title="PPM by Location") -> go.Figure:
    if df.empty:
        return _empty(title)
    agg = df.groupby("location", as_index=False).agg(
        rejection_quantity=("rejection quantity", "sum"),
        ppm_denominator=("ppm_denominator", "sum"),
    )
    agg = agg[agg["location"].astype(str).str.len() > 0]
    agg["ppm"] = agg["rejection_quantity"] * 1_000_000 / agg["ppm_denominator"].replace(0, math.nan)
    agg["ppm"] = agg["ppm"].fillna(0)
    agg = agg.sort_values("ppm")
    fig = go.Figure(go.Bar(x=agg["ppm"], y=agg["location"], orientation="h",
                           marker_color=[LOCATION_COLORS.get(v, BLUE) for v in agg["location"]],
                           text=[f"{v:,.0f}" for v in agg["ppm"]], textposition="outside", cliponaxis=False))
    fig.add_vline(x=20000, line_dash="dot", line_color=RED)
    return style_figure(fig, title, "PPM", "", height=280)


def ppm_distribution_chart(df: pd.DataFrame, target=20000, title="PPM Distribution") -> go.Figure:
    if df.empty or "safe_ppm" not in df.columns:
        return _empty(title)
    x = df["safe_ppm"].replace([math.inf, -math.inf], 0).fillna(0)
    fig = go.Figure(go.Histogram(x=x, nbinsx=30, marker_color=BLUE,
                                 hovertemplate="PPM: %{x:,.0f}<br>Rows: %{y}<extra></extra>"))
    fig.add_vline(x=target, line_dash="dot", line_color=RED, annotation_text="Target")
    return style_figure(fig, title, "PPM", "Records", height=300)


def production_vs_ppm(df: pd.DataFrame, title="PPM vs Production Quantity") -> go.Figure:
    if df.empty:
        return _empty(title)
    monthly = df.groupby("month_start", as_index=False).agg(
        production_quantity=("production quantity", "sum"),
        rejection_quantity=("rejection quantity", "sum"),
        ppm_denominator=("ppm_denominator", "sum"),
    )
    monthly["ppm"] = 0.0
    ok = monthly["ppm_denominator"] > 0
    monthly.loc[ok, "ppm"] = monthly.loc[ok, "rejection_quantity"] * 1_000_000 / monthly.loc[ok, "ppm_denominator"]
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_bar(x=monthly["month_start"], y=monthly["production_quantity"], name="Production Qty",
                marker_color=GREEN, opacity=.65, secondary_y=False)
    fig.add_scatter(x=monthly["month_start"], y=monthly["ppm"], name="PPM", mode="lines+markers",
                    line=dict(color=BLUE, width=2.5), secondary_y=True)
    fig.update_yaxes(title_text="Production Qty", secondary_y=False)
    fig.update_yaxes(title_text="PPM", secondary_y=True)
    return style_figure(fig, title, "Month", "", height=300)


def ppm_gauge(value: float, target: float = 20000, title="PPM Performance vs Target") -> go.Figure:
    max_value = max(target * 2, value * 1.15, 40000)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={"valueformat": ",.0f", "font": {"size": 30, "color": TEXT}},
        title={"text": title, "font": {"size": 14, "color": TEXT}},
        gauge={
            "axis": {"range": [0, max_value], "tickfont": {"color": MUTED}},
            "bar": {"color": BLUE, "thickness": .28},
            "bgcolor": CARD,
            "borderwidth": 0,
            "steps": [
                {"range": [0, target], "color": "#1f8f63"},
                {"range": [target, target * 1.25], "color": "#d9a928"},
                {"range": [target * 1.25, max_value], "color": "#b83b4b"},
            ],
            "threshold": {"line": {"color": "white", "width": 3}, "thickness": .8, "value": target},
        },
    ))
    fig.add_annotation(x=.5, y=.10, xref="paper", yref="paper",
                       text=f"Target ≤ {target:,.0f} PPM", showarrow=False,
                       font=dict(size=11, color=MUTED))
    return style_figure(fig, "", "", "", height=330)


def ppm_donut(df: pd.DataFrame, title="PPM Contribution by Defect") -> go.Figure:
    if df.empty:
        return _empty(title)
    x = df[df["defect"].astype(str).str.len() > 0].groupby("defect", as_index=False)["rejection quantity"].sum()
    x = x.nlargest(8, "rejection quantity")
    if x.empty:
        return _empty(title)
    fig = go.Figure(go.Pie(labels=x["defect"], values=x["rejection quantity"], hole=.62,
                           textinfo="percent", marker=dict(colors=PALETTE)))
    fig.add_annotation(text="Rejections", x=.5, y=.5, showarrow=False, font=dict(size=14, color=TEXT))
    return style_figure(fig, title, "", "", height=320)


def ppm_part_lines(df: pd.DataFrame, max_parts=6, title="Top PPM Parts · Monthly Trend") -> go.Figure:
    base = df.copy()
    if base.empty:
        return _empty(title)
    overall = base.groupby("part_no_clean")["rejection quantity"].sum().nlargest(max_parts).index.tolist()
    base = base[base["part_no_clean"].isin(overall)]
    agg = base.groupby(["month_start", "part_no_clean"], as_index=False).agg(
        rejection_quantity=("rejection quantity", "sum"),
        ppm_denominator=("ppm_denominator", "sum"),
    )
    agg["ppm"] = 0.0
    ok = agg["ppm_denominator"] > 0
    agg.loc[ok, "ppm"] = agg.loc[ok, "rejection_quantity"] * 1_000_000 / agg.loc[ok, "ppm_denominator"]
    return ppm_lines(agg, title)


def create_cost_pie_chart(df: pd.DataFrame) -> go.Figure:
    if df.empty:
        return _empty("Cost Distribution")
    fig = px.pie(df, values="Cost", names="Category", title="Cost Distribution")
    fig.update_layout(paper_bgcolor=CARD, plot_bgcolor=CARD, font=dict(color=TEXT))
    return fig
