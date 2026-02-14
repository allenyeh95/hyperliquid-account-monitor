import requests
import time
import pandas as pd
from datetime import datetime, timedelta
import os

class HyperliquidMonitor:
    def __init__(self, account_address):
        self.account_address = account_address
        self.base_url = "https://api.hyperliquid.xyz/info"
        self.equity_history = []
        
    def get_account_info(self):
        """Fetch account information"""
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
        """Display position information"""
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
    
    def monitor(self, update_interval=10):
        """Main monitoring loop"""
        print(f"\nStarting account monitoring... (Update interval: {update_interval}s)")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                positions = self.get_positions()
                self.display_positions(positions)
                
                # Show next update time
                next_update = datetime.now() + timedelta(seconds=update_interval)
                print(f"\nNext update: {next_update.strftime('%H:%M:%S')}")
                print("Press Ctrl+C to stop monitoring")
                
                time.sleep(update_interval)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Monitoring stopped")

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
    monitor.monitor(update_interval=10)

if __name__ == "__main__":
    main()
