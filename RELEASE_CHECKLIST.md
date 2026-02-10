# RELEASE_CANDIDATE FREEZE CHECKLIST

Status date: 2026-02-10
Scope: `user_data/strategies/*.py`, deployment stubs, and operations readiness documents.

## 1) Strategy re-scan results (critical-issue sweep)

### Automated checks executed
- `python -m compileall user_data/strategies`
  - Result: PASS (all 10 strategies compile).
- `rg -n "shift\(-[0-9]+\)|TODO|FIXME|BUG|HACK" user_data/strategies || true`
  - Result: PASS (no lookahead-like negative shifts, no unresolved TODO/FIXME/BUG/HACK markers).

### Manual risk review summary
- No unresolved **critical code blockers** were found in strategy implementations.
- Existing known limitations remain **operational/process items**, not code integrity defects:
  - live connector behavior (fees/funding/order semantics) must still be validated in dry-run before production.
  - final risk-owner signoff is still required for launch gating.

---

## 2) Go / No-Go gate (explicit release decision points)

Mark each line before release:

### A. Code integrity
- [ ] GO / [ ] NO-GO: All strategy files compile successfully (`compileall` pass).
- [ ] GO / [ ] NO-GO: No lookahead-pattern evidence (`shift(-n)` scan clean).
- [ ] GO / [ ] NO-GO: No unresolved critical markers (`TODO/FIXME/BUG/HACK` scan clean).

### B. Dry-run safety controls
- [ ] GO / [ ] NO-GO: `START_SAFE_PROFILE.md` settings applied (low leverage, low concurrency, strict protections).
- [ ] GO / [ ] NO-GO: Dry-run only (`dry_run: true`) for first rollout window.
- [ ] GO / [ ] NO-GO: Daily and rolling drawdown breakers configured and tested.

### C. Strategy scope control
- [ ] GO / [ ] NO-GO: Only production-candidate strategies enabled for first wave (`S1`, `S3`, `S5`).
- [ ] GO / [ ] NO-GO: All non-production strategies marked experimental and excluded from initial orchestration.

### D. Operations readiness
- [ ] GO / [ ] NO-GO: Alerting and on-call ownership confirmed for first live dry-run window.
- [ ] GO / [ ] NO-GO: Rollback operator has `ROLLBACK_PLAN.md` and tested commands.
- [ ] GO / [ ] NO-GO: Incident channel and escalation policy acknowledged by trading + risk stakeholders.

### E. Live cutover criteria
- [ ] GO / [ ] NO-GO: 24h dry-run meets execution quality thresholds (fill quality/slippage/latency).
- [ ] GO / [ ] NO-GO: 72h dry-run stays within loss and DD hard limits.
- [ ] GO / [ ] NO-GO: Risk owner signoff recorded.

---

## 3) Release-candidate freeze decision template

- Freeze outcome: [ ] GO / [ ] NO-GO
- Approved strategy set: __________________________
- Start timestamp (UTC): __________________________
- Risk owner: ____________________________________
- Ops owner: _____________________________________
- Notes: _________________________________________
