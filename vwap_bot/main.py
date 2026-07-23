import ccxt
import pandas as pd
import numpy as np
import time
from datetime import datetime as dt
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box

console = Console()

# trading 
SYMBOL = 'BTC/USDT'
TIMEFRAME = '5m'          # 5-minute candles (VWAP ke liye best)
LOOKBACK_PERIOD = 50      # Rolling VWAP period (50 candles)
STD_DEV_MULTIPLIER = 2.0  # VWAP Bands ka multiplier (2.0 = 95% confidence)
ENTRY_THRESHOLD = 0.5     # Entry ke liye minimum deviation (2.0 Std Dev)
EXIT_THRESHOLD = 0.1      # Exit ke liye deviation (jab price VWAP ke paas aaye)


def calculate_vwap_and_bands(df, period=50, multiplier=2.0):
    """
    Rolling VWAP aur Standard Deviation Bands calculate karta hai.
    Crypto 24/7 chalta hai, isliye hum Rolling VWAP use kar rahe hain.
    """
    # 1. Typical Price = (High + Low + Close) / 3
    df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
    
    # 2. Cumulative Values for VWAP
    df['Cum_TP_Vol'] = (df['Typical_Price'] * df['Volume']).rolling(window=period).sum()
    df['Cum_Vol'] = df['Volume'].rolling(window=period).sum()
    
    # 3. VWAP Formula
    df['VWAP'] = df['Cum_TP_Vol'] / df['Cum_Vol']
    
    # 4. Standard Deviation for Bands
    df['Variance'] = (df['Volume'] * (df['Typical_Price'] - df['VWAP'])**2).rolling(window=period).sum()
    df['Std_Dev'] = np.sqrt(df['Variance'] / df['Cum_Vol'])
    
    # 5. Upper aur Lower Bands
    df['Upper_Band'] = df['VWAP'] + (df['Std_Dev'] * multiplier)
    df['Lower_Band'] = df['VWAP'] - (df['Std_Dev'] * multiplier)
    
    # 6. Deviation % (Price VWAP se kitna door hai)
    df['Deviation_Pct'] = ((df['Close'] - df['VWAP']) / df['VWAP']) * 100
    
    return df


class VWAPBot:
    def __init__(self):
        self.exchange = ccxt.binance({'enableRateLimit': True})
        self.position = None     # long short or none
        self.entry_price = 0.0
        self.trade_history = []
        self.signal_log = []
        self.iterations = 0

    def fetch_data(self):
        try:
            raw_data = self.exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, limit=100)
            df = pd.DataFrame(raw_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
            df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
            df.set_index('Timestamp', inplace=True)
            return df
        except Exception as e:
            console.print(f"[red] Data fetch error: {e}[/red]")
            return None

    def analyze_and_trade(self, df):
        self.iterations += 1
        
        df = calculate_vwap_and_bands(df, LOOKBACK_PERIOD, STD_DEV_MULTIPLIER)
        
        latest = df.iloc[-1]
        current_price = latest['Close']
        vwap = latest['VWAP']
        upper_band = latest['Upper_Band']
        lower_band = latest['Lower_Band']
        deviation = latest['Deviation_Pct']
        
        # Z-Score (Standard deviations mein distance)
        z_score = (current_price - vwap) / latest['Std_Dev'] if latest['Std_Dev'] != 0 else 0
        
        signal = "HOLD"
        action_taken = ""

        # 1. EXIT Logic (Mean Reversion)
        if self.position and abs(z_score) < EXIT_THRESHOLD:
            action_taken = self._close_position(current_price)
            signal = "EXIT"
            
        # 2. ENTRY Logic 
        elif not self.position:
            if z_score < -ENTRY_THRESHOLD:  
                action_taken = self._open_position('LONG', current_price)
                signal = "BUY"
            elif z_score > ENTRY_THRESHOLD: 
                action_taken = self._open_position('SHORT', current_price)
                signal = "SELL"

        if action_taken:
            self.signal_log.insert(0, f"{dt.now().strftime('%H:%M:%S')} | {signal} | {action_taken}")
            if len(self.signal_log) > 5:
                self.signal_log.pop()

        return {
            'price': current_price, 'vwap': vwap, 'upper': upper_band, 'lower': lower_band,
            'deviation': deviation, 'z_score': z_score, 'signal': signal
        }

    def _open_position(self, side, price):
        self.position = side
        self.entry_price = price
        return f"Opened {side} @ ${price:,.2f}"

    def _close_position(self, price):
        pnl = 0.0
        if self.position == 'LONG':
            pnl = price - self.entry_price
        elif self.position == 'SHORT':
            pnl = self.entry_price - price
            
        self.trade_history.append({'side': self.position, 'entry': self.entry_price, 'exit': price, 'pnl': pnl})
        result = f"Closed {self.position} @ ${price:,.2f} | PnL: ${pnl:,.2f}"
        
        self.position = None
        self.entry_price = 0.0
        return result


# ui
def create_progress_bar(current_z, threshold):
    """Progress bar banata hai ki entry se kitna door hai"""
    percentage = min(abs(current_z) / threshold * 100, 100)
    filled = int(percentage / 5)  # 20 blocks
    empty = 20 - filled
    
    bar = "█" * filled + "░" * empty
    
    if abs(current_z) >= threshold:
        status = "[bold green] READY![/bold green]"
    else:
        remaining = threshold - abs(current_z)
        status = f"[yellow]{remaining:.2f} away[/yellow]"
    
    return f"[{bar}] {percentage:.1f}% - {status}"

def create_metrics_table(metrics, bot):
    """Main metrics ka table"""
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", justify="right")

    progress = create_progress_bar(metrics['z_score'],ENTRY_THRESHOLD)

    # Price aur VWAP
    table.add_row("Current Price", f"[bold white]${metrics['price']:,.2f}[/bold white]")
    table.add_row("VWAP (Fair Value)", f"[yellow]${metrics['vwap']:,.2f}[/yellow]")
    table.add_row("Upper Band (2σ)", f"[red]${metrics['upper']:,.2f}[/red]")
    table.add_row("Lower Band (2σ)", f"[green]${metrics['lower']:,.2f}[/green]")
    table.add_row("EntryProgress", progress)
    
    table.add_row("", "") 
    
    # Deviation aur Z-Score
    dev_color = "red" if metrics['deviation'] > 0 else "green"
    table.add_row("Deviation %", f"[{dev_color}]{metrics['deviation']:.3f}%[/{dev_color}]")
    table.add_row("Z-Score", f"[bold magenta]{metrics['z_score']:.2f}[/bold magenta]")
    
    table.add_row("", "") # Spacer
    
    if bot.position:
        pos_color = "green" if bot.position == 'LONG' else "red"
        table.add_row("Current Position", f"[bold {pos_color}]{bot.position}[/bold {pos_color}]")
        table.add_row("Entry Price", f"${bot.entry_price:,.2f}")
        
        # Live PnL
        live_pnl = (metrics['price'] - bot.entry_price) if bot.position == 'LONG' else (bot.entry_price - metrics['price'])
        pnl_color = "bright_green" if live_pnl >= 0 else "bright_red"
        table.add_row("Live PnL", f"[bold {pnl_color}]${live_pnl:,.4f}[/bold {pnl_color}]")
    else:
        table.add_row("Current Position", "[dim]FLAT (No Position)[/dim]")

    return table

def create_signal_log(bot):
    """Recent signals ka panel"""
    if not bot.signal_log:
        return Panel("[dim]Waiting for signals...[/dim]", title="📡 SIGNAL LOG", border_style="dim")
    
    text = Text()
    for log in bot.signal_log:
        if "BUY" in log:
            text.append(log + "\n", style="bold green")
        elif "SELL" in log:
            text.append(log + "\n", style="bold red")
        elif "EXIT" in log:
            text.append(log + "\n", style="bold yellow")
        else:
            text.append(log + "\n", style="dim")
            
    return Panel(text, title="📡 SIGNAL LOG", border_style="blue")

def create_trade_history(bot):
    """Completed trades ka table"""
    if not bot.trade_history:
        return Panel("[dim]No closed trades yet.[/dim]", title=" TRADE HISTORY", border_style="dim")
        
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Side")
    table.add_column("Entry", justify="right")
    table.add_column("Exit", justify="right")
    table.add_column("PnL", justify="right")
    
    for trade in bot.trade_history[-5:]: 
        side_style = "green" if trade['side'] == 'LONG' else "red"
        pnl_style = "bright_green" if trade['pnl'] >= 0 else "bright_red"
        table.add_row(
            f"[{side_style}]{trade['side']}[/{side_style}]",
            f"${trade['entry']:,.2f}",
            f"${trade['exit']:,.2f}",
            f"[{pnl_style}]${trade['pnl']:.4f}[/{pnl_style}]"
        )
    return Panel(table, title="💰 TRADE HISTORY", border_style="bright_green")

def build_dashboard(bot, metrics):
    """Complete dashboard layout"""
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=10)
    )
    
    # Header
    layout["header"].update(Panel(
        f"[bold cyan]📊 VWAP REVERSION BOT[/bold cyan] | [dim]{SYMBOL} ({TIMEFRAME})[/dim] | [yellow]{dt.now().strftime('%Y-%m-%d %H:%M:%S')}[/yellow]",
        box=box.DOUBLE, border_style="cyan"
    ))
    
    # Body
    layout["body"].split_row(
        Layout(name="metrics", ratio=1),
        Layout(name="signals", ratio=1)
    )
    layout["metrics"].update(Panel(create_metrics_table(metrics, bot), title="📈 MARKET METRICS", border_style="cyan"))
    layout["signals"].update(create_signal_log(bot))
    
    # Footer 
    layout["footer"].update(create_trade_history(bot))
    
    return layout


def run_bot():
    console.clear()
    console.print("[bold cyan]Initializing VWAP Reversion Bot...[/bold cyan]")
    
    bot = VWAPBot()
    
    console.print("[dim]Fetching initial data for VWAP calculation...[/dim]")
    initial_data = bot.fetch_data()
    if initial_data is None:
        console.print("[red]Failed to fetch initial data. Exiting.[/red]")
        return
    
    console.print("[bold green] Bot Ready! Launching Live Dashboard...[/bold green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")
    
    try:
        with Live(console=console, refresh_per_second=2, screen=True) as live:
            while True:
                data = bot.fetch_data()
                if data is not None:
                    metrics = bot.analyze_and_trade(data)
                    dashboard = build_dashboard(bot, metrics)
                    live.update(dashboard)
                
                time.sleep(30) 
                
    except KeyboardInterrupt:
        console.print("\n[bold red] Bot stopped by user.[/bold red]")

if __name__ == "__main__":
    run_bot()