# START_SAFE_PROFILE (First Dry-Run Defaults)

Purpose: ultra-conservative first deployment profile to validate stability before scaling.

## Profile goals
- Keep liquidation risk remote.
- Reduce simultaneous exposure.
- Enforce aggressive protection triggers.
- Prefer missed opportunities over large drawdowns.

## Recommended initial defaults

### 1) Leverage (low)
- `default_leverage: 1.0` (preferred for first 48-72h).
- Hard cap during first wave: `<= 1.5`.
- Disable any profile that implies leverage above `1.5`.

### 2) max_open_trades (reduced)
- Global `max_open_trades: 2` for first wave.
- Optional step-up path after stability:
  - Stage 1 (start): 2
  - Stage 2 (after 72h stable): 3
  - Stage 3 (after 7d stable): 4

### 3) Strict protections
Use or tighten the following controls:

- **CooldownPeriod**
  - `stop_duration_candles`: increase by ~25-50% vs default strategy values where practical.
- **StoplossGuard**
  - lower trade limit trigger by 1.
  - increase stop duration by ~25%.
- **MaxDrawdown guard**
  - `max_allowed_drawdown`: start at `0.05`-`0.06` for launch profile.
- **Daily loss limits**
  - soft halt: `-1.0%`
  - hard halt: `-1.8%`
- **Consecutive-loss breaker**
  - freeze 90m after 3 losses.
  - freeze 6h after 5 losses.

## First-wave strategy allowlist
Only start with production-candidate conservative set:
- `S1_HFT_Conservative_MicroTrend_Scalper`
- `S3_MFT_Conservative_TrendPullback`
- `S5_LFT_Conservative_MTF_TrendReversal`

All other strategies remain disabled (experimental).

## Example conservative config overlay (JSON)

```json
{
  "dry_run": true,
  "max_open_trades": 2,
  "leverage": {
    "default_leverage": 1.0
  },
  "protections": [
    {"method": "CooldownPeriod", "stop_duration_candles": 12},
    {
      "method": "StoplossGuard",
      "lookback_period_candles": 120,
      "trade_limit": 3,
      "stop_duration_candles": 30,
      "only_per_pair": false
    },
    {
      "method": "MaxDrawdown",
      "lookback_period_candles": 288,
      "trade_limit": 20,
      "stop_duration_candles": 72,
      "max_allowed_drawdown": 0.06
    }
  ]
}
```

## Promotion criteria to less-conservative profile
Promote only if all are true:
1. No breaker-triggered hard halts in last 72h.
2. Realized slippage remains within configured guard bands.
3. Rolling drawdown remains below 50% of hard threshold.
4. Risk owner approves profile step-up.
