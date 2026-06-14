# Analyze Digimktg Performance

Small collection of CLI tools to validate and analyze marketing campaign CSV data.

Prerequisites
- Python 3.8+
- Git (optional)

Install
1. Create and activate a virtual environment (recommended):

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

Files / Commands
- `input_campaign_data.py`: Validate and clean a raw campaign CSV and write `cleaned_campaign.csv` (default).

```bash
python input_campaign_data.py -i raw_campaigns.csv -o cleaned_campaign.csv
```

- `analyze_campaign.py`: Aggregate weekly metrics by `channel` and save `weekly_metrics.csv` (default).

```bash
python analyze_campaign.py -i cleaned_campaign.csv -o weekly_metrics.csv
```

- `efficiency_analysis.py`: Compute ROAS/CPA/net profit per channel and compare to targets.

```bash
python efficiency_analysis.py -i cleaned_campaign.csv
```

- `funnel_analysis.py`: Compute CTR/CVR per channel and compare to benchmarks.

```bash
python funnel_analysis.py -i cleaned_campaign.csv
```

Notes
- The tools expect input CSVs to include a `channel` column and common marketing columns like `impressions`, `clicks`, `spend`, `conversions`, `revenue`, and `orders` where applicable. See `input_campaign_data.py` for the exact required columns.
- `requirements.txt` currently lists `pandas` as the only third-party dependency.
