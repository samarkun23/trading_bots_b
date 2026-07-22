import ccxt
import pandas as pd
import mplfinance as mpf
import time
from datetime import datetime as dt
import json
import os

SYMBOL = 'BTC/USDT'
TIMEFRAME = '1m'
UPPER_PRICE = 120000
LOWER_PRICE = 110000
NUM_GRIDS = 10
TRADE_AMOUNT_TRADE = 10

API_KEY = '8am2lf6BY5YoGTeN160IMBWB5yCDpF0mAYJo2OtFN0C5LRQckKwAXHPz64Yx6qOt'
SECRET_KEY = 'lYrnkkeNUEaXP46AkiswBPYqWLFutPLOe8jF13wy7C6eHfBTFExvrMTYhXfL76bN'

def calculate_grid_levels(upper, lower, num_grids):
    print(f"Calculating {num_grids} grid levels...")
    print(f"Range: ${lower} - ${upper}")

    grid_spacing = (upper - lower) / num_grids

    grid_level = []
    for i in range(num_grids + 1):
        level = lower + (i * grid_spacing)
        grid_level.append(round(level,2))

    print(f" Grid spacing: ${grid_spacing:.2f}")
    print(f" Profit per grid: ${grid_spacing:.2f} per {TRADE_AMOUNT_TRADE} USDT trade")
    print(f"\n Grid Levels:")
    for i, level in enumerate(grid_level):
        bar = "BUY" if i < num_grids // 2 else "SELL" if i > num_grids // 2 else "⚪ MID " 
        print(f"   {bar} | Grid {i}: ${level:,.2f}")

    return grid_level
    

class GridTradingBot:
    def __init__(self,symbol, grid_levels, trade_amount, use_testnet=False):
        self.symbol = symbol
        self.grid_levels = grid_levels
        self.trade_amount = trade_amount
        self.grid_spacing = grid_levels[1] - grid_levels[0]

        # order tracking
        self.active_order = {}
        self.filled_trades = []
        self.trade_profit = 0.0

        # statistics
        self.total_buys = 0
        self.total_sells = 0
        self.iteration = 0
        
        #exchange setup
        self.exchange = None
        self.use_testnet = use_testnet
        self._setup_exchnage()
        
    def _setup_exchnage(self):
        if self.use_testnet:
            print("\n Connecting to Binance Testnet...") 
            self.exchange = ccxt.binance({
                'apiKey': API_KEY,
                'secret': SECRET_KEY,
                'enableRateLimit': True,
                'options': {'defaultType': 'spot'} 
            })
            self.exchange.set_sandbox_mode(True)
            print("Connected to testnet (Mock trading)")

        else:
            print("\n Connecting to Binance Public API (Simulation Mode)...")
            self.exchange = ccxt.binance({
                'enableRateLimit': True,
            })
            print("Connected (Simulation Mode - No real trades will be executed)")
