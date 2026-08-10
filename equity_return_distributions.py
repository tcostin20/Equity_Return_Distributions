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
def visualize_data(output_path: str, MLE_params:pd.DataFrame, CI_parametric: pd.DataFrame, CI_bootstrap: pd.DataFrame) -> None:
    '''
    Function that visualizes the equity return data for each ticker.

    Parameters
    ----------
    output_path (str):          The path to the csv file containing the equity return data.
    MLE_params (pd.DataFrame):  MLE-fit Normal parameters for each ticker, as produced by MLE_fit.
    CI_parametric (pd.DataFrame): Parametric confidence intervals for each ticker, as produced by parametric_CI.
    CI_bootstrap (pd.DataFrame):  Bootstrap confidence intervals for each ticker, as produced by bootstrap_CI.

    Returns
    ----------
    None
    '''
    # fixed categorical palette (blue, orange, aqua) - validated for colorblind-safety
    # and contrast via the dataviz skill's validator; assigned in this order so ticker
    # identity/color stays stable regardless of which tickers are selected
    CHART_PALETTE = ['#2a78d6', '#eb6834', '#1baf7a', '#eda100', '#e87ba4', '#008300', '#4a3aa7', '#e34948']

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

    # Resample to monthly frequency, taking the mean value of each month (for the price chart only)
    monthly_data = raw_data.resample('ME').mean().round(2)

    st.title("Equity Return Distributions")
    st.caption("MLE-fit Normal parameters and confidence intervals for daily log returns.")

    # define columns that will be used to position graph and ticker selection box
    col1, col2 = st.columns([4, 1])

    # create a dropdown menu for the user to select tickers of interest
    with col2:
        tickers = st.multiselect("Ticker(s):", raw_data.columns, default=list(raw_data.columns))

    if not tickers:
        st.warning("Select at least one ticker to see the analysis.")
        return

    # filter data based on user selection
    filtered_monthly = monthly_data[tickers]
    mle_params = MLE_params.loc[tickers]

    # fixed color scale keyed to the full ticker universe (not just the current
    # selection), so a ticker's color never changes when the selection changes
    company_names = {t: get_company_name(t) for t in raw_data.columns}
    color_scale = alt.Scale(domain=list(company_names.values()), range=CHART_PALETTE[:len(company_names)])

    with col1:
        # create line graph
        chart_data = filtered_monthly.rename(columns=company_names)
        date_col = chart_data.index.name or "Date"
        long_data = chart_data.reset_index().melt(
            id_vars=[date_col], var_name="Company", value_name="Price"
        )
        chart = (
            alt.Chart(long_data)
            .mark_line(strokeWidth=2, point=alt.OverlayMarkDef(size=50, filled=True))
            .encode(
                x=alt.X(f"{date_col}:T", title="Date", axis=alt.Axis(
                    format="%b-%y", gridColor="#e1e0d9", domainColor="#c3c2b7",
                    tickColor="#c3c2b7", labelColor="#52514e", titleColor="#0b0b0b")),
                y=alt.Y("Price:Q", title="Avg. Closing Price ($)", axis=alt.Axis(
                    gridColor="#e1e0d9", domainColor="#c3c2b7",
                    tickColor="#c3c2b7", labelColor="#52514e", titleColor="#0b0b0b")),
                color=alt.Color("Company:N", scale=color_scale, legend=alt.Legend(
                    title="Company", labelColor="#52514e", titleColor="#0b0b0b")),
                tooltip=[
                    alt.Tooltip(f"{date_col}:T", title="Date", format="%b %Y"),
                    alt.Tooltip("Company:N", title="Company"),
                    alt.Tooltip("Price:Q", title="Price ($)", format=".2f"),
                ]
            )
            .properties(background="#fcfcfb")
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(chart, use_container_width=True)

        # create monthly closing price summary statistics table
        st.subheader("Monthly Price Summary Statistics")
        summary_stats = pd.DataFrame({
            "Mean": filtered_monthly.mean(),
            "Standard Deviation": filtered_monthly.std(),
            "Skewness": filtered_monthly.skew(),
            "Kurtosis": filtered_monthly.kurtosis()
        })
        st.dataframe(
            summary_stats.style.format("{:.2f}"),
            column_config={
                "_index": st.column_config.Column(width=200),
                **{col: st.column_config.Column(width=100) for col in summary_stats.columns}
            }
        )

        # create parametric vs. bootstrap confidence interval comparison table
        st.subheader("Confidence Intervals: Parametric vs. Bootstrap")
        st.caption("Confidence interval comparison for the daily log-return mean (μ) and standard deviation (σ).")

        # convert the parametric variance bounds to standard deviation so both
        # methods' intervals are directly comparable in the same units
        ci_parametric_sigma = pd.DataFrame({
            'μ Lower': CI_parametric.loc[tickers, 'mu_lower'],
            'μ Upper': CI_parametric.loc[tickers, 'mu_upper'],
            'σ Lower': np.sqrt(CI_parametric.loc[tickers, 'var_lower']),
            'σ Upper': np.sqrt(CI_parametric.loc[tickers, 'var_upper']),
        })
        ci_bootstrap_renamed = CI_bootstrap.loc[tickers].rename(columns={
            'mu_lower': 'μ Lower', 'mu_upper': 'μ Upper',
            'sigma_lower': 'σ Lower', 'sigma_upper': 'σ Upper',
        })

        # combine both methods into one DataFrame with grouped column headers
        ci_comparison = pd.concat({'Parametric': ci_parametric_sigma, 'Bootstrap': ci_bootstrap_renamed}, axis=1)
        st.dataframe(ci_comparison.style.format("{:.4%}"))

#################################################################################################################################
def MLE_fit(data: pd.DataFrame) -> pd.DataFrame:
    '''
    Function that computes the MLE-fit Normal distribution parameters (mu, sigma)
    for each ticker's log return series.

    Parameters
    ----------
    data (pd.DataFrame): DataFrame of closing prices, with tickers as columns and
                         dates as the index.

    Returns
    ----------
    pd.DataFrame: DataFrame indexed by ticker with columns 'mu', 'sigma', and 'n'
                  holding the MLE-fit Normal parameters and sample size for each
                  ticker's log returns.
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
    Function that generates non-parametric bootstrap confidence intervals for the
    mean and standard deviation of each ticker's log return series.

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
        sample = log_returns[ticker].to_numpy() # isolate ticker data
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

    # feed data into data visualization function
    visualize_data(output_path, mle_params, CI_parametric, CI_bootstrap)

#################################################################################################################################
if __name__ == "__main__":
    if st.runtime.exists(): # type: ignore
        main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
