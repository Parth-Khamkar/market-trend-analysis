# Market Trend Analysis & Forecasting

Comprehensive market analysis using SQL queries and Python statistical modeling to forecast trends and identify investment opportunities.

## Project Overview

This project analyzes historical market data across 8 sectors to identify trends and build predictive models for future price movements. SQL is used for data aggregation and trend/anomaly detection; Python (scikit-learn) handles the forecasting layer, producing 90-day forecasts with 95% confidence intervals.

## Tech Stack

- **Python**: pandas, NumPy, scikit-learn, Matplotlib
- **SQL**: SQLite/PostgreSQL-compatible (window functions, CTEs)

## Project Structure

```
market-trend-analysis/
├── data/
│   └── market_data.csv          # Synthetic 3-year daily dataset, 8 sectors
├── sql/
│   └── market_analysis.sql      # Trend detection, volatility, anomaly queries
├── scripts/
│   ├── generate_data.py         # Synthetic data generator
│   └── forecast.py              # Forecasting model + accuracy scoring
├── output/
│   ├── forecast_summary.csv     # Per-sector accuracy + growth forecast
│   └── forecast_chart_*.png     # Forecast chart with confidence interval
└── README.md
```

## How It Works

1. **Data**: `market_data.csv` contains daily close price, volume, and market cap for 8 sectors (Technology, Healthcare, Energy, Financials, Consumer Goods, Industrials, Real Estate, Utilities) over 3 years, with embedded trend, seasonality, and occasional shocks.
2. **SQL layer** (`market_analysis.sql`): aggregates to monthly sector summaries, computes month-over-month % change to flag sustained trends, calculates 30-day rolling volatility, and flags anomalies via z-score.
3. **Forecasting** (`forecast.py`): fits a linear trend + seasonal regression per sector, validates on a held-out 60-day window, then forecasts 90 days forward with 95% confidence bands. Sectors are ranked by forecast growth to surface investment recommendations.

## Key Outcomes

| Metric | Result |
|---|---|
| Sectors analyzed | 8 |
| Avg. prediction accuracy (test window) | ~98% on synthetic data* |
| Avg. forecast error (MAPE) | ~1-2% on synthetic data* |
| Investment recommendations generated | Top 3 by forecast growth |

*Synthetic data is generated with a known, smooth trend + seasonality signal, so accuracy is higher than would be expected on real market data — real-world results depend heavily on data quality and market volatility. Swap in real price history (e.g. via a market data API) in `data/market_data.csv` to get representative numbers.

## Challenges Addressed

- Handling large time-series datasets efficiently in SQL (window functions vs. self-joins)
- Distinguishing genuine trend from noise/seasonality
- Balancing model simplicity (interpretability) against forecast accuracy

## Running It

```bash
pip install pandas numpy scikit-learn matplotlib

python scripts/generate_data.py     # regenerate the dataset (optional, one is included)
python scripts/forecast.py          # run the forecasting pipeline
```

Load `data/market_data.csv` into SQLite/Postgres and run `sql/market_analysis.sql` for the trend/anomaly queries.
