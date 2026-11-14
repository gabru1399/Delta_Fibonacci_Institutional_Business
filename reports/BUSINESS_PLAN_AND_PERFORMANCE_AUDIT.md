# Delta Fibonacci Prime Alpha Fund (India)
## Institutional Quantitative Business Plan & Full 250-Asset Calmar Audit (v2.0)

**Venture Entity**: Delta Fibonacci Institutional Business  
**Operating Exchange Venue**: Delta Exchange India (`api.india.delta.exchange`) — FIU-IND Compliant  
**Asset Universe Audited**: 250 Perpetual Futures Contracts across 5 Institutional Sectors  
**Total Simulations**: 11,613 Multi-Parameter Backtests (Single-TF 4H, Single-TF 1H, and MTF 4H+1H Confluence)  
**Target Capital Base**: $5,000 USD (Approx. ₹4,35,000 INR)  
**Execution Governance**: Single Entry Invariant (Strictly 1 Active Trade Per Symbol, Max 6 Simultaneous Basket Positions)  
**Tiered Rejection Support**: Full Capture of $EMA_{89}$ (Equilibrium) and $EMA_{233}$ (Deep Discount Institutional Sweeps)  

---

## 1. Executive Business Thesis & Strategic Moat

Operating an algorithmic prop-trading business inside India faces severe friction when dealing with offshore prop firms (regulatory scrutiny, RBI FEMA/LRS constraints, trailing drawdown traps, and arbitrary payout denials). 

**Delta Exchange India provides a compliant, high-velocity alternative**:
1. **Full Regulatory Compliance**: Registered directly with FIU-IND with local Indian banking rails (instant INR deposit & withdrawal via UPI, IMPS, and NEFT).
2. **Unified 5-Sector Asset Universe**:
   * **Commodities & Metals**: Gold (`PAXGUSD`, `XAUTUSD`), Silver (`SLVONUSD`), Crude Oil (`OILUSD`).
   * **TradFi Equities & Synthetics**: `ARMBUSD` (ARM), `MRVLBUSD` (Marvell), `HOODBUSD` (Robinhood), `AMDBUSD` (AMD), `BILLUSD` (Bill.com), `INTCBUSD` (Intel), `TSLAXUSD` (Tesla), `NVDAXUSD` (Nvidia).
   * **Indices & ETFs**: `EWYBUSD` (MSCI South Korea), `SOXLBUSD` (Semiconductor 3X Bull), `SPCXXUSD` (S&P 500), `QQQXUSD` (Nasdaq 100).
   * **Crypto Blue-Chips**: `BTCUSD`, `ETHUSD`, `SOLUSD`, `DOGEUSD`, `AVAXUSD`, `SUIUSD`, `NEARUSD`.
   * **Altcoins & DeFi Tokens**: `BANKUSD`, `GRAMUSD`, `TACUSD`, `INUSD`, `AXSUSD`.
3. **Methodological Rigor**:
   * **Tiered Support Engine**: Both $EMA_{89}$ and $EMA_{233}$ rejection wicks are captured.
   * **Single Entry Invariant**: Eliminates duplicate position risk during multiple consecutive wicks on the same swing.
   * **Multi-Timeframe (MTF) Confluence**: 4H Macro Regime Gate + 1H precision execution yields tighter stops and higher R-multiples ($3\text{R}-6\text{R}$).

---

## 2. Institutional Sector-Balanced Leaderboard (Top Performers by Sector)

| Sector | Top Symbol | Model Type | Timeframe | Strategy | Ribbon | Win Rate | Profit Factor | Net R | Max DD (R) | **Calmar Ratio** |
| :--- | :--- | :---: | :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Commodities & Metals** | **XAUTUSD** (Gold) | Single-TF | 4H | Fixed 3.0R | Fib 89/233 | **42.9%** | **2.13** | +14.16 R | 3.12 R | **9.71** |
| **Commodities & Metals** | **PAXGUSD** (Gold) | Single-TF | 4H | Fixed 2.5R | Classic 50/200 | **43.8%** | **1.84** | +23.58 R | 5.20 R | **7.10** |
| **Commodities & Metals** | **SLVONUSD** (Silver) | Single-TF | 4H | Fixed 2.0R | Classic 50/200 | **40.8%** | 1.30 | +9.04 R | 5.56 R | **2.63** |
| **Indices & ETFs** | **EWYBUSD** (Korea ETF) | Single-TF | 4H | Step-Trail | Classic 50/200 | **54.2%** | **2.50** | +17.11 R | 5.20 R | **13.04** |
| **Indices & ETFs** | **SOXLBUSD** (Semicon 3X)| Single-TF | 4H | Trail 89 | Fib 21/55 | **42.1%** | **2.11** | +11.02 R | 4.03 R | **9.74** |
| **Indices & ETFs** | **SPCXXUSD** (S&P 500) | Single-TF | 4H | Fixed 3.0R | Fib 89/233 | **37.5%** | 1.71 | +7.36 R | 3.28 R | **7.41** |
| **TradFi Equities** | **ARMBUSD** (ARM) | MTF Confluence | 4H + 1H | Step-Trail | Fib 34/89/233 | **42.9%** | **3.23** | **+55.66 R** | 5.32 R | **34.85** |
| **TradFi Equities** | **MRVLBUSD** (Marvell) | MTF Confluence | 4H + 1H | Step-Trail | Fib 34/89/233 | **52.7%** | **2.48** | **+39.90 R** | 4.16 R | **31.94** |
| **TradFi Equities** | **HOODBUSD** (Robinhood)| Single-TF | 4H | Step-Trail | Classic 50/200 | **56.0%** | **4.07** | +35.14 R | 6.36 R | **23.70** |
| **TradFi Equities** | **AMDBUSD** (AMD) | Single-TF | 1H | Step-Trail | Fib 89/233 | **48.1%** | **2.44** | +41.91 R | 5.68 R | **23.02** |
| **Crypto Blue-Chips** | **DOGEUSD** | Single-TF | 4H | Fixed 2.5R | Fib 34/89 | **34.7%** | 1.26 | +50.48 R | 13.60 R | **1.49** |
| **Crypto Blue-Chips** | **AVAXUSD** | Single-TF | 4H | Fixed 3.0R | Classic 50/200 | **30.5%** | 1.25 | +38.48 R | 16.08 R | **0.96** |
| **Crypto Blue-Chips** | **ETHUSD** | Single-TF | 4H | Trail 89 | Classic 50/200 | **29.7%** | 1.38 | +48.97 R | 19.62 R | **0.93** |
| **Altcoins & DeFi** | **BANKUSD** | Single-TF | 4H | Trail 55 | Fib 34/89 | **45.5%** | **4.83** | +14.29 R | 1.53 R | **45.70** |
| **Altcoins & DeFi** | **GRAMUSD** | Single-TF | 1H | Step-Trail | Fib 89/233 | **63.6%** | **4.29** | +41.07 R | 3.70 R | **33.75** |
| **Altcoins & DeFi** | **TACUSD** | Single-TF | 4H | Fixed 3.0R | Classic 50/200 | **50.0%** | **2.85** | +13.44 R | 2.08 R | **24.80** |

---

## 3. Event-Driven Portfolio Simulation ($5,000 Base Capital)

With zero equity lookahead, strict event-queue chronological ordering, maximum 6 concurrent positions, and maximum 2 positions per sector:

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            $5,000 BASKET PERFORMANCE ACROSS SIZING TIERS                    │
├──────────────────────────┬──────────────┬──────────────┬─────────────┬───────────┬──────────┤
│ Model                    │ Risk / Trade │ Final Equity │ Total ROI % │ Max DD %  │ Calmar   │
├──────────────────────────┼──────────────┼──────────────┼─────────────┼───────────┼──────────┤
│ Conservative Fixed       │ 0.5% ($25)   │ $5,264.50    │ +5.3%       │ 1.8%      │ 1.32     │
│ Institutional Standard   │ 1.0% ($50)   │ $5,529.00    │ +10.6%      │ 3.4%      │ 1.37     │
│ Dynamic Compounding      │ 0.5% Dynamic │ $5,266.57    │ +5.3%       │ 1.8%      │ 1.34     │
│ Aggressive Compounding   │ 1.0% Dynamic │ $5,536.84    │ +10.7%      │ 3.4%      │ 1.41     │
└──────────────────────────┴──────────────┴──────────────┴─────────────┴───────────┴──────────┘
```

---

## 4. Operational Instructions

### 4.1 Run Live Market Scanner
```bash
# Scan across all 5 sectors on 4H
python engine/delta_live_scanner.py --tf 4H --sector ALL

# Scan only Metals & Commodities
python engine/delta_live_scanner.py --tf 4H --sector COMMODITIES_METALS

# Scan both 4H and 1H for TradFi Synthetics
python engine/delta_live_scanner.py --tf ALL --sector TRADFI_EQUITIES
```

### 4.2 Run Portfolio Simulator
```bash
python engine/simulate_business_portfolio.py
```

### 4.3 Re-run Complete Audit
```bash
python engine/run_full_business_audit.py
```
