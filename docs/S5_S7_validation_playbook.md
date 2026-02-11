# Validation Playbook for S5/S6/S7 Futures Strategies

[中文版本 / Chinese Version](./zh/S5_S7_Validation_Playbook_CN.md)

## 1) Walk-forward template (multi-window)

Use identical exchange, pairs, and fee assumptions for all windows.

### Suggested windows

- Window A: Train 2021-01-01 to 2022-12-31, Test 2023-01-01 to 2023-06-30
- Window B: Train 2021-07-01 to 2023-06-30, Test 2023-07-01 to 2023-12-31
- Window C: Train 2022-01-01 to 2023-12-31, Test 2024-01-01 to 2024-06-30
- Window D: Train 2022-07-01 to 2024-06-30, Test 2024-07-01 to 2024-12-31

### Command template

```bash
freqtrade backtesting \
  -c user_data/configs/S5_config_stub.json \
  --strategy S5_LFT_Conservative_MTF_TrendReversal \
  --timerange 20230101-20230630 \
  --export trades
```

Repeat for `S6_LFT_Progressive_Momentum_Rotation` and `S7_Event_Volatility_Shock_Strategy`.

### Walk-forward acceptance checks

- Profitable windows ratio >= 0.60 (at least 3 of 5 windows if you run 5 splits).
- Median test Sharpe >= 0.8.
- Worst-window max drawdown <= 18%.
- Profit factor >= 1.15 in at least 70% of test windows.

---

## 2) Monte Carlo trade-sequence stress (shuffle returns)

Purpose: stress path dependence and verify robustness under sequencing uncertainty.

### Pseudo-procedure

1. Export closed trade returns from each backtest window.
2. For each strategy/window:
   - Run `N = 2000` simulations.
   - Shuffle trade return order with replacement (bootstrap) or without replacement (pure permutation).
   - Rebuild equity curve from identical starting capital.
3. Store distribution metrics:
   - CAGR distribution
   - max drawdown distribution
   - terminal equity distribution
4. Compare baseline backtest vs Monte Carlo quantiles.

### Acceptance checks

- Baseline terminal equity should be above Monte Carlo 35th percentile.
- Monte Carlo 95th percentile max drawdown <= 25%.
- Probability of ending below initial capital <= 20%.

---

## 3) Parameter stability heatmap plan

Run controlled hyperopt grids and map out smoothness (no narrow spikes).

### Axes per strategy

- S5 heatmap axes:
  - X: `adx_min` (18..38)
  - Y: `volatility_ceiling` (0.01..0.08)
  - Metric: median OOS profit factor across windows
- S6 heatmap axes:
  - X: `momentum_window` (12..72)
  - Y: `rs_threshold` (0.002..0.08)
  - Metric: median OOS Sharpe across windows
- S7 heatmap axes:
  - X: volatility burst quantile threshold (e.g. 0.80..0.95)
  - Y: volume spike multiplier (1.5..2.8)
  - Metric: OOS Calmar ratio

### Acceptance checks

- At least 25% of tested cells satisfy minimum criteria (PF >= 1.1 and MDD <= 20%).
- Best-cell performance is not more than 35% above median of top quartile cells (anti-overfit guard).
- Neighboring-cell degradation should be gradual: no more than 20% metric drop for a ±1 grid step in both directions.

---

## 4) Objective rejection criteria (hard fail list)

Reject strategy configuration if **any** condition is true:

1. Net profit <= 0 in >= 40% of walk-forward test windows.
2. Single-window max drawdown > 20%.
3. Profit factor < 1.05 in >= 50% of test windows.
4. Monte Carlo probability(terminal equity < initial equity) > 25%.
5. Median trade duration > 96h for S5/S6 or > 24h for S7 (execution drift warning).
6. Exposure concentration: top single pair contributes > 55% of total PnL.
7. More than 3 consecutive kill-switch weeks in live-paper forward test.

---

## 5) Notebook-style implementation skeleton

```python
# 1) Load exported trades from all walk-forward windows
trades = load_trades_csv("results/s5_windowA_trades.csv")

# 2) Compute baseline metrics
metrics = compute_metrics(trades)

# 3) Monte Carlo sequence stress
sim_curves = monte_carlo_shuffle(trades["return"], n=2000, mode="bootstrap")
mc_stats = summarize_mc(sim_curves)

# 4) Parameter heatmap aggregation
heatmap = aggregate_hyperopt_grid("results/s5_grid.json")
plot_heatmap(heatmap, x="adx_min", y="volatility_ceiling", value="oos_pf")

# 5) Apply rejection criteria
status = evaluate_rejection_rules(metrics, mc_stats)
print(status)
```
