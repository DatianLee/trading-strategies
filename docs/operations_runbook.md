# Operations Runbook: S1-S7 Portfolio Orchestration

## Scope
This runbook covers startup, live monitoring, incident response, and rollback for the portfolio orchestration layer coordinating S1-S7.

---

## 1) Startup Procedure

### Pre-flight checks
1. Confirm exchange connectivity and API key permissions (trade + futures + funding endpoints if available).
2. Validate base strategy configs and orchestrator config syntax.
3. Verify clock sync (NTP drift under 1 second).
4. Confirm profile selection (`conservative`, `balanced`, `aggressive`) for the session.
5. Confirm kill-switch channel (Slack/Telegram/webhook) is reachable.

### Launch sequence
1. Start data feed / pairlist refresh.
2. Start S1-S7 strategy workers in paused-entry mode.
3. Start portfolio orchestrator service.
4. Run a dry health check cycle:
   - bucket weights computed
   - caps loaded
   - risk breakers default to inactive
   - execution guards report green
5. Unpause entries in phased mode:
   - Phase A (15 min): enable S3/S4/S5/S6 only
   - Phase B (next 15 min): enable S1
   - Phase C: enable S2 and S7 if spread/vol conditions acceptable

### Startup acceptance criteria
- No config parse errors.
- No stale market data alerts.
- Risk state = `NORMAL`.
- Rejected order rate under 30% in first 30 minutes (higher indicates liquidity/config mismatch).

---

## 2) Live Monitoring

## Core dashboards
- Portfolio equity, daily PnL, rolling drawdown.
- Exposure by strategy and by asset.
- Correlation/alignment panel for BTC/ETH/SOL.
- Volatility regime panel.
- Execution quality: fill ratio, timeout rate, average slippage.

## Alert thresholds
- Daily loss <= -2.0% (warning), <= hard profile limit (critical).
- Rolling DD >= 6% (warning), >= 9% (critical).
- Consecutive losses >= 4 (warning), >= 6 (critical).
- Timeout failure rate > 8% over 1 hour.
- Slippage above profile threshold for 3 consecutive checks on one symbol.
- Funding hook degraded for >2 hours.

## Operator cadence
- Every hour: verify profile and breaker status.
- Every 4 hours: review top concentration exposures.
- Daily close (UTC): export operations report and trigger breaker reset review.

---

## 3) Incident Response

## Incident classes
- **P1 Critical**: hard daily loss limit hit, API outage, runaway exposure, repeated failed exits.
- **P2 Major**: drawdown breaker active, high correlation throttle persists, slippage spike.
- **P3 Minor**: intermittent funding data outage, moderate timeout increase.

## Standard response workflow
1. Acknowledge alert and classify severity.
2. Freeze new entries globally (`ENTRY_HALT=true`) for P1/P2.
3. Verify open positions and liquidation distance.
4. Reduce leverage/profile step if required.
5. Diagnose root cause by category:
   - Market regime shift
   - Liquidity/spread degradation
   - Exchange/API issue
   - Model drift / abnormal signal correlation
6. Apply mitigation playbook (below).
7. Resume gradually only after stabilization conditions are met.

## Mitigation playbooks

### A) Hard daily loss triggered
- Keep exits active, no new entries until next UTC day.
- Force profile to conservative for next session.
- Disable S2 and S7 for first 4 hours next day.

### B) Rolling drawdown breaker triggered
- Keep entry halt for configured freeze window.
- Reduce risk budget by 40% when resuming.
- Require 12h of non-negative cumulative PnL before restoring baseline.

### C) Correlation cluster event (BTC/ETH/SOL highly aligned)
- Apply throttle multiplier 0.60.
- Limit to 1 new position/15m.
- Prefer only highest edge-score signal among aligned assets.

### D) Execution degradation (timeouts/slippage)
- Raise spread filters by strictness (not loosen).
- Switch problematic symbols to cooldown list.
- If exchange unstable, flatten highest-risk positions and pause.

---

## 4) Rollback Procedure

Use rollback when orchestration logic behaves unexpectedly after deployment.

### Triggers for rollback
- Unexpected order rejects > 60% for >30 minutes.
- Exposure caps not enforced in logs.
- Breakers trigger inconsistently with metrics.
- Any uncaught exception loop in orchestrator process.

### Rollback steps
1. Set `ENTRY_HALT=true`.
2. Switch to previous known-good orchestration config version.
3. Restart orchestrator only (strategies remain running paused).
4. Run smoke test (weight calc, cap enforcement, breaker checks).
5. Unpause entries in phased mode.
6. Create incident ticket with diff, timestamps, and impacted symbols.

### Post-rollback validation
- At least 30 minutes stable operation.
- No cap violations.
- Timeout/slippage metrics back within baseline.

---

## 5) Change Management

- All threshold/config changes tracked in version control.
- Mandatory paper-trade validation for 7 days for major changes.
- Emergency overrides expire automatically after 12 hours.
- Weekly review:
  - breaker trigger count
  - top rejected-order reasons
  - concentration exceptions
  - net impact of correlation throttling
