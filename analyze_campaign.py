"""
analyze_campaign.py

Small CLI tool to analyze weekly marketing campaign performance by channel.

Usage example:
    python analyze_campaign.py -i campaign_data_week1.csv -o weekly_metrics.csv

Depends on: pandas
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
import pandas as pd


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    # find a date column
    date_cols = [c for c in df.columns if "date" in c.lower() or "day" in c.lower()]
    if date_cols:
        df["date"] = pd.to_datetime(df[date_cols[0]])
    else:
        try:
            df["date"] = pd.to_datetime(df.iloc[:, 0])
        except Exception as exc:
            raise ValueError("No parsable date column found in input CSV") from exc

    # ensure numeric columns exist
    for col in ["impressions", "clicks", "spend", "conversions", "revenue"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if "channel" not in df.columns:
        raise ValueError("Input CSV must include a 'channel' column identifying the marketing channel")

    return df


def preprocess(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["week"] = df["date"].dt.to_period("W").apply(lambda p: p.start_time)
    return df


def compute_weekly_metrics(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    agg = (
        df.groupby(["channel", "week"]).agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            spend=("spend", "sum"),
            conversions=("conversions", "sum"),
            revenue=("revenue", "sum"),
        )
        .reset_index()
    )

    # derived metrics (safe division)
    agg["ctr"] = agg.apply(lambda r: (r.clicks / r.impressions) if r.impressions > 0 else 0, axis=1)
    agg["cpc"] = agg.apply(lambda r: (r.spend / r.clicks) if r.clicks > 0 else 0, axis=1)
    agg["cpa"] = agg.apply(lambda r: (r.spend / r.conversions) if r.conversions > 0 else 0, axis=1)
    agg["roas"] = agg.apply(lambda r: (r.revenue / r.spend) if r.spend > 0 else None, axis=1)

    # week-over-week percent changes per channel
    agg = agg.sort_values(["channel", "week"]).reset_index(drop=True)
    metrics_for_mom = ["impressions", "clicks", "spend", "conversions", "revenue", "ctr", "cpc", "cpa", "roas"]
    for m in metrics_for_mom:
        agg[f"{m}_mom"] = agg.groupby("channel")[m].pct_change().fillna(0)

    return agg


def summarize_top_channels(agg: pd.DataFrame, metric: str = "conversions", top_n: int = 5) -> pd.DataFrame:
    latest_per_channel = agg.sort_values("week").groupby("channel").tail(1)
    return latest_per_channel.sort_values(metric, ascending=False).head(top_n)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyze weekly marketing campaign performance by channel")
    parser.add_argument("--input", "-i", required=True, help="Input CSV file path")
    parser.add_argument("--output", "-o", default="weekly_metrics.csv", help="Output CSV file path")
    parser.add_argument("--top", type=int, default=5, help="Show top N channels")
    parser.add_argument("--metric", default="conversions", help="Metric to rank channels (e.g., conversions, roas)")
    args = parser.parse_args(argv)

    path = Path(args.input)
    if not path.exists():
        print(f"Input file not found: {path}", file=sys.stderr)
        return 2

    try:
        df = load_data(path)
    except Exception as exc:
        print(f"Failed to load data: {exc}", file=sys.stderr)
        return 3

    df = preprocess(df)
    agg = compute_weekly_metrics(df)
    agg.to_csv(args.output, index=False)

    top = summarize_top_channels(agg, metric=args.metric, top_n=args.top)

    print(f"Saved weekly metrics to {args.output}")
    print("Top channels (latest week):")
    display_cols = ["channel", "week", args.metric, "roas"]
    available = [c for c in display_cols if c in top.columns]
    print(top[available].to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
