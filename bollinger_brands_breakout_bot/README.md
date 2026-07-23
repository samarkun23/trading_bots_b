#  Bollinger Bands Breakout Bot

A beginner-friendly trading bot that generates buy/sell signals when price breaks through Bollinger Bands.

##  Features
- ✅ Visual chart generation with Bollinger Bands
- ✅ Real-time price monitoring
- ✅ Automatic signal generation (BUY/SELL/HOLD)
- ✅ Dark theme charts
- ✅ Binance Testnet support (mock trading)
- ✅ Easy to understand for beginners

## 📚 How It Works
- **BUY Signal**: When price crosses above Upper Band (strong momentum)
- **SELL Signal**: When price crosses below Lower Band (strong selling pressure)
- **HOLD**: When price is between bands (no clear breakout)

## Configuration
- symbol = 'BTC/USDT'      # Trading pair
- timeframe = '1d'          # Candle timeframe (1m, 5m, 1h, 1d)
- limit = 100               # Number of candles to analyze

## 🛠️ Installation
```bash
pip install ccxt pandas mplfinance


