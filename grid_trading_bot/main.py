import ccxt
import pandas as pd
import time
from datetime import datetime as dt
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.progress import Progress, BarColumn, TextColumn
from rich import box
import sys

#Ui
console = Console()

# colors
COLOR_PRICE = "cyan"
COLOR_VOLUME = "blue"
COLOR_BUY = "green"
COLOR_SELL = "red"
COLOR_GRID = "yellow"
COLOR_PROFIT = "bright_green"
COLOR_BG = "black"

#trading
SYMBOL = 'BTC/USDT'
TIMEFRAME = '1m'
UPPER_PRICE = 66000
LOWER_PRICE = 65000
NUM_GRIDS = 10
TRADE_AMOUNT_USDT = 10

# grid bot class
class GridTradingBot:
    def __init__(self, symbol, grid_levels, trade_amount):
        self.symbol = symbol
        self.grid_levels = grid_levels
        self.trade_amount = trade_amount
        self.grid_spacing = grid_levels[1] - grid_levels[0]
        
        # Order Tracking
        self.active_orders = {}
        self.filled_trades = []
        self.total_profit = 0.0
        
        # Statistics
        self.total_buys = 0
        self.total_sells = 0
        self.iterations = 0
        self.price_history = []  # For chart
        self.volume_history = []  # For volume bars
        
        # Exchange Setup
        self.exchange = ccxt.binance({'enableRateLimit': True})
    
    def initialize_grid(self, current_price):
        console.print(f"\n[bold yellow]📍 Initializing Grid at Current Price: ${current_price:,.2f}[/bold yellow]")
        console.print("=" * 50)
    
    # Find nearest grid level
        nearest_level = min(self.grid_levels, key=lambda x: abs(x - current_price))
        nearest_index = self.grid_levels.index(nearest_level)
    
        console.print(f"[dim]Nearest grid level: ${nearest_level:,.2f} (Grid #{nearest_index})[/dim]\n")
    
        for i, level in enumerate(self.grid_levels):
            if level < current_price:
                self.active_orders[level] = {
                    'side': 'buy', 
                    'status': 'open',
                    'grid_num': i
                }
                marker = "◄── CURRENT" if level == nearest_level else ""
                console.print(f"   [green]🟢 BUY[/green]  order set at ${level:,.2f} {marker}")
            
            elif level > current_price:
                self.active_orders[level] = {
                    'side': 'sell', 
                    'status': 'open',
                    'grid_num': i
                }
                marker = "◄── CURRENT" if level == nearest_level else ""
                console.print(f"   [red]🔴 SELL[/red] order set at ${level:,.2f} {marker}")
            else:
                console.print(f"   [dim]⚪ SKIP[/dim]  (current price level) ${level:,.2f}")
    
        console.print(f"\n[bold]📊 Active Orders: {len(self.active_orders)}[/bold]")
    
        # immediately fill nearest grid bec of testing
        console.print(f"\n[yellow]⚡ Immediately filling nearest grid for testing...[/yellow]")
        time.sleep(1)
    
        fill_price = nearest_level
        # Nearest level fill immediately
        if nearest_level < current_price:
        # Nearest BUY order
            self.active_orders[nearest_level] = {
                'side': 'buy',
                'status': 'filled',
                'filled_at': dt.now().strftime('%H:%M:%S'),
                'fill_price': nearest_level
            }
            self.total_buys += 1

            self.filled_trades.append({
                'type': 'BUY',
                'level': nearest_level,
                'price': fill_price,
                'time': dt.now().strftime('%H:%M:%S'),
                'profit': 0  # currently no profit
            })
        
        # Opposite SELL order place
            sell_level = nearest_level + self.grid_spacing
            if sell_level in self.active_orders:
                self.active_orders[sell_level] = {
                    'side': 'sell',
                    'status': 'open'
                }
        
            console.print(f"\n   [bold green] BUY FILLED[/bold green] at ${nearest_level:,.2f}")
            console.print(f"   [dim]️  SELL order active at ${sell_level:,.2f}[/dim]")
        
        elif nearest_level > current_price:
            self.active_orders[nearest_level] = {
                'side': 'sell',
                'status': 'filled',
                'filled_at': dt.now().strftime('%H:%M:%S'),
                'fill_price': nearest_level
            }
            self.total_sells += 1
            
            self.filled_trades.append({
                'type': 'SELL',
                'level': nearest_level,
                'price': fill_price,
                'time': dt.now().strftime('%H:%M:%S'),
                'profit': 0  
            })
        

            buy_level = nearest_level - self.grid_spacing
            if buy_level in self.active_orders:
                self.active_orders[buy_level] = {
                    'side': 'buy',
                    'status': 'open'
                }
        
            console.print(f"\n   [bold red]✅ SELL FILLED[/bold red] at ${nearest_level:,.2f}")
            console.print(f"   [dim]️  BUY order active at ${buy_level:,.2f}[/dim]")
    
        console.print("\n[dim]Bot ab live market movements track karega...[/dim]\n")
    
    def check_and_execute(self, current_price, volume=0):
        self.iterations += 1
        self.price_history.append(current_price)
        self.volume_history.append(volume)
        
        # Keep only last 50 values
        if len(self.price_history) > 50:
            self.price_history = self.price_history[-50:]
            self.volume_history = self.volume_history[-50:]
        
        triggered = []
        
        for level, order in list(self.active_orders.items()):
            if order['status'] != 'open':
                continue
            
            hit = False
            if order['side'] == 'buy' and current_price <= level:
                hit = True
            elif order['side'] == 'sell' and current_price >= level:
                hit = True
            
            if hit:
                order['status'] = 'filled'
                triggered.append((level, order))
        
        for level, order in triggered:
            self._process_filled_order(level, order, current_price)
        
        return triggered
    
    def _process_filled_order(self, level, order, current_price):
        if order['side'] == 'buy':
            self.total_buys += 1
            self.filled_trades.append({'type': 'BUY', 'level': level, 'price': current_price, 'time': dt.now().strftime('%H:%M:%S')})
            
            sell_level = level + self.grid_spacing
            if sell_level not in self.active_orders or self.active_orders[sell_level]['status'] == 'filled':
                self.active_orders[sell_level] = {'side': 'sell', 'status': 'open'}
        
        elif order['side'] == 'sell':
            self.total_sells += 1
            grid_profit = self.grid_spacing * (self.trade_amount / level)
            self.total_profit += grid_profit
            self.filled_trades.append({'type': 'SELL', 'level': level, 'price': current_price, 'time': dt.now().strftime('%H:%M:%S'), 'profit': grid_profit})
            
            buy_level = level - self.grid_spacing
            if buy_level not in self.active_orders or self.active_orders[buy_level]['status'] == 'filled':
                self.active_orders[buy_level] = {'side': 'buy', 'status': 'open'}

#Ui 

def create_price_chart(price_history, grid_levels, current_price):
    """ASCII Price Chart banata hai (Reference image jaisa)"""
    if len(price_history) < 2:
        return "[dim]Collecting data...[/dim]"
    
    width = 50
    height = 15
    
    min_price = min(min(price_history), min(grid_levels)) * 0.999
    max_price = max(max(price_history), max(grid_levels)) * 1.001
    price_range = max_price - min_price
    
    chart = []
    
    # Header
    chart.append(f"[bold cyan]PRICE[/bold cyan]")
    chart.append("─" * width)
    
    # Draw chart row by row (top to bottom)
    for row in range(height):
        price_at_row = max_price - (row / height) * price_range
        line = ""
        
        for col in range(width):
            # Price line
            idx = int((col / width) * len(price_history))
            if idx < len(price_history):
                price = price_history[idx]
                price_row = int((max_price - price) / price_range * height)
                
                if price_row == row:
                    line += "[bold cyan]●[/bold cyan]"
                elif abs(price_row - row) <= 1:
                    line += "[dim cyan]·[/dim cyan]"
                else:
                    line += " "
            else:
                line += " "
        
        # Add price label on left
        if row == 0:
            label = f"[dim]{max_price:,.0f}[/dim]"
        elif row == height - 1:
            label = f"[dim]{min_price:,.0f}[/dim]"
        else:
            label = " " * 8
        
        chart.append(f"{label}{line}")
    
    chart.append("─" * width)
    chart.append(f"[bold yellow]GRID LEVELS:[/bold yellow] {len(grid_levels)} levels | Spacing: ${grid_levels[1] - grid_levels[0]:,.0f}")
    
    return "\n".join(chart)

def create_volume_bars(volume_history):
    """Volume bars banata hai"""
    if not volume_history:
        return "[dim]No volume data[/dim]"
    
    max_vol = max(volume_history) if volume_history else 1
    bar_width = 50
    
    chart = []
    chart.append(f"[bold blue]VOLUME[/bold blue]")
    chart.append("─" * bar_width)
    
    # Show last 20 volume bars
    recent_volumes = volume_history[-20:] if len(volume_history) >= 20 else volume_history
    
    for vol in recent_volumes:
        bar_length = int((vol / max_vol) * bar_width) if max_vol > 0 else 0
        bar = "█" * bar_length + "░" * (bar_width - bar_length)
        chart.append(f"[blue]{bar}[/blue] [dim]{vol:,.0f}[/dim]")
    
    return "\n".join(chart)

def create_grid_visualization(grid_levels, current_price, active_orders):
    """Grid levels ka visualization just like supply and demand"""
    chart = []
    chart.append(f"[bold yellow]SUPPLY / DEMAND[/bold yellow]")
    chart.append("─" * 40)
    
    # Sort grid levels from high to low
    sorted_levels = sorted(grid_levels, reverse=True)
    
    for level in sorted_levels:
        order = active_orders.get(level, {})
        side = order.get('side', 'unknown')
        status = order.get('status', 'unknown')
        
        # Determine symbol and color
        if side == 'buy' and status == 'open':
            symbol = " BUY"
            color = "green"
        elif side == 'sell' and status == 'open':
            symbol = " SELL"
            color = "red"
        elif status == 'filled':
            symbol = "✅ FILLED"
            color = "bright_green"
        else:
            symbol = " WAIT"
            color = "dim"
        
        # Current price marker
        if abs(level - current_price) < (grid_levels[1] - grid_levels[0]) / 2:
            marker = " ◄── CURRENT PRICE"
        else:
            marker = ""
        
        chart.append(f"[{color}]{symbol}[/{color}] ${level:,.0f}{marker}")
    
    return "\n".join(chart)

def create_stats_panel(bot, current_price):
    """Statistics panel banata hai"""
    open_orders = sum(1 for o in bot.active_orders.values() if o['status'] == 'open')
    filled_orders = sum(1 for o in bot.active_orders.values() if o['status'] == 'filled')
    
    table = Table(show_header=False, box=box.SIMPLE, padding=(0, 1))
    table.add_column("Label", style="dim")
    table.add_column("Value", justify="right")
    
    table.add_row("Current Price", f"[bold cyan]${current_price:,.2f}[/bold cyan]")
    table.add_row("Open Orders", f"[yellow]{open_orders}[/yellow]")
    table.add_row("Filled Orders", f"[bright_green]{filled_orders}[/bright_green]")
    table.add_row("Total Buys", f"[green]{bot.total_buys}[/green]")
    table.add_row("Total Sells", f"[red]{bot.total_sells}[/red]")
    table.add_row("Total Profit", f"[bold bright_green]${bot.total_profit:.4f}[/bold bright_green]")
    table.add_row("Iterations", f"[dim]{bot.iterations}[/dim]")
    
    return table

def create_trade_history(bot):
    # Recent trades table
    if not bot.filled_trades:
        return Panel("[dim]No trades yet...[/dim]", title="📋 TRADE HISTORY", border_style="dim")
    
    table = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    table.add_column("Time", style="dim")
    table.add_column("Type")
    table.add_column("Level", justify="right")
    table.add_column("Price", justify="right")
    table.add_column("Profit", justify="right")
    
    # Show last 5 trades
    recent_trades = bot.filled_trades[-5:]
    
    for trade in recent_trades:
        time = trade['time']
        type = f"[green]{trade['type']}[/green]" if trade['type'] == 'BUY' else f"[red]{trade['type']}[/red]"
        level = f"${trade['level']:,.0f}"
        price = f"${trade['price']:,.2f}"
        profit = f"${trade.get('profit', 0):.4f}" if trade.get('profit') else "-"
        
        table.add_row(time, type, level, price, profit)
    
    return Panel(table, title="📋 RECENT TRADES", border_style="blue")

def create_dashboard(bot, current_price):
    """Complete dashboard layout banata hai"""
    # Create layout
    layout = Layout()
    
    # Split layout
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=10)
    )
    
    # Header
    header_content = Panel(
        f"[bold cyan]🤖 GRID TRADING BOT[/bold cyan] | [dim]{SYMBOL}[/dim] | [yellow]{dt.now().strftime('%Y-%m-%d %H:%M:%S')}[/yellow]",
        box=box.DOUBLE,
        border_style="cyan"
    )
    layout["header"].update(header_content)
    
    # Body 
    layout["body"].split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=1)
    )
    
    # Left side
    price_chart = create_price_chart(bot.price_history, bot.grid_levels, current_price)
    volume_chart = create_volume_bars(bot.volume_history)
    
    left_content = Panel(
        f"{price_chart}\n\n{volume_chart}",
        title="📊 MARKET DATA",
        border_style="cyan"
    )
    layout["left"].update(left_content)
    
    # Right side
    grid_viz = create_grid_visualization(bot.grid_levels, current_price, bot.active_orders)
    stats = create_stats_panel(bot, current_price)
    
    right_content = Panel(
        f"{grid_viz}\n\n{stats}",
        title="📈 GRID STATUS",
        border_style="yellow"
    )
    layout["right"].update(right_content)
    
    # Footer
    trade_history = create_trade_history(bot)
    layout["footer"].update(trade_history)
    
    return layout

# main loop 
def fetch_latest_data(exchange, symbol, timeframe, limit=100):
    """Latest market data fetch karta hai"""
    try:
        raw_data = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        df = pd.DataFrame(raw_data, columns=['Timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
        df['Timestamp'] = pd.to_datetime(df['Timestamp'], unit='ms')
        df.set_index('Timestamp', inplace=True)
        return df
    except Exception as e:
        print(f" Error fetching data: {e}")
        return None

def calculate_grid_levels(upper, lower, num_grids):
    """Grid levels calculate karta hai"""
    grid_spacing = (upper - lower) / num_grids
    grid_levels = []
    for i in range(num_grids + 1):
        level = lower + (i * grid_spacing)
        grid_levels.append(round(level, 2))
    return grid_levels

def run_grid_bot():
    console.clear()
    console.print("[bold cyan]Initializing Grid Trading Bot...[/bold cyan]")
    
    grid_levels = calculate_grid_levels(UPPER_PRICE, LOWER_PRICE, NUM_GRIDS)
    
    bot = GridTradingBot(
        symbol=SYMBOL,
        grid_levels=grid_levels,
        trade_amount=TRADE_AMOUNT_USDT
    )
    
    data = fetch_latest_data(bot.exchange, SYMBOL, TIMEFRAME, limit=100)
    if data is None:
        console.print("[red]❌ Could not fetch data. Exiting.[/red]")
        return
    
    current_price = data.iloc[-1]['Close']
    volume = data.iloc[-1]['Volume']
    
    if current_price < LOWER_PRICE or current_price > UPPER_PRICE:
        console.print(f"[yellow]⚠️  WARNING: Price ${current_price:,.2f} is OUTSIDE grid range![/yellow]")
        console.print(f"[dim]Grid Range: ${LOWER_PRICE:,.2f} - ${UPPER_PRICE:,.2f}[/dim]")
    
    bot.initialize_grid(current_price)
    
    console.print("[bold green]✅ Bot initialized! Starting live dashboard...[/bold green]")
    console.print("[dim]Press Ctrl+C to stop[/dim]\n")
    
    try:
        with Live(console=console, refresh_per_second=2, screen=True) as live:
            while True:
                data = fetch_latest_data(bot.exchange, SYMBOL, TIMEFRAME, limit=100)
                
                if data is not None:
                    current_price = data.iloc[-1]['Close']
                    volume = data.iloc[-1]['Volume']
                    
                    bot.check_and_execute(current_price, volume)
                    
                    dashboard = create_dashboard(bot, current_price)
                    live.update(dashboard)
                
                time.sleep(5) 
                
    except KeyboardInterrupt:
        console.print("\n[bold red]🛑 Bot stopped by user[/bold red]") # !!
        
        console.print(f"\n[bold]Final Stats:[/bold]")
        console.print(f"  Total Profit: [green]${bot.total_profit:.4f}[/green]")
        console.print(f"  Total Trades: {len(bot.filled_trades)}")
        
        if bot.filled_trades:
            trades_df = pd.DataFrame(bot.filled_trades)
            trades_df.to_csv('grid_trade_history.csv', index=False)
            console.print(f"[dim]Trade history saved to 'grid_trade_history.csv'[/dim]")


if __name__ == "__main__":
    run_grid_bot()