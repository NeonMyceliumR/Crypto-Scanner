"""
Kraken Pro Trade History Extractor
===================================
For Pythonista 3 (iOS) and standard Python 3.6+

Fetches your complete trade history from Kraken and displays:
  - Entry/exit time
  - Symbol (pair)
  - Side (buy/sell)
  - Price
  - Size (volume)
  - Fee
  - Cost (price * size)
  - Realized P&L (net field, where available)

Usage
-----
1. Generate a Kraken API key with "Query Funds" and "Query Closed Orders & Trades"
   permissions (read-only — no trading permission needed).
2. Set API_KEY and API_SECRET below, or leave them blank to be prompted at runtime.
3. Run the script.  Results are printed to the console and saved to
   kraken_trades.csv in the same directory.

Kraken API docs: https://docs.kraken.com/api/docs/rest-api/get-trade-history
"""

import hashlib
import hmac
import base64
import time
import urllib.parse
import csv
import os
from datetime import datetime

try:
    import requests
except ImportError:
    raise SystemExit("requests is not installed. Run: pip install requests")

# ---------------------------------------------------------------------------
# Configuration — fill in your keys here or leave blank to be prompted
# ---------------------------------------------------------------------------
API_KEY    = ""   # e.g. "XXXX..."
API_SECRET = ""   # e.g. "YYYY..."
# ---------------------------------------------------------------------------

BASE_URL = "https://api.kraken.com"


# ── Authentication helpers ──────────────────────────────────────────────────

def _nonce() -> str:
    """Return a strictly-increasing nonce (milliseconds since epoch)."""
    return str(int(time.time() * 1000))


def _sign(uri_path: str, data: dict, secret: str) -> str:
    """
    Build the Kraken API-Sign header value.

    Signature = HMAC-SHA512(
        uri_path + SHA256(nonce + url_encoded_post_body),
        base64_decoded_secret
    )
    encoded as base64.
    """
    post_data = urllib.parse.urlencode(data)
    encoded   = (data["nonce"] + post_data).encode("utf-8")
    message   = uri_path.encode("utf-8") + hashlib.sha256(encoded).digest()
    mac       = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
    return base64.b64encode(mac.digest()).decode()


def _private_request(endpoint, api_key, api_secret, params=None):
    """POST to a private Kraken endpoint and return the parsed JSON."""
    uri_path = f"/0/private/{endpoint}"
    url      = BASE_URL + uri_path

    data = {"nonce": _nonce()}
    if params:
        data.update(params)

    headers = {
        "API-Key":  api_key,
        "API-Sign": _sign(uri_path, data, api_secret),
    }

    resp = requests.post(url, data=data, headers=headers, timeout=15)
    resp.raise_for_status()
    result = resp.json()

    if result.get("error"):
        raise RuntimeError(f"Kraken API error: {result['error']}")

    return result["result"]


# ── Trade fetching ──────────────────────────────────────────────────────────

def fetch_all_trades(api_key, api_secret):
    """
    Retrieve the full trade history, paging through results 50 at a time.
    Returns a list of trade dicts sorted by time (oldest first).
    """
    trades = {}
    offset = 0

    print("Fetching trade history from Kraken…")

    while True:
        result = _private_request(
            "TradesHistory",
            api_key,
            api_secret,
            {"ofs": offset},
        )

        batch = result.get("trades", {})
        if not batch:
            break

        trades.update(batch)
        count = result.get("count", len(trades))
        print(f"  Fetched {len(trades)} / {count} trades…")

        if len(trades) >= count:
            break

        offset += 50
        time.sleep(0.5)   # be polite to the rate-limiter

    # Convert to a flat list and sort chronologically
    trade_list = []
    for trade_id, t in trades.items():
        trade_list.append({**t, "trade_id": trade_id})

    trade_list.sort(key=lambda x: float(x.get("time", 0)))
    return trade_list


# ── Formatting helpers ──────────────────────────────────────────────────────

def _fmt_time(unix_ts: float) -> str:
    return datetime.utcfromtimestamp(unix_ts).strftime("%Y-%m-%d %H:%M:%S UTC")


def _fmt_pnl(value: str) -> str:
    try:
        f = float(value)
        return f"+{f:.4f}" if f >= 0 else f"{f:.4f}"
    except (TypeError, ValueError):
        return "n/a"


# ── Display ─────────────────────────────────────────────────────────────────

def print_trades(trades):
    """Print a formatted table of trades to stdout."""
    col = {
        "time":   26,
        "pair":   12,
        "side":    6,
        "price":  14,
        "vol":    14,
        "cost":   14,
        "fee":    10,
        "pnl":    12,
    }

    header = (
        f"{'TIME':<{col['time']}}"
        f"{'PAIR':<{col['pair']}}"
        f"{'SIDE':<{col['side']}}"
        f"{'PRICE':>{col['price']}}"
        f"{'SIZE':>{col['vol']}}"
        f"{'COST':>{col['cost']}}"
        f"{'FEE':>{col['fee']}}"
        f"{'REALIZED P&L':>{col['pnl']}}"
    )
    sep = "─" * len(header)

    print(f"\n{sep}")
    print("  KRAKEN TRADE HISTORY")
    print(sep)
    print(header)
    print(sep)

    for t in trades:
        pnl_raw = t.get("net", t.get("misc", ""))
        print(
            f"{_fmt_time(float(t['time'])):<{col['time']}}"
            f"{t.get('pair',''):<{col['pair']}}"
            f"{t.get('type',''):<{col['side']}}"
            f"{float(t.get('price','0')):>{col['price']}.6f}"
            f"{float(t.get('vol','0')):>{col['vol']}.6f}"
            f"{float(t.get('cost','0')):>{col['cost']}.4f}"
            f"{float(t.get('fee','0')):>{col['fee']}.4f}"
            f"{_fmt_pnl(pnl_raw):>{col['pnl']}}"
        )

    print(sep)
    print(f"  Total trades: {len(trades)}")
    print(sep + "\n")


# ── CSV export ───────────────────────────────────────────────────────────────

def export_csv(trades, path):
    """Write trades to a CSV file."""
    fieldnames = [
        "trade_id", "time_utc", "unix_time",
        "pair", "side", "order_type",
        "price", "volume", "cost", "fee",
        "realized_pnl", "order_id",
    ]

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for t in trades:
            writer.writerow({
                "trade_id":    t.get("trade_id", ""),
                "time_utc":    _fmt_time(float(t["time"])),
                "unix_time":   t.get("time", ""),
                "pair":        t.get("pair", ""),
                "side":        t.get("type", ""),
                "order_type":  t.get("ordertype", ""),
                "price":       t.get("price", ""),
                "volume":      t.get("vol", ""),
                "cost":        t.get("cost", ""),
                "fee":         t.get("fee", ""),
                "realized_pnl": t.get("net", ""),
                "order_id":    t.get("ordertxid", ""),
            })

    print(f"Saved {len(trades)} trades → {path}")


# ── Entry point ──────────────────────────────────────────────────────────────

def main():
    key    = API_KEY    or input("Kraken API Key:    ").strip()
    secret = API_SECRET or input("Kraken API Secret: ").strip()

    if not key or not secret:
        raise SystemExit("API key and secret are required.")

    trades = fetch_all_trades(key, secret)

    if not trades:
        print("No trades found.")
        return

    print_trades(trades)

    # Save CSV next to this script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path   = os.path.join(script_dir, "kraken_trades.csv")
    export_csv(trades, csv_path)


if __name__ == "__main__":
    main()
