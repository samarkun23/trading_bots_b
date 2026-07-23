# 🤖 Grid Trading Bot

An automated trading bot with beautiful terminal UI that profits from sideways market movements using grid trading strategy.

## 🎯 Features
- ✅ **Beautiful Terminal UI** (Rich library)
- ✅ Real-time price chart (ASCII art)
- ✅ Volume bars visualization
- ✅ Grid levels display (Supply/Demand)
- ✅ Live trade history
- ✅ Automatic buy/sell order placement
- ✅ Profit tracking per grid
- ✅ Dark theme interface

## 📚 How It Works
1. **Grid Setup**: Divides price range into multiple levels
2. **Buy Orders**: Placed below current price
3. **Sell Orders**: Placed above current price
4. **Profit**: Each grid fill generates profit from price difference
5. **Cycle**: Continuously places opposite orders

# Configuration
- SYMBOL = 'BTC/USDT'           # Trading pair
- UPPER_PRICE = 66000           # Grid upper bound
- LOWER_PRICE = 65000           # Grid lower bound
- NUM_GRIDS = 10                # Number of grid levels
- TRADE_AMOUNT_USDT = 10        # Amount per trade
- TIMEFRAME = '1m'              # Candle timeframe

## 🛠️ Installation
pip install ccxt pandas rich

# Terminal UI Components
**Left Panel:**
        Live price chart (cyan dots)
        Volume bars (blue)
        Grid levels info

**Right Panel:**
        Supply/Demand grid levels
        Current price marker
        Open/filled orders
        Statistics (profit, trades)

**Bottom Panel:**
        Recent trades history
        Profit per trade

## Grid Calculation
```bash
Grid Spacing = (Upper Price - Lower Price) / Number of Grids
Example: (66000 - 65000) / 10 = $100 per grid

Profit per grid = Grid Spacing × (Trade Amount / Grid Level)
Example: 100 × (10 / 65000) = $0.015 per trade
```

# Notes
    Best for sideways/range-bound markets
    Not suitable for strong trending markets
    Lower grid spacing = more trades (but smaller profit)
    Higher grid spacing = fewer trades (but larger profit)
    Requires sufficient balance for multiple orders

# UI
- Auto-refresh every 5 seconds
- Color-coded orders (Green=BUY, Red=SELL)
- Real-time price tracking
- Professional dark theme