# Portfolio Playbook: S1-S7 Coordinated Orchestration for Freqtrade

## Objective
Design a **robustness-first** portfolio layer for S1-S7 where capital is dynamically allocated across uncorrelated strategy buckets, and risk is managed globally at the portfolio level.

- Primary KPI: stability of equity curve and drawdown containment.
- Secondary KPI: risk-adjusted return consistency across regimes.

---

## 1) Portfolio Allocation Policy

### 1.1 Strategy buckets
Map the seven strategies into cadence/risk buckets:

- **HFT bucket**: S1, S2
- **MFT bucket**: S3, S4
- **LFT bucket**: S5, S6
- **Event bucket**: S7 (treated as tactical overlay with hard cap)

### 1.2 Risk-parity style bucket weights
Use realized bucket volatility (e.g., 20d EWMA of daily bucket returns) and inverse-vol weighting:

- Raw weight: `w_b_raw = 1 / sigma_b`
- Normalized: `w_b = w_b_raw / sum(w_b_raw)`

Then apply guardrails:

- HFT bucket cap: 40%
- MFT bucket cap: 40%
- LFT bucket cap: 45%
- Event (S7) cap: 20%
- Min per active bucket: 10%

If a bucket is disabled by risk breakers, redistribute pro-rata to remaining active buckets respecting caps.

### 1.3 Intra-bucket strategy weights
Within each bucket, allocate by inverse strategy volatility with equal-weight fallback:

- `w_s_in_bucket = (1 / sigma_s) / sum(1 / sigma_s)`
- If insufficient history (`< 100 trades`), use equal split among strategies in that bucket.

Hard per-strategy cap at portfolio level:

- Default cap: 18% notional per strategy
- Absolute cap (aggressive profile only): 22%

### 1.4 Per-asset exposure caps
Aggregate all open risk by base asset across all strategies:

- BTC max portfolio exposure: 30%
- ETH max portfolio exposure: 25%
- SOL max portfolio exposure: 18%
- Any other single asset: 15%
- Total top-3 assets combined: 60%

If a new order would breach a cap, scale down order size; if minimum order notional is violated after scaling, reject the order.

### 1.5 Correlation-aware throttling
Compute rolling signal alignment and return correlation for major assets and strategy outputs:

- Signal alignment score `A` for BTC/ETH/SOL = fraction of aligned directional signals over last 24h.
- Return correlation matrix `Corr` on 7d strategy PnL streams.

Throttling rules:

1. If `A >= 0.75`, reduce **new gross risk budget** by 25%.
2. If `A >= 0.90`, reduce new gross risk budget by 45% and block new entries from lowest edge-score strategy.
3. If mean pairwise strategy correlation `>= 0.65`, apply global position size multiplier 0.80.
4. If both (2) and (3) trigger, clamp multiplier to 0.60 and enforce max 1 new position per 15 minutes.

---

## 2) Global Risk Controls

### 2.1 Daily loss limit
Define daily realized + unrealized drawdown vs start-of-day equity:

- Soft limit: -2.0% -> freeze new entries for 2 hours; allow risk-reducing exits.
- Hard limit: -3.0% -> halt new entries until next UTC day.

### 2.2 Rolling drawdown breaker
Track rolling peak-to-trough drawdown of portfolio equity:

- Warning tier: rolling DD >= 6% -> halve per-trade risk (`size_mult=0.50`).
- Breaker tier: rolling DD >= 9% -> no new entries for 24h.
- Recovery condition: rolling DD < 5% and 12h with non-negative PnL -> restore to normal.

### 2.3 Consecutive-loss cooldown
At portfolio level (closed trades):

- 4 losses in a row: cooldown 90 minutes for new entries.
- 6 losses in a row: cooldown 6 hours.
- 8 losses in a row: cooldown 24 hours + force profile downgrade by one step (Aggressive -> Balanced -> Conservative).

Reset loss streak after two consecutive wins or after full cooldown elapses with no new losses.

### 2.4 Volatility regime switch
Use exchange-level realized vol proxy (e.g., BTC 1h ATR% or basket EWMA vol):

- **Normal vol**: baseline leverage/settings.
- **High vol**: if vol z-score >= +1.5 for 3 consecutive hours:
  - reduce leverage by 30%
  - reduce max_open_trades by 20%
  - tighten slippage threshold by 20%
- **Extreme vol**: if z-score >= +2.2:
  - reduce leverage by 50%
  - reduce max_open_trades by 40%
  - disable S2 and S7 new entries unless dedicated override flag is set.

---

## 3) Execution Safety Layer

### 3.1 Order timeout and retry policy
For entry and exit orders:

- Limit order timeout: 90s (HFT), 180s (MFT), 300s (LFT).
- Retry policy: max 2 retries with price refresh and reduced size (90% then 75%).
- If retries exhausted: cancel and emit `ORDER_TIMEOUT_FAIL` event.

Never retry if spread/slippage guard fails (see below).

### 3.2 Spread/slippage guard
Before order placement:

- `spread_bps <= max_spread_bps` by profile and bucket.
- expected slippage estimate <= `max_slippage_bps` by profile.

Runtime defaults:

- HFT: spread <= 8 bps, slippage <= 10 bps
- MFT: spread <= 15 bps, slippage <= 20 bps
- LFT: spread <= 20 bps, slippage <= 30 bps

If two consecutive guard failures on same symbol within 10 minutes, apply symbol cooldown (30 minutes).

### 3.3 Funding-fee awareness hook
If exchange/freqtrade integration exposes funding data:

- For long-biased entries: if projected funding over holding horizon > +0.04%, reduce position size by 25%.
- For short-biased entries: symmetric rule for negative funding.
- If absolute funding > 0.08% and trade edge-score is below threshold, reject entry.

If funding data unavailable, mark hook status as degraded and continue without this filter; raise monitoring warning.

---

## 4) Deployment Profiles (numeric defaults)

### Conservative
- leverage: `1.5x`
- max_open_trades: `6`
- risk_budget (gross at-risk capital): `0.8%` of equity
- per-strategy cap: `12%`
- per-asset cap multiplier: `0.85`
- daily hard loss limit: `-2.2%`

### Balanced
- leverage: `2.5x`
- max_open_trades: `10`
- risk_budget: `1.4%` of equity
- per-strategy cap: `18%`
- per-asset cap multiplier: `1.00`
- daily hard loss limit: `-3.0%`

### Aggressive
- leverage: `3.5x`
- max_open_trades: `14`
- risk_budget: `2.1%` of equity
- per-strategy cap: `22%`
- per-asset cap multiplier: `1.15`
- daily hard loss limit: `-3.8%`

---

## 5) Freqtrade Deployment Pattern

Use one orchestrator service (controller) that:

1. Reads strategy signals/positions from S1-S7 instances.
2. Computes current profile multipliers and global risk state.
3. Emits allowed order sizes and allow/deny decision per signal.
4. Writes decision logs for audit (`allocation_state`, `risk_state`, `execution_guard_state`).

Recommended control loop: every 60 seconds for risk and every 15 seconds for execution guards.

---

## 6) Governance and Change Control

- Any threshold change >10% requires paper-trade validation for 7 days.
- Profile changes in production require two-person approval.
- Breaker disable flags auto-expire after 12h.
- Weekly post-mortem: top 5 rejected orders, top 5 drawdown contributors, and correlation-throttle trigger frequency.
