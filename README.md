# InsightEdge Complaint Dashboard

A Streamlit dashboard for exploring the consolidated customer complaints dataset that was previously summarized in the newsletter.

## Run locally

1. Create and activate a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Start the app:

```bash
streamlit run app.py
```

## Data source

The dashboard reads the consolidated CSV at `files/combined_output(1).csv`.

## Structure

- `app.py` - Streamlit entry point and page layout
- `src/data_prep.py` - data loading, cleaning, and derived fields
- `src/charts.py` - reusable chart builders
