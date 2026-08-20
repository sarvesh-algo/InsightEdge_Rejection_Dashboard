from __future__ import annotations

from pathlib import Path
import math
import pandas as pd

# The uploaded project normally keeps the CSV under files/.
# The fallback candidates make the app work with the uploaded CSV name as well.
_BASE_DIR = Path(__file__).resolve().parents[1]
_CANDIDATE_PATHS = [
    _BASE_DIR / "files" / "combined_output(1).csv",
    _BASE_DIR / "files" / "combined_output(1)(2).csv",
    Path(__file__).resolve().parent / "files" / "combined_output(1).csv",
    Path(__file__).resolve().parent / "files" / "combined_output(1)(2).csv",
    Path("combined_output(1).csv"),
    Path("combined_output(1)(2).csv"),
]
DATA_PATH = next((p for p in _CANDIDATE_PATHS if p.exists()), _CANDIDATE_PATHS[0])

NUMERIC_COLUMNS = [
    "rework quantity", "segregation quantity", "deviation quantity",
    "rejection quantity", "production quantity", "sale quantity", "RSD", "PPM",
]

TEXT_COLUMNS = [
    "part no.", "part name", "defects", "Defect Description", "process",
    "Process Description", "unit", "machine", "location",
]


def _clean_text_series(series: pd.Series) -> pd.Series:
    return series.astype("string").fillna("").str.strip()


def load_data(path: str | Path = DATA_PATH) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"CSV file not found. Expected one of: {', '.join(map(str, _CANDIDATE_PATHS))}"
        )

    df = pd.read_csv(path)
    df.columns = [str(c).strip() for c in df.columns]

    # Normalize a few common source-name variations.
    aliases = {
        "Sale Qty": "sale quantity",
        "Sale Quantity": "sale quantity",
        "sale_qty": "sale quantity",
        "Rejection Qty": "rejection quantity",
        "Rejection Quantity": "rejection quantity",
        "Production Qty": "production quantity",
        "Production Quantity": "production quantity",
    }
    for old, new in aliases.items():
        if old in df.columns and new not in df.columns:
            df = df.rename(columns={old: new})

    for col in TEXT_COLUMNS:
        if col in df.columns:
            df[col] = _clean_text_series(df[col])

    for col in NUMERIC_COLUMNS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "Date" not in df.columns:
        raise ValueError("CSV must contain a 'Date' column.")

    # Support the existing DD-MM-YYYY source and fall back to pandas parsing.
    parsed = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
    fallback = pd.to_datetime(df["Date"], errors="coerce", dayfirst=True)
    df["Date"] = parsed.fillna(fallback)
    df = df.dropna(subset=["Date"]).copy()

    df["month_start"] = df["Date"].dt.to_period("M").dt.to_timestamp()
    df["month_label"] = df["month_start"].dt.strftime("%b %y")
    df["month_key"] = df["month_start"].dt.strftime("%Y-%m")

    for col in ["location", "process", "machine"]:
        if col in df.columns:
            df[col] = df[col].astype("string").fillna("").str.upper().str.strip()
        else:
            df[col] = ""

    df["defect"] = df.get("defects", "").astype("string").fillna("").str.strip()
    df["part_name_clean"] = df.get("part name", "").astype("string").fillna("").str.strip()
    df["part_no_clean"] = (
        df.get("part no.", "").astype("string").fillna("")
        .str.replace("'", "", regex=False).str.strip()
    )

    df["rejection quantity"] = pd.to_numeric(
        df.get("rejection quantity", 0), errors="coerce"
    ).fillna(0)
    df["production quantity"] = pd.to_numeric(
        df.get("production quantity", 0), errors="coerce"
    ).fillna(0)
    df["RSD"] = pd.to_numeric(df.get("RSD", 0), errors="coerce").fillna(0)

    # The current uploaded CSV has Production Quantity but no Sale Quantity.
    # Use Sale Quantity when present; otherwise Production Quantity is the
    # available denominator. This preserves the newsletter's PPM formula.
    if "sale quantity" in df.columns:
        df["sale quantity"] = pd.to_numeric(df["sale quantity"], errors="coerce").fillna(0)
        df["ppm_denominator"] = df["sale quantity"]
        df["ppm_denominator_label"] = "Sale Qty"
    else:
        df["ppm_denominator"] = df["production quantity"]
        df["ppm_denominator_label"] = "Production Qty (Sale Qty unavailable)"

    df["total_cost"] = df["rejection quantity"] * df["RSD"]
    df["safe_ppm"] = 0.0
    valid_denominator = df["ppm_denominator"] > 0
    df.loc[valid_denominator, "safe_ppm"] = (
        df.loc[valid_denominator, "rejection quantity"] * 1_000_000
        / df.loc[valid_denominator, "ppm_denominator"]
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
        # Include the complete end date even if timestamps are present.
        mask &= df["Date"] < pd.Timestamp(end) + pd.Timedelta(days=1)
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
    today = pd.Timestamp.today().normalize()
    latest_in_data = df["month_start"].max()
    earliest = df["month_start"].min()

    if pd.notna(latest_in_data) and latest_in_data > today:
        recent_months = df.loc[df["month_start"] <= today, "month_start"]
        latest = recent_months.max() if not recent_months.empty else latest_in_data
    else:
        latest = latest_in_data

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
    x = df[
        (df[group_column].astype(str).str.len() > 0)
        & (df[category_column].astype(str).str.len() > 0)
    ]
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
            ppm_denominator=("ppm_denominator", "sum"),
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
            ppm_denominator=("ppm_denominator", "sum"),
        )
        .sort_values("month_start")
    )


def aggregate_ppm(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    """Correct PPM aggregation: sum(rejections) / sum(denominator) * 1e6."""
    if df.empty:
        return pd.DataFrame(columns=group_cols + ["rejection_quantity", "ppm_denominator", "ppm"])

    if not group_cols:
        out = pd.DataFrame({
            "rejection_quantity": [df["rejection quantity"].sum()],
            "ppm_denominator": [df["ppm_denominator"].sum()],
        })
    else:
        out = (
            df.groupby(group_cols, as_index=False)
            .agg(
                rejection_quantity=("rejection quantity", "sum"),
                ppm_denominator=("ppm_denominator", "sum"),
            )
        )

    out["ppm"] = 0.0
    ok = out["ppm_denominator"] > 0
    out.loc[ok, "ppm"] = (
        out.loc[ok, "rejection_quantity"] * 1_000_000
        / out.loc[ok, "ppm_denominator"]
    )
    return out.replace([math.inf, -math.inf], 0).fillna(0)


def ppm_top_parts(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    out = aggregate_ppm(df, ["part_no_clean"])
    out = out[out["part_no_clean"].astype(str).str.len() > 0]
    return out.sort_values("ppm", ascending=False).head(n)


def monthly_ppm_top_part_lines(df: pd.DataFrame, max_parts: int = 10) -> pd.DataFrame:
    """Select highest-PPM part(s) by month, then track them across every month."""
    base = aggregate_ppm(df, ["month_start", "part_no_clean"])
    base = base[base["part_no_clean"].astype(str).str.len() > 0]
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
    tracked = aggregate_ppm(
        df[df["part_no_clean"].isin(winners)], ["month_start", "part_no_clean"]
    )
    return grid.merge(
        tracked[["month_start", "part_no_clean", "ppm"]],
        how="left", on=["month_start", "part_no_clean"]
    ).fillna({"ppm": 0})


def ppm_monthly_by_group(df: pd.DataFrame, group_col: str) -> pd.DataFrame:
    return aggregate_ppm(df, ["month_start", group_col])


def ppm_distribution(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["ppm"])
    return df[["safe_ppm"]].rename(columns={"safe_ppm": "ppm"}).copy()


def rolling_ppm(df: pd.DataFrame, window: int = 3) -> pd.DataFrame:
    monthly = monthly_totals(df)
    if monthly.empty:
        monthly["ppm"] = []
        monthly["rolling_ppm"] = []
        return monthly
    monthly["ppm"] = 0.0
    ok = monthly["ppm_denominator"] > 0
    monthly.loc[ok, "ppm"] = (
        monthly.loc[ok, "rejection_quantity"] * 1_000_000
        / monthly.loc[ok, "ppm_denominator"]
    )
    monthly["rolling_ppm"] = monthly["ppm"].rolling(window, min_periods=1).mean()
    return monthly
