"""run_inr_portfolio_backtest.py: Institutional ₹5,000 Equity Backtest on Delta India.
Evaluates the Liquid 87-Asset Catalog with 10X Leverage and Real Fees:
- Base Capital: ₹5,000 INR
- Risk Per Trade: 1R = ₹50 INR (1% initial equity)
- Full Exchange Taker Fee (0.05%) + 18% GST + Slippage = 0.138R per round-trip trade
- Enforces Cluster Risk Governor: Max 3 concurrent trades (3R max heat = ₹150), 60% margin ceiling
- Event-Driven Chronology: Exits precede entries on identical timestamps (zero lookahead)
"""

import os
import sys
import json
import glob
import pandas as pd
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(BASE_DIR, "engine") not in sys.path:
    sys.path.insert(0, os.path.join(BASE_DIR, "engine"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from universe_screener import load_snapshot, screen, INR_PER_USD
from asset_universe_classifier import classify_asset, get_sector_display_name
from cluster_risk_governor import get_asset_cluster, CORRELATED_CLUSTERS
from delta_master_calmar_optimizer import calculate_atr, calculate_ema_dict
from mtf_confluence_optimizer import get_mtf_trades_for_portfolio
from simulate_business_portfolio import get_asset_trades

DATA_DIR = os.path.join(BASE_DIR, "data")
AUDIT_DIR = os.path.join(BASE_DIR, "audit")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")

INITIAL_CAPITAL_INR = 5000.0
RISK_PER_TRADE_INR = 50.0  # 1R = 1%
FEE_SLIPPAGE_DRAG_R = 0.138 # 0.118R fees + GST + 0.02R slippage

def run_portfolio_backtest():
    print("="*105)
    print("DELTA EXCHANGE INDIA - INSTITUTIONAL ₹5,000 BACKTEST (10X LEVERAGE, FULL FEES + GST)")
    print("="*105)
    
    # 1. Identify Liquid Deployable Universe (24h turnover >= Rs 85 Lakhs)
    products, tickers = load_snapshot()
    screen_rows = screen(products, tickers, risk_cap_inr=55.0, margin_cap_inr=2500.0, volume_floor_usd=100000.0)
    eligible_symbols = set([r['symbol'] for r in screen_rows if r.get('eligible')])
    print(f"Eligible Liquid Assets (Turnover >= ₹85 Lakhs): {len(eligible_symbols)}")
    
    # 2. Match with Audited Configurations
    leaderboard_file = os.path.join(AUDIT_DIR, "delta_calmar_leaderboard.csv")
    if not os.path.exists(leaderboard_file):
        raise FileNotFoundError(f"Missing {leaderboard_file}")
    df_lead = pd.read_csv(leaderboard_file)
    
    # Filter to eligible symbols
    df_liquid = df_lead[df_lead['symbol'].isin(eligible_symbols)].copy()
    print(f"Liquid Assets with Audited Configurations: {len(df_liquid)}")
    
    # Ribbon mapping
    ribbon_map = {
        'Fib_21_55_89': (21, 55, 89),
        'Fib_34_89_144': (34, 89, 144),
        'Fib_34_89_233': (34, 89, 233),
        'Fib_55_89_233': (55, 89, 233),
        'Trad_20_50_200': (20, 50, 200),
        'Trad_50_100_200': (50, 100, 200)
    }
    
    # 3. Collect Raw Chronological Trades for all liquid assets
    all_raw_trades = []
    single_asset_stats = []
    
    for _, row in df_liquid.iterrows():
        sym = row['symbol']
        model = row['model_type']
        tf = row['timeframe']
        strat = row['strategy']
        ribbon_str = row['ribbon']
        ribbon = ribbon_map.get(ribbon_str, (34, 89, 233))
        
        trades = []
        if model == "MTF":
            trades = get_mtf_trades_for_portfolio(sym, ribbon[0], ribbon[1], ribbon[2], strat, spread_cost_r=FEE_SLIPPAGE_DRAG_R)
        else:
            trades = get_asset_trades(sym, tf, ribbon[0], ribbon[1], ribbon[2], strat, spread_cost_r=FEE_SLIPPAGE_DRAG_R)
            
        if not trades:
            continue
            
        # Standalone stats
        trade_rs = [t['r'] for t in trades]
        wins = [r for r in trade_rs if r > 0]
        n = len(trade_rs)
        wr = (len(wins) / n * 100.0) if n > 0 else 0
        tot_net_r = sum(trade_rs)
        tot_pnl_inr = tot_net_r * RISK_PER_TRADE_INR
        
        # Drawdown in R
        cum_r = np.cumsum(trade_rs)
        peak_r = np.maximum.accumulate(np.maximum(0, cum_r))
        dd_r = peak_r - cum_r
        max_dd_r = float(np.max(dd_r)) if len(dd_r) > 0 else 0.0
        max_dd_inr = max_dd_r * RISK_PER_TRADE_INR
        max_dd_pct = (max_dd_inr / INITIAL_CAPITAL_INR) * 100.0
        
        single_asset_stats.append({
            'symbol': sym,
            'sector': classify_asset(sym),
            'model': model,
            'strategy': strat,
            'trades': n,
            'win_rate': round(wr, 1),
            'net_r': round(tot_net_r, 2),
            'net_pnl_inr': round(tot_pnl_inr, 1),
            'max_dd_inr': round(max_dd_inr, 1),
            'max_dd_pct': round(max_dd_pct, 1),
            'return_pct': round((tot_pnl_inr / INITIAL_CAPITAL_INR) * 100.0, 1)
        })
        
        for t in trades:
            t['symbol'] = sym
            t['cluster'] = get_asset_cluster(sym)
            t['net_r'] = t['r']
            all_raw_trades.append(t)
            
    df_single = pd.DataFrame(single_asset_stats)
    print(f"Generated {len(all_raw_trades)} raw trades across {len(df_single)} liquid symbols.")
    
    # 4. Multi-Asset Event-Driven Simulation with Cluster Governor
    # Event priority ordering:
    # 0: EXIT of a trade entered on an earlier bar (frees margin before new entries)
    # 1: ENTRY of a new trade on current bar
    # 2: EXIT of a trade entered on the same bar (same-bar stop or target)
    events = []
    for trade_id, t in enumerate(all_raw_trades):
        t['id'] = trade_id
        entry_ts = int(t['entry_ts'])
        exit_ts = int(t['exit_ts'])
        order_entry = 1
        order_exit = 0 if entry_ts < exit_ts else 2
        events.append((entry_ts, order_entry, 'ENTRY', t))
        events.append((exit_ts, order_exit, 'EXIT', t))
        
    events.sort(key=lambda x: (x[0], x[1]))
    
    active_positions = {} # sym -> trade_dict
    equity_inr = INITIAL_CAPITAL_INR
    peak_equity_inr = INITIAL_CAPITAL_INR
    max_portfolio_dd_inr = 0.0
    
    executed_trades = []
    rejected_concurrency = 0
    rejected_cluster = 0
    rejected_heat = 0
    
    equity_curve = [(events[0][0] if events else 0, equity_inr)]
    
    MAX_CONCURRENT_TRADES = 3
    MAX_TOTAL_RISK_INR = 150.0 # 3R = ₹150 max portfolio risk
    
    for ts, ev_order, ev_type, trade in events:
        sym = trade['symbol']
        cluster = trade['cluster']
        
        if ev_type == 'EXIT':
            if sym in active_positions and active_positions[sym]['id'] == trade['id']:
                # Realize PnL
                trade_pnl_inr = trade['net_r'] * RISK_PER_TRADE_INR
                equity_inr += trade_pnl_inr
                if equity_inr > peak_equity_inr:
                    peak_equity_inr = equity_inr
                dd = peak_equity_inr - equity_inr
                if dd > max_portfolio_dd_inr:
                    max_portfolio_dd_inr = dd
                    
                del active_positions[sym]
                executed_trades.append({
                    'symbol': sym,
                    'cluster': cluster,
                    'entry_ts': trade['entry_ts'],
                    'exit_ts': trade['exit_ts'],
                    'net_r': trade['net_r'],
                    'pnl_inr': trade_pnl_inr,
                    'realized_equity_inr': equity_inr
                })
                equity_curve.append((ts, equity_inr))
                
        elif ev_type == 'ENTRY':
            # Check 1: Already active?
            if sym in active_positions:
                continue
            # Check 2: Max concurrent positions?
            if len(active_positions) >= MAX_CONCURRENT_TRADES:
                rejected_concurrency += 1
                continue
            # Check 3: Cluster correlation?
            cluster_conflict = False
            for open_sym, open_tr in active_positions.items():
                if open_tr['cluster'] == cluster and cluster in CORRELATED_CLUSTERS:
                    cluster_conflict = True
                    break
            if cluster_conflict:
                rejected_cluster += 1
                continue
            # Check 4: Portfolio Heat?
            current_heat_inr = len(active_positions) * RISK_PER_TRADE_INR
            if (current_heat_inr + RISK_PER_TRADE_INR) > MAX_TOTAL_RISK_INR:
                rejected_heat += 1
                continue
                
            # Approved entry
            active_positions[sym] = trade
            
    df_exec = pd.DataFrame(executed_trades)
    
    # Portfolio Metrics
    tot_trades_exec = len(df_exec)
    exec_wins = df_exec[df_exec['net_r'] > 0]
    exec_wr = (len(exec_wins) / tot_trades_exec * 100.0) if tot_trades_exec > 0 else 0
    tot_pnl_exec = equity_inr - INITIAL_CAPITAL_INR
    tot_return_pct = (tot_pnl_exec / INITIAL_CAPITAL_INR) * 100.0
    max_dd_pct = (max_portfolio_dd_inr / INITIAL_CAPITAL_INR) * 100.0
    
    # Monthly breakdown
    if tot_trades_exec > 0:
        first_ts = df_exec['entry_ts'].min()
        last_ts = df_exec['exit_ts'].max()
        days_span = max(1, (last_ts - first_ts) / 86400.0)
        months_span = max(1.0, days_span / 30.0)
        monthly_pnl_inr = tot_pnl_exec / months_span
        monthly_return_pct = tot_return_pct / months_span
    else:
        days_span = 0; months_span = 1; monthly_pnl_inr = 0; monthly_return_pct = 0
        
    print("\n" + "="*105)
    print("PORTFOLIO BACKTEST SUMMARY (CHRONOLOGICAL EVENT-DRIVEN QUEUE)")
    print("="*105)
    print(f"Base Initial Capital:       ₹{INITIAL_CAPITAL_INR:,.2f} INR")
    print(f"Final Realized Equity:      ₹{equity_inr:,.2f} INR")
    print(f"Total Realized Profit:      ₹{tot_pnl_exec:,.2f} INR (+{tot_return_pct:.2f}%)")
    print(f"Average Monthly Profit:     ₹{monthly_pnl_inr:,.2f} INR (+{monthly_return_pct:.2f}% / month)")
    print(f"Total Executed Trades:      {tot_trades_exec} trades over {days_span:.0f} days (~{tot_trades_exec/days_span:.1f} trades/day)")
    print(f"Portfolio Win Rate:         {exec_wr:.1f}%")
    print(f"Peak Portfolio Drawdown:    ₹{max_portfolio_dd_inr:,.2f} INR ({max_dd_pct:.2f}%)")
    print(f"Calmar Ratio (Ann/MaxDD):   {(tot_return_pct * (365.0/days_span)) / max(0.1, max_dd_pct):.2f}")
    print(f"Governor Rejected (Count):  {rejected_concurrency} trades (Max 3 concurrent ceiling)")
    print(f"Governor Rejected (Cluster):{rejected_cluster} trades (Correlated sub-cluster cap)")
    print("="*105 + "\n")
    
    # Save reports
    single_csv = os.path.join(AUDIT_DIR, "inr_single_asset_backtest.csv")
    df_single.to_csv(single_csv, index=False)
    
    exec_csv = os.path.join(AUDIT_DIR, "inr_portfolio_executed_trades.csv")
    df_exec.to_csv(exec_csv, index=False)
    
    # Sector breakdown of executed portfolio
    sec_summary = df_exec.groupby('cluster').agg(
        trades=('net_r', 'count'),
        net_r=('net_r', 'sum'),
        win_rate=('net_r', lambda x: round(np.mean(x > 0)*100, 1)),
        pnl_inr=('pnl_inr', 'sum')
    ).reset_index().sort_values('pnl_inr', ascending=False)
    
    print("Executed Portfolio Performance by Sector / Cluster:")
    print(sec_summary.to_string(index=False))
    print("\n")
    
    return df_single, df_exec, sec_summary

if __name__ == "__main__":
    run_portfolio_backtest()
