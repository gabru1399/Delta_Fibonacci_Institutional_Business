# QR-2026-1115 Remediation — Applied Patch Set

This branch carries the z.ai Quant Review (QR-2026-1115) remediation applied
on top of the audited baseline commit `649eb45`. The sign-off verdict is
unchanged: **GO for local dry-run paper trading; NO-GO for live capital**
until the memo's conditions C1–C5 are met (patch set applied, crash gate
armed, 60–90 days of logged forward paper fills, live sizing only on rolling
forward t ≥ 4.33, stakeholder economics restated from the audited rows).

## Applied commits (in order, all on top of `649eb45`)

| # | Commit | Module | Change |
|---|--------|--------|--------|
| 1 | `1da2c74` | `engine/delta_min_lot_sizer.py` | D1: strict 1.1R (₹55) hard cap; APPROVED_FLEX band (1.25×–2.5×) removed; integer lots floored, never rounded above budget |
| 2 | `0e64483` | `engine/delta_live_scanner.py` | D4: 800-bar 4H depth for EMA233 stabilization; `recent_pct_change` crash-tape fields on signals/anchors; fill-timing notes (live price vs backtest next-bar-open) |
| 3 | `f2df03c` | `engine/cluster_risk_governor.py` | D2: crash-replay gate — no new entries while symbol or cluster anchor ≤ −6% over the last two closed 4H bars; dormant when fields absent |
| 4 | `ae92219` | `engine/verify_live_readiness.py` | D3: kill-switch test made real (keyword args, executor bound to the file, halt REASON asserted); SOLUSD strict-cap regression added |
| 5 | `5f18023` | `delta_order_executor.py` | Follow-up: per-trade risk cap aligned with the sizer at 1.1R (₹55) — constructor and CLI defaults |
| 6 | `7b01e53` | `engine/verify_live_readiness.py` | Follow-up: wrapper tests pinned to limit orders (deterministic risk) + executor/sizer cap-alignment boundary pair |

## The two follow-up fixes (surfaced by the integration run)

**05 — sizer/executor cap mismatch.** The sizer's hard cap (commit 1) admits
min-lot trades up to ₹55 (1.1R), but the executor rejected anything above
₹50 (1.0R). Every sizer-approved ETHUSD-class min-lot order (e.g. ₹52.70)
would have been approved at sizing time and then rejected at order time.
Both gates now enforce the same ₹55 / 1.1R institutional bound; the executor
remains the final authority at that bound.

**06 — price-flaky wrapper test.** The wrapper test placed a MARKET order,
whose risk check references the LIVE mark price, so the suite's outcome
flipped with the tape (it aborted at ₹55.09 = 1.10R once ETH crossed
~$1,816; it had passed earlier only because ETH sat below ~$1,810). Both
bracket calls now use pinned LIMIT orders (risk ₹42.50 = 0.85R,
deterministic), so no test outcome depends on the live tape. A boundary
pair now asserts the aligned cap end-to-end: ₹52.70 (1.05R, the sizer's own
approved ETH row) is accepted by the executor, ₹59.50 (1.19R) is rejected
with the 1.1R reason. The kill-switch sub-test can now only halt for the
kill-switch reason.

## Verification (run at this branch tip)

```
python3 engine/verify_live_readiness.py
```

Expected key lines:

```
Strict Cap Check: SOLUSD 1-ct @ 2% stop risks ₹117.3 -> REJECTED_OVERSIZED (PASSED)
Position Sizer Check: PASSED. Approved trades are capped at 1.1R (₹55); flex band removed.
Cap Alignment A: ETHUSD 1-ct @ Rs 52.70 risk (1.05R, sizer APPROVED) -> executor ACCEPTS
Cap Alignment B: ETHUSD 1-ct @ Rs 59.50 risk (1.19R) -> executor REJECTS: ... exceeds the 1.1R per-trade cap ...
OK: Execution halted by kill-switch (reason verified): KILL SWITCH engaged ...
ALL 6 INSTITUTIONAL VERIFICATION TESTS PASSED (100% READY FOR LOCAL EXECUTION)
```

Tests [1], [2] and [6] exercise the live venue API (connectivity, candles,
scanner) and require network access; their risk assertions are all pinned
and deterministic.

## Standing note on backtest claims

The headline numbers previously reported for `run_inr_portfolio_backtest.py`
(₹19,318.27 / +286.4% / 2,056 trades / minimum equity ₹5,000 / 0.00%
drawdown) do not reproduce from the committed snapshot at `649eb45`. The
reproducible run yields ₹13,886.20 / +177.7% / 3,235 trades / 35.5% win
rate / minimum equity ₹4,622 / peak drawdown ₹7,200 — and reverses to
−15.5% under nothing but a reversed queue tie-break (the underlying
17,678-trade population carries +0.0034R per trade). Size every decision
off the audited rows, not the headline claims, and complete the paper
phase before any capital.
