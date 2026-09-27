"""
generate_data.py
Generates a synthetic daily market dataset (3 years) with trend, seasonality,
and noise, across multiple sectors — used as the raw input for the SQL
analysis and the forecasting model.
"""

import numpy as np
import pandas as pd

np.random.seed(42)

SECTORS = ["Technology", "Healthcare", "Energy", "Financials", "Consumer Goods",
           "Industrials", "Real Estate", "Utilities"]

START_DATE = "2023-01-01"
END_DATE = "2025-12-31"

dates = pd.date_range(START_DATE, END_DATE, freq="D")

rows = []
for sector in SECTORS:
    base_price = np.random.uniform(50, 200)
    trend_slope = np.random.uniform(-0.02, 0.05)  # per-day drift
    seasonal_amp = np.random.uniform(2, 10)
    vol = np.random.uniform(0.5, 2.5)

    price = base_price
    for i, d in enumerate(dates):
        trend = trend_slope * i
        seasonality = seasonal_amp * np.sin(2 * np.pi * i / 365.25)
        shock = np.random.normal(0, vol)
        # occasional anomaly / market event
        if np.random.rand() < 0.002:
            shock += np.random.choice([-1, 1]) * np.random.uniform(15, 30)

        price = max(1, base_price + trend + seasonality + shock)
        volume = int(np.random.lognormal(mean=11, sigma=0.4))

        rows.append({
            "date": d.strftime("%Y-%m-%d"),
            "sector": sector,
            "close_price": round(price, 2),
            "volume": volume,
            "market_cap_bn": round(price * np.random.uniform(0.8, 5.0), 2),
        })

df = pd.DataFrame(rows)
df.to_csv("/home/claude/market-trend-analysis/data/market_data.csv", index=False)
print(f"Generated {len(df):,} rows across {len(SECTORS)} sectors")
print(df.head())
