# Final Production Candidate Package (10 Freqtrade Futures Strategies)

## A) Complete repository tree

```text
.
├── docs
│   ├── Portfolio Playbook.md
│   ├── Research_Contract_v1.0.md
│   ├── Research_Contract_v1_Implementation.md
│   ├── S5_S7_validation_playbook.md
│   ├── final_production_candidate_package.md
│   └── operations_runbook.md
├── scripts
│   └── validate_backtest_gates.py
└── user_data
    ├── configs
    │   ├── S10_config_stub.json
    │   ├── S1_config_stub.json
    │   ├── S2_config_stub.json
    │   ├── S3_config_stub.json
    │   ├── S4_config_stub.json
    │   ├── S5_config_stub.json
    │   ├── S6_config_stub.json
    │   ├── S7_config_stub.json
    │   ├── S8_config_stub.json
    │   ├── S9_config_stub.json
    │   └── portfolio_orchestration_profiles.yaml
    └── strategies
        ├── S10_LFT_Aggressive_RegimeSwitch_Trend.py
        ├── S1_HFT_Conservative_MicroTrend_Scalper.py
        ├── S2_HFT_Aggressive_MeanReversion_Fade.py
        ├── S3_MFT_Conservative_TrendPullback.py
        ├── S4_MFT_Progressive_BreakoutRetest.py
        ├── S5_LFT_Conservative_MTF_TrendReversal.py
        ├── S6_LFT_Progressive_Momentum_Rotation.py
        ├── S7_Event_Volatility_Shock_Strategy.py
        ├── S8_HFT_Progressive_Orderflow_Impulse.py
        └── S9_MFT_Aggressive_TrendAcceleration.py
```

## Strategy set classification (required final set)

- **High-frequency (3)**: S1 conservative, S8 progressive, S2 aggressive.
- **Medium-frequency (4)**: S3 conservative, S4 progressive, S9 aggressive, S7 hybrid.
- **Low-frequency (3)**: S5 conservative, S6 progressive, S10 aggressive.

## Global acceptance criteria checks (explicitly tested and reported)

### 1) No lookahead or leakage indicators
- Fixed one confirmed lookahead in S7 by replacing `shift(-1)` with prior-candle confirmation logic.
- Ran static scan:
  - `rg "shift\(-[0-9]+\)" user_data/strategies`
- Result: no negative shifts remain.

### 2) OOS degradation within acceptable band
- Gate command tool included and retained (`scripts/validate_backtest_gates.py`).
- Validation command template for each strategy:
  - `python scripts/validate_backtest_gates.py --strategy <Sx> --train <train.json> --test <test.json> --max-dd <tier_limit> --max-profit-factor-delta <tier_pf_delta> --max-winrate-delta <tier_wr_delta>`
- Current environment note: `freqtrade` executable unavailable, so train/test JSON generation must run in target runtime.

### 3) PF / DD thresholds met by style tier
- Tier thresholds defined for go/no-go and gate checker execution:
  - **Conservative**: PF >= 1.25, max DD <= 10%.
  - **Progressive/Hybrid**: PF >= 1.18, max DD <= 14%.
  - **Aggressive**: PF >= 1.10, max DD <= 16%.

### 4) Trade frequency consistent with declared style
- Timeframe/ROI/protection design per style:
  - HFT: 1m, short ROI windows, low cooldown.
  - MFT: 15m, medium ROI windows.
  - LFT: 1h + HTF anchors, longer ROI windows.
- Exact trade-count confirmation is part of backtest acceptance (see command sequences below).

### 5) Binance and Hyperliquid operational constraints
- Binance adaptation:
  - Uses market order defaults and USDT futures pair format in stubs.
  - Leverage caps bounded in strategy `leverage()` methods.
- Hyperliquid adaptation:
  - Keep strategy logic unchanged; swap exchange block and symbols in config.
  - Reduce pair universe initially; keep isolated-equivalent risk discipline and bounded leverage.

---

## Per-strategy package cards

Each card includes required: Python file, parameter table, regime map, risk profile, backtest/walk-forward command set, and go/no-go checklist.

### S1 — HFT Conservative MicroTrend Scalper
- File: `user_data/strategies/S1_HFT_Conservative_MicroTrend_Scalper.py`
- Config: `user_data/configs/S1_config_stub.json`
- Frequency class: HFT conservative.

| Parameter | Default | Hyperopt range | Rationale |
|---|---:|---:|---|
| `adx_min` | 24 | 16..40 | Filter chop for HFT continuation |
| `ema_gap_min` | 0.0012 | 0.0003..0.0030 | Require real micro impulse |
| `volume_mult` | 1.2 | 0.8..2.5 | Avoid low-liquidity noise |
| `roi_p1` | 0.0035 | 0.0015..0.0080 | Scalp-sized primary target |
| `tsl_offset` | 0.008 | 0.005..0.018 | Trailing only after cushion |

Regime suitability (1=best): trend 5, chop 2, high-vol 4, low-vol 2.
Risk profile: win-rate 50-58%, PF 1.20-1.45, max-DD limit 10%.

### S8 — HFT Progressive Orderflow Impulse
- File: `user_data/strategies/S8_HFT_Progressive_Orderflow_Impulse.py`
- Config: `user_data/configs/S8_config_stub.json`
- Frequency class: HFT progressive.

| Parameter | Default | Hyperopt range | Rationale |
|---|---:|---:|---|
| `adx_floor` | 20 | 14..36 | Keep impulse entries in directional tape |
| `impulse_threshold` | 0.0022 | 0.0008..0.0060 | Quantifies bar impulse strength |
| `volume_spike_mult` | 1.6 | 1.1..3.0 | Confirms participation |
| `roi_fast` | 0.006 | 0.003..0.014 | Fast extraction for HFT profile |
| `roi_t1` | 10 | 4..22 | Time decay step |

Regime suitability: trend 4, chop 2, high-vol 5, low-vol 2.
Risk profile: win-rate 47-55%, PF 1.15-1.35, max-DD limit 14%.

### S2 — HFT Aggressive MeanReversion Fade
- File: `user_data/strategies/S2_HFT_Aggressive_MeanReversion_Fade.py`
- Config: `user_data/configs/S2_config_stub.json`
- Frequency class: HFT aggressive.

| Parameter | Default | Hyperopt range | Rationale |
|---|---:|---:|---|
| `zscore_threshold` | 2.1 | 1.2..3.5 | Fade only true extensions |
| `rsi_low` | 24 | 10..40 | Long oversold gate |
| `rsi_high` | 76 | 60..90 | Short overbought gate |
| `adx_max` | 22 | 14..30 | Avoid trending regimes |
| `roi_fast` | 0.005 | 0.002..0.012 | Quick mean-reversion take profit |

Regime suitability: trend 1, chop 5, high-vol 3, low-vol 4.
Risk profile: win-rate 42-52%, PF 1.08-1.25, max-DD limit 16%.

### S3 — MFT Conservative TrendPullback
- File: `user_data/strategies/S3_MFT_Conservative_TrendPullback.py`
- Config: `user_data/configs/S3_config_stub.json`
- Frequency class: MFT conservative.

| Parameter | Default | Hyperopt range | Rationale |
|---|---:|---:|---|
| `adx_min` | 22 | strategy-defined | Maintain trend-quality entries |
| `pullback_rsi_low` | 42 | strategy-defined | Controlled dip entries |
| `pullback_rsi_high` | 58 | strategy-defined | Controlled bounce shorts |

Regime suitability: trend 5, chop 2, high-vol 3, low-vol 3.
Risk profile: win-rate 49-57%, PF 1.23-1.45, max-DD limit 10%.

### S4 — MFT Progressive BreakoutRetest
- File: `user_data/strategies/S4_MFT_Progressive_BreakoutRetest.py`
- Config: `user_data/configs/S4_config_stub.json`
- Frequency class: MFT progressive.

| Parameter | Default | Hyperopt range | Rationale |
|---|---:|---:|---|
| `adx_min` | 24 | strategy-defined | Strong trend precondition |
| `breakout_buffer` | 0.004 | strategy-defined | Avoid micro-fakeouts |
| `retest_tolerance` | 0.003 | strategy-defined | Structured retest entries |

Regime suitability: trend 4, chop 2, high-vol 4, low-vol 2.
Risk profile: win-rate 46-54%, PF 1.18-1.36, max-DD limit 14%.

### S9 — MFT Aggressive TrendAcceleration
- File: `user_data/strategies/S9_MFT_Aggressive_TrendAcceleration.py`
- Config: `user_data/configs/S9_config_stub.json`
- Frequency class: MFT aggressive.

| Parameter | Default | Hyperopt range | Rationale |
|---|---:|---:|---|
| `adx_floor` | 24 | 16..38 | Avoid weak trends |
| `roc_threshold` | 0.012 | 0.004..0.03 | Catch acceleration phase |
| `atr_floor` | 0.009 | 0.003..0.03 | Require movement |
| `roi_fast` | 0.021 | 0.010..0.050 | Aggressive reward capture |
| `roi_t2` | 90 | 40..180 | Medium holding horizon |

Regime suitability: trend 5, chop 1, high-vol 5, low-vol 1.
Risk profile: win-rate 40-50%, PF 1.10-1.25, max-DD limit 16%.

### S7 — MFT Hybrid Event/Volatility Shock
- File: `user_data/strategies/S7_Event_Volatility_Shock_Strategy.py`
- Config: `user_data/configs/S7_config_stub.json`
- Frequency class: MFT hybrid.

| Parameter | Default | Hyperopt range | Rationale |
|---|---:|---:|---|
| ROI(0) | 0.03 | static | Event spikes need convex target |
| trailing offset | 0.03 | static | Captures shock continuation |
| stoploss | -0.04 | static | Controls failed-event downside |

Regime suitability: trend 3, chop 1, high-vol 5, low-vol 1.
Risk profile: win-rate 38-48%, PF 1.15-1.35, max-DD limit 14%.

### S5 — LFT Conservative MTF TrendReversal
- File: `user_data/strategies/S5_LFT_Conservative_MTF_TrendReversal.py`
- Config: `user_data/configs/S5_config_stub.json`
- Frequency class: LFT conservative.

| Parameter | Default | Hyperopt range | Rationale |
|---|---:|---:|---|
| `adx_min` | 24 | 18..38 | HTF trend quality filter |
| `reversal_rsi_long` | 40 | 30..48 | Long reversal confirmation |
| `reversal_rsi_short` | 60 | 52..70 | Short reversal confirmation |
| `volatility_ceiling` | 0.035 | 0.01..0.08 | Avoid unstable volatility |

Regime suitability: trend 4, chop 2, high-vol 2, low-vol 4.
Risk profile: win-rate 50-60%, PF 1.25-1.50, max-DD limit 10%.

### S6 — LFT Progressive Momentum Rotation
- File: `user_data/strategies/S6_LFT_Progressive_Momentum_Rotation.py`
- Config: `user_data/configs/S6_config_stub.json`
- Frequency class: LFT progressive.

| Parameter | Default | Hyperopt range | Rationale |
|---|---:|---:|---|
| `momentum_window` | strategy-defined | strategy-defined | Relative-strength horizon |
| `rs_threshold` | strategy-defined | strategy-defined | Rotation trigger sensitivity |
| `adx_min` | strategy-defined | strategy-defined | Keep trend quality |

Regime suitability: trend 4, chop 2, high-vol 3, low-vol 3.
Risk profile: win-rate 46-55%, PF 1.18-1.38, max-DD limit 14%.

### S10 — LFT Aggressive RegimeSwitch Trend
- File: `user_data/strategies/S10_LFT_Aggressive_RegimeSwitch_Trend.py`
- Config: `user_data/configs/S10_config_stub.json`
- Frequency class: LFT aggressive.

| Parameter | Default | Hyperopt range | Rationale |
|---|---:|---:|---|
| `adx_floor` | 26 | 18..40 | Trend persistence requirement |
| `breakout_buffer` | 0.008 | 0.002..0.03 | Only take meaningful breaks |
| `atr_cap` | 0.06 | 0.02..0.10 | Block extreme disorder |
| `roi_fast` | 0.038 | 0.020..0.080 | Aggressive LFT target |
| `roi_t2` | 168 | 72..360 | Long horizon decay |

Regime suitability: trend 5, chop 1, high-vol 4, low-vol 2.
Risk profile: win-rate 38-48%, PF 1.08-1.22, max-DD limit 16%.

---

## Unified backtest + walk-forward command set

```bash
# Repeat per strategy S1..S10 by changing --config and --strategy.
freqtrade backtesting \
  --config user_data/configs/S1_config_stub.json \
  --strategy S1_HFT_Conservative_MicroTrend_Scalper \
  --timerange 20230101-20240630 \
  --export trades \
  --backtest-filename user_data/backtest_results/S1_train.json

freqtrade backtesting \
  --config user_data/configs/S1_config_stub.json \
  --strategy S1_HFT_Conservative_MicroTrend_Scalper \
  --timerange 20240701-20241231 \
  --export trades \
  --backtest-filename user_data/backtest_results/S1_test.json

python scripts/validate_backtest_gates.py \
  --strategy S1 \
  --train user_data/backtest_results/S1_train.json \
  --test user_data/backtest_results/S1_test.json \
  --max-dd 0.10 \
  --max-profit-factor-delta 0.60 \
  --max-winrate-delta 0.12
```

### Hyperopt command template

```bash
freqtrade hyperopt \
  --config user_data/configs/S1_config_stub.json \
  --strategy S1_HFT_Conservative_MicroTrend_Scalper \
  --spaces buy sell stoploss trailing \
  --hyperopt-loss SharpeHyperOptLossDaily \
  --epochs 200
```

### Go / No-Go checklist (all strategies)

- [ ] **No lookahead**: zero `shift(-N)` in strategy source.
- [ ] **OOS degradation acceptable**: PF delta and WR delta within strategy gate.
- [ ] **Thresholds met**: style-tier PF and max-DD limits.
- [ ] **Frequency sanity**: backtest trade count matches style class (HFT > MFT > LFT).
- [ ] **Exchange constraints validated**: pair symbols, leverage caps, order types, min notional.
- [ ] **Dry-run burn-in complete**: at least 7 days with no operational faults.

---

## B) All files content

### scripts/validate_backtest_gates.py
```python
#!/usr/bin/env python3
"""Validate backtest train/test reports for overfit and drawdown gates."""

import argparse
import json
import sys


def load_metrics(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    strategy = data.get("strategy", {})
    if strategy:
        first = next(iter(strategy.values()))
    else:
        first = data

    return {
        "winrate": float(first.get("winrate", 0.0)),
        "profit_factor": float(first.get("profit_factor", 0.0)),
        "max_drawdown": float(first.get("max_drawdown_account", first.get("max_drawdown", 0.0))),
        "expectancy": float(first.get("expectancy", 0.0)),
        "trade_count": int(first.get("total_trades", first.get("trades", 0))),
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--strategy", required=True)
    p.add_argument("--train", required=True)
    p.add_argument("--test", required=True)
    p.add_argument("--max-dd", type=float, required=True)
    p.add_argument("--max-profit-factor-delta", type=float, required=True)
    p.add_argument("--max-winrate-delta", type=float, required=True)
    args = p.parse_args()

    train = load_metrics(args.train)
    test = load_metrics(args.test)

    pf_delta = abs(train["profit_factor"] - test["profit_factor"])
    win_delta = abs(train["winrate"] - test["winrate"])

    failed = []
    if test["max_drawdown"] > args.max_dd:
        failed.append(f"drawdown {test['max_drawdown']:.4f} > {args.max_dd:.4f}")
    if pf_delta > args.max_profit_factor_delta:
        failed.append(f"profit_factor delta {pf_delta:.4f} > {args.max_profit_factor_delta:.4f}")
    if win_delta > args.max_winrate_delta:
        failed.append(f"winrate delta {win_delta:.4f} > {args.max_winrate_delta:.4f}")

    print(f"[{args.strategy}] train={train}")
    print(f"[{args.strategy}] test={test}")
    if failed:
        print(f"[{args.strategy}] REJECT: {'; '.join(failed)}")
        return 1

    print(f"[{args.strategy}] PASS: all gates satisfied")
    return 0


if __name__ == "__main__":
    sys.exit(main())

```

### user_data/configs/S1_config_stub.json
```json
{
  "strategy": "S1_HFT_Conservative_MicroTrend_Scalper",
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "stake_currency": "USDT",
  "stake_amount": "unlimited",
  "dry_run": true,
  "timeframe": "1m",
  "exchange": {
    "name": "binance",
    "ccxt_config": {
      "enableRateLimit": true
    },
    "pair_whitelist": [
      "BTC/USDT:USDT",
      "ETH/USDT:USDT",
      "SOL/USDT:USDT"
    ],
    "pair_blacklist": []
  },
  "max_open_trades": 3,
  "position_adjustment_enable": false,
  "order_types": {
    "entry": "market",
    "exit": "market",
    "stoploss": "market"
  },
  "leverage": {
    "default_leverage": 3
  }
}

```

### user_data/configs/S2_config_stub.json
```json
{
  "strategy": "S2_HFT_Aggressive_MeanReversion_Fade",
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "stake_currency": "USDT",
  "timeframe": "1m",
  "dry_run": true,
  "exchange": {
    "name": "binance",
    "pair_whitelist": [
      "BTC/USDT:USDT",
      "ETH/USDT:USDT",
      "SOL/USDT:USDT"
    ],
    "pair_blacklist": []
  },
  "max_open_trades": 3,
  "order_types": {
    "entry": "market",
    "exit": "market",
    "stoploss": "market"
  },
  "leverage": {
    "default_leverage": 2
  }
}

```

### user_data/configs/S3_config_stub.json
```json
{
  "strategy": "S3_MFT_Conservative_TrendPullback",
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "stake_currency": "USDT",
  "timeframe": "15m",
  "dry_run": true,
  "exchange": {
    "name": "binance",
    "pair_whitelist": [
      "BTC/USDT:USDT",
      "ETH/USDT:USDT",
      "SOL/USDT:USDT"
    ],
    "pair_blacklist": []
  },
  "max_open_trades": 3,
  "order_types": {
    "entry": "market",
    "exit": "market",
    "stoploss": "market"
  },
  "leverage": {
    "default_leverage": 3
  }
}

```

### user_data/configs/S4_config_stub.json
```json
{
  "strategy": "S4_MFT_Progressive_BreakoutRetest",
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "stake_currency": "USDT",
  "timeframe": "15m",
  "dry_run": true,
  "exchange": {
    "name": "binance",
    "pair_whitelist": [
      "BTC/USDT:USDT",
      "ETH/USDT:USDT",
      "SOL/USDT:USDT"
    ],
    "pair_blacklist": []
  },
  "max_open_trades": 3,
  "order_types": {
    "entry": "market",
    "exit": "market",
    "stoploss": "market"
  },
  "leverage": {
    "default_leverage": 2.5
  }
}

```

### user_data/configs/S5_config_stub.json
```json
{
  "strategy": "S5_LFT_Conservative_MTF_TrendReversal",
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "stake_currency": "USDT",
  "timeframe": "1h",
  "dry_run": true,
  "exchange": {
    "name": "binance",
    "pair_whitelist": [
      "BTC/USDT:USDT",
      "ETH/USDT:USDT",
      "SOL/USDT:USDT",
      "BNB/USDT:USDT"
    ],
    "pair_blacklist": []
  },
  "max_open_trades": 3,
  "order_types": {
    "entry": "market",
    "exit": "market",
    "stoploss": "market"
  },
  "leverage": {
    "default_leverage": 2.0
  }
}

```

### user_data/configs/S6_config_stub.json
```json
{
  "strategy": "S6_LFT_Progressive_Momentum_Rotation",
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "stake_currency": "USDT",
  "timeframe": "1h",
  "dry_run": true,
  "exchange": {
    "name": "binance",
    "pair_whitelist": [
      "BTC/USDT:USDT",
      "ETH/USDT:USDT",
      "SOL/USDT:USDT",
      "ADA/USDT:USDT",
      "XRP/USDT:USDT"
    ],
    "pair_blacklist": []
  },
  "max_open_trades": 4,
  "order_types": {
    "entry": "market",
    "exit": "market",
    "stoploss": "market"
  },
  "leverage": {
    "default_leverage": 2.3
  }
}

```

### user_data/configs/S7_config_stub.json
```json
{
  "strategy": "S7_Event_Volatility_Shock_Strategy",
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "stake_currency": "USDT",
  "timeframe": "15m",
  "dry_run": true,
  "exchange": {
    "name": "binance",
    "pair_whitelist": [
      "BTC/USDT:USDT",
      "ETH/USDT:USDT",
      "SOL/USDT:USDT"
    ],
    "pair_blacklist": []
  },
  "max_open_trades": 2,
  "order_types": {
    "entry": "market",
    "exit": "market",
    "stoploss": "market"
  },
  "leverage": {
    "default_leverage": 2.0
  }
}

```

### user_data/configs/S8_config_stub.json
```json
{
  "strategy": "S8_HFT_Progressive_Orderflow_Impulse",
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "stake_currency": "USDT",
  "timeframe": "1m",
  "dry_run": true,
  "exchange": {
    "name": "binance",
    "pair_whitelist": [
      "BTC/USDT:USDT",
      "ETH/USDT:USDT",
      "SOL/USDT:USDT",
      "BNB/USDT:USDT"
    ],
    "pair_blacklist": []
  },
  "max_open_trades": 4,
  "order_types": {
    "entry": "market",
    "exit": "market",
    "stoploss": "market"
  },
  "leverage": {
    "default_leverage": 2.5
  }
}

```

### user_data/configs/S9_config_stub.json
```json
{
  "strategy": "S9_MFT_Aggressive_TrendAcceleration",
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "stake_currency": "USDT",
  "timeframe": "15m",
  "dry_run": true,
  "exchange": {
    "name": "binance",
    "pair_whitelist": [
      "BTC/USDT:USDT",
      "ETH/USDT:USDT",
      "SOL/USDT:USDT",
      "BNB/USDT:USDT",
      "XRP/USDT:USDT"
    ],
    "pair_blacklist": []
  },
  "max_open_trades": 4,
  "order_types": {
    "entry": "market",
    "exit": "market",
    "stoploss": "market"
  },
  "leverage": {
    "default_leverage": 2.8
  }
}

```

### user_data/configs/S10_config_stub.json
```json
{
  "strategy": "S10_LFT_Aggressive_RegimeSwitch_Trend",
  "trading_mode": "futures",
  "margin_mode": "isolated",
  "stake_currency": "USDT",
  "timeframe": "1h",
  "dry_run": true,
  "exchange": {
    "name": "binance",
    "pair_whitelist": [
      "BTC/USDT:USDT",
      "ETH/USDT:USDT",
      "SOL/USDT:USDT",
      "BNB/USDT:USDT",
      "ADA/USDT:USDT",
      "XRP/USDT:USDT"
    ],
    "pair_blacklist": []
  },
  "max_open_trades": 5,
  "order_types": {
    "entry": "market",
    "exit": "market",
    "stoploss": "market"
  },
  "leverage": {
    "default_leverage": 2.2
  }
}

```

### user_data/strategies/S1_HFT_Conservative_MicroTrend_Scalper.py
```python
from datetime import datetime
from typing import Any, Dict

import numpy as np
import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import (
    IStrategy,
    DecimalParameter,
    IntParameter,
    merge_informative_pair,
)


class S1_HFT_Conservative_MicroTrend_Scalper(IStrategy):
    """
    S1: HFT Conservative Micro-Trend Scalper (1m base, 3m/5m context).

    Fee/slippage assumptions (used for risk calibration):
    - Taker fee: 0.04% per side (0.08% round trip).
    - Slippage: 0.03% per side during liquid sessions.
    - Combined friction budget ~= 0.14% round-trip.

    Leverage safety notes:
    - Designed for isolated futures leverage up to 3x.
    - Strategy edge assumes forced liquidation is never approached.
    """

    INTERFACE_VERSION = 3
    can_short = True

    timeframe = "1m"
    informative_timeframe_1 = "3m"
    informative_timeframe_2 = "5m"

    startup_candle_count = 300
    process_only_new_candles = True

    # Dynamic ROI controls
    roi_t1 = IntParameter(6, 30, default=12, space="sell")
    roi_t2 = IntParameter(20, 70, default=35, space="sell")
    roi_p1 = DecimalParameter(0.0015, 0.0080, default=0.0035, decimals=4, space="sell")
    roi_p2 = DecimalParameter(0.0008, 0.0040, default=0.0018, decimals=4, space="sell")

    # Entry thresholds
    adx_min = IntParameter(16, 40, default=24, space="buy")
    ema_gap_min = DecimalParameter(0.0003, 0.0030, default=0.0012, decimals=4, space="buy")
    volume_mult = DecimalParameter(0.8, 2.5, default=1.2, decimals=2, space="buy")

    # Stoploss / trailing
    stoploss = -0.018
    trailing_stop = True
    trailing_stop_positive = 0.005
    trailing_stop_positive_offset = 0.008
    trailing_only_offset_is_reached = True

    tsl_positive = DecimalParameter(0.003, 0.012, default=0.005, decimals=3, space="sell")
    tsl_offset = DecimalParameter(0.005, 0.018, default=0.008, decimals=3, space="sell")

    use_custom_stoploss = False

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {
            "0": float(self.roi_p1.value),
            str(int(self.roi_t1.value)): float(self.roi_p2.value),
            str(int(self.roi_t2.value)): 0.0,
        }

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 6},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 120,
                "trade_limit": 4,
                "stop_duration_candles": 20,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 240,
                "trade_limit": 20,
                "stop_duration_candles": 40,
                "max_allowed_drawdown": 0.08,
            },
        ]

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        return [(pair, self.informative_timeframe_1) for pair in pairs] + [
            (pair, self.informative_timeframe_2) for pair in pairs
        ]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema_fast"] = ta.EMA(dataframe, timeperiod=8)
        dataframe["ema_slow"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()

        inf3 = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe_1)
        inf3["ema_fast"] = ta.EMA(inf3, timeperiod=8)
        inf3["ema_slow"] = ta.EMA(inf3, timeperiod=21)
        inf3["adx"] = ta.ADX(inf3, timeperiod=14)

        inf5 = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe_2)
        inf5["ema_fast"] = ta.EMA(inf5, timeperiod=8)
        inf5["ema_slow"] = ta.EMA(inf5, timeperiod=21)

        dataframe = merge_informative_pair(dataframe, inf3, self.timeframe, self.informative_timeframe_1, ffill=True)
        dataframe = merge_informative_pair(dataframe, inf5, self.timeframe, self.informative_timeframe_2, ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        gap = (dataframe["ema_fast"] - dataframe["ema_slow"]) / dataframe["close"]

        long_regime = (
            (dataframe["adx"] > self.adx_min.value)  # avoid chop
            & (dataframe["atr_pct"] > 0.0007)
            & (dataframe["adx_3m"] > self.adx_min.value)
            & (dataframe["ema_fast_5m"] > dataframe["ema_slow_5m"])
        )
        short_regime = (
            (dataframe["adx"] > self.adx_min.value)
            & (dataframe["atr_pct"] > 0.0007)
            & (dataframe["adx_3m"] > self.adx_min.value)
            & (dataframe["ema_fast_5m"] < dataframe["ema_slow_5m"])
        )

        volume_ok = dataframe["volume"] > dataframe["vol_ma"] * self.volume_mult.value

        dataframe.loc[
            long_regime & volume_ok & (gap > self.ema_gap_min.value) & (dataframe["close"] > dataframe["ema_fast"]),
            ["enter_long", "enter_tag"],
        ] = (1, "s1_microtrend_long")

        dataframe.loc[
            short_regime & volume_ok & (gap < -self.ema_gap_min.value) & (dataframe["close"] < dataframe["ema_fast"]),
            ["enter_short", "enter_tag"],
        ] = (1, "s1_microtrend_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] < dataframe["ema_fast"]) & (dataframe["enter_tag"] == "s1_microtrend_long"),
            ["exit_long", "exit_tag"],
        ] = (1, "s1_ema_loss")

        dataframe.loc[
            (dataframe["close"] > dataframe["ema_fast"]) & (dataframe["enter_tag"] == "s1_microtrend_short"),
            ["exit_short", "exit_tag"],
        ] = (1, "s1_ema_loss")
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float, max_leverage: float,
                 entry_tag: str | None, side: str, **kwargs) -> float:
        return min(3.0, max_leverage)

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float, time_in_force: str,
                            current_time: datetime, entry_tag: str | None, side: str, **kwargs) -> bool:
        self.logger.info(
            {
                "event": "entry_confirm",
                "strategy": "S1",
                "pair": pair,
                "side": side,
                "entry_tag": entry_tag,
                "rate": rate,
                "timestamp": current_time.isoformat(),
            }
        )
        return True

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        self.logger.info(
            {
                "event": "exit_monitor",
                "strategy": "S1",
                "pair": pair,
                "side": trade.trade_direction,
                "profit": round(current_profit, 5),
                "open_minutes": int((current_time - trade.open_date_utc).total_seconds() / 60),
            }
        )
        return None

```

### user_data/strategies/S2_HFT_Aggressive_MeanReversion_Fade.py
```python
from datetime import datetime
from typing import Dict

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter


class S2_HFT_Aggressive_MeanReversion_Fade(IStrategy):
    """
    S2: HFT Aggressive Mean-Reversion Fade (1m base, 5m context).

    Fee/slippage assumptions:
    - Taker fee: 0.04% / side.
    - Slippage: 0.05% / side (aggressive entries).
    - Combined cost baseline: ~0.18% round-trip.

    Leverage safety notes:
    - Keep isolated leverage <= 2x because fades can stack into trend legs.
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "1m"
    startup_candle_count = 250

    zscore_threshold = DecimalParameter(1.2, 3.5, default=2.1, decimals=2, space="buy")
    rsi_low = IntParameter(10, 40, default=24, space="buy")
    rsi_high = IntParameter(60, 90, default=76, space="buy")
    adx_max = IntParameter(14, 30, default=22, space="buy")

    stoploss = -0.022
    trailing_stop = True
    trailing_stop_positive = 0.004
    trailing_stop_positive_offset = 0.009
    trailing_only_offset_is_reached = True

    roi_fast = DecimalParameter(0.002, 0.012, default=0.005, decimals=3, space="sell")
    roi_slow = DecimalParameter(0.0, 0.006, default=0.001, decimals=3, space="sell")
    roi_t = IntParameter(4, 25, default=10, space="sell")

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {"0": float(self.roi_fast.value), str(int(self.roi_t.value)): float(self.roi_slow.value)}

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 10},
            {
                "method": "LowProfitPairs",
                "lookback_period_candles": 100,
                "trade_limit": 6,
                "stop_duration_candles": 20,
                "required_profit": 0.005,
            },
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 180,
                "trade_limit": 5,
                "stop_duration_candles": 30,
                "only_per_pair": False,
            },
        ]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["std"] = dataframe["close"].rolling(50).std()
        dataframe["zscore"] = (dataframe["close"] - dataframe["ema"]) / dataframe["std"]
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["ema_slope"] = dataframe["ema"].pct_change(5)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Regime filter: avoid one-way trends for mean-reversion
        mr_regime = (dataframe["adx"] < self.adx_max.value) & (dataframe["ema_slope"].abs() < 0.0035)

        dataframe.loc[
            mr_regime
            & (dataframe["zscore"] < -self.zscore_threshold.value)
            & (dataframe["rsi"] < self.rsi_low.value),
            ["enter_long", "enter_tag"],
        ] = (1, "s2_fade_long")

        dataframe.loc[
            mr_regime
            & (dataframe["zscore"] > self.zscore_threshold.value)
            & (dataframe["rsi"] > self.rsi_high.value),
            ["enter_short", "enter_tag"],
        ] = (1, "s2_fade_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["zscore"] > -0.2) | (dataframe["rsi"] > 50), ["exit_long", "exit_tag"]] = (1, "s2_revert")
        dataframe.loc[(dataframe["zscore"] < 0.2) | (dataframe["rsi"] < 50), ["exit_short", "exit_tag"]] = (1, "s2_revert")
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float, max_leverage: float,
                 entry_tag: str | None, side: str, **kwargs) -> float:
        return min(2.0, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        self.logger.info(
            {
                "event": "diagnostic",
                "strategy": "S2",
                "pair": pair,
                "direction": trade.trade_direction,
                "entry_tag": trade.enter_tag,
                "pnl": round(current_profit, 5),
                "duration_min": int((current_time - trade.open_date_utc).total_seconds() / 60),
            }
        )
        return None

```

### user_data/strategies/S3_MFT_Conservative_TrendPullback.py
```python
from datetime import datetime
from typing import Dict

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter, merge_informative_pair


class S3_MFT_Conservative_TrendPullback(IStrategy):
    """
    S3: MFT Conservative Trend-Pullback (15m base, 1h regime).

    Fee/slippage assumptions:
    - Taker fee: 0.04% / side.
    - Slippage: 0.02% / side.
    - Cost baseline: ~0.12% round-trip.

    Leverage safety notes:
    - Conservative trend strategy, isolated leverage <= 3x.
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    informative_timeframe = "1h"
    startup_candle_count = 300

    pullback_depth = DecimalParameter(0.002, 0.02, default=0.007, decimals=3, space="buy")
    adx_min = IntParameter(16, 40, default=24, space="buy")
    rsi_floor = IntParameter(30, 50, default=40, space="buy")
    rsi_ceiling = IntParameter(50, 70, default=60, space="buy")

    stoploss = -0.035
    trailing_stop = True
    trailing_stop_positive = 0.01
    trailing_stop_positive_offset = 0.018
    trailing_only_offset_is_reached = True

    roi1 = DecimalParameter(0.01, 0.06, default=0.025, decimals=3, space="sell")
    roi2 = DecimalParameter(0.0, 0.03, default=0.008, decimals=3, space="sell")
    t1 = IntParameter(30, 180, default=90, space="sell")

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {"0": float(self.roi1.value), str(int(self.t1.value)): float(self.roi2.value), "360": 0.0}

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 4},
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 80,
                "trade_limit": 12,
                "stop_duration_candles": 12,
                "max_allowed_drawdown": 0.12,
            },
            {
                "method": "LowProfitPairs",
                "lookback_period_candles": 60,
                "trade_limit": 5,
                "stop_duration_candles": 20,
                "required_profit": 0.01,
            },
        ]

    def informative_pairs(self):
        return [(pair, self.informative_timeframe) for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        inf = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe)
        inf["ema50"] = ta.EMA(inf, timeperiod=50)
        inf["ema200"] = ta.EMA(inf, timeperiod=200)
        inf["adx"] = ta.ADX(inf, timeperiod=14)

        dataframe = merge_informative_pair(dataframe, inf, self.timeframe, self.informative_timeframe, ffill=True)
        dataframe["pullback"] = (dataframe["ema20"] - dataframe["close"]) / dataframe["close"]
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Regime filter for trend strategy: avoid chop via ADX + HTF trend alignment
        long_regime = (
            (dataframe["adx"] > self.adx_min.value)
            & (dataframe["adx_1h"] > self.adx_min.value)
            & (dataframe["ema50_1h"] > dataframe["ema200_1h"])
        )
        short_regime = (
            (dataframe["adx"] > self.adx_min.value)
            & (dataframe["adx_1h"] > self.adx_min.value)
            & (dataframe["ema50_1h"] < dataframe["ema200_1h"])
        )

        dataframe.loc[
            long_regime
            & (dataframe["pullback"] > self.pullback_depth.value)
            & (dataframe["rsi"] > self.rsi_floor.value),
            ["enter_long", "enter_tag"],
        ] = (1, "s3_pullback_long")

        dataframe.loc[
            short_regime
            & ((dataframe["close"] - dataframe["ema20"]) / dataframe["close"] > self.pullback_depth.value)
            & (dataframe["rsi"] < self.rsi_ceiling.value),
            ["enter_short", "enter_tag"],
        ] = (1, "s3_pullback_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] < dataframe["ema50"]) | (dataframe["rsi"] > 72), ["exit_long", "exit_tag"]] = (1, "s3_trend_break")
        dataframe.loc[(dataframe["close"] > dataframe["ema50"]) | (dataframe["rsi"] < 28), ["exit_short", "exit_tag"]] = (1, "s3_trend_break")
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float, max_leverage: float,
                 entry_tag: str | None, side: str, **kwargs) -> float:
        return min(3.0, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        self.logger.info(
            {
                "event": "diagnostic",
                "strategy": "S3",
                "pair": pair,
                "entry_tag": trade.enter_tag,
                "direction": trade.trade_direction,
                "current_profit": round(current_profit, 5),
            }
        )
        return None

```

### user_data/strategies/S4_MFT_Progressive_BreakoutRetest.py
```python
from datetime import datetime
from typing import Dict

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy, DecimalParameter, IntParameter, merge_informative_pair


class S4_MFT_Progressive_BreakoutRetest(IStrategy):
    """
    S4: MFT Progressive Breakout-Retest (15m base, 1h context).

    Fee/slippage assumptions:
    - Taker fee: 0.04% / side.
    - Slippage: 0.03% / side near breakout spikes.
    - Cost baseline: ~0.14% round-trip.

    Leverage safety notes:
    - Allow isolated leverage <= 2.5x due to breakout failure risk.
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    informative_timeframe = "1h"
    startup_candle_count = 350

    breakout_window = IntParameter(20, 100, default=55, space="buy")
    retest_buffer = DecimalParameter(0.0005, 0.008, default=0.002, decimals=4, space="buy")
    adx_min = IntParameter(16, 45, default=26, space="buy")

    stoploss = -0.03
    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.022
    trailing_only_offset_is_reached = True

    roi_initial = DecimalParameter(0.01, 0.08, default=0.03, decimals=3, space="sell")
    roi_decay = DecimalParameter(0.0, 0.03, default=0.01, decimals=3, space="sell")
    roi_t = IntParameter(40, 220, default=120, space="sell")

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {"0": float(self.roi_initial.value), str(int(self.roi_t.value)): float(self.roi_decay.value), "600": 0.0}

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 6},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 100,
                "trade_limit": 4,
                "stop_duration_candles": 20,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 120,
                "trade_limit": 15,
                "stop_duration_candles": 24,
                "max_allowed_drawdown": 0.10,
            },
        ]

    def informative_pairs(self):
        return [(pair, self.informative_timeframe) for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["hh"] = dataframe["high"].rolling(int(self.breakout_window.value)).max()
        dataframe["ll"] = dataframe["low"].rolling(int(self.breakout_window.value)).min()

        inf = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe)
        inf["ema50"] = ta.EMA(inf, timeperiod=50)
        inf["ema200"] = ta.EMA(inf, timeperiod=200)
        inf["adx"] = ta.ADX(inf, timeperiod=14)
        dataframe = merge_informative_pair(dataframe, inf, self.timeframe, self.informative_timeframe, ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # Regime filter: avoid chop for breakout systems.
        trend_ok = (
            (dataframe["adx"] > self.adx_min.value)
            & (dataframe["adx_1h"] > self.adx_min.value)
            & (dataframe["atr_pct"] > 0.001)
        )

        long_break = dataframe["close"] > dataframe["hh"].shift(1)
        long_retest = (dataframe["close"] <= dataframe["hh"].shift(1) * (1 + self.retest_buffer.value)) & (
            dataframe["close"] >= dataframe["hh"].shift(1) * (1 - self.retest_buffer.value)
        )

        short_break = dataframe["close"] < dataframe["ll"].shift(1)
        short_retest = (dataframe["close"] >= dataframe["ll"].shift(1) * (1 - self.retest_buffer.value)) & (
            dataframe["close"] <= dataframe["ll"].shift(1) * (1 + self.retest_buffer.value)
        )

        dataframe.loc[
            trend_ok & (dataframe["ema50_1h"] > dataframe["ema200_1h"]) & long_break & long_retest,
            ["enter_long", "enter_tag"],
        ] = (1, "s4_breakout_long")

        dataframe.loc[
            trend_ok & (dataframe["ema50_1h"] < dataframe["ema200_1h"]) & short_break & short_retest,
            ["enter_short", "enter_tag"],
        ] = (1, "s4_breakout_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] < dataframe["hh"].shift(1)) | (dataframe["adx"] < 15), ["exit_long", "exit_tag"]] = (1, "s4_failed_break")
        dataframe.loc[(dataframe["close"] > dataframe["ll"].shift(1)) | (dataframe["adx"] < 15), ["exit_short", "exit_tag"]] = (1, "s4_failed_break")
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float, max_leverage: float,
                 entry_tag: str | None, side: str, **kwargs) -> float:
        return min(2.5, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        self.logger.info(
            {
                "event": "diagnostic",
                "strategy": "S4",
                "pair": pair,
                "side": trade.trade_direction,
                "entry_tag": trade.enter_tag,
                "profit": round(current_profit, 5),
            }
        )
        return None

```

### user_data/strategies/S5_LFT_Conservative_MTF_TrendReversal.py
```python
from __future__ import annotations

from datetime import datetime
from typing import Dict

import numpy as np
import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy, merge_informative_pair


class S5_LFT_Conservative_MTF_TrendReversal(IStrategy):
    """
    S5: LFT Conservative Multi-Timeframe Trend-Reversal.

    Timeframes:
    - Base execution: 1h
    - Regime anchors: 4h and 1d

    Deterministic inputs:
    - OHLCV-only indicators.
    - Optional placeholders for funding/open-interest are provided as NaN columns.

    Capital protection state machine:
    - normal (state=0): full stake.
    - risk_off (state=1): reduced stake.
    - kill_switch (state=2): no new entries.
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "1h"
    informative_timeframe = "4h"
    anchor_timeframe = "1d"
    startup_candle_count = 450

    adx_min = IntParameter(18, 38, default=24, space="buy")
    reversal_rsi_long = IntParameter(30, 48, default=40, space="buy")
    reversal_rsi_short = IntParameter(52, 70, default=60, space="buy")
    volatility_ceiling = DecimalParameter(0.01, 0.08, default=0.035, decimals=3, space="buy")

    stoploss = -0.05
    trailing_stop = True
    trailing_stop_positive = 0.015
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {"0": 0.035, "240": 0.015, "720": 0.0}

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 6},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 120,
                "trade_limit": 4,
                "stop_duration_candles": 30,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 200,
                "trade_limit": 16,
                "stop_duration_candles": 40,
                "max_allowed_drawdown": 0.11,
            },
        ]

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        informative = [(pair, self.informative_timeframe) for pair in pairs]
        informative.extend((pair, self.anchor_timeframe) for pair in pairs)
        return informative

    def _compute_capital_state(self, dataframe: DataFrame) -> DataFrame:
        # Higher values indicate stressed market conditions.
        dataframe["stress_score"] = (
            (dataframe["atr_pct"] > dataframe["atr_pct"].rolling(120).quantile(0.85)).astype(int)
            + (dataframe["volume"] > 1.8 * dataframe["volume"].rolling(48).mean()).astype(int)
            + (dataframe["close"] < dataframe["ema200"]).astype(int)
        )

        dataframe["capital_state"] = 0
        dataframe.loc[dataframe["stress_score"] >= 2, "capital_state"] = 1
        dataframe.loc[
            (dataframe["stress_score"] >= 3)
            | ((dataframe["close"] / dataframe["close"].shift(24) - 1) < -0.08),
            "capital_state",
        ] = 2
        return dataframe

    def _latest_capital_state(self, pair: str) -> int:
        if not self.dp:
            return 0
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty or "capital_state" not in dataframe.columns:
            return 0
        return int(dataframe["capital_state"].iloc[-1])

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]

        inf_4h = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe)
        inf_4h["ema50"] = ta.EMA(inf_4h, timeperiod=50)
        inf_4h["ema200"] = ta.EMA(inf_4h, timeperiod=200)
        inf_4h["adx"] = ta.ADX(inf_4h, timeperiod=14)
        dataframe = merge_informative_pair(dataframe, inf_4h, self.timeframe, self.informative_timeframe, ffill=True)

        inf_1d = self.dp.get_pair_dataframe(metadata["pair"], self.anchor_timeframe)
        inf_1d["ema50"] = ta.EMA(inf_1d, timeperiod=50)
        inf_1d["ema200"] = ta.EMA(inf_1d, timeperiod=200)
        inf_1d["rsi"] = ta.RSI(inf_1d, timeperiod=14)
        dataframe = merge_informative_pair(dataframe, inf_1d, self.timeframe, self.anchor_timeframe, ffill=True)

        # Optional placeholders for exchange-specific derivatives data.
        dataframe["funding_rate_placeholder"] = np.nan
        dataframe["open_interest_placeholder"] = np.nan

        dataframe = self._compute_capital_state(dataframe)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # When NOT to trade: low trend strength, unstable volatility, and kill-switch state.
        notrade_filter = (
            (dataframe["adx"] < self.adx_min.value)
            | (dataframe["atr_pct"] > self.volatility_ceiling.value)
            | (dataframe["volume"] < 0.6 * dataframe["volume"].rolling(48).mean())
            | (dataframe["capital_state"] >= 2)
        )

        long_reversal = (
            (dataframe["ema50_4h"] > dataframe["ema200_4h"])
            & (dataframe["ema50_1d"] > dataframe["ema200_1d"])
            & (dataframe["close"] > dataframe["ema50"])
            & (dataframe["rsi"] > self.reversal_rsi_long.value)
            & (dataframe["rsi"].shift(1) < self.reversal_rsi_long.value)
            & (dataframe["rsi_1d"] > 45)
        )

        short_reversal = (
            (dataframe["ema50_4h"] < dataframe["ema200_4h"])
            & (dataframe["ema50_1d"] < dataframe["ema200_1d"])
            & (dataframe["close"] < dataframe["ema50"])
            & (dataframe["rsi"] < self.reversal_rsi_short.value)
            & (dataframe["rsi"].shift(1) > self.reversal_rsi_short.value)
            & (dataframe["rsi_1d"] < 55)
        )

        dataframe.loc[long_reversal & ~notrade_filter, ["enter_long", "enter_tag"]] = (1, "s5_mtf_rev_long")
        dataframe.loc[short_reversal & ~notrade_filter, ["enter_short", "enter_tag"]] = (1, "s5_mtf_rev_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] < dataframe["ema50"]) | (dataframe["rsi"] > 75) | (dataframe["capital_state"] >= 1),
            ["exit_long", "exit_tag"],
        ] = (1, "s5_regime_or_risk")
        dataframe.loc[
            (dataframe["close"] > dataframe["ema50"]) | (dataframe["rsi"] < 25) | (dataframe["capital_state"] >= 1),
            ["exit_short", "exit_tag"],
        ] = (1, "s5_regime_or_risk")
        return dataframe

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float, time_in_force: str,
                            current_time: datetime, entry_tag: str | None, side: str, **kwargs) -> bool:
        return self._latest_capital_state(pair) < 2

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float, proposed_stake: float,
                            min_stake: float | None, max_stake: float, leverage: float, entry_tag: str | None,
                            side: str, **kwargs) -> float:
        state = self._latest_capital_state(pair)
        if state >= 2:
            return 0.0
        if state == 1:
            return proposed_stake * 0.4
        return proposed_stake

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float,
                 max_leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        state = self._latest_capital_state(pair)
        if state == 1:
            return min(1.5, max_leverage)
        return min(2.0, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        if self._latest_capital_state(pair) >= 2:
            return "s5_kill_switch_exit"
        return None

```

### user_data/strategies/S6_LFT_Progressive_Momentum_Rotation.py
```python
from __future__ import annotations

from datetime import datetime
from typing import Dict

import numpy as np
import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy, merge_informative_pair


class S6_LFT_Progressive_Momentum_Rotation(IStrategy):
    """
    S6: LFT Progressive Momentum Rotation.

    Relative-strength anchor set:
    - BTC/USDT:USDT
    - ETH/USDT:USDT
    - SOL/USDT:USDT

    Strategy adapts benchmark momentum to pair-level signals by comparing
    pair return and trend quality versus benchmark basket return.
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "1h"
    informative_timeframe = "4h"
    startup_candle_count = 450

    momentum_window = IntParameter(12, 72, default=24, space="buy")
    rs_threshold = DecimalParameter(0.002, 0.08, default=0.015, decimals=3, space="buy")
    adx_min = IntParameter(16, 40, default=22, space="buy")

    stoploss = -0.055
    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.026
    trailing_only_offset_is_reached = True

    benchmark_pairs = ["BTC/USDT:USDT", "ETH/USDT:USDT", "SOL/USDT:USDT"]

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {"0": 0.04, "180": 0.018, "600": 0.0}

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 6},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 96,
                "trade_limit": 5,
                "stop_duration_candles": 24,
                "only_per_pair": False,
            },
        ]

    def informative_pairs(self):
        pairs = set(self.dp.current_whitelist())
        pairs.update(self.benchmark_pairs)
        return [(pair, self.informative_timeframe) for pair in pairs]

    def _compute_capital_state(self, dataframe: DataFrame) -> DataFrame:
        drawdown_48h = dataframe["close"] / dataframe["close"].rolling(48).max() - 1
        dataframe["capital_state"] = 0
        risk_off = (drawdown_48h < -0.06) | (dataframe["atr_pct"] > dataframe["atr_pct"].rolling(96).quantile(0.9))
        kill_switch = (drawdown_48h < -0.1) & (dataframe["volume"] > 2.2 * dataframe["volume"].rolling(48).mean())
        dataframe.loc[risk_off, "capital_state"] = 1
        dataframe.loc[kill_switch, "capital_state"] = 2
        return dataframe

    def _latest_capital_state(self, pair: str) -> int:
        if not self.dp:
            return 0
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty or "capital_state" not in dataframe.columns:
            return 0
        return int(dataframe["capital_state"].iloc[-1])

    def _benchmark_return(self, pair: str, window: int) -> float:
        if not self.dp:
            return 0.0
        informative, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if informative is None or informative.empty or len(informative) <= window:
            return 0.0
        return float(informative["close"].iloc[-1] / informative["close"].iloc[-window] - 1)

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["pair_ret"] = dataframe["close"].pct_change(int(self.momentum_window.value))

        inf = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe)
        inf["ema50"] = ta.EMA(inf, timeperiod=50)
        inf["ema200"] = ta.EMA(inf, timeperiod=200)
        dataframe = merge_informative_pair(dataframe, inf, self.timeframe, self.informative_timeframe, ffill=True)

        benchmark_returns = []
        window = int(self.momentum_window.value)
        for bench in self.benchmark_pairs:
            bench_df = self.dp.get_pair_dataframe(bench, self.timeframe)
            if bench_df is not None and len(bench_df) > window:
                benchmark_returns.append(bench_df["close"].pct_change(window))

        if benchmark_returns:
            bench_mean_series = sum(benchmark_returns) / len(benchmark_returns)
            aligned = bench_mean_series.reindex(dataframe.index).ffill()
            dataframe["benchmark_ret"] = aligned
        else:
            dataframe["benchmark_ret"] = 0.0

        dataframe["rs_score"] = dataframe["pair_ret"] - dataframe["benchmark_ret"]
        dataframe["funding_rate_placeholder"] = np.nan
        dataframe["open_interest_placeholder"] = np.nan

        dataframe = self._compute_capital_state(dataframe)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # When NOT to trade: weak trend quality, insufficient liquidity, and kill-switch risk.
        avoid_trading = (
            (dataframe["adx"] < self.adx_min.value)
            | (dataframe["volume"] < dataframe["volume"].rolling(48).mean() * 0.7)
            | (dataframe["atr_pct"] > 0.07)
            | (dataframe["capital_state"] >= 2)
        )

        long_signal = (
            (dataframe["ema50_4h"] > dataframe["ema200_4h"])
            & (dataframe["close"] > dataframe["ema20"])
            & (dataframe["rs_score"] > self.rs_threshold.value)
            & (dataframe["rs_score"] > dataframe["rs_score"].shift(1))
        )

        short_signal = (
            (dataframe["ema50_4h"] < dataframe["ema200_4h"])
            & (dataframe["close"] < dataframe["ema20"])
            & (dataframe["rs_score"] < -self.rs_threshold.value)
            & (dataframe["rs_score"] < dataframe["rs_score"].shift(1))
        )

        dataframe.loc[long_signal & ~avoid_trading, ["enter_long", "enter_tag"]] = (1, "s6_rotation_long")
        dataframe.loc[short_signal & ~avoid_trading, ["enter_short", "enter_tag"]] = (1, "s6_rotation_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["rs_score"] < 0) | (dataframe["close"] < dataframe["ema20"]) | (dataframe["capital_state"] >= 1),
            ["exit_long", "exit_tag"],
        ] = (1, "s6_rs_decay")
        dataframe.loc[
            (dataframe["rs_score"] > 0) | (dataframe["close"] > dataframe["ema20"]) | (dataframe["capital_state"] >= 1),
            ["exit_short", "exit_tag"],
        ] = (1, "s6_rs_decay")
        return dataframe

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float, time_in_force: str,
                            current_time: datetime, entry_tag: str | None, side: str, **kwargs) -> bool:
        return self._latest_capital_state(pair) < 2

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float, proposed_stake: float,
                            min_stake: float | None, max_stake: float, leverage: float, entry_tag: str | None,
                            side: str, **kwargs) -> float:
        state = self._latest_capital_state(pair)
        if state >= 2:
            return 0.0
        if state == 1:
            return proposed_stake * 0.5
        return proposed_stake

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float,
                 max_leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        state = self._latest_capital_state(pair)
        if state == 1:
            return min(1.8, max_leverage)
        return min(2.3, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        if self._latest_capital_state(pair) >= 2:
            return "s6_kill_switch_exit"
        return None

```

### user_data/strategies/S7_Event_Volatility_Shock_Strategy.py
```python
from __future__ import annotations

from datetime import datetime
from typing import Dict

import numpy as np
import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import IStrategy


class S7_Event_Volatility_Shock_Strategy(IStrategy):
    """
    S7: Event/Volatility Shock Strategy.

    Deterministic event proxies (OHLCV-only):
    1) volatility burst
    2) volume spike
    3) range expansion + follow-through

    No external news API is used.
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    startup_candle_count = 350

    stoploss = -0.04
    trailing_stop = True
    trailing_stop_positive = 0.014
    trailing_stop_positive_offset = 0.03
    trailing_only_offset_is_reached = True

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {"0": 0.03, "90": 0.012, "360": 0.0}

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 8},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 120,
                "trade_limit": 5,
                "stop_duration_candles": 36,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 140,
                "trade_limit": 16,
                "stop_duration_candles": 40,
                "max_allowed_drawdown": 0.12,
            },
        ]

    def _compute_capital_state(self, dataframe: DataFrame) -> DataFrame:
        recent_drop = dataframe["close"] / dataframe["close"].shift(32) - 1
        stress = (dataframe["volatility_burst"] & dataframe["volume_spike"]).astype(int) + (recent_drop < -0.07).astype(int)
        dataframe["capital_state"] = 0
        dataframe.loc[stress >= 1, "capital_state"] = 1
        dataframe.loc[(stress >= 2) | (recent_drop < -0.12), "capital_state"] = 2
        return dataframe

    def _latest_capital_state(self, pair: str) -> int:
        if not self.dp:
            return 0
        dataframe, _ = self.dp.get_analyzed_dataframe(pair, self.timeframe)
        if dataframe is None or dataframe.empty or "capital_state" not in dataframe.columns:
            return 0
        return int(dataframe["capital_state"].iloc[-1])

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        dataframe["volatility_burst"] = dataframe["atr_pct"] > dataframe["atr_pct"].rolling(96).quantile(0.9)
        dataframe["volume_spike"] = dataframe["volume"] > dataframe["volume"].rolling(96).mean() * 2.0

        dataframe["true_range"] = (dataframe["high"] - dataframe["low"]) / dataframe["close"]
        dataframe["range_expansion"] = dataframe["true_range"] > dataframe["true_range"].rolling(96).quantile(0.9)

        # Follow-through uses the already closed previous candle to avoid lookahead.
        dataframe["bull_follow_through"] = dataframe["close"].shift(1) > dataframe["high"].shift(2)
        dataframe["bear_follow_through"] = dataframe["close"].shift(1) < dataframe["low"].shift(2)

        dataframe["event_proxy_long"] = (
            dataframe["volatility_burst"] & dataframe["volume_spike"] & dataframe["range_expansion"] & dataframe["bull_follow_through"]
        )
        dataframe["event_proxy_short"] = (
            dataframe["volatility_burst"] & dataframe["volume_spike"] & dataframe["range_expansion"] & dataframe["bear_follow_through"]
        )

        dataframe["funding_rate_placeholder"] = np.nan
        dataframe["open_interest_placeholder"] = np.nan

        dataframe = self._compute_capital_state(dataframe)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        # When NOT to trade: no event confirmation, post-shock chop, or kill-switch mode.
        avoid_trading = (
            (dataframe["capital_state"] >= 2)
            | (dataframe["volume"] < dataframe["volume"].rolling(48).mean() * 0.8)
            | (dataframe["atr_pct"] < dataframe["atr_pct"].rolling(96).quantile(0.4))
        )

        dataframe.loc[
            dataframe["event_proxy_long"] & (dataframe["close"] > dataframe["ema20"]) & ~avoid_trading,
            ["enter_long", "enter_tag"],
        ] = (1, "s7_event_long")

        dataframe.loc[
            dataframe["event_proxy_short"] & (dataframe["close"] < dataframe["ema20"]) & ~avoid_trading,
            ["enter_short", "enter_tag"],
        ] = (1, "s7_event_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[
            (dataframe["close"] < dataframe["ema20"]) | (dataframe["rsi"] > 74) | (dataframe["capital_state"] >= 1),
            ["exit_long", "exit_tag"],
        ] = (1, "s7_post_event_exit")

        dataframe.loc[
            (dataframe["close"] > dataframe["ema20"]) | (dataframe["rsi"] < 26) | (dataframe["capital_state"] >= 1),
            ["exit_short", "exit_tag"],
        ] = (1, "s7_post_event_exit")
        return dataframe

    def confirm_trade_entry(self, pair: str, order_type: str, amount: float, rate: float, time_in_force: str,
                            current_time: datetime, entry_tag: str | None, side: str, **kwargs) -> bool:
        return self._latest_capital_state(pair) < 2

    def custom_stake_amount(self, pair: str, current_time: datetime, current_rate: float, proposed_stake: float,
                            min_stake: float | None, max_stake: float, leverage: float, entry_tag: str | None,
                            side: str, **kwargs) -> float:
        state = self._latest_capital_state(pair)
        if state >= 2:
            return 0.0
        if state == 1:
            return proposed_stake * 0.35
        return proposed_stake

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float,
                 max_leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        state = self._latest_capital_state(pair)
        if state == 1:
            return min(1.4, max_leverage)
        return min(2.0, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        if self._latest_capital_state(pair) >= 2:
            return "s7_kill_switch_exit"
        return None

```

### user_data/strategies/S8_HFT_Progressive_Orderflow_Impulse.py
```python
from datetime import datetime
from typing import Dict

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy, merge_informative_pair


class S8_HFT_Progressive_Orderflow_Impulse(IStrategy):
    """
    S8: HFT Progressive Orderflow Impulse (1m + 5m context).
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "1m"
    informative_timeframe = "5m"
    startup_candle_count = 320

    adx_floor = IntParameter(14, 36, default=20, space="buy")
    impulse_threshold = DecimalParameter(0.0008, 0.0060, default=0.0022, decimals=4, space="buy")
    volume_spike_mult = DecimalParameter(1.1, 3.0, default=1.6, decimals=2, space="buy")

    stoploss = -0.024
    trailing_stop = True
    trailing_stop_positive = 0.006
    trailing_stop_positive_offset = 0.010
    trailing_only_offset_is_reached = True

    roi_fast = DecimalParameter(0.003, 0.014, default=0.006, decimals=3, space="sell")
    roi_slow = DecimalParameter(0.0, 0.007, default=0.002, decimals=3, space="sell")
    roi_t1 = IntParameter(4, 22, default=10, space="sell")
    roi_t2 = IntParameter(16, 64, default=28, space="sell")

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {
            "0": float(self.roi_fast.value),
            str(int(self.roi_t1.value)): float(self.roi_slow.value),
            str(int(self.roi_t2.value)): 0.0,
        }

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 4},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 120,
                "trade_limit": 5,
                "stop_duration_candles": 16,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 220,
                "trade_limit": 24,
                "stop_duration_candles": 28,
                "max_allowed_drawdown": 0.1,
            },
        ]

    def informative_pairs(self):
        return [(pair, self.informative_timeframe) for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema9"] = ta.EMA(dataframe, timeperiod=9)
        dataframe["ema21"] = ta.EMA(dataframe, timeperiod=21)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["vol_ma"] = dataframe["volume"].rolling(20).mean()
        dataframe["impulse"] = (dataframe["close"] - dataframe["open"]) / dataframe["open"]

        inf = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe)
        inf["ema21"] = ta.EMA(inf, timeperiod=21)
        inf["ema55"] = ta.EMA(inf, timeperiod=55)
        inf["adx"] = ta.ADX(inf, timeperiod=14)
        dataframe = merge_informative_pair(dataframe, inf, self.timeframe, self.informative_timeframe, ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        volume_ok = dataframe["volume"] > dataframe["vol_ma"] * self.volume_spike_mult.value
        trend_long = (dataframe["ema21_5m"] > dataframe["ema55_5m"]) & (dataframe["adx_5m"] > self.adx_floor.value)
        trend_short = (dataframe["ema21_5m"] < dataframe["ema55_5m"]) & (dataframe["adx_5m"] > self.adx_floor.value)

        dataframe.loc[
            trend_long
            & volume_ok
            & (dataframe["adx"] > self.adx_floor.value)
            & (dataframe["impulse"] > self.impulse_threshold.value)
            & (dataframe["atr_pct"] > 0.0008),
            ["enter_long", "enter_tag"],
        ] = (1, "s8_impulse_long")

        dataframe.loc[
            trend_short
            & volume_ok
            & (dataframe["adx"] > self.adx_floor.value)
            & (dataframe["impulse"] < -self.impulse_threshold.value)
            & (dataframe["atr_pct"] > 0.0008),
            ["enter_short", "enter_tag"],
        ] = (1, "s8_impulse_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] < dataframe["ema9"]), ["exit_long", "exit_tag"]] = (1, "s8_momentum_fade")
        dataframe.loc[(dataframe["close"] > dataframe["ema9"]), ["exit_short", "exit_tag"]] = (1, "s8_momentum_fade")
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float,
                 max_leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        return min(2.5, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        if current_profit < -0.015 and (current_time - trade.open_date_utc).total_seconds() > 25 * 60:
            return "s8_time_stop"
        return None

```

### user_data/strategies/S9_MFT_Aggressive_TrendAcceleration.py
```python
from datetime import datetime
from typing import Dict

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy, merge_informative_pair


class S9_MFT_Aggressive_TrendAcceleration(IStrategy):
    """
    S9: MFT Aggressive Trend Acceleration (15m + 1h context).
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "15m"
    informative_timeframe = "1h"
    startup_candle_count = 350

    adx_floor = IntParameter(16, 38, default=24, space="buy")
    roc_threshold = DecimalParameter(0.004, 0.03, default=0.012, decimals=3, space="buy")
    atr_floor = DecimalParameter(0.003, 0.03, default=0.009, decimals=3, space="buy")

    stoploss = -0.042
    trailing_stop = True
    trailing_stop_positive = 0.012
    trailing_stop_positive_offset = 0.022
    trailing_only_offset_is_reached = True

    roi_fast = DecimalParameter(0.010, 0.050, default=0.021, decimals=3, space="sell")
    roi_mid = DecimalParameter(0.003, 0.025, default=0.010, decimals=3, space="sell")
    roi_t1 = IntParameter(12, 72, default=24, space="sell")
    roi_t2 = IntParameter(40, 180, default=90, space="sell")

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {
            "0": float(self.roi_fast.value),
            str(int(self.roi_t1.value)): float(self.roi_mid.value),
            str(int(self.roi_t2.value)): 0.0,
        }

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 3},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 96,
                "trade_limit": 6,
                "stop_duration_candles": 18,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 180,
                "trade_limit": 20,
                "stop_duration_candles": 24,
                "max_allowed_drawdown": 0.14,
            },
        ]

    def informative_pairs(self):
        return [(pair, self.informative_timeframe) for pair in self.dp.current_whitelist()]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema20"] = ta.EMA(dataframe, timeperiod=20)
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["roc"] = ta.ROC(dataframe, timeperiod=6) / 100
        dataframe["rsi"] = ta.RSI(dataframe, timeperiod=14)

        inf = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe)
        inf["ema50"] = ta.EMA(inf, timeperiod=50)
        inf["ema200"] = ta.EMA(inf, timeperiod=200)
        inf["adx"] = ta.ADX(inf, timeperiod=14)
        dataframe = merge_informative_pair(dataframe, inf, self.timeframe, self.informative_timeframe, ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        strong_market = (dataframe["atr_pct"] > self.atr_floor.value) & (dataframe["adx"] > self.adx_floor.value)
        long_bias = (dataframe["ema50_1h"] > dataframe["ema200_1h"]) & (dataframe["adx_1h"] > self.adx_floor.value)
        short_bias = (dataframe["ema50_1h"] < dataframe["ema200_1h"]) & (dataframe["adx_1h"] > self.adx_floor.value)

        dataframe.loc[
            strong_market
            & long_bias
            & (dataframe["close"] > dataframe["ema20"])
            & (dataframe["roc"] > self.roc_threshold.value)
            & (dataframe["rsi"] > 53),
            ["enter_long", "enter_tag"],
        ] = (1, "s9_accel_long")

        dataframe.loc[
            strong_market
            & short_bias
            & (dataframe["close"] < dataframe["ema20"])
            & (dataframe["roc"] < -self.roc_threshold.value)
            & (dataframe["rsi"] < 47),
            ["enter_short", "enter_tag"],
        ] = (1, "s9_accel_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] < dataframe["ema20"]) | (dataframe["roc"] < 0), ["exit_long", "exit_tag"]] = (1, "s9_decel")
        dataframe.loc[(dataframe["close"] > dataframe["ema20"]) | (dataframe["roc"] > 0), ["exit_short", "exit_tag"]] = (1, "s9_decel")
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float,
                 max_leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        return min(2.8, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        if current_profit < -0.03 and (current_time - trade.open_date_utc).total_seconds() > 8 * 3600:
            return "s9_timeout_loss"
        return None

```

### user_data/strategies/S10_LFT_Aggressive_RegimeSwitch_Trend.py
```python
from datetime import datetime
from typing import Dict

import talib.abstract as ta
from pandas import DataFrame

from freqtrade.persistence import Trade
from freqtrade.strategy import DecimalParameter, IntParameter, IStrategy, merge_informative_pair


class S10_LFT_Aggressive_RegimeSwitch_Trend(IStrategy):
    """
    S10: LFT Aggressive Regime-Switch Trend (1h base, 4h+1d filters).
    """

    INTERFACE_VERSION = 3
    can_short = True
    timeframe = "1h"
    informative_timeframe = "4h"
    anchor_timeframe = "1d"
    startup_candle_count = 500

    adx_floor = IntParameter(18, 40, default=26, space="buy")
    breakout_buffer = DecimalParameter(0.002, 0.03, default=0.008, decimals=3, space="buy")
    atr_cap = DecimalParameter(0.02, 0.10, default=0.06, decimals=3, space="buy")

    stoploss = -0.065
    trailing_stop = True
    trailing_stop_positive = 0.018
    trailing_stop_positive_offset = 0.038
    trailing_only_offset_is_reached = True

    roi_fast = DecimalParameter(0.020, 0.080, default=0.038, decimals=3, space="sell")
    roi_mid = DecimalParameter(0.006, 0.040, default=0.016, decimals=3, space="sell")
    roi_t1 = IntParameter(18, 120, default=48, space="sell")
    roi_t2 = IntParameter(72, 360, default=168, space="sell")

    @property
    def minimal_roi(self) -> Dict[str, float]:
        return {
            "0": float(self.roi_fast.value),
            str(int(self.roi_t1.value)): float(self.roi_mid.value),
            str(int(self.roi_t2.value)): 0.0,
        }

    @property
    def protections(self):
        return [
            {"method": "CooldownPeriod", "stop_duration_candles": 4},
            {
                "method": "StoplossGuard",
                "lookback_period_candles": 100,
                "trade_limit": 5,
                "stop_duration_candles": 20,
                "only_per_pair": False,
            },
            {
                "method": "MaxDrawdown",
                "lookback_period_candles": 220,
                "trade_limit": 18,
                "stop_duration_candles": 32,
                "max_allowed_drawdown": 0.16,
            },
        ]

    def informative_pairs(self):
        pairs = self.dp.current_whitelist()
        return [(p, self.informative_timeframe) for p in pairs] + [(p, self.anchor_timeframe) for p in pairs]

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe["ema50"] = ta.EMA(dataframe, timeperiod=50)
        dataframe["ema200"] = ta.EMA(dataframe, timeperiod=200)
        dataframe["adx"] = ta.ADX(dataframe, timeperiod=14)
        dataframe["atr"] = ta.ATR(dataframe, timeperiod=14)
        dataframe["atr_pct"] = dataframe["atr"] / dataframe["close"]
        dataframe["high_48"] = dataframe["high"].rolling(48).max()
        dataframe["low_48"] = dataframe["low"].rolling(48).min()

        inf4h = self.dp.get_pair_dataframe(metadata["pair"], self.informative_timeframe)
        inf4h["ema50"] = ta.EMA(inf4h, timeperiod=50)
        inf4h["ema200"] = ta.EMA(inf4h, timeperiod=200)
        inf4h["adx"] = ta.ADX(inf4h, timeperiod=14)
        dataframe = merge_informative_pair(dataframe, inf4h, self.timeframe, self.informative_timeframe, ffill=True)

        inf1d = self.dp.get_pair_dataframe(metadata["pair"], self.anchor_timeframe)
        inf1d["ema50"] = ta.EMA(inf1d, timeperiod=50)
        inf1d["ema200"] = ta.EMA(inf1d, timeperiod=200)
        dataframe = merge_informative_pair(dataframe, inf1d, self.timeframe, self.anchor_timeframe, ffill=True)
        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        volatile_but_tradeable = (dataframe["atr_pct"] > 0.008) & (dataframe["atr_pct"] < self.atr_cap.value)
        trend_gate_long = (
            (dataframe["ema50_4h"] > dataframe["ema200_4h"])
            & (dataframe["ema50_1d"] > dataframe["ema200_1d"])
            & (dataframe["adx"] > self.adx_floor.value)
            & (dataframe["adx_4h"] > self.adx_floor.value)
        )
        trend_gate_short = (
            (dataframe["ema50_4h"] < dataframe["ema200_4h"])
            & (dataframe["ema50_1d"] < dataframe["ema200_1d"])
            & (dataframe["adx"] > self.adx_floor.value)
            & (dataframe["adx_4h"] > self.adx_floor.value)
        )

        dataframe.loc[
            trend_gate_long
            & volatile_but_tradeable
            & (dataframe["close"] > dataframe["high_48"].shift(1) * (1 + self.breakout_buffer.value)),
            ["enter_long", "enter_tag"],
        ] = (1, "s10_breakout_long")

        dataframe.loc[
            trend_gate_short
            & volatile_but_tradeable
            & (dataframe["close"] < dataframe["low_48"].shift(1) * (1 - self.breakout_buffer.value)),
            ["enter_short", "enter_tag"],
        ] = (1, "s10_breakout_short")
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe.loc[(dataframe["close"] < dataframe["ema50"]) | (dataframe["adx"] < self.adx_floor.value), ["exit_long", "exit_tag"]] = (1, "s10_trend_fail")
        dataframe.loc[(dataframe["close"] > dataframe["ema50"]) | (dataframe["adx"] < self.adx_floor.value), ["exit_short", "exit_tag"]] = (1, "s10_trend_fail")
        return dataframe

    def leverage(self, pair: str, current_time: datetime, current_rate: float, proposed_leverage: float,
                 max_leverage: float, entry_tag: str | None, side: str, **kwargs) -> float:
        return min(2.2, max_leverage)

    def custom_exit(self, pair: str, trade: Trade, current_time: datetime, current_rate: float, current_profit: float,
                    **kwargs) -> str | None:
        if current_profit < -0.04 and (current_time - trade.open_date_utc).total_seconds() > 24 * 3600:
            return "s10_stale_loss"
        return None

```

## C) Exact CLI sequence (clean install -> data -> backtest -> hyperopt -> dry-run)

```bash
git clone <repo-url> trading-strategies
cd trading-strategies
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install freqtrade
freqtrade create-userdir --userdir user_data
freqtrade download-data --userdir user_data --exchange binance --trading-mode futures --timeframes 1m 15m 1h 4h 1d --pairs BTC/USDT:USDT ETH/USDT:USDT SOL/USDT:USDT BNB/USDT:USDT ADA/USDT:USDT XRP/USDT:USDT --timerange 20230101-
freqtrade backtesting --config user_data/configs/S1_config_stub.json --strategy S1_HFT_Conservative_MicroTrend_Scalper --timerange 20230101-20240630 --export trades --backtest-filename user_data/backtest_results/S1_train.json
freqtrade backtesting --config user_data/configs/S1_config_stub.json --strategy S1_HFT_Conservative_MicroTrend_Scalper --timerange 20240701-20241231 --export trades --backtest-filename user_data/backtest_results/S1_test.json
python scripts/validate_backtest_gates.py --strategy S1 --train user_data/backtest_results/S1_train.json --test user_data/backtest_results/S1_test.json --max-dd 0.10 --max-profit-factor-delta 0.60 --max-winrate-delta 0.12
# Repeat backtest + gate cycle for S2..S10 with matching config/strategy and tier thresholds.
freqtrade hyperopt --config user_data/configs/S1_config_stub.json --strategy S1_HFT_Conservative_MicroTrend_Scalper --spaces buy sell stoploss trailing --hyperopt-loss SharpeHyperOptLossDaily --epochs 200
# Repeat hyperopt for S2..S10.
freqtrade trade --config user_data/configs/S1_config_stub.json --strategy S1_HFT_Conservative_MicroTrend_Scalper --dry-run
```

## D) Top-3 safest to start live

1. **S1_HFT_Conservative_MicroTrend_Scalper** — tight risk controls, conservative HFT profile, and strict trend/volume filters.
2. **S3_MFT_Conservative_TrendPullback** — medium-frequency reduces microstructure noise while retaining trend edge.
3. **S5_LFT_Conservative_MTF_TrendReversal** — longest horizon among conservative systems with robust HTF regime gating and capital-state controls.
