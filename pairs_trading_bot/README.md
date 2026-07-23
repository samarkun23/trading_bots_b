
# Pairs Trading Bot

# Pairs Trading Bot (Statistical Arbitrage)

An advanced quantitative trading bot that exploits price deviations between two correlated stocks.

## Features
- ✅ Statistical arbitrage strategy
- ✅ Z-score based entry/exit signals
- ✅ Market-neutral strategy (long-short)
- ✅ Correlation analysis
- ✅ Performance metrics (Sharpe Ratio, Returns)
- ✅ Professional visualization
- ✅ Support for Indian & US markets

## 📚 How It Works
1. **Correlation Check**: Finds highly correlated pairs (e.g., TCS-INFY, AAPL-MSFT)
2. **Price Ratio**: Calculates ratio between two stocks
3. **Z-Score**: Measures how far ratio deviates from mean
4. **Entry**: When Z-Score > 2.0 (overvalued) or < -2.0 (undervalued)
5. **Exit**: When Z-Score reverts to < 0.5

# Configuration
- PAIR_1 = 'TCS.NS'         # First stock
- PAIR_2 = 'INFY.NS'        # Second stock (correlated)
-  LOOKBACK_PERIOD = 60      # Days for mean calculation
- Z_SCORE_ENTRY = 2.0       # Entry threshold
- Z_SCORE_EXIT = 0.5        # Exit threshold
 
## ️ Installation
```bash
pip install yfinance pandas numpy matplotlib statsmodels