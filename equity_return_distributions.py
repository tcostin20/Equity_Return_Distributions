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

###########################################################
def get_data(ticker:list) -> pd.DataFrame:
    '''
    Function that returns equity return data for each ticker the
    user provides. The data is returned as a DataFrame.
    
    Parameters
    ----------
    ticker (list): A list of ticker symbols for which to retrieve equity return data.
    
    Returns
    ----------
    data (DataFrame): A DataFrame containing equity return distributions.
    '''
    pass

###########################################################
def main():
    # Example usage
    tickers = ['AAPL', 'MSFT', 'GOOGL']
    data = get_data(tickers)
    print(data)
