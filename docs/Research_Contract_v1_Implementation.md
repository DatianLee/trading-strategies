# Research Contract v1.0 - Freqtrade Futures Strategy Pack

## Folder Tree

```text
user_data/
  strategies/
    S1_HFT_Conservative_MicroTrend_Scalper.py
    S2_HFT_Aggressive_MeanReversion_Fade.py
    S3_MFT_Conservative_TrendPullback.py
    S4_MFT_Progressive_BreakoutRetest.py
  configs/
    S1_config_stub.json
    S2_config_stub.json
    S3_config_stub.json
    S4_config_stub.json
scripts/
  validate_backtest_gates.py
docs/
  Research_Contract_v1_Implementation.md
```

## Protection Set and Purpose

- **CooldownPeriod**: Prevents immediate re-entry after exit to reduce revenge trading and micro-chop re-triggering.
- **StoplossGuard**: Pauses trading after clustered stoplosses to avoid regime mismatch spirals.
- **MaxDrawdown**: Portfolio-level hard brake when rolling drawdown exceeds strategy tolerance.
- **LowProfitPairs**: Temporarily blocks weak pairs when rolling profitability is below required threshold.

## Regime Filters

- **Trend strategies (S1, S3, S4) avoid chop** using ADX floors, ATR floors, and HTF trend confirmation.
- **Mean-reversion strategy (S2) avoids one-way trend** using ADX ceiling and EMA slope cap.

## Backtest Commands (exact)

### S1
```bash
freqtrade backtesting \
  --config user_data/configs/S1_config_stub.json \
  --strategy S1_HFT_Conservative_MicroTrend_Scalper \
  --timeframe 1m \
  --timerange 20240101-20240630 \
  --export trades \
  --backtest-filename user_data/backtest_results/S1_train.json

freqtrade backtesting \
  --config user_data/configs/S1_config_stub.json \
  --strategy S1_HFT_Conservative_MicroTrend_Scalper \
  --timeframe 1m \
  --timerange 20240701-20240930 \
  --export trades \
  --backtest-filename user_data/backtest_results/S1_test.json
```

### S2
```bash
freqtrade backtesting \
  --config user_data/configs/S2_config_stub.json \
  --strategy S2_HFT_Aggressive_MeanReversion_Fade \
  --timeframe 1m \
  --timerange 20240101-20240630 \
  --export trades \
  --backtest-filename user_data/backtest_results/S2_train.json

freqtrade backtesting \
  --config user_data/configs/S2_config_stub.json \
  --strategy S2_HFT_Aggressive_MeanReversion_Fade \
  --timeframe 1m \
  --timerange 20240701-20240930 \
  --export trades \
  --backtest-filename user_data/backtest_results/S2_test.json
```

### S3
```bash
freqtrade backtesting \
  --config user_data/configs/S3_config_stub.json \
  --strategy S3_MFT_Conservative_TrendPullback \
  --timeframe 15m \
  --timerange 20230101-20240630 \
  --export trades \
  --backtest-filename user_data/backtest_results/S3_train.json

freqtrade backtesting \
  --config user_data/configs/S3_config_stub.json \
  --strategy S3_MFT_Conservative_TrendPullback \
  --timeframe 15m \
  --timerange 20240701-20241231 \
  --export trades \
  --backtest-filename user_data/backtest_results/S3_test.json
```

### S4
```bash
freqtrade backtesting \
  --config user_data/configs/S4_config_stub.json \
  --strategy S4_MFT_Progressive_BreakoutRetest \
  --timeframe 15m \
  --timerange 20230101-20240630 \
  --export trades \
  --backtest-filename user_data/backtest_results/S4_train.json

freqtrade backtesting \
  --config user_data/configs/S4_config_stub.json \
  --strategy S4_MFT_Progressive_BreakoutRetest \
  --timeframe 15m \
  --timerange 20240701-20241231 \
  --export trades \
  --backtest-filename user_data/backtest_results/S4_test.json
```

## Hyperopt Commands (parameter spaces)

```bash
freqtrade hyperopt --config user_data/configs/S1_config_stub.json --strategy S1_HFT_Conservative_MicroTrend_Scalper --spaces buy sell stoploss trailing --hyperopt-loss SharpeHyperOptLossDaily --epochs 200
freqtrade hyperopt --config user_data/configs/S2_config_stub.json --strategy S2_HFT_Aggressive_MeanReversion_Fade --spaces buy sell stoploss trailing --hyperopt-loss SharpeHyperOptLossDaily --epochs 200
freqtrade hyperopt --config user_data/configs/S3_config_stub.json --strategy S3_MFT_Conservative_TrendPullback --spaces buy sell stoploss trailing --hyperopt-loss SharpeHyperOptLossDaily --epochs 200
freqtrade hyperopt --config user_data/configs/S4_config_stub.json --strategy S4_MFT_Progressive_BreakoutRetest --spaces buy sell stoploss trailing --hyperopt-loss SharpeHyperOptLossDaily --epochs 200
```

## Expected Report Table Template

| Strategy | Dataset | Win Rate | Profit Factor | Max Drawdown | Expectancy | Trade Count |
|---|---|---:|---:|---:|---:|---:|
| S1 | Train | ... | ... | ... | ... | ... |
| S1 | Test | ... | ... | ... | ... | ... |
| S2 | Train | ... | ... | ... | ... | ... |
| S2 | Test | ... | ... | ... | ... | ... |
| S3 | Train | ... | ... | ... | ... | ... |
| S3 | Test | ... | ... | ... | ... | ... |
| S4 | Train | ... | ... | ... | ... | ... |
| S4 | Test | ... | ... | ... | ... | ... |

## Pass/Fail Gates (overfit + drawdown)

```bash
python scripts/validate_backtest_gates.py \
  --strategy S1 --train user_data/backtest_results/S1_train.json --test user_data/backtest_results/S1_test.json \
  --max-dd 0.10 --max-profit-factor-delta 0.60 --max-winrate-delta 0.12
python scripts/validate_backtest_gates.py \
  --strategy S2 --train user_data/backtest_results/S2_train.json --test user_data/backtest_results/S2_test.json \
  --max-dd 0.12 --max-profit-factor-delta 0.75 --max-winrate-delta 0.15
python scripts/validate_backtest_gates.py \
  --strategy S3 --train user_data/backtest_results/S3_train.json --test user_data/backtest_results/S3_test.json \
  --max-dd 0.15 --max-profit-factor-delta 0.50 --max-winrate-delta 0.10
python scripts/validate_backtest_gates.py \
  --strategy S4 --train user_data/backtest_results/S4_train.json --test user_data/backtest_results/S4_test.json \
  --max-dd 0.14 --max-profit-factor-delta 0.55 --max-winrate-delta 0.12
```

A strategy is **REJECTED** if:
1. Test max drawdown exceeds `--max-dd`.
2. Absolute train-test profit factor delta exceeds `--max-profit-factor-delta`.
3. Absolute train-test win rate delta exceeds `--max-winrate-delta`.

---

## Strategy Cards

### S1 — HFT Conservative Micro-Trend Scalper
- **Universe**: BTC/ETH/SOL USDT-margined futures.
- **Timeframes**: 1m execution; 3m/5m confirmation.
- **Edge hypothesis**: short burst continuation with HTF alignment and volume confirmation.
- **Key assumptions**: tight spread, low slippage windows, trend persistence for 3-20 minutes.
- **Failure modes**: low-liquidity chop, abrupt reversal headlines, latency spikes.

### S2 — HFT Aggressive Mean-Reversion Fade
- **Universe**: BTC/ETH/SOL USDT-margined futures.
- **Timeframes**: 1m execution; implicit 5m trend via slope proxy.
- **Edge hypothesis**: fast reversion from short-term overextension.
- **Key assumptions**: no strong one-way regime, fills close to touch, bounded drift.
- **Failure modes**: trend days, liquidation cascades, volatility regime shift upward.

### S3 — MFT Conservative Trend-Pullback
- **Universe**: BTC/ETH/SOL USDT-margined futures.
- **Timeframes**: 15m execution; 1h trend gate.
- **Edge hypothesis**: buy/sell pullbacks in established HTF trend.
- **Key assumptions**: ADX confirms trend quality, pullbacks are corrective not structural breaks.
- **Failure modes**: range transitions, failed continuation, macro-event gaps.

### S4 — MFT Progressive Breakout-Retest
- **Universe**: BTC/ETH/SOL USDT-margined futures.
- **Timeframes**: 15m breakout logic; 1h trend confidence.
- **Edge hypothesis**: breakout confirmation after retest reduces false breaks.
- **Key assumptions**: breakouts hold prior extremes and momentum remains active.
- **Failure modes**: fakeouts in high-noise sessions, low-volume breakouts, ADX collapses.
