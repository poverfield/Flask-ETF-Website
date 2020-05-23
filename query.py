##query financial data from yahoo finance and upate the sql tables
from models import ETF_Data #import db to upgrade w/ each query
from models import db
import yfinance as yf
import pandas as pd
import numpy as np
import csv

# get a list of ticker names from etf_list.csv
f= open('etf_list.txt')
contents = f.read()
f.close()
new_content = contents.replace('\n', '|')
etf_list = new_content.split('|')



#define RSI function
def RSI(series, period):
     delta = series.diff().dropna()
     u = delta * 0
     d = u.copy()
     u[delta > 0] = delta[delta > 0]
     d[delta < 0] = -delta[delta < 0]
     u[u.index[period-1]] = np.mean( u[:period] ) #first value is sum of avg gains
     u = u.drop(u.index[:(period-1)])
     d[d.index[period-1]] = np.mean( d[:period] ) #first value is sum of avg losses
     d = d.drop(d.index[:(period-1)])
     rs = pd.stats.moments.ewma(u, com=period-1, adjust=False)
     pd.stats.moments.ewma(d, com=period-1, adjust=False)
     return 100 - 100 / (1 + rs)


# get list of all entries in datatable to

#update each table
for etf in etf_list:

    etf_name = etf
    tickerData = yf.Ticker(etf_name) # pull datea from yahoo finanace
    df = tickerData.history(period='1d', start='2015-1-1') # get historical prices since 2015

    # get lits of values
    date = df.index.to_list() # get list of dates from index column
    open_price = df['Open'].to_list() # list of open prices
    high_price = df['High'].to_list() # list of high prices
    low_price = df['Low'].to_list()
    close_price = df['Close'].to_list()
    volume = df['Volume'].to_list()

    # calculate Bollinger bands
    bb_mean = df['Close'].rolling(window=20).mean()
    rstd = df['Close'].rolling(window=20).std()
    bb_upper = (bb_mean + 2 * rstd).to_list()
    bb_lower = (bb_mean - 2 * rstd).to_list()


    #calculate the rsi
    rsi = RSI[df['Close'], 14] # standard RSI
    rsi_sma = rsi.rolling(window=20).mean()
    rsi_std = df['Close'].rolling(window=20).std() # rsi standard deviation
    rsi_upper = (rsi_sma + 2 * rsi_std).to_list()
    rsi_lower = (rsi_sma - 2 * rsi_std).to_list()
    rsi = rsi.to_list()


    # unify lengths for all data objects
    # get the shortest length
    new_length = min(len(date),
                    len(open_price),
                    len(high_price),
                    len(low_price),
                    len(close_price),
                    len(volume),
                    len(bb_mean),
                    len(bb_upper),
                    len(bb_lower),
                    len(rsi),
                    len(rsi_upper),
                    len(rsi_lower))

    # update all tables to equal new length
    date = date[-new_length:]
    open_price = open_price[-new_length:]
    high_price = high_price[-new_length:]
    low_price = low_price[-new_length:]
    close_price = close_price[-new_length:]
    volume = volume[-new_length:]
    bb_mean = bb_mean[-new_length:]
    bb_upper = bb_upper[-new_length:]
    bb_lower = bb_lower[-new_length:]
    rsi = rsi[-new_length:]
    rsi_upper = rsi_upper[-new_length:]
    rsi_lower = rsi_lower[-new_length:]


    # generate trade signals (for now a simple BB crossover)
    n = len(open_price)-1
    buy_signal = list()
    sell_signal = list()
    for i in range(1,n):

        if close_price[i-1] < bb_lower[i-1] and close_price[i] > bb_lower[i]: # if price crosses BB lower then generate buy signal
            buy_signal.append(i)

        elif close_price[i-1] > bb_upper[i-1] and close_price[i] < bb_upper[i]: # if price corsses BB upper than generate sell signal
            sell_signal.append(i)


    # Update SQL Database
    #update the current ticker values
    if ETF_Data.query.filter_by(name=etf_name): # if this entry exists

        etf = ETF_Data.query.filter_by(name=etf_name) # grab the etf to edit
        etf.date = date
        etf.open_price = open_price
        etf.high_price = high_price
        etf.low_price = low_price
        etf.close_price = close_price
        etf.volume = volume
        etf.bb_mean = bb_mean
        etf.bb_upper = bb_upper
        etf.bb_lower = bb_lower
        etf.rsi = rsi
        etf.rsi_upper = rsi_upper
        etf.rsi_lower = rsi_lower
        etf.buy_signal = buy_signal
        etf.sell_signal = sell_signal

        db.session.add(etf) # update value in table
        db.session.commit() #commit changes

    else: # if entry doesn't alredy exist create a new entry

        new_entry = ETF_Data(etf_name,
                            date,
                            open_price,
                            high_price,
                            low_price,
                            close_price,
                            volume,
                            bb_mean,
                            bb_upper,
                            bb_lower,
                            rsi,
                            rsi_upper,
                            rsi_lower,
                            buy_signal,
                            sell_signal)
        db.session.add(new_entry)
        db.session.commit()
