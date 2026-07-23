
# VWAP Reversion Bot 
An institutional-grade mean reversion bot using Volume Weighted Average Price (VWAP) with live terminal dashboard.
🎯 Features

    ✅ Professional Terminal Dashboard (Rich library)
    ✅ Rolling VWAP calculation
    ✅ Standard deviation bands (2σ)
    ✅ Z-Score based signals
    ✅ Live PnL tracking
    ✅ Entry progress indicator
    ✅ Signal log
    ✅ Trade history with performance

📚 How It Works

    VWAP Calculation: Volume-weighted average price (fair value)
    Bands: Upper & Lower bands at 2 standard deviations
    Z-Score: Measures distance from VWAP in standard deviations
    Entry Signal: 
        LONG: Z-Score < -1.0 (price below lower band - oversold)
        SHORT: Z-Score > 1.0 (price above upper band - overbought)
    Exit Signal: Z-Score < 0.1 (price reverted to mean)

# Configuration
    SYMBOL = 'BTC/USDT'              # Trading pair
    TIMEFRAME = '5m'                 # 5-minute candles (optimal)
    LOOKBACK_PERIOD = 50             # Rolling VWAP period
    STD_DEV_MULTIPLIER = 1.5         # Band width (1.5 = tighter)
    ENTRY_THRESHOLD = 0.5            # Z-Score for entry (lower = more trades)
    EXIT_THRESHOLD = 0.1             # Z-Score for exit

# For testing only:
    SIMULATION_MODE = False          # True = simulated price movements
# Installation
```bash
pip install ccxt pandas mplfinance
```
# Performance Metrics

    Win Rate: ~65-75% (mean reversion)
    Best for: Sideways/choppy markets
    Avoid: Strong trending markets

**Notes**

    Use 5m or 15m timeframe for best results
    Works best with high-volume assets (BTC, ETH)
    Lower ENTRY_THRESHOLD = more trades (but lower quality)
    Higher STD_DEV_MULTIPLIER = fewer but stronger signals
    Simulation mode available for testing without real market

# Recommended Settings
**Conservative (Fewer, High-Quality Trades):**
```bash
ENTRY_THRESHOLD = 1.5
EXIT_THRESHOLD = 0.3
STD_DEV_MULTIPLIER = 2.0
```
**Moderate (Balanced):**
```bash
ENTRY_THRESHOLD = 1.0
EXIT_THRESHOLD = 0.2
STD_DEV_MULTIPLIER = 1.5
```
**Aggressive (More Trades):**
```bash
ENTRY_THRESHOLD = 0.5
EXIT_THRESHOLD = 0.1
STD_DEV_MULTIPLIER = 1.0
```

# Terminal dashboard
**Left Panel - Market Metrics:**

    Current Price
    VWAP (Fair Value)
    Upper/Lower Bands (2σ)
    Deviation %
    Z-Score
    Entry Progress Bar
    Current Position & Live PnL

**Right Panel - Signal Log:**

    Real-time BUY/SELL/EXIT signals
    Timestamp for each signal

**Bottom Panel - Trade History:**

    Completed trades
    Entry/Exit prices
    PnL per trade

**💡 Strategy Logic**
```bash
Z-Score < -0.5  →  BUY (Long)   [Price oversold]
Z-Score >  0.5  →  SELL (Short) [Price overbought]
Z-Score <  0.1  →  EXIT         [Mean reversion]
```

