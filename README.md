# E-Commerce Demand Forecasting & Inventory Optimization

![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)
![SQLite](https://img.shields.io/badge/Database-SQLite-003B57.svg)
![Forecasting](https://img.shields.io/badge/Forecasting-Facebook%20Prophet-orange.svg)
![Visualization](https://img.shields.io/badge/Visualization-Tableau-E97627.svg)
![Analytics](https://img.shields.io/badge/Domain-Retail%20Analytics-success.svg)

## Overview

An end-to-end retail analytics project that transforms historical e-commerce transactions into demand forecasts and inventory planning decisions.

The solution uses **Python, SQLite, SQL, Facebook Prophet, and Tableau** to generate realistic retail data, forecast weekly demand for individual products, calculate inventory control metrics, identify products needing attention, and present insights through an executive dashboard.

Unlike a standard forecasting project, this workflow connects forecast output directly to replenishment decisions through **Safety Stock**, **Reorder Point**, and **Inventory Risk Classification**.

---

## Business Problem

Retail businesses must balance two costly risks:

- **Stockouts** that lead to lost revenue and poor customer experience.
- **Overstocking** that increases storage and working-capital costs.

This project addresses those risks by forecasting future product demand and translating the forecast into practical inventory recommendations.

---

## Project Objectives

- Generate a realistic multi-year e-commerce dataset.
- Store transactional and inventory data in a relational SQLite database.
- Aggregate product sales into weekly demand series using SQL.
- Forecast demand for the next 12 weeks using Facebook Prophet.
- Calculate inventory planning metrics including safety stock and reorder point.
- Classify products as Healthy, Warning, or Critical.
- Build an executive Tableau dashboard for retail and supply-chain decision support.

---

## End-to-End Workflow

```text
Synthetic Retail Data Generation
            │
            ▼
SQLite Relational Database
            │
            ▼
SQL Weekly Sales Aggregation
            │
            ▼
Product-Level Demand Forecasting
            │
            ▼
Inventory Optimization Logic
            │
            ▼
Tableau Executive Dashboard
```

---

## Tech Stack

| Area | Tools and Technologies |
|---|---|
| Programming | Python |
| Data Processing | Pandas, NumPy |
| Database | SQLite |
| Querying | SQL |
| Forecasting | Facebook Prophet |
| Model Evaluation | Scikit-learn MAE |
| Visualization | Tableau |
| Version Control | Git and GitHub |

---

## Repository Structure

```text
E-Commerce-Demand-Forecasting-Inventory-Optimization/
│
├── data/
│   ├── ecommerce_data.db
│   ├── final_dashboard_data.csv
│   └── predicted_inventory_forecast.csv
│
├── scripts/
│   ├── generate_data.py
│   └── forecast_inventory.py
│
├── dashboard/
│   └── E-Commerce Demand Forecasting.twb
│
├── images/
│   └── dashboard_overview.png
│
├── README.md
├── requirements.txt
└── .gitignore
```


## Dataset Summary

The project creates a synthetic but business-realistic retail dataset with:

- **3 years** of data from January 2023 to December 2025
- **120 products**
- **5,000 customers**
- **50,000+ transactions**
- Seasonal demand spikes during November and December
- Lower demand during January and February
- Promotions
- Bulk-order outliers
- Missing-value scenarios
- Product stockout periods
- Product-level current inventory and lead-time data

### Database Tables

| Table | Description |
|---|---|
| `customers` | Customer master data, including country and acquisition channel |
| `products` | Product catalog with category, unit cost, and unit price |
| `sales_transactions` | Transaction-level sales data with quantity and promotion flag |
| `inventory_status` | Current stock level and supplier lead time for each product |
| `predicted_inventory_forecast` | Historical demand, forecast output, and inventory planning metrics |

---

## Phase 1 — Data Generation and SQL Setup

A Python data generator creates the transactional database and simulates realistic retail behavior.

### Key Data Engineering Features

- Relational SQLite database design
- Customer, product, transaction, and inventory tables
- Seasonal sales behavior
- Promotion flags
- Bulk order anomalies
- Null values for data quality handling
- Product stockout events

---

## Phase 2 — Demand Forecasting and Inventory Optimization

### Demand Forecasting

Sales transactions are aggregated into weekly demand at the product level.

For every product, the forecasting pipeline:

1. Sorts historical weekly demand.
2. Creates training and testing periods.
3. Trains a Facebook Prophet model.
4. Produces a 12-week forward forecast.
5. Calculates Mean Absolute Error (MAE).
6. Saves results to the SQLite forecast output table.

### Inventory Optimization Metrics

The pipeline calculates:

- Average Daily Demand
- Demand Variability
- Safety Stock
- Reorder Point
- Lead-Time Demand

### Inventory Risk Classification

| Status | Business Meaning |
|---|---|
| 🟢 Healthy | Current stock is sufficient relative to the reorder threshold |
| 🟠 Warning | Current stock is approaching the risk zone |
| 🔴 Critical | Current stock is below the reorder point and requires immediate attention |

---

## Phase 3 — Tableau Dashboard and Business Insights

The Tableau dashboard is designed for retail managers, demand planners, and supply-chain stakeholders.

### Dashboard Preview

<img width="1920" height="1200" alt="E-Commerce Demand Forecasting Dashboard" src="https://github.com/user-attachments/assets/db57d8fd-1d53-4760-96fa-4526656ecf78" />

### Executive KPI Layer

- Total Revenue
- Total Profit
- Forecast Demand
- Products Requiring Attention
- Forecast Horizon
- Products Forecasted

### Sales and Forecasting Analytics

- Revenue Trend
- Actual Sales vs 12-Week Demand Forecast
- Top 15 Revenue-Generating Products

### Inventory Optimization Analytics

- Inventory Status Donut
- Inventory Risk Matrix
- Reorder Action Table
- Product-level stock risk monitoring

---

## Key Results

| Metric | Result |
|---|---:|
| Revenue Analysed | ₹99.2 Million |
| Profit Analysed | ₹41.8 Million |
| Products Forecasted | 120 |
| Forecast Horizon | 12 Weeks |
| Products Requiring Attention | 38 |
| Critical Products Identified | 1 |

---

## Business Value

This solution helps retail teams:

- Plan replenishment more proactively.
- Identify products with potential stockout risk.
- Prioritize products requiring inventory attention.
- Connect demand forecasting with operational inventory decisions.
- Monitor revenue, profit, product performance, and inventory health from one dashboard.

---

## How to Run the Project

### Prerequisites

- Python 3.10 or later
- Git
- Tableau Desktop or Tableau Public
- A virtual environment is recommended

### 1. Clone the Repository

```bash
git clone https://github.com/sharath-redddy/E-Commerce-Demand-Forecasting-Inventory-Optimization.git
cd E-Commerce-Demand-Forecasting-Inventory-Optimization
```

### 2. Create and Activate a Virtual Environment

**Windows PowerShell**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

If `requirements.txt` has not yet been created, install the required packages with:

```bash
pip install pandas numpy prophet scikit-learn
```

### 4. Generate the Retail Database

```bash
python scripts/generate_data.py
```

This creates:

```text
data/ecommerce_data.db
```

and populates the database with customer, product, sales transaction, and inventory data.

> If `generate_data.py` writes the database to the project root in your current version, move the created `ecommerce_data.db` file into the `data/` folder after execution.

### 5. Run Demand Forecasting and Inventory Optimization

```bash
python scripts/forecast_inventory.py
```

This process:

- Reads sales and inventory data from SQLite.
- Aggregates weekly product demand.
- Runs Prophet forecasting for each eligible product.
- Generates 12-week demand forecasts.
- Calculates safety stock and reorder point.
- Writes results to the `predicted_inventory_forecast` table.

### 6. Export Dashboard Data

Open `ecommerce_data.db` in DB Browser for SQLite or another SQLite client.

Export the `predicted_inventory_forecast` table as:

```text
data/final_dashboard_data.xlsx
```

### 7. Open the Tableau Dashboard

Open:

```text
dashboard/E-Commerce Demand Forecasting.twb
```

If Tableau requests a data source, reconnect it to:

```text
data/final_dashboard_data.xlsx
```

The dashboard will populate with the latest forecast and inventory results.

---

## How the Project Works in Practice

```text
generate_data.py
        ↓
ecommerce_data.db
        ↓
forecast_inventory.py
        ↓
predicted_inventory_forecast output table
        ↓
final_dashboard_data.xlsx
        ↓
Tableau dashboard
```

---

## Skills Demonstrated

- Data Engineering
- Synthetic Data Generation
- Relational Database Design
- SQL Aggregation
- Data Cleaning
- Time-Series Forecasting
- Demand Planning
- Inventory Optimization
- Supply Chain Analytics
- Tableau Dashboard Development
- KPI Design
- Business Storytelling
- Git and GitHub

---

## Future Enhancements

- Compare Prophet with XGBoost, LightGBM, or ARIMA forecasting models.
- Add a fully automated Python export from SQLite to Excel or CSV.
- Build a one-command pipeline runner.
- Add model monitoring and automated retraining.
- Add supplier-level lead-time analysis.
- Integrate a cloud data warehouse such as BigQuery.
- Build a Streamlit application for operational users.
- Replace synthetic data with real ERP, POS, or e-commerce platform data.

---


## Final Outcome

This project demonstrates how a retail analytics workflow can move beyond simple sales reporting. It uses predictive demand signals to support inventory planning decisions, helping stakeholders identify what to replenish, when to act, and where inventory risk is concentrated.
