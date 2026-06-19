# Analyze Digimktg Performance

A FastAPI backend service that validates and analyzes marketing campaign CSV data through HTTP endpoints.

## Overview

This project provides REST API endpoints for data validation, cleaning, and marketing metrics analysis. Choose between:
- **Query parameter endpoints**: Pass file path as URL parameter (for local file access)
- **POST body endpoints**: Send file path in JSON request body
- **Upload endpoints**: Send CSV file directly in multipart form upload

## Prerequisites

- Python 3.8+
- Git (optional)

## Install

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

## Running the API Server

Start the FastAPI server locally:

```bash
uvicorn fastapi_main:app --reload
```

The API will be available at `http://localhost:8000`.

Access the interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Data Cleaning / Validation

**GET /cleaned_data_local_test**
- Test endpoint with hardcoded file path
- Returns: JSON preview of cleaned data (first few rows)

**GET /cleaned_data_from_file**
- Query parameter: `file_path` (string)
- Example: `GET /cleaned_data_from_file?file_path=campaign_data.csv`
- Returns: JSON preview of cleaned data
- Validates: File exists, is a .csv file

**POST /cleaned_data_from_upload**
- Accepts: multipart form file upload
- Returns: JSON preview of cleaned data
- Validates: File exists, is a .csv file

### Efficiency Analysis (ROAS, CPA, Net Profit)

**GET /efficiency_analysis_from_file**
- Query parameter: `file_path` (string)
- Example: `GET /efficiency_analysis_from_file?file_path=cleaned_campaign.csv`
- Returns: Efficiency metrics by channel (ROAS, CPA, net profit)

**POST /efficiency_analysis_from_file**
- Request body: `{"filePath": "path/to/file.csv"}`
- Returns: Efficiency metrics by channel

**POST /efficiency_analysis_from_upload_file**
- Accepts: multipart form file upload
- Returns: Efficiency metrics by channel

### Funnel Analysis (CTR, CVR)

**POST /funnel_analysis_from_upload_file**
- Accepts: multipart form file upload
- Returns: Funnel metrics by channel (CTR, CVR, benchmark comparisons)

### Campaign Analysis

**POST /analyze_campaign**
- Accepts: multipart form file upload
- Returns: Weekly metrics aggregation with derived KPIs

## Input Data Requirements

All CSV inputs must include:
- **Required columns**: `date`, `campaign_name`, `channel`, `segment`, `impressions`, `clicks`, `conversions`, `spend`, `revenue`, `orders`
- **Data types**: Numeric columns (impressions, clicks, spend, etc.) must be parseable as numbers
- **Dates**: Must be in a parseable datetime format

See `input_campaign_data.py` for detailed validation logic.

## Command-Line Tools (Legacy)

The project also supports direct CLI usage:

```bash
# Validate and clean CSV
python input_campaign_data.py -i raw_campaigns.csv -o cleaned_campaign.csv

# Aggregate weekly metrics
python analyze_campaign.py -i cleaned_campaign.csv -o weekly_metrics.csv

# Efficiency analysis
python efficiency_analysis.py -i cleaned_campaign.csv

# Funnel analysis
python funnel_analysis.py -i cleaned_campaign.csv
```

## Technologies

- **FastAPI**: Modern Python web framework for building APIs
- **Pandas**: Data manipulation and analysis
- **Pydantic**: Data validation using Python type hints
- **Uvicorn**: ASGI web server