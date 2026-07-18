#!/usr/bin/env python3
"""
ETH & BTC Large Buy Alert Monitor
Real-time detection of large buying volume spikes
Mobile-Friendly Alerts
"""

import requests
import json
from datetime import datetime, timedelta
import statistics
import time

def get_klines(symbol='ETHUSDT', interval='1m', limit=60):
    """Get candlestick data from Binance"""
    try:
        url = 'https://api.binance.com/api/v3/klines'
        params = {
            'symbol': symbol,
            'interval': interval,
            'limit': limit
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f'ERROR fetching {symbol}: {e}')
        return None

def analyze_buy_volume(klines):
    """Analyze buy vs sell volume"""
    if not klines or len(klines) < 2:
        return None
    
    analysis = {
        'total_volume': 0,
        'buy_volume': 0,
        'sell_volume': 0,
        'buy_ratio': 0,
        'current_price': 0,
        'candles': []
    }
    
    for kline in klines:
        open_price = float(kline[1])
        close_price = float(kline[4])
        high = float(kline[2])
        low = float(kline[3])
        volume = float(kline[7])
        time_str = datetime.fromtimestamp(int(kline[0])/1000).strftime("%H:%M")
        
        analysis['total_volume'] += volume
        analysis['current_price'] = close_price
        
        # Estimate buy/sell based on close position
        if close_price > open_price:
            estimated_buy = volume * ((close_price - open_price) / (high - low)) if (high - low) > 0 else volume * 0.5
            analysis['buy_volume'] += estimated_buy
        else:
            estimated_sell = volume * ((open_price - close_price) / (high - low)) if (high - low) > 0 else volume * 0.5
            analysis['sell_volume'] += estimated_sell
        
        analysis['candles'].append({
            'time': time_str,
            'open': open_price,
            'close': close_price,
            'high': high,
            'low': low,
            'volume': volume,
            'is_buy_candle': close_price > open_price
        })
    
    analysis['buy_ratio'] = (analysis['buy_volume'] / analysis['total_volume']) * 100 if analysis['total_volume'] > 0 else 0
    
    return analysis

def detect_large_buy(klines, threshold_multiplier=2.0):
    """Detect unusually large buy volume"""
    if not klines or len(klines) < 10:
        return None
    
    volumes = [float(k[7]) for k in klines]
    avg_volume = sum(volumes[:-1]) / len(volumes[:-1])  # Exclude current
    current_volume = volumes[-1]
    
    current_kline = klines[-1]
    open_price = float(current_kline[1])
    close_price = float(current_kline[4])
    high = float(current_kline[2])
    low = float(current_kline[3])
    
    # Is it a buy candle?
    is_buy_candle = close_price > open_price
    
    # Volume surge?
    volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
    is_volume_spike = volume_ratio > threshold_multiplier
    
    # Price movement
    price_change = ((close_price - open_price) / open_price) * 100 if open_price > 0 else 0
    
    return {
        'is_buy_candle': is_buy_candle,
        'is_volume_spike': is_volume_spike,
        'volume_ratio': volume_ratio,
        'current_volume': current_volume,
        'avg_volume': avg_volume,
        'current_price': close_price,
        'price_change_pct': price_change,
        'alert_strength': volume_ratio if (is_buy_candle and is_volume_spike) else 0
    }

def monitor_eth_btc_alerts(check_interval=60, duration_minutes=30):
    """Monitor ETH and BTC for large buys"""
    print('\n')
    print('='*60)
    print('ETH & BTC LARGE BUY MONITOR')
    print('='*60)
    print(f'Monitoring 1-minute candles for large buys')
    print(f'Check interval: {check_interval}s')
    print(f'Duration: {duration_minutes} minutes')
    print('='*60)
    print()
    
    start_time = time.time()
    duration_seconds = duration_minutes * 60
    alert_count = {'ETH': 0, 'BTC': 0}
    
    while time.time() - start_time < duration_seconds:
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Check ETH
        eth_klines = get_klines(symbol='ETHUSDT', interval='1m', limit=60)
        if eth_klines:
            eth_alert = detect_large_buy(eth_klines, threshold_multiplier=2.0)
            if eth_alert and eth_alert['alert_strength'] > 0:
                alert_count['ETH'] += 1
                print(f'\n🚨 [{timestamp}] LARGE ETH BUY DETECTED!')
                print('-' * 60)
                print(f'Price: ${eth_alert["current_price"]:.2f}')
                print(f'Volume: {eth_alert["volume_ratio"]:.2f}x average')
                print(f'Current Vol: ${eth_alert["current_volume"]/1e6:.2f}M')
                print(f'Avg Vol: ${eth_alert["avg_volume"]/1e6:.2f}M')
                print(f'Price Change: {eth_alert["price_change_pct"]:+.2f}%')
                print(f'Alert Strength: {eth_alert["alert_strength"]:.2f}/5')
                print()
        
        # Check BTC
        btc_klines = get_klines(symbol='BTCUSDT', interval='1m', limit=60)
        if btc_klines:
            btc_alert = detect_large_buy(btc_klines, threshold_multiplier=2.0)
            if btc_alert and btc_alert['alert_strength'] > 0:
                alert_count['BTC'] += 1
                print(f'\n🚨 [{timestamp}] LARGE BTC BUY DETECTED!')
                print('-' * 60)
                print(f'Price: ${btc_alert["current_price"]:.2f}')
                print(f'Volume: {btc_alert["volume_ratio"]:.2f}x average')
                print(f'Current Vol: ${btc_alert["current_volume"]/1e6:.2f}M')
                print(f'Avg Vol: ${btc_alert["avg_volume"]/1e6:.2f}M')
                print(f'Price Change: {btc_alert["price_change_pct"]:+.2f}%')
                print(f'Alert Strength: {btc_alert["alert_strength"]:.2f}/5')
                print()
        
        # Sleep before next check
        time.sleep(check_interval)
    
    print()
    print('='*60)
    print('MONITORING COMPLETE')
    print(f'Total Alerts: ETH={alert_count["ETH"]}, BTC={alert_count["BTC"]}')
    print('='*60)
    print()

def single_check():
    """Single check (no loop)"""
    print('\n')
    print('='*60)
    print('ETH & BTC LARGE BUY CHECK')
    print('='*60)
    print()
    
    timestamp = datetime.now().strftime("%m/%d %H:%M:%S")
    
    # ETH Check
    print('ETH ANALYSIS')
    print('-' * 60)
    eth_klines = get_klines(symbol='ETHUSDT', interval='1m', limit=60)
    if eth_klines:
        eth_data = analyze_buy_volume(eth_klines)
        eth_alert = detect_large_buy(eth_klines, threshold_multiplier=2.0)
        
        print(f'Price: ${eth_alert["current_price"]:.2f}')
        print(f'Buy Ratio: {eth_data["buy_ratio"]:.1f}%')
        print(f'Current Volume: ${eth_alert["current_volume"]/1e6:.2f}M')
        print(f'Avg Volume: ${eth_alert["avg_volume"]/1e6:.2f}M')
        print(f'Volume Ratio: {eth_alert["volume_ratio"]:.2f}x')
        print(f'Price Change: {eth_alert["price_change_pct"]:+.2f}%')
        
        if eth_alert['alert_strength'] > 0:
            print(f'⚠️  LARGE BUY - Alert Strength: {eth_alert["alert_strength"]:.2f}/5')
        else:
            print('Status: Normal')
    print()
    
    # BTC Check
    print('BTC ANALYSIS')
    print('-' * 60)
    btc_klines = get_klines(symbol='BTCUSDT', interval='1m', limit=60)
    if btc_klines:
        btc_data = analyze_buy_volume(btc_klines)
        btc_alert = detect_large_buy(btc_klines, threshold_multiplier=2.0)
        
        print(f'Price: ${btc_alert["current_price"]:.2f}')
        print(f'Buy Ratio: {btc_data["buy_ratio"]:.1f}%')
        print(f'Current Volume: ${btc_alert["current_volume"]/1e6:.2f}M')
        print(f'Avg Volume: ${btc_alert["avg_volume"]/1e6:.2f}M')
        print(f'Volume Ratio: {btc_alert["volume_ratio"]:.2f}x')
        print(f'Price Change: {btc_alert["price_change_pct"]:+.2f}%')
        
        if btc_alert['alert_strength'] > 0:
            print(f'⚠️  LARGE BUY - Alert Strength: {btc_alert["alert_strength"]:.2f}/5')
        else:
            print('Status: Normal')
    print()
    
    print('='*60)
    print(f'Updated: {timestamp}')
    print('='*60)
    print()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'monitor':
        # Run continuous monitoring
        # Usage: python eth_btc_alerts.py monitor
        monitor_eth_btc_alerts(check_interval=60, duration_minutes=30)
    else:
        # Single check
        single_check()
