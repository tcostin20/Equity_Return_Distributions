# Equity Return Distributions

An interactive Streamlit dashboard for exploring the historical price behavior of publicly traded equities. The app downloads daily closing prices from Yahoo Finance, caches them locally, and visualizes monthly average closing prices with summary statistics describing the underlying return distribution.

## Overview

This project pulls historical daily closing price data for a configurable list of equity tickers, persists it to a local CSV cache, and serves an interactive dashboard for exploring price trends over time. For each selected ticker, the app resamples daily prices to monthly averages and computes distributional statistics (mean, standard deviation, skewness, and kurtosis) to characterize the shape of the ticker's return behavior.

## Features

- **Automated data retrieval** — Fetches daily closing prices via the [`yfinance`](https://pypi.org/project/yfinance/) API for any list of ticker symbols over a specified date range and interval.
- **Local caching** — Downloaded data is saved to a CSV file and only re-fetched when the requested tickers change, avoiding redundant API calls.
- **Interactive visualization** — A Streamlit dashboard with a ticker selection dropdown and a wide-layout line chart of monthly average closing prices.
- **Distributional statistics** — Computes mean, standard deviation, skewness, and kurtosis for each ticker's monthly price series.

## Project Structure

```
Equity_Return_Distributions/
├── equity_return_distributions.py   # Main application: data retrieval, caching, and Streamlit dashboard
├── price_data/
│   └── closing_prices.csv           # Cached closing price data (auto-generated)
└── README.md
```

## Requirements

- Python 3.9+
- [`yfinance`](https://pypi.org/project/yfinance/)
- [`pandas`](https://pypi.org/project/pandas/)
- [`streamlit`](https://pypi.org/project/streamlit/)

Install dependencies with:

```bash
pip install yfinance pandas streamlit
```

## Usage

Run the app with Streamlit:

```bash
streamlit run equity_return_distributions.py
```

By default, the app tracks `AAPL`, `MSFT`, and `GOOGL` over a 5-year daily window. To analyze different equities or time periods, edit the `tickers`, `period_start`, `period_end`, and `interval` arguments passed to `get_data()` in `main()`.

Once running, use the dropdown in the dashboard to select a ticker and view its monthly average closing price trend.

## Data Source

All price data is sourced from [Yahoo Finance](https://finance.yahoo.com/) via the `yfinance` library. Prices are adjusted for splits and dividends (`auto_adjust=True`).

## Author

Thomas Costin ([tcostin20@gmail.com](mailto:tcostin20@gmail.com))
