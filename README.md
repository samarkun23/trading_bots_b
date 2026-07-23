
#  Algorithmic Trading Bots Collection

A collection of professional trading bots for cryptocurrency and stock markets.

## 📂 Projects

### 1. **Bollinger Bands Breakout Bot** 📊
- **Level**: Beginner
- **Strategy**: Momentum breakout
- **Best For**: Trending markets
- [View Details](bollinger_brands_breakout_bot/README.md)

### 2. **Pairs Trading Bot (Stat Arb)** 📈
- **Level**: Advanced
- **Strategy**: Statistical arbitrage, market-neutral
- **Best For**: Correlated stock pairs
- [View Details](pairs_trading_bot/README.md)

### 3. **Grid Trading Bot** 🤖
- **Level**: Intermediate
- **Strategy**: Grid trading, range-bound
- **Best For**: Sideways markets
- **Features**: Beautiful terminal UI
- [View Details](grid_trading_bot/README.md)

### 4. **VWAP Reversion Bot** 📊
- **Level**: Advanced
- **Strategy**: Mean reversion, institutional
- **Best For**: High-volume assets
- **Features**: Professional dashboard
- [View Details](vwap_bot/README.md)

## Note 
- Add some csv and png that bot generate at the root folder that is basically a sample of the output.

## 🛠️ Installation

Each bot has its own dependencies. Install all at once:
```bash
pip install ccxt pandas numpy mplfinance yfinance rich statsmodels matplotlib
```
**RECOMMENDED**
- Requirement.txt present at the root folder insalls all dependencies at once or init a venv environment and then install it inside the venv.