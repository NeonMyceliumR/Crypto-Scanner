#!/usr/bin/env python3
"""
Cardano (ADA) Buying Activity Analyzer
Mobile-Friendly Version with Breakout Detection
Analyzes consolidation, buying pressure, and breakout potential
"""

import requests
import json
from datetime import datetime, timedelta
import statistics

def get_cardano_klines(interval='1d', limit=60):
    """Get Cardano (ADA/USDT) candlestick data from Binance"""
    try:
        url = 'https://api.binance.com/api/v3/klines'
        params = {
            'symbol': 'ADAUSDT',
            'interval': interval,
            'limit': limit
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f'ERROR: Could not fetch Cardano data: {e}')
        return None

def analyze_buying_pressure(klines):
    """Analyze buying pressure from volume and price action"""
    if not klines or len(klines) < 2:
        return None
    
    analysis = {
        'total_volume': 0,
        'buy_volume': 0,
        'sell_volume': 0,
        'avg_volume': 0,
        'buy_pressure_ratio': 0,
        'price_range': {'high': 0, 'low': float('inf')},
        'consolidation_score': 0,
        'volatility': 0
    }
    
    closes = []
    volumes = []
    
    for kline in klines:
        open_price = float(kline[1])
        close_price = float(kline[4])
        high = float(kline[2])
        low = float(kline[3])
        volume = float(kline[7])
        
        closes.append(close_price)
        volumes.append(volume)
        
        analysis['total_volume'] += volume
        analysis['price_range']['high'] = max(analysis['price_range']['high'], high)
        analysis['price_range']['low'] = min(analysis['price_range']['low'], low)
        
        if close_price > open_price:
            analysis['buy_volume'] += volume * ((close_price - open_price) / (high - low)) if (high - low) > 0 else volume * 0.5
        else:
            analysis['sell_volume'] += volume * ((open_price - close_price) / (high - low)) if (high - low) > 0 else volume * 0.5
    
    analysis['avg_volume'] = analysis['total_volume'] / len(klines)
    analysis['buy_pressure_ratio'] = (analysis['buy_volume'] / analysis['total_volume']) * 100 if analysis['total_volume'] > 0 else 0
    
    if len(closes) > 1:
        std_dev = statistics.stdev(closes)
        mean_close = statistics.mean(closes)
        analysis['volatility'] = (std_dev / mean_close) * 100 if mean_close > 0 else 0
        analysis['consolidation_score'] = 100 - analysis['volatility']
    
    return analysis

def get_recent_activity(klines, days=7):
    """Analyze recent activity (last 7 days)"""
    if not klines:
        return None
    
    recent = klines[-days:] if len(klines) >= days else klines
    
    recent_volume = sum([float(k[7]) for k in recent])
    overall_volume = sum([float(k[7]) for k in klines])
    
    recent_closes = [float(k[4]) for k in recent]
    recent_trend = "UP" if recent_closes[-1] > recent_closes[0] else "DOWN"
    recent_change_pct = ((recent_closes[-1] - recent_closes[0]) / recent_closes[0]) * 100
    
    return {
        'recent_volume': recent_volume,
        'volume_vs_average': (recent_volume / (overall_volume / len(klines))) * 100,
        'trend': recent_trend,
        'change_pct': recent_change_pct,
        'days_analyzed': len(recent),
        'current_price': recent_closes[-1]
    }

def detect_consolidation_pattern(klines):
    """Detect if price is consolidating (range-bound)"""
    if not klines or len(klines) < 10:
        return None
    
    closes = [float(k[4]) for k in klines[-20:]]
    
    high = max(closes)
    low = min(closes)
    range_size = high - low
    mid = (high + low) / 2
    
    consolidated_closes = sum(1 for c in closes if low + (range_size * 0.1) < c < high - (range_size * 0.1))
    consolidation_pct = (consolidated_closes / len(closes)) * 100
    
    return {
        'range_high': high,
        'range_low': low,
        'range_size': range_size,
        'range_midpoint': mid,
        'consolidation_percentage': consolidation_pct,
        'is_consolidating': consolidation_pct > 60
    }

def detect_breakout_potential(klines):
    """Detect if price is poised for breakout"""
    if not klines or len(klines) < 20:
        return None
    
    # Get last 20 candles
    recent_closes = [float(k[4]) for k in klines[-20:]]
    recent_highs = [float(k[2]) for k in klines[-20:]]
    recent_lows = [float(k[3]) for k in klines[-20:]]
    recent_volumes = [float(k[7]) for k in klines[-20:]]
    
    current_price = recent_closes[-1]
    current_high = recent_highs[-1]
    current_low = recent_lows[-1]
    current_volume = recent_volumes[-1]
    
    # Range highs/lows
    range_high = max(recent_highs)
    range_low = min(recent_lows)
    
    # Volume analysis
    avg_volume = sum(recent_volumes) / len(recent_volumes)
    volume_surge = current_volume > avg_volume * 1.5
    
    # Position in range (0-1, where 1 is at top)
    range_size = range_high - range_low
    position_in_range = (current_price - range_low) / range_size if range_size > 0 else 0.5
    
    # Momentum (last 3 closes trending up)
    momentum_up = recent_closes[-1] > recent_closes[-2] > recent_closes[-3]
    
    # Distance to resistance
    distance_to_resistance = range_high - current_price
    resistance_pct = (distance_to_resistance / current_price) * 100 if current_price > 0 else 0
    
    # Support
    distance_to_support = current_price - range_low
    support_pct = (distance_to_support / current_price) * 100 if current_price > 0 else 0
    
    # Breakout score
    breakout_score = 0
    if position_in_range > 0.7:
        breakout_score += 25
    if volume_surge:
        breakout_score += 25
    if momentum_up:
        breakout_score += 25
    if resistance_pct < 2:  # Very close to resistance
        breakout_score += 25
    
    return {
        'current_price': current_price,
        'resistance': range_high,
        'support': range_low,
        'distance_to_resistance': distance_to_resistance,
        'resistance_pct': resistance_pct,
        'distance_to_support': distance_to_support,
        'support_pct': support_pct,
        'position_in_range': position_in_range,
        'volume_surge': volume_surge,
        'current_volume': current_volume,
        'avg_volume': avg_volume,
        'volume_ratio': current_volume / avg_volume if avg_volume > 0 else 0,
        'momentum_up': momentum_up,
        'breakout_score': breakout_score,
        'likely_breakout': breakout_score >= 50
    }

def analyze_cardano_mobile():
    """Main analysis function (mobile-friendly)"""
    print('\n')
    print('='*50)
    print('CARDANO ADA ANALYSIS')
    print('='*50)
    print()
    
    print('Fetching data...')
    klines = get_cardano_klines(interval='1d', limit=60)
    
    if not klines:
        print('ERROR: Could not get data')
        return
    
    print('Analyzing...\n')
    
    # Overall analysis
    overall = analyze_buying_pressure(klines)
    recent = get_recent_activity(klines, days=7)
    consolidation = detect_consolidation_pattern(klines)
    breakout = detect_breakout_potential(klines)
    
    # CURRENT PRICE
    print('CURRENT PRICE')
    print('-' * 50)
    print(f'ADA: ${recent["current_price"]:.4f}')
    print()
    
    # RANGE INFO
    print('RANGE (Last 20 days)')
    print('-' * 50)
    print(f'Resistance: ${consolidation["range_high"]:.4f}')
    print(f'Support:    ${consolidation["range_low"]:.4f}')
    print(f'Range Size: ${consolidation["range_size"]:.4f}')
    print(f'Midpoint:   ${consolidation["range_midpoint"]:.4f}')
    print()
    
    # DISTANCE TO RESISTANCE/SUPPORT
    print('DISTANCE TO LEVELS')
    print('-' * 50)
    print(f'To Resist: ${breakout["distance_to_resistance"]:.4f} ({breakout["resistance_pct"]:.2f}%)')
    print(f'To Support: ${breakout["distance_to_support"]:.4f} ({breakout["support_pct"]:.2f}%)')
    position_text = f"{breakout['position_in_range']*100:.0f}%"
    print(f'Position: {position_text} (0%=Support, 100%=Resist)')
    print()
    
    # CONSOLIDATION
    print('CONSOLIDATION STATUS')
    print('-' * 50)
    consol_text = "YES ✓" if consolidation["is_consolidating"] else "NO"
    print(f'Consolidating: {consol_text}')
    print(f'Score: {consolidation["consolidation_percentage"]:.0f}%')
    print()
    
    # BUYING PRESSURE
    print('BUYING PRESSURE')
    print('-' * 50)
    buy_pct = overall["buy_pressure_ratio"]
    if buy_pct > 55:
        signal = "BULLISH ▲"
    elif buy_pct < 45:
        signal = "BEARISH ▼"
    else:
        signal = "NEUTRAL ●"
    print(f'Signal: {signal}')
    print(f'Ratio: {buy_pct:.1f}%')
    print()
    
    # VOLUME ANALYSIS
    print('VOLUME')
    print('-' * 50)
    vol_surge = "YES ↑" if breakout["volume_surge"] else "NO"
    print(f'Surge: {vol_surge}')
    print(f'Ratio: {breakout["volume_ratio"]:.2f}x avg')
    print()
    
    # RECENT ACTION
    print('RECENT (7 days)')
    print('-' * 50)
    print(f'Trend: {recent["trend"]}')
    print(f'Change: {recent["change_pct"]:+.2f}%')
    vol_status = "HIGH" if recent["volume_vs_average"] > 120 else "LOW" if recent["volume_vs_average"] < 80 else "NORMAL"
    print(f'Volume: {vol_status}')
    print()
    
    # KEY METRICS
    print('METRICS (60 days)')
    print('-' * 50)
    print(f'Vol: ${overall["total_volume"]/1e6:.1f}M')
    print(f'Avg: ${overall["avg_volume"]/1e6:.1f}M/day')
    print(f'Volatility: {overall["volatility"]:.1f}%')
    print()
    
    # BREAKOUT POTENTIAL
    print('BREAKOUT ANALYSIS')
    print('-' * 50)
    breakout_status = "LIKELY ▲" if breakout["likely_breakout"] else "UNLIKELY"
    print(f'Breakout Ready: {breakout_status}')
    print(f'Score: {breakout["breakout_score"]}/100')
    if breakout["momentum_up"]:
        print('✓ Momentum UP')
    else:
        print('✗ Momentum DOWN')
    print()
    
    # SETUP
    print('TRADING SETUP')
    print('-' * 50)
    
    if consolidation["is_consolidating"]:
        print('✓ CONSOLIDATING')
        if buy_pct > 52:
            print('✓ BULLISH BIAS')
            if breakout["likely_breakout"]:
                print('▲ BREAKOUT READY!')
                print(f'  Target: ${consolidation["range_high"]:.4f}')
                print(f'  Entry: On close above')
                print(f'  Stop: ${consolidation["range_midpoint"]:.4f}')
            else:
                print('→ Watch for breakout above')
                print(f'  ${consolidation["range_high"]:.4f}')
        elif buy_pct < 48:
            print('✓ BEARISH BIAS')
            print('→ Watch for breakdown below')
            print(f'  ${consolidation["range_low"]:.4f}')
        else:
            print('⚪ NEUTRAL BIAS')
            print('→ Awaiting directional move')
    else:
        print('✗ NOT CONSOLIDATING')
        if recent["trend"] == "UP":
            print('→ Trending UP')
        else:
            print('→ Trending DOWN')
    
    print()
    print('='*50)
    print(f'Updated: {datetime.now().strftime("%m/%d %H:%M UTC")}')
    print('='*50)
    print()

def quick_summary(klines):
    """Quick one-liner summary"""
    if not klines:
        return
    
    recent = get_recent_activity(klines, days=7)
    consolidation = detect_consolidation_pattern(klines)
    overall = analyze_buying_pressure(klines)
    breakout = detect_breakout_potential(klines)
    
    consol = "CONSOL" if consolidation["is_consolidating"] else "TREND"
    bias = "BULL" if overall["buy_pressure_ratio"] > 52 else "BEAR" if overall["buy_pressure_ratio"] < 48 else "NEUT"
    bo = "BO!" if breakout["likely_breakout"] else ""
    
    print(f'\nADA: ${recent["current_price"]:.4f} | {consol} | {bias} | Vol: {recent["volume_vs_average"]:.0f}% {bo}\n')

if __name__ == '__main__':
    # Full analysis
    analyze_cardano_mobile()
    
    # Uncomment for quick summary instead:
    # klines = get_cardano_klines(interval='1d', limit=60)
    # quick_summary(klines)
