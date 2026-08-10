'''
------------------------------------------------------------------------------
Description: Analysis of equity return distributions for various asset classes
Author: Thomas Costin (tcostin20@gmail.com)
Date started: 8/3/2026
Data source: Yahoo Finance (https://finance.yahoo.com/)
------------------------------------------------------------------------------
'''

import yfinance as yf
import pandas as pd
import altair as alt
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
    ticker (list): A list of ticker symbols for which to retrieve equity return data.
    period_start (str): The start date for the data period.
    period_end (str): The end date for the data period.
    interval (str): The frequency of the data points.
    
    Returns
    ----------
    None
    '''
    # check to see whether a csv file already exists at the output path
    if Path(output_path).exists():
            existing_columns = pd.read_csv(output_path, index_col=0, nrows=0).columns
            if set(existing_columns) == set(tickers):
                return  # If the file exists and has the same columns, do nothing

    # download the closing price data for the specified tickers and time period
    closing_price_data = yf.download(tickers, start=period_start, end=period_end, interval=interval, auto_adjust=True)['Close'] # type: ignore

    # save data set to the output path
    closing_price_data.to_csv(output_path, index=True, float_format='%.2f')

#################################################################################################################################
def visualize_data(output_path: str) -> None:
    '''
    Function that visualizes the equity return data for each ticker.
    
    Parameters
    ----------
    output_path (str): The path to the csv file containing the equity return data.
    
    Returns
    ----------
    None
    '''
    # switch layout to widescreen mode
    st.set_page_config(layout="wide")

    # cache the data to avoid reloading it every time the app is run
    @st.cache_data
    def load_data(output_path: str) -> pd.DataFrame:
        return pd.read_csv(output_path, index_col=0, parse_dates=True)

    # define function to pull full company name from Yahoo Finance given a ticker symbol
    def get_company_name(ticker: str) -> str:
        return yf.Ticker(ticker).info['longName']  # type: ignore

    # pull raw data from CSV file
    raw_data = load_data(output_path)

    # Resample to monthly frequency, taking the mean value of each month
    monthly_data = raw_data.resample('ME').mean().round(2)

    # define columns that will be used to position graph and ticker selection box
    col1, col2= st.columns([4, 1])

    # create a dropdown menu for the user to select tickers of interest
    with col2:
        tickers = st.multiselect("Ticker(s):", raw_data.columns, default=list(raw_data.columns))

    # filter data based on user selection above
    filtered_data = monthly_data[tickers]

    # calculate summary statistics for each ticker
    mean = filtered_data.mean()
    std = filtered_data.std()
    skew = filtered_data.skew()
    kurt = filtered_data.kurtosis()

    with col1:
        # create title page
        st.title("Average Closing Price by Month")

        # create line graph
        chart_data = filtered_data.rename(columns={t: get_company_name(t) for t in tickers})
        date_col = chart_data.index.name or "Date"
        long_data = chart_data.reset_index().melt(
            id_vars=[date_col], var_name="Company", value_name="Price"
        )
        chart = (
            alt.Chart(long_data)
            .mark_line()
            .encode(
                x=alt.X(f"{date_col}:T", title="Date", axis=alt.Axis(format="%b-%y")),
                y=alt.Y("Price:Q", title="Avg. Closing Price ($)"),
                color="Company:N"
            )
        )
        st.altair_chart(chart, use_container_width=True)

        # create summary statistics table
        st.subheader("Summary Statistics")

        # create a DataFrame to hold the summary statistics
        summary_stats = pd.DataFrame({
            "Mean": mean,
            "Standard Deviation": std,
            "Skewness": skew,
            "Kurtosis": kurt
        })

        # display the summary statistics table with custom column widths
        st.dataframe(
            summary_stats.style.format("{:.2f}"),
            column_config={
                "_index": st.column_config.Column(width=200),
                **{col: st.column_config.Column(width=100) for col in summary_stats.columns}
            }
        )

#################################################################################################################################



#################################################################################################################################
def main():
    # define tickers
    tickers = ['AAPL', 'MSFT', 'GOOGL']

    # define output path
    output_path = '/Users/thomascostin/Library/CloudStorage/OneDrive-Personal/00 Career Development/03 Interview Prep/01 Quantitative Research/03 Project/Equity_Return_Distributions/price_data/closing_prices.csv'

    # get closing price data and save it to a csv file at the output path defined above
    get_data(tickers, period_start="2021-08-03", period_end="2026-08-03", interval="1d", output_path=output_path)

    # feed data into data visualization function
    #visualize_data(output_path)

#################################################################################################################################
if __name__ == "__main__":
    if st.runtime.exists(): # type: ignore
        main()
    else:
        sys.argv = ["streamlit", "run", sys.argv[0]]
        sys.exit(stcli.main())
