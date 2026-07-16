import pandas as pd
import ccxt
import mplfinance as mpf
from datetime import datetime as dt
import time

# If your run this without api then its only give signal but if you want it to trade on binance then you have to use api and uncommont the function below execute_trade function in the run bot function

exchnage = ccxt.binance({
    "apiKey": "your_api_key",
    "secret": "your_api_secret",
    'enableRateLimit': True, # respect rate limits,
    'options': {
        'defaultType': 'spot'
    } 
})

exchnage.set_sandbox_mode(True) 

# exchnage.urls['api'] = {
#     'public': 'https://testnet.binance.vision/api',
#     'private': 'https://testnet.binance.vision/api',
# }

# parameters setup
symbol = 'DOGE/USDT' # symbol of bitcoin and usdt
timeframe = '5m' # 1 hours candles 
limit = 100 # past 100 candels
trade_amount = 10 # amount to trade

# data fetching 
def fetch_market_data():
    try:
        print(f"Fetching {timeframe} data for {symbol} from Binance...")

        # Fetch the data from binance as OHLCV
        raw_data = exchnage.fetch_ohlcv(symbol, timeframe, limit=limit)

        # converting the raw data into a pandas dataframe
        df = pd.DataFrame(raw_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])

        # converting timestamps (milisec) into normal Date/Time format
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')

        # setting Timestamp as index for mplfinance
        df.set_index('Timestamp', inplace=True) 

        return df

    except Exception as e:
        print(f"Error fetching data from Binance: {e}")
        return None

# function to calculate the Bollinger Bands
def calculate_bollinger_bands(df, window=20, num_std=2):
    print("Calculating Bollinger Bands...")

    #middle brand : 20-period simple moving average (SMA)
    df['Middle_Band'] = df['Close'].rolling(window=window).mean()

    #standard deviation 
    rolling_std = df['Close'].rolling(window=window).std()

    #upper band and lower band
    df['Upper_Band'] = df['Middle_Band'] + num_std * rolling_std
    df['Lower_Band'] = df['Middle_Band'] - num_std * rolling_std

    return df

# chart visualization
def plot_chart(df):
    print("Plotting chart...")

    # tell the mpfinance that which line need to add on chat 
    add_plot = [
        mpf.make_addplot(df["Middle_Band"],color="blue",width=1.5,label='Middle'),
        mpf.make_addplot(df["Upper_Band"],color="green",width=1,label='Upper'),
        mpf.make_addplot(df["Lower_Band"],color="red",width=1,label='Lower')
    ]

    # ploting a chart 
    mpf.plot(
        df,
        type='candle',
        addplot=add_plot,
        title=f'\n{symbol} {timeframe} Charts with bollinger bands',
        ylabel='Price (USDT)',
        volume=True,
        style='nightclouds',
        figsize=(12,8),
        savefig='bollinger_chart.png' 
    )

def generate_signals(df):
    print("\n🧠 Analyzing latest market data for signals...")
    
    # Hum sirf latest (last) candle ko check karenge decision lene ke liye
    latest = df.iloc[-1]  # Last row
    previous = df.iloc[-2] # Usse pichli row (confirmation ke liye)
    
    current_close = latest['Close']
    current_upper = latest['Upper_Band']
    current_lower = latest['Lower_Band']
    
    print(f"📊 Current Price: {current_close:.2f}")
    print(f"⬆️ Upper Band: {current_upper:.2f}")
    print(f"⬇️ Lower Band: {current_lower:.2f}")
    print("-" * 40)
    
    # ✅ BUY LOGIC: Price ne Upper Band ko tod diya (Breakout)
    if current_close > current_upper:
        print("🚀🚀🚀 BUY SIGNAL GENERATED! 🚀🚀🚀")
        print("Reason: Price broke above the Upper Bollinger Band (Strong Momentum)")
        return "BUY"
        
    # ✅ SELL LOGIC: Price ne Lower Band ko tod diya (Breakdown)
    elif current_close < current_lower:
        print("🔻🔻🔻 SELL SIGNAL GENERATED! 🔻🔻🔻")
        print("Reason: Price broke below the Lower Bollinger Band (Strong Selling Pressure)")
        return "SELL"
        
    # ⏸️ HOLD LOGIC: Price bands ke beech mein hai (No Trade)
    else:
        print("⏸️ HOLD / NO SIGNAL")
        print("Reason: Price is consolidating between the bands. Wait for breakout.")
        return "HOLD"
    
def execute_trade(signal):
    try:
        balance = exchnage.fetch_balance()
        usdt_balance = balance['USDT']['free']
        btc_balance = balance['BTC']['free']
        
        print(f"\n Current balance: ")
        print(f" USDT: {usdt_balance:.2f}")
        print(f" BTC: {btc_balance:.8f}")
        
        if signal == "BUY" and usdt_balance >= trade_amount:
            print("\n Placing BUY order for {trade_amount} USDT worth of BTC")
            order = exchnage.create_market_buy_order(symbol, trade_amount/95000)
            print(f"Buy order placed. Order ID: {order['id']}")
            print(f" Status: {order['status']}")

        elif signal == "SELL" and btc_balance > 0:
            print("\n Placing the Sell order for all btc")
            order = exchnage.create_market_sell_order(symbol, btc_balance)
            print(f"Sell Order Placed Successfully!")
            print(f" Order ID: {order['id']}")
            print(f" Status: {order['status']}")
        else:
            print("\n⏸️ No order executed (Insufficient funds or no signal)")

    except Exception as e:
        print(f"Error executing trade: {e}")

def run_bot():
    print("="*60)
    print("🤖 Bollinger Bands Breakout Bot - LIVE MODE (Testnet)")
    print("="*60)
    print(f"📊 Trading Pair: {symbol}")
    print(f"⏱️ Timeframe: {timeframe}")
    print(f"💵 Trade Amount: {trade_amount} USDT per trade")
    print(f"\n🔄 Bot started! Checking market every 60 seconds...")
    print(f"   Press Ctrl+C to stop the bot\n")
    
    iteration = 1
    
    while True:
        try: 
            print(f"\n{'='*60}")
            print(f"🔍 Iteration #{iteration} - {dt.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"{'='*60}")
            
            # Step 1: Data fetch karo
            data = fetch_market_data()
            
            if data is not None:
                # Step 2: Bands calculate karo
                data_with_bands = calculate_bollinger_bands(data)
                
                # Step 3: Signal generate karo
                signal = generate_signals(data_with_bands)
                
                # Step 4: Current price aur bands dikhao
                latest = data_with_bands.iloc[-1]
                print(f"\n📊 Current Price: ${latest['Close']:.2f}")
                print(f"⬆️ Upper Band: ${latest['Upper_Band']:.2f}")
                print(f"⬇️ Lower Band: ${latest['Lower_Band']:.2f}")
                print(f"\n🎯 Signal: {signal}")
                
                # Step 5: Agar BUY/SELL signal hai, toh trade execute karo
                if signal in ["BUY", "SELL"]:
                    print(f"\n💥 BREAKOUT DETECTED! Executing trade...")
                    print(f"Signal: {signal}")
                    print(f"execute a trade")
                    # execute_trade(signal)
                else:
                    print(f"⏸️ No breakout. Waiting for next candle...")
            
            # Step 6: 60 seconds wait karo (1 minute candle ke liye)
            print(f"\n⏳ Waiting 60 seconds for next check...")
            time.sleep(60)

            iteration += 1
        except KeyboardInterrupt:
            print("\n\n🛑 Bot stopped by user. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error in main loop: {e}")
            print("⏳ Retrying in 60 seconds...")
            time.sleep(60)


# main execution
if __name__ == "__main__":
    run_bot() 