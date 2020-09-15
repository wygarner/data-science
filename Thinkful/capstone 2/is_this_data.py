

import pandas as pd
import numpy as np
import matplotlib as plt
import seaborn as sns

import urllib3
import certifi
import sqlite3

import statsmodels.api as sm
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Connect to Orderbook database and read orderbook
conn = sqlite3.connect('cb_books.db')


http = urllib3.PoolManager(cert_reqs = 'CERT_REQUIRED' , ca_certs = certifi.where())

books_df = pd.read_sql_query('SELECT * FROM better_books' , conn)

conn = sqlite3.connect('cb_trades.db')
trades_df = pd.read_sql_query('SELECT * FROM better_trades' , conn)

books_df['timestamp'] = pd.to_datetime(books_df['timestamp'])
books_df['timestamp'] = books_df['timestamp'].dt.tz_localize('US/Eastern')           

trades_df['time'] = pd.to_datetime(trades_df['time'])

conn = sqlite3.connect('one_time_now.db')
c = conn.cursor()

features_d_list = list()
for lag in [10,30,60,300,600]:
    for index,values in books_df.iterrows():
        features_d = dict()
        tfi= 0 
        lag_books = books_df.loc[books_df['time_ms']<values['time_ms']]
        lag_books = lag_books.loc[lag_books['time_ms']>values['time_ms']-lag]
        lag_books = lag_books.reset_index()
        lag_trades = trades_df.loc[trades_df['time'] > values['timestamp'] - np.timedelta64(lag,'s')]
        lag_trades = lag_trades.loc[lag_trades['time'] < values['timestamp']]
        lag_trades.reset_index()
        trade_counts = lag_trades['side'].value_counts()
        try:
            market_buys = trade_counts['buy']
            market_sells = trade_counts['sell']
            if len(lag_books)>0:
                average_OIR = lag_books['OIR'].mean()
                sum_OIR = lag_books['OIR'].sum()
                average_VOI = lag_books['VOI'].mean()
                sum_VOI = lag_books['VOI'].sum()
                average_spread = lag_books['SPREAD'].mean()
                midprice_change = values['MIDPRICE'] - lag_books.iloc[0]['MIDPRICE']
                tfi = market_buys / market_sells
                features_d['lag_TFI'] = tfi
                features_d['lag_'+str(lag)+'_average_OIR'] = average_OIR
                features_d['lag_'+str(lag)+'_average_VOI'] = average_VOI
                features_d['lag_'+str(lag)+'_sum_OIR'] = sum_OIR
                features_d['lag_'+str(lag)+'_sum_VOI'] = sum_VOI
                features_d['lag_'+str(lag)+'_average_spread'] = average_spread
                features_d['lag_'+str(lag)+'_midprice_change'] = midprice_change
                for i in [10,30,60,300,600]:
                    forecast_books = books_df.loc[books_df['time_ms'] <= values['time_ms'] + (i+1)]
                    forecast_books = forecast_books.loc[forecast_books['time_ms'] >= values['time_ms'] + (i-1)]
                    forecast_midprice = forecast_books['MIDPRICE'].mean()
                    features_d['forecast_'+str(i)+'_midprice_change'] = forecast_midprice - values['MIDPRICE']
                features_d['lag'] = lag
                
                print(features_d,'\n')
                c.execute("INSERT INTO come_correct VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",(tfi,average_OIR,average_VOI,sum_OIR,sum_VOI,average_spread,midprice_change,features_d['forecast_10_midprice_change'],features_d['forecast_30_midprice_change'],features_d['forecast_60_midprice_change'],features_d['forecast_300_midprice_change'],features_d['forecast_600_midprice_change'],lag))
                conn.commit()
        except(KeyError):
            print('No trades','\n')

            
            
            





