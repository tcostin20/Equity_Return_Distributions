## Overview

This project explores the extent to which equity returns follow a normal distribution. Using daily adjusted close prices across 15 publicly-traded stocks, we begin by assuming that that log returns are normally distributed and calculate parameters $\mu$ and $\sigma$ using maximum likelihood estimation. These parameters are used to generate confidence intervals by ticker for $\mu$ and $\sigma$, which are compared to confidence intervals generated using both traditional and block bootstrap methods.

## Requirements

- Python 3.9+
- [`yfinance`](https://pypi.org/project/yfinance/)
- [`numpy`](https://numpy.org)
- [`pandas`](https://pypi.org/project/pandas/)
- [`altair`](https://altair-viz.github.io)
- [`scipy`](https://scipy.org)
- [`streamlit`](https://pypi.org/project/streamlit/)

## Data Source

All price data is sourced from [Yahoo Finance](https://finance.yahoo.com/) via the `yfinance` library. Prices are adjusted for splits and dividends.

## Author

Thomas Costin ([tcostin20@gmail.com](mailto:tcostin20@gmail.com))
