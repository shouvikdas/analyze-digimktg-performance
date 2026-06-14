"""input_campaign_data.py

Simple CSV ingestion and validation for marketing campaign data.

Expected columns:
- date, campaign_name, channel, segment,
- impressions, clicks, conversions, spend, revenue, orders

Usage:
    python input_campaign_data.py -i campaign_data.csv -o cleaned.csv
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
import pandas as pd


REQUIRED_COLUMNS = [
    "date",
    "campaign_name",
    "channel",
    "segment",
    "impressions",
    "clicks",
    "conversions",
    "spend",
    "revenue",
    "orders",
]


def validate_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def load_and_clean(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    validate_columns(df)

    # parse dates
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().any():
        raise ValueError("Some 'date' values could not be parsed")

    # numeric conversions
    num_cols = ["impressions", "clicks", "conversions", "spend", "revenue", "orders"]
    
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    # Impressions may be empty for Email channel — fill with 0 for Email
    if "channel" in df.columns:
        email_mask = df["channel"].str.lower() == "email"
        df.loc[email_mask, "impressions"] = df.loc[email_mask, "impressions"].fillna(0)

    # For other channels, fill missing numeric values with 0
    df[num_cols] = df[num_cols].fillna(0)

    # Verify there are no negative values in numeric columns
    neg_counts = {c: int((df[c] < 0).sum()) for c in num_cols}
    neg_cols = [c for c, cnt in neg_counts.items() if cnt > 0]
    if neg_cols:
        details = ", ".join(f"{c}: {neg_counts[c]} negative" for c in neg_cols)
        raise ValueError(f"Negative values found in numeric columns: {details}")

    # ensure integer columns where appropriate
    df["orders"] = df["orders"].astype(int)

    return df


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Ingest and validate campaign CSV data")
    parser.add_argument("--input", "-i", required=True, help="Input CSV path")
    parser.add_argument("--output", "-o", default="cleaned_campaign.csv", help="Output cleaned CSV path")
    args = parser.parse_args(argv)

    inp = Path(args.input)
    if not inp.exists():
        print(f"Input file not found: {inp}", file=sys.stderr)
        return 2

    try:
        df = load_and_clean(inp)
    except Exception as exc:
        print(f"Failed to load/validate data: {exc}", file=sys.stderr)
        return 3

    out = Path(args.output)
    df.to_csv(out, index=False)
    print(f"Wrote cleaned data to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
