## Overview

The goal of this project is to explore the extent to which equity returns follow a normal distribution. Using daily adjusted close prices across 15 publicly-traded stocks, we begin by assuming that that log returns are normally distributed and calculate parameters $\mu$ and $\sigma$ using maximum likelihood estimation. These parameters are then used to generate confidence intervals ($\alpha = 0.05$) for $\mu$ and $\sigma$ by each ticker.

## Requirements

- Python 3.9+
- [`yfinance`](https://pypi.org/project/yfinance/)
- [`pandas`](https://pypi.org/project/pandas/)
- [`streamlit`](https://pypi.org/project/streamlit/)

## Data Source

All price data is sourced from [Yahoo Finance](https://finance.yahoo.com/) via the `yfinance` library. Prices are adjusted for splits and dividends (`auto_adjust=True`).

## Author

Thomas Costin ([tcostin20@gmail.com](mailto:tcostin20@gmail.com))
