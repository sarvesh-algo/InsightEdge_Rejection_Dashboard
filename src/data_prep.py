from __future__ import annotations

from pathlib import Path
import math
import pandas as pd
from datetime import timedelta

DATA_PATH = Path(__file__).resolve().parents[1] / "files" / "combined_output(1).csv"

NUMERIC_COLUMNS = [
    "rework quantity", "segregation quantity", "deviation quantity",
    "rejection quantity", "production quantity", "RSD", "PPM",
]

TEXT_COLUMNS = [
    "part no.", "part name", "defects", "Defect Description", "process",
    "Process Description", "unit", "machine", "location",
]


def _clean_text_series(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("").str.strip()


def load_data(path: str | Path = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]

    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = _clean_text_series(df[col])

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "Date" not in df.columns:
        raise ValueError("CSV must contain a 'Date' column.")

    df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
    df = df.dropna(subset=["Date"]).copy()

    df["month_start"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    df["month_label"] = df["month_start"].dt.strftime("%b %y")
    df["month_key"] = df["month_start"].dt.strftime("%Y-%m")

    df["location"] = df.get("location", "").astype("string").fillna("").str.upper().str.strip()
    df["process"] = df.get("process", "").astype("string").fillna("").str.upper().str.strip()
    df["machine"] = df.get("machine", "").astype("string").fillna("").str.upper().str.strip()
    df["defect"] = df.get("defects", "").astype("string").fillna("").str.strip()
    df["part_name_clean"] = df.get("part name", "").astype("string").fillna("").str.strip()
    df["part_no_clean"] = (
        df.get("part no.", "").astype("string").fillna("")
        .str.replace("'", "", regex=False).str.strip()
    )

    df["rejection quantity"] = pd.to_numeric(df.get("rejection quantity", 0), errors="coerce").fillna(0)
    df["production quantity"] = pd.to_numeric(df.get("production quantity", 0), errors="coerce").fillna(0)
    df["RSD"] = pd.to_numeric(df.get("RSD", 0), errors="coerce").fillna(0)

    df["total_cost"] = df["rejection quantity"] * df["RSD"]
    df["safe_ppm"] = 0.0
    valid_prod = df["production quantity"] > 0
    df.loc[valid_prod, "safe_ppm"] = (
        df.loc[valid_prod, "rejection quantity"] * 1_000_000
        / df.loc[valid_prod, "production quantity"]
    )
    df["safe_ppm"] = df["safe_ppm"].replace([math.inf, -math.inf], 0).fillna(0)
    return df


def filter_data(
    df: pd.DataFrame,
    start: str | pd.Timestamp | None = None,
    end: str | pd.Timestamp | None = None,
    locations: list[str] | None = None,
    processes: list[str] | None = None,
    machines: list[str] | None = None,
    defects: list[str] | None = None,
    parts: list[str] | None = None,
) -> pd.DataFrame:
    mask = pd.Series(True, index=df.index)
    if start is not None:
        mask &= df["Date"] >= pd.Timestamp(start)
    if end is not None:
        mask &= df["Date"] <= pd.Timestamp(end)
    if locations:
        mask &= df["location"].isin([x.upper().strip() for x in locations])
    if processes:
        mask &= df["process"].isin([x.upper().strip() for x in processes])
    if machines:
        mask &= df["machine"].isin([x.upper().strip() for x in machines])
    if defects:
        mask &= df["defect"].isin([x.strip() for x in defects])
    if parts:
        mask &= df["part_no_clean"].isin([x.strip() for x in parts])
    return df.loc[mask].copy()


def period_for_agenda(df: pd.DataFrame, agenda: str) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Automatic newsletter periods based on the latest month present in the filtered dataset."""
    latest = df["month_start"].max()
    earliest = df["month_start"].min()
    if agenda == "Agenda 2 · Last 6 Months (Excl. Current)":
        end = latest - pd.offsets.MonthBegin(1)
        start = end - pd.DateOffset(months=5)
    elif agenda == "Agenda 3 · Current Month":
        start = latest
        end = latest + pd.offsets.MonthEnd(1)
    elif agenda == "Agenda 4 · Last 6 Months (Incl. Current)":
        start = latest - pd.DateOffset(months=5)
        end = latest + pd.offsets.MonthEnd(1)
    else:
        start = earliest
        end = latest + pd.offsets.MonthEnd(1)
    return pd.Timestamp(start), pd.Timestamp(end)


def top_n(df: pd.DataFrame, column: str, value: str = "rejection quantity", n: int = 5) -> pd.DataFrame:
    if df.empty or column not in df.columns:
        return pd.DataFrame(columns=[column, value])
    out = (
        df[df[column].astype(str).str.len() > 0]
        .groupby(column, as_index=False)[value].sum()
        .sort_values(value, ascending=False).head(n)
    )
    return out


def top_n_by_group(
    df: pd.DataFrame,
    group_column: str,
    category_column: str,
    value: str = "rejection quantity",
    n: int = 3,
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=[group_column, category_column, value])
    x = df[(df[group_column].astype(str).str.len() > 0) & (df[category_column].astype(str).str.len() > 0)]
    agg = x.groupby([group_column, category_column], as_index=False)[value].sum()
    return (
        agg.sort_values([group_column, value], ascending=[True, False])
        .groupby(group_column, group_keys=False).head(n)
    )


def monthly_summary(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby(["month_start", "location"], as_index=False)
        .agg(
            rejection_quantity=("rejection quantity", "sum"),
            total_cost=("total_cost", "sum"),
            production_quantity=("production quantity", "sum"),
        )
        .sort_values(["month_start", "location"])
    )


def monthly_totals(df: pd.DataFrame) -> pd.DataFrame:
    return (
        df.groupby("month_start", as_index=False)
        .agg(
            rejection_quantity=("rejection quantity", "sum"),
            total_cost=("total_cost", "sum"),
            production_quantity=("production quantity", "sum"),
        )
        .sort_values("month_start")
    )


def aggregate_ppm(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Correct PPM aggregation: sum(rejections)/sum(production), not max(row PPM)."""
    out = (
        df.groupby(group_cols, as_index=False)
        .agg(rejection_quantity=("rejection quantity", "sum"), production_quantity=("production quantity", "sum"))
    )
    out["ppm"] = 0.0
    ok = out["production_quantity"] > 0
    out.loc[ok, "ppm"] = out.loc[ok, "rejection_quantity"] * 1_000_000 / out.loc[ok, "production_quantity"]
    return out


def ppm_top_parts(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    out = aggregate_ppm(df, ["part_no_clean"])
    return out.sort_values("ppm", ascending=False).head(n)


def monthly_ppm_top_part_lines(df: pd.DataFrame, max_parts: int = 10) -> pd.DataFrame:
    """Pick the highest-PPM part in each month, then track those parts across every month."""
    base = aggregate_ppm(df, ["month_start", "part_no_clean"])
    if base.empty:
        return base
    winners = (
        base.sort_values(["month_start", "ppm"], ascending=[True, False])
        .groupby("month_start", as_index=False).head(1)["part_no_clean"]
        .drop_duplicates().head(max_parts).tolist()
    )
    months = pd.DataFrame({"month_start": sorted(df["month_start"].dropna().unique())})
    parts = pd.DataFrame({"part_no_clean": winners})
    if parts.empty:
        return pd.DataFrame(columns=["month_start", "part_no_clean", "ppm"])
    grid = months.merge(parts, how="cross")
    tracked = aggregate_ppm(df[df["part_no_clean"].isin(winners)], ["month_start", "part_no_clean"])
    return grid.merge(tracked[["month_start", "part_no_clean", "ppm"]], how="left", on=["month_start", "part_no_clean"]).fillna({"ppm": 0})
