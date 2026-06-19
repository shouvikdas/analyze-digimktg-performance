import io
from pathlib import Path

import pandas as pd
import streamlit as st

import input_campaign_data
import analyze_campaign


st.set_page_config(page_title="Campaign Analyzer", layout="wide")


st.title("Marketing Campaign — Weekly Metrics Generator")

st.markdown("Upload a raw campaign CSV; the app will validate, clean, aggregate weekly metrics, and provide a download.")

uploaded = st.file_uploader("Upload raw campaign CSV", type=["csv"])

if uploaded is None:
    st.info("Upload a CSV to begin.")
else:
    try:
        # Use the project's cleaning function (accepts file-like objects)
        cleaned_df = input_campaign_data.load_and_clean(uploaded)
    except Exception as exc:
        st.error(f"Failed to parse/validate uploaded CSV: {exc}")
    else:
        st.success("Input validated and cleaned.")
        st.subheader("Cleaned data preview")
        st.dataframe(cleaned_df.head(200))

        # Run the analysis pipeline: preprocess -> compute weekly metrics
        try:
            prepped = analyze_campaign.preprocess(cleaned_df)
            weekly = analyze_campaign.compute_weekly_metrics(prepped)
        except Exception as exc:
            st.error(f"Failed to compute weekly metrics: {exc}")
        else:
            st.subheader("Weekly metrics (aggregated)")
            st.dataframe(weekly.head(200))

            csv_bytes = weekly.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download weekly_metrics.csv",
                data=csv_bytes,
                file_name="weekly_metrics.csv",
                mime="text/csv",
            )

            # also show top channels option
            with st.expander("Top channels"):
                metric = st.selectbox("Rank by metric", options=["conversions", "revenue", "roas"], index=0)
                top_n = st.number_input("Top N", value=5, min_value=1, max_value=50)
                try:
                    top = analyze_campaign.summarize_top_channels(weekly, metric=metric, top_n=int(top_n))
                    st.table(top)
                except Exception as exc:
                    st.write("Could not compute top channels:", exc)
