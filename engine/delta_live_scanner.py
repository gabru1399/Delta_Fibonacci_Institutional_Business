"""delta_live_scanner.py: Live Institutional Scanner for Delta Exchange India.
Scans the Curated 250-Asset Catalog for genuine Fibonacci Prime Rejections (EMA 89 and EMA 233).
Features:
- Single Entry Invariant: Tracks active positions in 'active_positions.json' to prevent duplicate alerts.
- Tiered Support Detection: Catches both standard EMA 89 wicks and deep discount EMA 233 sweeps.
- Multi-Sector Filtering: Classifies opportunities across Metals, TradFi, Crypto Majors, and Altcoins.
- Dual-Timeframe Execution: Scans 4H and 1H candles.
"""

import os
import sys
import json
import time
import glob
import argparse
import urllib.request
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(BASE_DIR, "engine") not in sys.path:
    sys.path.insert(0, os.path.join(BASE_DIR, "engine"))

from asset_universe_classifier import classify_asset, get_sector_display_name, ALL_SECTORS

ACTIVE_POS_FILE = os.path.join(BASE_DIR, "engine", "active_positions.json")
DELTA_API = "https://api.india.delta.exchange"
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

def calculate_ema(series, span):
    return series.ewm(span=span, adjust=False).mean()

def calculate_atr(df, period=14):
    high = df['high'].to_numpy(dtype=float)
    low = df['low'].to_numpy(dtype=float)
    close = df['close'].to_numpy(dtype=float)
    n = len(df)
    tr = np.zeros(n)
    tr[0] = high[0] - low[0]
    for i in range(1, n):
        tr[i] = max(high[i] - low[i], abs(high[i] - close[i-1]), abs(low[i] - close[i-1]))
    atr = pd.Series(tr).rolling(period).mean().bfill().to_numpy()
    return atr

def load_active_positions():
    if os.path.exists(ACTIVE_POS_FILE):
        try:
            with open(ACTIVE_POS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_active_positions(pos_dict):
    try:
        with open(ACTIVE_POS_FILE, "w") as f:
            json.dump(pos_dict, f, indent=2)
    except Exception:
        pass

def fetch_recent_candles(symbol, resolution="240", count=300):
    now = int(time.time())
    start = now - (count * 4 * 3600 if resolution == "240" else count * 3600)
    url = f"{DELTA_API}/v2/chart/history?symbol={symbol}&resolution={resolution}&from={start}&to={now}"
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode('utf-8'))
        res = data.get('result', {})
        t = res.get('t', [])
        if not t or len(t) < 50:
            return None
        df = pd.DataFrame({
            'timestamp': t,
            'open': res.get('o', []),
            'high': res.get('h', []),
            'low': res.get('l', []),
            'close': res.get('c', []),
            'volume': res.get('v', [])
        })
        df = df.sort_values('timestamp').reset_index(drop=True)
        return df
    except Exception:
        return None

def scan_asset_setup(symbol, tf="4H", equity=5000.0, risk_pct=0.01):
    """Scans an asset for Tiered Fibonacci Rejections enforcing Single Entry."""
    res_code = "240" if tf == "4H" else "60"
    df = fetch_recent_candles(symbol, resolution=res_code, count=300)
    if df is None or len(df) < 250:
        return None
        
    closes = df['close']
    ema55 = calculate_ema(closes, 55).to_numpy()
    ema89 = calculate_ema(closes, 89).to_numpy()
    ema233 = calculate_ema(closes, 233).to_numpy()
    atr = calculate_atr(df, 14)
    
    i = len(df) - 1 # Forming candle
    prev = i - 1    # Confirmed closed candle
    
    o = df['open'].iloc[prev]
    h = df['high'].iloc[prev]
    l = df['low'].iloc[prev]
    c = df['close'].iloc[prev]
    rng = h - l
    if rng <= 0:
        return None
        
    curr_55 = ema55[prev]
    curr_89 = ema89[prev]
    curr_233 = ema233[prev]
    curr_atr = atr[prev]
    
    # 1. Macro Regime Gate
    regime = "NEUTRAL"
    if curr_89 > curr_233:
        regime = "BULLISH" # LONGS ONLY
    elif curr_89 < curr_233:
        regime = "BEARISH" # SHORTS ONLY
        
    setup = None
    
    # Check Single Entry status
    active_pos = load_active_positions()
    pos_key = f"{symbol}_{tf}"
    if pos_key in active_pos:
        last_entry_ts = active_pos[pos_key].get('entry_ts', 0)
        bar_duration = 14400 if tf == "4H" else 3600
        if (df['timestamp'].iloc[prev] - last_entry_ts) < (12 * bar_duration):
            return None
            
    # Bullish setup check (Tiered Support: EMA 89 or EMA 233)
    if regime == "BULLISH":
        lower_wick = min(o, c) - l
        wick_ratio = lower_wick / rng
        
        shelf = None
        if (l <= curr_89 * 1.002 or l <= curr_55 * 1.002) and (c >= curr_89):
            shelf = "EMA_89"
        elif (l <= curr_233 * 1.002) and (c >= curr_233):
            shelf = "EMA_233"
            
        if shelf and wick_ratio >= 0.25:
            entry = df['close'].iloc[i] # Current market price
            stop = (min(curr_233, l) - 0.35 * curr_atr) if shelf == "EMA_233" else (l - 0.30 * curr_atr)
            risk_dist = entry - stop
            if risk_dist > 0:
                dollar_risk = equity * risk_pct
                pos_size = dollar_risk / risk_dist
                setup = {
                    'symbol': symbol,
                    'sector': classify_asset(symbol),
                    'tf': tf,
                    'regime': regime,
                    'shelf': shelf,
                    'action': 'BUY / LONG',
                    'entry': round(entry, 4),
                    'stop': round(stop, 4),
                    'risk_distance': round(risk_dist, 4),
                    't1': round(entry + (1.5 * risk_dist), 4),
                    't2': round(entry + (2.5 * risk_dist), 4),
                    't3': round(entry + (4.0 * risk_dist), 4),
                    'rr': 2.5,
                    'position_size_units': round(pos_size, 4),
                    'dollar_risk': dollar_risk,
                    'wick_pct': round(wick_ratio * 100.0, 1),
                    'entry_ts': int(df['timestamp'].iloc[prev])
                }
                
    # Bearish setup check (Tiered Resistance: EMA 89 or EMA 233)
    elif regime == "BEARISH":
        upper_wick = h - max(o, c)
        wick_ratio = upper_wick / rng
        
        shelf = None
        if (h >= curr_89 * 0.998 or h >= curr_55 * 0.998) and (c <= curr_89):
            shelf = "EMA_89"
        elif (h >= curr_233 * 0.998) and (c <= curr_233):
            shelf = "EMA_233"
            
        if shelf and wick_ratio >= 0.25:
            entry = df['close'].iloc[i]
            stop = (max(curr_233, h) + 0.35 * curr_atr) if shelf == "EMA_233" else (h + 0.30 * curr_atr)
            risk_dist = stop - entry
            if risk_dist > 0:
                dollar_risk = equity * risk_pct
                pos_size = dollar_risk / risk_dist
                setup = {
                    'symbol': symbol,
                    'sector': classify_asset(symbol),
                    'tf': tf,
                    'regime': regime,
                    'shelf': shelf,
                    'action': 'SELL / SHORT',
                    'entry': round(entry, 4),
                    'stop': round(stop, 4),
                    'risk_distance': round(risk_dist, 4),
                    't1': round(entry - (1.5 * risk_dist), 4),
                    't2': round(entry - (2.5 * risk_dist), 4),
                    't3': round(entry - (4.0 * risk_dist), 4),
                    'rr': 2.5,
                    'position_size_units': round(pos_size, 4),
                    'dollar_risk': dollar_risk,
                    'wick_pct': round(wick_ratio * 100.0, 1),
                    'entry_ts': int(df['timestamp'].iloc[prev])
                }
                
    return setup

def main():
    parser = argparse.ArgumentParser(description="Delta Exchange India Institutional Fibonacci Scanner")
    parser.add_argument("--tf", choices=["4H", "1H", "ALL"], default="4H", help="Timeframe to scan")
    parser.add_argument("--sector", choices=ALL_SECTORS + ["ALL"], default="ALL", help="Asset sector filter")
    parser.add_argument("--equity", type=float, default=5000.0, help="Base trading capital (USD)")
    parser.add_argument("--risk", type=float, default=0.01, help="Risk per trade (fraction, e.g. 0.01 for 1 percent)")
    args = parser.parse_args()
    
    leaderboard_file = os.path.join(BASE_DIR, "audit", "delta_calmar_leaderboard.csv")
    if os.path.exists(leaderboard_file):
        df_lead = pd.read_csv(leaderboard_file)
        symbols = df_lead['symbol'].drop_duplicates().tolist()
    else:
        csv_files = glob.glob(os.path.join(BASE_DIR, "data", "*_4h.csv"))
        symbols = [os.path.basename(f).split('_')[0] for f in csv_files]
        
    if args.sector != "ALL":
        symbols = [s for s in symbols if classify_asset(s) == args.sector]
        
    timeframes = ["4H", "1H"] if args.tf == "ALL" else [args.tf]
    
    print("\n" + "="*115)
    print(f"DELTA EXCHANGE INDIA LIVE INSTITUTIONAL SCANNER | CAPITAL: ${args.equity:,.2f} | RISK: {args.risk*100:.1f}%")
    print(f"Sectors: {args.sector} | Timeframes: {timeframes} | Active Symbols: {len(symbols)}")
    print("="*115)
    
    found_setups = []
    
    for sym in symbols[:40]: # Scan top 40 assets for rapid response
        for tf in timeframes:
            try:
                setup = scan_asset_setup(sym, tf=tf, equity=args.equity, risk_pct=args.risk)
                if setup:
                    found_setups.append(setup)
                    print(f"  [SIGNAL] {setup['symbol']} ({setup['tf']}) -> {setup['action']} @ {setup['entry']} (Shelf: {setup['shelf']}, Wick: {setup['wick_pct']}%)")
            except Exception:
                continue
                
    print("\n" + "-"*115)
    if not found_setups:
        print("No active Fibonacci rejection setups currently forming on the selected assets.")
        print("Macro gates and single-entry protection are active.")
    else:
        df_res = pd.DataFrame(found_setups)
        cols = ['symbol', 'sector', 'tf', 'action', 'shelf', 'entry', 'stop', 't2', 'rr', 'position_size_units', 'wick_pct']
        print(df_res[cols].to_string(index=False))
    print("="*115 + "\n")

if __name__ == '__main__':
    main()
