import pandas as pd
import ccxt
import mplfinance as mpf
from datetime import datetime as dt
import time
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box
import numpy as np

# ═══════════════════════════════════════════════════
# 🎨 TERMINAL UI SETUP
# ═══════════════════════════════════════════════════

console = Console()

# ═══════════════════════════════════════════════════
#  TRADING PARAMETERS
# ═══════════════════════════════════════════════════

symbol = 'BTC/USDT'
timeframe = '5m'
limit = 100
trade_amount = 10

# ══════════════════════════════════════════════════
# 🤖 EXCHANGE SETUP
# ═══════════════════════════════════════════════════

exchange = ccxt.binance({
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})

# ═══════════════════════════════════════════════════
#  DATA FETCHING
# ═══════════════════════════════════════════════════

def fetch_market_data():
    try:
        raw_data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(raw_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        df.set_index('Timestamp', inplace=True)
        return df
    except Exception as e:
        console.print(f"[red]Error fetching data: {e}[/red]")
        return None

# ═══════════════════════════════════════════════════
#  BOLLINGER BANDS CALCULATION
# ══════════════════════════════════════════════════

def calculate_bollinger_bands(df, window=20, num_std=2):
    df['Middle_Band'] = df['Close'].rolling(window=window).mean()
    rolling_std = df['Close'].rolling(window=window).std()
    df['Upper_Band'] = df['Middle_Band'] + num_std * rolling_std
    df['Lower_Band'] = df['Middle_Band'] - num_std * rolling_std
    
    # Bandwidth aur %B calculate karo (advanced metrics)
    df['Bandwidth'] = ((df['Upper_Band'] - df['Lower_Band']) / df['Middle_Band']) * 100
    df['Percent_B'] = ((df['Close'] - df['Lower_Band']) / (df['Upper_Band'] - df['Lower_Band']))
    
    return df

# ═══════════════════════════════════════════════════
#  SIGNAL GENERATION
# ═══════════════════════════════════════════════════

class BollingerBot:
    def __init__(self):
        self.signals_history = []
        self.total_signals = 0
        self.buy_signals = 0
        self.sell_signals = 0
        
    def generate_signals(self, df):
        latest = df.iloc[-1]
        current_close = latest['Close']
        current_upper = latest['Upper_Band']
        current_lower = latest['Lower_Band']
        
        signal = "HOLD"
        signal_color = "dim"
        
        if current_close > current_upper:
            signal = "BUY"
            signal_color = "bold bright_green"
            self.buy_signals += 1
        elif current_close < current_lower:
            signal = "SELL"
            signal_color = "bold bright_red"
            self.sell_signals += 1
        
        self.total_signals += 1
        
        # Signal history mein add karo
        signal_info = {
            'time': dt.now().strftime('%H:%M:%S'),
            'signal': signal,
            'price': current_close,
            'upper': current_upper,
            'lower': current_lower
        }
        self.signals_history.insert(0, signal_info)
        if len(self.signals_history) > 5:
            self.signals_history.pop()
        
        return signal, signal_color, latest

# ═══════════════════════════════════════════════════
# 🎨 UI COMPONENTS
# ═══════════════════════════════════════════════════

def create_metrics_table(df, bot):
    """Market metrics ka table banata hai"""
    latest = df.iloc[-1]
    
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    table.add_column("Metric", style="bold cyan")
    table.add_column("Value", justify="right")
    
    # Price info
    table.add_row("Current Price", f"[bold white]${latest['Close']:,.2f}[/bold white]")
    table.add_row("Upper Band", f"[red]${latest['Upper_Band']:,.2f}[/red]")
    table.add_row("Middle Band (SMA)", f"[yellow]${latest['Middle_Band']:,.2f}[/yellow]")
    table.add_row("Lower Band", f"[green]${latest['Lower_Band']:,.2f}[/green]")
    
    table.add_row("", "")
    
    # Advanced metrics
    table.add_row("Bandwidth", f"[dim]{latest['Bandwidth']:.2f}%[/dim]")
    table.add_row("%B Indicator", f"[magenta]{latest['Percent_B']:.3f}[/magenta]")
    
    # Distance from bands
    dist_upper = ((latest['Close'] - latest['Upper_Band']) / latest['Upper_Band']) * 100
    dist_lower = ((latest['Close'] - latest['Lower_Band']) / latest['Lower_Band']) * 100
    
    table.add_row("Distance to Upper", f"[red]{dist_upper:+.2f}%[/red]")
    table.add_row("Distance to Lower", f"[green]{dist_lower:+.2f}%[/green]")
    
    return table

def create_signal_panel(signal, signal_color, latest):
    """Current signal ka panel"""
    signal_text = Text()
    signal_text.append(f"Current Signal: ", style="bold")
    signal_text.append(f"{signal}", style=signal_color)
    
    if signal == "BUY":
        reason = "Price broke above Upper Band (Bullish Breakout)"
        reason_style = "bright_green"
    elif signal == "SELL":
        reason = "Price broke below Lower Band (Bearish Breakdown)"
        reason_style = "bright_red"
    else:
        reason = "Price consolidating between bands"
        reason_style = "dim"
    
    panel_content = f"[bold]{signal}[/bold]\n\n[dim]{reason}[/dim]\n\nPrice: [white]${latest['Close']:,.2f}[/white]"
    
    border_color = "green" if signal == "BUY" else "red" if signal == "SELL" else "dim"
    
    return Panel(panel_content, title="🎯 SIGNAL", border_style=border_color)


def create_signals_history(bot):
    """Recent signals history"""
    if not bot.signals_history:
        return Panel("[dim]Waiting for signals...[/dim]", title=" SIGNAL HISTORY", border_style="dim")
    
    # ✅ Correct column definitions (all 5 columns properly defined)
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Time", style="dim", width=8)
    table.add_column("Signal", width=8)
    table.add_column("Price", justify="right")
    table.add_column("Upper", justify="right", style="dim")
    table.add_column("Lower", justify="right", style="dim")
    
    # ✅ Remove the invalid "Upper" and "Lower" rows
    # (Yeh unnecessary the aur error deta tha)
    
    for sig in bot.signals_history:
        sig_style = "bright_green" if sig['signal'] == "BUY" else "bright_red" if sig['signal'] == "SELL" else "dim"
        table.add_row(
            sig['time'],
            f"[{sig_style}]{sig['signal']}[/{sig_style}]",
            f"${sig['price']:,.2f}",
            f"${sig['upper']:,.2f}",
            f"${sig['lower']:,.2f}"
        )
    
    return Panel(table, title=" SIGNAL HISTORY", border_style="blue")

def create_stats_panel(bot):
    """Statistics panel"""
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    table.add_column("Stat", style="dim")
    table.add_column("Value", justify="right")
    
    table.add_row("Total Iterations", f"[cyan]{bot.total_signals}[/cyan]")
    table.add_row("BUY Signals", f"[green]{bot.buy_signals}[/green]")
    table.add_row("SELL Signals", f"[red]{bot.sell_signals}[/red]")
    
    if bot.total_signals > 0:
        buy_pct = (bot.buy_signals / bot.total_signals) * 100
        sell_pct = (bot.sell_signals / bot.total_signals) * 100
        table.add_row("Buy Ratio", f"[dim]{buy_pct:.1f}%[/dim]")
        table.add_row("Sell Ratio", f"[dim]{sell_pct:.1f}%[/dim]")
    
    return table

def build_dashboard(df, bot, signal, signal_color, latest):
    """Complete dashboard layout"""
    layout = Layout()
    
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=10)
    )
    
    # Header
    layout["header"].update(Panel(
        f"[bold cyan]📊 BOLLINGER BANDS BREAKOUT BOT[/bold cyan] | [dim]{symbol} ({timeframe})[/dim] | [yellow]{dt.now().strftime('%Y-%m-%d %H:%M:%S')}[/yellow]",
        box=box.DOUBLE, border_style="cyan"
    ))
    
    # Body - Left and Right
    layout["body"].split_row(
        Layout(name="metrics", ratio=2),
        Layout(name="signals", ratio=1)
    )
    
    # Left side
    metrics_table = create_metrics_table(df, bot)
    signal_panel = create_signal_panel(signal, signal_color, latest)
    
    left_content = Layout()
    left_content.split_column(
        Layout(name="metrics_panel", size=15),
        Layout(name="signal_panel")
    )
    left_content["metrics_panel"].update(Panel(metrics_table, title="📈 MARKET METRICS", border_style="cyan"))
    left_content["signal_panel"].update(signal_panel)
    
    layout["metrics"].update(left_content)
    
    # Right side
    stats = create_stats_panel(bot)
    layout["signals"].update(Panel(stats, title="📊 STATISTICS", border_style="yellow"))
    
    # Footer - Signal history
    layout["footer"].update(create_signals_history(bot))
    
    return layout

# ═══════════════════════════════════════════════════
# 📈 CHART GENERATION (Optional)
# ═══════════════════════════════════════════════════

def plot_chart(df):
    """Chart save karta hai (optional)"""
    add_plot = [
        mpf.make_addplot(df["Middle_Band"], color="blue", width=1.5),
        mpf.make_addplot(df["Upper_Band"], color="green", width=1),
        mpf.make_addplot(df["Lower_Band"], color="red", width=1)
    ]
    
    mpf.plot(
        df, type='candle', addplot=add_plot,
        title=f'\n{symbol} {timeframe} Chart with Bollinger Bands',
        ylabel='Price (USDT)', volume=True,
        style='nightclouds', figsize=(12, 8),
        savefig='bollinger_chart.png'
    )

# ══════════════════════════════════════════════════
# 🚀 MAIN BOT LOOP
# ═══════════════════════════════════════════════════

def run_bot():
    console.clear()
    console.print("[bold cyan]Initializing Bollinger Bands Breakout Bot...[/bold cyan]")
    
    bot = BollingerBot()
    
    console.print("[bold green]✅ Bot Ready! Launching Live Dashboard...[/bold green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")
    
    try:
        with Live(console=console, refresh_per_second=1, screen=True) as live:
            iteration = 1
            while True:
                # Data fetch
                data = fetch_market_data()
                
                if data is not None:
                    # Calculate bands
                    data_with_bands = calculate_bollinger_bands(data)
                    
                    # Generate signal
                    signal, signal_color, latest = bot.generate_signals(data_with_bands)
                    
                    # Build and update dashboard
                    dashboard = build_dashboard(data_with_bands, bot, signal, signal_color, latest)
                    live.update(dashboard)
                    
                    # Optional: Chart save every 10 iterations
                    if iteration % 10 == 0:
                        try:
                            plot_chart(data_with_bands)
                        except:
                            pass
                
                time.sleep(5)  # 5 seconds refresh
                iteration += 1
                
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Bot stopped by user[/bold red]")
        console.print(f"\n[bold]Final Stats:[/bold]")
        console.print(f"  Total Iterations: {bot.total_signals}")
        console.print(f"  BUY Signals: {bot.buy_signals}")
        console.print(f"  SELL Signals: {bot.sell_signals}")

# ═══════════════════════════════════════════════════
# 🎯 START BOT
# ═══════════════════════════════════════════════════

if __name__ == "__main__":
    run_bot()