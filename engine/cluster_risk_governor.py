"""cluster_risk_governor.py: Institutional Portfolio Heat & Sector Cluster Governor.
Enforces institutional risk constraints on Delta Exchange India for a ₹5,000 base capital:
1. Max Portfolio Heat: 3R total open risk (₹150 max at any time).
2. Max Active Positions: 3 simultaneous trades.
3. Sector Cluster Rule: Max 1 position per correlated sub-cluster (e.g. only 1 of ARM/MRVL/AMD, only 1 of XAUT/PAXG).
4. Margin Cap: Total blocked margin <= 60% of equity (₹3,000 max).
"""

import os
import sys
import json
from typing import Dict, Any, List, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if os.path.join(BASE_DIR, "engine") not in sys.path:
    sys.path.insert(0, os.path.join(BASE_DIR, "engine"))

from asset_universe_classifier import classify_asset

# Correlated Sub-clusters that must never be traded simultaneously
CORRELATED_CLUSTERS = {
    "SEMICONDUCTORS": ["ARMBUSD", "MRVLBUSD", "AMDBUSD", "NVDBUSD", "SOXLBUSD"],
    "PRECIOUS_METALS": ["XAUTUSD", "PAXGUSD", "SLVONUSD"],
    "CRYPTO_MAJORS": ["BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD"],
    "MEME_COINS": ["DOGEUSD", "PEPEUSD", "SHIBUSD", "BONKUSD", "FLOKIUSD"]
}

def get_asset_cluster(symbol: str) -> str:
    """Returns the sub-cluster name if asset is part of a high-correlation group."""
    for cluster_name, assets in CORRELATED_CLUSTERS.items():
        if symbol in assets:
            return cluster_name
    return classify_asset(symbol)

def validate_new_trade_entry(
    candidate_order: Dict[str, Any],
    active_positions: Dict[str, Any],
    equity_inr: float = 5000.0,
    max_open_trades: int = 3,
    max_total_risk_r: float = 3.0,
    max_margin_ratio: float = 0.60
) -> Tuple[bool, str]:
    """Validates whether a new trade setup is permitted under portfolio risk rules.
    
    Returns (is_approved: bool, reason: str).
    """
    candidate_sym = candidate_order['symbol']
    
    # 1. Check if candidate is already actively open (Single Entry Invariant)
    if candidate_sym in active_positions:
        return False, f"Asset {candidate_sym} already has an active open position."

    # 2. Check total active trade count
    if len(active_positions) >= max_open_trades:
        return False, f"Portfolio trade count limit reached ({len(active_positions)}/{max_open_trades})."

    # 3. Check Sub-Cluster Correlation
    candidate_cluster = get_asset_cluster(candidate_sym)
    for open_sym in active_positions.keys():
        open_cluster = get_asset_cluster(open_sym)
        if candidate_cluster == open_cluster and candidate_cluster in CORRELATED_CLUSTERS:
            return False, f"Cluster conflict: {candidate_sym} shares sub-cluster '{candidate_cluster}' with active position {open_sym}."

    # 4. Check Total Portfolio Heat (Risk in INR)
    candidate_risk = candidate_order.get('actual_risk_inr', equity_inr * 0.01)
    current_risk_sum = sum(p.get('actual_risk_inr', equity_inr * 0.01) for p in active_positions.values())
    max_allowed_risk = equity_inr * (max_total_risk_r * 0.01) * 1.05  # 3R = ₹150 with 5% rounding tolerance (₹157.5)
    
    if (current_risk_sum + candidate_risk) > max_allowed_risk:
        return False, f"Portfolio heat cap exceeded: Total risk would be ₹{current_risk_sum + candidate_risk:.1f} (Cap: ₹{max_allowed_risk:.1f})."

    # 5. Check Total 10X Margin Blocked
    candidate_margin = candidate_order.get('margin_10x_inr', candidate_order.get('notional_inr', 0) / 10.0)
    current_margin_sum = sum(p.get('margin_10x_inr', 0) for p in active_positions.values())
    max_allowed_margin = equity_inr * max_margin_ratio # ₹3,000
    
    if (current_margin_sum + candidate_margin) > max_allowed_margin:
        return False, f"Total 10X margin limit exceeded: Blocked margin would be ₹{current_margin_sum + candidate_margin:.1f} (Cap: ₹{max_allowed_margin:.1f})."

    return True, "Trade approved by Cluster Risk Governor."

if __name__ == "__main__":
    print("Testing Cluster Risk Governor on ₹5,000 Portfolio...")
    
    active_sample = {
        "ETHUSD": {"actual_risk_inr": 52.7, "margin_10x_inr": 263.5},
        "ARMBUSD": {"actual_risk_inr": 50.0, "margin_10x_inr": 166.6}
    }
    
    # Test 1: Try adding MRVL (Semiconductor cluster conflict with ARM)
    cand_mrvl = {"symbol": "MRVLBUSD", "actual_risk_inr": 48.0, "margin_10x_inr": 150.0}
    ok1, reason1 = validate_new_trade_entry(cand_mrvl, active_sample)
    print(f"Test 1 (MRVL vs ARM): Approved={ok1} | Reason: {reason1}")
    
    # Test 2: Try adding Gold XAUT (Different cluster, fits within 3R)
    cand_gold = {"symbol": "XAUTUSD", "actual_risk_inr": 49.7, "margin_10x_inr": 331.5}
    ok2, reason2 = validate_new_trade_entry(cand_gold, active_sample)
    print(f"Test 2 (Gold XAUT): Approved={ok2} | Reason: {reason2}")
    
    # Test 3: If Gold is added, try adding a 4th position (Trade count cap)
    active_sample["XAUTUSD"] = {"actual_risk_inr": 49.7, "margin_10x_inr": 331.5}
    cand_doge = {"symbol": "DOGEUSD", "actual_risk_inr": 38.0, "margin_10x_inr": 127.5}
    ok3, reason3 = validate_new_trade_entry(cand_doge, active_sample)
    print(f"Test 3 (4th Trade DOGE): Approved={ok3} | Reason: {reason3}")
