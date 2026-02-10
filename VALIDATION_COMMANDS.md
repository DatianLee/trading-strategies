# VALIDATION COMMANDS

All commands assume repository root and Freqtrade installed.

## 0) Core data download (Binance futures, focus assets)

```bash
freqtrade download-data \
  --userdir user_data \
  --exchange binance \
  --trading-mode futures \
  --timeframes 1m 15m 1h 4h 1d \
  --pairs BTC/USDT:USDT ETH/USDT:USDT SOL/USDT:USDT \
  --timerange 20230101-
```

## 1) Gate thresholds by strategy tier

- Conservative (S1, S3, S5): `max-dd 0.10`, `max-profit-factor-delta 0.55`, `max-winrate-delta 0.10`
- Progressive (S4, S6, S8): `max-dd 0.12`, `max-profit-factor-delta 0.65`, `max-winrate-delta 0.12`
- Aggressive/Event (S2, S7, S9, S10): `max-dd 0.16`, `max-profit-factor-delta 0.80`, `max-winrate-delta 0.15`

## 2) Per-strategy backtest + gate commands (template)

```bash
# Train
freqtrade backtesting \
  --config user_data/configs/SX_config_stub.json \
  --strategy STRATEGY_CLASS \
  --timerange 20230101-20240630 \
  --export trades \
  --backtest-filename user_data/backtest_results/SX_train.json

# Test
freqtrade backtesting \
  --config user_data/configs/SX_config_stub.json \
  --strategy STRATEGY_CLASS \
  --timerange 20240701-20241231 \
  --export trades \
  --backtest-filename user_data/backtest_results/SX_test.json

# Gate
python scripts/validate_backtest_gates.py \
  --strategy SX \
  --train user_data/backtest_results/SX_train.json \
  --test user_data/backtest_results/SX_test.json \
  --max-dd <TIER_MAX_DD> \
  --max-profit-factor-delta <TIER_PF_DELTA> \
  --max-winrate-delta <TIER_WIN_DELTA>
```

## 3) Concrete strategy map

| ID | Strategy class | Config |
|---|---|---|
| S1 | `S1_HFT_Conservative_MicroTrend_Scalper` | `user_data/configs/S1_config_stub.json` |
| S2 | `S2_HFT_Aggressive_MeanReversion_Fade` | `user_data/configs/S2_config_stub.json` |
| S3 | `S3_MFT_Conservative_TrendPullback` | `user_data/configs/S3_config_stub.json` |
| S4 | `S4_MFT_Progressive_BreakoutRetest` | `user_data/configs/S4_config_stub.json` |
| S5 | `S5_LFT_Conservative_MTF_TrendReversal` | `user_data/configs/S5_config_stub.json` |
| S6 | `S6_LFT_Progressive_Momentum_Rotation` | `user_data/configs/S6_config_stub.json` |
| S7 | `S7_Event_Volatility_Shock_Strategy` | `user_data/configs/S7_config_stub.json` |
| S8 | `S8_HFT_Progressive_Orderflow_Impulse` | `user_data/configs/S8_config_stub.json` |
| S9 | `S9_MFT_Aggressive_TrendAcceleration` | `user_data/configs/S9_config_stub.json` |
| S10 | `S10_LFT_Aggressive_RegimeSwitch_Trend` | `user_data/configs/S10_config_stub.json` |

## 4) Hyperopt sanity run (example)

```bash
freqtrade hyperopt \
  --config user_data/configs/S1_config_stub.json \
  --strategy S1_HFT_Conservative_MicroTrend_Scalper \
  --spaces buy sell stoploss trailing \
  --hyperopt-loss SharpeHyperOptLossDaily \
  --epochs 100
```

## 5) Dry-run smoke test (example)

```bash
freqtrade trade \
  --config user_data/configs/S1_config_stub.json \
  --strategy S1_HFT_Conservative_MicroTrend_Scalper \
  --dry-run
```

## 6) Hyperliquid adaptation note retention

- Keep identical strategy logic; adjust only:
  - exchange connector/config,
  - symbol format,
  - fee/slippage/funding assumptions,
  - min-notional and leverage limits.
- Re-run the same train/test gate cycle before enabling live execution.

