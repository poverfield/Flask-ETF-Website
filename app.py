from myproject import app
from myproject import db
from myproject.models import ETF_Data
from flask import render_template
import yfinance as yf
import pandas as pd
import numpy as np
import csv

#define RSI function
def RSI(series,period):

    rsi = [] # create empty list to store RSI values in
    # get values from series (close data)
    delta = series.diff().dropna()
    u = delta * 0 #gains
    d = u.copy() # loses
    u[delta > 0] = delta[delta > 0]
    d[delta < 0] = -delta[delta < 0]

     # loop through gains/loses and create RSI line_values
    for i in range(period,len(series) -1):


        # get RSI for first period
        if i == period:

            avg_gain = np.mean( u[:period] )
            avg_loss = np.mean( d[:period] ) #first value is sum of avg losses
            rs = avg_gain/avg_loss
            rsi.append(100 - 100 / (1 + rs))

        elif i > period:

            #get previous avg gain for last 13 days (period-1)
            avg_gain = np.mean( u[(i-period):i] )
            avg_loss = np.mean( d[(i-period):i] ) #first value is sum of avg losses

            # get current gain
            current_gain = u[i]
            current_loss = u[i]

            rs = (avg_gain + current_gain)/(avg_loss + current_loss)
            rsi.append(100-100 /(1+rs))


    #create dataframe from list
    RSI = pd.DataFrame(rsi)
    return(RSI)



@app.route('/')
def index():

    '''
    #query data
    # get a list of ticker names from etf_list.csv
    f= open('static/etf_list.txt')
    contents = f.read()
    f.close()
    new_content = contents.replace('\n', '|')
    etf_list = new_content.split('|')
    '''

    etf_list = ['AAPL', 'AMZN', 'MSFT']
    #update each table
    for etf in etf_list:

        etf_name = etf
        tickerData = yf.Ticker(etf_name) # pull datea from yahoo finanace
        df = tickerData.history(period='1d', start='2020-1-1') # get historical prices since 2015

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
        rsi = RSI(df['Close'], 14) # standard RSI
        rsi_sma = rsi.rolling(window=20).mean()
        rsi_std = rsi.rolling(window=20).std() # rsi standard deviation
        rsi_upper = (rsi_sma + 2 * rsi_std).values.tolist()
        rsi_lower = (rsi_sma - 2 * rsi_std).values.tolist()
        rsi = rsi.values.tolist()


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
        date = str(date[-new_length:])
        open_price = str(open_price[-new_length:])
        high_price = str(high_price[-new_length:])
        low_price = str(low_price[-new_length:])
        close_price = str(close_price[-new_length:])
        volume = str(volume[-new_length:])
        bb_mean = str(bb_mean[-new_length:])
        bb_upper = str(bb_upper[-new_length:])
        bb_lower = str(bb_lower[-new_length:])
        rsi = str(rsi[-new_length:])
        rsi_upper = str(rsi_upper[-new_length:])
        rsi_lower = str(rsi_lower[-new_length:])


        # generate trade signals (for now a simple BB crossover)
        n = len(open_price)-1
        buy_signal = list()
        sell_signal = list()
        for i in range(1,n):

            if close_price[i-1] < bb_lower[i-1] and close_price[i] > bb_lower[i]: # if price crosses BB lower then generate buy signal
                buy_signal.append(i)

            elif close_price[i-1] > bb_upper[i-1] and close_price[i] < bb_upper[i]: # if price corsses BB upper than generate sell signal
                sell_signal.append(i)

        # set buy and sell signals to lists
        buy_signal = str(buy_signal)
        sell_signal = str(sell_signal)


        # Update SQL Database
        #update the current ticker values
        '''
        if ETF_Data.query.filter_by(etf_name=etf_name): # if this entry exists
            print('matched on ' + etf_name)

            etf = ETF_Data.query.filter_by(etf_name=etf_name) # grab the etf to edit
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
        '''

        #else: # if entry doesn't alredy exist create a new entry

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

    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)
