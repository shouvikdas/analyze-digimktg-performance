"""efficiency_analysis.py

Compute ROAS, CPA and Net Profit per channel from a cleaned campaign CSV and
compare to provided targets. Prints a concise table with status indicators.

Usage:
    python efficiency_analysis.py -i cleaned_campaign.csv
    python efficiency_analysis.py -i cleaned_campaign.csv --shipping 10 --product-cost-pct 0.4 --target-roas 3.5 --max-cpa 60
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
import math
import pandas as pd


DEFAULT_TARGET_ROAS = 4.0
DEFAULT_MAX_CPA = 50.0
DEFAULT_SHIPPING = 8.0
DEFAULT_PRODUCT_COST_PCT = 0.35


def load_cleaned(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"channel", "spend", "revenue", "conversions", "orders"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in cleaned CSV: {missing}")
    return df


def compute_efficiency(df: pd.DataFrame, shipping_cost: float=0, product_cost_pct: float=0) -> pd.DataFrame:
    d = df.copy()
    d["_channel_key"] = d["channel"].astype(str).str.strip().str.lower().str.replace(" ", "_")

    agg = (
        d.groupby("_channel_key").agg(
            spend=("spend", "sum"),
            revenue=("revenue", "sum"),
            conversions=("conversions", "sum"),
            orders=("orders", "sum"),
        )
        .reset_index()
    )

    def safe_roas(row):
        if row.spend == 0:
            return math.inf if row.revenue > 0 else 0.0
        return row.revenue / row.spend

    def safe_cpa(row):
        return (row.spend / row.conversions) if row.conversions > 0 else None

    agg["roas"] = agg.apply(safe_roas, axis=1)
    agg["cpa"] = agg.apply(safe_cpa, axis=1)

    # total costs = spend + orders * shipping + revenue * product_cost_pct
    agg["total_costs"] = agg.apply(lambda r: r.spend + r.orders * shipping_cost + r.revenue * product_cost_pct, axis=1)
    agg["net_profit"] = agg["revenue"] - agg["total_costs"]

    # attach human channel label
    labels = d.groupby("_channel_key").agg(channel_label=("channel", "first")).reset_index()
    agg = agg.merge(labels, on="_channel_key", how="left")

    cols = [
        "channel_label",
        "_channel_key",
        "spend",
        "revenue",
        "conversions",
        "orders",
        "roas",
        "cpa",
        "total_costs",
        "net_profit",
    ]
    return agg[cols]


def format_money(v: float | None) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "-"
    return f"${v:,.2f}"


def status_symbol(condition: bool | None) -> str:
    if condition is None:
        return "?"
    return "▲" if condition else "▼"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute ROAS/CPA/net profit per channel and compare to targets")
    parser.add_argument("--input", "-i", required=True, help="Cleaned campaign CSV path")
    parser.add_argument("--shipping", type=float, default=DEFAULT_SHIPPING, help="Shipping cost per order")
    parser.add_argument("--product-cost-pct", type=float, default=DEFAULT_PRODUCT_COST_PCT, help="Product cost percentage of revenue (0-1)")
    parser.add_argument("--target-roas", type=float, default=DEFAULT_TARGET_ROAS, help="Target minimum ROAS (x)")
    parser.add_argument("--max-cpa", type=float, default=DEFAULT_MAX_CPA, help="Maximum acceptable CPA ($)")
    parser.add_argument("--output", "-o", help="Optional output CSV path")
    args = parser.parse_args(argv)

    inp = Path(args.input)
    if not inp.exists():
        print(f"Input file not found: {inp}", file=sys.stderr)
        return 2

    try:
        df = load_cleaned(inp)
    except Exception as exc:
        print(f"Failed to load cleaned data: {exc}", file=sys.stderr)
        return 3

    report = compute_efficiency(df, shipping_cost=args.shipping, product_cost_pct=args.product_cost_pct)

    # compare to targets and build display table
    def pass_roas(x):
        if x is None:
            return None
        if math.isinf(x):
            return True
        return x >= args.target_roas

    def pass_cpa(x):
        if x is None:
            return None
        return x <= args.max_cpa

    table = report.copy()
    # Build user-friendly columns and textual status indicators
    table["ROAS"] = table["roas"].map(lambda v: f"{v:.2f}x" if (v is not None and not math.isinf(v)) else ("∞" if v is not None and math.isinf(v) else "-"))

    def roas_status_text(v):
        if v is None:
            return "[?] N/A"
        if math.isinf(v) or v >= args.target_roas:
            return "[OK] Above"
        return "[X] Below"

    table["ROAS Status"] = table["roas"].map(roas_status_text)

    table["CPA"] = table["cpa"].map(lambda v: format_money(v) if v is not None else "-")

    def cpa_status_text(v):
        if v is None:
            return "[?] N/A"
        return "[OK] Below" if v <= args.max_cpa else "[X] Above"

    table["CPA Status"] = table["cpa"].map(cpa_status_text)

    table["Net Profit"] = table["net_profit"].map(format_money)

    def netprofit_status_text(v):
        try:
            num = float(v)
        except Exception:
            return "[?] N/A"
        return "[OK] Positive" if num > 0 else "[X] Negative"

    table["Net Profit Status"] = table["net_profit"].map(netprofit_status_text)

    out_cols = [
        "channel_label",
        "ROAS",
        "ROAS Status",
        "CPA",
        "CPA Status",
        "Net Profit",
        "Net Profit Status",
    ]

    display = table[out_cols].rename(columns={"channel_label": "Channel"})
    print(display.to_string(index=False))

    if args.output:
        outp = Path(args.output)
        report.to_csv(outp, index=False)
        print(f"Wrote report to {outp}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
