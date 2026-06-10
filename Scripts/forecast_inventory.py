import logging
import math
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error


# Configuration
DB_PATH = Path(__file__).resolve().parent / "ecommerce_data.db"
FORECAST_WEEKS = 12
TEST_WEEKS = 12
TOP_N_PRODUCTS = None  # Set to None to process all products
MIN_HISTORY_WEEKS = 24
Z_SCORE_95 = 1.645
OUTPUT_TABLE = "predicted_inventory_forecast"


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


WEEKLY_AGG_SQL = """
WITH clean_sales AS (
  SELECT
    order_id,
    date(date) AS date,
    COALESCE(CAST(customer_id AS TEXT), 'Unknown') AS customer_id,
    product_id,
    quantity,
    promotion_applied
  FROM sales_transactions
  WHERE quantity IS NOT NULL
),
weekly AS (
  SELECT
    s.product_id,
    date(s.date, 'weekday 1', '-7 days') AS week_start,
    SUM(s.quantity) AS total_quantity_sold,
    SUM(s.quantity * p.unit_price) AS total_revenue,
    SUM(s.quantity * (p.unit_price - p.unit_cost)) AS total_profit,
    CASE
      WHEN SUM(CASE WHEN s.promotion_applied = 1 THEN s.quantity ELSE 0 END) = 0 THEN NULL
      ELSE SUM(CASE WHEN s.promotion_applied = 1 THEN s.quantity * p.unit_price ELSE 0 END) * 1.0
           / SUM(CASE WHEN s.promotion_applied = 1 THEN s.quantity ELSE 0 END)
    END AS avg_price_discount
  FROM clean_sales s
  JOIN products p USING (product_id)
  GROUP BY s.product_id, week_start
)
SELECT
  product_id,
  week_start,
  total_quantity_sold,
  total_revenue,
  total_profit,
  avg_price_discount,
  AVG(total_quantity_sold) OVER (
    PARTITION BY product_id
    ORDER BY week_start
    ROWS BETWEEN 3 PRECEDING AND CURRENT ROW
  ) AS rolling_4wk_avg
FROM weekly
ORDER BY product_id, week_start;
"""


def load_inventory_status(connection: sqlite3.Connection) -> pd.DataFrame:
    return pd.read_sql_query(
        "SELECT product_id, current_stock_level, lead_time_days FROM inventory_status",
        connection,
    )


def normalize_weekly_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "week_start_date" in df.columns:
        df = df.rename(columns={"week_start_date": "ds"})
    elif "week_start" in df.columns:
        df = df.rename(columns={"week_start": "ds"})

    if "total_quantity_sold" in df.columns:
        df = df.rename(columns={"total_quantity_sold": "y"})

    if "ds" not in df.columns or "y" not in df.columns:
        raise ValueError("weekly sales DataFrame must contain 'ds' and 'y' columns")

    df["ds"] = pd.to_datetime(df["ds"])
    return df


def select_products(df: pd.DataFrame, top_n: int | None = TOP_N_PRODUCTS) -> list[int]:
    product_ranking = df.groupby("product_id")["y"].sum().sort_values(ascending=False)
    if top_n is None:
        return product_ranking.index.tolist()
    return product_ranking.head(top_n).index.tolist()


def create_prophet_model() -> Prophet:
    model = Prophet(
        weekly_seasonality=True,
        yearly_seasonality=True,
        daily_seasonality=False,
        seasonality_mode="additive",
    )
    model.add_country_holidays(country_name="US")
    return model


def compute_metrics(actual: pd.Series, predicted: pd.Series) -> tuple[float, float]:
    mae = mean_absolute_error(actual, predicted)
    nonzero_mask = actual != 0
    if nonzero_mask.any():
        mape = np.mean(np.abs((actual[nonzero_mask] - predicted[nonzero_mask]) / actual[nonzero_mask])) * 100
    else:
        mape = float("nan")
    return mae, mape


def compute_inventory_metrics(quantity_series: pd.Series, lead_time_days: int) -> dict[str, float]:
    avg_daily_demand = quantity_series.mean() / 7.0
    sigma_d = quantity_series.std(ddof=0) / math.sqrt(7.0)
    safety_stock = Z_SCORE_95 * math.sqrt(lead_time_days) * sigma_d
    reorder_point = avg_daily_demand * lead_time_days + safety_stock
    return {
        "avg_daily_demand": avg_daily_demand,
        "sigma_d": sigma_d,
        "safety_stock": safety_stock,
        "reorder_point": reorder_point,
    }


def build_forecast_for_product(
    product_df: pd.DataFrame,
    inventory_row: pd.Series,
    forecast_weeks: int = FORECAST_WEEKS,
    test_weeks: int = TEST_WEEKS,
) -> pd.DataFrame:
    product_df = product_df.sort_values("ds").reset_index(drop=True)
    if len(product_df) < test_weeks + 4:
        raise ValueError(
            f"Product {product_df['product_id'].iloc[0]} has only {len(product_df)} weeks; need at least {test_weeks + 4} weeks"
        )

    train_df = product_df.iloc[:-test_weeks].copy()
    test_df = product_df.iloc[-test_weeks:].copy()

    model = create_prophet_model()
    model.fit(train_df[["ds", "y"]])

    test_future = test_df[["ds"]].copy()
    test_pred = model.predict(test_future)
    test_merged = test_df.merge(
        test_pred[["ds", "yhat"]], on="ds", how="left"
    )
    mae, mape = compute_metrics(test_merged["y"], test_merged["yhat"])

    full_future = model.make_future_dataframe(periods=forecast_weeks, freq="W-MON")
    forecast = model.predict(full_future)
    forecast = forecast[["ds", "yhat"]].tail(forecast_weeks).copy()
    forecast["Forecasted_Demand"] = forecast["yhat"].clip(lower=0).round(2)

    inventory_metrics = compute_inventory_metrics(train_df["y"], inventory_row["lead_time_days"])

    history_rows = product_df.copy()
    history_rows["Forecasted_Demand"] = np.nan
    history_rows["lead_time_days"] = inventory_row["lead_time_days"]
    history_rows["current_stock_level"] = inventory_row["current_stock_level"]
    history_rows["sigma_d"] = inventory_metrics["sigma_d"]
    history_rows["avg_daily_demand"] = inventory_metrics["avg_daily_demand"]
    history_rows["safety_stock"] = inventory_metrics["safety_stock"]
    history_rows["reorder_point"] = inventory_metrics["reorder_point"]
    history_rows["mae"] = mae
    history_rows["mape"] = mape
    history_rows["period"] = "history"
    history_rows["is_forecast"] = False

    forecast_rows = pd.DataFrame(
        {
            "product_id": inventory_row["product_id"],
            "ds": forecast["ds"],
            "total_quantity_sold": np.nan,
            "total_revenue": np.nan,
            "total_profit": np.nan,
            "avg_price_discount": np.nan,
            "rolling_4wk_avg": np.nan,
            "Forecasted_Demand": forecast["Forecasted_Demand"],
            "lead_time_days": inventory_row["lead_time_days"],
            "current_stock_level": inventory_row["current_stock_level"],
            "sigma_d": inventory_metrics["sigma_d"],
            "avg_daily_demand": inventory_metrics["avg_daily_demand"],
            "safety_stock": inventory_metrics["safety_stock"],
            "reorder_point": inventory_metrics["reorder_point"],
            "mae": mae,
            "mape": mape,
            "period": "forecast",
            "is_forecast": True,
        }
    )

    return pd.concat([history_rows, forecast_rows], ignore_index=True)


def write_forecast_to_db(connection: sqlite3.Connection, df: pd.DataFrame) -> None:
    df.to_sql(OUTPUT_TABLE, connection, if_exists="replace", index=False)
    logger.info("Wrote %d rows to '%s'", len(df), OUTPUT_TABLE)


def main() -> None:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    with sqlite3.connect(DB_PATH) as conn:
        try:
            weekly_sales = pd.read_sql_query(
                "SELECT * FROM df_weekly",
                conn,
                parse_dates=["week_start_date"],
            )
        except Exception:
            weekly_sales = pd.read_sql_query(
                WEEKLY_AGG_SQL,
                conn,
                parse_dates=["week_start"],
            )
        inventory = load_inventory_status(conn)

    weekly_sales = normalize_weekly_columns(weekly_sales)
    required_columns = {
        "product_id",
        "ds",
        "y",
        "total_revenue",
        "total_profit",
        "avg_price_discount",
        "rolling_4wk_avg",
    }
    missing_columns = required_columns - set(weekly_sales.columns)
    if missing_columns:
        raise ValueError(f"Missing required weekly sales columns: {missing_columns}")

    selected_products = select_products(weekly_sales, TOP_N_PRODUCTS)
    logger.info("Selected %d products for forecasting", len(selected_products))

    consolidated = []
    for product_id in selected_products:
        product_df = weekly_sales[weekly_sales["product_id"] == product_id].copy()
        if product_df.empty:
            logger.warning("No weekly data for product_id %s", product_id)
            continue

        inventory_row = inventory[inventory["product_id"] == product_id]
        if inventory_row.empty:
            logger.warning("Missing inventory row for product_id %s", product_id)
            continue
        inventory_row = inventory_row.iloc[0]

        try:
            product_consolidated = build_forecast_for_product(product_df, inventory_row)
            consolidated.append(product_consolidated)
            logger.info("Processed product_id %s with %d history rows and %d forecast rows",
                        product_id,
                        len(product_df),
                        FORECAST_WEEKS,
                        )
        except Exception as exc:
            logger.exception("Skipping product_id %s due to error: %s", product_id, exc)

    if not consolidated:
        raise RuntimeError("No forecasts were generated")

    forecast_df = pd.concat(consolidated, ignore_index=True)
    forecast_df = forecast_df.sort_values(["product_id", "ds"]) 

    # Write results back to SQLite
    with sqlite3.connect(DB_PATH) as conn:
        write_forecast_to_db(conn, forecast_df)

    logger.info("Forecasting completed successfully")
    


if __name__ == "__main__":
    main()
