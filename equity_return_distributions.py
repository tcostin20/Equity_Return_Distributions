'''
------------------------------------------------------------------------------
Description: Analysis of equity return distributions for various asset classes
Author: Thomas Costin (tcostin20@gmail.com)
Date started: 8/3/2026
Data source: Yahoo Finance (https://finance.yahoo.com/)
------------------------------------------------------------------------------
'''

import yfinance as yf
import numpy as np
import pandas as pd
import altair as alt
from scipy import stats
from pathlib import Path
import streamlit as st
import sys
from streamlit.web import cli as stcli
from arch import bootstrap as ar
import math

#################################################################################################################################
def get_data(tickers:list,period_start:str,period_end:str,interval:str, output_path:str) -> None:
    '''
    Function that creates a csv file containing equity return data for each ticker the user provides.
    
    Parameters
    ----------
    ticker (list):      A list of ticker symbols for which to retrieve equity return data.
    period_start (str): The start date for the data period.
    period_end (str):   The end date for the data period.
    interval (str):     The frequency of the data points.
    
    Returns
    ----------
    None
    '''
    # check to see whether a csv file already exists at the output path
    if Path(output_path).exists():
            existing_columns = pd.read_csv(output_path, index_col=0, nrows=0).columns
            if set(existing_columns) == set(tickers):
                return  # if the file exists and is identical do nothing

    # download the closing price data for the specified tickers and time period
    closing_price_data = yf.download(tickers, start=period_start, end=period_end, interval=interval, auto_adjust=True)['Close'] # type: ignore

    # save data set to the output path
    closing_price_data.to_csv(output_path, index=True, float_format='%.2f')

#################################################################################################################################
def MLE_fit(data: pd.DataFrame) -> pd.DataFrame:
    '''
    Function that computes the Normal distribution parameters mu and sigma
    for each ticker's log return series using maximum likelihood estimation.

    Parameters
    ----------
    data (pd.DataFrame): DataFrame of closing prices, with tickers as columns and
                         dates as the index.

    Returns
    ----------
    pd.DataFrame: DataFrame indexed by ticker with columns 'mu', 'sigma', and 'n'
                  holding the Normal parameters and sample size for each ticker's 
                  log returns.
    '''
    # compute log returns for each ticker
    log_returns = np.log(data / data.shift(1)).dropna() # type: ignore

    # Note: we take the log return instead of simple return to ensure our distribution has
    # bounds from negative infinity to positive infinity, which mirrors the normal
    # distribution. A simple return would have a lower bound at negative 1. We use the
    # "dropna()" function because the shift causes the first row of data to be NaN.

    # MLE for mu is the sample mean of returns (definitional)
    mu = log_returns.mean()

    # MLE for sigma is the biased (ddof=0) sample standard deviation of returns (definitional)
    sigma = log_returns.std(ddof=0)

    # number of return observations used to fit each ticker
    n = log_returns.count()

    # combine into a single DataFrame indexed by ticker
    MLE_fit_data = pd.DataFrame({'mu': mu, 'sigma': sigma, 'n': n})
    return MLE_fit_data

#################################################################################################################################
def parametric_CI(MLE_fit: pd.DataFrame, alpha: float) -> pd.DataFrame:
    '''
    Function that generates parametric confidence intervals for the mean and variance
    of each ticker's log return series, based on the Normal MLE fit.

    Parameters
    ----------
    MLE_fit (pd.DataFrame): DataFrame indexed by ticker with columns 'mu', 'sigma',
                            and 'n', as produced by MLE_fit_normal.
    confidence (float):     The confidence level for the interval.

    Returns
    -------
    pd.DataFrame: DataFrame indexed by ticker with columns 'mu_lower', 'mu_upper',
                  'var_lower', and 'var_upper' holding the confidence interval bounds
                  for the mean and variance of each ticker's log returns.
    '''
    # unpack fitted parameters and sample size
    mu = MLE_fit['mu']
    n = MLE_fit['n']

    # calculate variance based on normal distribution (this uses n-1 DOF vs. n for the MLE calculation)
    sample_var = MLE_fit['sigma']**2 * n / (n - 1)
    sample_std = np.sqrt(sample_var)

    # calculate confidence interval for mu and store upper/lower bounds in variables
    mu_lower, mu_upper = stats.t.interval(1 - alpha, df=n - 1, loc=mu, scale=sample_std / np.sqrt(n))

    # calculate critical values for variance using chi-squared distribution
    chi2_lower = stats.chi2.ppf(alpha / 2, df=n - 1)
    chi2_upper = stats.chi2.ppf(1 - alpha / 2, df=n - 1)

    # 
    var_lower = (n - 1) * sample_var / chi2_upper
    var_upper = (n - 1) * sample_var / chi2_lower

    # combine into a single DataFrame indexed by ticker
    return pd.DataFrame({
        'mu_lower': mu_lower,
        'mu_upper': mu_upper,
        'var_lower': var_lower,
        'var_upper': var_upper
    })

#################################################################################################################################
def bootstrap_CI(data: pd.DataFrame, n_boot: int, alpha: float, random_state: int) -> pd.DataFrame:
    '''
    Function that generates non-parametric bootstrap confidence intervals 
    for the mean and standard deviation of each ticker's log return series.

    Parameters
    ----------
    data (pd.DataFrame): DataFrame of closing prices, with tickers as columns and
                         dates as the index.
    n_boot (int):        Number of bootstrap resamples to draw.
    alpha (float):       Significance level for the interval.
    random_state (int):  Seed for the random number generator, for reproducibility.

    Returns
    -------
    pd.DataFrame: DataFrame indexed by ticker with columns 'mu_lower', 'mu_upper',
                  'sigma_lower', and 'sigma_upper' holding the bootstrap confidence
                  interval bounds for the mean and standard deviation of each
                  ticker's log returns.
    '''
    # compute log returns for each ticker (keep statistic consistent across parametric and bootstrap)
    log_returns = np.log(data / data.shift(1)).dropna() # type: ignore

    # create random number generator to be used for resampling
    random_numbers = np.random.default_rng(random_state)

    results = {}
    for ticker in log_returns.columns:
        sample = log_returns[ticker].to_numpy() # isolate ticker data and convert to numpy array to improve speed
        n = len(sample) # define resample size

        # draw n_boot resamples of size n
        sample_indices = random_numbers.integers(0, n, size=(n_boot, n))
        boot_samples = sample[sample_indices]

        # compute mean and standard deviation on every resample
        boot_means = boot_samples.mean(axis=1)
        boot_stds = boot_samples.std(axis=1, ddof=1)

        # input results into dictionary using the percentile method (i.e., find the 97.5% and 2.5% percentiles)
        results[ticker] = {
            'mu_lower': np.percentile(boot_means, 100 * alpha / 2),
            'mu_upper': np.percentile(boot_means, 100 * (1 - alpha / 2)),
            'sigma_lower': np.percentile(boot_stds, 100 * alpha / 2),
            'sigma_upper': np.percentile(boot_stds, 100 * (1 - alpha / 2)),
        }

    return pd.DataFrame.from_dict(results, orient='index')

#################################################################################################################################
def block_bootstrap_CI(data:pd.DataFrame, n_boot: int, alpha: float, random_state: int) -> pd.DataFrame:
    '''
    Function that generates non-parametric block bootstrap confidence intervals 
    for the mean and standard deviation of each ticker's log return series.

    Parameters
    ----------
    data (pd.DataFrame): DataFrame of closing prices, with tickers as columns and
                         dates as the index.
    n_boot (int):        Number of bootstrap resamples to draw.
    alpha (float):       Significance level for the interval.
    random_state (int):  Seed for the random number generator, for reproducibility.

    Returns
    -------
    pd.DataFrame: DataFrame indexed by ticker with columns 'mu_lower', 'mu_upper',
                  'sigma_lower', and 'sigma_upper' holding the block bootstrap confidence
                  interval bounds for the mean and standard deviation of each
                  ticker's log returns.
    '''
    # compute log returns for each ticker (keep statistic consistent across parametric and bootstrap)
    log_returns = np.log(data / data.shift(1)).dropna() # type: ignore

    # create random number generator to be used for resampling
    random_numbers = np.random.default_rng(random_state)

    # calculate optimal block length
    circular_block_length = ar.optimal_block_length(log_returns)['circular'].round().clip(lower=1)

    results = {}
    for ticker in log_returns.columns:
        sample = log_returns[ticker].to_numpy() # isolate ticker data and convert to numpy array to improve speed
        n = len(sample)
        ticker_block_length = int(circular_block_length[ticker]) # retrieve boot length from circular block length array
        num_blocks = math.ceil(n/ticker_block_length) # calculate number of blocks needed ensuring you have enough indicies

        # generate n_boot by num_blocks matrix that contains starting indices for each block
        block_start_positions = random_numbers.integers(0, n, size=(n_boot, num_blocks))

        # expand each block start into a full block of length L, wrapping around via modulo n
        block_offsets = np.arange(ticker_block_length) # relative positions within a block
        block_indices = (block_start_positions[:, :, None] + block_offsets) % n  # shape (n_boot, num_blocks, L)

        # flatten the blocks into full-length resamples and trim the overshoot down to exactly n columns
        sample_indices = block_indices.reshape(n_boot, num_blocks * ticker_block_length)[:, :n]

        # draw n_boot resamples of size n
        block_boot_samples = sample[sample_indices]

        # compute mean and standard deviation on every resample
        boot_means = block_boot_samples.mean(axis=1)
        boot_stds = block_boot_samples.std(axis=1, ddof=1)

        # input results into dictionary using the percentile method (i.e., find the 97.5% and 2.5% percentiles)
        results[ticker] = {
            'mu_lower': np.percentile(boot_means, 100 * alpha / 2),
            'mu_upper': np.percentile(boot_means, 100 * (1 - alpha / 2)),
            'sigma_lower': np.percentile(boot_stds, 100 * alpha / 2),
            'sigma_upper': np.percentile(boot_stds, 100 * (1 - alpha / 2)),
        }

    return pd.DataFrame.from_dict(results, orient='index')

#################################################################################################################################
def visualize_data(output_path: str, MLE_params:pd.DataFrame, CI_parametric: pd.DataFrame, CI_bootstrap: pd.DataFrame, CI_block_bootstrap: pd.DataFrame) -> None:
    '''
    Function that visualizes the equity return data for each ticker.

    Parameters
    ----------
    output_path (str):            The path to the csv file containing the equity return data.
    MLE_params (pd.DataFrame):    MLE-fit Normal parameters for each ticker.
    CI_parametric (pd.DataFrame): Parametric confidence intervals for each ticker.
    CI_bootstrap (pd.DataFrame):  Bootstrap confidence intervals for each ticker.
    CI_block_bootstrap (pd.DataFrame): Block bootstrap confidence intervals for each ticker.

    Returns
    ----------
    None
    '''
    # single color used for the histogram bars, regardless of the selected ticker
    BAR_COLOR = '#2a78d6'

    # switch layout to widescreen mode
    st.set_page_config(layout="wide", page_title="Equity Return Distributions")

    # custom styling for a cleaner, more professional look
    st.markdown("""
        <style>
        :root {
            --chart-surface: #ffffff;
            --page-plane: #ffffff;
            --ink-primary: #0b0b0b;
            --ink-secondary: #52514e;
            --ink-muted: #898781;
            --border: rgba(11,11,11,0.10);
        }
        .stApp {
            background-color: var(--page-plane);
            font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
        }
        .block-container {
            padding-top: 2rem;
            max-width: 1200px;
        }
        h1, h2, h3 {
            color: var(--ink-primary);
            font-weight: 600;
            letter-spacing: -0.01em;
        }
        [data-testid="stMetric"] {
            background-color: var(--chart-surface);
            border: 1px solid var(--border);
            border-radius: 10px;
            padding: 14px 18px;
        }
        [data-testid="stMetricLabel"] {
            color: var(--ink-secondary);
        }
        [data-testid="stCaptionContainer"] {
            color: var(--ink-muted);
        }
        </style>
    """, unsafe_allow_html=True)

    # cache the data to avoid reloading it every time the app is run
    @st.cache_data
    def load_data(output_path: str) -> pd.DataFrame:
        return pd.read_csv(output_path, index_col=0, parse_dates=True)

    # define function to pull full company name from Yahoo Finance given a ticker symbol
    # (cached so the app doesn't re-hit the network on every widget interaction)
    @st.cache_data
    def get_company_name(ticker: str) -> str:
        return yf.Ticker(ticker).info['longName']  # type: ignore

    # pull raw daily data from CSV file
    raw_data = load_data(output_path)

    st.title("Equity Return Distributions")
    st.caption("All data is sourced from Yahoo Finance via the yfinance library")

    # always analyze the full ticker universe
    tickers = list(raw_data.columns)
    mle_params = MLE_params.loc[tickers]

    # daily log returns, matching the series the confidence intervals are computed on
    log_returns = np.log(raw_data / raw_data.shift(1)).dropna() # type: ignore
    filtered_log_returns = log_returns[tickers]

    # map tickers to company names for display
    company_names = {t: get_company_name(t) for t in raw_data.columns}

    # dropdown to pick a single ticker for the return distribution histogram
    selected_ticker = st.selectbox(
        "Select a ticker",
        options=tickers,
        format_func=lambda t: company_names[t],
        width=250
    )

    # build a density histogram (bar heights integrate to 1, not raw counts) so the
    # shape is directly comparable to a fitted normal PDF regardless of sample size
    selected_returns = log_returns[selected_ticker]
    hist_counts, bin_edges = np.histogram(selected_returns, bins="auto", density=True)
    hist_data = pd.DataFrame({
        "bin_left": bin_edges[:-1],
        "bin_right": bin_edges[1:],
        "density": hist_counts
    })

    # fitted normal PDF using this ticker's MLE mu/sigma, evaluated across the
    # histogram's range, so the overlay lines up with the empirical bars
    mu = mle_params.loc[selected_ticker, 'mu']
    sigma = mle_params.loc[selected_ticker, 'sigma']
    x_grid = np.linspace(bin_edges[0], bin_edges[-1], 200)
    normal_curve = pd.DataFrame({
        "log_return": x_grid,
        "density": stats.norm.pdf(x_grid, loc=mu, scale=sigma)
    })

    st.subheader(f"Daily Log Return Distribution — {company_names[selected_ticker]}")
    histogram = (
        alt.Chart(hist_data)
        .mark_bar(color=BAR_COLOR)
        .encode(
            x=alt.X("bin_left:Q", bin="binned", title=None, axis=alt.Axis(
                format="%", gridColor="#e1e0d9", domainColor="#c3c2b7",
                tickColor="#c3c2b7", labelColor="#52514e", titleColor="#0b0b0b")),
            x2="bin_right:Q",
            y=alt.Y("density:Q", title="Density", axis=alt.Axis(
                gridColor="#e1e0d9", domainColor="#c3c2b7",
                tickColor="#c3c2b7", labelColor="#52514e", titleColor="#0b0b0b")),
            tooltip=[
                alt.Tooltip("bin_left:Q", title="Bin Start", format=".2%"),
                alt.Tooltip("bin_right:Q", title="Bin End", format=".2%"),
                alt.Tooltip("density:Q", title="Density", format=".2f"),
            ]
        )
    )
    fitted_curve = (
        alt.Chart(normal_curve)
        .mark_line(color="#0b0b0b", strokeWidth=2, strokeDash=[4, 3])
        .encode(
            x=alt.X("log_return:Q"),
            y=alt.Y("density:Q"),
            tooltip=[
                alt.Tooltip("log_return:Q", title="Log Return", format=".2%"),
                alt.Tooltip("density:Q", title="Fitted Normal Density", format=".2f"),
            ]
        )
    )
    st.altair_chart((histogram + fitted_curve).configure_view(strokeWidth=0), use_container_width=True)
    st.caption("Note: dashed line is normal PDF fitted via MLE")

    # Q-Q plot comparing the selected ticker's sample quantiles against the quantiles
    # implied by the fitted normal (mu, sigma) - points falling on the reference line
    # indicate agreement with normality; curvature in the tails indicates fat/thin tails
    qq_theoretical, qq_sample = stats.probplot(selected_returns, dist="norm", sparams=(mu, sigma), fit=False)
    qq_data = pd.DataFrame({"theoretical": qq_theoretical, "sample": qq_sample})
    qq_range = [qq_data[["theoretical", "sample"]].min().min(), qq_data[["theoretical", "sample"]].max().max()]
    qq_reference_data = pd.DataFrame({"theoretical": qq_range, "sample": qq_range})

    st.subheader(f"Normal Q-Q Plot — {company_names[selected_ticker]}")
    qq_scatter = (
        alt.Chart(qq_data)
        .mark_circle(size=30, color=BAR_COLOR, opacity=0.7)
        .encode(
            x=alt.X("theoretical:Q", title="Theoretical Quantile (Fitted Normal)", axis=alt.Axis(
                format="%", gridColor="#e1e0d9", domainColor="#c3c2b7",
                tickColor="#c3c2b7", labelColor="#52514e", titleColor="#0b0b0b")),
            y=alt.Y("sample:Q", title="Sample Quantile (Observed)", axis=alt.Axis(
                format="%", gridColor="#e1e0d9", domainColor="#c3c2b7",
                tickColor="#c3c2b7", labelColor="#52514e", titleColor="#0b0b0b")),
            tooltip=[
                alt.Tooltip("theoretical:Q", title="Theoretical", format=".2%"),
                alt.Tooltip("sample:Q", title="Observed", format=".2%"),
            ]
        )
    )
    qq_reference_line = (
        alt.Chart(qq_reference_data)
        .mark_line(color="#0b0b0b", strokeWidth=1.5, strokeDash=[4, 3])
        .encode(x="theoretical:Q", y="sample:Q")
    )
    st.altair_chart((qq_scatter + qq_reference_line).configure_view(strokeWidth=0), use_container_width=True)
    st.caption("Note: points on the dashed line indicate agreement with the fitted normal distribution; deviations in the tails indicate non-normality.")

    # box-and-whisker plot of the selected ticker's daily log returns
    box_data = pd.DataFrame({"log_return": selected_returns})

    st.subheader(f"Daily Log Return Box Plot — {company_names[selected_ticker]}")
    box_plot = (
        alt.Chart(box_data)
        .mark_boxplot(color=BAR_COLOR, size=50, outliers={"color": BAR_COLOR})
        .encode(
            x=alt.X("log_return:Q", title=None, axis=alt.Axis(
                format="%", gridColor="#e1e0d9", domainColor="#c3c2b7",
                tickColor="#c3c2b7", labelColor="#52514e", titleColor="#0b0b0b"))
        )
        .properties(height=200)
        .configure_view(strokeWidth=0)
    )
    st.altair_chart(box_plot, use_container_width=True)

    # create daily log return summary statistics table
    st.subheader("Daily Log Return Summary Statistics")
    summary_stats = pd.DataFrame({
        "Mean": filtered_log_returns.mean(),
        "Standard Deviation": filtered_log_returns.std(),
        "Skewness": filtered_log_returns.skew(),
        "Excess Kurtosis": filtered_log_returns.kurtosis(),
        "Minimum": filtered_log_returns.min(),
        "Maximum": filtered_log_returns.max()
    })
    st.dataframe(
        summary_stats.style.format({
            "Mean": "{:.2%}",
            "Standard Deviation": "{:.2%}",
            "Skewness": "{:.2f}",
            "Excess Kurtosis": "{:.2f}",
            "Minimum": "{:.2%}",
            "Maximum": "{:.2%}"
        }),
        column_config={
            "_index": st.column_config.Column(width=200),
            **{col: st.column_config.Column(width=100) for col in summary_stats.columns}
        }
    )
    st.caption("Note: excess kurtosis of zero implies that the underlying data follows a normal distribution. Positive excess kurtosis (i.e., leptokurtic) suggests that the data's distribution has more outliers. Negative excess kurtosis (i.e., platykurtic) suggests that the data's distribution produces fewer outliers." )

    # collapse a pair of bounds into a single "lower to upper" range string
    def pct_range(lower: pd.Series, upper: pd.Series) -> pd.Series:
        return lower.map(lambda x: f"{x:.2%}") + " to " + upper.map(lambda x: f"{x:.2%}")

    # convert the parametric variance bounds to standard deviation so both
    # methods' intervals are directly comparable in the same units
    parametric_sigma_lower = np.sqrt(CI_parametric.loc[tickers, 'var_lower'])
    parametric_sigma_upper = np.sqrt(CI_parametric.loc[tickers, 'var_upper'])

    # create parametric vs. bootstrap confidence interval comparison table for mu
    st.subheader("Confidence Intervals: Mean")
    mu_comparison = pd.DataFrame({
        'Parametric': pct_range(CI_parametric.loc[tickers, 'mu_lower'], CI_parametric.loc[tickers, 'mu_upper']),
        'Bootstrap': pct_range(CI_bootstrap.loc[tickers, 'mu_lower'], CI_bootstrap.loc[tickers, 'mu_upper']),
        'Block Bootstrap': pct_range(CI_block_bootstrap.loc[tickers, 'mu_lower'], CI_block_bootstrap.loc[tickers, 'mu_upper']),
    })
    st.dataframe(mu_comparison)

    # create parametric vs. bootstrap confidence interval comparison table for sigma
    st.subheader("Confidence Intervals: Standard Deviation")
    sigma_comparison = pd.DataFrame({
        'Parametric': pct_range(parametric_sigma_lower, parametric_sigma_upper), # type: ignore
        'Bootstrap': pct_range(CI_bootstrap.loc[tickers, 'sigma_lower'], CI_bootstrap.loc[tickers, 'sigma_upper']),
        'Block Bootstrap': pct_range(CI_block_bootstrap.loc[tickers, 'sigma_lower'], CI_block_bootstrap.loc[tickers, 'sigma_upper']),
    })
    st.dataframe(sigma_comparison)

#################################################################################################################################
def main():
    # define variables to be used
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    period_start = "2021-08-03"
    period_end = "2026-08-03"
    interval = "1d"
    output_path = '/Users/thomascostin/Library/CloudStorage/OneDrive-Personal/00 Career Development/03 Interview Prep/01 Quantitative Research/03 Project/Equity_Return_Distributions/price_data/closing_prices.csv'
    alpha = 0.05 # significance for confidence interval
    n_boot = 10000 # number of resamples
    random_state = 1 # seed to be used with bootstrap to enable replication

    # generate daily closing price data and cache local csv file
    get_data(tickers, period_start, period_end, interval, output_path)

    # convert cached closing price data from csv to pandas DataFrame
    closing_price_data = pd.read_csv(output_path, index_col=0, parse_dates=True)

    # compute Normal distribution parameters for each ticker using MLE
    mle_params = MLE_fit(closing_price_data)

    # generate parametric CI for the mean and variance of each ticker
    CI_parametric = parametric_CI(mle_params, alpha)

    # compute bootstrap CI for the mean and standard deviation of each ticker
    CI_bootstrap = bootstrap_CI(closing_price_data, n_boot, alpha, random_state)

    # compute block bootstrap CI for the mean and standard deviation of each ticker
    CI_block_bootstrap = block_bootstrap_CI(closing_price_data, n_boot, alpha, random_state)

    # feed data into data visualization function
    visualize_data(output_path, mle_params, CI_parametric, CI_bootstrap, CI_block_bootstrap)

#################################################################################################################################
if __name__ == "__main__":
    if st.runtime.exists(): # type: ignore
        main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
