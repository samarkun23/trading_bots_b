import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime,timedelta
import warnings
warnings.filterwarnings('ignore')

PAIR_1 = 'AAPL' 
PAIR_2 = 'MSFT' 


# trading parameters
LOOKBACK_PERIOD = 60  # Days for calculating mean and std
Z_SCORE_ENTRY = 2.0   # Entry threshold (z-score > 2 or < -2)
Z_SCORE_EXIT = 0.5    # Exit threshold (z-score < 0.5)

def fetch_pair_data(pair1, pair2, period='6mo'):
    """
    Fetch historical data for both stocks using yf.Ticker()
    """
    print(f"📥 Fetching data for {pair1} and {pair2}...")
    
    stock1 = yf.Ticker(pair1).history(period=period)
    stock2 = yf.Ticker(pair2).history(period=period)
    
    if stock1.empty or stock2.empty:
        print(f" Error: No data fetched for one or both stocks!")
        print(f"   Stock1 rows: {len(stock1)}, Stock2 rows: {len(stock2)}")
        raise ValueError("Could not fetch data. Check stock symbols.")
    
    close1 = stock1['Close'].squeeze()  # .squeeze() ensures it's a Series
    close2 = stock2['Close'].squeeze()
    
    # Check data types
    print(f"   Stock1 data points: {len(close1)}")
    print(f"   Stock2 data points: {len(close2)}")
    
    df = pd.DataFrame({
        'Stock1': close1,
        'Stock2': close2
    }).dropna()
    
    if df.empty:
        raise ValueError("No overlapping dates found between the two stocks!")
    
    print(f" Data fetched: {len(df)} trading days")
    return df

def calculate_spread_and_zscore(df, lookback=60):
    print("📊 Calculating spread and z-score...")
    
    # Method 1: Price Ratio (Stock1 / Stock2)
    df['Price_Ratio'] = df['Stock1'] / df['Stock2']
    
    # Method 2: Spread (for hedging)
    # You can also use: df['Spread'] = df['Stock1'] - (hedge_ratio * df['Stock2'])
    
    # Calculate Z-Score of the ratio
    # Z-score = (Current Value - Mean) / Standard Deviation # i don't remember this so i wrote it
    rolling_mean = df['Price_Ratio'].rolling(window=lookback).mean()
    rolling_std = df['Price_Ratio'].rolling(window=lookback).std()
    
    df['Rolling_Mean'] = rolling_mean
    df['Rolling_Std'] = rolling_std
    df['Z_Score'] = (df['Price_Ratio'] - rolling_mean) / rolling_std
    
    return df

# Generate signal based on z score
def generate_signals(df, entry_threshold=2.0, exit_threshold=0.5):
    print("🎯 Generating trading signals...")
    
    df['Signal'] = 0  # 0 = No position
    df['Position'] = 0  # Track current position
    
    # When z-score > entry_threshold: 
    # Stock1 is expensive relative to Stock2
    # SHORT Stock1, LONG Stock2
    df.loc[df['Z_Score'] > entry_threshold, 'Signal'] = -1  # Short ratio
    
    # When z-score < -entry_threshold:
    # Stock1 is cheap relative to Stock2
    # LONG Stock1, SHORT Stock2
    df.loc[df['Z_Score'] < -entry_threshold, 'Signal'] = 1  # Long ratio
    
    # Exit when z-score reverts to mean (near 0)
    df.loc[abs(df['Z_Score']) < exit_threshold, 'Signal'] = 0  # Exit
    
    # Fill forward the position (hold until exit signal)
    df['Position'] = df['Signal'].replace(0, np.nan).ffill().fillna(0)
    
    # Count signals
    long_signals = (df['Signal'] == 1).sum()
    short_signals = (df['Signal'] == -1).sum()
    
    print(f"📈 Long Signals (Buy Stock1, Sell Stock2): {long_signals}")
    print(f"📉 Short Signals (Sell Stock1, Buy Stock2): {short_signals}")
    
    return df

#  plot the pairs trading
def plot_pairs_trading(df, pair1_name, pair2_name):
    print("📈 Creating visualization...")
    
    fig, axes = plt.subplots(3, 1, figsize=(14, 10))
    
    axes[0].plot(df.index, df['Stock1'], label=pair1_name, linewidth=2)
    axes[0].plot(df.index, df['Stock2'], label=pair2_name, linewidth=2)
    axes[0].set_title(f'{pair1_name} vs {pair2_name} - Price Movement')
    axes[0].set_ylabel('Price (₹)')
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    
    ax2 = axes[1]
    ax2.plot(df.index, df['Price_Ratio'], label='Price Ratio', color='blue', linewidth=2)
    ax2.plot(df.index, df['Rolling_Mean'], label='Rolling Mean', color='orange', linestyle='--')
    ax2.fill_between(df.index, 
                     df['Rolling_Mean'] + 2*df['Rolling_Std'], 
                     df['Rolling_Mean'] - 2*df['Rolling_Std'], 
                     alpha=0.3, color='gray', label='±2 Std Dev')
    ax2.set_title('Price Ratio with Bollinger Bands')
    ax2.set_ylabel('Ratio')
    ax2.legend()
    ax2.grid(True, alpha=0.3)
    
    ax3 = axes[2]
    ax3.plot(df.index, df['Z_Score'], label='Z-Score', color='purple', linewidth=2)
    ax3.axhline(y=2.0, color='r', linestyle='--', alpha=0.7, label='Entry (+2)')
    ax3.axhline(y=-2.0, color='r', linestyle='--', alpha=0.7, label='Entry (-2)')
    ax3.axhline(y=0.5, color='g', linestyle=':', alpha=0.7, label='Exit (±0.5)')
    ax3.axhline(y=-0.5, color='g', linestyle=':', alpha=0.7)
    ax3.fill_between(df.index, 2, -2, alpha=0.1, color='green')
    
    long_signals = df[df['Signal'] == 1]
    short_signals = df[df['Signal'] == -1]
    ax3.scatter(long_signals.index, long_signals['Z_Score'], 
                color='green', marker='^', s=100, label='LONG Signal', zorder=5)
    ax3.scatter(short_signals.index, short_signals['Z_Score'], 
                color='red', marker='v', s=100, label='SHORT Signal', zorder=5)
    
    ax3.set_title('Z-Score with Trading Signals')
    ax3.set_ylabel('Z-Score')
    ax3.set_xlabel('Date')
    ax3.legend(loc='upper right')
    ax3.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('pairs_trading_chart.png', dpi=300, bbox_inches='tight')
    print("✅ Chart saved as 'pairs_trading_chart.png'")
    plt.show()

def calculate_performance(df):
    print("\n📊 Strategy Performance Analysis:")
    print("=" * 50)
    
    # Calculate returns
    df['Stock1_Return'] = df['Stock1'].pct_change()
    df['Stock2_Return'] = df['Stock2'].pct_change()
    
    # Pairs trading return (market neutral)
    # When position = 1: Long Stock1, Short Stock2
    # When position = -1: Short Stock1, Long Stock2
    df['Strategy_Return'] = df['Position'] * (df['Stock1_Return'] - df['Stock2_Return'])
    
    # Remove NaN values
    df_clean = df.dropna()
    
    if len(df_clean) == 0:
        print(" No valid trades found!")
        return
    
    total_return = (1 + df_clean['Strategy_Return']).prod() - 1
    sharpe_ratio = np.sqrt(252) * df_clean['Strategy_Return'].mean() / df_clean['Strategy_Return'].std()
    
    print(f"Total Return: {total_return:.2%}")
    print(f"Sharpe Ratio: {sharpe_ratio:.2f}")
    print(f"Number of Trading Days: {len(df_clean)}")
    print(f"Max Drawdown: {df_clean['Strategy_Return'].min():.2%}")
    print("=" * 50)

def run_pairs_trading_bot():
    print("=" * 60)
    print("PAIRS TRADING BOT (Statistical Arbitrage)")
    print("=" * 60)
    print(f"Pair: {PAIR_1} vs {PAIR_2}")
    print(f"Lookback Period: {LOOKBACK_PERIOD} days")
    print(f"Entry Z-Score: ±{Z_SCORE_ENTRY}")
    print(f"Exit Z-Score: ±{Z_SCORE_EXIT}")
    print("=" * 60)
    
    df = fetch_pair_data(PAIR_1, PAIR_2, period='6mo')
    
    correlation = df['Stock1'].corr(df['Stock2'])
    print(f"\n📈 Correlation Coefficient: {correlation:.3f}")
    
    if correlation < 0.7:
        print("️  Warning: Correlation is below 0.7. Pairs may not be suitable for stat arb!")
    else:
        print(" Good! Stocks are highly correlated.")
    
    df = calculate_spread_and_zscore(df, lookback=LOOKBACK_PERIOD)
    
    df = generate_signals(df, entry_threshold=Z_SCORE_ENTRY, exit_threshold=Z_SCORE_EXIT)
    
    print("\n" + "=" * 60)
    print(" CURRENT STATUS (Latest Data Point):")
    print("=" * 60)
    latest = df.iloc[-1]
    print(f"Date: {latest.name.strftime('%Y-%m-%d')}")
    print(f"{PAIR_1} Price: ₹{latest['Stock1']:.2f}")
    print(f"{PAIR_2} Price: ₹{latest['Stock2']:.2f}")
    print(f"Price Ratio: {latest['Price_Ratio']:.4f}")
    print(f"Z-Score: {latest['Z_Score']:.2f}")
    
    if latest['Z_Score'] > Z_SCORE_ENTRY:
        print(f"\n🔴 SIGNAL: SHORT {PAIR_1} / LONG {PAIR_2}")
        print("   Reason: Ratio is too high (Stock1 overvalued)")
    elif latest['Z_Score'] < -Z_SCORE_ENTRY:
        print(f"\n🟢 SIGNAL: LONG {PAIR_1} / SHORT {PAIR_2}")
        print("   Reason: Ratio is too low (Stock1 undervalued)")
    else:
        print(f"\n⚪ SIGNAL: NO POSITION (Wait for opportunity)")
    
    print("=" * 60)
    
    calculate_performance(df)
    
    plot_pairs_trading(df, PAIR_1, PAIR_2)
    
    print("\n Pairs Trading Bot completed successfully!")

if __name__ == "__main__":
    run_pairs_trading_bot()
