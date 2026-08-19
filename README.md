## Introduction

The fact that equity returns do not follow a normal distribution has been widely researched since being first introduced by Mandelbrot (1963)<sup>[(1)](#ref-1)</sup> and Fama (1965)<sup>[(2)](#ref-2)</sup>. As such, the goal of this project is not to add to the already substantial body of academic work but instead to create a simple demonstration of the non-normality of equity returns for a basket of fifteen common stocks and ETFs. Additionally, we also compare the normal distribution to plausible alternatives and examine whether our findings change over different time horizons (e.g., 5-, 10-, and 15-year datasets). A summary of our findings is provided in dashboard format via the [`streamlit`](https://pypi.org/project/streamlit/) and [`altair`](https://altair-viz.github.io) python libraries.

## Data Source and Structure

Our dataset consists of daily close price, adjusted for dividends and stock splits, for each of the tickers in our basket of common stocks and ETFs. The data was sourced from from [Yahoo Finance](https://finance.yahoo.com/) via the `yfinance` library. Given that we are comparing the actual distribution of equity returns to the normal distribution we run our analysis using log returns intstead of simple returns. This ensures that our data has bounds $(-\infty,\infty)$ which is consistent with the bounds of a normal distribution (simple returns are bounded below because it is impossible to lose more than the value of the ticker).

## Methods Used

TBU

## Requirements

- Python 3.9+
- [`yfinance`](https://pypi.org/project/yfinance/)
- [`numpy`](https://numpy.org)
- [`pandas`](https://pypi.org/project/pandas/)
- [`altair`](https://altair-viz.github.io)
- [`scipy`](https://scipy.org)
- [`streamlit`](https://pypi.org/project/streamlit/)

## References

<a id="ref-1">[1]</a> Mandelbrot, B. (1963). The Variation of Certain Speculative Prices. *The Journal of Business*, 36(4), 394–419. [https://doi.org/10.1086/294632](https://doi.org/10.1086/294632)

<a id="ref-2">[2]</a> Fama, E. F. (1965). The Behavior of Stock-Market Prices. *The Journal of Business*, 38(1), 34–105. [https://doi.org/10.1086/294743](https://doi.org/10.1086/294743)

## Author

Thomas Costin ([tcostin20@gmail.com](mailto:tcostin20@gmail.com))
