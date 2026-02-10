# Research Contract v1.0 — Freqtrade Futures Blueprint (BTC/ETH/SOL, Binance-first + Hyperliquid Notes)

## 0) Scope and Non-Negotiables

**Mission scope**
- Build a research-first, implementation-ready blueprint for **Freqtrade-compatible futures strategies** on:
  - **Binance USDT-M perpetuals (primary venue)**
  - **Hyperliquid perpetuals (adaptation notes only in this phase)**
- Research universe (initial):
  - `BTC/USDT:USDT`, `ETH/USDT:USDT`, `SOL/USDT:USDT`
- Deliver strategy architecture and validation rules before writing strategy code.

**Hard constraints (binding)**
1. **No lookahead bias / no future leakage / no repainting** in indicators, labels, exits, or protections.
2. Every future strategy artifact must include:
   - explicit long/short **entry** conditions
   - explicit long/short **exit** conditions
   - fixed **stoploss** + **trailing** stop logic
   - **protections schema**: cooldown, stoploss guard, low-profit-pairs concept
   - explicit **risk budget per trade** and **max concurrent exposure**
3. Objective is **risk-adjusted robustness**, not absolute return.
4. Minimum viability gate for any candidate strategy:
   - **Profit Factor > 1.5**
   - **Style-specific win-rate band** (defined in §4)
   - **Style-tier max drawdown cap** (defined in §4)

---

## 1) Design Principles (Open-Source-Inspired, Freqtrade-Native)

This blueprint synthesizes working principles commonly seen in high-quality open-source stacks (Freqtrade/Hummingbot/Jesse/Lean-like workflows), but execution remains **native Freqtrade strategy Python only**.

### 1.1 Framework-level principles to adopt
- **Research/Execution separation**: factor hypothesis is isolated from execution constraints (fees, slippage, latency assumptions).
- **Deterministic pipelines**: same config + same data = same result (reproducible backtests/hyperopt).
- **Composability**: each strategy is assembled from modular factor blocks (trend, mean-reversion, volatility, structure, regime).
- **Scenario robustness over peak metrics**: accept lower CAGR if sensitivity + walk-forward stability improve.
- **Risk-first controls**: exposure and drawdown controls can veto otherwise valid entries.

### 1.2 Freqtrade-native implementation doctrine
- Use only native Freqtrade capabilities:
  - `populate_indicators`, `populate_entry_trend`, `populate_exit_trend`
  - strategy-level `stoploss`, `trailing_stop`, optional custom stop behavior (without future data)
  - Freqtrade protections configuration for cooldown/guard rails
  - Freqtrade futures settings for leverage and shorting
- Avoid external execution engines or non-Freqtrade order routers in strategy logic.

---

## 2) Strategy Taxonomy (A)

Define a 3×3 matrix: **time horizon tier (HFT/MFT/LFT)** × **risk posture (Conservative/Progressive/Aggressive)**.

> Note: “HFT” here means *higher-frequency retail bar-based Freqtrade style*, not exchange co-located microsecond HFT.

### 2.1 Horizon definitions
- **HFT-like (HF)**: 1m–5m execution timeframe, holding minutes to a few hours.
- **MFT (MF)**: 5m–30m execution timeframe, holding hours to 1–3 days.
- **LFT (LF)**: 1h–4h execution timeframe, holding multi-day to multi-week.

### 2.2 Risk posture definitions
- **Conservative (C)**: tighter regime filters, lower leverage assumptions, stricter entry quality.
- **Progressive (P)**: balanced selectivity and opportunity capture.
- **Aggressive (A)**: looser filters, faster turnover, higher false-positive tolerance.

### 2.3 Taxonomy table (targets, not guarantees)

| Style Cell | Typical TF | Trade Frequency | Win-rate Band | PF Target | Max DD Cap |
|---|---|---:|---:|---:|---:|
| HF-C | 1m–5m | High | 50–60% | >= 1.6 | <= 12% |
| HF-P | 1m–5m | High | 45–55% | >= 1.6 | <= 15% |
| HF-A | 1m–5m | Very High | 40–52% | >= 1.5 | <= 18% |
| MF-C | 5m–30m | Medium | 48–58% | >= 1.7 | <= 10% |
| MF-P | 5m–30m | Medium | 44–55% | >= 1.6 | <= 13% |
| MF-A | 5m–30m | Med-High | 40–52% | >= 1.5 | <= 16% |
| LF-C | 1h–4h | Low | 42–55% | >= 1.8 | <= 9% |
| LF-P | 1h–4h | Low-Med | 38–50% | >= 1.7 | <= 12% |
| LF-A | 1h–4h | Medium | 35–48% | >= 1.5 | <= 15% |

---

## 3) Factor Map (B)

Each strategy candidate must declare a factor stack with feature purpose, anti-leakage guardrails, and veto order.

### 3.1 Core factor families
1. **Trend factors**
   - Examples: EMA slope hierarchy, ADX trend strength, higher-timeframe directional filter.
   - Use-case: avoid counter-trend entries in momentum regimes.

2. **Mean-reversion factors**
   - Examples: z-score distance from VWAP/EMA band, RSI/Stoch extremes in range regimes.
   - Use-case: fade stretched moves when trend strength is weak.

3. **Volatility factors**
   - Examples: ATR percentile, realized volatility buckets, Bollinger bandwidth state.
   - Use-case: scale stop distance, trailing behavior, and entry throttles.

4. **Structure / micro-structure proxies**
   - Examples: swing high/low break (past-confirmed only), candle range compression/expansion, volume shock filters.
   - Use-case: timing and confirmation around breakout or failure points.

5. **Regime filters**
   - Examples: trend vs range classifier, volatility regime map, funding/funding-proxy stress state.
   - Use-case: route signals to appropriate playbook (trend-follow, MR, or flat/no-trade).

### 3.2 Factor-veto hierarchy
- **Regime veto** → **Risk veto** → **Signal confirmation** → **Execution gates**.
- Any veto failure cancels entry regardless of signal score.

### 3.3 Anti-leakage requirements for factors
- Indicators are computed using current and past bars only.
- No centered windows for decision features.
- No future candles for swing/structure validation.
- Multi-timeframe merges must use aligned, closed higher-timeframe candles only.

---

## 4) Risk, Exposure, and Performance Contract

### 4.1 Risk budget per trade (mandatory declaration)
For each strategy style cell:
- Define **base risk per trade** (e.g., 0.25%–1.00% of equity).
- Convert stop distance to position size using volatility-adjusted stop.
- If volatility exceeds threshold, reduce size or skip trade.

**Initial envelope (research default):**
- Conservative: 0.25%–0.50% equity risk/trade
- Progressive: 0.50%–0.75% equity risk/trade
- Aggressive: 0.75%–1.00% equity risk/trade

### 4.2 Max concurrent exposure
- Cap simultaneous open risk across all pairs and both directions.
- Research default:
  - Conservative: <= 1.25% total open risk
  - Progressive: <= 2.00% total open risk
  - Aggressive: <= 3.00% total open risk
- Add pair concentration cap (e.g., single symbol <= 50% of total risk budget).

### 4.3 Exit architecture (must exist in every strategy)
- **Hard stoploss**: fixed catastrophic fail-safe.
- **Adaptive/trailing component**: engages after favorable excursion threshold.
- **Time stop**: optional but recommended for stale trades.
- **Regime flip exit**: optional but recommended (exit when regime invalidates setup).

### 4.4 Performance gates (research promotion criteria)
A strategy advances only if all are true in OOS windows:
1. Profit Factor > 1.5
2. Win rate within style band (§2.3)
3. Max drawdown <= style DD cap (§2.3)
4. Net expectancy remains positive after fee/slippage stress.

---

## 5) Protections Schema Contract (mandatory)

Every strategy must define protections conceptually equivalent to:
1. **Cooldown period** after trade close to prevent immediate churn.
2. **Stoploss guard** to halt new entries after clustered stopouts.
3. **Low-profit-pairs filter** to throttle/disable underperforming symbols over lookback.

Recommended add-ons:
- Max drawdown protection window
- Pair lock after high volatility loss event
- Daily loss cap (session-level breaker)

---

## 6) Validation Protocol (C)

### 6.1 Data partitioning
- Use strict chronological split with no shuffle:
  - **Train**: initial development segment
  - **Validation**: parameter/model selection segment
  - **Test (holdout)**: untouched final evaluation segment
- Minimum expected sample quality:
  - multiple volatility regimes
  - bull, bear, and range periods
  - include funding regime diversity when available

### 6.2 Rolling walk-forward
- Use rolling or anchored walk-forward cycles:
  1. fit/tune on window _W1_
  2. test on forward window _T1_
  3. roll forward and repeat
- Promotion requires consistency across cycles (not one outstanding slice).

### 6.3 Sensitivity and stability checks
- Parameter perturbation tests (±10–20% around chosen values).
- Cost stress tests (fee + slippage increments).
- Execution delay simulation proxy (late fill / missed fill assumptions).
- Pair-wise robustness (BTC-only, ETH-only, SOL-only, combined portfolio).

### 6.4 Acceptance standard
- No single-parameter fragility.
- No heavy dependence on one symbol or one regime.
- OOS degradation acceptable only within predefined tolerance band.

---

## 7) Failure-Mode Checklist (D)

Before any strategy is considered deployable, explicitly evaluate:
1. **Slippage sensitivity**
   - Does edge survive realistic taker-heavy conditions in high-vol windows?
2. **Fee drag**
   - Is turnover too high for net expectancy after fees?
3. **Funding impact**
   - For perp holding periods, does funding invert edge in persistent bias regimes?
4. **Regime break risk**
   - Does strategy fail abruptly when transitioning trend↔range or low↔high vol?
5. **Correlation clustering**
   - BTC/ETH/SOL co-move can inflate portfolio tail risk despite per-trade controls.
6. **Liquidation proximity / leverage misuse**
   - Ensure stop distance and leverage assumptions are consistent with liquidation buffer.
7. **Data quality artifacts**
   - Missing candles, timestamp drift, bad volume spikes, symbol mapping errors.

---

## 8) Binance-First Implementation Notes

1. **Instrument conventions**
   - Use Binance futures pair notation compatible with Freqtrade futures mode.
2. **Cost model**
   - Include realistic maker/taker and slippage assumptions in backtests.
3. **Liquidity gating**
   - Require minimum rolling notional/volume thresholds per pair.
4. **Funding-aware holding bias**
   - For LF styles, include optional funding penalty filter in trade selection.

---

## 9) Hyperliquid Adaptation Notes (Research-only in v1)

When porting Binance-first strategies to Hyperliquid:
1. Recalibrate fee/slippage/fill assumptions (market microstructure differs).
2. Revalidate latency and order execution assumptions for short-horizon styles.
3. Re-estimate volatility and spread regimes per instrument.
4. Re-run full walk-forward and sensitivity battery before any deployment claim.
5. Keep identical anti-leakage controls and risk contract; only venue parameters adapt.

---

## 10) Deliverables for Next Phase (Code Phase Gate)

No strategy code is written until this contract is accepted. After acceptance, phase-2 deliverables will be:
1. Freqtrade strategy templates for selected style cells (starting MF-C and MF-P).
2. Shared risk/protections mixin pattern (still Freqtrade-native strategy files).
3. Backtest config packs (Binance futures) for BTC/ETH/SOL.
4. Validation report template: IS/OOS, walk-forward, sensitivity, failure-mode scoring.

---

## 11) Sign-off Criteria

This Research Contract v1.0 is accepted when:
- Taxonomy (A), factor map (B), validation protocol (C), and failure checklist (D) are approved.
- Performance gates and risk caps are explicitly acknowledged as binding.
- Binance-first scope and Hyperliquid adaptation-only scope are confirmed.

