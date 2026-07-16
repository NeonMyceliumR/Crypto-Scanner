import requests
import json
from datetime import datetime, timedelta

def get_binance_tickers():
    """Get all trading pairs from Binance"""
    try:
        url = 'https://api.binance.com/api/v3/exchangeInfo'
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Filter for USDT pairs and get symbols
        symbols = [s['symbol'] for s in data['symbols'] if s['symbol'].endswith('USDT') and s['status'] == 'TRADING']
        return symbols
    except Exception as e:
        print(f'Error fetching tickers: {e}')
        return []

def get_coin_price(symbol):
    """Get current price for a symbol"""
    try:
        url = f'https://api.binance.com/api/v3/ticker/24hr'
        response = requests.get(url, params={'symbol': symbol}, timeout=10)
        response.raise_for_status()
        return float(response.json()['lastPrice'])
    except:
        return None

def get_market_cap_estimate(symbol, price):
    """Estimate market cap from price and volume"""
    try:
        # Get 24h volume
        url = f'https://api.binance.com/api/v3/ticker/24hr'
        response = requests.get(url, params={'symbol': symbol}, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        quote_volume = float(data['quoteAssetVolume'])  # Volume in USDT
        return quote_volume
    except:
        return None

def get_historical_volume(symbol, days=14):
    """Get historical volume data from Binance"""
    try:
        url = 'https://api.binance.com/api/v3/klines'
        
        # Get daily candles for the last X days
        params = {
            'symbol': symbol,
            'interval': '1d',
            'limit': days
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        klines = response.json()
        
        # Extract volume data
        volumes = []
        for kline in klines:
            # kline[7] is quote asset volume
            volume = float(kline[7])
            volumes.append(volume)
        
        return volumes
    except Exception as e:
        return None

def calculate_stats(volumes):
    """Calculate volume statistics"""
    if not volumes or len(volumes) < 2:
        return None
    
    yesterday_volume = volumes[-1]
    avg_volume = sum(volumes[:-1]) / len(volumes[:-1])  # Average excluding yesterday
    
    if avg_volume == 0:
        return None
    
    volume_change_pct = ((yesterday_volume - avg_volume) / avg_volume) * 100
    
    return {
        'yesterday': yesterday_volume,
        'average': avg_volume,
        'change_pct': volume_change_pct
    }

def scan_for_unusual_volume(min_volume_change=50, limit=50):
    """Scan for unusual volume on small caps"""
    print('\n' + '='*70)
    print('BINANCE SMALL CAP VOLUME SCANNER')
    print('='*70)
    print(f'Scanning for coins with >{min_volume_change}% volume increase...\n')
    
    tickers = get_binance_tickers()
    print(f'Found {len(tickers)} trading pairs. Scanning...\n')
    
    unusual_volume = []
    scanned = 0
    
    for symbol in tickers:
        scanned += 1
        if scanned % 50 == 0:
            print(f'Scanned {scanned}/{len(tickers)}...')
        
        volumes = get_historical_volume(symbol, days=14)
        
        if volumes is None or len(volumes) < 2:
            continue
        
        stats = calculate_stats(volumes)
        
        if stats is None:
            continue
        
        # Only interested in volume increases
        if stats['change_pct'] > min_volume_change:
            price = get_coin_price(symbol)
            
            unusual_volume.append({
                'symbol': symbol,
                'yesterday_volume': stats['yesterday'],
                'avg_volume': stats['average'],
                'volume_change_pct': stats['change_pct'],
                'price': price
            })
    
    # Sort by volume change percentage
    unusual_volume.sort(key=lambda x: x['volume_change_pct'], reverse=True)
    
    # Display results
    print(f'{"SYMBOL":<12} {"YESTERDAY VOL":<18} {"14D AVG":<18} {"CHANGE %":<12} {"PRICE":<10}')
    print('-'*70)
    
    for coin in unusual_volume[:limit]:
        symbol = coin['symbol'].replace('USDT', '')
        yesterday = f"${coin['yesterday_volume']/1_000_000:.2f}M"
        average = f"${coin['avg_volume']/1_000_000:.2f}M"
        change = f"+{coin['volume_change_pct']:.1f}%"
        price = f"${coin['price']:.6f}" if coin['price'] else "N/A"
        
        print(f'{symbol:<12} {yesterday:<18} {average:<18} {change:<12} {price:<10}')
    
    print('\n' + '='*70)
    print(f'Found {len(unusual_volume)} coins with unusual volume')
    print(f'Scanned: {scanned} pairs')
    print(f'Updated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*70 + '\n')
    
    return unusual_volume

if __name__ == '__main__':
    # Scan for coins with >50% volume increase (adjust as needed)
    results = scan_for_unusual_volume(min_volume_change=50, limit=20)
