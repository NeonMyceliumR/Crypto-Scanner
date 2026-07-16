# Crypto Volume Scanner

Find unusual trading volume on small-cap coins before the move happens.

## What It Does

Scans 2000+ trading pairs on Binance and identifies coins with abnormal volume spikes compared to their 14-day average. Perfect for spotting potential breakouts and unusual market activity.

## Features

✨ **Scans 2000+ Binance trading pairs**
- Analyzes 14 days of historical data
- Calculates average daily volume
- Identifies volume anomalies
- Shows % change from baseline
- Displays current price for each coin
- Customizable filters

## Example Output

```
BINANCE SMALL CAP VOLUME SCANNER
======================================================================

SYMBOL       YESTERDAY VOL      14D AVG            CHANGE %     PRICE
-----------  ---------------    ---------------    ----------   --------
OPN          $850k              $125k              +580%        $0.002341
SHIB         $2.1M              $400k              +425%        $0.000089
DOGE         $1.5M              $950k              +58%         $0.156
```

## Installation

### On Pythonista (iOS)
1. Copy `scanner.py` to your Pythonista app
2. Run the script

### On Desktop/Linux/Mac
```bash
git clone https://github.com/NeonMyceliumR/Crypto-Scanner.git
cd Crypto-Scanner
pip install requests
python scanner.py
```

## Usage

### Basic (Default settings)
```python
python scanner.py
```

### Custom parameters
```python
from scanner import scan_for_unusual_volume

# Find coins with >100% volume increase, show top 10
results = scan_for_unusual_volume(min_volume_change=100, limit=10)
```

## Parameters

- `min_volume_change` (default: 50) - Minimum % increase from 14-day average
- `limit` (default: 50) - Number of results to display

### Examples

**Find aggressive volume spikes:**
```python
scan_for_unusual_volume(min_volume_change=200, limit=5)
```

**Broader scan (more results):**
```python
scan_for_unusual_volume(min_volume_change=25, limit=100)
```

## How It Works

1. Fetches all USDT trading pairs from Binance
2. Gets 14 days of daily volume data for each pair
3. Calculates average volume (excluding today)
4. Compares yesterday's volume to the average
5. Ranks by % increase
6. Displays top results with current price

## Requirements

- Python 3.6+
- `requests` library
- Internet connection
- Binance API access (free)

## Installation (Python)

```bash
pip install requests
```

## Performance

- **Scan time:** ~2-3 minutes (scans all 2000+ pairs)
- **Data freshness:** Yesterday's closing volume
- **API calls:** ~2000 (within Binance rate limits)

## Customization

### Adjust scan intensity
```python
# More conservative - only major spikes
min_volume_change=150

# More aggressive - catch early moves
min_volume_change=25
```

### Limit results
```python
# Show top 5
limit=5

# Show top 100
limit=100
```

## API Information

This tool uses the **free Binance REST API** (no authentication required):
- `https://api.binance.com/api/v3/exchangeInfo` - Get all pairs
- `https://api.binance.com/api/v3/klines` - Get historical volume
- `https://api.binance.com/api/v3/ticker/24hr` - Get current prices

**Rate Limits:** 1200 requests per minute (more than enough for this tool)

## Disclaimers

⚠️ **IMPORTANT:**
- This tool is for informational purposes only
- Not financial advice - always do your own research (DYOR)
- Past volume doesn't guarantee future results
- Crypto trading is risky - only invest what you can afford to lose
- This tool scans Binance only; other exchanges may have different activity

## Roadmap

- [ ] Multi-exchange support (Kraken, Coinbase, etc.)
- [ ] Alert system (email/Discord notifications)
- [ ] Historical tracking (log results over time)
- [ ] Price action filters (combine with technical analysis)
- [ ] Web dashboard
- [ ] Mobile app

## Contributing

Got ideas? Found a bug? Feel free to:
- Open an issue
- Submit a pull request
- Suggest features

## License

MIT License - Use freely, modify, and distribute

## Author

**NeonMyceliumR** - Crypto scanner enthusiast 🍄📊

## Support

If you find this useful, consider:
- Starring the repo ⭐
- Sharing with other traders
- Contributing improvements
- Sponsoring development

---

**Questions?** Open an issue and I'll help!
