"""
forecast.py
Market Trend Analysis & Forecasting

Pipeline:
1. Load market_data.csv (output of SQL aggregation / generate_data.py)
2. Fit a per-sector linear trend + seasonal regression model
3. Forecast the next 90 days with 95% confidence intervals
4. Score model accuracy on a held-out test window
5. Rank sectors by forecasted growth -> investment recommendations
6. Save charts + a results summary CSV
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_percentage_error, r2_score
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DATA_PATH = "/home/claude/market-trend-analysis/data/market_data.csv"
OUTPUT_DIR = "/home/claude/market-trend-analysis/output"
FORECAST_HORIZON_DAYS = 90
TEST_HOLDOUT_DAYS = 60


def build_features(df):
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values("date").reset_index(drop=True)
    df["t"] = (df["date"] - df["date"].min()).dt.days
    df["doy_sin"] = np.sin(2 * np.pi * df["date"].dt.dayofyear / 365.25)
    df["doy_cos"] = np.cos(2 * np.pi * df["date"].dt.dayofyear / 365.25)
    return df


def fit_and_forecast(sector_df, horizon_days):
    sector_df = build_features(sector_df)
    train = sector_df.iloc[:-TEST_HOLDOUT_DAYS]
    test = sector_df.iloc[-TEST_HOLDOUT_DAYS:]

    X_cols = ["t", "doy_sin", "doy_cos"]
    model = LinearRegression()
    model.fit(train[X_cols], train["close_price"])

    # Accuracy on held-out window
    test_pred = model.predict(test[X_cols])
    mape = mean_absolute_percentage_error(test["close_price"], test_pred)
    r2 = r2_score(test["close_price"], test_pred)
    accuracy_pct = max(0, (1 - mape) * 100)

    # Residual std for confidence intervals
    train_pred = model.predict(train[X_cols])
    resid_std = np.std(train["close_price"] - train_pred)

    # Refit on full history, then forecast forward
    model.fit(sector_df[X_cols], sector_df["close_price"])
    last_date = sector_df["date"].max()
    last_t = sector_df["t"].max()
    future_dates = pd.date_range(last_date + pd.Timedelta(days=1), periods=horizon_days)
    future = pd.DataFrame({
        "date": future_dates,
        "t": np.arange(last_t + 1, last_t + 1 + horizon_days),
    })
    future["doy_sin"] = np.sin(2 * np.pi * future["date"].dt.dayofyear / 365.25)
    future["doy_cos"] = np.cos(2 * np.pi * future["date"].dt.dayofyear / 365.25)
    future["forecast"] = model.predict(future[X_cols])
    future["upper_95"] = future["forecast"] + 1.96 * resid_std
    future["lower_95"] = future["forecast"] - 1.96 * resid_std

    growth_pct = 100 * (future["forecast"].iloc[-1] - sector_df["close_price"].iloc[-1]) / sector_df["close_price"].iloc[-1]

    return {
        "mape": mape,
        "accuracy_pct": accuracy_pct,
        "r2": r2,
        "future": future,
        "history": sector_df,
        "growth_pct": growth_pct,
    }


def main():
    df = pd.read_csv(DATA_PATH)
    sectors = df["sector"].unique()

    results = {}
    for sector in sectors:
        sector_df = df[df["sector"] == sector][["date", "close_price"]]
        results[sector] = fit_and_forecast(sector_df, FORECAST_HORIZON_DAYS)

    # --- Summary table (mirrors the "Key Outcomes" metrics) ---
    summary_rows = []
    for sector, r in results.items():
        summary_rows.append({
            "sector": sector,
            "prediction_accuracy_pct": round(r["accuracy_pct"], 1),
            "forecast_error_mape_pct": round(r["mape"] * 100, 1),
            "r2_score": round(r["r2"], 3),
            "90d_forecast_growth_pct": round(r["growth_pct"], 2),
        })
    summary = pd.DataFrame(summary_rows).sort_values("90d_forecast_growth_pct", ascending=False)
    summary.to_csv(f"{OUTPUT_DIR}/forecast_summary.csv", index=False)

    avg_accuracy = summary["prediction_accuracy_pct"].mean()
    avg_error = summary["forecast_error_mape_pct"].mean()
    top_recommendations = summary.head(3)

    print("=" * 60)
    print("MARKET TREND ANALYSIS & FORECASTING — RESULTS")
    print("=" * 60)
    print(f"Sectors analyzed:            {len(sectors)}")
    print(f"Avg prediction accuracy:     {avg_accuracy:.1f}%")
    print(f"Avg forecast error (MAPE):   {avg_error:.1f}%")
    print("\nTop 3 investment recommendations (by 90-day forecast growth):")
    print(top_recommendations[["sector", "90d_forecast_growth_pct", "prediction_accuracy_pct"]].to_string(index=False))
    print(f"\nFull results: {OUTPUT_DIR}/forecast_summary.csv")

    # --- Chart: forecast with confidence interval for the top sector ---
    top_sector = top_recommendations.iloc[0]["sector"]
    r = results[top_sector]
    hist = r["history"].tail(180)
    fut = r["future"]

    plt.figure(figsize=(10, 5))
    plt.plot(hist["date"], hist["close_price"], label="Actual", color="#2563eb")
    plt.plot(fut["date"], fut["forecast"], label="Forecast", color="#06b6d4", linestyle="--")
    plt.fill_between(fut["date"], fut["lower_95"], fut["upper_95"], color="#06b6d4", alpha=0.2, label="95% CI")
    plt.title(f"{top_sector} — Price Forecast (Next {FORECAST_HORIZON_DAYS} Days)")
    plt.xlabel("Date")
    plt.ylabel("Price")
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/forecast_chart_{top_sector.replace(' ', '_')}.png", dpi=150)
    print(f"Chart saved: {OUTPUT_DIR}/forecast_chart_{top_sector.replace(' ', '_')}.png")


if __name__ == "__main__":
    main()
