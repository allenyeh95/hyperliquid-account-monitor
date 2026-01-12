import requests
import time
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import os

class HyperliquidMonitor:
    def __init__(self, account_address):
        self.account_address = account_address
        self.base_url = "https://api.hyperliquid.xyz/info"
        self.equity_history = []
        
    def get_account_info(self):
        try:
            payload = {
                "type": "clearinghouseState",
                "user": self.account_address
            }
            response = requests.post(self.base_url, json=payload, timeout=10)
            data = response.json()
            
            if 'error' in data:
                print(f"Error: {data['error']}")
                return None
            return data
        except Exception as e:
            print(f"API Request Error: {e}")
            return None
    
    def get_positions(self):
        """Get current positions"""
        data = self.get_account_info()
        if not data:
            return []
        
        positions = []
        if 'assetPositions' in data:
            for pos in data['assetPositions']:
                position_info = pos['position']
                symbol = position_info['coin']
                size = float(position_info['szi'])
                entry_px = float(position_info['entryPx'])
                unrealized_pnl = float(position_info.get('unrealizedPnl', 0))
                
                if size != 0:
                    direction = "LONG" if size > 0 else "SHORT"
                    positions.append({
                        'symbol': symbol,
                        'size': abs(size),
                        'direction': direction,
                        'entry_price': entry_px,
                        'unrealized_pnl': unrealized_pnl
                    })
        
        return positions
    
    def get_account_value(self):
        """Get total account value"""
        data = self.get_account_info()
        if not data:
            return 0
        
        total_value = 0
        if 'marginSummary' in data:
            total_value = float(data['marginSummary'].get('accountValue', 0))
        
        # Record historical data
        self.equity_history.append({
            'timestamp': datetime.now(),
            'value': total_value
        })
        
        # Keep only last 7 days of data
        seven_days_ago = datetime.now() - timedelta(days=7)
        self.equity_history = [h for h in self.equity_history 
                              if h['timestamp'] > seven_days_ago]
        
        return total_value
    
    def display_positions(self, positions):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("=" * 70)
        print(f"HYPERLIQUID ACCOUNT MONITOR")
        print(f"Account: {self.account_address[:10]}...{self.account_address[-6:]}")
        print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        total_value = self.get_account_value()
        print(f"Account Value: ${total_value:,.2f}")
        print("-" * 70)
        
        if not positions:
            print("No active positions")
            return
        
        print(f"{'Symbol':<12} {'Direction':<12} {'Size':<15} {'Entry Price':<15} {'Unrealized P&L':<15}")
        print("-" * 70)
        
        for pos in positions:
            direction = pos['direction']
            
            # Color-coded direction
            if direction == "LONG":
                direction_text = f"\033[92m▲ LONG\033[0m"
            else:
                direction_text = f"\033[91m▼ SHORT\033[0m"
            
            # Format P&L with color
            pnl = pos['unrealized_pnl']
            pnl_color = "\033[92m" if pnl >= 0 else "\033[91m"
            pnl_text = f"{pnl_color}${pnl:+,.2f}\033[0m"
            
            print(f"{pos['symbol']:<12} {direction_text:<20} {pos['size']:<15.4f} "
                  f"${pos['entry_price']:<14.2f} {pnl_text:<20}")
    
    def plot_account_value(self):
        """Plot 7-day account value chart"""
        if len(self.equity_history) < 2:
            print("Insufficient data for chart")
            return
        
        # Prepare data
        df = pd.DataFrame(self.equity_history)
        df.set_index('timestamp', inplace=True)
        
        # Create chart
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['value'], 'b-', linewidth=2.5, label='Account Value')
        
        # Fill area under curve
        plt.fill_between(df.index, df['value'], alpha=0.2)
        
        # Format chart
        plt.title('7-Day Account Value History', fontsize=16, fontweight='bold', pad=20)
        plt.xlabel('Date & Time', fontsize=12)
        plt.ylabel('Account Value (USD)', fontsize=12)
        plt.grid(True, alpha=0.3, linestyle='--')
        
        # Format axes
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        plt.gcf().autofmt_xdate()
        
        # Add latest value annotation
        latest_value = df['value'].iloc[-1]
        plt.annotate(f'Current: ${latest_value:,.2f}', 
                    xy=(df.index[-1], latest_value),
                    xytext=(10, 10), textcoords='offset points',
                    fontsize=11, fontweight='bold',
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="yellow", alpha=0.8))
        
        # Add statistics
        if len(df) > 0:
            max_val = df['value'].max()
            min_val = df['value'].min()
            change = ((latest_value - df['value'].iloc[0]) / df['value'].iloc[0] * 100) if df['value'].iloc[0] != 0 else 0
            
            stats_text = f"Max: ${max_val:,.2f}\nMin: ${min_val:,.2f}\nChange: {change:+.2f}%"
            plt.text(0.02, 0.98, stats_text, transform=plt.gca().transAxes,
                    fontsize=10, verticalalignment='top',
                    bbox=dict(boxstyle="round,pad=0.5", facecolor="lightgray", alpha=0.7))
        
        plt.legend()
        plt.tight_layout()
        
        # Save chart
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"account_value_{timestamp}.png"
        plt.savefig(filename, dpi=120)
        plt.close()
        
        print(f"\n📊 Chart saved: {filename}")
    
    def monitor(self, update_interval=10, plot_interval=300):
        """Main monitoring loop"""
        last_plot_time = time.time()
        
        print(f"\nStarting account monitoring... (Update interval: {update_interval}s)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                positions = self.get_positions()
                self.display_positions(positions)
                
                # Generate chart periodically
                current_time = time.time()
                if current_time - last_plot_time >= plot_interval:
                    print("\n" + "-" * 70)
                    print("Generating 7-day account value chart...")
                    self.plot_account_value()
                    last_plot_time = current_time
                
                # Show next update time
                next_update = datetime.now() + timedelta(seconds=update_interval)
                print(f"\nNext update: {next_update.strftime('%H:%M:%S')}")
                print("Press Ctrl+C to stop monitoring")
                
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped")
            # Generate final chart before exit
            if self.equity_history:
                print("Generating final chart...")
                self.plot_account_value()

def main():
    """Main program"""
    print("=" * 70)
    print("HYPERLIQUID ACCOUNT MONITORING SYSTEM")
    print("=" * 70)
    
    # Get account address
    account_address = input("Enter your Hyperliquid account address: ").strip()
    
    if not account_address:
        print("Error: Account address is required")
        return
    
    # Validate address format (basic check)
    if not account_address.startswith('0x') or len(account_address) != 42:
        print("Warning: Address format may be invalid. Continue anyway? (y/n)")
        if input().lower() != 'y':
            return
    
    # Create monitor instance
    monitor = HyperliquidMonitor(account_address)
    
    # Test connection
    print("\nTesting connection...")
    test_data = monitor.get_account_info()
    if not test_data:
        print("Error: Cannot connect to Hyperliquid API or invalid account address")
        return
    
    print("✅ Connection successful! Starting monitoring...")
    time.sleep(2)
    
    # Start monitoring
    monitor.monitor(update_interval=10, plot_interval=300)

if __name__ == "__main__":
    main()
