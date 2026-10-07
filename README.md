# TFEX Terminal V4 — Live Analytics Shell

Streamlit shell for a TFEX trading journal. Demo trading records and fake performance numbers are intentionally removed.

## Included
- Dashboard / Orders / Positions / Journal / Analytics navigation
- Live-account shell; read-only until TFEX API is connected
- Deep Analytics structure: Day / Week / Month / Year / All time
- Win rate by period, time of day, asset, side, and day of week
- Holding-time analytics: average, median, shortest, longest, intraday/overnight
- P/L, Profit Factor, Expectancy, Average R, Max Drawdown placeholders
- Risk/Reward analytics placeholders
- Monthly trading calendar modeled after the requested mobile layout
- Empty Trade Log table ready for real TFEX execution data
- Filters for asset, side, result, setup/note search

## Run
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Important
This version does NOT connect to TFEX and does NOT submit orders. It is a UI/data-contract shell waiting for real TFEX API authentication and read-only account/execution sync.
