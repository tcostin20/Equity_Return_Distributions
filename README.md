## Introduction

The fact that equity returns do not follow a normal distribution has been widely researched since being first explored by Mandelbrot (1963)<sup>[(1)](#ref-1)</sup> and Fama (1965)<sup>[(2)](#ref-2)</sup>. As such, the goal of this project is not to add to the already substantial body of academic work on this subject. Instead, we aim to create a simple demonstration of the non-normality of equity returns for a basket of fifteen publicly traded stocks. Additionally, we explore plausible alternative distributions that better describe equity returns and examine whether our findings change over sub-periods.

## Data Source and Structure

Our dataset consists of daily close price, adjusted for dividends and stock splits, for each of the tickers in our basket of stocks. The data was sourced from from [Yahoo Finance](https://finance.yahoo.com/) via the `yfinance` library and is for the 15-year period ended August 25, 2026. Given that we are anchoring on the normal distribution we run our analysis using log returns intstead of simple returns, which gives our data bounds that are consistent with the bounds of a normal distribution (simple returns are bounded below at negative one because it is impossible to lose more than the value of the ticker). After calculating log returns we drop the first row of our dataset (i.e., the first day of data) as there is no prior day close price to use to calculate returns for that day.

## Ticker Selection Rationale

The tickers we selected consist of ten technology companies that have invested heavily in artifical intelligence and/or provide services/products realted to AI and five alternative asset managers with exposure to the private credit industry. We are interested in whether these two groups have seen equity returns become less normally distributed since the release of ChatGPT on November 30, 2022. For the ten technology companies, our question is driven by articles in major news publications that suggest AI related spending has spooked some equity investors ([WSJ](https://www.wsj.com/tech/ai/meta-q2-earnings-report-2026-stock-9808dd3c)). For the five alternative asset managers, our question is driven by a recent surge in redemption requests at large private credit funds ([WSJ](https://www.wsj.com/finance/investing/investors-seek-to-pull-nearly-16-billion-from-private-credit-funds-81b6fe37)), which appears to also be related to concerns about the impact of AI on software businesses.

## Methdology and Findings

After gathering and cleaning our data, we examine the dataset visually using a histogram that compares actual density to implied PDF based on MLE parameters, quantile-quantile plot, and box-and-wisker plot. These visualizations support our assumption that none of the selected tickers have normally distributed returns, although Blackstone, Google, and Blue Owl diverge less significantly from the normal distribution than the others. The table of summary statistics presented below these visuals adds further credence to our assumption by showing that all tickers have positive excess kurtosis and non-zero skewness. We note that Blackstone, Google, and Blue Owl have less excess kurtosis than the other tickers, which is in agreement with our previous comment about those tickers diverging less from the normal distribution than others.

## Requirements

- Python 3.9+
- [`yfinance`](https://pypi.org/project/yfinance/)
- [`numpy`](https://numpy.org)
- [`pandas`](https://pypi.org/project/pandas/)
- [`altair`](https://altair-viz.github.io)
- [`scipy`](https://scipy.org)
- [`streamlit`](https://pypi.org/project/streamlit/)
- [`arch`](https://pypi.org/project/arch/)

## References

<a id="ref-1">[1]</a> Mandelbrot, B. (1963). The Variation of Certain Speculative Prices. *The Journal of Business*, 36(4), 394–419. [https://doi.org/10.1086/294632](https://doi.org/10.1086/294632)

<a id="ref-2">[2]</a> Fama, E. F. (1965). The Behavior of Stock-Market Prices. *The Journal of Business*, 38(1), 34–105. [https://doi.org/10.1086/294743](https://doi.org/10.1086/294743)

## Author

Thomas Costin ([tcostin20@gmail.com](mailto:tcostin20@gmail.com))
