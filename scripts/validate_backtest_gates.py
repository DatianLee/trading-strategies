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
