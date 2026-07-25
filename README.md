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

---

## Trade Journal — Mistake Analysis Engine

`trade_journal.py` is a companion module that turns raw trade logs into behavioural intelligence. Every trade is tagged with the mistakes that occurred, and a statistical engine surfaces which habits are actually costing you money.

### Mistake checkboxes

Each trade can be tagged with any combination of:

| Key | Label |
|-----|-------|
| `entered_early` | Enter early |
| `entered_late` | Enter late |
| `moved_stop` | Move the stop |
| `increased_size` | Oversize the position |
| `revenge_trade` | Revenge trade |
| `broke_plan` | Break the plan |
| `ignored_signal` | Ignore a signal |
| `emotional` | Trade emotionally |
| `fomo` | FOMO in |
| `took_partial_profit_early` | Take partial profit early |

### Statistical engine

For every mistake the engine computes:

- **Win rate** with the mistake present vs. absent
- **Average PnL** with the mistake present vs. absent
- **Chi-square test** — is the relationship statistically significant?
- **Phi coefficient** — how strong is the relationship?
- **Trend** — is this mistake improving or worsening over time?

Insights are then translated into plain English and ranked by PnL impact, for example:

> *When you Trade emotionally, your win rate drops from 57% to 0% (5 of 40 trades flagged). Average PnL: $-36.59 with this mistake vs $+4.88 without (-41.47 per trade). This is statistically significant — the relationship is strong (φ=-0.38, p=0.017). Watch out: this behaviour is getting worse over time.*

### Usage

```bash
# Log a completed trade interactively
python trade_journal.py log

# Full behavioural report (all time)
python trade_journal.py report

# Report restricted to the last 30 days
python trade_journal.py report 30
```

### Log trades programmatically

```python
from trade_journal import log_trade, print_mistake_report

log_trade(
    symbol='BTCUSDT',
    entry_price=30000,
    exit_price=29100,
    size_usd=1000,
    mistakes=['revenge_trade', 'emotional'],
    notes='Chased a loss after getting stopped out'
)

print_mistake_report()
```

Trades are stored locally in `trades.json` — no external services required.

---

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
