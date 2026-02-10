# PATCH NOTES

Date: 2026-02-10

## Applied Changes

### 1) S1 exit logic reliability fix
- **File:** `user_data/strategies/S1_HFT_Conservative_MicroTrend_Scalper.py`
- **Issue:** Exit rules referenced dataframe `enter_tag` values to decide long vs short exits.
- **Risk:** In Freqtrade, per-trade entry tags are not guaranteed to be represented in analyzed candle dataframe for exit signal generation in a way this logic assumed. This can cause exits to be missed or behave inconsistently.
- **Patch:**
  - `exit_long` now triggers when `close < ema_fast` **or** `adx < adx_min`.
  - `exit_short` now triggers when `close > ema_fast` **or** `adx < adx_min`.
- **Safety impact:** Improves deterministic exit reachability and reduces stale-position risk under trend deterioration.

## Non-code Deliverables Added

### 2) Acceptance report
- **File:** `ACCEPTANCE_AUDIT_REPORT.md`
- Added full audit evidence, checklist outcomes, issue table, and unresolved human-decision items.

### 3) Validation command matrix
- **File:** `VALIDATION_COMMANDS.md`
- Added standardized executable commands for:
  - data download,
  - per-strategy backtest (train/test),
  - gate checks via `scripts/validate_backtest_gates.py`,
  - hyperopt,
  - dry-run.

## No-Critical-Issue Statement

No critical issues found after patching the S1 exit-logic defect and validating repository structure and syntax.

