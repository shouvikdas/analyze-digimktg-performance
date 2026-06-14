"""funnel_analysis.py

Compute CTR and CVR per channel from a cleaned campaign CSV and compare
to benchmarks. Reports percentage-point differences and short interpretations.

Usage:
    python funnel_analysis.py -i cleaned_campaign.csv
    python funnel_analysis.py -i cleaned_campaign.csv -b benchmarks.csv -o funnel_report.csv

Benchmarks CSV (optional) should have columns: channel, ctr, cvr (percent values, e.g. 2.5)
If not provided, built-in historical benchmarks are used.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
import pandas as pd


DEFAULT_BENCHMARKS = {
    "facebook_ads": {"ctr": 2.5, "cvr": 3.8},
    "google_ads": {"ctr": 5.0, "cvr": 4.5},
    "tiktok_ads": {"ctr": 2.0, "cvr": 0.9},
    "email": {"ctr": 15.0, "cvr": 2.1},
}


def load_cleaned(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    # ensure required columns exist
    required = {"channel", "impressions", "clicks", "conversions"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns in cleaned CSV: {missing}")
    return df


def load_benchmarks(path: Path) -> dict[str, dict[str, float]]:
    df = pd.read_csv(path)
    if not {"channel", "ctr", "cvr"}.issubset(df.columns):
        raise ValueError("Benchmark CSV must contain columns: channel, ctr, cvr")
    bench = {}
    for _, row in df.iterrows():
        key = str(row["channel"]).strip().lower().replace(" ", "_")
        bench[key] = {"ctr": float(row["ctr"]), "cvr": float(row["cvr"]) }
    return bench


def compute_funnel(df: pd.DataFrame, benchmarks: dict[str, dict[str, float]] | None = None) -> pd.DataFrame:
    df = df.copy()
    # normalize channel key for grouping
    df["_channel_key"] = df["channel"].astype(str).str.strip().str.lower().str.replace(" ", "_")

    grouped = (
        df.groupby("_channel_key").agg(
            impressions=("impressions", "sum"),
            clicks=("clicks", "sum"),
            conversions=("conversions", "sum"),
        )
        .reset_index()
    )

    # compute rates as percentages; guard against division by zero
    grouped["ctr"] = grouped.apply(lambda r: (r.clicks / r.impressions * 100) if r.impressions > 0 else 0.0, axis=1)
    grouped["cvr"] = grouped.apply(lambda r: (r.conversions / r.clicks * 100) if r.clicks > 0 else 0.0, axis=1)

    bench = DEFAULT_BENCHMARKS.copy()
    if benchmarks:
        # merge provided benchmarks (override defaults)
        for k, v in benchmarks.items():
            bench[k] = v

    # attach benchmarks and diffs
    def get_b(k: str, metric: str) -> float | None:
        return bench.get(k, {}).get(metric)

    grouped["benchmark_ctr"] = grouped["_channel_key"].apply(lambda k: get_b(k, "ctr"))
    grouped["benchmark_cvr"] = grouped["_channel_key"].apply(lambda k: get_b(k, "cvr"))

    grouped["diff_ctr_pp"] = grouped.apply(lambda r: (r.ctr - r.benchmark_ctr) if pd.notna(r.benchmark_ctr) else None, axis=1)
    grouped["diff_cvr_pp"] = grouped.apply(lambda r: (r.cvr - r.benchmark_cvr) if pd.notna(r.benchmark_cvr) else None, axis=1)

    def interpret(diff: float | None, metric_name: str) -> str:
        if diff is None:
            return f"No benchmark for {metric_name}"
        if abs(diff) < 0.1:
            return f"Matches benchmark (within {abs(diff):.2f} pp)"
        if diff > 0:
            return f"Above benchmark by {diff:.2f} percentage points"
        return f"Below benchmark by {abs(diff):.2f} percentage points"

    grouped["interp_ctr"] = grouped["diff_ctr_pp"].apply(lambda d: interpret(d, "CTR"))
    grouped["interp_cvr"] = grouped["diff_cvr_pp"].apply(lambda d: interpret(d, "CVR"))

    # present original channel label when available (take first occurrence)
    first_labels = df.groupby("_channel_key").agg(channel_label=("channel", "first")).reset_index()
    grouped = grouped.merge(first_labels, on="_channel_key", how="left")

    # reorder columns for readability
    cols = [
        "channel_label",
        "_channel_key",
        "impressions",
        "clicks",
        "conversions",
        "ctr",
        "benchmark_ctr",
        "diff_ctr_pp",
        "interp_ctr",
        "cvr",
        "benchmark_cvr",
        "diff_cvr_pp",
        "interp_cvr",
    ]
    return grouped[cols]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compute CTR/CVR per channel and compare to benchmarks")
    parser.add_argument("--input", "-i", required=True, help="Cleaned campaign CSV path")
    parser.add_argument("--benchmarks", "-b", help="Optional benchmarks CSV path (columns: channel, ctr, cvr)")
    parser.add_argument("--output", "-o", help="Optional output CSV path for the report")
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

    benchmarks = None
    if args.benchmarks:
        bpath = Path(args.benchmarks)
        if not bpath.exists():
            print(f"Benchmarks file not found: {bpath}", file=sys.stderr)
            return 4
        try:
            benchmarks = load_benchmarks(bpath)
        except Exception as exc:
            print(f"Failed to load benchmarks: {exc}", file=sys.stderr)
            return 5

    report = compute_funnel(df, benchmarks=benchmarks)

    # prepare and print a concise report table with status indicators
    def status_symbol(diff: float | None) -> str:
        if diff is None:
            return "?"
        if abs(diff) < 0.1:
            return "—"  # matches
        return "▲" if diff > 0 else "▼"

    table = report.copy()
    # format numeric columns as strings with two decimals
    table["CTR Actual"] = table["ctr"].map(lambda v: f"{v:.2f}%")
    table["CTR Benchmark"] = table["benchmark_ctr"].map(lambda v: f"{v:.2f}%" if pd.notna(v) else "-")
    table["CTR Diff"] = table["diff_ctr_pp"].map(lambda v: f"{v:+.2f} pp" if pd.notna(v) else "-")
    table["CTR Status"] = table["diff_ctr_pp"].map(status_symbol)

    table["CVR Actual"] = table["cvr"].map(lambda v: f"{v:.2f}%")
    table["CVR Benchmark"] = table["benchmark_cvr"].map(lambda v: f"{v:.2f}%" if pd.notna(v) else "-")
    table["CVR Diff"] = table["diff_cvr_pp"].map(lambda v: f"{v:+.2f} pp" if pd.notna(v) else "-")
    table["CVR Status"] = table["diff_cvr_pp"].map(status_symbol)

    out_cols = [
        "channel_label",
        "CTR Actual",
        "CTR Benchmark",
        "CTR Diff",
        "CTR Status",
        "CVR Actual",
        "CVR Benchmark",
        "CVR Diff",
        "CVR Status",
    ]

    display_df = table[out_cols].rename(columns={"channel_label": "Channel"})
    print(display_df.to_string(index=False))

    if args.output:
        outp = Path(args.output)
        report.to_csv(outp, index=False)
        print(f"Wrote report to {outp}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
