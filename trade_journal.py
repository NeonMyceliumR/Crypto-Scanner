#!/usr/bin/env python3
"""
Trade Journal - Mistake Analysis Engine

Logs trades with behavioural mistake tags and uncovers statistical patterns
unique to each trader. Answers:
  * Is this statistically significant?
  * How strong is the relationship?
  * Has it changed over time?
  * Is this improving or deteriorating?

Usage
-----
  python trade_journal.py log           # log a new trade interactively
  python trade_journal.py report        # full report (all time)
  python trade_journal.py report 30     # report for last 30 days
"""

import json
import math
import os
import statistics
from datetime import datetime, timedelta

JOURNAL_FILE = 'trades.json'

# Canonical mistake keys and their display labels
MISTAKES = [
    'entered_early',
    'entered_late',
    'moved_stop',
    'increased_size',
    'revenge_trade',
    'broke_plan',
    'ignored_signal',
    'emotional',
    'fomo',
    'took_partial_profit_early',
]

MISTAKE_LABELS = {
    'entered_early':             'Enter early',
    'entered_late':              'Enter late',
    'moved_stop':                'Move the stop',
    'increased_size':            'Oversize the position',
    'revenge_trade':             'Revenge trade',
    'broke_plan':                'Break the plan',
    'ignored_signal':            'Ignore a signal',
    'emotional':                 'Trade emotionally',
    'fomo':                      'FOMO in',
    'took_partial_profit_early': 'Take partial profit early',
}


# ── Storage ───────────────────────────────────────────────────────────────────

def load_trades():
    """Load trades from the journal file."""
    if not os.path.exists(JOURNAL_FILE):
        return []
    with open(JOURNAL_FILE, 'r') as f:
        return json.load(f)


def save_trades(trades):
    """Persist trades to the journal file."""
    with open(JOURNAL_FILE, 'w') as f:
        json.dump(trades, f, indent=2)


# ── Trade logging ─────────────────────────────────────────────────────────────

def log_trade(symbol, entry_price, exit_price, size_usd, mistakes=None, notes=''):
    """
    Log a completed trade.

    Parameters
    ----------
    symbol      : str   Trading pair, e.g. 'BTCUSDT'
    entry_price : float Entry price
    exit_price  : float Exit price
    size_usd    : float Position size in USDT
    mistakes    : list  Subset of MISTAKES keys; None or [] = clean trade
    notes       : str   Optional freeform notes
    """
    if mistakes is None:
        mistakes = []

    invalid = [m for m in mistakes if m not in MISTAKES]
    if invalid:
        raise ValueError(f'Unknown mistake(s): {invalid}. Valid keys: {MISTAKES}')

    pnl = (exit_price - entry_price) / entry_price * size_usd
    won = pnl > 0

    trades = load_trades()
    trade = {
        'id':        (max(t['id'] for t in trades) + 1) if trades else 1,
        'timestamp': datetime.now().isoformat(),
        'symbol':    symbol.upper(),
        'entry':     entry_price,
        'exit':      exit_price,
        'size_usd':  size_usd,
        'pnl':       round(pnl, 2),
        'won':       won,
        'mistakes':  mistakes,
        'notes':     notes,
    }

    trades.append(trade)
    save_trades(trades)
    print(f'Trade logged: {symbol.upper()} | PnL ${pnl:+.2f} | '
          f'Mistakes: {", ".join(MISTAKE_LABELS[m] for m in mistakes) or "none"}')
    return trade


# ── Statistics ────────────────────────────────────────────────────────────────

def _chi_square_p(chi2_stat):
    """
    Approximate p-value for chi-square with 1 degree of freedom.

    For χ²(1), the CDF is erf(√(x/2)), so the survival function is
    erfc(√(x/2)).  Note: √(x/2) == √x / √2, so the two equivalent
    forms are identical.
    """
    if chi2_stat <= 0:
        return 1.0
    return math.erfc(math.sqrt(chi2_stat / 2.0))


def _phi_coefficient(a, b, c, d):
    """
    Phi (φ) coefficient for a 2×2 contingency table.

    a = wins   with mistake      b = losses with mistake
    c = wins   without mistake   d = losses without mistake
    """
    denom = math.sqrt((a + b) * (c + d) * (a + c) * (b + d))
    if denom == 0:
        return 0.0
    return (a * d - b * c) / denom


def analyse_mistake(trades, mistake_key):
    """
    Compute statistics for a single mistake type.

    Returns a dict of metrics, or None when there are fewer than 2 trades
    on either side of the split (insufficient data).
    """
    with_m  = [t for t in trades if mistake_key in t['mistakes']]
    without = [t for t in trades if mistake_key not in t['mistakes']]

    # Require at least 5 trades on each side for reliable inference
    if len(with_m) < 5 or len(without) < 5:
        return None

    # 2×2 contingency table
    a = sum(1 for t in with_m  if t['won'])   # wins   with mistake
    b = len(with_m)  - a                       # losses with mistake
    c = sum(1 for t in without if t['won'])    # wins   without
    d = len(without) - c                       # losses without

    n = len(trades)
    denom_chi = (a + b) * (c + d) * (a + c) * (b + d)
    chi2 = (n * (a * d - b * c) ** 2 / denom_chi) if denom_chi else 0.0

    win_rate_with    = a / len(with_m)
    win_rate_without = c / len(without)
    avg_pnl_with     = statistics.mean(t['pnl'] for t in with_m)
    avg_pnl_without  = statistics.mean(t['pnl'] for t in without)

    phi = _phi_coefficient(a, b, c, d)
    p   = _chi_square_p(chi2)

    # Trend: compare mistake frequency in the first half vs second half of trades
    sorted_trades = sorted(trades, key=lambda t: t['timestamp'])
    mid        = len(sorted_trades) // 2
    early_half = sorted_trades[:mid]
    late_half  = sorted_trades[mid:]
    rate_early = sum(1 for t in early_half if mistake_key in t['mistakes']) / len(early_half) if early_half else 0
    rate_late  = sum(1 for t in late_half  if mistake_key in t['mistakes']) / len(late_half)  if late_half  else 0
    # Positive trend = mistake becoming more frequent over time.
    # Whether that is "worsening" or "improving" depends on the mistake's impact.
    trend = rate_late - rate_early

    return {
        'mistake':          mistake_key,
        'label':            MISTAKE_LABELS[mistake_key],
        'count':            len(with_m),
        'total_trades':     n,
        'win_rate_with':    round(win_rate_with,    4),
        'win_rate_without': round(win_rate_without, 4),
        'avg_pnl_with':     round(avg_pnl_with,     2),
        'avg_pnl_without':  round(avg_pnl_without,  2),
        'chi2':             round(chi2, 4),
        'p_value':          round(p,    4),
        'significant':      p < 0.05,
        'phi':              round(phi,  4),
        'trend':            round(trend, 4),
    }


# ── Plain-English insights ────────────────────────────────────────────────────

def _strength_label(phi):
    """Map phi coefficient magnitude to a verbal strength description."""
    a = abs(phi)
    if a >= 0.5:
        return 'very strong'
    if a >= 0.3:
        return 'strong'
    if a >= 0.15:
        return 'moderate'
    return 'weak'


def generate_insight(stat):
    """Translate a mistake-stat dict into plain English."""
    label        = stat['label']
    wr_with      = stat['win_rate_with']    * 100
    wr_without   = stat['win_rate_without'] * 100
    pnl_with     = stat['avg_pnl_with']
    pnl_without  = stat['avg_pnl_without']
    sig          = stat['significant']
    phi          = stat['phi']
    trend        = stat['trend']
    count        = stat['count']
    n            = stat['total_trades']

    lines = []

    # Win-rate impact
    direction = 'drops' if wr_with < wr_without else 'improves'
    lines.append(
        f'When you {label}, your win rate {direction} from {wr_without:.0f}% '
        f'to {wr_with:.0f}% ({count} of {n} trades flagged).'
    )

    # P&L impact
    pnl_diff = pnl_with - pnl_without
    lines.append(
        f'Average PnL: ${pnl_with:+.2f} with this mistake vs '
        f'${pnl_without:+.2f} without ({pnl_diff:+.2f} per trade).'
    )

    # Statistical significance
    if sig:
        strength = _strength_label(phi)
        lines.append(
            f'This is statistically significant — the relationship is {strength} '
            f'(φ={phi:.2f}, p={stat["p_value"]:.3f}).'
        )
    else:
        lines.append(
            f'Not yet statistically significant (p={stat["p_value"]:.3f}) — '
            f'log more trades for a clearer signal.'
        )

    # Trend: becoming more frequent = worsening when mistake hurts, improving when it helps
    mistake_hurts = pnl_with < pnl_without
    if abs(trend) < 0.05:
        lines.append('The frequency of this behaviour has been stable over time.')
    elif (trend > 0) == mistake_hurts:
        lines.append('Watch out: this behaviour is getting worse over time.')
    else:
        lines.append('Good news: this behaviour is improving over time.')

    return ' '.join(lines)


# ── Full report ───────────────────────────────────────────────────────────────

def print_mistake_report(days=None):
    """
    Print a full mistake-analysis report.

    Parameters
    ----------
    days : int or None
        If provided, restrict analysis to the last N days.
    """
    trades = load_trades()

    if days is not None:
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        trades = [t for t in trades if t['timestamp'] >= cutoff]

    if not trades:
        print('No trades found. Log some trades first.')
        return

    total     = len(trades)
    wins      = sum(1 for t in trades if t['won'])
    total_pnl = sum(t['pnl'] for t in trades)

    print('\n' + '='*70)
    print('TRADE MISTAKE ANALYSIS REPORT')
    if days:
        print(f'Period: last {days} days')
    print('='*70)
    print(f'\nTotal trades : {total}')
    print(f'Win rate     : {wins / total * 100:.1f}%  ({wins}W / {total - wins}L)')
    print(f'Total PnL    : ${total_pnl:+.2f}')
    if total > 1:
        pnl_values = [t['pnl'] for t in trades]
        try:
            pnl_stdev = statistics.stdev(pnl_values)
            avg_pnl   = statistics.mean(pnl_values)
            expectancy_ratio = (avg_pnl / pnl_stdev) if pnl_stdev else float('inf')
            print(f'Avg PnL/trade: ${avg_pnl:+.2f}  |  PnL StDev: ${pnl_stdev:.2f}  |  Expectancy ratio: {expectancy_ratio:.2f}')
        except statistics.StatisticsError:
            pass

    # ── Mistake breakdown table ───────────────────────────────────────────────
    print('\n' + '-'*70)
    print('MISTAKE BREAKDOWN')
    print('-'*70)
    print(f'{"Mistake":<28} {"#":>4} {"WR-with":>8} {"WR-clean":>9} {"PnL-Δ":>8} {"p":>7} {"Sig":>4}')
    print('-'*70)

    insights = []
    for key in MISTAKES:
        label = MISTAKE_LABELS[key]
        count = sum(1 for t in trades if key in t['mistakes'])
        stat  = analyse_mistake(trades, key)

        if stat is None:
            print(f'{label:<28} {count:>4}  {"—":>7}  {"—":>8}  {"—":>7}  {"—":>6}  {"—":>3}')
            continue

        pnl_diff = stat['avg_pnl_with'] - stat['avg_pnl_without']
        sig_mark = '✓' if stat['significant'] else ''
        print(
            f'{label:<28} {stat["count"]:>4} '
            f'{stat["win_rate_with"] * 100:>7.1f}% '
            f'{stat["win_rate_without"] * 100:>8.1f}% '
            f'{pnl_diff:>+8.2f} '
            f'{stat["p_value"]:>7.3f} '
            f'{sig_mark:>4}'
        )
        insights.append((abs(pnl_diff), stat))

    # ── Top insights ──────────────────────────────────────────────────────────
    if insights:
        insights.sort(key=lambda x: x[0], reverse=True)
        print('\n' + '-'*70)
        print('TOP INSIGHTS  (ranked by PnL impact)')
        print('-'*70)
        for _, stat in insights[:5]:
            text = generate_insight(stat)
            print(f'\n  ▶ {stat["label"].upper()}')
            # Wrap long text for readability
            words  = text.split()
            line   = '    '
            for word in words:
                if len(line) + len(word) + 1 > 70:
                    print(line)
                    line = '    ' + word + ' '
                else:
                    line += word + ' '
            if line.strip():
                print(line)

    # ── Clean-trade summary ───────────────────────────────────────────────────
    clean = [t for t in trades if not t['mistakes']]
    if clean:
        clean_wins = sum(1 for t in clean if t['won'])
        clean_pnl  = sum(t['pnl'] for t in clean)
        print(f'\n{"─"*70}')
        print(f'Clean trades (no mistakes): {len(clean)}/{total} '
              f'| Win rate: {clean_wins / len(clean) * 100:.1f}% '
              f'| PnL: ${clean_pnl:+.2f}')

    print('\n' + '='*70)
    print(f'Report generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*70 + '\n')


# ── Interactive CLI ───────────────────────────────────────────────────────────

def interactive_log():
    """Walk the user through logging a trade interactively."""
    print('\n' + '='*60)
    print('LOG A TRADE')
    print('='*60)

    symbol      = input('Symbol (e.g. BTCUSDT): ').strip()
    entry_price = float(input('Entry price          : '))
    exit_price  = float(input('Exit price           : '))
    size_usd    = float(input('Position size (USDT) : '))

    print('\nMistakes made? Press Enter to skip, type y to mark.\n')
    mistakes = []
    for key, label in MISTAKE_LABELS.items():
        ans = input(f'  ☐  {label}? [y/N]: ').strip().lower()
        if ans == 'y':
            mistakes.append(key)

    notes = input('\nNotes (optional): ').strip()
    log_trade(symbol, entry_price, exit_price, size_usd, mistakes, notes)


def _print_usage():
    print('\nUsage:')
    print('  python trade_journal.py log           # log a new trade interactively')
    print('  python trade_journal.py report        # full report (all time)')
    print('  python trade_journal.py report 30     # report for last 30 days')
    print()


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        _print_usage()
    elif sys.argv[1] == 'log':
        interactive_log()
    elif sys.argv[1] == 'report':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else None
        print_mistake_report(days=days)
    else:
        _print_usage()
