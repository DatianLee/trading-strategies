# ROLLBACK_PLAN (If Live Metrics Degrade)

Objective: revert trading risk quickly and deterministically when live behavior diverges from expected performance.

## Trigger conditions (any one = rollback)
- Daily realized PnL <= `-1.8%`.
- Rolling drawdown >= `6%` during launch phase.
- Consecutive losses >= `5` within active session.
- Slippage/latency breaches invalidate entry quality for 30+ minutes.
- Exchange instability causes repeated order failures/cancellations.

## Rollback severity levels

### Level 1 — Immediate risk compression (no full stop)
- Set `max_open_trades` to `1`.
- Force `default_leverage` to `1.0`.
- Disable new entries for experimental strategies.
- Keep only one conservative strategy active if needed for diagnostics.

### Level 2 — Trading halt (recommended default on trigger)
- Disable all new entries (global pause).
- Let existing positions exit by stop/ROI or close manually if execution risk rises.
- Keep data ingestion and monitoring alive for postmortem telemetry.

### Level 3 — Full rollback to known-safe baseline
- Restore previous known-good config snapshot from version control tag.
- Restart bot in `dry_run: true` mode.
- Re-enable trading only after root-cause and signoff.

## Operator runbook steps
1. **Acknowledge incident** in ops channel with UTC timestamp and trigger metric.
2. **Apply halt/rollback config**:
   - set `dry_run: true` if uncertain,
   - set `max_open_trades: 0` or disable all pairs/strategies for immediate entry stop.
3. **Reload/restart** bot process with rollback config.
4. **Verify state**:
   - no new entries accepted,
   - open trades count decreasing or manually reduced,
   - alerts return to normal noise floor.
5. **Capture evidence**:
   - logs,
   - exchange error samples,
   - PnL and DD timelines,
   - order latency/slippage snapshots.
6. **Communicate status** to risk + operations owners every 15 minutes until stable.
7. **Post-incident review** before any re-enable.

## Required pre-created artifacts
- `rollback` git tag or commit hash for last known-good deploy.
- Versioned safe config overlay from `START_SAFE_PROFILE.md`.
- Contact roster (risk owner, on-call operator, exchange escalation).

## Re-enable checklist (must all pass)
- Root cause identified and documented.
- Fix verified in dry-run for >= 24h.
- No recurring trigger condition during verification window.
- Risk owner + ops owner dual approval recorded.
