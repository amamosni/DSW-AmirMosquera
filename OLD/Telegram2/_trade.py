# Author: Yogesh K for finxter.com
# python script: trading with Bollinger bands for Binance
from binance.client import Client
from binance.enums import HistoricalKlinesType
from _config import config
from _logger import logger
import pandas as pd     # needs pip install
import numpy as np
import matplotlib.pyplot as plt   # needs pip install
import pytz
import random

client = Client(config["BINANCE_API_KEY"], config["BINANCE_API_SECRET_KEY"], testnet=False)
#pares = config["BINANCE_TRACE_SYMBOL"]
pares = ["BELUSDT", "ATAUSDT", "SANDUSDT"]
interval = config["BINANCE_TRACE_INTERVAL"]

#def get_symbol():
#    for par in pares:
#        print(par)
#        global symbol
#        symbol = par
#    return symbol


def get_symbol():
    global symbol
    symbol = random.choice(pares)
    print(symbol)
    return symbol

def get_data_frame():
    symbol = get_symbol()
    # valid intervals - 1m, 3m, 5m, 15m, 30m, 1h, 2h, 4h, 6h, 8h, 12h, 1d, 3d, 1w, 1M
    # request historical candle (or klines) data using timestamp from above, interval either every min, hr, day or month
    # starttime = '30 minutes ago UTC' for last 30 mins time
    # e.g. client.get_historical_klines(symbol='ETHUSDT', '1m', starttime)
    # starttime = '1 Dec, 2017', '1 Jan, 2018'  for last month of 2017
    # e.g. client.get_historical_klines(symbol='BTCUSDT', '1h', "1 Dec, 2017", "1 Jan, 2018")

    starttime = '1 day ago UTC'  # to start for 1 day ago
    bars = client.get_historical_klines(symbol, interval, starttime, klines_type=HistoricalKlinesType.FUTURES)

    for line in bars:        # Keep only first 5 columns, "date" "open" "high" "low" "close"
        del line[5:]
    df = pd.DataFrame(bars, columns=['date', 'open', 'high', 'low', 'close']) #  2 dimensional tabular data

    return df

def plot_graph(df : pd.DataFrame):
    df=df.astype(float)
    df[['close', 'sma','upper', 'lower']].plot()
    plt.xlabel('Fecha',fontsize=18)
    plt.ylabel('Cierre/Precio actual',fontsize=18)
    x_axis = df.index
    plt.fill_between(x_axis, df['lower'], df['upper'], color='grey',alpha=0.30)
    plt.scatter(df.index,df['buy'], color='purple',label='Buy',  marker='^', alpha = 1) # purple = buy
    plt.scatter(df.index,df['sell'], color='red',label='Sell',  marker='v', alpha = 1)  # red = sell

    # plt.show()
    plt.savefig('output.jpg')
    plt.close()

def buy_or_sell(df):
    current_price = float(client.futures_symbol_ticker(symbol =symbol)['price'])
    current_upper = pd.to_numeric(df.iloc[-1:]['upper'], downcast='float')[0]
    current_lower = pd.to_numeric(df.iloc[-1:]['lower'], downcast='float')[0]
    upper_lower_delta = current_upper - current_lower
    current_price_delta = current_price - current_lower
    current_price_percentage = current_price_delta / upper_lower_delta * 100.0
    percentage_current_upper = ((current_price - current_upper) / current_upper) * 100
    percentage_current_lower = ((current_lower - current_price) / current_upper) * 100

    logger.info(f"Precio actual de {symbol}: {current_price}, {config['BINANCE_TRACE_INTERVAL']} BBSup: {current_upper:.4f} BBInf: {current_lower:.4f} DBBSup {percentage_current_upper:.2f}% DBBInf {percentage_current_lower:.2f}%") #=> {current_price_percentage:.2f}%
    return (current_price, current_upper, current_lower, current_price_percentage, percentage_current_upper, percentage_current_lower, symbol)

def bollinger_trade_logic():
    symbol_df = get_data_frame()
    period = 20
    # small time Moving average. calculate 20 moving average using Pandas over close price
    symbol_df['sma'] = symbol_df['close'].rolling(period).mean()
    # Get standard deviation
    symbol_df['std'] = symbol_df['close'].rolling(period).std()
    # Calculate Upper Bollinger band
    symbol_df['upper'] = symbol_df['sma']  + (2 * symbol_df['std'])
    # Calculate Lower Bollinger band
    symbol_df['lower'] = symbol_df['sma']  - (2 * symbol_df['std'])
    # To print in human readable date and time (from timestamp)
    symbol_df.set_index('date', inplace=True)
    symbol_df.index = pd.to_datetime(symbol_df.index, unit='ms') # index set to first column = date_and_time

    New_York = pytz.timezone('America/New_York')
    symbol_df.index = symbol_df.index.tz_localize(pytz.utc).tz_convert(New_York)

    # prepare buy and sell signals. The lists prepared are still panda dataframes with float nos
    close_list = pd.to_numeric(symbol_df['close'], downcast='float')
    upper_list = pd.to_numeric(symbol_df['upper'], downcast='float')
    lower_list = pd.to_numeric(symbol_df['lower'], downcast='float')
    symbol_df['buy'] = np.where(close_list < lower_list,   symbol_df['close'], np.NaN )
    symbol_df['sell'] = np.where(close_list > upper_list,   symbol_df['close'], np.NaN )
    # with open('output.txt', 'w') as f:
    #     f.write(symbol_df.to_string())

    plot_graph(symbol_df)

    (current_price, current_upper, current_lower, current_price_percentage, percentage_current_upper, percentage_current_lower, symbol) = buy_or_sell(symbol_df)
    return (current_price, current_upper, current_lower, current_price_percentage, percentage_current_upper, percentage_current_lower, symbol)

if __name__ == "__main__":
    logger.warn("Use python main.py instead, Start collecting with default setting")
    bollinger_trade_logic()
       # Change symbol here e.g. BTCUSDT, BNBBTC, ETHUSDT, NEOBTC