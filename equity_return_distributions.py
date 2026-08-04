'''
------------------------------------------------------------------------------
Description: Analysis of equity return distributions for various asset classes
Author: Thomas Costin (tcostin20@gmail.com)
Date started: 8/3/2026
Data source: TBU
------------------------------------------------------------------------------
'''

import yfinance as yf
import pandas as pd
from pathlib import Path

###########################################################
def get_data(tickers:list,period_start:str,period_end:str,interval:str) -> None:
    '''
    Function that creates a csv file containing equity 
    return data for each ticker the user provides.
    
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
    # define where to save the CSV file
    output_path = '/Users/thomascostin/Library/CloudStorage/OneDrive-Personal/00 Career Development/03 Interview Prep/01 Quantitative Research/03 Project/Equity_Return_Distributions/price_data/closing_prices.csv'

    # check to see whether a csv file already exists at the output path
    if Path(output_path).exists():
        overwrite = input(f"File already exists at, overwrite? [y/n]: ")
        if overwrite != "y":
            return

    # download the closing price data for the specified tickers and time period
    closing_price_data = yf.download(tickers, start=period_start, end=period_end, interval=interval, auto_adjust=True)['Close'] # type: ignore

    # save data set to the output path defined above
    closing_price_data.to_csv(output_path, index=True, float_format='%.2f')

###########################################################
def main():
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    data = get_data(tickers, period_start="2021-08-03", period_end="2026-08-03", interval="1d")

if __name__ == "__main__":
    main()
